"""
Evaluation script for comparing trained PPO policy against classical baselines.
Generates comprehensive comparative tables and figures.
"""

import sys
from pathlib import Path
import argparse
import json
import pandas as pd
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from sb3_contrib import MaskablePPO
from rl.environment import WarehouseFleetEnv
from rl.config import RLConfig
from baselines.nearest_robot import NearestRobotPolicy
from baselines.priority_greedy import PriorityGreedyPolicy
from baselines.random_policy import RandomMaskedPolicy
from experiments.benchmark_runner import evaluate_policy


def evaluate_all(
    checkpoint_path: Path,
    num_episodes: int = 15,
    base_seed: int = 7777,
    output_dir: Path = None
):
    if output_dir is None:
        output_dir = PROJECT_ROOT / "results"
    output_dir.mkdir(parents=True, exist_ok=True)

    config = RLConfig(
        num_robots=5,
        num_candidate_tasks=5,
        max_steps_per_episode=350,
        enable_battery=True
    )
    env = WarehouseFleetEnv(config)

    # 1. Load trained PPO model
    print(f"\nLoading trained PPO model from: {checkpoint_path}")
    ppo_model = MaskablePPO.load(str(checkpoint_path))
    ppo_model.name = "PPO-Learned"

    # 2. Define all benchmark contestants
    contestants = [
        ("Random-Valid", RandomMaskedPolicy(name="Random-Valid"), False),
        ("Nearest-Eligible-Robot", NearestRobotPolicy(name="Nearest-Eligible-Robot"), False),
        ("Priority-Aware-Greedy", PriorityGreedyPolicy(name="Priority-Aware-Greedy"), False),
        ("PPO-Learned", ppo_model, True)
    ]

    all_summaries = []
    all_dfs = []

    print("\n" + "=" * 65)
    print(f"BENCHMARK EVALUATION ACROSS {num_episodes} UNSEEN TEST SCENARIOS")
    print("=" * 65)

    for name, policy, is_sb3 in contestants:
        print(f"\n--> Evaluating {name}...")
        res = evaluate_policy(
            policy=policy,
            env=env,
            num_episodes=num_episodes,
            base_seed=base_seed,
            is_sb3_model=is_sb3
        )
        all_summaries.append(res["summary"])
        all_dfs.append(res["dataframe"])
        print(f"    Mean Reward: {res['summary']['mean_reward']} +/- {res['summary']['std_reward']}")
        print(f"    Mean Completed: {res['summary']['mean_completed_tasks']} +/- {res['summary']['std_completed_tasks']}")
        print(f"    Mean Throughput: {res['summary']['mean_throughput']} tasks / 1000 steps")

    # Combine dataframes
    all_episodes_df = pd.concat(all_dfs, ignore_index=True)
    summary_df = pd.DataFrame(all_summaries)

    ep_path = output_dir / "final_benchmark_episodes.csv"
    summary_path = output_dir / "final_benchmark_summary.csv"
    all_episodes_df.to_csv(ep_path, index=False)
    summary_df.to_csv(summary_path, index=False)

    print("\n" + "=" * 65)
    print("FINAL COMPARATIVE RESULTS TABLE")
    print("=" * 65)
    print(summary_df.to_string(index=False))

    return summary_df


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate PPO vs Baselines")
    parser.add_argument(
        "--checkpoint",
        type=str,
        default=str(PROJECT_ROOT / "checkpoints" / "ppo" / "best_model.zip"),
        help="Path to trained PPO model zip"
    )
    parser.add_argument("--episodes", type=int, default=10, help="Number of test episodes")
    parser.add_argument("--seed", type=int, default=7777, help="Base evaluation seed")
    args = parser.parse_args()

    ckpt = Path(args.checkpoint)
    if not ckpt.exists():
        fallback = PROJECT_ROOT / "checkpoints" / "ppo" / "ppo_warehouse_final.zip"
        if fallback.exists():
            ckpt = fallback
        else:
            raise FileNotFoundError(f"Checkpoint not found: {ckpt}")

    evaluate_all(ckpt, num_episodes=args.episodes, base_seed=args.seed)
