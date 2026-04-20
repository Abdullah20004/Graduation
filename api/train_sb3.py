"""
RL Training Script using Stable-Baselines3
Easy to configure, train, and evaluate agents for DVWA
"""
import sys
import io
import os
from pathlib import Path
from datetime import datetime
import json

# Fix encoding for Windows console
# Fix encoding for Windows console (SAFE for Jupyter)
# sys.stdout hack removed to prevent Jupyter output capture issues

from stable_baselines3 import PPO, A2C, DQN
from stable_baselines3.common.evaluation import evaluate_policy
from stable_baselines3.common.callbacks import CheckpointCallback, EvalCallback
from stable_baselines3.common.monitor import Monitor
import gymnasium as gym
from gymnasium.wrappers import TimeLimit
import gym as old_gym

from cyborg_integration import create_cyborg_env, RandomAttackAgent, RandomDefenseAgent, DVWAFlatWrapper, TrainedAgent
from CybORG.Agents.Wrappers.BaseWrapper import BaseWrapper
from CybORG.Agents.Wrappers.OpenAIGymWrapper import OpenAIGymWrapper
import numpy as np
import random
from stable_baselines3.common.utils import set_random_seed

# DVWAFlatWrapper is now imported from cyborg_integration

class GymToGymnasiumWrapper(gym.Env):
    """Wrapper to convert old Gym environment to Gymnasium"""
    def __init__(self, env):
        self.env = env
        # Convert spaces
        self.observation_space = self._convert_space(env.observation_space)
        self.action_space = self._convert_space(env.action_space)
    
    def _convert_space(self, space):
        """Convert gym.Space to gymnasium.Space"""
        if isinstance(space, old_gym.spaces.Box):
            return gym.spaces.Box(low=space.low, high=space.high, shape=space.shape, dtype=space.dtype)
        elif isinstance(space, old_gym.spaces.Discrete):
            return gym.spaces.Discrete(n=space.n)
        else:
            return space
    
    def reset(self, seed=None, options=None):
        """Reset environment"""
        obs = self.env.reset()
        # If old gym returned only obs, add empty info
        if not isinstance(obs, tuple):
            obs = (obs, {})
        return obs
    
    def step(self, action):
        """Step environment"""
        result = self.env.step(action)
        
        if len(result) == 4:
            obs, reward, done, info = result
            terminated = done
            truncated = False
        elif len(result) == 5:
            obs, reward, terminated, truncated, info = result
        else:
            raise ValueError(f"Unexpected step return length: {len(result)}")
        
        return obs, reward, terminated, truncated, info
    
    def render(self):
        return self.env.render()
    
    def close(self):
        return self.env.close()


# Training Configuration
CONFIG = {
    'blue_defender': {
        'algorithm': 'PPO',
        'total_timesteps': 100000,
        'learning_rate': 0.0003,
        'n_steps': 2048,
        'batch_size': 64,
        'n_epochs': 10,
        'gamma': 0.99,
        'verbose': 1,
        'ent_coef': 0.0,  # Entropy coefficient for exploration (PPO/A2C)
        'exploration_fraction': 0.2, # Fraction of total timesteps for exploration decay (DQN)
        'exploration_final_eps': 0.05, # Final exploration rate (DQN)
        'allowed_attacks': ['XSS', 'SQL Injection']
    },
    'red_attacker': {
        'algorithm': 'PPO',
        'total_timesteps': 100000,
        'learning_rate': 0.0003,
        'n_steps': 2048,
        'batch_size': 64,
        'n_epochs': 10,
        'gamma': 0.99,
        'verbose': 1,
        'ent_coef': 0.01, # Higher entropy for attacker to explore diverse strategies
        'exploration_fraction': 0.3,
        'exploration_final_eps': 0.05,
        'allowed_attacks': ['XSS', 'SQL Injection']
    }
}


def create_training_env(agent_type='blue', allowed_attacks=None):
    """Create and wrap environment for training"""
    print(f"\n🌐 Creating environment for {agent_type} agent...")
    
    # Create CybORG environment
    cyborg = create_cyborg_env(
        red_agent=RandomAttackAgent if agent_type == 'blue' else None,
        allowed_attacks=allowed_attacks
    )
    print("Wrapper chain:", env)
    
from stable_baselines3.common.callbacks import BaseCallback

# Add parent directory to path to import generate_vulns_focused
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
try:
    from generate_vulns_focused import generate_vulnerabilities, save_vulnerability_config
except ImportError:
    # Fallback if running from root or different structure
    sys.path.append(os.path.abspath(os.path.join(os.getcwd(), '..')))
    from generate_vulns_focused import generate_vulnerabilities, save_vulnerability_config

class EpisodeLoggerCallback(BaseCallback):
    """
    Callback for logging episode metrics (reward, length) to console
    """
    def __init__(self, verbose=0):
        super().__init__(verbose)
        self.episode_count = 0
        self.cumulative_reward = 0
        self.episode_length = 0
        self.episode_rewards = [] # Store history
        self.episode_lengths = []
        
    def _on_step(self):
        # Accumulate reward for current step (approximate, for live view)
        # Note: self.locals['rewards'] contains rewards for current step
        # But for accurate episode sums, we rely on Monitor wrapper info
        
        dones = self.locals['dones']
        infos = self.locals['infos']
        
        for idx, done in enumerate(dones):
            if done:
                self.episode_count += 1
                info = infos[idx]
                
                # Check for Monitor wrapper info
                if 'episode' in info:
                    ep_reward = info['episode']['r']
                    ep_length = info['episode']['l']
                    self.episode_rewards.append(ep_reward)
                    self.episode_lengths.append(ep_length)
                    print(f"   Episode {self.episode_count}: Reward = {ep_reward:.2f}, Length = {ep_length}")
                else:
                    print(f"   Episode {self.episode_count} finished.")
        return True


def evaluate_random_baseline(agent_type='blue', n_episodes=50, allowed_attacks=None):
    """
    Evaluate random agents to establish baseline performance
    """
    print(f"\n📊 Evaluating Random Baseline for {agent_type.upper()} ({n_episodes} episodes)...")
    
    # Create environment with Random agents
    env = create_training_env(agent_type, allowed_attacks)
    
    # Instead of model.predict, we just rely on the random agent inside the environment
    # But for full control, we can also use a "RandomPolicy" wrapper if needed via Stable Baselines,
    # or just step through the environment manually since the opponnet is ALSO random by default in create_training_env
    # However, create_training_env wraps everything in Monitor, so we can just run a loop.
    
    episode_rewards = []
    episode_lengths = []
    
    obs = env.reset()
    current_ep_reward = 0
    current_ep_len = 0
    
    completed_episodes = 0
    
    while completed_episodes < n_episodes:
        # Check if environment is wrapped in something that expects actions
        # For 'blue' training env, we control Blue.
        # We need to take RANDOM actions for Blue.
        
        action = env.action_space.sample()
        step_result = env.step(action)
        
        if len(step_result) == 4:
            obs, reward, done, info = step_result
        elif len(step_result) == 5:
             obs, reward, terminated, truncated, info = step_result
             done = terminated or truncated
        else:
             raise ValueError(f"Unexpected step return length: {len(step_result)}")
        
        # Monitor wrapper might give us info on done
        # But we need to check the info dict carefully depending on gym version wrappers
        
        # Note: Stable Baselines Monitor wrapper adds 'episode' key to info when done
        if isinstance(info, list): # Vector env support
            info_dict = info[0]
        else:
            info_dict = info
            
        if done: # Terminated or Truncated handled by wrapper usually returning done=True
            if 'episode' in info_dict:
                episode_rewards.append(info_dict['episode']['r'])
                episode_lengths.append(info_dict['episode']['l'])
            else:
                # Fallback if Monitor is not attaching info (shouldn't happen with SB3 Monitor)
                pass 
                
            completed_episodes += 1
            if completed_episodes % 10 == 0:
                print(f"   Episode {completed_episodes}/{n_episodes} completed")
                
            current_ep_reward = 0
            current_ep_len = 0
            obs = env.reset()
            
    env.close()
    
    mean_reward = np.mean(episode_rewards)
    std_reward = np.std(episode_rewards)
    
    print(f"\n✅ Baseline Evaluation Complete")
    print(f"   Mean Reward: {mean_reward:.2f} (+/- {std_reward:.2f})")
    print(f"   Mean Length: {np.mean(episode_lengths):.2f}")
    
    results = {
        'agent_type': agent_type,
        'algorithm': 'Random',
        'n_episodes': n_episodes,
        'mean_reward': float(mean_reward),
        'std_reward': float(std_reward),
        'episode_rewards': [float(r) for r in episode_rewards],
        'episode_lengths': [float(l) for l in episode_lengths],
        'evaluated_at': datetime.now().isoformat()
    }
    
    return results

def create_training_env(agent_type='blue', allowed_attacks=None, config_path=None, red_opponent_path=None, blue_opponent_path=None):
    """Create and wrap environment for training"""
    print(f"\n[Env] Creating environment for {agent_type} agent...")
    
    # Configure opponents
    red_agent_cls = None
    blue_agent_cls = None
    
    from functools import partial
    
    if agent_type == 'blue':
        # We are Blue. Opponent is Red.
        if red_opponent_path:
             print(f"   [Opponent] Using trained Red opponent: {red_opponent_path}")
             red_agent_cls = partial(TrainedAgent, model_path=red_opponent_path)
        else:
             print(f"   [Opponent] Using Random Red opponent")
             red_agent_cls = RandomAttackAgent
    else:
        # We are Red. Opponent is Blue.
        if blue_opponent_path:
             print(f"   [Opponent] Using trained Blue opponent: {blue_opponent_path}")
             blue_agent_cls = partial(TrainedAgent, model_path=blue_opponent_path)
        else:
             print(f"   [Opponent] Using Random Blue opponent")
             blue_agent_cls = RandomDefenseAgent

    # Create CybORG environment
    cyborg = create_cyborg_env(
        red_agent=red_agent_cls,
        blue_agent=blue_agent_cls,
        allowed_attacks=allowed_attacks,
        config_path=config_path,
        dynamic_generation=True  # Ensure fresh vulns per episode for robust training
    )
    
    # Wrap for Gym compatibility
    agent_name = f'{agent_type}_agent_0'  # DVWA agent naming
    
    # Use CUSTOM Wrapper instead of FixedFlatWrapper
    wrapped = DVWAFlatWrapper(cyborg)
    
    gym_env = OpenAIGymWrapper(agent_name=agent_name, env=wrapped)
    
    # Convert old Gym to new Gymnasium
    gymnasium_env = GymToGymnasiumWrapper(gym_env)
    
    # Add episode time limit (CRITICAL: without this, episodes never end!)
    # This ensures episodes terminate after max_steps, allowing training to progress
    max_episode_steps = 150  # Reduced from 500 to prevent catastrophic penalty accumulation
    time_limited_env = TimeLimit(gymnasium_env, max_episode_steps=max_episode_steps)
    
    # Monitor for tracking
    env = Monitor(time_limited_env)
    
    print(f"   [OK] Environment created")
    print(f"   Agent: {agent_name}")
    print(f"   Observation space: {env.observation_space}")
    print(f"   Action space: {env.action_space}")
    
    return env


from stable_baselines3.common.utils import set_random_seed

def train_agent(agent_type='blue', config=None, model_dir='./models', log_dir='./logs', opponent_path=None, seed=None):
    """
    Train an RL agent
    
    Args:
        agent_type: 'blue' (defender) or 'red' (attacker)
        config: Training configuration dict (uses default if None)
        model_dir: Directory to save models
        log_dir: Directory to save logs
        opponent_path: Path to trained opponent model (optional)
        seed: Random seed for reproducibility
    """
    # Set seed if provided
    if seed is not None:
        print(f"🌱 Setting random seed: {seed}")
        set_random_seed(seed)
        random.seed(seed)
        np.random.seed(seed)
    
    # Setup dirs
    model_dir = Path(model_dir)
    log_dir = Path(log_dir)
    model_dir.mkdir(parents=True, exist_ok=True)
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Get config
    if config is None:
        config = CONFIG.get(f'{agent_type}_defender' if agent_type == 'blue' else f'{agent_type}_attacker')
    
    # Get allowed attacks
    allowed_attacks = config.get('allowed_attacks', ['XSS', 'SQL Injection'])
    
    print("\n" + "="*70)
    print(f"[{'BLUE' if agent_type == 'blue' else 'RED'}] Training {agent_type.upper()} Agent")
    if opponent_path:
        print(f"   VS Opponent: {opponent_path}")
    print("="*70)
    
    # =========================================================
    # GENERATE FOCUSED VULNERABILITIES
    # =========================================================
    print("[Vulns] Generating focused vulnerabilities for training...")
    try:
        # Generate vulns using the script logic
        vulns, seed_gen = generate_vulnerabilities(
            min_vulns=5,
            max_vulns=10,
            seed=seed # Pass the main seed
        )
        # Save to a local config file for training
        config_path = os.path.join(os.getcwd(), 'config', 'vulns_focused_training.json')
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        save_vulnerability_config(vulns, seed_gen, output_path=config_path)
        print(f"   ✓ Vulnerabilities generated and saved to: {config_path}")
        print(f"   ✓ Seed: {seed_gen}")
        print(f"   ✓ Count: {len([v for v in vulns if v['enabled']])}")
    except Exception as e:
        print(f"⚠️ Failed to generate focused vulns: {e}")
        print("   Falling back to default vulns.json or mocks.")
        config_path = None
    
    print("="*70)
    print(f"Algorithm: {config['algorithm']}")
    print(f"Total timesteps: {config['total_timesteps']:,}")
    print(f"Learning rate: {config['learning_rate']}")
    print(f"Attacks: {allowed_attacks}")
    if seed is not None:
        print(f"Seed: {seed}")
    print("="*70)
    
    # Create environment with custom config path
    # Determine which opponent arg to set based on our agent type
    red_opp = opponent_path if agent_type == 'blue' else None
    blue_opp = opponent_path if agent_type == 'red' else None
    
    # Pass seed to environment creation if supported
    env = create_training_env(agent_type, allowed_attacks, config_path=config_path, 
                              red_opponent_path=red_opp, blue_opponent_path=blue_opp)
    
    # Force seed on env if available
    if seed is not None:
        env.reset(seed=seed)
    
    # Create algorithm
    print(f"\n[Model] Building {config['algorithm']} model...")
    
    if config['algorithm'] == 'PPO':
        model = PPO(
            'MlpPolicy',
            env,
            learning_rate=config['learning_rate'],
            n_steps=config['n_steps'],
            batch_size=config['batch_size'],
            n_epochs=config['n_epochs'],
            gamma=config['gamma'],
            ent_coef=config.get('ent_coef', 0.0), # Use config value
            verbose=config['verbose'],
            tensorboard_log=str(log_dir)
        )
    elif config['algorithm'] == 'A2C':
        model = A2C(
            'MlpPolicy',
            env,
            learning_rate=config['learning_rate'],
            gamma=config['gamma'],
            ent_coef=config.get('ent_coef', 0.0), # Use config value
            verbose=config['verbose'],
            tensorboard_log=str(log_dir)
        )
    elif config['algorithm'] == 'DQN':
        model = DQN(
            'MlpPolicy',
            env,
            learning_rate=config['learning_rate'],
            gamma=config['gamma'],
            exploration_fraction=config.get('exploration_fraction', 0.1),
            exploration_final_eps=config.get('exploration_final_eps', 0.05),
            verbose=config['verbose'],
            tensorboard_log=str(log_dir)
        )
    else:
        raise ValueError(f"Unknown algorithm: {config['algorithm']}")
    
    print("   [OK] Model created")
    
    # Setup callbacks
    checkpoint_callback = CheckpointCallback(
        save_freq=10000,
        save_path=str(model_dir / agent_type),
        name_prefix=f'{agent_type}_agent'
    )
    
    episode_logger = EpisodeLoggerCallback()
    
    # Start training
    print(f"\n🎓 Starting training...")
    print(f"Progress will be displayed below:\n")
    
    start_time = datetime.now()
    
    try:
        model.learn(
            total_timesteps=config['total_timesteps'],
            callback=[checkpoint_callback, episode_logger],
            progress_bar=False
        )
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Save final model
        final_path = model_dir / f'{agent_type}_agent_final.zip'
        model.save(final_path)
        
        print("\n" + "="*70)
        print("✅ TRAINING COMPLETE")
        print("="*70)
        print(f"Duration: {duration:.1f} seconds")
        print(f"Final model: {final_path}")
        print(f"Checkpoints: {model_dir / agent_type}/")
        print(f"TensorBoard logs: {log_dir}/")
        print("="*70)
        
        # Quick evaluation (DISABLED to avoid user confusion about "extra" runs)
        # print("\n📊 Running quick evaluation (10 episodes)...")
        # mean_reward, std_reward = evaluate_policy(model, env, n_eval_episodes=10)
        # print(f"   Mean reward: {mean_reward:.2f} (+/- {std_reward:.2f})")
        
        # Save training info
        info = {
            'agent_type': agent_type,
            'algorithm': config['algorithm'],
            'total_timesteps': config['total_timesteps'],
            'training_duration_seconds': duration,
            'final_model_path': str(final_path),
            'final_model_path': str(final_path),
            'mean_reward': float(np.mean(episode_logger.episode_rewards)) if episode_logger.episode_rewards else 0.0, 
            'std_reward': float(np.std(episode_logger.episode_rewards)) if episode_logger.episode_rewards else 0.0,
            'trained_at': datetime.now().isoformat(),
            'config_path': str(config_path) if config_path else "default",
            'episode_rewards': episode_logger.episode_rewards, # Save full history
            'episode_lengths': episode_logger.episode_lengths
        }
        
        info_path = model_dir / f'{agent_type}_agent_info.json'
        with open(info_path, 'w') as f:
            json.dump(info, f, indent=2)
        
        print(f"\n💾 Training info saved: {info_path}\n")
        
        return model, info
        
    except KeyboardInterrupt:
        print("\n\n⚠️ Training interrupted by user")
        # Save current model
        interrupted_path = model_dir / f'{agent_type}_agent_interrupted.zip'
        model.save(interrupted_path)
        print(f"💾 Model saved: {interrupted_path}\n")
        return model, {}
    
    finally:
        env.close()


def load_and_evaluate(model_path, agent_type='blue', n_episodes=100):
    """Load a trained model and evaluate it"""
    print("\n" + "="*70)
    print(f"📈 Evaluating Model: {model_path}")
    print("="*70)
    
    # Load model
    if 'PPO' in str(model_path) or CONFIG[f'{agent_type}_defender']['algorithm'] == 'PPO':
        model = PPO.load(model_path)
    elif 'A2C' in str(model_path) or CONFIG[f'{agent_type}_defender']['algorithm'] == 'A2C':
        model = A2C.load(model_path)
    elif 'DQN' in str(model_path) or CONFIG[f'{agent_type}_defender']['algorithm'] == 'DQN':
        model = DQN.load(model_path)
    else:
        raise ValueError(f"Cannot determine algorithm from {model_path}")
    
    print(f"✓ Model loaded")
    
    # Create environment
    env = create_training_env(agent_type)
    
    # Evaluate
    print(f"\nRunning {n_episodes} episodes...")
    mean_reward, std_reward = evaluate_policy(
        model, env, n_eval_episodes=n_episodes, return_episode_rewards=False
    )
    
    print("\n" + "="*70)
    print("📊 Evaluation Results")
    print("="*70)
    print(f"Episodes: {n_episodes}")
    print(f"Mean reward: {mean_reward:.2f}")
    print(f"Std reward: {std_reward:.2f}")
    print("="*70 + "\n")
    
    env.close()
    
    return mean_reward, std_reward


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Train RL agents for HackOps using Stable-Baselines3",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument('--agent', choices=['blue', 'red'], default='blue',
                       help='Agent type to train')
    parser.add_argument('--algorithm', choices=['PPO', 'A2C', 'DQN'], default='PPO',
                       help='RL algorithm to use')
    parser.add_argument('--timesteps', type=int, default=100000,
                       help='Total training timesteps')
    parser.add_argument('--lr', type=float, default=0.0003,
                       help='Learning rate')
    parser.add_argument('--model-dir', default='./models',
                       help='Directory to save models')
    parser.add_argument('--log-dir', default='./logs',
                       help='Directory for TensorBoard logs')
    parser.add_argument('--evaluate', type=str,
                       help='Path to model to evaluate (skips training)')
    parser.add_argument('--eval-episodes', type=int, default=100,
                       help='Number of evaluation episodes')
    parser.add_argument('--attacks', nargs='+', default=['XSS', 'SQL Injection'],
                       help='Attacks to include (e.g. XSS "SQL Injection")')
    
    parser.add_argument('--baseline', action='store_true',
                       help='Run baseline evaluation with random agents')
    parser.add_argument('--ent-coef', type=float, default=None,
                       help='Entropy coefficient for PPO/A2C (overrides config)')
    parser.add_argument('--opponent', type=str, default=None,
                       help='Path to opponent model (for adversarial training)')
    parser.add_argument('--seed', type=int, default=None,
                       help='Random seed for reproducibility')
    
    args = parser.parse_args()
    
    # Set seed globally if provided
    if args.seed is not None:
        set_random_seed(args.seed)
        random.seed(args.seed)
        np.random.seed(args.seed)
    
    if args.baseline:
        # Baseline evaluation mode
        # Baseline uses the seed from args implicitly if we pass it, 
        # but evaluate_random_baseline needs update if we want exact reproducible baseline
        # For now, just setting global seed helps
        baseline_results = evaluate_random_baseline(args.agent, args.eval_episodes, args.attacks)
        # Save baseline results
        baseline_path = Path(args.model_dir) / f'{args.agent}_baseline_info.json'
        baseline_path.parent.mkdir(parents=True, exist_ok=True)
        with open(baseline_path, 'w') as f:
            json.dump(baseline_results, f, indent=2)
        print(f"💾 Baseline results saved: {baseline_path}")

    elif args.evaluate:
        # Evaluation mode
        load_and_evaluate(args.evaluate, args.agent, args.eval_episodes)
    else:
        # Training mode
        config = CONFIG.get(f'{args.agent}_defender' if args.agent == 'blue' else f'{args.agent}_attacker').copy()
        
        # Override config with args
        if args.algorithm: config['algorithm'] = args.algorithm
        if args.timesteps: config['total_timesteps'] = args.timesteps
        if args.lr: config['learning_rate'] = args.lr
        if args.attacks: config['allowed_attacks'] = args.attacks
        if args.ent_coef is not None: config['ent_coef'] = args.ent_coef
        
        # Add seed to config so it can be used in model creation
        if args.seed is not None:
             config['seed'] = args.seed
        
        # Override algorithm just in case (e.g. if config had one default but CLI specified another, 
        # we might want to adjust other params, but here we just pass it)
        
        model, info = train_agent(args.agent, config, args.model_dir, args.log_dir, opponent_path=args.opponent, seed=args.seed)
        
        print("\n🎉 Training session complete!")
        print(f"\nTo view training progress:")
        print(f"  tensorboard --logdir {args.log_dir}")
        print(f"\nTo evaluate the model:")
        print(f"  python train_sb3.py --evaluate {info.get('final_model_path', 'MODEL_PATH')} --agent {args.agent}")
        print()
