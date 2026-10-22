import pytest
import numpy as np
import gymnasium as gym
from gymnasium.utils.env_checker import check_env

from rl.environment import WarehouseFleetEnv
from rl.config import RLConfig


def test_env_spaces():
    config = RLConfig(num_robots=5, num_candidate_tasks=5, max_steps_per_episode=100)
    env = WarehouseFleetEnv(config)

    assert isinstance(env.observation_space, gym.spaces.Box)
    assert env.observation_space.dtype == np.float32
    assert env.observation_space.shape == (94,)

    assert isinstance(env.action_space, gym.spaces.Discrete)
    assert env.action_space.n == 26


def test_env_reset():
    config = RLConfig(num_robots=5, num_candidate_tasks=5, max_steps_per_episode=100, seed=42)
    env = WarehouseFleetEnv(config)
    obs, info = env.reset(seed=42)

    assert obs.shape == (94,)
    assert np.all(obs >= 0.0) and np.all(obs <= 1.0)
    assert "waiting_tasks" in info
    assert "metrics" in info


def test_action_masking():
    config = RLConfig(num_robots=5, num_candidate_tasks=5, max_steps_per_episode=100)
    env = WarehouseFleetEnv(config)
    env.reset(seed=42)

    mask = env.action_masks()
    assert isinstance(mask, np.ndarray)
    assert mask.shape == (26,)
    assert mask.dtype == bool
    # Action 0 (NO-OP) must always be legal
    assert bool(mask[0]) is True
    # At start with idle robots and waiting tasks, some dispatch actions must be legal
    assert int(np.sum(mask)) > 1


def test_env_step_masked_rollout():
    config = RLConfig(num_robots=3, num_candidate_tasks=3, max_steps_per_episode=50, seed=123)
    env = WarehouseFleetEnv(config)
    obs, _ = env.reset(seed=123)

    total_reward = 0.0
    for step in range(50):
        mask = env.action_masks()
        valid_actions = np.where(mask)[0]
        action = np.random.choice(valid_actions)

        obs, reward, terminated, truncated, info = env.step(action)
        total_reward += reward

        assert obs.shape == env.observation_space.shape
        assert isinstance(reward, float)
        assert isinstance(terminated, bool)
        assert isinstance(truncated, bool)

    assert truncated is True, "Episode should truncate at max_steps_per_episode"


def test_gym_env_checker():
    # Verify environment follows gymnasium specifications
    config = RLConfig(num_robots=3, num_candidate_tasks=3, max_steps_per_episode=30)
    env = WarehouseFleetEnv(config)
    check_env(env.unwrapped, skip_render_check=True)
