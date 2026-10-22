"""
Gymnasium environment for Multi-Robot Warehouse Fleet Management.
Standardized Gymnasium interface supporting action masking for MaskablePPO.
"""

from typing import Optional, Dict, Any, Tuple
import numpy as np
import gymnasium as gym
from gymnasium import spaces

from core.sim_engine import WarehouseSimEngine
from rl.config import RLConfig
from rl.observations import ObservationBuilder
from rl.actions import ActionHandler
from rl.rewards import RewardCalculator


class WarehouseFleetEnv(gym.Env):
    """
    Gymnasium-compatible multi-robot warehouse fleet allocation environment.
    Integrates real Moving AI benchmark map and scenarios.
    """

    metadata = {"render_modes": ["human", "rgb_array"], "render_fps": 30}

    def __init__(self, config: Optional[RLConfig] = None):
        super().__init__()
        self.config = config or RLConfig()

        # Initialize simulation engine
        self.engine = WarehouseSimEngine(
            num_robots=self.config.num_robots,
            enable_battery=self.config.enable_battery,
            low_battery_threshold=self.config.low_battery_threshold,
            enforce_timer=False,
            seed=self.config.seed
        )

        self.obs_builder = ObservationBuilder(
            num_robots=self.config.num_robots,
            num_candidate_tasks=self.config.num_candidate_tasks,
            max_steps=self.config.max_steps_per_episode
        )

        self.action_handler = ActionHandler(
            num_robots=self.config.num_robots,
            num_candidate_tasks=self.config.num_candidate_tasks
        )

        self.reward_calculator = RewardCalculator()

        # Define Gym Spaces
        self.observation_space = spaces.Box(
            low=0.0,
            high=1.0,
            shape=(self.obs_builder.total_dim,),
            dtype=np.float32
        )

        self.action_space = spaces.Discrete(self.action_handler.total_actions)

        self.episode_steps = 0
        self.episode_reward = 0.0
        self.episode_completions = 0

    def action_masks(self) -> np.ndarray:
        """
        Required method for SB3-Contrib MaskablePPO.
        Returns a 1D boolean array indicating valid actions.
        """
        return self.action_handler.get_action_mask(self.engine)

    def reset(
        self,
        *,
        seed: Optional[int] = None,
        options: Optional[Dict[str, Any]] = None
    ) -> Tuple[np.ndarray, Dict[str, Any]]:
        super().reset(seed=seed)

        self.episode_steps = 0
        self.episode_reward = 0.0
        self.episode_completions = 0

        scenario_offset = 0
        if options and "scenario_offset" in options:
            scenario_offset = options["scenario_offset"]
        elif seed is not None:
            scenario_offset = seed * 7

        state = self.engine.reset(seed=seed, scenario_offset=scenario_offset)
        obs = self.obs_builder.build_observation(self.engine)

        info = {
            "step": 0,
            "waiting_tasks": len(self.engine.waiting_tasks),
            "completed_tasks": 0,
            "metrics": dict(self.engine.metrics)
        }

        return obs, info

    def step(self, action: int) -> Tuple[np.ndarray, float, bool, bool, Dict[str, Any]]:
        self.episode_steps += 1
        action_executed = False

        # 1. Decode and execute action if valid
        decoded = self.action_handler.decode_action(action)
        if decoded is not None:
            r_idx, t_idx = decoded
            if (
                r_idx < len(self.engine.robots)
                and t_idx < len(self.engine.waiting_tasks)
            ):
                robot = self.engine.robots[r_idx]
                task = self.engine.waiting_tasks[t_idx]
                if robot.current_task is None and not robot.is_faulty and not robot.is_charging:
                    success = self.engine.assign_task_to_robot(
                        robot_id=robot.robot_id,
                        task_id=task.task_id
                    )
                    action_executed = success

        # 2. Dynamic task arrival: periodic benchmark scenario injection
        if (
            self.episode_steps % self.config.task_arrival_interval == 0
            or len(self.engine.waiting_tasks) < 2
        ):
            self.engine.add_new_scenario_task()

        # 3. Step the physical simulation engine
        step_result = self.engine.step()

        # 4. Compute reward
        step_reward = self.reward_calculator.calculate_reward(
            self.engine, step_result, action_executed
        )
        self.episode_reward += step_reward
        self.episode_completions += step_result.get("step_completions", 0)

        # 5. Check termination and truncation
        terminated = False
        truncated = self.episode_steps >= self.config.max_steps_per_episode

        # 6. Build observation and info dict
        obs = self.obs_builder.build_observation(self.engine)
        info = {
            "step": self.episode_steps,
            "episode_reward": self.episode_reward,
            "episode_completions": self.episode_completions,
            "waiting_tasks": len(self.engine.waiting_tasks),
            "completed_tasks": len(self.engine.completed_tasks),
            "metrics": dict(self.engine.metrics),
            "action_mask": self.action_masks()
        }

        return obs, step_reward, terminated, truncated, info

    def render(self):
        """Optional render hook."""
        pass

    def close(self):
        pass
