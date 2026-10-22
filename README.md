# Autonomous Multi-Robot Warehouse Fleet Management System
### Reinforcement Learning Coordination, Classical Baselines, and Integrated Godot 3D Visualization

An advanced, research-grade multi-robot warehouse fleet management and task allocation system powered by **Maskable Proximal Policy Optimization (PPO)**, classical dispatch heuristics, deterministic collision-aware multi-agent path coordination, and a real-time **Godot 4 3D industrial visualization**.

---

## 1. System Architecture & Highlights

```
+---------------------------------------------------------------------------------+
|                        BENCHMARK & SCENARIO ENGINE                              |
|   Moving AI Octile Map (161x63, 5699 Walkable Cells) | 1,000 Benchmark Scenarios|
+---------------------------------------------------------------------------------+
                                        │
                                        ▼
+---------------------------------------------------------------------------------+
|                         DISCRETE SIMULATION CORE                                |
|   - Multi-Robot Kinetics (Heading, Speed, Battery Discharge & Autonomous Docks) |
|   - Deterministic Collision Manager (Destination Conflict & Edge-Swap Avoidance)|
|   - A* Time-Extended Path Planning with Dynamic Obstacle Yielding               |
+---------------------------------------------------------------------------------+
           │                                                    │
           ▼                                                    ▼
+---------------------------------------+   +------------------------------------+
|       DECISION & LEARNING LAYER       |   |       LIVE 3D VISUALIZATION        |
|  - Gymnasium Environment (94-dim obs) |   |  - Godot 4.7 Industrial Warehouse  |
|  - SB3-Contrib MaskablePPO (26 acts)  |   |  - Realistic AGV Models + Status   |
|  - CTDE Multi-Agent PPO (MAPPO)       |   |  - Real-Time TCP Telemetry Stream  |
|  - Classical Heuristics (NER, PAG)    |   |  - In-Engine Fleet Dashboard / HUD |
+---------------------------------------+   +------------------------------------+
```

- **Moving AI Benchmark Fidelity:** Native integration of Moving AI warehouse map (`161 x 63` grid, 5,699 walkable cells, 4,444 obstacle cells) and 1,000 scenario missions.
- **Hierarchical Safety Invariants:** Deterministic spatial reservation and edge-swap cancellation guaranteeing $0$ collisions and $0$ deadlocks across all episodes.
- **Rigorous Action Masking:** 100% legal dispatch guarantee using `sb3-contrib`'s `MaskablePPO` over a discrete combinatorial allocation space.
- **Empirical Baseline Validation:** Strictly controlled comparisons against Random-Valid, Nearest-Eligible-Robot (NER), and Priority-Aware Greedy (PAG) heuristics across identical seeds.
- **Bi-directional Python-Godot Telemetry Bridge:** Fast, non-blocking TCP socket server streaming 60 Hz AGV coordinates, battery states, heading angles, and HUD metrics to Godot 4.7.

---

## 2. Quantitative Benchmark Results

Evaluated across **15 unseen test scenarios** (Scenarios 500–999, fleet size = 5, max steps = 350):

| Policy / Algorithm | Mean Reward (± Std) | Completed Tasks (± Std) | Fleet Throughput (Tasks / 1k steps) | Total Distance (Cells) | Mean Latency (ms) | Actual Collisions |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Random-Valid** | 155.68 ± 58.14 | 8.53 ± 2.29 | 24.38 | 1735.13 | 0.007 ms | **0** |
| **Nearest-Eligible-Robot (NER)** | **193.65 ± 71.18** | **9.93 ± 2.89** | **28.38** | 1739.33 | **0.002 ms** | **0** |
| **Priority-Aware-Greedy (PAG)** | 189.36 ± 54.64 | 9.67 ± 2.26 | 27.62 | 1739.67 | **0.002 ms** | **0** |
| **PPO-Learned** | 155.38 ± **43.90** | 8.53 ± **1.81** | 24.38 | 1736.07 | 0.256 ms | **0** |

*All results are empirically recorded in `results/final_benchmark_summary.csv` and visual charts in `results/plots/`.*

---

## 3. Directory Structure

```
d:/multi_robot/
├── main.py                     # Interactive 2D Pygame simulation entry point
├── robot.py                    # AGV kinetics, battery accounting, and heading tracking
├── task.py                     # Task lifecycle and priority progression
├── warehouse.py                # Benchmark grid loader and validity checks
├── pathfinding.py              # 4-directional A* with blocked obstacle avoidance
├── collision_manager.py        # Coordinated conflict resolution and swap prevention
├── benchmark_loader.py         # Moving AI map and scenario parser
├── pytest.ini                  # Pytest configuration
├── data/                       # Benchmark maps and 1,000 scenarios
│   ├── maps/raw/warehouse-10-20-10-2-1.map
│   └── scenarios/raw/warehouse-10-20-10-2-1-random-1.scen
├── core/                       # Decoupled simulation core
│   ├── __init__.py
│   └── sim_engine.py           # Headless WarehouseSimEngine
├── rl/                         # Reinforcement Learning Pipeline
│   ├── config.py               # Hyperparameter configuration
│   ├── observations.py         # 94-dimensional normalized observation builder
│   ├── actions.py              # Action space encoder & invalid action masking
│   ├── rewards.py              # Shaped reward engine (delivery, motion, congestion)
│   ├── environment.py          # Gymnasium WarehouseFleetEnv
│   ├── train_ppo.py            # MaskablePPO training entry point
│   ├── evaluate.py             # Side-by-side benchmark evaluation script
│   ├── callbacks.py            # TensorBoard & metrics logging callbacks
│   └── mappo.py                # Multi-Agent CTDE extension
├── baselines/                  # Classical Task Allocation Heuristics
│   ├── nearest_robot.py        # Nearest-Eligible-Robot (NER)
│   ├── priority_greedy.py      # Priority-Aware Greedy (PAG)
│   └── random_policy.py        # Random Valid Dispatcher
├── bridge/                     # Python-to-Godot Telemetry Bridge
│   └── telemetry_server.py     # Non-blocking TCP state broadcaster & command listener
├── godot-warehouse3d/          # Godot 4.7 3D Industrial Warehouse Project
│   ├── project.godot           # Godot project settings (OpenGL Compatibility)
│   ├── main.tscn               # Main 3D warehouse scene
│   └── warehouse_scene.gd      # Scene generator, realistic AGVs, and live HUD
├── experiments/                # Experiment harnesses & plotting
│   ├── benchmark_runner.py     # Classical baselines evaluator
│   └── plot_results.py         # Publication figure generator
├── tests/                      # Comprehensive Unit Test Suite (15/15 passing)
│   ├── test_env_stack.py
│   ├── test_simulation.py
│   ├── test_rl_env.py
│   └── test_bridge.py
├── results/                    # Machine-readable evaluation logs and charts
│   ├── baseline_summary.csv
│   ├── final_benchmark_summary.csv
│   └── plots/                  # Generated comparison graphs
└── docs/                       # Research documentation
    ├── ARCHITECTURE.md
    ├── RL_PROBLEM_FORMULATION.md
    ├── EXPERIMENT_PROTOCOL.md
    ├── RESULTS.md
    └── TROUBLESHOOTING.md
```

---

## 4. Quickstart Guide (Windows PowerShell)

All commands are tested and verified with Python 3.12.10 in `.\venv`.

### 4.1 Run the Full Test Suite
Executes 15 comprehensive tests covering kinetics, collisions, Gymnasium specifications, and the telemetry bridge:
```powershell
.\venv\Scripts\python.exe -m pytest tests -v
```

### 4.2 Run Classical Baselines Evaluation
Runs Random-Valid, Nearest-Eligible-Robot, and Priority-Aware-Greedy:
```powershell
.\venv\Scripts\python.exe experiments\benchmark_runner.py
```

### 4.3 Train PPO Model
```powershell
# Quick verification smoke test (2,048 steps):
.\venv\Scripts\python.exe rl\train_ppo.py --smoke

# Full training experiment (30,000 timesteps):
.\venv\Scripts\python.exe rl\train_ppo.py --timesteps 30000 --seed 101
```

### 4.4 Evaluate Trained Policy vs. Baselines
```powershell
.\venv\Scripts\python.exe rl\evaluate.py --checkpoint checkpoints\ppo\best_model.zip --episodes 15 --seed 8888
```

### 4.5 Generate Publication Graphs
```powershell
.\venv\Scripts\python.exe experiments\plot_results.py
```

### 4.6 Launch Interactive 2D Pygame Simulation
```powershell
.\venv\Scripts\python.exe main.py
```
*Keybindings: `1-5` select robot, Left Click moves idle robot, `A` assigns task, `T` generates new task.*

### 4.7 Launch Integrated Godot 4 3D Visualization

**Step 1: Start the Python Telemetry Server**
```powershell
.\venv\Scripts\python.exe bridge\telemetry_server.py
```

**Step 2: Launch Godot 4.7 3D Client**
```powershell
& "C:\Users\Ananyaa\Downloads\Godot_v4.7.2-stable_win64.exe\Godot_v4.7.2-stable_win64_console.exe" --path "godot-warehouse3d"
```
*In Godot:*
- **Camera Presets:**
  - Press `1` for Isometric High Overview
  - Press `2` for Top-down Bird's Eye View
  - Press `3` to Follow **Robot R1**
  - Press `4` to Follow **Robot R2**
  - Press `5` to Follow **Robot R3**
  - Press `6` to Follow **Robot R4**
  - Press `7` to Follow **Robot R5**
  - *(Or simply click any Robot Card or Camera Button on the HUD!)*
- **3D Source & Destination Beacons:**
  - 📍 **Green glowing pillars & rings:** Active Pickup locations labeled with Task ID and priority.
  - 🎯 **Red/Orange glowing beacons:** Active Dropoff destination locations.
  - ⏳ **Yellow markers:** Queued waiting tasks.
- **Interactive Task Dispatcher:**
  - Select Source, Destination, Priority (HIGH, MEDIUM, LOW), and Target AGV (Auto RL or specific Robot R1..R5), then click **🚀 Dispatch Custom Task**!
- **Fleet Analytics & RL Monitor:**
  - 🏆 **Best Robot Trophy:** Real-time top performer by deliveries and efficiency.
  - 🧠 **RL Agent Monitor:** Live decision stream, action masking ratio, step rewards, and cumulative reward.
- **Playback Controls:**
  - Press `Space` to Pause / Resume simulation.
  - Press `R` to Reset simulation.
  - Speed toggle button: Normal ($1\times$), Slow ($0.5\times$), Fast ($2\times$).

---

## 5. Research Documentation

For detailed scientific descriptions, consult:
- [`docs/ARCHITECTURE.md`](file:///d:/multi_robot/docs/ARCHITECTURE.md): Multi-layer system design, coordinate conversions, and safety guarantees.
- [`docs/RL_PROBLEM_FORMULATION.md`](file:///d:/multi_robot/docs/RL_PROBLEM_FORMULATION.md): CMDP mathematical formalism, observation features, action masking, and dense rewards.
- [`docs/EXPERIMENT_PROTOCOL.md`](file:///d:/multi_robot/docs/EXPERIMENT_PROTOCOL.md): Benchmark partitioning, metric definitions, and reproducibility protocol.
- [`docs/RESULTS.md`](file:///d:/multi_robot/docs/RESULTS.md): In-depth statistical analysis, performance trade-offs, and empirical insights.
- [`docs/TROUBLESHOOTING.md`](file:///d:/multi_robot/docs/TROUBLESHOOTING.md): Operational guide for network ports, drivers, and dependencies.
