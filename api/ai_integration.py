import os
import sys
import logging
import time

# Add parent directory to path to allow importing from root
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from generate_vulns_focused import VULNERABILITY_CATALOG
except ImportError:
    VULNERABILITY_CATALOG = {}

from action_mapper import ActionMapper
from dvwa_controller import DVWAController
from cyborg_integration import (
    TrainedAgent, 
    RandomAttackAgent, 
    RandomDefenseAgent,
    DVWAExploitAction,
    DVWAPatchAction,
    DVWAScanAction
)

logger = logging.getLogger("AI_Integration")

class AIOrchestrator:
    """Manages the lifecycle of an AI turn"""
    
    def __init__(self, game_session):
        self.session = game_session
        self.mapper = ActionMapper()
        # Initialize session logger if not present
        if not hasattr(self.session, 'dvwa_activity_logs'):
            self.session.dvwa_activity_logs = []
        if not hasattr(self.session, 'ai_agent_logs'):
            self.session.ai_agent_logs = []
        
        # Pass session logger to controller
        self.controller = DVWAController(session_logger=self.session.dvwa_activity_logs)
        
        # Ensure agents and discovery state are initialized in the session
        self._initialize_agents()
        if not hasattr(self.session, 'ai_red_discovered_vulns'):
            self.session.ai_red_discovered_vulns = []
        if not hasattr(self.session, 'ai_red_recon_done'):
            self.session.ai_red_recon_done = False

    def _initialize_agents(self):
        """Initialize RL agents if not present"""
        models_dir = os.path.join(os.path.dirname(__file__), '..', 'models')
        
        # Initialize Red Agent
        if not hasattr(self.session, 'red_agent'):
            # Check for trained red agent
            red_model_path = os.path.join(models_dir, 'red_agent_final.zip')
            if os.path.exists(red_model_path):
                try:
                    self.session.red_agent = TrainedAgent(red_model_path, name='red_agent', algorithm='PPO')
                    logger.info(f"Initialized Red Agent (Trained PPO): {red_model_path}")
                except Exception as e:
                    logger.warning(f"Failed to load Red Agent: {e}. Falling back to Random.")
                    self.session.red_agent = RandomAttackAgent()
            else:
                self.session.red_agent = RandomAttackAgent() 
                logger.info("Initialized Red Agent (Random)")
            
        # Initialize Blue Agent
        if not hasattr(self.session, 'blue_agent'):
            # Check for trained blue agent
            blue_model_path = os.path.join(models_dir, 'blue_agent_final.zip')
            if os.path.exists(blue_model_path):
                try:
                    self.session.blue_agent = TrainedAgent(blue_model_path, name='blue_agent', algorithm='PPO')
                    logger.info(f"Initialized Blue Agent (Trained PPO): {blue_model_path}")
                except Exception as e:
                    logger.warning(f"Failed to load Blue Agent: {e}. Falling back to Random.")
                    self.session.blue_agent = RandomDefenseAgent()
            else:
                self.session.blue_agent = RandomDefenseAgent()
                logger.info("Initialized Blue Agent (Random)")

    def step(self, agent_type='red'):
        """
        Execute one turn for the specified agent.
        1. Get observation from Game Session state
        2. Query Agent for action
        3. Map Action -> Concrete Payload
        4. Execute Payload against DVWA
        5. Update Game State
        """
        from datetime import datetime
        
        def _log_ai_activity(stage, details, success=True, current_page=None):
            """Helper to log AI agent activity"""
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "agent_type": agent_type,
                "stage": stage,
                "details": details,
                "success": success,
                "current_page": current_page
            }
            self.session.ai_agent_logs.append(log_entry)
            logger.info(f"[AI-{agent_type.upper()}] {stage}: {details}")
        
        try:
            # 1. Get Observation & Action Space
            _log_ai_activity("observation", "Gathering current game state")
            observation = self._get_observation(agent_type)
            action_space = self._get_action_space(agent_type)
            
            # Log what the agent sees
            if agent_type == 'red':
                discovered = getattr(self.session, 'ai_red_discovered_vulns', [])
                exploitable = [v for v in observation.get('exploitable_vulns', [])]
                obs_summary = f"Discovered: {len(discovered)}, Exploitable: {len(exploitable)}, Already exploited: {len(observation.get('exploited_vulns', []))}"
            else:
                obs_summary = f"Active vulns: {len(observation.get('active_vulns', []))}, Patched: {len(observation.get('patched_vulns', []))}"
            _log_ai_activity("observation", obs_summary)
            
            # 1.5 SPECIAL CASE: Red Agent Reconnaissance
            # If Red agent has no discovered vulns, it MUST perform recon first
            if agent_type == 'red':
                discovered = getattr(self.session, 'ai_red_discovered_vulns', [])
                recon_done = getattr(self.session, 'ai_red_recon_done', False)
                
                # If nothing discovered yet, or occasionally to find more
                if not discovered or (not recon_done and random.random() < 0.4):
                    return self._run_ai_recon()
            
            # 2. Query Agent
            agent = self.session.red_agent if agent_type == 'red' else self.session.blue_agent
            
            _log_ai_activity("decision", f"Querying {agent.__class__.__name__} for action")
            action = agent.get_action(observation, action_space)
            
            if not action:
                _log_ai_activity("decision", "Agent chose to SLEEP (no action)", success=True)
                logger.info(f"{agent_type} agent chose NO ACTION (Sleep)")
                return {
                    "success": True,
                    "message": "Agent chose to wait (Sleep Action)"
                }
            
            # Log action details
            action_class = action.__class__.__name__
            action_details = f"Selected {action_class}"
            if hasattr(action, 'vuln_id'):
                action_details += f" targeting {action.vuln_id}"
            _log_ai_activity("decision", action_details)
                
            # 3. Map Action
            # Pass session state (vulns) to mapper so it knows URLs
            # We mock a 'state' object that has active_vulns dict
            mock_state = type('MockState', (), {'active_vulns': {v['id']: v for v in self.session.vulnerabilities if v.get('enabled')}})()
            
            mapped_action = self.mapper.map_action(action, mock_state)
            
            # Log mapped action with page info
            target_page = mapped_action.get('location', 'unknown')
            action_type_str = mapped_action.get('type', 'unknown')
            _log_ai_activity("mapping", f"Mapped to {action_type_str} on page {target_page}", current_page=target_page)
            
            # 4. Execute Payload
            _log_ai_activity("execution", f"Executing {action_type_str} on {target_page}", current_page=target_page)
            execution_result = self.controller.execute_action(mapped_action)
            
            # Log execution result
            if execution_result.get('success'):
                _log_ai_activity("execution", f"Successfully executed {action_type_str} on {target_page}", success=True, current_page=target_page)
                
                # Log to DVWA activity logs as well
                dvwa_log_entry = {
                    "timestamp": time.time(),
                    "type": action_type_str,
                    "location": target_page,
                    "success": True,
                    "details": f"AI {agent_type.upper()} {action_type_str} on {target_page}",
                    "payload": mapped_action.get('payload', '')
                }
                self.session.dvwa_activity_logs.append(dvwa_log_entry)
            else:
                _log_ai_activity("execution", f"Failed: {execution_result.get('message', 'Unknown error')}", success=False, current_page=target_page)
            
            # 5. Update Game State based on action type
            vuln_id = mapped_action.get('vuln_id')
            logger.info(f"[DEBUG] Checking game state update: vuln_id={vuln_id}, success={execution_result.get('success')}, action_type={action_type_str}")
            
            if execution_result.get('success') and vuln_id:
                vuln = next((v for v in self.session.vulnerabilities if v['id'] == vuln_id and v.get('enabled')), None)
                logger.info(f"[DEBUG] Found vulnerability: {vuln is not None}")
                
                if action_type_str == 'patch' and vuln:
                    # Check if not already patched
                    already_patched = vuln_id in [d['vuln_id'] for d in self.session.defenses_applied]
                    logger.info(f"[DEBUG] Patch check: already_patched={already_patched}")
                    
                    if not already_patched:
                        # Check if proactive (not yet exploited)
                        proactive = vuln_id not in [e['vuln_id'] for e in self.session.exploits_found]
                        points = 30 if proactive else 15
                        
                        self.session.score['defender'] += points
                        self.session.defenses_applied.append({
                            "vuln_id": vuln_id,
                            "timestamp": time.time(),
                            "points": points,
                            "fix_command": "ai_agent_patch",
                            "proactive": proactive
                        })
                        logger.info(f"[GAME STATE] Defender scored {points} points for patching {vuln_id} ({'proactive' if proactive else 'reactive'})")
                
                elif action_type_str == 'exploit' and vuln:
                    # Check if not already exploited and not patched
                    already_exploited = vuln_id in [e['vuln_id'] for e in self.session.exploits_found]
                    already_patched = vuln_id in [d['vuln_id'] for d in self.session.defenses_applied]
                    logger.info(f"[DEBUG] Exploit check: already_exploited={already_exploited}, already_patched={already_patched}")
                    
                    if not already_exploited and not already_patched:
                        # Award points based on severity
                        points = {
                            "critical": 100,
                            "high": 50,
                            "medium": 25,
                            "low": 10
                        }.get(vuln.get('severity', 'low').lower(), 10)
                        
                        logger.info(f"[DEBUG] Awarding {points} points for {vuln.get('severity')} vuln")
                        
                        self.session.score['attacker'] += points
                        self.session.exploits_found.append({
                            "vuln_id": vuln_id,
                            "timestamp": time.time(),
                            "points": points,
                            "details": {"payload": mapped_action.get('payload', ''), "method": "ai_agent"}
                        })
                        logger.info(f"[GAME STATE] Attacker scored {points} points for exploiting {vuln_id} ({vuln.get('severity')})")
            
            return {
                "success": True,
                "agent": agent_type,
                "original_action": str(action),
                "mapped_action": {
                    "type": mapped_action.get("type"),
                    "vuln_id": mapped_action.get("vuln_id"),
                    "location": mapped_action.get("location"),
                    "description": mapped_action.get("description")
                },
                "execution_result": {
                    "success": execution_result.get("success"),
                    "message": execution_result.get("message", "")
                },
                "current_page": target_page
            }
            
        except Exception as e:
            logger.error(f"AI Step Failed: {e}")
            _log_ai_activity("error", f"Step failed: {str(e)}", success=False)
            import traceback
            traceback.print_exc()
            return {"success": False, "message": str(e)}

    def _get_observation(self, agent_type):
        """Construct observation dictionary from session state"""
        # This matches what RandomAttackAgent expects AND what DVWAFlatWrapper expects
        active_ids = [v['id'] for v in self.session.vulnerabilities if v.get('enabled')]
        patched_ids = [d['vuln_id'] for d in self.session.defenses_applied]
        exploited_ids = [e['vuln_id'] for e in self.session.exploits_found]
        
        if agent_type == 'red':
             # NEW: Filter by what the AI has DISCOVERED
             discovered = getattr(self.session, 'ai_red_discovered_vulns', [])
             exploitable = [vid for vid in active_ids if vid not in patched_ids and vid in discovered]
             
             return {
                 'exploitable_vulns': exploitable,
                 'exploited_vulns': exploited_ids,
                 # AI only sees what it has 'scanned' or 'found'
                 'active_vulns': [vid for vid in active_ids if vid in discovered], 
                 'patched_vulns': [vid for vid in patched_ids if vid in discovered]
             }
        else:
             # Defender sees all active vulnerabilities (IDS/DPI simulation)
             return {
                 'active_vulns': active_ids,
                 'patched_vulns': patched_ids,
                 'exploited_vulns': exploited_ids
             }

    def _get_action_space(self, agent_type):
        """
        Construct the action space dictionary required by TrainedAgent to reconstruct discrete actions.
        MUST match the logic in DVWAAgentInterface to ensure correct action mapping.
        """
        vuln_id_map = {}
        location_map = {None: True}
        
        # 1. Load from Session (Active)
        for v in self.session.vulnerabilities:
            if v.get('enabled'):
                vuln_id_map[v['id']] = True
                if 'location' in v:
                    location_map[v['location']] = True
                    
        # 2. Load from Catalog (All possible - ensures static size)
        if VULNERABILITY_CATALOG:
            for attack_type, vulns in VULNERABILITY_CATALOG.items():
                for v in vulns:
                    vuln_id_map[v['id']] = True
                    if 'location' in v:
                        location_map[v['location']] = True
        
        if not vuln_id_map:
             vuln_id_map['placeholder_vuln'] = True

        # Define available action classes
        if agent_type == 'red':
            actions = [DVWAExploitAction, DVWAScanAction]
        else:
            actions = [DVWAPatchAction, DVWAScanAction]

        return {
            'action': actions,
            'vuln_id': vuln_id_map,
            'location': location_map,
            'payload': {None: True} # Add payload map if needed by actions
        }

    # =========================================================================
    # AI RED TOOLS (Simulated Reconnaissance)
    # =========================================================================

    def _run_ai_recon(self):
        """Perform simulated reconnaissance (Port Scan or Directory Discovery)"""
        import random
        from datetime import datetime
        import time
        
        # Decide which tool to use
        tool = random.choice(['Port Scan', 'Directory Discovery'])
        
        # Log start
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "agent_type": "red",
            "stage": "tool_execution",
            "details": f"Launching automated {tool}...",
            "success": True
        }
        self.session.ai_agent_logs.append(log_entry)
        
        # Simulate delay
        time.sleep(1) 
        
        # Discovery Logic: Find a subset of enabled vulnerabilities
        discovery_pool = [v for v in self.session.vulnerabilities if v.get('enabled')]
        already_discovered = getattr(self.session, 'ai_red_discovered_vulns', [])
        
        newly_found = []
        if tool == 'Port Scan':
            # Port scan finds 1-3 random vulns
            sample_size = min(random.randint(2, 4), len(discovery_pool))
            candidates = random.sample(discovery_pool, sample_size)
            newly_found = [v['id'] for v in candidates if v['id'] not in already_discovered]
            details = f"Nmap results: Discovered {len(candidates)} services. Possible entry points: {', '.join(newly_found) if newly_found else 'none new'}."
        else:
            # Dir discovery finds specific paths
            sample_size = min(random.randint(1, 3), len(discovery_pool))
            candidates = random.sample(discovery_pool, sample_size)
            newly_found = [v['id'] for v in candidates if v['id'] not in already_discovered]
            details = f"Gobuster results: Found {len(candidates)} hidden directories. Intersting endpoints found: {', '.join([v['location'] for v in candidates])}."

        # Update session
        self.session.ai_red_discovered_vulns.extend(newly_found)
        self.session.ai_red_recon_done = True
        
        # Log results
        result_entry = {
            "timestamp": datetime.now().isoformat(),
            "agent_type": "red",
            "stage": "tool_result",
            "details": details,
            "success": True
        }
        self.session.ai_agent_logs.append(result_entry)
        
        # Log to activity feed as well
        self.session.dvwa_activity_logs.append({
            "timestamp": time.time(),
            "type": "recon",
            "location": "network",
            "success": True,
            "details": f"AI Attacker executed {tool} - {len(newly_found)} new leads found",
            "payload": f"automated_{tool.lower().replace(' ', '_')}"
        })
        
        return {
            "success": True,
            "agent": "red",
            "mapped_action": {
                "type": "recon",
                "description": f"Executed {tool}"
            },
            "execution_result": {
                "success": True,
                "message": details
            }
        }
