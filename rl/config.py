"""
Configuration parameters for RL training, evaluation, and simulation.
"""

from dataclasses import dataclass
from pathlib import Path


@dataclass
class RLConfig:
    # Fleet & Environment
    num_robots: int = 5
    num_candidate_tasks: int = 5
    max_steps_per_episode: int = 400
    enable_battery: bool = True
    low_battery_threshold: float = 18.0
    task_arrival_interval: int = 40  # steps between new task generation

    # PPO Hyperparameters
    learning_rate: float = 3e-4
    n_steps: int = 1024  # Rollout length
    batch_size: int = 64
    n_epochs: int = 10
    gamma: float = 0.99
    gae_lambda: float = 0.95
    clip_range: float = 0.2
    ent_coef: float = 0.01
    vf_coef: float = 0.5
    max_grad_norm: float = 0.5

    # Training Schedule
    total_timesteps: int = 60000
    eval_freq: int = 5000
    eval_episodes: int = 5
    save_freq: int = 10000
    seed: int = 42

    # Paths
    project_root: Path = Path(__file__).resolve().parent.parent
    checkpoint_dir: Path = project_root / "checkpoints" / "ppo"
    log_dir: Path = project_root / "logs" / "ppo"
    results_dir: Path = project_root / "results"
