from CybORG import CybORG
from CybORG.Shared.Scenarios.ScenarioGenerator import ScenarioGenerator
from CybORG.Shared.Scenario import Scenario
from CybORG.Simulator.State import State
from CybORG.Simulator.Actions import Action
from CybORG.Shared import Observation
from CybORG.Agents import SleepAgent
import random
import json

class DVWAVulnAction(Action):
    def __init__(self, vuln_type):
        self.vuln_type = vuln_type  # e.g., 'sql_injection', 'xss'

    def execute(self, state: State) -> Observation:
        # Simulate attack: Check if vuln is active from vulns.json
        with open('/app/config/vulns.json', 'r') as f:
            vulns = json.load(f)
        if vulns.get(self.vuln_type, False):
            state.compromise_host('dvwa_host')  # Abstract compromise
            return Observation(success=True, info=f"Exploited {self.vuln_type}")
        return Observation(success=False)

class DVWAPatchAction(Action):
    def __init__(self, vuln_type):
        self.vuln_type = vuln_type

    def execute(self, state: State) -> Observation:
        # Simulate defense: Toggle vuln off (in sim, or call apply_vulns.php via subprocess)
        import subprocess
        subprocess.run(['php', '/app/apply_vulns.php', '--patch', self.vuln_type])
        return Observation(success=True, info=f"Patched {self.vuln_type}")

class DVWAScenarioGenerator(ScenarioGenerator):
    def __init__(self, num_vulns=5, default_red_agent=None):
        super().__init__()
        self.num_vulns = num_vulns
        self.default_red_agent = default_red_agent or 'RandomAttackAgent'
        # Load random vulns like your generate_vulns.py
        self.vulns = self._generate_random_vulns()

    def _generate_random_vulns(self):
        # Mimic generate_vulns.py logic
        possible_vulns = [
            'sql_injection', 'xss', 'command_injection', 'file_upload',
            'sqli_blind', 'xss_stored', 'csrf', 'lfi', 'rce', 'idor'
        ]
        # Ensure we don't try to sample more than available
        count = min(self.num_vulns, len(possible_vulns))
        return {v: random.choice([True, False]) for v in random.sample(possible_vulns, count)}

    def create_scenario(self, np_random) -> Scenario:
        # Create proper agent instances
        # CybORG expects Agent objects, not plain dicts
        agents = {
            'Red': SleepAgent(),  # Placeholder for now
            'Blue': SleepAgent()  # Placeholder blue agent
        }
        
        # Initialize scenario with agent objects
        scenario = Scenario(agents=agents)
        
        # Create the state passing the scenario reference
        state = self.create_state(scenario, np_random)
        
        # Assign state to scenario
        scenario.starting_state = state
        
        return scenario

    def create_state(self, scenario, np_random) -> State:
        state = State(scenario, np_random)
        state.add_host('dvwa_host', ip='172.17.0.2')  # Docker IP for DVWA container
        state.add_subnet('internal')
        # Add vulns as processes or sessions on host
        for vuln, active in self.vulns.items():
            if active:
                state.add_process('dvwa_host', vuln, pid=random.randint(1000, 9999))
        return state

    def get_blue_agents(self):
        return ['blue_defender']  # User or RL defender

    def get_red_agents(self):
        return [self.default_red_agent]  # RL attacker

# Simple random red agent for testing
class RandomAttackAgent:
    def get_action(self, observation, action_space):
        return random.choice(action_space)  # Random vuln exploit

if __name__ == "__main__":
    # Usage example in app.py or separate script
    sg = DVWAScenarioGenerator()
    cyborg = CybORG(sg, 'sim')
    print("CybORG environment created successfully!")