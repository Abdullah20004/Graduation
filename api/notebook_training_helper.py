"""
Training helper for Jupyter notebook with live progress streaming.
Handles subprocess training with real-time output display.
"""
import subprocess
import json
import time
from pathlib import Path
from IPython.display import clear_output


from training_results import TrainingResults
from training_visualizer import TrainingVisualizer
import numpy as np

def run_baseline_evaluation(agent, n_episodes=50, seed=None):
    """Run baseline evaluation process with live output"""
    venv_python = Path('venv/Scripts/python.exe')
    cmd = [
        str(venv_python),
        'train_sb3.py',
        '--agent', agent,
        '--baseline',
        '--eval-episodes', str(n_episodes)
    ]
    
    if seed is not None:
        cmd.extend(['--seed', str(seed)])
    
    print(f"\n{'='*70}")
    print(f"📉 Running Baseline Evaluation: {agent.upper()}")
    print(f"{'='*70}")
    
    try:
        # Use Popen to stream output
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding='utf-8',
            errors='replace',
            bufsize=1,
            universal_newlines=True
        )
        
        for line in process.stdout:
            print(line.rstrip())
            
        process.wait()
        
        if process.returncode != 0:
            print(f"❌ Baseline evaluation failed with exit code {process.returncode}")
            return None
            
        print("✅ Baseline evaluation finished.")
        
        # Load and verify
        results_mgr = TrainingResults()
        baseline = results_mgr.get_baseline(agent)
        if baseline:
            print(f"\n📊 {agent.upper()} Baseline Summary:")
            print(f"   Mean Reward: {baseline.get('mean_reward', 0):.2f}")
            print(f"   Std Reward:  {baseline.get('std_reward', 0):.2f}")
            return baseline
            
    except Exception as e:
        print(f"❌ Baseline evaluation failed: {e}")
    return None

def run_training_with_live_progress(agent, algorithm, timesteps, lr, attacks=None, ent_coef=None, opponent_path=None, seed=None):
    """
    Run training via subprocess with LIVE output streaming.
    Shows progress bars, episode metrics, and training updates in real-time.
    """
    
    # Build command
    venv_python = Path('venv/Scripts/python.exe')
    if not venv_python.exists():
        print("❌ Virtual environment not found!")
        return None
    
    cmd = [
        str(venv_python),
        'train_sb3.py',
        '--agent', agent,
        '--algorithm', algorithm,
        '--timesteps', str(timesteps),
        '--lr', str(lr)
    ]
    
    if attacks:
        cmd.extend(['--attacks'] + attacks)
        
    if ent_coef is not None:
        cmd.extend(['--ent-coef', str(ent_coef)])
        
    if opponent_path:
        cmd.extend(['--opponent', str(opponent_path)])
        print(f"⚔️ Training against: {opponent_path}")
        
    if seed is not None:
        cmd.extend(['--seed', str(seed)])
        print(f"🌱 Using random seed: {seed}")
    
    print(f"\n{'='*70}")
    print(f"🚀 Starting Training: {agent.upper()} with {algorithm}")
    print(f"{'='*70}")
    print(f"Timesteps: {timesteps:,}")
    print(f"Learning Rate: {lr}")
    if ent_coef is not None:
        print(f"Entropy Coef: {ent_coef}")
    print(f"\n📊 Live Training Output:\n")
    
    # Run training with LIVE output streaming
    start_time = time.time()
    
    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,  # Combine stderr with stdout
            text=True,
            encoding='utf-8',
            errors='replace',
            bufsize=1,  # Line buffered
            universal_newlines=True
        )
        
        # Stream output in real-time
        last_line = ""
        for line in process.stdout:
            line = line.rstrip()
            
            # Filter out gym deprecation warnings
            if 'Gym has been unmaintained' in line or 'migration_guide' in line:
                continue
            
            # Show important lines
            if any(keyword in line for keyword in [
                'Timesteps:', 'Episode', 'Mean reward', 'Mean ep len',
                '===', '✅', '❌', 'Duration:', 'Model saved', 'TRAINING',
                'Phase', 'Algorithm:', 'Learning Rate:',
                'Seed:', 'Vulnerabilities:', 'Generated', 'Active Vulns',
                'Model saved:', 'Final model:'
            ]):
                print(line)
            
            # Show progress bars (overwrite same line)
            elif 'it/s' in line or ('%' in line and '━' in line):
                # Clear previous progress line
                print(f"\r{line}", end='', flush=True)
                last_line = line
        
        # New line after progress bar
        if last_line:
            print()
        
        process.wait()
        duration = time.time() - start_time
        
        if process.returncode == 0:
            print(f"\n{'='*70}")
            print("✅ TRAINING COMPLETED SUCCESSFULLY")
            print(f"{'='*70}")
            print(f"Total Duration: {duration:.1f} seconds")
            print(f"{'='*70}\n")
            
            # Load training info
            info_path = Path('models') / f'{agent}_agent_info.json'
            if info_path.exists():
                with open(info_path) as f:
                    return json.load(f)
            return {'agent': agent, 'algorithm': algorithm, 'timesteps': timesteps}
        else:
            print(f"\n❌ Training failed with exit code {process.returncode}")
            return None
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None

def plot_training_results(agent_type):
    """Generate plots for the latest training session"""
    results_mgr = TrainingResults()
    visualizer = TrainingVisualizer()
    
    # Load trained info
    info_path = Path('models') / f'{agent_type}_agent_info.json'
    trained_info = results_mgr.load_session(info_path)
    
    if trained_info:
        # Plot training curve
        visualizer.plot_training_curve(trained_info, save_name=f'{agent_type}_training_curve.png')
        
        # Compare with baseline if available
        baseline_info = results_mgr.get_baseline(agent_type)
        if baseline_info:
             visualizer.plot_baseline_vs_trained(baseline_info, trained_info, agent_type)
             
    display_plots(agent_type)

def display_plots(agent_type):
    """Display generated plots in notebook"""
    from IPython.display import Image, display
    
    plot_dir = Path('plots')
    
    curve_path = plot_dir / f'{agent_type}_training_curve.png'
    baseline_path = plot_dir / f'{agent_type}_baseline_comparison.png'
    
    if curve_path.exists():
        print("Training Curve:")
        display(Image(filename=curve_path))
        
    if baseline_path.exists():
        print("Baseline Comparison:")
        display(Image(filename=baseline_path))


def load_training_history():
    """Load all training runs from saved info files"""
    models_dir = Path('models')
    if not models_dir.exists():
        return []
    
    history = []
    for info_file in models_dir.glob('*_info.json'):
        try:
            with open(info_file) as f:
                history.append(json.load(f))
        except:
            pass
    
    return sorted(history, key=lambda x: x.get('trained_at', ''), reverse=True)


def evaluate_model_live(agent, n_episodes=10):
    """Evaluate a trained model with live output"""
    venv_python = Path('venv/Scripts/python.exe')
    model_path = Path('models') / f'{agent}_agent_final.zip'
    
    if not model_path.exists():
        print(f"❌ Model not found: {model_path}")
        print("Train the model first!")
        return
    
    cmd = [
        str(venv_python),
        'train_sb3.py',
        '--evaluate', str(model_path),
        '--agent', agent,
        '--eval-episodes', str(n_episodes)
    ]
    
    print(f"\n📈 Evaluating {agent.upper()} agent ({n_episodes} episodes)...\n")
    
    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding='utf-8',
            errors='replace',
            bufsize=1,
            universal_newlines=True
        )
        
        for line in process.stdout:
            line = line.rstrip()
            if 'Gym has been unmaintained' not in line:
                print(line)
        
        process.wait()
        
    except Exception as e:
        print(f"❌ Evaluation failed: {e}")

def get_available_attacks():
    """Dynamically load available attacks from generator catalog"""
    try:
        import sys
        import os
        # Add parent directory to path to find generate_vulns_focused
        sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
        from generate_vulns_focused import VULNERABILITY_CATALOG
        
        # Mapping for display names
        display_names = {
            'xss': 'XSS (Cross-Site Scripting)',
            'sqli': 'SQL Injection',
            'rce': 'RCE (Remote Code Execution)',
            'csrf': 'CSRF (Cross-Site Request Forgery)',
            'lfi': 'LFI (Local File Inclusion)'
        }
        
        attacks = []
        for key in VULNERABILITY_CATALOG.keys():
            name = display_names.get(key, key.upper())
            attacks.append((name, key)) # Tuple (Display Name, Key)
            
        return sorted(attacks)
        
    except Exception as e:
        print(f"⚠️ Could not load catalog: {e}")
        return [('XSS', 'xss'), ('SQL Injection', 'sqli')]
