# Implementation Plan: RL-Based Multi-Robot Warehouse Fleet Management

This plan tracks the systematic execution of all project milestones.

---

## Phase 1: Environment & Project Audit
- [x] Inspect existing workspace, files, and benchmark map (`data/maps/raw/warehouse-10-20-10-2-1.map`).
- [x] Verify benchmark loader and scenario parsing (161x63 grid, 5,699 walkable cells, 1,000 scenarios).
- [x] Audit Python runtime (Python 3.12.10) and hardware capabilities (Intel Core Ultra 5 225H).
- [x] Verify Godot engine availability (Godot 4.7.2 stable official).
- [x] Establish dependency compatibility matrix (Torch CPU, Gymnasium, Stable-Baselines3, SB3-Contrib).
- [x] Produce `PROJECT_STATUS.md` and initial audit logs.

---

## Phase 2: Simulation Core Stabilization & Robot Dynamics
- [x] Decouple simulation engine from Pygame rendering into `core/sim_engine.py` (preserving existing `main.py`).
- [x] Implement enhanced robot dynamics in `robot.py`:
  - 4-directional heading tracking (East, South, West, North)
  - Battery accounting: discharge during motion ($0.08\%/\text{cell}$) and idle ($0.01\%/\text{step}$)
  - Dedicated charging docks ($4$ perimeter stations) and autonomous low-battery routing
  - Fault injection and recovery states
- [x] Add explicit deadlock detection and conflict resolution to `collision_manager.py`.
- [x] Write unit test suite `tests/test_simulation.py` verifying collision avoidance, pathfinding, and battery accounting (7/7 passing).

---

## Phase 3: Research-Grade Gymnasium Environment
- [x] Create `rl/environment.py` implementing the `gymnasium.Env` standard API:
  - `reset(seed=None, options=None)`
  - `step(action)`
  - `action_masks()` for SB3-Contrib
- [x] Design observation space (`rl/observations.py`):
  - 94-dimensional normalized vector (robots, candidate tasks, global queue backlog, congestion).
- [x] Design action space with invalid-action masking (`rl/actions.py`):
  - 26 discrete actions (NO-OP + 5 robots $\times$ 5 tasks).
- [x] Formulate dense, shaped reward function (`rl/rewards.py`):
  - Delivery ($+20$), pickup ($+5$), travel cost ($-0.04$), congestion penalty ($-0.20$), depletion penalty ($-10$).
- [x] Write test suite `tests/test_rl_env.py` and pass `gymnasium.utils.env_checker.check_env` (5/5 passing).

---

## Phase 4: Classical Baselines & Fair Comparison Protocol
- [x] Implement Baseline 1: Nearest-Eligible-Robot Heuristic (`baselines/nearest_robot.py`).
- [x] Implement Baseline 2: Priority-Aware Greedy Dispatcher (`baselines/priority_greedy.py`).
- [x] Implement Baseline 3: Random Dispatcher with Action Masking (`baselines/random_policy.py`).
- [x] Standardize benchmark evaluation harness (`experiments/benchmark_runner.py`) ensuring identical seeds and scenario offsets.

---

## Phase 5: PPO Training Pipeline
- [x] Implement PPO training pipeline using `MaskablePPO` from `sb3-contrib` (`rl/train_ppo.py`).
- [x] Implement evaluation callbacks, TensorBoard metric logging, and checkpointing (`rl/callbacks.py`).
- [x] Execute smoke training run (2,048 steps, 3.2s).
- [x] Execute full training experiment on benchmark scenarios (30,720 steps, 35.1s, explained variance $0.94$).
- [x] Save model checkpoints to `checkpoints/ppo/best_model.zip` and `ppo_warehouse_final.zip`.
- [x] Implement model evaluation and inference entry point (`rl/evaluate.py`).

---

## Phase 6: Multi-Agent RL (MAPPO) Architecture Extension
- [x] Formulate Centralized Training with Decentralized Execution (CTDE) multi-agent setup.
- [x] Implement parameter-shared Local Actor and Centralized Critic (`rl/mappo.py`).
- [x] Implement CTDE rollout and policy optimization loop.

---

## Phase 7: Godot 3D Visualization & Python Bridge
- [x] Implement bidirectional Python-Godot TCP telemetry bridge (`bridge/telemetry_server.py`).
- [x] Extend Godot project (`godot-warehouse3d/warehouse_scene.gd`):
  - Realistic 3D AGV chassis, 4 wheels, optical sensor puck, status glow halo, dynamic cargo crates, and floating `Label3D`
  - Real-time TCP stream client with smooth position and angular interpolation
  - In-engine HUD fleet dashboard displaying steps, throughput, conflicts, and per-robot battery cards
  - Interactive controls (Pause, Resume, Reset, Speed $1\times/2\times$, Camera Presets).
- [x] Verified Godot engine execution with Godot 4.7.2.

---

## Phase 8: Empirical Evaluation, Benchmarking & Publication Outputs
- [x] Execute comprehensive evaluation across 15 unseen benchmark scenarios (`rl/evaluate.py`).
- [x] Record quantitative metrics: completed tasks, throughput, makespan, distance, wait time, inference latency.
- [x] Generate comparative publication plots in `results/plots/` (`experiments/plot_results.py`).
- [x] Author full research documentation:
  - `README.md`
  - `PROJECT_STATUS.md`
  - `IMPLEMENTATION_PLAN.md`
  - `docs/ARCHITECTURE.md`
  - `docs/RL_PROBLEM_FORMULATION.md`
  - `docs/EXPERIMENT_PROTOCOL.md`
  - `docs/RESULTS.md`
  - `docs/TROUBLESHOOTING.md`
- [x] Full test suite verification: **15/15 tests passing**.
