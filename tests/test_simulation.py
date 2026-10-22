import pytest
from warehouse import ROWS, COLS, warehouse
from benchmark_loader import MAP_FILE, SCENARIO_DIR, load_map, load_scenarios
from robot import Robot
from task import Task
from pathfinding import a_star
from collision_manager import update_collision_aware
from core.sim_engine import WarehouseSimEngine, CHARGING_STATIONS


def test_benchmark_loading():
    b_map = load_map(MAP_FILE)
    assert b_map.width == 161
    assert b_map.height == 63
    scen_file = SCENARIO_DIR / "warehouse-10-20-10-2-1-random-1.scen"
    scens = load_scenarios(scen_file, b_map)
    assert len(scens) == 1000


def test_pathfinding_validity():
    # Test pathfinding along open outer aisle
    start = (1, 5)
    goal = (1, 25)
    path = a_star(start, goal)
    assert len(path) > 0
    assert path[0] == start
    assert path[-1] == goal
    for r, c in path:
        assert warehouse[r][c] == 0, f"Path entered blocked cell ({r}, {c})"


def test_robot_battery_drain_and_heading():
    robot = Robot(row=1, col=5, robot_id=1, max_battery=100.0)
    initial_battery = robot.battery
    robot.drain_move()
    assert robot.battery < initial_battery
    assert robot.total_distance == 1

    # Heading check
    robot.update_heading_from_step(1, 6)
    assert robot.heading == 0  # East
    robot.row, robot.col = 1, 6
    robot.update_heading_from_step(2, 6)
    assert robot.heading == 1  # South


def test_collision_swap_prevention():
    # Place R1 at (1, 10) wanting (1, 11)
    # Place R2 at (1, 11) wanting (1, 10)
    r1 = Robot(row=1, col=10, robot_id=1)
    r2 = Robot(row=1, col=11, robot_id=2)
    r1.path = [(1, 11)]
    r2.path = [(1, 10)]

    metrics = update_collision_aware([r1, r2], enforce_timer=False)
    # Positions must NOT swap!
    assert (r1.row, r1.col) == (1, 10)
    assert (r2.row, r2.col) == (1, 11)
    assert metrics["swaps_prevented"] >= 2


def test_destination_clash_resolution():
    # Place R1 at (1, 10) and R2 at (1, 12), both wanting (1, 11)
    r1 = Robot(row=1, col=10, robot_id=1)
    r2 = Robot(row=1, col=12, robot_id=2)
    r1.path = [(1, 11)]
    r2.path = [(1, 11)]

    update_collision_aware([r1, r2], enforce_timer=False)
    # Only one robot (lower ID R1) should claim (1, 11)
    assert (r1.row, r1.col) == (1, 11)
    assert (r2.row, r2.col) == (1, 12)
    assert (r1.row, r1.col) != (r2.row, r2.col)


def test_sim_engine_task_lifecycle():
    engine = WarehouseSimEngine(num_robots=2, enable_battery=False, enforce_timer=False, seed=42)
    state = engine.reset(seed=42)
    assert len(engine.robots) == 2
    assert len(engine.waiting_tasks) > 0

    first_task = engine.waiting_tasks[0]
    task_id = first_task.task_id
    success = engine.assign_task_to_robot(robot_id=1, task_id=task_id)
    assert success is True
    assert engine.robots[0].current_task is not None
    assert engine.robots[0].task_stage == "GOING_TO_PICKUP"

    # Step engine until pickup occurs or max steps
    picked_up = False
    for _ in range(500):
        engine.step()
        if engine.robots[0].task_stage == "GOING_TO_DROPOFF":
            picked_up = True
            break
    assert picked_up is True, "Robot did not reach pickup location"


def test_sim_engine_determinism():
    engine1 = WarehouseSimEngine(num_robots=3, seed=123)
    s1 = engine1.reset(seed=123)
    pos1 = [(r["row"], r["col"]) for r in s1["robots"]]

    engine2 = WarehouseSimEngine(num_robots=3, seed=123)
    s2 = engine2.reset(seed=123)
    pos2 = [(r["row"], r["col"]) for r in s2["robots"]]

    assert pos1 == pos2, "Reset was not deterministic under identical seed"
