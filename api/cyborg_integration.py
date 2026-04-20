import os
import sys
import numpy as np
import inspect
import random
import json

# Detect PROJECT_ROOT relative to this file: api/cyborg_integration.py -> PROJECT_ROOT/
current_file_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_file_dir)
if project_root not in sys.path:
    sys.path.append(project_root)

# CybORG Core Imports
from CybORG import CybORG
from CybORG.Shared.Scenarios.ScenarioGenerator import ScenarioGenerator
from CybORG.Shared.Scenario import Scenario, ScenarioAgent
from CybORG.Agents import BaseAgent, SleepAgent
from CybORG.Agents.SimpleAgents.Meander import RedMeanderAgent
try:
    from CybORG.Simulator.State import State
except ImportError:
    State = object
try:
    from CybORG.Simulator.Actions import Action
except ImportError:
    Action = object
from CybORG.Simulator.SimulationController import SimulationController
from CybORG.Agents.Wrappers.BaseWrapper import BaseWrapper
from CybORG.Shared.ActionSpace import ActionSpace
from CybORG.Shared.AgentInterface import AgentInterface
from CybORG.Shared.Observation import Observation

# Import Master Data early to ensure STATIC consistency across all components
try:
    from generate_vulns_focused import VULNERABILITY_CATALOG, generate_vulnerabilities
    from dvwa_pages import DVWA_PAGES
except ImportError:
    # CRITICAL: DO NOT use a different fallback during the same session!
    # If this fails, we want it to fail loudly during development rather than silently shifting indices.
    VULNERABILITY_CATALOG = {}
    DVWA_PAGES = {}
    generate_vulnerabilities = None

def get_all_vuln_ids():
    """Get a consistent sorted list of all possible vulnerability IDs from the catalog"""
    ids = []
    if VULNERABILITY_CATALOG:
        for v_list in VULNERABILITY_CATALOG.values():
            for v in v_list:
                ids.append(v['id'])
    return sorted(list(set(ids)))

def get_all_locations():
    """Get a consistent sorted list of all possible page locations"""
    locations = set()
    if VULNERABILITY_CATALOG:
        for v_list in VULNERABILITY_CATALOG.values():
            for v in v_list:
                if 'location' in v:
                    loc = v['location']
                    if not loc.startswith("/"): loc = "/" + loc
                    locations.add(loc)
    if DVWA_PAGES:
        # Check if DVWA_PAGES is a list or dict
        pages = DVWA_PAGES if isinstance(DVWA_PAGES, list) else list(DVWA_PAGES.keys())
        for page in pages:
            loc = page
            if not loc.startswith("/"): loc = "/" + loc
            locations.add(loc)
    return sorted(list(locations))

try:
    from stable_baselines3 import PPO, A2C, DQN
except ImportError:
    PPO, A2C, DQN = None, None, None

# Removed redundant VULNERABILITY_CATALOG import/fallback (moved to top)

# Use custom Observation and BaseAgent classes for DVWA
# (CybORG's versions have incompatible signatures)
class DVWAObservation:
    """Custom observation class for DVWA actions"""
    def __init__(self, success=False, info="", reward=0, data=None, **kwargs):
        self.success = success
        self.info = info
        self.reward = reward
        self.data = data if data is not None else {}
        for k, v in kwargs.items():
            setattr(self, k, v)
    
    def __getitem__(self, key):
        return getattr(self, key, self.data.get(key))
    
    def __contains__(self, key):
        return hasattr(self, key) or key in self.data

    def get(self, key, default=None):
         if hasattr(self, key):
             return getattr(self, key)
         return self.data.get(key, default)
            
    def filter_addresses(self, ips, cidrs, include_localhost):
        # Stub method to prevent initialization errors
        return self
        
    def combine_obs(self, other_obs):
        # Helper to combine observations if needed
        return self



class DVWAActionSpace(ActionSpace):
    """Custom ActionSpace that includes vuln_id"""
    def __init__(self, actions, agent, allowed_subnets):
        super().__init__(actions, agent, allowed_subnets)
        self.vuln_id = {}
        self.location = {None: True}  # Initialize with None for scans without specific location
        self.payload = {None: True}  # Initialize with None for exploits without specific payload
        self.fuzz_type = {None: True, 'SQLi': True, 'XSS': True} # NEW: For Professional Fuzzing
        self.attack_type = {'SQLi': True, 'XSS': True} # NEW: For SmartExploit
        
    def __getitem__(self, key):
        return self.get_action_space()[key]
        
    def __contains__(self, key):
        return key in self.get_action_space()
        
    def __iter__(self):
        return iter(self.get_action_space())
        
    def get_action_space(self):
        space = super().get_action_space()
        space['vuln_id'] = self.vuln_id
        space['location'] = self.location
        space['payload'] = self.payload
        space['fuzz_type'] = self.fuzz_type
        space['attack_type'] = self.attack_type
        return space
        
    def update(self, observation, known=True):
        if observation is None:
             return
        obs_dict = getattr(observation, 'data', observation)
        
        if isinstance(obs_dict, dict):
             super().update(obs_dict, known)
        
        # Scan for vuln_ids and locations in observation
        if isinstance(obs_dict, dict):
            # If we see active_vulns or exploitable_vulns, add them to known vuln_ids
            # Also capture payloads if present in exploit details? 
            # Usually payload is input, not output, but ActionSpace needs to know valid values.
            # For now, we can add a dummy payload or capture from successful exploits.
            
            for key in ['active_vulns', 'exploitable_vulns', 'patched_vulns', 'exploited_vulns']:
                if key in obs_dict:
                    for vid in obs_dict[key]:
                        self.vuln_id[vid] = known
            
            # Also check if 'data' field is a list of vulns (from ScanAction)
            if 'data' in obs_dict and isinstance(obs_dict['data'], list):
                for v in obs_dict['data']:
                    if isinstance(v, dict):
                        if 'id' in v:
                            self.vuln_id[v['id']] = known
                        if 'location' in v:
                            self.location[v['location']] = known
            
            # If we have exploit details with payloads
            if 'details' in obs_dict and 'payload' in obs_dict['details']:
                self.payload[obs_dict['details']['payload']] = known

    def reset(self, agent):
        super().reset(agent)
        self.vuln_id = {}
        self.location = {}
        self.payload = {}

class DVWAAgentInterface(AgentInterface):
    """Custom AgentInterface that uses DVWAActionSpace"""
    def __init__(self, agent_obj, agent_name, actions, allowed_subnets, scenario, active=True, internal_only=False):
        super().__init__(agent_obj, agent_name, actions, allowed_subnets, scenario, active, internal_only)
        # Override action_space with custom one
        self.action_space = DVWAActionSpace(actions, agent_name, allowed_subnets)
        
        # CRITICAL FIX: Load ALL possible vulnerabilities and locations to ensure STATIC action space size
        # This prevents indexing mismatches between different models or episodes.
        
        # 1. Backfill vuln_ids from catalog (sorted)
        all_ids = get_all_vuln_ids()
        for vid in all_ids:
            self.action_space.vuln_id[vid] = True
            
        # 2. Backfill locations from catalog and DVWA_PAGES (sorted)
        all_locations = set()
        if VULNERABILITY_CATALOG:
            for v_list in VULNERABILITY_CATALOG.values():
                for v in v_list:
                    if 'location' in v:
                        all_locations.add(v['location'])
        
        try:
             import sys
             sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
             from dvwa_pages import DVWA_PAGES
             for page in DVWA_PAGES:
                 all_locations.add("/" + page)
        except ImportError:
             pass
             
        for loc in sorted(list(all_locations)):
            self.action_space.location[loc] = True

        if not self.action_space.vuln_id:
            self.action_space.vuln_id['placeholder_vuln'] = True
            
        # Silencing STATS prints to reduce training log noise
        # print(f"   STATS: Loaded {len(self.action_space.vuln_id)} potential actions from catalog")
        # print(f"   STATS: Loaded {len(self.action_space.location)} potential locations")
        
        action_space_dict = self.action_space.get_action_space()
        
        observation = Observation()
        init_obs = getattr(observation, 'data', {})
        
        self.agent.set_initial_values(
            action_space=action_space_dict,
            observation=init_obs
        )

class DVWABaseAgent(BaseAgent):
    """Base class for DVWA agents"""
    def __init__(self, name="dvwa_agent"):
        super().__init__(name=name)
    
    def train(self, results):
        pass

    def end_episode(self):
        pass

    def set_initial_values(self, action_space, observation):
        pass

    def get_action(self, observation, action_space=None):
        return None
        
import random
import json
import os
import subprocess
import docker

MOCK_VULNS_CONFIG = {
    "vulnerabilities": [
        {"id": "xss_stored_1", "type": "XSS", "severity": "high", "enabled": True, "location": "guestbook.php"},
        {"id": "xss_reflected_1", "type": "XSS", "severity": "medium", "enabled": True, "location": "search.php"},
        {"id": "sqli_login", "type": "SQL Injection", "severity": "critical", "enabled": True, "location": "login.php"},
        {"id": "sqli_search", "type": "SQL Injection", "severity": "high", "enabled": True, "location": "search.php"}
    ]
}

class DVWAState:
    """Standalone state that tracks DVWA vulnerabilities
    
    This is a simplified implementation that doesn't inherit from CybORG's State.
    It focuses on tracking DVWA-specific vulnerability states for XSS and SQLi attacks.
    """
    def __init__(self):
        """Initialize empty vulnerability state"""
        self.active_vulns = {}
        self.patched_vulns = set()
        self.exploited_vulns = set()
        self.discovered_vulns = set() # NEW: Track what the agent has already scanned
        self.port_scan_done = False # NEW: Track if port scan was already rewarded
        self.dir_discovery_done = False # NEW: Track if dir discovery was already rewarded
        # Minimal attributes required by CybORG
        self.subnets = {}
        self.hosts = {}
        self.sessions = {}
        self.ip_addresses = {}
        self.subnet_name_to_cidr = {}
        # PROGRESSIVE PENALTY: Track action repeats to prevent "thrashing"
        self.last_action_str = None
        self.action_repeat_count = 0
        # PROFESSIONAL RECON: Fuzzing signals per page location
        self.fuzz_signals = {} # Mapping of location -> signal_value
        
    def set_np_random(self, np_random):
        pass

    def get_true_state(self, info):
        # Return a dummy observation object or self wrapped
        return DVWAObservation(data=self.__dict__)

    def update_data_links(self):
        # Stub to prevent crashes
        pass
        
    def load_vulns_from_config(self, config_path='/var/www/html/config/vulns.json', allowed_attacks=None):
        """Load current vulnerability state from DVWA"""
        config = None
        
        # Try loading from file
        try:
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    config = json.load(f)
        except Exception as e:
            print(f"Error loading vulns: {e}")
            
        # Fallback to mock config if no file
        if config is None:
            print(f"⚠️ Config not found at {config_path}, using MOCK configuration")
            config = MOCK_VULNS_CONFIG
            
        try:
            self.active_vulns = {}
            for v in config.get('vulnerabilities', []):
                if not v.get('enabled', True):
                    continue
                
                # Filter by allowed attacks
                if allowed_attacks:
                    v_type = v.get('type', '').lower()
                    # Check if any allowed attack string is in the vulnerability type
                    # e.g. 'xss' in 'XSS', 'sql' in 'SQL Injection'
                    if not any(attack.lower() in v_type for attack in allowed_attacks):
                        continue
                
                self.active_vulns[v['id']] = v
                
            print(f"   Loaded {len(self.active_vulns)} vulnerabilities")
            if allowed_attacks:
                print(f"   Filtered by: {allowed_attacks}")
                
        except Exception as e:
            print(f"Error parsing vulns: {e}")
            self.active_vulns = {}
            
    def get_observation(self, agent_name):
        """Generate observation for agent"""
        if 'blue' in agent_name:
            # Defender sees all active vulnerabilities
            return {
                'active_vulns': list(self.active_vulns.keys()),
                'patched_vulns': list(self.patched_vulns),
                'exploited_vulns': list(self.exploited_vulns),
                'total_vulns': len(self.active_vulns)
            }
        else:
            # Attacker only sees exploitable (not patched) vulns
            exploitable = [v for v in self.active_vulns.keys() 
                          if v not in self.patched_vulns]
            return {
                'exploitable_vulns': exploitable,
                'exploited_vulns': list(self.exploited_vulns)
            }


class DVWAExploitAction(Action):
    """Action for exploiting a vulnerability"""
    def __init__(self, vuln_id, payload=None):
        super().__init__()
        self.vuln_id = vuln_id
        self.payload = payload
        self.priority = 1 
        
    def __str__(self):
        return f"Exploit {self.vuln_id}"
        
    def execute(self, state: DVWAState) -> DVWAObservation:
        """Execute exploit against DVWA"""
        # 1. Enforcement: Is it fuzzed? (Must have a signal for this page)
        vuln_type = state.active_vulns.get(self.vuln_id, {}).get('type', '').lower()
        location = state.active_vulns.get(self.vuln_id, {}).get('location')
        
        # Mapping vuln types to required signals
        type_to_signal = {'sql injection': 1.0, 'xss': 2.0}
        required_signal = type_to_signal.get(vuln_type, 0.0)
        
        current_signal = state.fuzz_signals.get(location, 0.0)
        
        if current_signal != required_signal:
             return DVWAObservation(
                 success=False,
                 info="Unprofessional Attack: Page was not fuzzed/verified first!",
                 reward=-10.0 # High penalty for non-realistic blind exploitation
             )

        if self.vuln_id not in state.active_vulns:
            return DVWAObservation(
                success=False, 
                info="Vulnerability not found",
                reward=-5.0 # High penalty for blind guessing
            )
            
        if self.vuln_id in state.exploited_vulns:
            return DVWAObservation(
                success=False, 
                info=f"Already exploited {self.vuln_id}",
                reward=-10 # Penalty for redundant action
            )
            
        if self.vuln_id in state.patched_vulns:
            return DVWAObservation(
                success=False, 
                info=f"Vulnerability {self.vuln_id} has been patched",
                reward=-2.0 # Penalty for attacking a fixed target
            )
            
        vuln = state.active_vulns[self.vuln_id]
        
        # Simulate exploit success based on vulnerability severity
        success_rate = {
            'critical': 0.9,
            'high': 0.7,
            'medium': 0.5,
            'low': 0.3
        }.get(vuln.get('severity', 'medium'), 0.5)
        
        if random.random() < success_rate:
            state.exploited_vulns.add(self.vuln_id)
            reward = {
                'critical': 100,
                'high': 50,
                'medium': 25,
                'low': 10
            }.get(vuln.get('severity', 'medium'), 10)
            
            return DVWAObservation(
                success=True, 
                info=f"Successfully exploited {self.vuln_id}",
                reward=reward
            )
        else:
            return DVWAObservation(
                success=False, 
                info=f"Exploit failed for {self.vuln_id}",
                reward=-2.0 # Reduced from -5 to stabilize reward curve
            )


class DVWAPatchAction(Action):
    """Action for patching a vulnerability"""
    def __init__(self, vuln_id):
        super().__init__()
        self.vuln_id = vuln_id
        self.priority = 1
        
    def __str__(self):
        return f"Patch {self.vuln_id}"
        
    def execute(self, state: DVWAState) -> DVWAObservation:
        """Patch vulnerability in DVWA"""
        if self.vuln_id not in state.active_vulns:
            return DVWAObservation(success=False, info="Vulnerability not found")
            
        if self.vuln_id in state.patched_vulns:
            return DVWAObservation(success=False, info="Already patched", reward=-5)
            
        state.patched_vulns.add(self.vuln_id)
        
        # Reward: Higher if patched before exploitation (proactive)
        proactive = self.vuln_id not in state.exploited_vulns
        reward = 30 if proactive else 15
        
        return DVWAObservation(
            success=True,
            info=f"Patched {self.vuln_id}",
            reward=reward,
            proactive=proactive
        )


class DVWAScanAction(Action):
    """Action for scanning to discover vulnerabilities (Defense/Blue Use)"""
    def __init__(self, location=None):
        super().__init__()
        self.location = location
        self.priority = 1
        
    def __str__(self):
        return f"Scan {self.location if self.location else 'Global'}"
        
    def execute(self, state: DVWAState) -> DVWAObservation:
        """Scan for vulnerabilities (Internal/Blue side)"""
        if self.location:
            found = [v for v in state.active_vulns.values() 
                    if v.get('location') == self.location]
        else:
            found = list(state.active_vulns.values())
            
        return DVWAObservation(
            success=True,
            info=f"Internal Scan complete for {self.location if self.location else 'Global'}",
            data=found,
            reward=10
        )


class DVWAFuzzAction(Action):
    """Action for fuzzing to discover vulnerability signatures (Signals)"""
    def __init__(self, location=None, fuzz_type=None):
        super().__init__()
        self.location = location
        self.fuzz_type = fuzz_type # e.g. 'SQLi', 'XSS'
        self.priority = 1
        
    def __str__(self):
        f_str = f" ({self.fuzz_type})" if self.fuzz_type else ""
        return f"Fuzz {self.location if self.location else 'Global'}{f_str}"
        
    def execute(self, state: DVWAState) -> DVWAObservation:
        """Fuzz a location to generate a Signal"""
        if not self.location:
             return DVWAObservation(success=False, info="Fuzzing requires a specific location", reward=-5)
             
        # Check if any active vuln on this page matches the fuzz type
        found_vuln = None
        for vuln_id, vuln in state.active_vulns.items():
            if vuln['location'] == self.location:
                v_type = vuln.get('type', '').lower()
                # Simplified matching for Demo
                if self.fuzz_type == 'SQLi' and 'sql' in v_type:
                    found_vuln = vuln
                    signal = 1.0 # SQL Error signal
                elif self.fuzz_type == 'XSS' and 'xss' in v_type:
                    found_vuln = vuln
                    signal = 2.0 # XSS Reflection signal
                elif not self.fuzz_type:
                    found_vuln = vuln
                    signal = 0.5 # Generic "Something's here" signal
        
        # Check if already fuzzed this location to prevent reward farming
        already_fuzzed = self.location in state.fuzz_signals
        
        if found_vuln:
            state.fuzz_signals[self.location] = signal
            # Significant reward for the FIRST discovery to encourage exploration
            reward = 50.0 if not already_fuzzed else -10.0 
            
            return DVWAObservation(
                success=True,
                info=f"Fuzzing revealed Signal: {signal}{' (Already Known)' if already_fuzzed else ''}",
                reward=reward,
                signal=signal
            )
        else:
            state.fuzz_signals[self.location] = 0.0 # Confirmed normal
            return DVWAObservation(
                success=False,
                info="Fuzzing revealed no anomalies (Normal 200)",
                reward=-0.5,
                signal=0.0
            )

class DVWASmartExploitAction(Action):
    """PROFESSIONAL ACTION: RL Brain decides strategy, LLM generates payload. 
    This action is ID-blind and works in real environments.
    """
    def __init__(self, location, attack_type):
        super().__init__()
        self.location = location
        self.attack_type = attack_type # 'SQLi' or 'XSS'
        self.priority = 1
        
    def __str__(self):
        return f"SmartExploit {self.location} ({self.attack_type})"
        
    def execute(self, state: DVWAState) -> DVWAObservation:
        """Logic for smart exploitation based on page signal"""
        # 1. Check if the page has been fuzzed and has a signal
        current_signal = state.fuzz_signals.get(self.location, -1.0)
        
        if current_signal == -1.0:
            return DVWAObservation(
                success=False,
                info="Unprofessional Attack: Page was not fuzzed first!",
                reward=-15.0 # High penalty for blind attacks
            )
            
        # 2. Check if the attack type matches the signal
        # Mapping: 1.0 -> SQLi, 2.0 -> XSS
        valid_signal = (self.attack_type == 'SQLi' and current_signal == 1.0) or \
                       (self.attack_type == 'XSS' and current_signal == 2.0)
                       
        if not valid_signal:
            return DVWAObservation(
                success=False,
                info=f"Ineffective Attack: Tried {self.attack_type} on Signal {current_signal}",
                reward=-2.0 # Lowered penalty to encourage trying exploits
            )

        # 3. Find the ACTUAL vulnerability in the simulation state (The reward source)
        matching_vuln_id = None
        for vid, v in state.active_vulns.items():
            if v['location'] == self.location:
                v_type = v.get('type', '').lower()
                if (self.attack_type == 'SQLi' and 'sql' in v_type) or \
                   (self.attack_type == 'XSS' and 'xss' in v_type):
                    matching_vuln_id = vid
                    break
                    
        if not matching_vuln_id or matching_vuln_id in state.patched_vulns:
             return DVWAObservation(success=False, info="Vulnerability not found or already patched", reward=-2.0)

        # 4. Success!
        if matching_vuln_id in state.exploited_vulns:
             return DVWAObservation(success=False, info="Already exploited!", reward=-2.0)
             
        state.exploited_vulns.add(matching_vuln_id)
        return DVWAObservation(
            success=True,
            info=f"SmartExploit Succeeded on {matching_vuln_id}!",
            reward=500.0 # THE JACKPOT: Forces agent to learn this path
        )

class DVWAPortScanAction(Action):
    """Action for scanning ports and services"""
    def __init__(self):
        super().__init__()
        self.priority = 1
        
    def __str__(self):
        return "Port Scan"
        
    def execute(self, state: DVWAState) -> DVWAObservation:
        """Simulate a port scan"""
        if state.port_scan_done:
            return DVWAObservation(success=False, info="Port scan already completed", reward=-2)
            
        state.port_scan_done = True
        return DVWAObservation(
            success=True,
            info="Port scan completed. Discovered open ports: 80, 443, 3306",
            data={'ports': [80, 443, 3306]},
            reward=10 # First-time reward for discovery
        )

class DVWADirectoryDiscoveryAction(Action):
    """Action for discovering hidden directories/pages"""
    def __init__(self):
        super().__init__()
        self.priority = 1
        
    def __str__(self):
        return "Directory Discovery"
        
    def execute(self, state: DVWAState) -> DVWAObservation:
        """Simulate directory discovery"""
        if state.dir_discovery_done:
            return DVWAObservation(success=False, info="Directory discovery already completed", reward=-5)
            
        state.dir_discovery_done = True
        return DVWAObservation(
            success=True,
            info="Directory discovery completed. Found 2 hidden paths.",
            data={'paths': ['/admin', '/config']},
            reward=15 # First-time reward for discovery
        )




class DVWASimulationController(SimulationController):
    """Custom SimulationController to handle DVWAState"""
    def __init__(self, scenario, agents, np_random):
        super().__init__(scenario, agents, np_random)
        
    def _create_environment(self, scenario: Scenario):
        """Set state from scenario if available, skipping standard State creation"""
        if hasattr(scenario, 'starting_state'):
            self.state = scenario.starting_state
            # Initialize empty maps to prevent crashes in other methods
            self.hostname_ip_map = {}
            self.subnet_cidr_map = {}
            self.end_turn_actions = {}  # Must be a dict
        else:
            super()._create_environment(scenario)
            
    def _create_agents(self, scenario, agent_classes: dict = None) -> dict:
        """Override to use DVWAAgentInterface"""
        agents = {}
        for agent_name in scenario.agents:
            agent_info = scenario.get_agent_info(agent_name)
            if agent_classes is not None and agent_name in agent_classes:
                agent_obj = agent_classes[agent_name]
            else:
                agent_obj = agent_info.agent_type
            
            # Ensure agent_obj has np_random if needed (copying base logic)
            agent_obj.np_random = self.np_random
            agent_obj.end_episode()
            
            agents[agent_name] = DVWAAgentInterface(
                agent_obj,
                agent_name,
                agent_info.actions,
                allowed_subnets=agent_info.allowed_subnets,
                scenario=scenario,
                active = agent_info.active,
                internal_only = agent_info.internal_only
            )
        return agents

    def execute_action(self, action: Action) -> Observation:
        """Override to capture the raw observation (and its reward)"""
        obs = action.execute(self.state)
        if not hasattr(self, 'raw_results_list'):
            self.raw_results_list = []
        self.raw_results_list.append(obs)
        return obs

    def step(self, actions, *args, **kwargs):
        """Update observations and map raw results to agents"""
        self.raw_results_list = []
        obs_map = super().step(actions, *args, **kwargs)
        
        # Map raw results back to agents based on execution order
        if not hasattr(self, 'raw_obs_per_agent'):
            self.raw_obs_per_agent = {}
        
        # CybORG executes actions in the order of actions.keys()
        for i, agent_name in enumerate(actions.keys()):
            if i < len(self.raw_results_list):
                self.raw_obs_per_agent[agent_name] = self.raw_results_list[i]
        
        return obs_map

    def get_last_observation(self, agent_name: str) -> Observation:
        """Returns the last observation for the given agent"""
        if hasattr(self, 'last_observations') and agent_name in self.last_observations:
            return self.last_observations[agent_name]
        return Observation()

class DVWACybORG(CybORG):
    """Custom CybORG class to use DVWASimulationController"""
    def _create_env_controller(self, env_config, agents):
        # In this version of CybORG, we must pass the scenario_generator to the controller
        return DVWASimulationController(self.scenario_generator, agents, self.np_random)

    def step(self, agent: str = None, action=None, messages: dict = None, skip_valid_action_check: bool = False):
        result = super().step(agent, action, messages, skip_valid_action_check)
        
        # 1. First, pull the actual reward from the Action.execute (instead of standard checkers)
        if agent:
             try:
                 ctrl = self.environment_controller
                 if hasattr(ctrl, 'raw_obs_per_agent') and agent in ctrl.raw_obs_per_agent:
                     raw_obs = ctrl.raw_obs_per_agent[agent]
                     if hasattr(raw_obs, 'reward'):
                          result.reward = float(raw_obs.reward)
             except Exception:
                 pass

        # 2. Then, apply PROGRESSIVE PENALTY for repetitive actions
        state = self.environment_controller.state
        current_action_str = str(action) if action else "None"
        
        if current_action_str == state.last_action_str:
            state.action_repeat_count += 1
        else:
            state.last_action_str = current_action_str
            state.action_repeat_count = 0
            
        # If repeating, apply an increasing penalty overlay
        if state.action_repeat_count > 0:
            # -2.0 for 1st repeat, -4.0 for 2nd, etc. 
            # CAP the penalty at -50.0 to prevent astronomical reward ranges that break gradients
            repeat_penalty = min(state.action_repeat_count * 3.0, 50.0)
            result.reward -= float(repeat_penalty)
            if hasattr(result, 'info'):
                # Ensure it's a string
                result.info = str(result.info) if result.info else ""
                result.info += f" [Repeat Penalty: -{repeat_penalty}]"
        
        return result



import sys
import os

# Try to import generator for dynamic scenario generation
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
try:
    from generate_vulns_focused import generate_vulnerabilities, VULNERABILITY_CATALOG
except ImportError:
    generate_vulnerabilities = None
    VULNERABILITY_CATALOG = {}

def get_all_vuln_ids():
    """Get a consistent sorted list of all possible vulnerability IDs from the catalog"""
    ids = []
    if VULNERABILITY_CATALOG:
        for v_list in VULNERABILITY_CATALOG.values():
            for v in v_list:
                ids.append(v['id'])
    return sorted(list(set(ids)))

class DVWAScenarioGenerator(ScenarioGenerator):
    """Scenario generator that uses actual DVWA configuration
    
    Inherits from CybORG's ScenarioGenerator base class.
    """
    
    def __init__(self, default_red_agent=None, config_path=None, allowed_attacks=None, dynamic_generation=False):
        super().__init__()
        # Priority: 1. Passed config_path, 2. Env var, 3. Container standard, 4. Relative PROJECT_ROOT
        if config_path:
            self.config_path = config_path
        elif os.environ.get('VULNS_JSON_PATH'):
            self.config_path = os.environ.get('VULNS_JSON_PATH')
        elif os.path.exists('/var/www/html/config/vulns.json'):
            self.config_path = '/var/www/html/config/vulns.json'
        else:
            # Detect PROJECT_ROOT relative to this file: api/cyborg_integration.py -> PROJECT_ROOT/
            current_dir = os.path.dirname(os.path.abspath(__file__))
            self.config_path = os.path.join(os.path.dirname(current_dir), 'config', 'vulns.json')
            
        self.allowed_attacks = allowed_attacks
        self.dynamic_generation = dynamic_generation

    def determine_done(self, env_controller):
        """
        End the episode if all vulnerabilities have been successfully exploited.
        This prevents accumulation of negative rewards after the objective is met.
        """
        state = env_controller.state
        if not hasattr(state, 'active_vulns') or not state.active_vulns:
            return False
            
        # If all active vulns are either exploited or patched, we are done!
        # (There is nothing left for the red agent to hit)
        all_resolved = all(v_id in state.exploited_vulns or v_id in state.patched_vulns 
                           for v_id in state.active_vulns)
        
        if all_resolved:
             # print("DEBUG: Scenario objective met (all vulns exploited or patched) - Ending episode.")
             pass
        return all_resolved

    def create_scenario(self, np_random=None):
        """Create DVWA-based scenario. Agents are assigned later via CybORG constructor."""
        
        # Prepare the custom DVWA state
        state = DVWAState()
        
        if self.dynamic_generation and generate_vulnerabilities:
            # Generate fresh vulnerabilities in memory for this episode
            vulns, seed = generate_vulnerabilities(
                min_vulns=3,
                max_vulns=8
            )
            # Manually load into state
            state.active_vulns = {}
            for v in vulns:
                if v.get('enabled', True):
                    state.active_vulns[v['id']] = v
            
            # Silenced verbose environment prints for cleaner training logs
            # print(f"🎲 Generated Scenario with Seed: {seed}")
            # print(f"   Active Vulns ({len(state.active_vulns)}): {', '.join(state.active_vulns.keys())}")

        else:
            # Load from static file
            state.load_vulns_from_config(self.config_path, self.allowed_attacks)
        
        # Define agents for the scenario
        # These act as placeholders/definitions for the topology
        red_agent = ScenarioAgent(
            agent_name='red_agent_0',
            team='Red',
            starting_sessions=[],
            actions=[DVWASmartExploitAction, DVWAFuzzAction, DVWAPortScanAction, DVWADirectoryDiscoveryAction],
            osint={},
            allowed_subnets=[],
            agent_type=SleepAgent(),
            active=True
        )
        # ... (rest is same)

        
        blue_agent = ScenarioAgent(
            agent_name='blue_agent_0',
            team='Blue',
            starting_sessions=[],
            actions=[DVWAPatchAction, DVWAScanAction],
            osint={},
            allowed_subnets=[],
            agent_type=SleepAgent(),
            active=True
        )
        
        # Create scenario with agents and empty reward calculators (to prevent KeyErrors)
        scenario = Scenario(
            agents={
                'red_agent_0': red_agent,
                'blue_agent_0': blue_agent
            },
            team_agents={
                'Red': ['red_agent_0'],
                'Blue': ['blue_agent_0']
            },
            team_calcs={
                'Red': [],
                'Blue': []
            }
        )
        # Attach state to scenario so DVWASimulationController can pick it up
        scenario.starting_state = state
        
        return scenario
        
    def get_action_space(self, agent_name):
        """Define available actions for each agent"""
        if 'blue' in agent_name:
            return ['patch', 'scan']
        else:
            return ['exploit', 'reconnaissance']


class RandomAttackAgent(DVWABaseAgent):
    """Simple random red agent for testing"""
    def __init__(self, name="red_agent"):
        super().__init__(name=name)
        self.starting_sessions = []
        self.default_actions = []
    
    def get_action(self, observation, action_space):
        if not observation:
            return None
            
        # Get discovered signals
        fuzz_signals = observation.get('fuzz_signals', {})
        locations_with_signals = [loc for loc, sig in fuzz_signals.items() if sig > 0]
        
        if locations_with_signals:
            # If we have signals, try a SMART exploit
            target_loc = random.choice(locations_with_signals)
            signal = fuzz_signals[target_loc]
            
            # Simple heuristic: map signal to likely attack_type
            a_type = 'SQLi' if signal == 1.0 else 'XSS'
            return DVWASmartExploitAction(location=target_loc, attack_type=a_type)
        
        # Default: Fuzz a random location
        all_locs = get_all_locations()
        if all_locs:
             target = random.choice(all_locs)
             f_type = random.choice(['SQLi', 'XSS'])
             return DVWAFuzzAction(location=target, fuzz_type=f_type)
        
        return None


class RandomDefenseAgent(DVWABaseAgent):
    """Simple random blue agent for testing"""
    def __init__(self, name="blue_agent"):
        super().__init__(name=name)
        self.starting_sessions = []
        self.default_actions = []
    
    def get_action(self, observation, action_space):
        if not observation or 'active_vulns' not in observation:
            return DVWAScanAction()
            
        active = observation['active_vulns']
        patched = observation['patched_vulns']
        
        unpatched = [v for v in active if v not in patched]
        if unpatched:
            vuln_id = random.choice(unpatched)
            return DVWAPatchAction(vuln_id)
        return None


class DVWAFlatWrapper(BaseWrapper):
    """
    Flattens DVWA observations into a fixed-size vector for RL agents.
    Vector structure per vulnerability slot (max 20):
    [IsActive, IsPatched, IsExploited]
    """
    def __init__(self, env=None, max_vulns=20, max_locations=20):
        super().__init__(env)
        self.max_vulns = max_vulns
        self.max_locations = max_locations
        self.static_vuln_ids = get_all_vuln_ids()
        self.static_locations = get_all_locations()
        
    def observation_change(self, agent, obs):
        if obs is None:
            return None
        obs_data = getattr(obs, 'data', obs)
        if obs_data is None:
            return None
        
        # Build observation vector using STATIC mapping
        obs_vec = []
        
        # 1. Vulnerability Status (EXCLUDING IsActive cheat bit)
        # Vector structure per vulnerability slot: [IsPatched, IsExploited]
        for i in range(self.max_vulns):
            if i < len(self.static_vuln_ids):
                vid = self.static_vuln_ids[i]
                
                # Patched (Blue action visibility)
                is_patched = 1.0 if vid in obs_data.get('patched_vulns', []) else 0.0
                
                # Exploited (Red action visibility)
                is_exploited = 1.0 if vid in obs_data.get('exploited_vulns', []) else 0.0
                
                obs_vec.extend([is_patched, is_exploited])
            else:
                obs_vec.extend([0.0, 0.0])
        
        # 2. Page Fuzzing Signals (The "Realistic" Source of Intel)
        # Vector structure per location slot: [SignalValue]
        fuzz_signals = obs_data.get('fuzz_signals', {})
        for i in range(self.max_locations):
            if i < len(self.static_locations):
                loc = self.static_locations[i]
                # CRITICAL: Use -1.0 for "Unknown" (haven't fuzzed yet)
                # 0.0 is used for "Confirmed Normal"
                signal = float(fuzz_signals.get(loc, -1.0))
                obs_vec.append(signal)
            else:
                obs_vec.append(-1.0)
        
        return np.array(obs_vec, dtype=np.float32)

class TrainedAgent(DVWABaseAgent):
    """Wraps a trained SB3 model to act as a CybORG agent"""
    def __init__(self, model_path, name="trained_agent", algorithm='PPO'):
        super().__init__(name=name)
        if PPO is None:
            raise ImportError("stable_baselines3 is not installed")
        
        if algorithm == 'PPO':
             self.model = PPO.load(model_path)
        elif algorithm == 'A2C':
             self.model = A2C.load(model_path)
        elif algorithm == 'DQN':
             self.model = DQN.load(model_path)
        else:
             raise ValueError(f"Unknown algorithm: {algorithm}")
             
        self.wrapper = DVWAFlatWrapper()
        
    def get_action(self, observation, action_space):
        # Flatten observation
        flat_obs = self.wrapper.observation_change(self.name, observation)
        
        # Predict action index
        action_idx, _ = self.model.predict(flat_obs, deterministic=True)
        
        # Convert index to Action object
        possible_actions = self._get_possible_actions(action_space)
        if 0 <= action_idx < len(possible_actions):
            return possible_actions[action_idx]
        return None

    def _get_possible_actions(self, action_space):
        possible_actions = []
        if 'action' not in action_space:
             return []
             
        for action in action_space['action']:
             sig_params = inspect.signature(action).parameters
             param_list = [{}]
             for p in sig_params:
                 if p == 'priority': continue
                 if p not in action_space: continue 
                 
                 if len(action_space[p]) == 1:
                     for p_dict in param_list:
                         p_dict[p] = list(action_space[p].keys())[0]
                 else:
                     new_param_list = []
                     for p_dict in param_list:
                         for key, val in action_space[p].items():
                             p_temp = p_dict.copy()
                             p_temp[p] = key
                             new_param_list.append(p_temp)
                     param_list = new_param_list
             
             for p_dict in param_list:
                 possible_actions.append(action(**p_dict))
                 
        return possible_actions

def create_cyborg_env(config_path=None, allowed_attacks=None, red_agent=None, blue_agent=None, dynamic_generation=False, **kwargs):
    """Factory function to create configured CybORG environment with both red & blue agents"""
    
    # Create the DVWA-aware scenario generator
    sg = DVWAScenarioGenerator(
        config_path=config_path,
        allowed_attacks=allowed_attacks,
        dynamic_generation=dynamic_generation
    )
    
    # Determine agents
    # If red_agent passed (class), instantiate it. Else default to RandomAttackAgent
    red_agent_instance = red_agent(name='red_agent_0') if red_agent else RandomAttackAgent(name='red_agent_0')
    
    # Blue agent
    blue_agent_instance = blue_agent(name='blue_agent_0') if blue_agent else RandomDefenseAgent(name='blue_agent_0')
    
    # Create CybORG with BOTH attacker (red) and defender (blue)
    # Use custom DVWACybORG to ensure correct controller and persistent state
    cyborg = DVWACybORG(
        scenario_generator=sg,
        environment='sim',
        agents={
            'red_agent_0': red_agent_instance,
            'blue_agent_0': blue_agent_instance
        }
    )
    
    # Optional: add wrappers if you already use them in app.py
    # from CybORG.Agents.Wrappers import OpenAIGymWrapper, FixedFlatWrapper
    # cyborg = OpenAIGymWrapper(agent_name='blue_agent_0', env=FixedFlatWrapper(cyborg))
    
    return cyborg