"""
PPO Training Pipeline for Multi-Robot Warehouse Fleet Management.
Uses SB3-Contrib MaskablePPO with action masking, periodic evaluation,
TensorBoard logging, and checkpoint saving.
"""

import sys
from pathlib import Path
import argparse
import json
import time

# Ensure project root in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import torch
import numpy as np
from sb3_contrib import MaskablePPO
from sb3_contrib.common.wrappers import ActionMasker
from sb3_contrib.common.maskable.callbacks import MaskableEvalCallback

from rl.environment import WarehouseFleetEnv
from rl.config import RLConfig
from rl.callbacks import WarehouseMetricsCallback


def mask_fn(env: WarehouseFleetEnv) -> np.ndarray:
    return env.action_masks()


def make_env(config: RLConfig, seed: int, scenario_offset: int = 0):
    env = WarehouseFleetEnv(config)
    env.reset(seed=seed, options={"scenario_offset": scenario_offset})
    return ActionMasker(env, mask_fn)


def train(
    smoke: bool = False,
    total_timesteps: int = 40000,
    seed: int = 42,
    resume_checkpoint: str = None,
    checkpoint_dir: Path = None,
    log_dir: Path = None
):
    if smoke:
        total_timesteps = 2048
        eval_freq = 1024
        print("\n[SMOKE RUN] Executing fast 2,048-timestep training verification...")
    else:
        eval_freq = 5000

    config = RLConfig(
        num_robots=5,
        num_candidate_tasks=5,
        max_steps_per_episode=300,
        enable_battery=True,
        seed=seed
    )

    if checkpoint_dir is None:
        checkpoint_dir = PROJECT_ROOT / "checkpoints" / "ppo"
    if log_dir is None:
        log_dir = PROJECT_ROOT / "logs" / "ppo"

    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    log_dir.mkdir(parents=True, exist_ok=True)

    # 1. Initialize training and evaluation environments
    train_env = make_env(config, seed=seed, scenario_offset=0)
    eval_env = make_env(config, seed=seed + 999, scenario_offset=500)

    # 2. Setup callbacks
    metrics_cb = WarehouseMetricsCallback(log_dir=log_dir, verbose=1)
    eval_cb = MaskableEvalCallback(
        eval_env,
        best_model_save_path=str(checkpoint_dir),
        log_path=str(log_dir),
        eval_freq=eval_freq,
        n_eval_episodes=4,
        deterministic=True,
        verbose=1
    )

    # 3. Initialize or resume PPO model
    if resume_checkpoint and Path(resume_checkpoint).exists():
        print(f"\nResuming training from checkpoint: {resume_checkpoint}")
        model = MaskablePPO.load(
            resume_checkpoint,
            env=train_env,
            tensorboard_log=str(log_dir)
        )
    else:
        print("\nInitializing new MaskablePPO policy...")
        policy_kwargs = dict(
            net_arch=dict(pi=[128, 128], vf=[128, 128]),
            activation_fn=torch.nn.ReLU
        )
        model = MaskablePPO(
            "MlpPolicy",
            train_env,
            learning_rate=config.learning_rate,
            n_steps=config.n_steps,
            batch_size=config.batch_size,
            n_epochs=config.n_epochs,
            gamma=config.gamma,
            gae_lambda=config.gae_lambda,
            clip_range=config.clip_range,
            ent_coef=config.ent_coef,
            vf_coef=config.vf_coef,
            max_grad_norm=config.max_grad_norm,
            policy_kwargs=policy_kwargs,
            tensorboard_log=str(log_dir),
            seed=seed,
            verbose=1
        )

    # 4. Save training configuration
    train_metadata = {
        "algorithm": "MaskablePPO",
        "seed": seed,
        "total_timesteps": total_timesteps,
        "n_steps": config.n_steps,
        "batch_size": config.batch_size,
        "learning_rate": config.learning_rate,
        "num_robots": config.num_robots,
        "num_candidate_tasks": config.num_candidate_tasks,
        "max_steps_per_episode": config.max_steps_per_episode,
        "enable_battery": config.enable_battery,
        "checkpoint_dir": str(checkpoint_dir),
        "log_dir": str(log_dir),
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    with open(checkpoint_dir / "training_config.json", "w", encoding="utf-8") as f:
        json.dump(train_metadata, f, indent=4)

    # 5. Train
    start_train_time = time.time()
    print(f"\nStarting training for {total_timesteps} timesteps...")
    model.learn(
        total_timesteps=total_timesteps,
        callback=[metrics_cb, eval_cb],
        reset_num_timesteps=False
    )
    duration = time.time() - start_train_time
    print(f"\nTraining completed in {duration:.1f} seconds ({duration/60.0:.2f} minutes).")

    # 6. Save final checkpoint
    final_path = checkpoint_dir / "ppo_warehouse_final"
    model.save(str(final_path))
    print(f"Final model saved to: {final_path}.zip")

    return model, final_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train PPO for Multi-Robot Warehouse")
    parser.add_argument("--smoke", action="store_true", help="Run short smoke test (2048 steps)")
    parser.add_argument("--timesteps", type=int, default=40000, help="Total training timesteps")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--resume", type=str, default=None, help="Path to checkpoint to resume")
    args = parser.parse_args()

    train(
        smoke=args.smoke,
        total_timesteps=args.timesteps,
        seed=args.seed,
        resume_checkpoint=args.resume
    )
