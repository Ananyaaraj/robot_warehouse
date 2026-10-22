"""
Benchmark evaluation runner for classical baselines and learned RL policies.
Ensures strictly identical starting seeds, scenarios, and safety constraints.
"""

from typing import List, Dict, Any, Optional
import time
import json
import sys
from pathlib import Path

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np
import pandas as pd

from rl.environment import WarehouseFleetEnv
from rl.config import RLConfig
from baselines.nearest_robot import NearestRobotPolicy
from baselines.priority_greedy import PriorityGreedyPolicy
from baselines.random_policy import RandomMaskedPolicy


def evaluate_policy(
    policy,
    env: WarehouseFleetEnv,
    num_episodes: int = 10,
    base_seed: int = 1000,
    is_sb3_model: bool = False
) -> Dict[str, Any]:
    """
    Evaluates a policy across deterministic episodes.
    Returns per-episode results and aggregate summary statistics.
    """
    policy_name = getattr(policy, "name", policy.__class__.__name__)
    episode_records = []

    for ep in range(num_episodes):
        ep_seed = base_seed + ep * 13
        scenario_offset = (base_seed + ep * 37) % 800

        obs, info = env.reset(seed=ep_seed, options={"scenario_offset": scenario_offset})
        ep_reward = 0.0
        step_count = 0
        inference_times = []

        terminated = False
        truncated = False

        while not (terminated or truncated):
            start_time = time.perf_counter()

            if is_sb3_model:
                action_masks = env.action_masks()
                action, _ = policy.predict(obs, action_masks=action_masks, deterministic=True)
                action = int(action)
            elif hasattr(policy, "predict"):
                action = policy.predict(obs, env)
            else:
                action = 0

            inf_time = (time.perf_counter() - start_time) * 1000.0
            inference_times.append(inf_time)

            obs, reward, terminated, truncated, info = env.step(action)
            ep_reward += reward
            step_count += 1

        engine_metrics = info["metrics"]
        completed = engine_metrics["completed_tasks"]
        throughput = (completed / max(1, step_count)) * 1000.0

        rec = {
            "policy": policy_name,
            "episode": ep + 1,
            "seed": ep_seed,
            "steps": step_count,
            "reward": round(ep_reward, 2),
            "completed_tasks": completed,
            "throughput_per_1k_steps": round(throughput, 2),
            "total_distance": engine_metrics["total_distance"],
            "total_wait_time": engine_metrics["total_wait_time"],
            "conflicts_resolved": engine_metrics["conflicts_resolved"],
            "swaps_prevented": engine_metrics["swaps_prevented"],
            "deadlocks_detected": engine_metrics["deadlocks_detected"],
            "battery_depletions": engine_metrics["battery_depletions"],
            "mean_inference_ms": round(float(np.mean(inference_times)), 3)
        }
        episode_records.append(rec)

    df = pd.DataFrame(episode_records)
    summary = {
        "policy": policy_name,
        "episodes": num_episodes,
        "mean_reward": round(float(df["reward"].mean()), 2),
        "std_reward": round(float(df["reward"].std()), 2),
        "mean_completed_tasks": round(float(df["completed_tasks"].mean()), 2),
        "std_completed_tasks": round(float(df["completed_tasks"].std()), 2),
        "mean_throughput": round(float(df["throughput_per_1k_steps"].mean()), 2),
        "mean_distance": round(float(df["total_distance"].mean()), 2),
        "mean_wait_time": round(float(df["total_wait_time"].mean()), 2),
        "total_swaps_prevented": int(df["swaps_prevented"].sum()),
        "total_deadlocks": int(df["deadlocks_detected"].sum()),
        "mean_inference_ms": round(float(df["mean_inference_ms"].mean()), 3)
    }

    return {"records": episode_records, "summary": summary, "dataframe": df}


def run_all_baselines(num_episodes: int = 10, output_dir: Optional[Path] = None):
    if output_dir is None:
        output_dir = Path(__file__).resolve().parent.parent / "results"
    output_dir.mkdir(parents=True, exist_ok=True)

    config = RLConfig(
        num_robots=5,
        num_candidate_tasks=5,
        max_steps_per_episode=300,
        enable_battery=True
    )
    env = WarehouseFleetEnv(config)

    policies = [
        RandomMaskedPolicy(name="Random-Valid"),
        NearestRobotPolicy(name="Nearest-Eligible-Robot"),
        PriorityGreedyPolicy(name="Priority-Aware-Greedy")
    ]

    all_summaries = []
    all_dfs = []

    print(f"\n=======================================================")
    print(f"RUNNING CLASSICAL BASELINES EVALUATION ({num_episodes} EPISODES)")
    print(f"=======================================================")

    for pol in policies:
        print(f"\nEvaluating {pol.name}...")
        res = evaluate_policy(pol, env, num_episodes=num_episodes, base_seed=5000)
        all_summaries.append(res["summary"])
        all_dfs.append(res["dataframe"])
        print(f"  Summary: {res['summary']}")

    combined_df = pd.concat(all_dfs, ignore_index=True)
    csv_path = output_dir / "baseline_evaluation_episodes.csv"
    combined_df.to_csv(csv_path, index=False)

    summary_df = pd.DataFrame(all_summaries)
    summary_path = output_dir / "baseline_summary.csv"
    summary_df.to_csv(summary_path, index=False)

    print(f"\nResults saved to:")
    print(f"  {csv_path}")
    print(f"  {summary_path}")

    return summary_df


if __name__ == "__main__":
    run_all_baselines(num_episodes=5)
