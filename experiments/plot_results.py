"""
Plotting utility for multi-robot warehouse fleet benchmark results.
Generates publication-quality figures comparing PPO vs classical baselines.
"""

import sys
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def generate_benchmark_plots(
    summary_csv: Path = None,
    episodes_csv: Path = None,
    output_dir: Path = None
):
    if output_dir is None:
        output_dir = PROJECT_ROOT / "results" / "plots"
    output_dir.mkdir(parents=True, exist_ok=True)

    if summary_csv is None:
        summary_csv = PROJECT_ROOT / "results" / "final_benchmark_summary.csv"
        if not summary_csv.exists():
            summary_csv = PROJECT_ROOT / "results" / "baseline_summary.csv"

    if episodes_csv is None:
        episodes_csv = PROJECT_ROOT / "results" / "final_benchmark_episodes.csv"
        if not episodes_csv.exists():
            episodes_csv = PROJECT_ROOT / "results" / "baseline_evaluation_episodes.csv"

    sum_df = pd.read_csv(summary_csv)
    ep_df = pd.read_csv(episodes_csv)

    # Style settings
    plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")
    colors = ["#4A90E2", "#50E3C2", "#F5A623", "#9013FE"]

    # 1. Plot Reward Comparison with Error Bars
    fig, ax = plt.subplots(figsize=(8, 5))
    policies = sum_df["policy"].tolist()
    means = sum_df["mean_reward"].tolist()
    stds = sum_df["std_reward"].tolist()
    x_pos = range(len(policies))

    bars = ax.bar(x_pos, means, yerr=stds, capsize=6, color=colors[:len(policies)], alpha=0.88, edgecolor="black")
    ax.set_xticks(x_pos)
    ax.set_xticklabels(policies, rotation=15, ha="right", fontsize=11)
    ax.set_ylabel("Mean Cumulative Episode Reward", fontsize=12)
    ax.set_title("Multi-Robot Fleet Reward Comparison (Benchmark Scenarios)", fontsize=13, fontweight="bold")

    for bar, mean in zip(bars, means):
        height = bar.get_height()
        ax.annotate(f"{mean:.1f}",
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 4),
                    textcoords="offset points",
                    ha="center", va="bottom", fontsize=10, fontweight="bold")

    plt.tight_layout()
    p1 = output_dir / "reward_comparison.png"
    plt.savefig(p1, dpi=300)
    plt.close()
    print(f"Saved: {p1}")

    # 2. Plot Throughput Comparison (Tasks per 1,000 steps)
    fig, ax = plt.subplots(figsize=(8, 5))
    throughputs = sum_df["mean_throughput"].tolist()
    bars2 = ax.bar(x_pos, throughputs, color="#2ECC71", alpha=0.85, edgecolor="black")
    ax.set_xticks(x_pos)
    ax.set_xticklabels(policies, rotation=15, ha="right", fontsize=11)
    ax.set_ylabel("Fleet Throughput (Completed Tasks / 1,000 Steps)", fontsize=12)
    ax.set_title("Fleet Mission Throughput Comparison", fontsize=13, fontweight="bold")

    for bar, tp in zip(bars2, throughputs):
        height = bar.get_height()
        ax.annotate(f"{tp:.1f}",
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 4),
                    textcoords="offset points",
                    ha="center", va="bottom", fontsize=10, fontweight="bold")

    plt.tight_layout()
    p2 = output_dir / "throughput_comparison.png"
    plt.savefig(p2, dpi=300)
    plt.close()
    print(f"Saved: {p2}")

    # 3. Plot Task Completion Distribution Boxplot
    fig, ax = plt.subplots(figsize=(9, 5))
    policy_groups = [group["completed_tasks"].values for _, group in ep_df.groupby("policy", sort=False)]
    unique_pols = ep_df["policy"].unique().tolist()

    bp = ax.boxplot(policy_groups, tick_labels=unique_pols, patch_artist=True, notch=False)
    for patch, color in zip(bp["boxes"], colors[:len(unique_pols)]):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)

    ax.set_ylabel("Completed Tasks per Episode", fontsize=12)
    ax.set_title("Distribution of Completed Tasks per Scenario", fontsize=13, fontweight="bold")
    ax.set_xticklabels(unique_pols, rotation=15, ha="right", fontsize=11)

    plt.tight_layout()
    p3 = output_dir / "task_completion_distribution.png"
    plt.savefig(p3, dpi=300)
    plt.close()
    print(f"Saved: {p3}")

    print("All benchmark plots generated successfully!")


if __name__ == "__main__":
    generate_benchmark_plots()
