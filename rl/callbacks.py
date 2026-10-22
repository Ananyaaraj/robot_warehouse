"""
Custom callbacks for training monitoring, metrics logging, and checkpointing.
"""

from typing import Optional
from pathlib import Path
import numpy as np
from stable_baselines3.common.callbacks import BaseCallback


class WarehouseMetricsCallback(BaseCallback):
    """
    Logs warehouse-specific fleet performance metrics to TensorBoard and memory.
    """

    def __init__(self, log_dir: Optional[Path] = None, verbose: int = 0):
        super().__init__(verbose)
        self.log_dir = log_dir
        self.episode_rewards = []
        self.episode_completions = []
        self.episode_throughputs = []

    def _on_step(self) -> bool:
        # Inspect info dict for episode completion
        infos = self.locals.get("infos", [])
        for info in infos:
            if "episode_reward" in info and (self.locals.get("dones", [False])[0]):
                ep_reward = info["episode_reward"]
                completed = info.get("episode_completions", 0)
                steps = info.get("step", 1)
                throughput = (completed / max(1, steps)) * 1000.0

                self.episode_rewards.append(ep_reward)
                self.episode_completions.append(completed)
                self.episode_throughputs.append(throughput)

                if self.logger:
                    self.logger.record("fleet/episode_reward", ep_reward)
                    self.logger.record("fleet/completed_tasks", completed)
                    self.logger.record("fleet/throughput_per_1k", throughput)

                    metrics = info.get("metrics", {})
                    self.logger.record("fleet/total_distance", metrics.get("total_distance", 0))
                    self.logger.record("fleet/conflicts_resolved", metrics.get("conflicts_resolved", 0))
                    self.logger.record("fleet/swaps_prevented", metrics.get("swaps_prevented", 0))
                    self.logger.record("fleet/deadlocks_detected", metrics.get("deadlocks_detected", 0))

        return True
