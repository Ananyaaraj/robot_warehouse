"""
Action space definition and action masking for multi-robot task allocation.
"""

from typing import Tuple, Optional
import numpy as np

from core.sim_engine import WarehouseSimEngine


class ActionHandler:
    """
    Manages discrete dispatch decisions and generates validity masks.
    Total actions = 1 (NO-OP) + num_robots * num_candidate_tasks
    """

    def __init__(self, num_robots: int = 5, num_candidate_tasks: int = 5):
        self.num_robots = num_robots
        self.num_candidate_tasks = num_candidate_tasks
        self.total_actions = 1 + self.num_robots * self.num_candidate_tasks

    def decode_action(self, action: int) -> Optional[Tuple[int, int]]:
        """
        Decodes action integer into (robot_idx, task_idx).
        Returns None for action 0 (NO-OP).
        """
        if action == 0:
            return None
        action_idx = action - 1
        robot_idx = action_idx // self.num_candidate_tasks
        task_idx = action_idx % self.num_candidate_tasks
        return (robot_idx, task_idx)

    def encode_action(self, robot_idx: int, task_idx: int) -> int:
        """Encodes (robot_idx, task_idx) into single discrete action integer."""
        return 1 + robot_idx * self.num_candidate_tasks + task_idx

    def get_action_mask(self, engine: WarehouseSimEngine) -> np.ndarray:
        """
        Returns boolean mask of length total_actions.
        True indicates an action is valid; False indicates invalid.
        Action 0 (NO-OP) is always valid.
        """
        mask = np.zeros(self.total_actions, dtype=bool)
        mask[0] = True  # NO-OP is always feasible

        for r_idx in range(self.num_robots):
            if r_idx >= len(engine.robots):
                continue
            robot = engine.robots[r_idx]

            # Robot must be idle, non-faulty, not charging, and have sufficient battery
            robot_eligible = (
                robot.current_task is None
                and not robot.is_faulty
                and not robot.is_charging
                and robot.battery >= 12.0
            )

            if not robot_eligible:
                continue

            for t_idx in range(self.num_candidate_tasks):
                if t_idx >= len(engine.waiting_tasks):
                    continue
                task = engine.waiting_tasks[t_idx]

                # Task must be waiting
                if task.status == "WAITING":
                    action_id = self.encode_action(r_idx, t_idx)
                    mask[action_id] = True

        return mask
