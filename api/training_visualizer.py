
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
import json

class TrainingVisualizer:
    """Helper class for plotting training results"""
    
    def __init__(self, output_dir='./plots'):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def _rolling_average(self, data, window=50):
        """Calculate rolling average for smoothing"""
        if not data or len(data) < window:
            return data
        ret = np.cumsum(data, dtype=float)
        ret[window:] = ret[window:] - ret[:-window]
        return ret[window - 1:] / window

    def plot_training_curve(self, info, title=None, save_name=None):
        """Plot mean reward over episodes"""
        if not info or 'episode_rewards' not in info:
            print("No episode reward data found.")
            return
            
        rewards = info['episode_rewards']
        
        plt.figure(figsize=(10, 6))
        
        # Plot raw data faintly
        plt.plot(rewards, alpha=0.3, color='blue', label='Episode Reward')
        
        # Plot smoothed data
        window = min(50, len(rewards)//5) if len(rewards) > 50 else 1
        if window > 1:
            smoothed = self._rolling_average(rewards, window)
            plt.plot(np.arange(len(rewards)-len(smoothed), len(rewards)), smoothed, 
                     color='darkblue', linewidth=2, label=f'Rolling Avg ({window})')
            
        plt.title(title or f"Training Progress: {info.get('agent_type', 'Agent').upper()}")
        plt.xlabel('Episode')
        plt.ylabel('Reward')
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        if save_name:
            plt.savefig(self.output_dir / save_name)
            print(f"   📊 Plot saved: {self.output_dir / save_name}")
        
        plt.close()

    def plot_comparison(self, sessions, title="Model Comparison", metric='mean_reward', save_name=None):
        """Compare multiple sessions"""
        plt.figure(figsize=(12, 6))
        
        for session in sessions:
            rewards = session.get('episode_rewards', [])
            if not rewards: continue
            
            label = f"{session.get('agent_type')} ({session.get('algorithm')})"
            
            # Use smoothed line only for comparison to avoid clutter
            window = min(50, len(rewards)//5) if len(rewards) > 50 else 1
            if window > 1:
                smoothed = self._rolling_average(rewards, window)
                x_axis = np.arange(len(rewards)-len(smoothed), len(rewards))
                plt.plot(x_axis, smoothed, label=label, linewidth=2)
            else:
                plt.plot(rewards, label=label, alpha=0.8)
                
        plt.title(title)
        plt.xlabel('Episode')
        plt.ylabel('Reward (Smoothed)')
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        if save_name:
            plt.savefig(self.output_dir / save_name)
            print(f"   📊 Comparison plot saved: {self.output_dir / save_name}")
            
        plt.close()

    def plot_baseline_vs_trained(self, baseline_info, trained_info, agent_type='blue'):
        """Plot trained model performance against baseline"""
        if not baseline_info or not trained_info:
            return
            
        save_name = f"{agent_type}_baseline_comparison.png"
        
        plt.figure(figsize=(10, 6))
        
        # Baseline (mean line)
        base_mean = baseline_info.get('mean_reward', 0)
        plt.axhline(y=base_mean, color='r', linestyle='--', label=f'Baseline (Random): {base_mean:.1f}')
        
        # Trained
        rewards = trained_info.get('episode_rewards', [])
        window = min(50, len(rewards)//5) if len(rewards) > 50 else 1
        if window > 1:
             smoothed = self._rolling_average(rewards, window)
             plt.plot(np.arange(len(rewards)-len(smoothed), len(rewards)), smoothed, 
                      color='green', linewidth=2, label='Trained Agent')
        else:
             plt.plot(rewards, color='green', label='Trained Agent')
             
        plt.title(f"{agent_type.upper()} Agent: Trained vs Random Baseline")
        plt.xlabel('Episode')
        plt.ylabel('Reward')
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        plt.savefig(self.output_dir / save_name)
        print(f"   📊 Baseline comparison saved: {self.output_dir / save_name}")
        plt.close()
