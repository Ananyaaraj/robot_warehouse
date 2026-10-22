"""
Priority-Aware Greedy Task Allocation Baseline.
Prioritizes high-priority tasks and minimizes total mission delivery time.
"""

from typing import Optional
import numpy as np
from rl.environment import WarehouseFleetEnv


class PriorityGreedyPolicy:
    """
    Ranks tasks by priority tier (HIGH > MEDIUM > LOW), then pairs with the
    robot that minimizes pickup-to-dropoff mission cost.
    """

    def __init__(self, name: str = "Priority-Aware-Greedy"):
        self.name = name

    def predict(self, obs: np.ndarray, env: WarehouseFleetEnv) -> int:
        mask = env.action_masks()
        valid_actions = np.where(mask)[0]

        if len(valid_actions) == 1 and valid_actions[0] == 0:
            return 0

        engine = env.engine
        best_action = 0
        best_score = float("-inf")

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

                dist_to_pickup = abs(robot.row - task.pickup[0]) + abs(robot.col - task.pickup[1])
                dist_mission = abs(task.pickup[0] - task.dropoff[0]) + abs(task.pickup[1] - task.dropoff[1])
                total_dist = dist_to_pickup + dist_mission

                # Score function: higher priority weight, lower distance penalty
                score = (task.priority * 100.0) - total_dist

                if score > best_score:
                    best_score = score
                    best_action = action

        return best_action
