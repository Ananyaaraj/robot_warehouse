"""
Nearest-Eligible-Robot (NER) Task Allocation Baseline.
Heuristic that pairs highest waiting tasks with the closest available robot.
"""

from typing import Optional
import numpy as np
from rl.environment import WarehouseFleetEnv


class NearestRobotPolicy:
    """
    Evaluates Manhattan distance between idle eligible robots and waiting task pickups,
    selecting the minimum distance pair that satisfies the action mask.
    """

    def __init__(self, name: str = "Nearest-Eligible-Robot"):
        self.name = name

    def predict(self, obs: np.ndarray, env: WarehouseFleetEnv) -> int:
        mask = env.action_masks()
        valid_actions = np.where(mask)[0]

        # If only NO-OP is valid, return 0
        if len(valid_actions) == 1 and valid_actions[0] == 0:
            return 0

        engine = env.engine
        best_action = 0
        min_dist = float("inf")

        for action in valid_actions:
            if action == 0:
                continue
            decoded = env.action_handler.decode_action(action)
            if decoded is None:
                continue
            r_idx, t_idx = decoded

            if r_idx < len(engine.robots) and t_idx < len(engine.waiting_tasks):
                robot = engine.robots[r_idx]
                task = engine.waiting_tasks[t_idx]
                dist = abs(robot.row - task.pickup[0]) + abs(robot.col - task.pickup[1])

                if dist < min_dist:
                    min_dist = dist
                    best_action = action

        return best_action
