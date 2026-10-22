# Reinforcement Learning Problem Formulation

## 1. Mathematical Formalism

We formulate multi-robot warehouse fleet coordination as a **Constrained Markov Decision Process (CMDP)** with decentralized execution and hierarchical safety enforcement:

$$\mathcal{M} = \langle \mathcal{S}, \mathcal{A}, \mathcal{P}, \mathcal{R}, \mathcal{C}, \gamma \rangle$$

where:
- $\mathcal{S}$ is the state space representing robot positions, headings, battery states, and task queues.
- $\mathcal{A}$ is the action space of discrete dispatch assignments.
- $\mathcal{P}: \mathcal{S} \times \mathcal{A} \to \Delta(\mathcal{S})$ is the transition probability governed by the discrete-event warehouse simulator.
- $\mathcal{R}: \mathcal{S} \times \mathcal{A} \times \mathcal{S} \to \mathbb{R}$ is the objective reward function promoting throughput and energy efficiency.
- $\mathcal{C}$ is a set of hard safety constraints (no spatial overlaps, no edge swaps) enforced deterministically by the underlying collision manager rather than soft penalties.
- $\gamma \in [0, 1)$ is the discount factor ($\gamma = 0.99$).

---

## 2. Observation Space ($\mathcal{S}$)

The policy receives a normalized, fixed-length observation vector $\mathbf{o} \in \mathbb{R}^{94}$ containing three structured sub-vectors:

### 2.1 Fleet State Sub-vector ($5 \text{ robots} \times 10 \text{ features} = 50$)
For each robot $i \in \{0, \dots, N-1\}$:
1. $r_i / H$: Normalized row index in $[0, 1]$.
2. $c_i / W$: Normalized column index in $[0, 1]$.
3. $\theta_i / 3$: Normalized discrete heading ($\text{East}=0, \text{South}=0.33, \text{West}=0.66, \text{North}=1.0$).
4. $b_i / 100$: Normalized battery level in $[0, 1]$.
5. $\mathbb{I}(\text{IDLE})$: One-hot indicator (1.0 if robot is available for dispatch).
6. $\mathbb{I}(\text{GOING\_TO\_PICKUP})$: One-hot indicator (1.0 if traveling to pickup location).
7. $\mathbb{I}(\text{GOING\_TO\_DROPOFF})$: One-hot indicator (1.0 if carrying payload to drop-off).
8. $\mathbb{I}(\text{CHARGING})$: One-hot indicator (1.0 if at charging dock).
9. $\mathbb{I}(\text{FAULT})$: One-hot indicator (1.0 if disabled due to battery depletion).
10. $\min(1.0, |\text{path}_i| / 100)$: Normalized remaining path distance.

### 2.2 Task Queue Sub-vector ($5 \text{ candidate tasks} \times 8 \text{ features} = 40$)
For each candidate task $j \in \{0, \dots, K-1\}$:
1. $\mathbb{I}(\text{Exists})$: 1.0 if task exists in queue, else 0.0.
2. $p_r / H$: Normalized pickup row.
3. $p_c / W$: Normalized pickup column.
4. $d_r / H$: Normalized dropoff row.
5. $d_c / W$: Normalized dropoff column.
6. $\text{priority} / 3.0$: Normalized priority ($\text{HIGH}=1.0, \text{MEDIUM}=0.66, \text{LOW}=0.33$).
7. $\min(1.0, \text{wait\_duration} / 200)$: Normalized waiting duration.
8. $\min(1.0, \|\mathbf{p} - \mathbf{d}\|_1 / 200)$: Estimated Manhattan mission distance.

### 2.3 Global Fleet & Environment Sub-vector ($4 \text{ features}$)
1. $\min(1.0, |\mathcal{Q}_{\text{wait}}| / 20)$: Normalized waiting queue backlog.
2. $\min(1.0, N_{\text{completed}} / 50)$: Normalized completed task counter.
3. $t / t_{\max}$: Normalized episode step counter.
4. $N_{\text{blocked}} / N$: Spatial congestion ratio.

---

## 3. Action Space and Invalid Action Masking ($\mathcal{A}$)

The action space consists of $1 + (N \times K) = 26$ discrete decisions:
- $a = 0$: `NO-OP` (allow all active AGVs to continue their current trajectories).
- $a \in \{1, \dots, 25\}$: Assign robot $i = \lfloor (a - 1) / K \rfloor$ to waiting task $j = (a - 1) \bmod K$.

### Invalid Action Mask $\mathbf{m}(s) \in \{0, 1\}^{26}$
An action $a$ is masked out ($\mathbf{m}[a] = 0$) if:
1. Robot $i$ is currently executing an assigned mission ($\text{task} \neq \text{None}$).
2. Robot $i$ is faulty ($\text{battery} \le 0$).
3. Robot $i$ is actively recharging ($\text{stage} = \text{CHARGING}$).
4. Robot $i$ has critically low battery ($b_i < 12.0\%$).
5. Task $j$ is not currently waiting or index exceeds the queue length.

`NO-OP` ($a = 0$) is guaranteed to always remain legal ($\mathbf{m}[0] = 1$). During policy evaluation and sampling with `MaskablePPO`, invalid action logits are forced to $-\infty$:

$$\pi(a \mid s) = \frac{\exp(z_a) \cdot \mathbf{m}[a]}{\sum_{a'} \exp(z_{a'}) \cdot \mathbf{m}[a']}$$

This mathematically guarantees $0\%$ invalid action execution.

---

## 4. Reward Formulation

The step reward $R_t$ is designed as a dense, potential-based shaping function:

$$R_t = R_{\text{delivery}} + R_{\text{pickup}} - C_{\text{motion}} - C_{\text{idle}} - C_{\text{congestion}} - C_{\text{deadlock}} - C_{\text{depletion}}$$

1. **Delivery Reward ($+20.0 \times \text{priority\_weight}$):** Strong positive incentive upon successful cargo delivery at destination.
2. **Pickup Reward ($+5.0$):** Intermediate milestone reward when the assigned AGV arrives at the item rack and begins transit.
3. **Motion Cost ($-0.04 \times N_{\text{moving}}$):** Travel cost penalizing unnecessary detours and wasteful movement.
4. **Idle Penalty ($-0.05 \times N_{\text{idle}}$ when $|\mathcal{Q}_{\text{wait}}| > 0$):** Discourages robots from idling when tasks await delivery.
5. **Congestion Penalty ($-0.20 \times N_{\text{blocked}}$):** Penalizes traffic bottlenecks where robots wait on others.
6. **Deadlock Penalty ($-1.0$):** Penalty when two or more robots enter a mutual wait cycle.
7. **Depletion Penalty ($-10.0$):** Critical penalty if an AGV exhausts its battery to $0\%$.

---

## 5. Multi-Agent CTDE Extension (MAPPO)

In the multi-agent setup:
- **Centralized Critic:** $V_\phi(S)$ takes global state $S \in \mathbb{R}^{94}$.
- **Decentralized Actor:** $\pi_\theta(a_i \mid o_i)$ takes local AGV state $o_i \in \mathbb{R}^{54}$ and outputs dispatch preferences over candidate tasks.
- **Homogeneous Parameter Sharing:** All AGVs share actor weights $\theta$, eliminating combinatorial action explosion while preserving decentralized decision autonomy.
