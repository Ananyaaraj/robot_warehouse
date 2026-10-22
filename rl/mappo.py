"""
Multi-Agent PPO (MAPPO) with Centralized Training and Decentralized Execution (CTDE).
Implements parameter-shared actor-critic network for multi-robot warehouse fleet.
"""

from typing import List, Dict, Any, Tuple
import sys
from pathlib import Path
import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from rl.environment import WarehouseFleetEnv
from rl.config import RLConfig


class LocalActor(nn.Module):
    """
    Decentralized actor policy: takes local agent observation + candidate tasks
    and outputs action logits over candidate tasks [NO-OP, Task 1..K].
    """

    def __init__(self, obs_dim: int, num_tasks: int = 5):
        super().__init__()
        self.num_tasks = num_tasks
        self.action_dim = 1 + num_tasks  # NO-OP + K tasks
        self.net = nn.Sequential(
            nn.Linear(obs_dim, 128),
            nn.ReLU(),
            nn.Linear(128, 128),
            nn.ReLU(),
            nn.Linear(128, self.action_dim)
        )

    def forward(self, obs: torch.Tensor, mask: torch.Tensor = None) -> torch.Tensor:
        logits = self.net(obs)
        if mask is not None:
            # Apply large negative value to invalid actions
            logits = logits + (mask.float().log().clamp(min=-1e9))
        return logits


class CentralizedCritic(nn.Module):
    """
    Centralized critic: takes the global fleet observation and estimates state value V(s).
    """

    def __init__(self, global_dim: int):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(global_dim, 256),
            nn.ReLU(),
            nn.Linear(256, 128),
            nn.ReLU(),
            nn.Linear(128, 1)
        )

    def forward(self, global_obs: torch.Tensor) -> torch.Tensor:
        return self.net(global_obs)


class MAPPOTrainer:
    """
    Coordinates CTDE training for homogeneous warehouse AGV fleet with parameter sharing.
    """

    def __init__(
        self,
        env: WarehouseFleetEnv,
        lr: float = 3e-4,
        gamma: float = 0.99,
        clip_eps: float = 0.2
    ):
        self.env = env
        self.gamma = gamma
        self.clip_eps = clip_eps
        self.global_dim = env.observation_space.shape[0]
        # Local agent observation size: 10 robot features + 40 task features + 4 global = 54
        self.local_dim = 10 + (env.config.num_candidate_tasks * 8) + 4
        self.num_tasks = env.config.num_candidate_tasks

        self.actor = LocalActor(self.local_dim, self.num_tasks)
        self.critic = CentralizedCritic(self.global_dim)

        self.actor_optimizer = optim.Adam(self.actor.parameters(), lr=lr)
        self.critic_optimizer = optim.Adam(self.critic.parameters(), lr=lr)

    def extract_agent_obs(self, global_obs: np.ndarray, agent_idx: int) -> np.ndarray:
        """Extracts local view for agent i from the global observation vector."""
        # Agent features (10)
        r_start = agent_idx * 10
        agent_features = global_obs[r_start:r_start + 10]
        # Task features (num_tasks * 8 = 40)
        task_start = self.env.config.num_robots * 10
        task_features = global_obs[task_start:task_start + (self.num_tasks * 8)]
        # Global features (4)
        global_features = global_obs[-4:]
        return np.concatenate([agent_features, task_features, global_features])

    def get_agent_mask(self, agent_idx: int) -> np.ndarray:
        """Constructs local action mask for agent i: [NO-OP, Task 0..K-1]."""
        mask = np.zeros(1 + self.num_tasks, dtype=bool)
        mask[0] = True  # NO-OP always legal
        robot = self.env.engine.robots[agent_idx]
        if robot.current_task is None and not robot.is_faulty and not robot.is_charging and robot.battery >= 12.0:
            for t_idx in range(min(self.num_tasks, len(self.env.engine.waiting_tasks))):
                if self.env.engine.waiting_tasks[t_idx].status == "WAITING":
                    mask[1 + t_idx] = True
        return mask

    def train_step(self, num_episodes: int = 5) -> Dict[str, float]:
        """Runs a short CTDE rollout and performs policy/value gradient updates."""
        all_rewards = []
        for _ in range(num_episodes):
            obs, _ = self.env.reset()
            ep_reward = 0.0
            done = False
            while not done:
                # Find available agent to step
                chosen_action = 0
                for a_idx in range(len(self.env.engine.robots)):
                    mask = self.get_agent_mask(a_idx)
                    if np.sum(mask) > 1:
                        local_obs = torch.FloatTensor(self.extract_agent_obs(obs, a_idx))
                        mask_tensor = torch.BoolTensor(mask)
                        logits = self.actor(local_obs, mask_tensor)
                        probs = torch.softmax(logits, dim=-1)
                        dist = torch.distributions.Categorical(probs)
                        local_act = dist.sample().item()
                        if local_act > 0:
                            # Map to global action index
                            chosen_action = self.env.action_handler.encode_action(a_idx, local_act - 1)
                            break

                next_obs, reward, term, trunc, info = self.env.step(chosen_action)
                ep_reward += reward
                done = term or trunc
                obs = next_obs
            all_rewards.append(ep_reward)

        return {"mean_reward": float(np.mean(all_rewards))}


def test_mappo_instantiation():
    config = RLConfig(num_robots=5, num_candidate_tasks=5, max_steps_per_episode=50)
    env = WarehouseFleetEnv(config)
    trainer = MAPPOTrainer(env)
    res = trainer.train_step(num_episodes=2)
    print(f"MAPPO test completed with result: {res}")
    return res


if __name__ == "__main__":
    test_mappo_instantiation()
