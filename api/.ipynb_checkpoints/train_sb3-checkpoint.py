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
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from stable_baselines3 import PPO, A2C, DQN
from stable_baselines3.common.evaluation import evaluate_policy
from stable_baselines3.common.callbacks import CheckpointCallback, EvalCallback
from stable_baselines3.common.monitor import Monitor
import gymnasium as gym
import gym as old_gym

from cyborg_integration import create_cyborg_env, RandomAttackAgent
from CybORG.Agents.Wrappers.FixedFlatWrapper import FixedFlatWrapper
from CybORG.Agents.Wrappers.OpenAIGymWrapper import OpenAIGymWrapper


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
        return obs, {}
    
    def step(self, action):
        """Step environment"""
        obs, reward, done, info = self.env.step(action)
        return obs, reward, done, False, info
    
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
        'verbose':1
    },
    'red_attacker': {
        'algorithm': 'PPO',
        'total_timesteps': 100000,
        'learning_rate': 0.0003,
        'n_steps': 2048,
        'batch_size': 64,
        'n_epochs': 10,
        'gamma': 0.99,
        'verbose': 1
    }
}


def create_training_env(agent_type='blue'):
    """Create and wrap environment for training"""
    print(f"\n🌐 Creating environment for {agent_type} agent...")
    
    # Create CybORG environment
    cyborg = create_cyborg_env(red_agent=RandomAttackAgent if agent_type == 'blue' else None)
    
    # Wrap for Gym compatibility
    agent_name = f'{agent_type}_agent_0'  # DroneSwarmScenarioGenerator naming
    wrapped = FixedFlatWrapper(cyborg)
    gym_env = OpenAIGymWrapper(agent_name=agent_name, env=wrapped)
    
    # Convert old Gym to new Gymnasium
    gymnasium_env = GymToGymnasiumWrapper(gym_env)
    
    # Monitor for tracking
    env = Monitor(gymnasium_env)
    
    print(f"   ✓ Environment created")
    print(f"   Agent: {agent_name}")
    print(f"   Observation space: {env.observation_space}")
    print(f"   Action space: {env.action_space}")
    
    return env


def train_agent(agent_type='blue', config=None, model_dir='./models', log_dir='./logs'):
    """
    Train an RL agent
    
    Args:
        agent_type: 'blue' (defender) or 'red' (attacker)
        config: Training configuration dict (uses default if None)
        model_dir: Directory to save models
        log_dir: Directory to save logs
    """
    # Setup dirs
    model_dir = Path(model_dir)
    log_dir = Path(log_dir)
    model_dir.mkdir(parents=True, exist_ok=True)
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Get config
    if config is None:
        config = CONFIG.get(f'{agent_type}_defender' if agent_type == 'blue' else f'{agent_type}_attacker')
    
    print("\n" + "="*70)
    print(f"{'🛡️ ' if agent_type == 'blue' else '⚔️ '} Training {agent_type.upper()} Agent")
    print("="*70)
    print(f"Algorithm: {config['algorithm']}")
    print(f"Total timesteps: {config['total_timesteps']:,}")
    print(f"Learning rate: {config['learning_rate']}")
    print("="*70)
    
    # Create environment
    env = create_training_env(agent_type)
    
    # Create algorithm
    print(f"\n🏗️ Building {config['algorithm']} model...")
    
    if config['algorithm'] == 'PPO':
        model = PPO(
            'MlpPolicy',
            env,
            learning_rate=config['learning_rate'],
            n_steps=config['n_steps'],
            batch_size=config['batch_size'],
            n_epochs=config['n_epochs'],
            gamma=config['gamma'],
            verbose=config['verbose'],
            tensorboard_log=str(log_dir)
        )
    elif config['algorithm'] == 'A2C':
        model = A2C(
            'MlpPolicy',
            env,
            learning_rate=config['learning_rate'],
            gamma=config['gamma'],
            verbose=config['verbose'],
            tensorboard_log=str(log_dir)
        )
    elif config['algorithm'] == 'DQN':
        model = DQN(
            'MlpPolicy',
            env,
            learning_rate=config['learning_rate'],
            gamma=config['gamma'],
            verbose=config['verbose'],
            tensorboard_log=str(log_dir)
        )
    else:
        raise ValueError(f"Unknown algorithm: {config['algorithm']}")
    
    print("   ✓ Model created")
    
    # Setup callbacks
    checkpoint_callback = CheckpointCallback(
        save_freq=10000,
        save_path=str(model_dir / agent_type),
        name_prefix=f'{agent_type}_agent'
    )
    
    # Start training
    print(f"\n🎓 Starting training...")
    print(f"Progress will be displayed below:\n")
    
    start_time = datetime.now()
    
    try:
        model.learn(
            total_timesteps=config['total_timesteps'],
            callback=checkpoint_callback,
            progress_bar=True
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
        
        # Quick evaluation
        print("\n📊 Running quick evaluation (10 episodes)...")
        mean_reward, std_reward = evaluate_policy(model, env, n_eval_episodes=10)
        print(f"   Mean reward: {mean_reward:.2f} (+/- {std_reward:.2f})")
        
        # Save training info
        info = {
            'agent_type': agent_type,
            'algorithm': config['algorithm'],
            'total_timesteps': config['total_timesteps'],
            'training_duration_seconds': duration,
            'final_model_path': str(final_path),
            'mean_reward': float(mean_reward),
            'std_reward': float(std_reward),
            'trained_at': datetime.now().isoformat()
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
    
    args = parser.parse_args()
    
    if args.evaluate:
        # Evaluation mode
        load_and_evaluate(args.evaluate, args.agent, args.eval_episodes)
    else:
        # Training mode
        config = {
            'algorithm': args.algorithm,
            'total_timesteps': args.timesteps,
            'learning_rate': args.lr,
            'n_steps': 2048,
            'batch_size': 64,
            'n_epochs': 10,
            'gamma': 0.99,
            'verbose': 1
        }
        
        model, info = train_agent(args.agent, config, args.model_dir, args.log_dir)
        
        print("\n🎉 Training session complete!")
        print(f"\nTo view training progress:")
        print(f"  tensorboard --logdir {args.log_dir}")
        print(f"\nTo evaluate the model:")
        print(f"  python train_sb3.py --evaluate {info.get('final_model_path', 'MODEL_PATH')} --agent {args.agent}")
        print()
