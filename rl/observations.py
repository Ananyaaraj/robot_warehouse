"""
Observation builder for multi-robot warehouse fleet.
Transforms simulation state into a normalized fixed-size feature vector.
"""

from typing import List, Dict, Any
import numpy as np

from warehouse import ROWS, COLS
from core.sim_engine import WarehouseSimEngine


class ObservationBuilder:
    """
    Extracts and normalizes features from the warehouse simulation state.
    Observation layout:
      - For each robot (10 features):
        [row_norm, col_norm, heading_norm, battery_norm,
         is_idle, is_pickup, is_dropoff, is_charging, is_faulty, path_len_norm]
      - For each candidate task (8 features):
        [exists, pickup_row_norm, pickup_col_norm, dropoff_row_norm, dropoff_col_norm,
         priority_norm, wait_time_norm, distance_norm]
      - Global features (4 features):
        [queue_len_norm, completed_tasks_norm, step_norm, congestion_ratio]
    Total dimension = num_robots * 10 + num_candidate_tasks * 8 + 4
    """

    def __init__(
        self,
        num_robots: int = 5,
        num_candidate_tasks: int = 5,
        max_steps: int = 400
    ):
        self.num_robots = num_robots
        self.num_candidate_tasks = num_candidate_tasks
        self.max_steps = max_steps

        self.robot_feature_dim = 10
        self.task_feature_dim = 8
        self.global_feature_dim = 4

        self.total_dim = (
            self.num_robots * self.robot_feature_dim
            + self.num_candidate_tasks * self.task_feature_dim
            + self.global_feature_dim
        )

    def build_observation(self, engine: WarehouseSimEngine) -> np.ndarray:
        obs = np.zeros(self.total_dim, dtype=np.float32)
        idx = 0

        # 1. Robot features
        for i in range(self.num_robots):
            if i < len(engine.robots):
                r = engine.robots[i]
                obs[idx] = r.row / float(ROWS)
                obs[idx + 1] = r.col / float(COLS)
                obs[idx + 2] = r.heading / 3.0
                obs[idx + 3] = r.battery / 100.0
                obs[idx + 4] = 1.0 if r.current_task is None and not r.is_faulty else 0.0
                obs[idx + 5] = 1.0 if r.task_stage == "GOING_TO_PICKUP" else 0.0
                obs[idx + 6] = 1.0 if r.task_stage == "GOING_TO_DROPOFF" else 0.0
                obs[idx + 7] = 1.0 if r.is_charging else 0.0
                obs[idx + 8] = 1.0 if r.is_faulty else 0.0
                obs[idx + 9] = min(1.0, len(r.path) / 100.0)
            idx += self.robot_feature_dim

        # 2. Candidate waiting tasks features
        for j in range(self.num_candidate_tasks):
            if j < len(engine.waiting_tasks):
                t = engine.waiting_tasks[j]
                manhattan_dist = abs(t.pickup[0] - t.dropoff[0]) + abs(t.pickup[1] - t.dropoff[1])
                wait_duration = max(0, engine.current_step - t.creation_step)

                obs[idx] = 1.0  # task exists
                obs[idx + 1] = t.pickup[0] / float(ROWS)
                obs[idx + 2] = t.pickup[1] / float(COLS)
                obs[idx + 3] = t.dropoff[0] / float(ROWS)
                obs[idx + 4] = t.dropoff[1] / float(COLS)
                obs[idx + 5] = t.priority / 3.0
                obs[idx + 6] = min(1.0, wait_duration / 200.0)
                obs[idx + 7] = min(1.0, manhattan_dist / 200.0)
            idx += self.task_feature_dim

        # 3. Global fleet & environment features
        queue_len = len(engine.waiting_tasks)
        completed_count = len(engine.completed_tasks)
        blocked_count = sum(1 for r in engine.robots if r.blocked_steps > 0)

        obs[idx] = min(1.0, queue_len / 20.0)
        obs[idx + 1] = min(1.0, completed_count / 50.0)
        obs[idx + 2] = min(1.0, engine.current_step / float(self.max_steps))
        obs[idx + 3] = blocked_count / float(max(1, len(engine.robots)))

        return obs
