# HackOps AI Development Guide
## Reinforcement Learning for Cybersecurity Agents

---

## Table of Contents

1. [Introduction](#introduction)
2. [Environment Setup](#environment-setup)
3. [Reinforcement Learning Fundamentals](#reinforcement-learning-fundamentals)
4. [PPO Algorithm Deep Dive](#ppo-algorithm-deep-dive)
5. [Custom Environment Design](#custom-environment-design)
6. [Agent Architecture](#agent-architecture)
7. [Training Configuration](#training-configuration)
8. [Reward Engineering](#reward-engineering)
9. [Training Procedures](#training-procedures)
10. [Evaluation Metrics](#evaluation-metrics)
11. [Hyperparameter Tuning](#hyperparameter-tuning)
12. [Advanced Techniques](#advanced-techniques)

---

## Introduction

### Project Overview

HackOps uses **Reinforcement Learning (RL)** to train intelligent agents that can autonomously attack or defend web applications. We train two types of agents:

- **Blue Agent (Defender)**: Learns to identify and patch vulnerabilities
- **Red Agent (Attacker)**: Learns to discover and exploit security flaws

### Why Reinforcement Learning?

Traditional supervised learning requires labeled datasets of "correct" security actions. RL allows agents to:
- Learn through trial and error
- Discover novel attack/defense strategies
- Adapt to dynamic environments
- Optimize long-term security outcomes

---

## Environment Setup

### Prerequisites

**System Requirements**:
- Python 3.10 or higher
- 8GB+ RAM (16GB recommended for training)
- GPU with CUDA support (optional but recommended)
- Windows 10/11, Linux, or macOS

### Installation Steps

#### 1. Create Virtual Environment

```bash
cd api
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/macOS
source venv/bin/activate
```

#### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

**Key Dependencies**:
```
stable-baselines3==2.2.1    # RL algorithms
gymnasium==0.29.1           # Environment interface
shimmy==1.3.0              # Environment wrappers
torch>=2.0.0               # Neural network backend
tensorboard>=2.14.0        # Training visualization
jupyter>=1.0.0             # Interactive training
matplotlib>=3.7.0          # Plotting
numpy<2.0                  # Numerical computing
```

#### 3. Install CybORG

CybORG is installed from source in the virtual environment:

```bash
# Already included in venv/src/cyborg/
# Custom DVWA integration modules added
```

#### 4. Verify Installation

```bash
python test_cyborg_comprehensive.py
```

Expected output:
```
✓ Test 1/7: Environment Creation
✓ Test 2/7: Reset Functionality
✓ Test 3/7: Action Space
✓ Test 4/7: Observation Space
✓ Test 5/7: Step Function
✓ Test 6/7: Agent Integration
✓ Test 7/7: Episode Completion

✓ 7/7 tests passed!
```

---

## Reinforcement Learning Fundamentals

### The RL Framework

Reinforcement Learning is formalized as a **Markov Decision Process (MDP)**:

**MDP Tuple**: (S, A, P, R, γ)

- **S**: State space (what the agent observes)
- **A**: Action space (what the agent can do)
- **P**: Transition probability P(s'|s,a)
- **R**: Reward function R(s,a,s')
- **γ**: Discount factor (0 ≤ γ ≤ 1)

### Key Concepts

#### 1. Policy (π)

A policy maps states to actions:

```
π: S → A
```

- **Deterministic**: π(s) = a
- **Stochastic**: π(a|s) = P(a|s)

#### 2. Value Functions

**State Value Function**:
```
V^π(s) = E_π[Σ(t=0 to ∞) γ^t * r_t | s_0 = s]
```

Expected cumulative discounted reward starting from state s.

**Action Value Function (Q-function)**:
```
Q^π(s,a) = E_π[Σ(t=0 to ∞) γ^t * r_t | s_0 = s, a_0 = a]
```

Expected return after taking action a in state s.

#### 3. Advantage Function

```
A^π(s,a) = Q^π(s,a) - V^π(s)
```

How much better is action a compared to the average action in state s?

#### 4. Bellman Equations

**Bellman Expectation Equation**:
```
V^π(s) = Σ_a π(a|s) * Σ_s' P(s'|s,a) * [R(s,a,s') + γ * V^π(s')]
```

**Bellman Optimality Equation**:
```
V*(s) = max_a Σ_s' P(s'|s,a) * [R(s,a,s') + γ * V*(s')]
```

---

## PPO Algorithm Deep Dive

### Why PPO?

**Proximal Policy Optimization** is our algorithm of choice because:

1. **Stable**: Prevents catastrophic policy updates
2. **Sample Efficient**: Reuses data effectively
3. **Simple**: Easier to implement than TRPO
4. **Effective**: State-of-the-art performance

### Mathematical Foundation

#### Policy Gradient Theorem

The gradient of expected return with respect to policy parameters θ:

```
∇_θ J(θ) = E_π[∇_θ log π_θ(a|s) * A^π(s,a)]
```

Where:
- J(θ) = expected return under policy π_θ
- A^π(s,a) = advantage function

#### Vanilla Policy Gradient Update

```
θ_{new} = θ_{old} + α * ∇_θ J(θ)
```

**Problem**: Large updates can destabilize training.

#### Trust Region Policy Optimization (TRPO)

TRPO constrains updates using KL divergence:

```
maximize_θ E[π_θ(a|s) / π_θ_old(a|s) * A(s,a)]
subject to: E[KL(π_θ_old || π_θ)] ≤ δ
```

**Problem**: Computationally expensive (requires conjugate gradient).

#### PPO: Clipped Objective

PPO simplifies TRPO with a clipped surrogate objective:

```
L^CLIP(θ) = E[min(r_t(θ) * A_t, clip(r_t(θ), 1-ε, 1+ε) * A_t)]
```

Where:
- r_t(θ) = π_θ(a_t|s_t) / π_θ_old(a_t|s_t) (probability ratio)
- ε = clipping parameter (typically 0.1 to 0.3)
- A_t = advantage estimate at timestep t

**Intuition**:
- If A_t > 0 (good action): increase π_θ(a|s), but not more than (1+ε)
- If A_t < 0 (bad action): decrease π_θ(a|s), but not more than (1-ε)

### Complete PPO Objective

```
L^PPO(θ) = E[L^CLIP(θ) - c_1 * L^VF(θ) + c_2 * S[π_θ](s)]
```

**Components**:

1. **Clipped Policy Loss** (L^CLIP):
   ```
   L^CLIP = E[min(r_t * A_t, clip(r_t, 1-ε, 1+ε) * A_t)]
   ```

2. **Value Function Loss** (L^VF):
   ```
   L^VF = E[(V_θ(s_t) - V_t^target)^2]
   ```
   Where V_t^target is the TD(λ) return.

3. **Entropy Bonus** (S):
   ```
   S[π_θ](s) = -Σ_a π_θ(a|s) * log π_θ(a|s)
   ```
   Encourages exploration.

**Coefficients**:
- c_1 = 0.5 (value function coefficient)
- c_2 = 0.01 (entropy coefficient)

### Generalized Advantage Estimation (GAE)

PPO uses GAE to estimate advantages:

```
A_t^GAE(γ,λ) = Σ(l=0 to ∞) (γλ)^l * δ_{t+l}
```

Where:
```
δ_t = r_t + γ * V(s_{t+1}) - V(s_t)
```

**Parameters**:
- γ = discount factor (0.99)
- λ = GAE parameter (0.95)

**Recursive Form**:
```
A_t = δ_t + γλ * A_{t+1}
```

### PPO Training Algorithm

```
1. Initialize policy network π_θ and value network V_φ
2. For iteration = 1, 2, ... do:
   3. Collect trajectories {(s_t, a_t, r_t)} using π_θ_old
   4. Compute advantages A_t using GAE
   5. Compute returns V_t^target = A_t + V(s_t)
   6. For epoch = 1 to K do:
      7. For minibatch in data do:
         8. Compute ratio r_t = π_θ(a_t|s_t) / π_θ_old(a_t|s_t)
         9. Compute clipped objective L^CLIP
         10. Compute value loss L^VF
         11. Compute entropy S
         12. Total loss L = L^CLIP - c_1*L^VF + c_2*S
         13. Update θ and φ using Adam optimizer
   14. θ_old ← θ
```

---

## Custom Environment Design

### Gymnasium Interface

Our environment implements the Gymnasium API:

```python
class DVWAEnv(gym.Env):
    def __init__(self, ...):
        self.observation_space = ...
        self.action_space = ...
    
    def reset(self, seed=None):
        # Initialize new episode
        return observation, info
    
    def step(self, action):
        # Execute action
        return observation, reward, terminated, truncated, info
```

### State Space (Observation)

**Observation Vector** (dimension: 50):

```python
observation = {
    # Page Information (10 dims)
    'current_page_id': int,           # Which page agent is on
    'page_category': one_hot(6),      # Public, Auth, Shopping, etc.
    'pages_visited': binary(20),      # Which pages have been visited
    
    # Vulnerability Information (25 dims)
    'vulns_discovered': binary(25),   # Which vulns found
    'vulns_exploited': binary(25),    # Which vulns exploited (Red)
    'vulns_patched': binary(25),      # Which vulns patched (Blue)
    
    # Mission State (15 dims)
    'time_remaining': float,          # Normalized time left
    'score_attacker': float,          # Current attacker score
    'score_defender': float,          # Current defender score
    'actions_taken': int,             # Number of actions so far
    'success_rate': float,            # % of successful actions
}
```

### Action Space

**Discrete Actions** (total: 100+):

```python
action_space = Discrete(n_actions)

# Action Categories:
# 0-19: Navigate to page X
# 20-44: Scan page X for vulnerabilities
# 45-69: Exploit vulnerability X (Red Agent)
# 70-94: Patch vulnerability X (Blue Agent)
# 95-99: Special actions (wait, analyze, etc.)
```

### Reward Function

#### Blue Agent (Defender) Rewards

```python
def compute_blue_reward(action, result):
    reward = 0
    
    # Successful patch
    if action_type == 'patch' and result.success:
        if result.proactive:  # Patched before exploitation
            reward += 50
        else:  # Patched after exploitation
            reward += 30
    
    # Vulnerability discovered
    if action_type == 'scan' and result.found_vulns > 0:
        reward += 10 * result.found_vulns
    
    # Vulnerability exploited (penalty)
    if result.vuln_exploited:
        reward -= 20
    
    # Invalid action
    if not result.valid:
        reward -= 5
    
    # Time penalty (encourage efficiency)
    reward -= 0.1
    
    return reward
```

#### Red Agent (Attacker) Rewards

```python
def compute_red_reward(action, result):
    reward = 0
    
    # Successful exploit
    if action_type == 'exploit' and result.success:
        severity_bonus = {
            'critical': 100,
            'high': 50,
            'medium': 25,
            'low': 10
        }
        reward += severity_bonus[result.severity]
    
    # Vulnerability discovered
    if action_type == 'scan' and result.found_vulns > 0:
        reward += 10 * result.found_vulns
    
    # Failed exploit
    if action_type == 'exploit' and not result.success:
        reward -= 10
    
    # Vulnerability patched (penalty)
    if result.vuln_patched:
        reward -= 15
    
    # Invalid action
    if not result.valid:
        reward -= 5
    
    return reward
```

### Episode Termination

An episode ends when:

```python
terminated = (
    time_elapsed >= max_time or           # Time limit (300s)
    all_vulns_patched or                  # Blue wins
    all_vulns_exploited or                # Red wins
    no_valid_actions_remaining            # Stalemate
)
```

---

## Agent Architecture

### Neural Network Design

Both policy and value networks use the same architecture:

```
Input Layer (50 neurons)
    ↓
Dense Layer 1 (256 neurons, ReLU)
    ↓
Dense Layer 2 (256 neurons, ReLU)
    ↓
Dense Layer 3 (128 neurons, ReLU)
    ↓
Output Layer
    ├─→ Policy Head (n_actions neurons, Softmax)
    └─→ Value Head (1 neuron, Linear)
```

**PyTorch Implementation**:

```python
class ActorCriticNetwork(nn.Module):
    def __init__(self, obs_dim, action_dim):
        super().__init__()
        
        # Shared layers
        self.shared = nn.Sequential(
            nn.Linear(obs_dim, 256),
            nn.ReLU(),
            nn.Linear(256, 256),
            nn.ReLU(),
            nn.Linear(256, 128),
            nn.ReLU()
        )
        
        # Policy head
        self.policy = nn.Sequential(
            nn.Linear(128, action_dim),
            nn.Softmax(dim=-1)
        )
        
        # Value head
        self.value = nn.Linear(128, 1)
    
    def forward(self, obs):
        features = self.shared(obs)
        action_probs = self.policy(features)
        state_value = self.value(features)
        return action_probs, state_value
```

### Activation Functions

**ReLU (Rectified Linear Unit)**:
```
f(x) = max(0, x)
f'(x) = 1 if x > 0 else 0
```

**Softmax** (for policy output):
```
σ(z)_i = exp(z_i) / Σ_j exp(z_j)
```

Converts logits to probability distribution.

---

## Training Configuration

### Hyperparameters

**Core PPO Parameters**:
```python
PPO_CONFIG = {
    # Learning
    'learning_rate': 3e-4,           # Adam learning rate
    'n_steps': 2048,                 # Steps per rollout
    'batch_size': 64,                # Minibatch size
    'n_epochs': 10,                  # Epochs per update
    
    # PPO Specific
    'gamma': 0.99,                   # Discount factor
    'gae_lambda': 0.95,              # GAE parameter
    'clip_range': 0.2,               # PPO clipping ε
    'clip_range_vf': None,           # Value function clipping
    
    # Regularization
    'ent_coef': 0.01,                # Entropy coefficient
    'vf_coef': 0.5,                  # Value function coefficient
    'max_grad_norm': 0.5,            # Gradient clipping
    
    # Network
    'net_arch': [256, 256, 128],     # Hidden layer sizes
    'activation_fn': nn.ReLU,        # Activation function
}
```

### Training Schedule

**Total Training**: 100,000 timesteps

```
Episodes: ~50-100 (depending on episode length)
Updates: ~48 (every 2048 steps)
Minibatches per update: 320 (2048 / 64)
Total gradient updates: ~15,360
Training time: 1-2 hours (CPU), 15-30 min (GPU)
```

---

## Training Procedures

### Method 1: Jupyter Notebook

**File**: `api/HackOps_Training.ipynb`

**Steps**:
1. Launch Jupyter: `jupyter notebook`
2. Open `HackOps_Training.ipynb`
3. Run cells sequentially
4. Use interactive controls to configure training
5. Click "🚀 START TRAINING"
6. Monitor live progress bars and plots

**Features**:
- Real-time metric visualization
- Interactive hyperparameter tuning
- Live episode replay
- Model evaluation tools

### Method 2: CLI Training

**File**: `api/train_sb3.py`

**Basic Usage**:
```bash
python train_sb3.py --agent blue --timesteps 100000
```

**Advanced Options**:
```bash
python train_sb3.py \
    --agent blue \
    --timesteps 100000 \
    --learning-rate 0.0003 \
    --n-steps 2048 \
    --batch-size 64 \
    --gamma 0.99 \
    --gae-lambda 0.95 \
    --clip-range 0.2 \
    --ent-coef 0.01 \
    --vf-coef 0.5 \
    --max-grad-norm 0.5 \
    --save-freq 10000 \
    --eval-freq 5000 \
    --n-eval-episodes 10 \
    --seed 42
```

### Training Loop Pseudocode

```python
# Initialize
env = DVWAEnv(agent_type='blue')
model = PPO('MlpPolicy', env, **PPO_CONFIG)

# Training loop
for update in range(n_updates):
    # Collect rollout
    rollout = collect_rollout(env, model, n_steps=2048)
    
    # Compute advantages
    advantages = compute_gae(rollout, gamma=0.99, lambda=0.95)
    
    # Update policy
    for epoch in range(10):
        for batch in minibatches(rollout, batch_size=64):
            # Forward pass
            actions_prob, values = model(batch.obs)
            
            # Compute losses
            ratio = actions_prob / batch.old_probs
            clipped_ratio = clip(ratio, 1-0.2, 1+0.2)
            policy_loss = -min(ratio * batch.advantages, 
                              clipped_ratio * batch.advantages)
            value_loss = (values - batch.returns)^2
            entropy = -sum(actions_prob * log(actions_prob))
            
            # Total loss
            loss = policy_loss + 0.5*value_loss - 0.01*entropy
            
            # Backward pass
            loss.backward()
            clip_grad_norm_(model.parameters(), 0.5)
            optimizer.step()
    
    # Logging
    log_metrics(update, rollout, model)
    
    # Checkpointing
    if update % 10 == 0:
        model.save(f'checkpoints/model_{update}.zip')
```

---

## Evaluation Metrics

### Training Metrics

**Episode Metrics**:
- `ep_rew_mean`: Mean episode reward
- `ep_len_mean`: Mean episode length
- `success_rate`: % of successful actions
- `exploration_rate`: Entropy of policy

**Learning Metrics**:
- `policy_loss`: L^CLIP value
- `value_loss`: L^VF value
- `entropy_loss`: Policy entropy
- `approx_kl`: KL divergence between old and new policy
- `clip_fraction`: % of ratios clipped

**Performance Metrics**:
- `fps`: Frames (steps) per second
- `time_elapsed`: Total training time
- `total_timesteps`: Cumulative steps

### Evaluation Protocol

```python
def evaluate_agent(model, env, n_episodes=10):
    rewards = []
    success_rates = []
    
    for episode in range(n_episodes):
        obs, info = env.reset()
        episode_reward = 0
        successes = 0
        actions = 0
        
        while True:
            action, _states = model.predict(obs, deterministic=True)
            obs, reward, terminated, truncated, info = env.step(action)
            
            episode_reward += reward
            actions += 1
            if info.get('success', False):
                successes += 1
            
            if terminated or truncated:
                break
        
        rewards.append(episode_reward)
        success_rates.append(successes / actions if actions > 0 else 0)
    
    return {
        'mean_reward': np.mean(rewards),
        'std_reward': np.std(rewards),
        'mean_success_rate': np.mean(success_rates),
        'std_success_rate': np.std(success_rates)
    }
```

---

## Hyperparameter Tuning

### Learning Rate

**Effect**: Controls step size of gradient descent

```
θ_new = θ_old - α * ∇L(θ)
```

**Typical Values**: 1e-5 to 1e-3
**Our Choice**: 3e-4

**Tuning**:
- Too high → unstable training, divergence
- Too low → slow learning, local minima

### Discount Factor (γ)

**Effect**: Balances immediate vs future rewards

```
V(s) = r_0 + γ*r_1 + γ²*r_2 + ...
```

**Range**: 0 to 1
**Our Choice**: 0.99

**Interpretation**:
- γ = 0: Only immediate rewards matter
- γ = 1: All future rewards equally important
- γ = 0.99: Rewards 100 steps away worth 37% of immediate reward

### GAE Lambda (λ)

**Effect**: Bias-variance tradeoff in advantage estimation

**Range**: 0 to 1
**Our Choice**: 0.95

**Extremes**:
- λ = 0: Low variance, high bias (TD(0))
- λ = 1: High variance, low bias (Monte Carlo)

### Clip Range (ε)

**Effect**: Limits policy update magnitude

**Range**: 0.1 to 0.3
**Our Choice**: 0.2

**Impact**:
- Smaller ε: More conservative updates, slower learning
- Larger ε: More aggressive updates, risk of instability

### Entropy Coefficient

**Effect**: Encourages exploration

**Range**: 0.001 to 0.1
**Our Choice**: 0.01

**Behavior**:
- Higher: More random actions, better exploration
- Lower: More deterministic, faster convergence

---

## Advanced Techniques

### Curriculum Learning

Train agents on progressively harder scenarios:

```python
# Stage 1: Few vulnerabilities, simple exploits
env_easy = DVWAEnv(max_vulns=3, difficulty='easy')
model.learn(total_timesteps=20000, env=env_easy)

# Stage 2: Medium complexity
env_medium = DVWAEnv(max_vulns=7, difficulty='medium')
model.learn(total_timesteps=30000, env=env_medium)

# Stage 3: Full complexity
env_hard = DVWAEnv(max_vulns=15, difficulty='hard')
model.learn(total_timesteps=50000, env=env_hard)
```

### Multi-Agent Training

Train Red and Blue agents against each other:

```python
# Self-play loop
for iteration in range(100):
    # Train Blue against current Red
    blue_model.learn(opponent=red_model, timesteps=10000)
    
    # Train Red against updated Blue
    red_model.learn(opponent=blue_model, timesteps=10000)
    
    # Evaluate
    evaluate_matchup(blue_model, red_model)
```

### Transfer Learning

Use pre-trained models as starting points:

```python
# Load pre-trained model
base_model = PPO.load('models/blue_agent_base.zip')

# Fine-tune on specific vulnerability types
env_sqli = DVWAEnv(vuln_types=['sqli'])
base_model.learn(total_timesteps=20000, env=env_sqli)
base_model.save('models/blue_agent_sqli_specialist.zip')
```

### Reward Shaping

Add intermediate rewards to guide learning:

```python
def shaped_reward(state, action, next_state, base_reward):
    # Base reward from environment
    reward = base_reward
    
    # Bonus for visiting new pages
    if next_state.page not in state.visited_pages:
        reward += 5
    
    # Bonus for discovering vulnerabilities
    if len(next_state.discovered_vulns) > len(state.discovered_vulns):
        reward += 10
    
    # Penalty for repeated failed actions
    if action == state.last_action and not state.last_success:
        reward -= 2
    
    return reward
```

---

## Conclusion

This AI development guide provides the mathematical and practical foundation for training intelligent cybersecurity agents in HackOps. The combination of PPO's stability, custom reward engineering, and domain-specific environment design enables agents to learn sophisticated attack and defense strategies.

**Key Takeaways**:
1. PPO provides stable, sample-efficient policy optimization
2. Custom environment design captures cybersecurity domain knowledge
3. Careful reward engineering shapes desired agent behavior
4. Proper evaluation ensures agents generalize beyond training scenarios
5. Advanced techniques like curriculum learning and self-play enhance performance

**Next Steps**:
- Experiment with hyperparameters
- Implement custom reward functions
- Try multi-agent training
- Explore transfer learning opportunities
- Contribute improvements to the codebase!

---

**Last Updated**: January 2026  
**Authors**: HackOps Development Team  
**License**: Educational Use
