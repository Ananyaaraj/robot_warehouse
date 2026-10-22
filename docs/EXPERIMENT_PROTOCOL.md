# Benchmark Experiment Protocol & Reproducibility Guide

## 1. Benchmark Map and Scenario Specifications

- **Map File:** `data/maps/raw/warehouse-10-20-10-2-1.map` (Moving AI Octile Format)
  - Dimensions: $161 \times 63$ (Width $\times$ Height)
  - Walkable Cells: 5,699
  - Obstacle Cells: 4,444
- **Scenario File:** `data/scenarios/raw/warehouse-10-20-10-2-1-random-1.scen`
  - Total Scenarios: 1,000 independent pickup-delivery pairs with verified optimal path distances.
- **Dataset Partitioning:**
  - *Training Set:* Scenarios 0 to 499 (scenario offset cursor $\in [0, 499]$)
  - *Unseen Test Evaluation Set:* Scenarios 500 to 999 (offset cursor $\in [500, 999]$)
  - *Strict Invariant:* Test scenarios are never used during PPO training.

---

## 2. Experimental Setup & Controls

To ensure scientific rigor and fairness, all baseline heuristics and the trained RL policy are subjected to strictly identical test environments:
1. **Fleet Size:** 5 robots ($R_1, \dots, R_5$).
2. **Initial Positions:** Derived deterministically from scenario start positions with identical seeds.
3. **Episode Length:** $T_{\max} = 350$ discrete simulation steps.
4. **Battery Accounting:** Enabled ($100.0\%$ initial, $0.08\%$ drain/move, $0.01\%$ drain/idle, $1.5\%$ charge rate at designated charging docks).
5. **Safety Constraints:** All methods pass through the identical collision manager (`collision_manager.py`).

---

## 3. Evaluation Metrics Definition

| Metric | Definition | Units | Optimization Goal |
| :--- | :--- | :--- | :--- |
| **Completed Tasks** | Total delivery missions fulfilled within the episode | Count | Higher is better |
| **Throughput** | $\frac{N_{\text{completed}}}{T_{\text{steps}}} \times 1000$ | Tasks / 1,000 steps | Higher is better |
| **Episode Reward** | Cumulative shaped reward accrued by the fleet | Scalar | Higher is better |
| **Travel Distance** | Total Manhattan cells traversed across all AGVs | Cells | Lower is better (efficiency) |
| **Fleet Wait Time** | Total steps spent waiting due to conflicts or idle states | Steps | Lower is better |
| **Swap Collisions Prevented**| Total head-on swap maneuvers arrested by safety layer | Events | Safety verification ($= 0$ actual collisions) |
| **Deadlocks Detected** | Number of persistent blocked cycles recovered | Events | Lower is better ($= 0$) |
| **Inference Latency** | Time taken by algorithm to compute next action | Milliseconds | Lower is better |

---

## 4. Execution Commands (Windows PowerShell)

### Run Unit Test Suite
```powershell
.\venv\Scripts\python.exe -m pytest tests -v
```

### Run Classical Baselines Evaluation (5 Episodes)
```powershell
.\venv\Scripts\python.exe experiments\benchmark_runner.py
```

### Train MaskablePPO Policy
```powershell
# Short smoke verification (2,048 steps)
.\venv\Scripts\python.exe rl\train_ppo.py --smoke

# Full training run (30,000 timesteps)
.\venv\Scripts\python.exe rl\train_ppo.py --timesteps 30000 --seed 101
```

### Run Comparative Benchmark Evaluation
```powershell
.\venv\Scripts\python.exe rl\evaluate.py --checkpoint checkpoints\ppo\best_model.zip --episodes 15 --seed 8888
```

### Generate Comparative Plots
```powershell
.\venv\Scripts\python.exe experiments\plot_results.py
```

### Launch Godot 3D Telemetry Simulation
```powershell
# Terminal 1: Launch Python Telemetry Server
.\venv\Scripts\python.exe bridge\telemetry_server.py

# Terminal 2: Launch Godot 3D Visualization
& "C:\Users\Ananyaa\Downloads\Godot_v4.7.2-stable_win64.exe\Godot_v4.7.2-stable_win64_console.exe" --path "godot-warehouse3d"
```
