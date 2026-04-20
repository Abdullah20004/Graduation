
import json
import os
from pathlib import Path
from datetime import datetime

class TrainingResults:
    """Manages training results persistence and comparison"""
    
    def __init__(self, results_dir='./models'):
        self.results_dir = Path(results_dir)
        self.results_dir.mkdir(parents=True, exist_ok=True)
        
    def load_session(self, path):
        """Load a specific session file"""
        try:
            with open(path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading session {path}: {e}")
            return None

    def load_all_sessions(self, agent_type=None):
        """Load all training sessions, optionally filtered by agent type"""
        sessions = []
        # Look for *_info.json or custom result files
        for f in self.results_dir.glob('*_info.json'):
            session = self.load_session(f)
            if session:
                if agent_type and session.get('agent_type') != agent_type:
                    continue
                session['filename'] = f.name
                sessions.append(session)
        
        # Sort by date
        return sorted(sessions, key=lambda x: x.get('trained_at', ''), reverse=True)
        
    def get_baseline(self, agent_type):
        """Get baseline results for agent type"""
        path = self.results_dir / f'{agent_type}_baseline_info.json'
        if path.exists():
            return self.load_session(path)
        return None
        
    def compare_sessions(self, session_ids):
        """
        Compare multiple training sessions by ID (filename or index)
        Returns a dict with comparison metrics
        """
        pass # To be implemented if complex comparison logic is needed
        
    def get_best_model(self, agent_type, metric='mean_reward'):
        """Get the best performing model for an agent type"""
        sessions = self.load_all_sessions(agent_type)
        if not sessions:
            return None
            
        # Filter sessions that have the metric
        valid_sessions = [s for s in sessions if metric in s]
        if not valid_sessions:
            return None
            
        return max(valid_sessions, key=lambda x: x[metric])
