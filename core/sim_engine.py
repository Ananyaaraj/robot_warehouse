"""
Core Warehouse Simulation Engine.
Headless, deterministic, high-performance simulation core supporting
multi-robot fleet management, battery dynamics, charging pads,
and benchmark scenario task execution.
"""

from typing import List, Tuple, Optional, Dict, Any
import random
from pathlib import Path

from warehouse import ROWS, COLS, warehouse
from benchmark_loader import (
    MAP_FILE,
    SCENARIO_DIR,
    load_map,
    load_scenarios,
    Scenario
)
from robot import Robot
from task import Task
from collision_manager import update_collision_aware


CHARGING_STATIONS: List[Tuple[int, int]] = [
    (1, 5),
    (1, 155),
    (61, 5),
    (61, 155)
]


class WarehouseSimEngine:
    """
    Discrete-time warehouse simulation engine for multi-robot logistics.
    Decoupled from graphical renderers for fast RL rollouts and headless evaluation.
    """

    def __init__(
        self,
        num_robots: int = 5,
        scenario_file: Optional[Path] = None,
        enable_battery: bool = True,
        low_battery_threshold: float = 18.0,
        enforce_timer: bool = False,
        seed: Optional[int] = None
    ):
        self.num_robots = num_robots
        self.enable_battery = enable_battery
        self.low_battery_threshold = low_battery_threshold
        self.enforce_timer = enforce_timer
        self.rng = random.Random(seed)

        # Load benchmark map and scenarios
        self.benchmark_map = load_map(MAP_FILE)
        if scenario_file is None:
            scenario_file = SCENARIO_DIR / "warehouse-10-20-10-2-1-random-1.scen"
        self.scenario_file = scenario_file
        self.all_scenarios = load_scenarios(self.scenario_file, self.benchmark_map)

        self.robots: List[Robot] = []
        self.tasks: List[Task] = []
        self.waiting_tasks: List[Task] = []
        self.completed_tasks: List[Task] = []
        self.current_step = 0
        self.scenario_cursor = 0

        # Performance & Safety Metrics
        self.metrics: Dict[str, Any] = {
            "completed_tasks": 0,
            "total_steps": 0,
            "total_distance": 0,
            "total_wait_time": 0,
            "moves_executed": 0,
            "conflicts_resolved": 0,
            "swaps_prevented": 0,
            "deadlocks_detected": 0,
            "battery_depletions": 0,
            "charges_completed": 0
        }

        self.reset(seed=seed)

    @staticmethod
    def to_grid_pos(pos: Tuple[int, int]) -> Tuple[int, int]:
        """Convert benchmark (x, y) coordinates to grid (row, col) = (y, x)."""
        return (pos[1], pos[0])

    def reset(
        self,
        seed: Optional[int] = None,
        scenario_offset: int = 0,
        num_initial_tasks: int = 5
    ) -> Dict[str, Any]:
        """Reset the simulation environment deterministically."""
        if seed is not None:
            self.rng = random.Random(seed)

        self.current_step = 0
        self.scenario_cursor = scenario_offset % max(1, len(self.all_scenarios) - 20)

        # Reset metrics
        self.metrics = {
            "completed_tasks": 0,
            "total_steps": 0,
            "total_distance": 0,
            "total_wait_time": 0,
            "moves_executed": 0,
            "conflicts_resolved": 0,
            "swaps_prevented": 0,
            "deadlocks_detected": 0,
            "battery_depletions": 0,
            "charges_completed": 0
        }

        # Select initial valid robot starting positions
        robot_positions: List[Tuple[int, int]] = []
        used_positions = set()

        for scen in self.all_scenarios[self.scenario_cursor:]:
            pos = self.to_grid_pos(scen.start)
            if pos not in used_positions and warehouse[pos[0]][pos[1]] == 0:
                robot_positions.append(pos)
                used_positions.add(pos)
                if len(robot_positions) == self.num_robots:
                    break

        if len(robot_positions) < self.num_robots:
            # Fallback search for walkable cells
            for r in range(ROWS):
                for c in range(COLS):
                    if warehouse[r][c] == 0 and (r, c) not in used_positions:
                        robot_positions.append((r, c))
                        used_positions.add((r, c))
                        if len(robot_positions) == self.num_robots:
                            break
                if len(robot_positions) == self.num_robots:
                    break

        self.robots = [
            Robot(row, col, robot_id=i + 1)
            for i, (row, col) in enumerate(robot_positions)
        ]

        self.tasks.clear()
        self.waiting_tasks.clear()
        self.completed_tasks.clear()

        # Generate initial tasks from scenarios
        priorities = ["HIGH", "MEDIUM", "LOW"]
        for i in range(num_initial_tasks):
            scen_idx = (self.scenario_cursor + self.num_robots + i) % len(self.all_scenarios)
            scen = self.all_scenarios[scen_idx]
            task = Task(
                task_id=i + 1,
                pickup=self.to_grid_pos(scen.start),
                dropoff=self.to_grid_pos(scen.goal),
                priority=priorities[i % len(priorities)],
                creation_step=0
            )
            self.tasks.append(task)
            self.waiting_tasks.append(task)

        return self.get_state_dict()

    def add_new_scenario_task(self, priority: Optional[str] = None) -> Optional[Task]:
        """Generate a new task from the benchmark scenario stream."""
        self.scenario_cursor = (self.scenario_cursor + 1) % len(self.all_scenarios)
        scen = self.all_scenarios[self.scenario_cursor]
        pickup = self.to_grid_pos(scen.start)
        dropoff = self.to_grid_pos(scen.goal)

        if pickup == dropoff:
            return None

        if priority is None:
            priority = self.rng.choice(["HIGH", "MEDIUM", "LOW"])

        new_task = Task(
            task_id=len(self.tasks) + 1,
            pickup=pickup,
            dropoff=dropoff,
            priority=priority,
            creation_step=self.current_step
        )
        self.tasks.append(new_task)
        self.waiting_tasks.append(new_task)
        return new_task

    def find_nearest_walkable(self, r: int, c: int) -> Tuple[int, int]:
        """Find the nearest walkable cell to the given coordinate."""
        r = max(0, min(ROWS - 1, int(r)))
        c = max(0, min(COLS - 1, int(c)))
        if warehouse[r][c] == 0:
            return (r, c)
        for dist in range(1, 20):
            for dr in range(-dist, dist + 1):
                for dc in [-dist, dist]:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < ROWS and 0 <= nc < COLS and warehouse[nr][nc] == 0:
                        return (nr, nc)
            for dc in range(-dist, dist + 1):
                for dr in [-dist, dist]:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < ROWS and 0 <= nc < COLS and warehouse[nr][nc] == 0:
                        return (nr, nc)
        return (1, 1)

    def create_custom_task(
        self,
        pickup: Tuple[int, int],
        dropoff: Tuple[int, int],
        priority: str = "HIGH",
        robot_id: Optional[int] = None
    ) -> Optional[Task]:
        """Create a task with user-specified source and destination."""
        valid_pickup = self.find_nearest_walkable(pickup[0], pickup[1])
        valid_dropoff = self.find_nearest_walkable(dropoff[0], dropoff[1])
        if valid_pickup == valid_dropoff:
            valid_dropoff = self.find_nearest_walkable(valid_dropoff[0] + 2, valid_dropoff[1] + 2)

        new_task = Task(
            task_id=len(self.tasks) + 1,
            pickup=valid_pickup,
            dropoff=valid_dropoff,
            priority=priority,
            creation_step=self.current_step
        )
        self.tasks.append(new_task)
        self.waiting_tasks.append(new_task)

        if robot_id is not None:
            self.assign_task_to_robot(robot_id, new_task.task_id)

        return new_task

    def assign_next_task_smart(self) -> Optional[Tuple[int, int]]:
        """
        Intelligent multi-feature task allocation:
        Evaluates task priority, robot proximity, past performance,
        battery health, and fleet workload balancing.
        """
        if not self.waiting_tasks:
            return None

        available_robots = [
            r for r in self.robots
            if r.current_task is None and not r.is_faulty and not r.is_charging and r.battery >= 15.0
        ]
        if not available_robots:
            return None

        best_pair = None
        best_score = float("-inf")
        sorted_tasks = sorted(self.waiting_tasks, key=lambda t: t.priority, reverse=True)

        for task in sorted_tasks[:5]:
            for robot in available_robots:
                dist = abs(robot.row - task.pickup[0]) + abs(robot.col - task.pickup[1])
                workload_penalty = robot.tasks_completed * 2.5
                score = (
                    (task.priority * 35.0)
                    - (dist * 1.0)
                    + (robot.battery * 0.25)
                    + (robot.efficiency_score * 0.2)
                    - workload_penalty
                )

                if score > best_score:
                    best_score = score
                    best_pair = (robot.robot_id, task.task_id)

        if best_pair is not None:
            success = self.assign_task_to_robot(best_pair[0], best_pair[1])
            if success:
                return best_pair
        return None

    def assign_task_to_robot(self, robot_id: int, task_id: int) -> bool:
        """
        Assign an idle robot to a waiting task. Computes A* path to pickup.
        Returns True if assignment succeeded, False otherwise.
        """
        robot = next((r for r in self.robots if r.robot_id == robot_id), None)
        task = next((t for t in self.waiting_tasks if t.task_id == task_id), None)

        if robot is None or task is None:
            return False

        if robot.current_task is not None or robot.is_faulty:
            return False

        # Route robot to pickup location
        blocked = {(o.row, o.col) for o in self.robots if o is not robot}
        success = robot.set_destination(task.pickup[0], task.pickup[1], blocked_positions=blocked)

        # If already at pickup or path found
        if (robot.row, robot.col) == task.pickup:
            success = True
            robot.path = []

        if not success:
            return False

        robot.current_task = task
        robot.task_stage = "GOING_TO_PICKUP"
        task.assign_robot(robot.robot_id, step=self.current_step)
        if task in self.waiting_tasks:
            self.waiting_tasks.remove(task)

        return True

    def _manage_battery_and_charging(self):
        """Update robot battery charging status when at charging stations."""
        for robot in self.robots:
            curr_pos = (robot.row, robot.col)
            if curr_pos in CHARGING_STATIONS:
                if robot.battery < robot.max_battery * 0.98:
                    robot.charge()
                else:
                    robot.is_charging = False
                    if robot.task_stage == "CHARGING":
                        robot.task_stage = "IDLE"
                        self.metrics["charges_completed"] += 1
            else:
                robot.is_charging = False

            # Emergency autonomous charge routing for idle robots with low battery
            if (
                self.enable_battery
                and robot.battery < self.low_battery_threshold
                and robot.current_task is None
                and robot.task_stage != "CHARGING"
                and not robot.is_faulty
            ):
                # Find closest charging station
                stations_sorted = sorted(
                    CHARGING_STATIONS,
                    key=lambda s: abs(s[0] - robot.row) + abs(s[1] - robot.col)
                )
                for station in stations_sorted:
                    if robot.set_destination(station[0], station[1]):
                        robot.task_stage = "CHARGING"
                        break

    def step(self) -> Dict[str, Any]:
        """
        Advance the entire warehouse simulation by 1 discrete time step.
        Executes collision-aware movement, task transitions, and battery accounting.
        """
        self.current_step += 1
        self.metrics["total_steps"] += 1

        # 1. Update charging stations
        if self.enable_battery:
            self._manage_battery_and_charging()

        # 2. Coordinated collision-aware movement
        step_metrics = update_collision_aware(
            self.robots, enforce_timer=self.enforce_timer
        )
        self.metrics["moves_executed"] += step_metrics["moves_executed"]
        self.metrics["conflicts_resolved"] += step_metrics["conflicts_resolved"]
        self.metrics["swaps_prevented"] += step_metrics["swaps_prevented"]
        self.metrics["deadlocks_detected"] += step_metrics["deadlocks_detected"]

        # 3. Task lifecycle execution
        completed_in_step = 0
        pickups_in_step = 0

        for robot in self.robots:
            task = robot.current_task
            if task is None:
                continue

            current_pos = (robot.row, robot.col)

            # Stage 1: Arrived at pickup
            if robot.task_stage == "GOING_TO_PICKUP":
                if current_pos == task.pickup:
                    robot.task_stage = "GOING_TO_DROPOFF"
                    task.mark_picked_up(step=self.current_step)
                    pickups_in_step += 1

                    # Route to drop-off
                    blocked = {(o.row, o.col) for o in self.robots if o is not robot}
                    robot.set_destination(task.dropoff[0], task.dropoff[1], blocked_positions=blocked)

            # Stage 2: Arrived at drop-off
            elif robot.task_stage == "GOING_TO_DROPOFF":
                if current_pos == task.dropoff:
                    task.complete(step=self.current_step)
                    robot.tasks_completed += 1
                    robot.current_task = None
                    robot.task_stage = "IDLE"
                    self.completed_tasks.append(task)
                    self.metrics["completed_tasks"] += 1
                    completed_in_step += 1

        # Check total distance and waiting
        self.metrics["total_distance"] = sum(r.total_distance for r in self.robots)
        self.metrics["total_wait_time"] = sum(r.total_wait_time for r in self.robots)
        for robot in self.robots:
            if robot.is_faulty and robot.battery <= 0.0:
                self.metrics["battery_depletions"] += 1

        state = self.get_state_dict()
        state["step_pickups"] = pickups_in_step
        state["step_completions"] = completed_in_step
        state["step_moves"] = step_metrics["moves_executed"]
        state["step_conflicts"] = step_metrics["conflicts_resolved"]

        return state

    def get_state_dict(self) -> Dict[str, Any]:
        """Export full simulation snapshot suitable for RL and visualization."""
        robot_data = []
        for r in self.robots:
            eff = round(100.0 - (r.blocked_steps * 2.0), 1)
            r.efficiency_score = max(50.0, min(100.0, eff))
            robot_data.append({
                "id": r.robot_id,
                "row": r.row,
                "col": r.col,
                "heading": r.heading,
                "heading_degrees": r.heading_degrees,
                "battery": round(r.battery, 2),
                "is_faulty": r.is_faulty,
                "is_charging": r.is_charging,
                "stage": r.task_stage,
                "task_id": r.current_task.task_id if r.current_task else None,
                "path_len": len(r.path),
                "path": list(r.path),
                "tasks_completed": r.tasks_completed,
                "efficiency": r.efficiency_score
            })

        active_tasks = []
        for r in self.robots:
            if r.current_task is not None:
                t = r.current_task
                active_tasks.append({
                    "id": t.task_id,
                    "robot_id": r.robot_id,
                    "pickup": list(t.pickup),
                    "dropoff": list(t.dropoff),
                    "priority": t.priority_name,
                    "stage": r.task_stage,
                    "status": t.status
                })

        waiting_tasks = []
        for t in self.waiting_tasks[:6]:
            waiting_tasks.append({
                "id": t.task_id,
                "pickup": list(t.pickup),
                "dropoff": list(t.dropoff),
                "priority": t.priority_name,
                "status": t.status
            })

        best_robot = max(
            self.robots,
            key=lambda r: (r.tasks_completed, r.efficiency_score, r.battery),
            default=self.robots[0] if self.robots else None
        )
        best_robot_info = {
            "id": best_robot.robot_id if best_robot else 1,
            "tasks_completed": best_robot.tasks_completed if best_robot else 0,
            "efficiency": best_robot.efficiency_score if best_robot else 100.0,
            "battery": round(best_robot.battery, 1) if best_robot else 100.0
        }

        return {
            "step": self.current_step,
            "robots": robot_data,
            "active_tasks": active_tasks,
            "waiting_tasks": waiting_tasks,
            "waiting_tasks_count": len(self.waiting_tasks),
            "completed_tasks_count": len(self.completed_tasks),
            "total_tasks_count": len(self.tasks),
            "best_robot": best_robot_info,
            "metrics": dict(self.metrics)
        }
