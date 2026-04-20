# HackOps RL Brain Training: Complete Documentation

> **Source**: All data in this document is extracted directly from the executed notebook
> [`api/Red_Agent_Training.ipynb`](api/Red_Agent_Training.ipynb) and the saved result artifacts
> in `api/results/red_agent/`.

---

## Table of Contents

1. [Objective](#1-objective)
2. [Environment Design](#2-environment-design)
3. [Step 1: Setup and Reproducibility](#3-step-1-setup-and-reproducibility)
4. [Step 2: Baseline Evaluation (Random Agent)](#4-step-2-baseline-evaluation-random-agent)
5. [Step 3: Vanilla PPO Training](#5-step-3-vanilla-ppo-training)
6. [Step 4: Recurrent PPO (LSTM) Training](#6-step-4-recurrent-ppo-lstm-training)
7. [Step 5: Model Saving and Archival](#7-step-5-model-saving-and-archival)
8. [Step 6: Visualization and Analysis](#8-step-6-visualization-and-analysis)
9. [Step 7: Final Tournament Comparison](#9-step-7-final-tournament-comparison)
10. [Step 8: Detailed Inference Playback](#10-step-8-detailed-inference-playback)
11. [Key Findings and Conclusions](#11-key-findings-and-conclusions)
12. [Saved Artifacts](#12-saved-artifacts)

---

## 1. Objective

The goal of the RL Brain training phase was to create a **strategic decision-making agent** for the Red Team (Attacker) that learns to:

1. **Discover** vulnerable pages through intelligent fuzzing (not random scanning).
2. **Verify** vulnerabilities by matching fuzz signals to attack types.
3. **Exploit** only confirmed targets using the correct attack class (SQLi vs. XSS).
4. **Avoid** wasteful actions: blind exploitation, redundant fuzzing, and action repetition.

The agent is trained using **Proximal Policy Optimization (PPO)** from the Stable-Baselines3 library. Two architectural variants were trained and compared:

- **Vanilla PPO** (MlpPolicy) — A stateless, reactive agent.
- **Recurrent PPO** (MlpLstmPolicy) — A memory-augmented agent using LSTM cells that can remember past actions within an episode.

---

## 2. Environment Design

### 2.1 Observation Space

```
Box(-1.0, 3.0, shape=(60,), dtype=float32)
```

The agent observes a **60-dimensional vector** consisting of:

| Segment | Dimensions | Content |
|---------|-----------|---------|
| Vulnerability Status | 40 (20 slots x 2) | `[IsPatched, IsExploited]` per vulnerability slot. **Note**: `IsActive` was deliberately REMOVED to prevent the "cheat bit" problem. |
| Page Fuzz Signals | 20 (20 location slots x 1) | Signal value per page location. `-1.0` = not yet fuzzed; `0.0` = fuzzed, nothing found; `1.0` = SQL error detected; `2.0` = XSS reflection detected. |

The observation design is **ID-blind**: the agent never sees *which* vulnerability is active. It only sees the results of its own actions (fuzz signals, exploit outcomes).

### 2.2 Action Space

```
Discrete(82)
```

The agent can choose from **82 discrete actions**, expanded from:

| Action Type | Parameters | Count |
|------------|-----------|-------|
| `DVWASmartExploitAction` | location (15 pages) x attack_type (SQLi, XSS) | 30 |
| `DVWAFuzzAction` | location (15 pages) x fuzz_type (SQLi, XSS, None) | 45 |
| `DVWAPortScanAction` | (no params) | 1 |
| `DVWADirectoryDiscoveryAction` | (no params) | 1 |
| Other parameter combinations | | ~5 |

### 2.3 Reward Structure

The reward function enforces the **professional Recon -> Verify -> Exploit** workflow:

| Action | Condition | Reward | Purpose |
|--------|-----------|--------|---------|
| **Fuzz** (first time, signal found) | New discovery | **+50.0** | Encourage exploration |
| **Fuzz** (repeated on same page) | Redundant | **-10.0** | Prevent reward farming |
| **Fuzz** (no signal found) | Dead end | **-0.5** | Small cost for intel gathering |
| **SmartExploit** (correct signal + success) | Full workflow | **+500.0** | The JACKPOT for professional behavior |
| **SmartExploit** (page not fuzzed) | Blind attack | **-15.0** | Heavy penalty for unprofessional behavior |
| **SmartExploit** (wrong attack type for signal) | Mismatch | **-2.0** | Penalty for wrong technique |
| **Port Scan** (first time) | Discovery | **+10.0** | Reward for recon |
| **Directory Discovery** (first time) | Discovery | **+15.0** | Reward for recon |
| **Any repeated action** | Progressive penalty | **-3.0 * repeat_count** (capped at -50) | Prevent "thrashing" loops |

### 2.4 Episode Dynamics

- Each episode uses **dynamically generated vulnerabilities** (3-8 random vulns per episode via `generate_vulns_focused.py`).
- Vulnerability assignments to pages are randomized by seed.
- Allowed attack types: **SQLi and XSS only**.
- The Blue Agent (defender) acts as a **random opponent** during Red training.
- Episode ends when all vulnerabilities are resolved (exploited or patched) or after the maximum step limit.

---

## 3. Step 1: Setup and Reproducibility

**Notebook Cell 2**: Environment initialization.

| Setting | Value |
|---------|-------|
| Random Seed | `42` |
| GPU Available | `True` (CUDA) |
| Models Directory | `api/models/red_agent/` |
| Logs Directory | `api/logs/red_agent/` |
| Results Directory | `api/results/red_agent/` |

**Libraries Used**:
- `stable_baselines3==2.7.1` (PPO)
- `sb3_contrib` (RecurrentPPO with LSTM)
- `torch==2.5.1+cu121`
- Custom: `cyborg_integration.py`, `train_sb3.py`

**GPU Warning** (Documented, Non-blocking):
> SB3 PPO with `MlpPolicy` is primarily optimized for CPU. The GPU was available but
> utilization was suboptimal for this architecture. This is a known SB3 limitation
> (see issue #1245) and does not affect model quality.

---

## 4. Step 2: Baseline Evaluation (Random Agent)

**Notebook Cell 4**: Establish performance floor using a `RandomAttackAgent`.

### Configuration
- Agent: `RandomAttackAgent` (random fuzzing + random exploitation)
- Episodes: **50**
- Allowed Attacks: SQLi, XSS

### Results

| Metric | Value |
|--------|-------|
| **Mean Reward** | **525.68** |
| **Standard Deviation** | 703.23 |
| **Mean Episode Length** | 149.68 steps |

**Interpretation**: The random agent achieved a positive mean reward (525.68), but with extremely high variance (std = 703.23). This indicates that the random agent occasionally "stumbles into" successful exploit chains by luck, but its behavior is inconsistent and unreliable. This serves as the floor that the trained agent must consistently exceed.

---

## 5. Step 3: Vanilla PPO Training

**Notebook Cell 6**: Train the first RL agent using standard PPO.

### Hyperparameters

| Parameter | Value | Notes |
|-----------|-------|-------|
| `policy` | `MlpPolicy` | Standard feedforward neural network |
| `learning_rate` | 0.0003 | Default PPO learning rate |
| `n_steps` | 2048 | Rollout buffer size |
| `batch_size` | 64 | SGD minibatch size |
| `n_epochs` | 10 | Number of passes over the rollout buffer |
| `gamma` | 0.99 | Discount factor (long-term reward focus) |
| `ent_coef` | 0.05 | Entropy coefficient (encourages exploration) |
| `total_timesteps` | **200,000** | Total training steps |

### Training Outcomes

| Metric | Value |
|--------|-------|
| **Training Duration** | **15.7 minutes** |
| **Final Mean Reward** (last 100 episodes) | **876.52** |
| **Final Standard Deviation** | 551.24 |
| **Final Mean Episode Length** | 146.85 steps |
| **Improvement over Baseline** | +66.7% |

### Checkpoints Saved
- Every 10,000 steps to `api/models/red_agent/checkpoints/`
- Final model: `api/models/red_agent/red_agent_final.zip`

---

## 6. Step 4: Recurrent PPO (LSTM) Training

**Notebook Cell 7**: Train a second RL agent using RecurrentPPO with LSTM memory.

### Hyperparameters

| Parameter | Value | Notes |
|-----------|-------|-------|
| `policy` | `MlpLstmPolicy` | LSTM-augmented policy network |
| `learning_rate` | 0.0005 | Slightly higher for memory network |
| `n_steps` | 2048 | Rollout buffer size |
| `batch_size` | 128 | Larger batch for sequence processing |
| `gamma` | 0.99 | Same long-term focus |
| `ent_coef` | 0.05 | Same exploration bonus |
| `total_timesteps` | **500,000** | 2.5x more training (memory needs more data) |

### Training Outcomes

| Metric | Value |
|--------|-------|
| **Training Duration** | **1073.4 minutes (~17.9 hours)** |
| **Final Mean Reward** (last 100 episodes) | **964.46** |
| **Final Standard Deviation** | 645.10 |
| **Final Mean Episode Length** | 144.73 steps |
| **Improvement over Baseline** | +83.5% |
| **Improvement over Vanilla PPO** | +10.0% |

### Why LSTM Took Longer
The RecurrentPPO processes sequences instead of individual observations. Each LSTM forward pass must maintain hidden states across the rollout, and the backpropagation through time (BPTT) is significantly more expensive. Combined with 2.5x more timesteps (500K vs 200K), this resulted in ~68x longer wall-clock time.

---

## 7. Step 5: Model Saving and Archival

**Notebook Cells 9-10**: Save final models and scientific metadata.

### Vanilla PPO
- **Model**: `api/models/red_agent/red_agent_final.zip` (246 KB)
- **Metadata**: `api/results/red_agent/training_info.json`

### Recurrent PPO (LSTM)
- **Model**: `api/models/red_agent/lstm_version/red_agent_lstm_final.zip` (8.4 MB)
- **Metadata**: `api/results/red_agent/lstm_version/training_info_lstm.json`

The LSTM model is **34x larger** than the Vanilla model due to the additional recurrent weight matrices.

---

## 8. Step 6: Visualization and Analysis

**Notebook Cells 12-13**: Reward convergence charts.

### Chart 1: Vanilla PPO Reward Convergence
- Raw episode rewards plotted with a 20-episode moving average.
- Random baseline shown as a horizontal green dashed line.
- Shows clear upward trend from early negative rewards toward consistent positive territory.

### Chart 2: Head-to-Head Comparison (Thesis Chart)
- Both Vanilla PPO (blue) and Recurrent PPO (orange) plotted on the same axes.
- 50-episode rolling average shows:
  - Vanilla PPO converges faster (fewer episodes) but to a lower plateau.
  - LSTM PPO starts slower but eventually reaches a higher stable reward.
- Random baseline (red dashed line) clearly below both trained agents.
- Title: **"HackOps 4th Year Thesis: Strategic Brain Comparison"**

---

## 9. Step 7: Final Tournament Comparison

Two tournament evaluations were run with fresh environments.

### Tournament 1: Vanilla PPO vs. Baseline (Cell 15)

| Agent | Mean Reward | Std Dev |
|-------|------------|---------|
| Random Baseline | 525.68 | 703.23 |
| Vanilla PPO (Trained) | **1,150.20** | 612.43 |

**Strategic Improvement**: **118.8%** over baseline.

### Tournament 2: Three-Way Comparison (Cell 16)

50 episodes per agent on the same environment configuration:

| Rank | Agent | Mean Reward | Std Dev |
|------|-------|------------|---------|
| 1 | **Memory (LSTM) Agent** | **1,096.21** | 628.86 |
| 2 | Vanilla PPO Agent | 814.84 | 513.36 |
| 3 | Random Baseline | 525.68 | 703.23 |

**Winner**: **Memory (LSTM) Agent**

---

## 10. Step 8: Detailed Inference Playback

The notebook includes step-by-step action traces showing exactly what each agent does turn-by-turn.

### 10.1 Vanilla PPO Playback (Cell 18 — 20 steps)

Example trace of the Vanilla PPO agent on a fresh episode:

```
Step 01: Fuzz /index.php (XSS)                   | Reward =  -0.5  | No signal
Step 02: SmartExploit /product_detail.php (SQLi)  | Reward = -15.0  | BLIND (not fuzzed!)
Step 03: Fuzz /orders.php (SQLi)                  | Reward =  -0.5  | No signal
...
Step 13: Fuzz /products.php                       | Reward =  50.0  | SIGNAL FOUND!
Step 14: SmartExploit /search.php (SQLi)          | Reward = -15.0  | BLIND (wrong page)
...
Total Reward after 20 steps: -43.00
```

**Observation**: The Vanilla PPO agent successfully discovers signals (Step 13) but fails to correctly follow up — it exploits the wrong page (Step 14) because it has **no memory** of which page produced the signal.

### 10.2 Battleground: Vanilla vs. LSTM (Cell 19 — 25 steps each, same seed)

**Vanilla PPO (The Reactor)**:
```
Step 08: Directory Discovery                      | Reward:  15.0  | Good recon
Step 15: Fuzz /register.php (XSS)                 | Reward:  50.0  | SIGNAL FOUND!
... but never exploits it correctly.
Total: -84.50
```

**Recurrent PPO (The Strategist)**:
```
Step 07: Fuzz /search.php (SQLi)                  | Reward:  50.0  | SIGNAL FOUND!
Step 08: SmartExploit /search.php (SQLi)          | Reward: 500.0  | THE JACKPOT!!!
Step 12: Fuzz /support.php (SQLi)                 | Reward:  50.0  | Another signal
Step 14: Fuzz /products.php (SQLi)                | Reward:  50.0  | Another signal
Step 21: Fuzz /login.php (SQLi)                   | Reward:  50.0  | Another signal
Total: 525.00
```

**Critical Difference**: The LSTM agent demonstrated the ability to:
1. Fuzz a page (Step 7) and **remember** that it found a SQLi signal at `/search.php`.
2. Immediately follow up with the correct `SmartExploit /search.php (SQLi)` (Step 8) — earning the **+500.0 jackpot**.
3. Continue systematically fuzzing other pages.

The Vanilla agent found signals but could not connect the "Fuzz → Exploit" chain reliably because it lacks inter-step memory.

---

## 11. Key Findings and Conclusions

### 11.1 Performance Summary

| Metric | Random | Vanilla PPO | Recurrent PPO (LSTM) |
|--------|--------|------------|---------------------|
| Mean Reward (Training) | 525.68 | 876.52 | 964.46 |
| Mean Reward (Tournament) | 525.68 | 814.84 | **1,096.21** |
| Training Time | N/A | 15.7 min | 17.9 hours |
| Model Size | N/A | 246 KB | 8.4 MB |
| Improvement over Random | — | +55.0% | **+108.5%** |

### 11.2 Conclusions

1. **RL Training Succeeded**: Both PPO variants significantly outperformed the random baseline, proving that the reward structure successfully guides the agent toward the professional Recon → Verify → Exploit workflow.

2. **Memory Matters**: The LSTM agent's ability to remember which pages were fuzzed and what signals were found gave it a decisive advantage. The key behavior was the "Fuzz → Immediate Exploit" chain (Step 7→8 in the playback), which the Vanilla PPO could not replicate consistently.

3. **Reward Design Worked**: The high penalty for blind attacks (-15.0) and the massive jackpot for correct exploitation (+500.0) successfully shaped the agent's behavior away from random guessing and toward systematic reconnaissance.

4. **Variance Remains High**: All agents showed high standard deviation (500-700), indicating that episode outcomes are heavily influenced by the random vulnerability generation. This is expected in a stochastic environment and does not indicate a problem.

5. **The Brain is Ready for the LLM**: Both trained models output discrete action indices that map to `SmartExploit /page (AttackType)`. These indices are the **Task Packets** that the LLM Actioner will translate into concrete payloads.

---

## 12. Saved Artifacts

### Models

| File | Size | Description |
|------|------|-------------|
| `api/models/red_agent/red_agent_final.zip` | 246 KB | Vanilla PPO final weights |
| `api/models/red_agent/lstm_version/red_agent_lstm_final.zip` | 8.4 MB | Recurrent PPO LSTM final weights |
| `api/models/red_agent/checkpoints/` | varies | Vanilla PPO checkpoints every 10K steps |

### Results

| File | Description |
|------|-------------|
| `api/results/red_agent/baseline_results.json` | Random baseline evaluation data |
| `api/results/red_agent/training_info.json` | Vanilla PPO training history and metadata |
| `api/results/red_agent/lstm_version/training_info_lstm.json` | LSTM training history and metadata |

### Key Source Files

| File | Role |
|------|------|
| `api/Red_Agent_Training.ipynb` | The notebook that produced all of these results |
| `api/train_sb3.py` | Training utilities (environment creation, evaluation) |
| `api/cyborg_integration.py` | CybORG environment, actions, rewards, wrappers |
| `api/action_mapper.py` | Bridge from RL action index to payload (placeholder for LLM) |
| `generate_vulns_focused.py` | Dynamic vulnerability generation per episode |
