"""
HackOps Flask API Bridge - Enhanced with Code Viewing & Editing
"""
# api/app.py
import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="gym")

from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
import docker
import json
import os
import subprocess
import time
from datetime import datetime
import tempfile
import tarfile
import io
from cyborg_scenario import DVWAScenarioGenerator, CybORG
try:
    from zapv2 import ZAPv2
except ImportError:
    ZAPv2 = None

# Red (attacker) and Blue (defender) baseline agents
from CybORG.Agents.SimpleAgents.Meander import RedMeanderAgent
from CybORG.Agents import SleepAgent
from cyborg_integration import (
    create_cyborg_env, 
    DVWAExploitAction, 
    DVWAPatchAction,
    DVWAScanAction,
    RandomAttackAgent
)
from ai_integration import AIOrchestrator
from dvwa_pages import DVWA_PAGES
from tools_registry import ToolsRegistry
from dvwa_controller import DVWAController
from bs4 import BeautifulSoup

app = Flask(__name__)
CORS(app)

# Docker client
client = docker.from_env()

# Game state storage
game_sessions = {}

# Environment status tracking
ENV_STATUS_OFFLINE = "offline"
ENV_STATUS_STARTING = "starting"
ENV_STATUS_ONLINE = "online"
current_env_status = ENV_STATUS_OFFLINE

# Note: CybORG environment is created on-demand in endpoints using create_cyborg_env()
# Global initialization commented out to avoid startup errors
# sg = DVWAScenarioGenerator(default_red_agent=RandomAttackAgent)
# cyborg = CybORG(sg, 'sim')
# wrapped_cyborg = OpenAIGymWrapper(agent_name='blue_defender', env=FixedFlatWrapper(cyborg))


@app.route('/start_simulation', methods=['POST'])
def start_simulation():
    """Legacy endpoint - creates a new simulation session"""
    try:
        # Create environment on-demand
        cyborg_env = create_cyborg_env()
        session_id = f"sim_{int(time.time())}"
        
        # Store in session
        game_sessions[session_id] = {
            'cyborg_env': cyborg_env,
            'vulns': {}  # Will be populated from config
        }
        
        return jsonify({
            'status': 'success',
            'session_id': session_id,
            'message': 'Simulation started'
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# Helper function to find the target container robustly
def get_target_container():
    """
    Finds the target DVWA container using labels first, then falling back to known names.
    """
    try:
        # 1. Try finding by label (best for Docker Compose)
        # Match by service name 'target'
        # We also look for labels that indicate it's part of our project
        filters = {"label": ["com.docker.compose.service=target"]}
        containers = client.containers.list(all=True, filters=filters)
        
        # If we found multiple, prefer the running one
        if containers:
            for c in containers:
                if c.status == 'running':
                    return c
            return containers[0] # Return the first found (even if stopped)
            
        # 2. Fallback to name-based lookup
        # Priority: 1. explicit name, 2. compose name (hyphen), 3. compose name (underscore)
        container_names = ['hackops-target', 'hackops-project-target-1', 'hackops-project_target_1']
        for name in container_names:
            try:
                c = client.containers.get(name)
                return c
            except docker.errors.NotFound:
                continue
    except Exception as e:
        print(f"[DEBUG] get_target_container error: {e}")
    
    return None

@app.route('/attack', methods=['POST'])
def attack():
    """Legacy attack endpoint"""
    data = request.json
    session_id = data.get('session_id')
    
    if not session_id or session_id not in game_sessions:
        return jsonify({'status': 'error', 'message': 'Invalid session'}), 400
    
    try:
        container = get_target_container()
        
        if not container:
            return jsonify({'status': 'error', 'message': 'Target container not found'}), 404
            

        result = container.exec_run(f"php /app/apply_vulns.php --exploit {data.get('vuln_type', 'unknown')}")
        return jsonify({
            'status': 'success',
            'message': 'Attack executed',
            'result': result.output.decode() if result.output else ''
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/defend', methods=['POST'])
def defend():
    """Legacy defend endpoint"""
    data = request.json
    session_id = data.get('session_id')
    
    if not session_id or session_id not in game_sessions:
        return jsonify({'status': 'error', 'message': 'Invalid session'}), 400
    
    return jsonify({
        'status': 'success',
        'message': 'Defense action recorded'
    })


# Get paths relative to the current script location
# api/app.py -> PROJECT_ROOT is HackOps/
API_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(API_DIR)
CONFIG_PATH = os.path.join(PROJECT_ROOT, 'config', 'vulns.json')
LOGS_PATH = os.path.join(PROJECT_ROOT, 'logs', 'vulnerabilities.log')

class GameSession:
    def __init__(self, session_id, difficulty='easy', player_role='red'):
        self.session_id = session_id
        self.start_time = time.time()
        self.vulnerabilities = []
        self.exploits_found = []
        self.defenses_applied = []
        self.score = {"attacker": 0, "defender": 0}
        self.container_id = None
        self.seed = None
        self.code_modifications = {}
        self.cyborg_env = None
        self.cyborg_state = None
        self.ai_orchestrator = None # Initialize lazily
        # Difficulty & role settings
        self.difficulty = difficulty   # 'easy' | 'medium' | 'hard'
        self.player_role = player_role # 'red' | 'blue'
        # Logging storage
        self.dvwa_activity_logs = []  # Normal website activity logs
        self.ai_agent_logs = []  # AI agent decision logs
        
    def to_dict(self):
        return {
            "session_id": self.session_id,
            "elapsed_time": int(time.time() - self.start_time),
            "vulnerabilities": self.vulnerabilities,
            "exploits_found": self.exploits_found,
            "defenses_applied": self.defenses_applied,
            "score": self.score,
            "seed": self.seed,
            "difficulty": self.difficulty,
            "player_role": self.player_role,
            "code_modifications": self.code_modifications,
            "dvwa_activity_logs_count": len(self.dvwa_activity_logs),
            "ai_agent_logs_count": len(self.ai_agent_logs)
        }

# ============================================================================
# CODE VIEWING & EDITING ENDPOINTS
# ============================================================================

@app.route('/api/code/view/<session_id>/<vuln_id>', methods=['GET'])
def view_vulnerability_code(session_id, vuln_id):
    """Get the source code for a specific vulnerability"""
    try:
        if session_id not in game_sessions:
            return jsonify({"status": "error", "message": "Session not found"}), 404
        
        session = game_sessions[session_id]
        vuln = next((v for v in session.vulnerabilities if v['id'] == vuln_id), None)
        
        if not vuln:
            return jsonify({"status": "error", "message": "Vulnerability not found"}), 404
        
        # Get the container
        container = get_target_container()
        if not container or container.status != 'running':
             return jsonify({"status": "error", "message": "Container not running or not found"}), 500

        
        # Read file from container
        file_path = f"/var/www/html{vuln['location']}"
        result = container.exec_run(f'cat {file_path}')
        
        if result.exit_code != 0:
            return jsonify({
                "status": "error", 
                "message": f"Could not read file: {result.output.decode()}"
            }), 500
        
        source_code = result.output.decode('utf-8')
        
        # Store original code if not already stored
        if vuln_id not in session.code_modifications:
            session.code_modifications[vuln_id] = {
                "original_code": source_code,
                "modified": False
            }
        
        is_modified = session.code_modifications[vuln_id].get('modified', False)
        
        return jsonify({
            "status": "success",
            "vuln_id": vuln_id,
            "location": vuln['location'],
            "source_code": source_code,
            "is_modified": is_modified,
            "language": "php",
            "description": vuln['description'],
            "severity": vuln['severity'],
            "fix_command": vuln.get('fix_command', ''),
            "type": vuln['type']
        }), 200
        
    except Exception as e:
        # Use repr(e) or similar to avoid direct printing of problematic characters
        print(f"[ERROR] view_vulnerability_code: {type(e).__name__}: {str(e).encode('utf-8', errors='replace').decode('utf-8')}")
        import traceback
        traceback.print_exc()
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/api/code/update/<session_id>/<vuln_id>', methods=['POST'])
def update_vulnerability_code(session_id, vuln_id):
    """Update the source code for a vulnerability (defender only)"""
    try:
        if session_id not in game_sessions:
            return jsonify({"status": "error", "message": "Session not found"}), 404
        
        data = request.json
        new_code = data.get('code')
        
        if not new_code:
            return jsonify({"status": "error", "message": "No code provided"}), 400
        
        session = game_sessions[session_id]
        vuln = next((v for v in session.vulnerabilities if v['id'] == vuln_id), None)
        
        if not vuln:
            return jsonify({"status": "error", "message": "Vulnerability not found"}), 404
        
        # Get the container
        container = get_target_container()
        if not container or container.status != 'running':
             return jsonify({"status": "error", "message": "Container not running or not found"}), 500

        
        # Write new code to container
        file_path = f"/var/www/html{vuln['location']}"
        
        # Create a temporary file with the new code using UTF-8 encoding
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', delete=False, suffix='.php') as tmp:
            tmp.write(new_code)
            tmp_path = tmp.name
        
        try:
            start_val = time.time()
            # 1. Pre-patch syntax linting
            lint_result = lint_php_code(container, tmp_path)
            print(f"[DEBUG] Linting took {time.time() - start_val:.2f}s")
            
            if not lint_result['success']:
                penalty = 100
                session.score['defender'] -= penalty
                
                # Log the breakage
                from datetime import datetime
                session.dvwa_activity_logs.append({
                    "timestamp": datetime.now().isoformat(),
                    "action_type": "error",
                    "location": vuln['location'],
                    "description": f"DEFENDER BROKE THE PAGE (Syntax Error) with patch for {vuln_id}: {lint_result['message']}",
                    "success": False,
                    "payload": None
                })
                
                return jsonify({
                    "status": "success",
                    "type": "warning",
                    "message": f"Patch REJECTED due to SYNTAX ERROR: {lint_result['message']}. Penalty: -100 points.",
                    "points_awarded": -penalty,
                    "is_broken": True
                }), 200

            # Get timestamp before deployment
            deploy_time = int(time.time())

            # 2. Copy file to container
            start_copy = time.time()
            with open(tmp_path, 'rb') as f:
                container.put_archive(
                    '/var/www/html' + os.path.dirname(vuln['location']),
                    create_tarball(os.path.basename(vuln['location']), f.read())
                )
            print(f"[DEBUG] Copying to container took {time.time() - start_copy:.2f}s")
            
            # Post-patch health check (HTML output)
            start_health = time.time()
            health_status = check_page_health(vuln['location'])
            print(f"[DEBUG] Health check took {time.time() - start_health:.2f}s")
            
            # Post-patch Apache error log check
            start_logs = time.time()
            log_status = check_apache_logs(container, deploy_time)
            print(f"[DEBUG] Log check took {time.time() - start_logs:.2f}s")
            
            is_broken = not health_status['success'] or not log_status['success']
            
            # Default response values
            status_type = "success"
            message = "Patch applied successfully."
            points_awarded = 0
            
            # Combine error messages
            error_msg = ""
            if not health_status['success']:
                error_msg = health_status['message']
            elif not log_status['success']:
                error_msg = log_status['message']
                
            # Track modification
            session.code_modifications[vuln_id] = {
                "timestamp": time.time(),
                "original_code": session.code_modifications.get(vuln_id, {}).get('original_code', ''),
                "modified": True,
                "is_broken": is_broken,
                "error_message": error_msg
            }
            
            if is_broken:
                # Penalty for breaking the page
                penalty = 100
                session.score['defender'] -= penalty
                points_awarded = -penalty
                message = f"Patch applied but PAGE IS BROKEN: {error_msg}. Penalty: -100 points."
                status_type = "warning"
                
                # Log the breakage
                from datetime import datetime
                session.dvwa_activity_logs.append({
                    "timestamp": datetime.now().isoformat(),
                    "action_type": "error",
                    "location": vuln['location'],
                    "description": f"DEFENDER BROKE THE PAGE with patch for {vuln_id}: {error_msg}",
                    "success": False,
                    "payload": None
                })
            else:
                # 5. NEW: Check if the patch is actually secure (Exploit Verification)
                # We try some standard payloads for the vulnerability type
                standard_payloads = {
                    'sqli': ["' or 1=1 --", '" or 1=1 --', "' union select 1,2,3 --"],
                    'xss': ["<script>alert(1)</script>", "<img src=x onerror=alert(1)>"],
                    'lfi': ["../../../../etc/passwd", "php://filter/read=convert.base64-encode/resource=index.php"],
                    'ssrf': ["http://127.0.0.1:80", "file:///etc/passwd"],
                    'rce': ["; id", "| whoami", "`uname -a`"]
                }
                
                vulnerable = False
                tested_payloads = standard_payloads.get(vuln['type'], [])
                
                # Optimized: only test the strongest/first payload for speed
                if tested_payloads:
                    p = tested_payloads[0]
                    start_exploit = time.time()
                    if real_exploit_check(vuln['location'], vuln['type'], p):
                        vulnerable = True
                    print(f"[DEBUG] Exploit check ({vuln['type']} on {p}) took {time.time() - start_exploit:.2f}s")
                
                if vulnerable:
                    message = "Patch applied and page is running, but THE VULNERABILITY STILL EXISTS! 0 points awarded."
                    status_type = "info"
                    points_awarded = 0
                else:
                    # Award points if not already defended
                    if vuln_id not in [d['vuln_id'] for d in session.defenses_applied]:
                        points = 30  # Full points for manual code fix
                        session.score['defender'] += points
                        points_awarded = points
                        
                        session.defenses_applied.append({
                            "vuln_id": vuln_id,
                            "timestamp": time.time(),
                            "points": points,
                            "fix_command": "manual_code_edit",
                            "proactive": vuln_id not in [e['vuln_id'] for e in session.exploits_found]
                        })
                        message = "Excellent! Code updated and vulnerability secured. +30 points."

                # 6. NEW: Run Semgrep SAST for additional feedback
                start_semgrep = time.time()
                semgrep_report = ToolsOrchestrator.run_semgrep(tmp_path)
                print(f"[DEBUG] Semgrep took {time.time() - start_semgrep:.2f}s")
                
                if semgrep_report.get('results'):
                    message += f" [SAST Warning: Semgrep found {len(semgrep_report['results'])} potential issues in your code.]"
            
            return jsonify({
                "status": "success",
                "type": status_type,
                "message": message,
                "points_awarded": points_awarded,
                "is_broken": is_broken
            }), 200
            
        finally:
            os.unlink(tmp_path)
        
    except Exception as e:
        # Safely print the error message even if it contains non-terminal characters
        error_msg = str(e).encode('ascii', errors='replace').decode('ascii')
        print(f"[ERROR] update_vulnerability_code: {error_msg}")
        import traceback
        traceback.print_exc()
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/api/code/test/<session_id>/<vuln_id>', methods=['POST'])
def test_exploit(session_id, vuln_id):
    """Test an exploit payload (attacker only)"""
    try:
        if session_id not in game_sessions:
            return jsonify({"status": "error", "message": "Session not found"}), 404
        
        data = request.json
        payload = data.get('payload')
        
        if not payload:
            return jsonify({"status": "error", "message": "No payload provided"}), 400
        
        session = game_sessions[session_id]
        vuln = next((v for v in session.vulnerabilities if v['id'] == vuln_id), None)
        
        if not vuln:
            return jsonify({"status": "error", "message": "Vulnerability not found"}), 404
        
        # Check if already defended
        if vuln_id in [d['vuln_id'] for d in session.defenses_applied]:
            return jsonify({
                "status": "success",
                "success": False,
                "message": "Exploit failed. Vulnerability has been patched.",
                "payload": payload
            }), 200
        
        # Try real exploit test first if container is up
        is_successful = False
        try:
            is_successful = real_exploit_check(vuln['location'], vuln['type'], payload)
        except:
            # Fallback to simulation if real check fails
            is_successful = simulate_exploit_test(vuln, payload)
        
        # Award points if successful and not already exploited
        points_awarded = 0
        if is_successful and vuln_id not in [e['vuln_id'] for e in session.exploits_found]:
            points = {
                "critical": 100,
                "high": 50,
                "medium": 25,
                "low": 10
            }.get(vuln['severity'], 10)
            
            session.score['attacker'] += points
            points_awarded = points
            
            session.exploits_found.append({
                "vuln_id": vuln_id,
                "timestamp": time.time(),
                "points": points,
                "details": {"payload": payload}
            })
        
        return jsonify({
            "status": "success",
            "success": is_successful,
            "message": "Exploit successful! Vulnerability compromised." if is_successful else "Exploit failed. Try a different approach.",
            "payload": payload,
            "points_awarded": points_awarded
        }), 200
        
    except Exception as e:
        error_msg = str(e).encode('ascii', errors='replace').decode('ascii')
        print(f"[ERROR] test_exploit: {error_msg}")
        return jsonify({"status": "error", "message": str(e)}), 500


def real_exploit_check(location, vuln_type, payload):
    """Perform a real HTTP request to verify if an exploit works"""
    try:
        import requests
        url = f"http://localhost:8080{location}"
        
        # Determine method and params
        if "login" in location or "review" in location or "upload" in location:
            method = "POST"
            data = {"username": payload, "password": "password", "review": payload, "input": payload, "xml": payload}
            resp = requests.post(url, data=data, timeout=3)
        else:
            method = "GET"
            params = {"q": payload, "id": payload, "category": payload, "code": payload, "url": payload, "file": payload}
            resp = requests.get(url, params=params, timeout=3)
            
        content = resp.text
        
        # Heuristics for success
        if vuln_type == 'sqli':
            # Look for SQL syntax errors or reflections indicates lack of filtering
            indicators = ["SQL syntax", "mysql_fetch_array", "mysqli_query", "PDOException"]
            return any(ind in content for ind in indicators) or payload in content
        elif vuln_type == 'xss':
            # Look for raw payload in response (not escaped)
            return payload in content and htmlspecialchars_sim(payload) not in content
        elif vuln_type == 'lfi' or vuln_type == 'rce':
            # Look for system indicators
            return "root:x:0:0" in content or "uid=" in content or "www-data" in content
            
        # Fallback to simulation logic if we can't be sure
        return simulate_exploit_test({'type': vuln_type}, payload)
    except:
        return False

def htmlspecialchars_sim(text):
    return text.replace("&", "&amp;").replace('"', "&quot;").replace("'", "&#039;").replace("<", "&lt;").replace(">", "&gt;")

def simulate_exploit_test(vuln, payload):
    """Simulate testing an exploit (simplified pattern matching)"""
    vuln_type = vuln['type']
    payload_lower = payload.lower()
    
    # Simple pattern matching for demonstration
    patterns = {
        'sqli': ["'", '"', 'or', 'union', 'select', '--', '/*'],
        'xss': ['<script', 'onerror', 'onload', 'javascript:', '<img'],
        'lfi': ['../', '/etc/passwd', '/etc/shadow', 'file://'],
        'rce': [';', '|', '&', '`', '$', 'bash', 'sh'],
        'xxe': ['<!entity', 'system', '<!doctype'],
        'ssrf': ['http://', 'file://', 'gopher://', '127.0.0.1', 'localhost'],
        'csrf': ['<form', 'method=', 'action='],
        'idor': ['id=', 'user=', '../'],
    }
    
    if vuln_type in patterns:
        return any(pattern in payload_lower for pattern in patterns[vuln_type])
    
    return False


def lint_php_code(container, tmp_path):
    """Run PHP linter on a temporary file in the container"""
    try:
        # Copy the file to a temporary location in the container
        dest_path = f"/tmp/lint_{int(time.time())}.php"
        with open(tmp_path, 'rb') as f:
            tar_data = create_tarball(os.path.basename(dest_path), f.read())
            container.put_archive('/tmp/', tar_data)
            
        # Run lint
        result = container.exec_run(f"php -l {dest_path}")
        
        # Clean up
        container.exec_run(f"rm {dest_path}")
        
        # PHP linter returns 0 on success, >0 on failure
        # Output looks like "No syntax errors detected in..." or "Parse error: syntax error..."
        output = result.output.decode('utf-8', errors='ignore')
        success = result.exit_code == 0
        
        return {
            "success": success,
            "message": output.strip()
        }
    except Exception as e:
        print(f"[ERROR] lint_php_code: {e}")
        return {"success": False, "message": f"Linting failed: {e}"}

def check_apache_logs(container, since_timestamp):
    """Check Apache error logs for fatal PHP errors occurring after a given timestamp"""
    try:
        # Instead of tailing a file (which might be a blocking symlink to /dev/stderr),
        # we use the Docker SDK's logs() method.
        # since_timestamp is unix time.
        logs_bytes = container.logs(
            since=since_timestamp, 
            stderr=True, 
            stdout=False, 
            tail=100
        )
        
        if not logs_bytes:
            return {"success": True, "message": "No new logs"}
            
        log_output = logs_bytes.decode('utf-8', errors='ignore')
        
        # We look for "PHP Fatal error", "PHP Parse error", "Uncaught Error"
        lines = log_output.strip().split('\n')
        
        fatal_errors = []
        for line in reversed(lines):
            # Also catch Warning and Notice (critical for detecting undefined variable crashes in logic)
            if any(err in line for err in ["PHP Fatal error", "PHP Parse error", "Uncaught", "PHP Warning", "PHP Notice"]):
                fatal_errors.append(line)
                
        if fatal_errors:
            # Extract just the error message part to be readable
            msg = fatal_errors[0]
            if "] " in msg:
                msg = msg.split("] ")[-1]
            return {
                "success": False,
                "message": msg
            }
            
        return {"success": True, "message": "No relevant errors found in logs"}
    except Exception as e:
        print(f"[ERROR] check_apache_logs: {e}")
        return {"success": True, "message": f"Log check failed: {e}"}


def check_page_health(location):
    """
    Check if a page is loading correctly in the DVWA container
    """
    try:
        import requests
        # We try to access the page from the host side
        # Assuming the container is mapped to 8080
        url = f"http://localhost:8080{location}"
        
        # We use a shorter timeout for local environment (2s)
        response = requests.get(url, timeout=2)
        
        if response.status_code >= 500:
            return {
                "success": False, 
                "message": f"HTTP Error {response.status_code}"
            }
        
        # Check for PHP errors in the content
        content = response.text
            
        # Common PHP error strings (without colons to handle HTML tags)
        php_errors = ["Parse error", "Fatal error", "syntax error", "Fatal", "Warning", "Notice"]
        for error in php_errors:
            if error in content:
                # Extract snippet of the error
                error_idx = content.find(error)
                snippet = content[error_idx:error_idx+100]
                return {
                    "success": False, 
                    "message": f"PHP Software Error: {snippet}"
                }
                
        # If the page is completely blank or extremely short, it's a silent crash
        # Most DVWA HTML pages are at least a few hundred bytes
        if len(content) < 15:
            return {
                "success": False,
                "message": "Page is blank or returned no HTML content (silent crash)"
            }
        
        return {"success": True}
        
    except Exception as e:
        return {
            "success": False, 
            "message": f"Connection failed: {str(e)}"
        }


def create_tarball(filename, content):
    """Create a tar archive for docker put_archive"""
    tar_stream = io.BytesIO()
    tar = tarfile.TarFile(fileobj=tar_stream, mode='w')
    
    tarinfo = tarfile.TarInfo(name=filename)
    tarinfo.size = len(content)
    tarinfo.mtime = time.time()
    
    tar.addfile(tarinfo, io.BytesIO(content))
    tar.close()
    
    tar_stream.seek(0)
    return tar_stream.read()


# ============================================================================
# EXISTING ENDPOINTS (keeping all original functionality)
# ============================================================================

@app.route('/api/environment/start', methods=['POST'])
def start_environment():
    """Start a new vulnerable environment with optional seed"""
    global current_env_status
    current_env_status = ENV_STATUS_STARTING
    try:
        data = request.json or {}
        seed = data.get('seed', None)
        difficulty = data.get('difficulty', 'easy').lower()
        player_role = data.get('role', 'red').lower()
        
        # Validate difficulty
        if difficulty not in ('easy', 'medium', 'hard'):
            difficulty = 'easy'
        # Validate role
        if player_role not in ('red', 'blue'):
            player_role = 'red'
        
        session_id = f"session_{int(time.time())}"
        
        print(f"[INFO] Initializing session with seed: {seed}")
        print(f"[INFO] (Note: Automatic container startup skipped - ensure container is running in separate terminal)")
        
        # Ensure config directory exists on host
        config_dir = os.path.join(PROJECT_ROOT, 'config')
        os.makedirs(config_dir, exist_ok=True)
        
        print("[INFO] Waiting for environment to prepare vulns.json...")
        
        print("[INFO] Containers started, waiting for vulns.json...")
        
        # Monitor container health during startup
        current_env_status = ENV_STATUS_STARTING
        
        # Wait for vulns.json to be created
        max_wait = 90
        waited = 0
        
        while waited < max_wait:
            if os.path.exists(os.path.normpath(CONFIG_PATH).strip()):
                break
            
            # Check if container died during startup
            container = get_target_container()
            if container and container.status == 'exited':
                logs = container.logs().decode('utf-8')
                print(f"[ERROR] Container exited unexpectedly during startup!")
                print(f"[DEBUG] Container Logs: {logs}")
                current_env_status = ENV_STATUS_OFFLINE
                return jsonify({
                    "status": "error",
                    "message": "Container exited during startup. Check docker logs.",
                    "logs": logs[-500:] # Send last 500 chars of logs
                }), 500
                
            if waited % 10 == 0:
                print(f"[DEBUG] Waiting for {CONFIG_PATH}... ({waited}s)")
            time.sleep(2)
            waited += 2

        if not os.path.exists(os.path.normpath(CONFIG_PATH).strip()):
            current_env_status = ENV_STATUS_OFFLINE
            return jsonify({
                "status": "error",
                "message": f"Timeout: vulns.json was not generated after {waited}s. Container might be stuck or failing."
            }), 500

        print(f"[SUCCESS] vulns.json found after {waited}s!")
        
        # Read vulnerability config
        try:
            vuln_config = read_vulnerability_config()
            session = GameSession(session_id, difficulty=difficulty, player_role=player_role)
            session.seed = seed or vuln_config.get('seed')
            session.vulnerabilities = vuln_config.get('vulnerabilities', [])
            
            # NEW: Initialize CybORG environment
            session.cyborg_env = create_cyborg_env(config_path=CONFIG_PATH)
            session.cyborg_state = session.cyborg_env.reset()
            
            game_sessions[session_id] = session
            
            enabled_count = len([v for v in session.vulnerabilities if v.get('enabled')])
            
            print(f"[SUCCESS] Session created with {enabled_count} vulnerabilities")
            print(f"[SUCCESS] CybORG environment initialized")
            print(f"[SUCCESS] Difficulty: {difficulty}, Role: {player_role}")
            
            return jsonify({
                "status": "success",
                "session_id": session_id,
                "seed": session.seed,
                "difficulty": difficulty,
                "player_role": player_role,
                "difficulty_label": ToolsRegistry.difficulty_label(difficulty),
                "vulnerabilities_count": enabled_count,
                "target_url": "http://localhost:8080",
                "cyborg_ready": True
            }), 200
            
        except Exception as e:
            print(f"[ERROR] Failed to initialize: {e}")
            current_env_status = ENV_STATUS_OFFLINE
            return jsonify({
                "status": "error",
                "message": str(e)
            }), 500
        
        current_env_status = ENV_STATUS_ONLINE
        
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/environment/stop', methods=['POST'])
def stop_environment():
    """Stop the current environment"""
    try:
        print("[INFO] Stop requested - ensure you stop the container manually")
        global current_env_status
        current_env_status = ENV_STATUS_OFFLINE
        
        return jsonify({"status": "success"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/environment/status', methods=['GET'])
def environment_status():
    global current_env_status
    try:
        container = get_target_container()
        is_running = container is not None and container.status == 'running'
        
        # Determine status logically
        if not is_running:
            # If we were starting, but container is gone/exited, we are now offline
            if current_env_status != ENV_STATUS_STARTING:
                current_env_status = ENV_STATUS_OFFLINE
            else:
                # If we are starting, we might still be in the middle of 'docker-compose up'
                # but let's check if the container exists but is not running yet
                if container and container.status in ['created', 'restarting']:
                    current_env_status = ENV_STATUS_STARTING
                else:
                    # Still Offline if it exited during starting phase
                    if container and container.status == 'exited':
                        current_env_status = ENV_STATUS_OFFLINE
        else:
            # Container is running, if we weren't already online, we might be starting or online
            if current_env_status != ENV_STATUS_ONLINE:
                if os.path.exists(CONFIG_PATH):
                    current_env_status = ENV_STATUS_ONLINE
                else:
                    current_env_status = ENV_STATUS_STARTING

        # Final sanity check: if status is online but container died, it's offline
        if current_env_status == ENV_STATUS_ONLINE and not is_running:
             current_env_status = ENV_STATUS_OFFLINE

        # Debugging logging (limited to avoid spamming logs)
        # print(f"[DEBUG] Status Check: {current_env_status} (Container: {container.status if container else 'None'})")
            
        return jsonify({
            "status": "success",
            "is_running": is_running,
            "env_status": current_env_status,
            "container_status": container.status if container else "not found",
            "container_name": container.name if container else None,
            "timestamp": time.time()
        }), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/session/<session_id>', methods=['GET'])
def get_session(session_id):
    """Get current game session state"""
    if session_id not in game_sessions:
        return jsonify({"status": "error", "message": "Session not found"}), 404
    
    session = game_sessions[session_id]
    return jsonify({"status": "success", "session": session.to_dict()}), 200

@app.route('/api/session/<session_id>/vulnerabilities', methods=['GET'])
def get_vulnerabilities(session_id):
    """Get list of vulnerabilities"""
    if session_id not in game_sessions:
        return jsonify({"status": "error", "message": "Session not found"}), 404
    
    session = game_sessions[session_id]
    enabled_vulns = [v for v in session.vulnerabilities if v.get('enabled')]
    
    return jsonify({
        "status": "success",
        "vulnerabilities": enabled_vulns,
        "total": len(enabled_vulns)
    }), 200


@app.route('/api/session/<session_id>/challenge', methods=['GET'])
def get_challenge_info(session_id):
    """Get challenge overview information for defenders"""
    if session_id not in game_sessions:
        return jsonify({"status": "error", "message": "Session not found"}), 404
    
    session = game_sessions[session_id]
    enabled_vulns = [v for v in session.vulnerabilities if v.get('enabled')]
    
    # Count by severity
    severity_breakdown = {
        'critical': len([v for v in enabled_vulns if v['severity'] == 'critical']),
        'high': len([v for v in enabled_vulns if v['severity'] == 'high']),
        'medium': len([v for v in enabled_vulns if v['severity'] == 'medium']),
        'low': len([v for v in enabled_vulns if v['severity'] == 'low'])
    }
    
    # Count discovered (defended) vulnerabilities
    discovered_count = len(session.defenses_applied)
    
    return jsonify({
        "status": "success",
        "total_vulnerabilities": len(enabled_vulns),
        "discovered_count": discovered_count,
        "severity_breakdown": severity_breakdown,
        "hint": "Scan each page systematically to discover vulnerabilities. Look for common injection points."
    }), 200


@app.route('/api/session/<session_id>/scan', methods=['POST'])
def scan_page(session_id):
    """Scan a page for vulnerabilities (defender action)"""
    try:
        if session_id not in game_sessions:
            return jsonify({"status": "error", "message": "Session not found"}), 404
        
        data = request.json
        location = data.get('location')
        
        if not location:
            return jsonify({"status": "error", "message": "No location provided"}), 400
        
        session = game_sessions[session_id]
        
        # Log the scan action
        from datetime import datetime
        session.dvwa_activity_logs.append({
            "timestamp": datetime.now().isoformat(),
            "action_type": "scan",
            "location": location,
            "description": f"User scanned page {location}",
            "success": True,
            "payload": None
        })
        
        # Find vulnerabilities at this location
        vulnerabilities = [
            v for v in session.vulnerabilities 
            if v.get('enabled') and v['location'] == location
        ]
        
        if vulnerabilities:
            return jsonify({
                "status": "success",
                "found": True,
                "vulnerabilities": vulnerabilities,
                "message": f"Found {len(vulnerabilities)} vulnerability(s) at {location}"
            }), 200
        else:
            return jsonify({
                "status": "success",
                "found": False,
                "vulnerabilities": [],
                "message": f"No vulnerabilities found at {location}"
            }), 200
        
    except Exception as e:
        print(f"[ERROR] scan_page: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/api/session/<session_id>/logs/activity', methods=['GET'])
def get_activity_logs(session_id):
    """Get DVWA activity logs for a session"""
    try:
        if session_id not in game_sessions:
            return jsonify({"status": "error", "message": "Session not found"}), 404
        
        session = game_sessions[session_id]
        limit = request.args.get('limit', type=int, default=50)
        
        # Return most recent logs first
        logs = session.dvwa_activity_logs[-limit:] if limit > 0 else session.dvwa_activity_logs
        logs = list(reversed(logs))
        
        return jsonify({
            "status": "success",
            "logs": logs,
            "total": len(session.dvwa_activity_logs)
        }), 200
        
    except Exception as e:
        print(f"[ERROR] get_activity_logs: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/api/session/<session_id>/logs/ai', methods=['GET'])
def get_ai_logs(session_id):
    """Get AI agent logs for a session"""
    try:
        if session_id not in game_sessions:
            return jsonify({"status": "error", "message": "Session not found"}), 404
        
        session = game_sessions[session_id]
        limit = request.args.get('limit', type=int, default=50)
        
        # Return most recent logs first
        logs = session.ai_agent_logs[-limit:] if limit > 0 else session.ai_agent_logs
        logs = list(reversed(logs))
        
        return jsonify({
            "status": "success",
            "logs": logs,
            "total": len(session.ai_agent_logs)
        }), 200
        
    except Exception as e:
        print(f"[ERROR] get_ai_logs: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/api/session/<session_id>/pages', methods=['GET'])
def get_session_pages(session_id):
    """Get all DVWA pages with vulnerability status for a session"""
    try:
        if session_id not in game_sessions:
            return jsonify({"status": "error", "message": "Session not found"}), 404
        
        session = game_sessions[session_id]
        
        # Build page status for each page
        pages_status = []
        
        for page_path, page_info in DVWA_PAGES.items():
            # Find vulnerabilities on this page
            page_vulns = [v for v in session.vulnerabilities 
                         if v.get('enabled') and v.get('location') == '/' + page_path]
            
            # Check how many are patched
            patched_vulns = [v for v in page_vulns 
                           if v['id'] in [d['vuln_id'] for d in session.defenses_applied]]
            
            # Check how many are exploited
            exploited_vulns = [v for v in page_vulns
                             if v['id'] in [e['vuln_id'] for e in session.exploits_found]]
            
            pages_status.append({
                "path": "/" + page_path,
                "name": page_info["name"],
                "category": page_info["category"],
                "description": page_info["description"],
                "has_vulnerabilities": len(page_vulns) > 0,
                "vulnerability_count": len(page_vulns),
                "patched_count": len(patched_vulns),
                "exploited_count": len(exploited_vulns),
                "is_safe": len(page_vulns) == 0 or len(patched_vulns) == len(page_vulns),
                "vulnerabilities": [{"id": v["id"], "type": v["type"], "severity": v["severity"]} 
                                  for v in page_vulns]
            })
        
        # Group by category
        categories = {}
        for page in pages_status:
            cat = page["category"]
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(page)
        
        return jsonify({
            "status": "success",
            "pages": pages_status,
            "by_category": categories,
            "summary": {
                "total_pages": len(pages_status),
                "vulnerable_pages": len([p for p in pages_status if p["has_vulnerabilities"]]),
                "safe_pages": len([p for p in pages_status if p["is_safe"]]),
                "categories": list(categories.keys())
            }
        }), 200
        
    except Exception as e:
        print(f"[ERROR] get_session_pages: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/api/attacker/test/<session_id>', methods=['POST'])
def test_attack(session_id):
    """Test an attack payload (attacker action)"""
    try:
        if session_id not in game_sessions:
            return jsonify({"status": "error", "message": "Session not found"}), 404
        
        data = request.json
        page = data.get('page')
        attack_type = data.get('attack_type')
        payload = data.get('payload')
        
        if not all([page, attack_type, payload]):
            return jsonify({
                "status": "error", 
                "message": "Missing required fields"
            }), 400
        
        session = game_sessions[session_id]
        
        # Log the attack attempt
        from datetime import datetime
        session.dvwa_activity_logs.append({
            "timestamp": datetime.now().isoformat(),
            "action_type": "exploit",
            "location": page,
            "description": f"User tested {attack_type} exploit",
            "success": True,
            "payload": payload[:100] if len(payload) > 100 else payload
        })
        
        # Find vulnerability at this page matching the attack type
        vuln = next((
            v for v in session.vulnerabilities 
            if v.get('enabled') and v['location'] == page and v['type'] == attack_type
        ), None)
        
        if not vuln:
            return jsonify({
                "status": "success",
                "success": False,
                "message": "No matching vulnerability found at this location",
                "hint": "Try a different attack vector or page"
            }), 200
        
        # Check if already defended
        if vuln['id'] in [d['vuln_id'] for d in session.defenses_applied]:
            return jsonify({
                "status": "success",
                "success": False,
                "defended": True,
                "message": "Attack blocked! This vulnerability has been patched by the defender.",
                "vulnerability": {
                    "id": vuln['id'],
                    "type": vuln['type'],
                    "severity": vuln['severity'],
                    "description": vuln['description']
                }
            }), 200
        
        # Simulate attack success
        is_successful = simulate_exploit_test(vuln, payload)
        
        if not is_successful:
            return jsonify({
                "status": "success",
                "success": False,
                "message": "Attack failed. The payload was not effective.",
                "hint": vuln.get('hint', 'Try a different payload approach'),
                "vulnerability": {
                    "id": vuln['id'],
                    "type": vuln['type'],
                    "severity": vuln['severity']
                }
            }), 200
        
        # Award points if successful and not already exploited
        points_awarded = 0
        already_exploited = vuln['id'] in [e['vuln_id'] for e in session.exploits_found]
        
        if not already_exploited:
            points = {
                "critical": 100,
                "high": 50,
                "medium": 25,
                "low": 10
            }.get(vuln['severity'], 10)
            
            session.score['attacker'] += points
            points_awarded = points
            
            session.exploits_found.append({
                "vuln_id": vuln['id'],
                "timestamp": time.time(),
                "points": points,
                "details": {
                    "payload": payload,
                    "attack_type": attack_type,
                    "page": page
                }
            })
        
        return jsonify({
            "status": "success",
            "success": True,
            "message": "Attack successful! Vulnerability exploited.",
            "points_awarded": points_awarded,
            "vulnerability": {
                "id": vuln['id'],
                "type": vuln['type'],
                "severity": vuln['severity'],
                "description": vuln['description'],
                "location": vuln['location']
            }
        }), 200
        
    except Exception as e:
        print(f"[ERROR] test_attack: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/exploit/report', methods=['POST'])
def report_exploit():
    """Report a discovered exploit (legacy endpoint)"""
    try:
        data = request.json
        session_id = data.get('session_id')
        vuln_id = data.get('vuln_id')
        exploit_details = data.get('details', {})
        
        if session_id not in game_sessions:
            return jsonify({"status": "error", "message": "Session not found"}), 404
        
        session = game_sessions[session_id]
        
        if vuln_id in [e['vuln_id'] for e in session.exploits_found]:
            return jsonify({
                "status": "success", 
                "message": "Already reported",
                "points_awarded": 0
            }), 200
        
        vuln = next((v for v in session.vulnerabilities 
                    if v['id'] == vuln_id and v.get('enabled')), None)
        
        if not vuln:
            return jsonify({
                "status": "error", 
                "message": "Invalid vulnerability"
            }), 400
        
        points = {
            "critical": 100,
            "high": 50,
            "medium": 25,
            "low": 10
        }.get(vuln['severity'], 10)
        
        session.score['attacker'] += points
        session.exploits_found.append({
            "vuln_id": vuln_id,
            "timestamp": time.time(),
            "points": points,
            "details": exploit_details
        })
        
        return jsonify({
            "status": "success",
            "points_awarded": points,
            "total_score": session.score['attacker']
        }), 200
        
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/defense/apply', methods=['POST'])
def apply_defense():
    """Apply a defense/patch (legacy endpoint)"""
    try:
        data = request.json
        session_id = data.get('session_id')
        vuln_id = data.get('vuln_id')
        fix_command = data.get('fix_command')
        
        if session_id not in game_sessions:
            return jsonify({"status": "error", "message": "Session not found"}), 404
        
        session = game_sessions[session_id]
        
        # Log the defense action
        from datetime import datetime
        vuln = next((v for v in session.vulnerabilities if v['id'] == vuln_id), None)
        if vuln:
            session.dvwa_activity_logs.append({
                "timestamp": datetime.now().isoformat(),
                "action_type": "patch",
                "location": vuln.get('location', 'unknown'),
                "description": f"User applied patch for {vuln_id}",
                "success": True,
                "payload": None
            })
        
        if vuln_id in [d['vuln_id'] for d in session.defenses_applied]:
            return jsonify({
                "status": "success", 
                "message": "Already defended",
                "points_awarded": 0
            }), 200
        
        vuln = next((v for v in session.vulnerabilities 
                    if v['id'] == vuln_id and v.get('enabled')), None)
        
        if not vuln:
            return jsonify({
                "status": "error",
                "message": "Invalid vulnerability"
            }), 400
        
        was_exploited = vuln_id in [e['vuln_id'] for e in session.exploits_found]
        points = 30 if not was_exploited else 15
        
        session.score['defender'] += points
        session.defenses_applied.append({
            "vuln_id": vuln_id,
            "timestamp": time.time(),
            "points": points,
            "fix_command": fix_command,
            "proactive": not was_exploited
        })
        
        return jsonify({
            "status": "success",
            "points_awarded": points,
            "total_score": session.score['defender'],
            "proactive": not was_exploited
        }), 200
        
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/logs', methods=['GET'])
def get_logs():
    """Get recent activity logs"""
    try:
        if not os.path.exists(LOGS_PATH):
            return jsonify({"status": "success", "logs": []}), 200
        
        with open(LOGS_PATH, 'r') as f:
            lines = f.readlines()[-50:]
        
        return jsonify({
            "status": "success",
            "logs": [line.strip() for line in lines]
        }), 200
        
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    
# ============================================================================
# CYBORG RL INTEGRATION ENDPOINTS
# ============================================================================

@app.route('/api/rl/step', methods=['POST'])
def rl_step():
    """Execute RL agent action in CybORG environment"""
    try:
        data = request.json
        session_id = data.get('session_id')
        agent_name = data.get('agent_name')  # 'red_agent' or 'blue_agent'
        action_type = data.get('action_type')  # 'exploit', 'patch', 'scan'
        vuln_id = data.get('vuln_id')
        
        if session_id not in game_sessions:
            return jsonify({"status": "error", "message": "Session not found"}), 404
            
        session = game_sessions[session_id]
        
        if not session.cyborg_env:
            return jsonify({"status": "error", "message": "CybORG not initialized"}), 500
        
        # Create appropriate action
        if action_type == 'exploit':
            action = DVWAExploitAction(vuln_id)
        elif action_type == 'patch':
            action = DVWAPatchAction(vuln_id)
        elif action_type == 'scan':
            action = DVWAScanAction()
        else:
            return jsonify({"status": "error", "message": "Invalid action type"}), 400
        
        # Execute action in CybORG
        observation = action.execute(session.cyborg_state)
        
        # Update game state based on observation
        if observation.success:
            if action_type == 'exploit' and observation.reward:
                session.score['attacker'] += observation.reward
                if vuln_id not in [e['vuln_id'] for e in session.exploits_found]:
                    session.exploits_found.append({
                        "vuln_id": vuln_id,
                        "timestamp": time.time(),
                        "points": observation.reward,
                        "method": "cyborg_rl"
                    })
            elif action_type == 'patch' and observation.reward:
                session.score['defender'] += observation.reward
                if vuln_id not in [d['vuln_id'] for d in session.defenses_applied]:
                    session.defenses_applied.append({
                        "vuln_id": vuln_id,
                        "timestamp": time.time(),
                        "points": observation.reward,
                        "fix_command": "cyborg_rl_patch",
                        "proactive": observation.data.get('proactive', False)
                    })
        
        return jsonify({
            "status": "success",
            "observation": observation.data,
            "reward": observation.reward,
            "success": observation.success,
            "info": observation.info,
            "updated_score": session.score
        }), 200
        
    except Exception as e:
        print(f"[ERROR] rl_step: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/api/rl/train', methods=['POST'])
def start_rl_training():
    """Start RL training session"""
    try:
        data = request.json
        session_id = data.get('session_id')
        agent_type = data.get('agent_type', 'blue')  # 'red' or 'blue'
        episodes = data.get('episodes', 100)
        
        if session_id not in game_sessions:
            return jsonify({"status": "error", "message": "Session not found"}), 404
        
        # This would be handled by train_rl.py in production
        # For now, return training status
        return jsonify({
            "status": "success",
            "message": "Training initiated",
            "session_id": session_id,
            "agent_type": agent_type,
            "episodes": episodes,
            "note": "Use train_rl.py script for actual training"
        }), 200
        
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/api/rl/state', methods=['GET'])
def get_rl_state():
    """Get current CybORG environment state"""
    try:
        session_id = request.args.get('session_id')
        
        if session_id not in game_sessions:
            return jsonify({"status": "error", "message": "Session not found"}), 404
            
        session = game_sessions[session_id]
        
        if not session.cyborg_state:
            return jsonify({"status": "error", "message": "CybORG not initialized"}), 500
        
        return jsonify({
            "status": "success",
            "state": {
                "active_vulns": list(session.cyborg_state.active_vulns.keys()),
                "exploited_vulns": list(session.cyborg_state.exploited_vulns),
                "patched_vulns": list(session.cyborg_state.patched_vulns),
                "total_active": len(session.cyborg_state.active_vulns)
            }
        }), 200
        
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

def read_vulnerability_config():
    """Read vulnerability configuration from mounted volume"""
    
    # Path normalization and stripping for Windows robustness
    # Use abspath to resolve any relative path issues
    safe_path = os.path.normpath(os.path.abspath(CONFIG_PATH)).strip()
    
    if not os.path.exists(safe_path):
        raise FileNotFoundError(f"Vulnerability config not found at {safe_path}")
    
    # print(f"[DEBUG] Reading vulns.json from: {safe_path}")
    
    # Retry mechanism for file locks (common on Windows with Docker volumes)
    max_retries = 5
    for attempt in range(max_retries):
        try:
            # On Windows, sometimes file is being synced/locked by Docker
            with open(safe_path, 'r', encoding='utf-8') as f:
                content = f.read()
                if not content:
                    raise ValueError("File is empty")
                config = json.loads(content)
            return config
        except (IOError, ValueError, json.JSONDecodeError) as e:
            if attempt == max_retries - 1:
                print(f"[ERROR] Final attempt to read config failed: {e}")
                raise
            # print(f"[WARNING] Retry {attempt+1} reading config: {e}")
            time.sleep(1.5)
    
    return None


# ============================================================================
# AI AGENT ENDPOINTS (Added)
# ============================================================================

@app.route('/api/ai/step', methods=['POST'])
def trigger_ai_step():
    """Trigger a turn for the AI agent"""
    try:
        data = request.json
        session_id = data.get('session_id')
        agent_type = data.get('agent', 'red') # 'red' or 'blue'
        
        if session_id not in game_sessions:
            return jsonify({"status": "error", "message": "Session not found"}), 404
            
        session = game_sessions[session_id]
        
        # Initialize orchestrator if needed
        if not hasattr(session, 'ai_orchestrator') or not session.ai_orchestrator:
             session.ai_orchestrator = AIOrchestrator(session)
             
        # Execute Step
        result = session.ai_orchestrator.step(agent_type)
        
        return jsonify({
            "status": "success",
            "result": result
        }), 200
        
    except Exception as e:
        print(f"[ERROR] ai_step: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"status": "error", "message": str(e)}), 500

# ============================================================================
# SECURITY TOOLS ORCHESTRATOR (sqlmap, ZAP, Semgrep, XSSer)
# ============================================================================

class HackOpsScanner:
    """Built-in Python scanner for SQLi and XSS - reliable, no external tools needed."""

    SQLI_PAYLOADS = [
        ("' OR '1'='1", "'1'='1"),
        ("' OR 1=1 --", "SELECT"),
        ("'; SELECT 1,2,3 --", "SELECT"),
        ("' UNION SELECT null,null,null --", "UNION"),
        ("' AND (SELECT 1 FROM (SELECT SLEEP(0))x) --", None),  # time-based marker
        ("' OR 'x'='x", "x"),
    ]

    XSS_PAYLOADS = [
        "<script>alert('xss')</script>",
        "<img src=x onerror=alert(1)>",
        "<svg onload=alert(1)>",
        "\"'><script>alert(1)</script>",
        "<body onload=alert(1)>",
        "javascript:alert(1)",
    ]

    PAGE_PARAMS = {
        '/search.php':   [('GET', 'q')],
        '/profile.php':  [('GET', 'id')],
        '/product.php':  [('GET', 'id')],
        '/order.php':    [('GET', 'id')],
        '/view.php':     [('GET', 'file')],
        '/review.php':   [('POST', 'review'), ('POST', 'product_id')],
        '/login.php':    [('POST', 'username'), ('POST', 'password')],
    }

    @classmethod
    def get_session(cls, base_url):
        import requests
        s = requests.Session()
        s.post(f"{base_url}/login.php", data={'username': 'john_doe', 'password': 'password'}, timeout=5)
        s.cookies.set('security', 'low')
        return s

    @classmethod
    def scan_sqli(cls, target_url):
        import requests
        from urllib.parse import urlparse
        results = []
        parsed = urlparse(target_url)
        base_url = f"{parsed.scheme}://{parsed.netloc}"
        path = parsed.path

        # Get baseline response
        session = cls.get_session(base_url)
        params_list = cls.PAGE_PARAMS.get(path, [('GET', 'id')])

        for method, param in params_list:
            baseline_res = session.get(target_url, params={param: 'test'}, timeout=5)
            baseline_text = baseline_res.text

            for payload, indicator in cls.SQLI_PAYLOADS:
                try:
                    if method == 'GET':
                        res = session.get(target_url, params={param: payload}, timeout=5)
                    else:
                        res = session.post(target_url, data={param: payload}, timeout=5)

                    # Check for SQL errors or indicator strings
                    sql_errors = [
                        'SQL syntax', 'mysql_fetch', 'ORA-', 'syntax error',
                        'SQLSTATE', 'Warning: mysql', 'Unclosed quotation'
                    ]
                    error_found = any(e.lower() in res.text.lower() for e in sql_errors)
                    # Check if response significantly differs from baseline (different row count etc)
                    diff_factor = abs(len(res.text) - len(baseline_text)) / max(len(baseline_text), 1)
                    indicator_found = indicator and indicator.lower() in res.text.lower()

                    if error_found or indicator_found or diff_factor > 0.3:
                        results.append({
                            'type': 'SQL Injection',
                            'parameter': param,
                            'payload': payload,
                            'evidence': 'SQL error' if error_found else ('indicator' if indicator_found else 'response-diff'),
                            'response_snippet': res.text[:200]
                        })
                        break  # One confirmed vuln per param is enough
                except Exception as e:
                    pass

        return results

    @classmethod
    def scan_xss(cls, target_url):
        import requests
        from urllib.parse import urlparse
        results = []
        parsed = urlparse(target_url)
        base_url = f"{parsed.scheme}://{parsed.netloc}"
        path = parsed.path

        session = cls.get_session(base_url)
        params_list = cls.PAGE_PARAMS.get(path, [('GET', 'q')])

        for method, param in params_list:
            for payload in cls.XSS_PAYLOADS:
                try:
                    if method == 'GET':
                        res = session.get(target_url, params={param: payload}, timeout=5)
                    else:
                        res = session.post(target_url, data={param: payload}, timeout=5)

                    # Check for unescaped payload reflected in response
                    if payload in res.text:
                        results.append({
                            'type': 'Reflected XSS',
                            'parameter': param,
                            'payload': payload,
                            'evidence': 'payload reflected unescaped in response',
                        })
                        break
                    # Check for partially reflected xss (HTML context like script tag without the full payload)
                    elif '<script>' in res.text and 'alert' in res.text:
                        results.append({
                            'type': 'Reflected XSS (partial)',
                            'parameter': param,
                            'payload': payload,
                            'evidence': 'script tag found in response'
                        })
                        break
                except Exception as e:
                    pass

        return results

class ToolsOrchestrator:
    @staticmethod
    def _get_auth_cookies(target_url):
        import requests
        try:
            # Parse the base URL (http://localhost:8080)
            from urllib.parse import urlparse
            parsed_url = urlparse(target_url)
            base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
            
            # Login to get session
            s = requests.Session()
            login_url = f"{base_url}/login.php"
            data = {"username": "john_doe", "password": "password"}
            s.post(login_url, data=data, timeout=5)
            s.cookies.set('security', 'low')
            
            # Format cookies for tools
            cookies = s.cookies.get_dict()
            cookie_string = "; ".join([f"{k}={v}" for k, v in cookies.items()])
            return cookie_string
        except Exception as e:
            print(f"Failed to get auth cookies: {e}")
            return ""

    # Known vulnerable parameters per page path
    PAGE_PARAMS = {
        '/search.php':    ('GET',  'q=test'),
        '/profile.php':   ('GET',  'id=1'),
        '/product.php':   ('GET',  'id=1'),
        '/order.php':     ('GET',  'id=1'),
        '/view.php':      ('GET',  'file=index.php'),
        '/login.php':     ('POST', 'username=admin&password=test'),
        '/review.php':    ('POST', 'review=test&product_id=1'),
    }

    @staticmethod
    def _inject_params(target_url):
        """Return a URL with test parameters injected, based on page path."""
        from urllib.parse import urlparse, urlencode, urlunparse
        parsed = urlparse(target_url)
        path = parsed.path
        entry = ToolsOrchestrator.PAGE_PARAMS.get(path)
        if not entry:
            # Append a generic param so sqlmap has something to test
            qs = parsed.query or 'id=1'
            return urlunparse(parsed._replace(query=qs))
        method, params = entry
        if method == 'GET' and '?' not in target_url:
            return target_url + '?' + params
        return target_url

    @staticmethod
    def run_sqlmap(target_url, risk=1, level=1):
        """Run sqlmap against a target URL"""
        try:
            cookies = ToolsOrchestrator._get_auth_cookies(target_url)
            scan_url = ToolsOrchestrator._inject_params(target_url)

            # Find sqlmap executable
            venv_sqlmap = os.path.join(PROJECT_ROOT, 'api', 'venv', 'Scripts', 'sqlmap.exe')
            if os.name == 'nt' and os.path.exists(venv_sqlmap):
                sqlmap_bin = venv_sqlmap
            else:
                sqlmap_bin = 'sqlmap'

            cmd = [
                sqlmap_bin, "-u", scan_url,
                "--batch", "--risk", str(risk), "--level", str(level),
                "--random-agent", "--threads=5",
                "--technique=BEUSTQ",  # all techniques
                "--dbms=mysql",        # hint the dbms for speed
            ]

            if cookies:
                cmd.extend(["--cookie", cookies])

            print(f"SQLMap command: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            return {
                "success": True,
                "output": result.stdout,
                "error": result.stderr
            }
        except Exception as e:
            print(f"SQLMap failed or not found: {e}. Using simulation.")
            return ToolsOrchestrator.run_simulated_sqlmap(target_url)

    @staticmethod
    def run_simulated_sqlmap(target_url):
        """Mock SQLMap output if tool isn't installed"""
        from urllib.parse import urlparse
        path = urlparse(target_url).path
        # Very convincing mock output
        output = f"--- [sqlmap] scanning {target_url} ---\n"
        output += "[INFO] testing for SQL injection on GET parameter 'id'\n"
        
        # Check if we have a real SQLi vuln here in our catalog (hacky but works for demo)
        if any(p in path for p in ['search', 'product', 'login', 'user']):
            output += "[CONFIRMED] GET parameter 'id' is vulnerable to boolean-based blind SQL injection\n"
            output += "[CONFIRMED] GET parameter 'id' is vulnerable to error-based SQL injection\n"
            output += "[INFO] back-end DBMS: MySQL >= 5.6\n"
        else:
            output += "[INFO] GET parameter 'id' does not seem to be injectable\n"
            
        return {"success": True, "output": output, "simulated": True}

    @staticmethod
    def run_semgrep(file_path):
        """Run Semgrep SAST on a specific file"""
        try:
            # Command for semgrep
            cmd = ["semgrep", "scan", "--config", "auto", "--json", file_path]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            if result.returncode == 0:
                return json.loads(result.stdout)
            else:
                raise Exception(f"Semgrep returned {result.returncode}")
        except Exception as e:
            print(f"Semgrep failed or not found: {e}. Using simulation.")
            return ToolsOrchestrator.run_simulated_semgrep(file_path)

    @staticmethod
    def run_simulated_semgrep(file_path):
        """Mock Semgrep JSON output"""
        # Read file to see if it's actually vulnerable
        try:
            with open(file_path, 'r') as f:
                content = f.read()
        except:
            content = ""

        results = []
        filename = os.path.basename(file_path) if file_path else "unknown_file.php"
        
        if "$_GET" in content or "$_POST" in content:
            if "query" in content.lower() or "select" in content.lower():
                results.append({
                    "check_id": "php.lang.security.injection.sql-injection",
                    "path": filename,
                    "start": {"line": 10, "col": 5},
                    "extra": {
                        "message": "Detected potential SQL injection. Direct usage of user input in query.",
                        "severity": "ERROR"
                    }
                })
            # For profile.php which echoes user details
            if "echo" in content.lower() or "print" in content.lower() or "printf" in content.lower() or "<?= " in content:
                 results.append({
                    "check_id": "php.lang.security.injection.xss",
                    "path": filename,
                    "start": {"line": 15, "col": 5},
                    "extra": {
                        "message": "Detected potential XSS. User input is echoed without sanitization.",
                        "severity": "WARNING"
                    }
                })
        
        return {"results": results, "simulated": True}

    @staticmethod
    def run_zap_scan(target_url):
        """Run ZAP Scan (simulated by default for complexity)"""
        # Real ZAP is too heavy for most local setups, so we simulate it
        # by checking our session's ground truth for the given URL
        from urllib.parse import urlparse
        path = urlparse(target_url).path
        
        alerts = []
        # Check if this path matches ANY enabled vulnerability in our global catalog?
        # Better: let the endpoint pass the session_id so we can check the REAL state.
        # For now, generic simulation:
        if any(p in path for p in ['search', 'contact', 'review']):
            alerts.append({
                "alert": "Cross-Site Scripting (Reflected)",
                "risk": "High",
                "reliability": "Confirmed",
                "url": target_url,
                "param": "q",
                "evidence": "<script>alert(1)</script>"
            })
        
        if 'login' in path:
             alerts.append({
                "alert": "SQL Injection",
                "risk": "High",
                "reliability": "Confirmed",
                "url": target_url,
                "param": "username",
                "evidence": "admin' --"
            })

        return {"alerts": alerts, "simulated": True}

    @staticmethod
    def run_real_zap_scan(target_url):
        """Run OWASP ZAP active scan using its REST API directly."""
        import requests as req
        ZAP_API = 'http://127.0.0.1:8081'
        
        # Translate host for internal Docker networking if needed
        # ZAP inside Docker cannot reach 'localhost:8080' (which is the host), 
        # it must use the service name 'target' defined in docker-compose.
        internal_url = target_url.replace("localhost:8080", "target").replace("127.0.0.1:8080", "target")
        if "://" not in internal_url:
            internal_url = f"http://target{internal_url}"
            
        print(f"ZAP Internal Scan Target: {internal_url} (Original: {target_url})")

        try:
            # Check ZAP is alive
            version_res = req.get(f'{ZAP_API}/JSON/core/view/version/', timeout=5)
            print(f"ZAP version: {version_res.json()}")
        except Exception as e:
            return {"error": f"ZAP not available at {ZAP_API}: {e}"}

        try:
            # Get cookies using the ORIGINAL URL (because host-based backend sees localhost)
            cookies = ToolsOrchestrator._get_auth_cookies(target_url)
            
            # Set auth cookie via replacer
            if cookies:
                req.get(f'{ZAP_API}/JSON/replacer/action/removeRule/', params={'description': 'HackOps_Auth_Cookie'}, timeout=5)
                req.get(f'{ZAP_API}/JSON/replacer/action/addRule/', timeout=5, params={
                    'description': 'HackOps_Auth_Cookie',
                    'enabled': 'true',
                    'matchType': 'REQ_HEADER',
                    'matchRegex': 'false',
                    'matchString': 'Cookie',
                    'replacement': cookies,
                    'initiators': ''
                })
                print(f"ZAP: cookies configured: {cookies[:60]}...")

            # Spider
            print(f"ZAP: Spidering {internal_url}")
            spider_res = req.get(f'{ZAP_API}/JSON/spider/action/scan/', params={'url': internal_url}, timeout=10)
            scan_id = spider_res.json().get('scan')
            
            if not scan_id:
                return {"error": f"Failed to start spider for {internal_url}. Response: {spider_res.text}"}

            for _ in range(60):  # Max 2 minutes
                status_res = req.get(f'{ZAP_API}/JSON/spider/view/status/', params={'scanId': scan_id}, timeout=5)
                status = int(status_res.json().get('status', 0))
                if status >= 100:
                    break
                time.sleep(2)

            # Active scan
            print(f"ZAP: Active scanning {internal_url}")
            ascan_res = req.get(f'{ZAP_API}/JSON/ascan/action/scan/', params={'url': internal_url}, timeout=10)
            scan_id = ascan_res.json().get('scan')
            
            if not scan_id:
                # If ascan fails to start, we still return the alerts from spidering/baseline
                print("ZAP: Active scan failed to start, returning existing alerts.")
            else:
                for _ in range(120):  # Max 10 minutes
                    status_res = req.get(f'{ZAP_API}/JSON/ascan/view/status/', params={'scanId': scan_id}, timeout=5)
                    status = int(status_res.json().get('status', 0))
                    print(f"ZAP ascan progress: {status}%")
                    if status >= 100:
                        break
                    time.sleep(5)

            # Fetch alerts for the INTERNAL URL
            alerts_res = req.get(f'{ZAP_API}/JSON/core/view/alerts/', params={'baseurl': internal_url}, timeout=10)
            alerts = alerts_res.json().get('alerts', [])

            # Translate internal URLs back to localhost in the report for the user
            for alert in alerts:
                if 'url' in alert:
                    alert['url'] = alert['url'].replace("http://target", "http://localhost:8080")

            return {
                "alerts": alerts,
                "total": len(alerts),
                "high": sum(1 for a in alerts if a.get('risk') == 'High'),
                "medium": sum(1 for a in alerts if a.get('risk') == 'Medium'),
            }
        except Exception as e:
            import traceback
            traceback.print_exc()
            return {"error": str(e)}

# ============================================================================
# TOOLS AVAILABILITY ENDPOINT
# ============================================================================

@app.route('/api/tools/available/<session_id>', methods=['GET'])
def get_available_tools(session_id):
    """Return the tools the human player can use in this session."""
    if session_id not in game_sessions:
        return jsonify({"status": "error", "message": "Session not found"}), 404
    
    session = game_sessions[session_id]
    role = session.player_role
    difficulty = session.difficulty
    
    all_tools = ToolsRegistry.get_all_tools_with_status(role=role, difficulty=difficulty)
    available_tools = [t for t in all_tools if t['available']]
    locked_tools = [t for t in all_tools if not t['available']]
    
    return jsonify({
        "status": "success",
        "difficulty": difficulty,
        "difficulty_label": ToolsRegistry.difficulty_label(difficulty),
        "player_role": role,
        "available_tools": available_tools,
        "locked_tools": locked_tools,
        "total_available": len(available_tools),
    }), 200


@app.route('/api/tools/hint/<session_id>/<vuln_id>', methods=['GET'])
def tool_hint(session_id, vuln_id):
    """Return a hint about the vulnerability type at a location (no payload).
    Only available to attackers on Easy and Medium difficulties."""
    if session_id not in game_sessions:
        return jsonify({"status": "error", "message": "Session not found"}), 404
    
    session = game_sessions[session_id]
    allowed, reason = ToolsRegistry.check_tool_access(
        'vuln_hint', role=session.player_role, difficulty=session.difficulty
    )
    if not allowed:
        return jsonify({"status": "error", "message": reason}), 403
    
    vuln = next((v for v in session.vulnerabilities if v['id'] == vuln_id and v.get('enabled')), None)
    if not vuln:
        return jsonify({"status": "error", "message": "Vulnerability not found"}), 404
    
    # Return type and severity only — never the payload
    return jsonify({
        "status": "success",
        "hint": {
            "vuln_type": vuln['type'],
            "severity": vuln['severity'],
            "location": vuln['location'],
            "description_hint": f"There is a {vuln['type'].upper()} vulnerability of {vuln['severity']} severity on this page. Look for user-controlled input fields."
        }
    }), 200

@app.route('/api/tools/page-hint/<session_id>', methods=['POST'])
def tool_page_hint(session_id):
    """Return a hint about which input fields on a page are worth investigating.
    Only available to attackers on Easy difficulty."""
    if session_id not in game_sessions:
        return jsonify({"status": "error", "message": "Session not found"}), 404
    
    session = game_sessions[session_id]
    allowed, reason = ToolsRegistry.check_tool_access(
        'page_hint', role=session.player_role, difficulty=session.difficulty
    )
    if not allowed:
        return jsonify({"status": "error", "message": reason}), 403
    
    data = request.json or {}
    target_url = data.get('target_url')
    if not target_url:
        return jsonify({"status": "error", "message": "No target_url provided"}), 400
        
    from urllib.parse import urlparse
    path = urlparse(target_url).path
    
    # We find all vulns that belong to this path
    page_vulns = [v for v in session.vulnerabilities if path.endswith(v.get('location', '')) and v.get('enabled')]
    
    if not page_vulns:
        return jsonify({
            "status": "success",
            "hint": {
                "message": "There are no known vulnerabilities on this specific page.",
                "vulnerable_params": []
            }
        }), 200
        
    # Extract the vulnerable parameters
    params = set()
    for v in page_vulns:
        if 'exploit' in v and 'parameter' in v['exploit']:
            params.add(v['exploit']['parameter'])
            
    return jsonify({
        "status": "success",
        "hint": {
            "message": f"Found {len(page_vulns)} vulnerability(ies) on this page.",
            "vulnerable_params": list(params),
            "advice": f"You should investigate the following parameters: {', '.join(params)}" if params else "Check for hidden inputs or headers."
        }
    }), 200


@app.route('/api/tools/http-inspect/<session_id>', methods=['POST'])
def tool_http_inspect(session_id):
    """Fetch a page and return raw headers + response snippet. Available to all."""
    if session_id not in game_sessions:
        return jsonify({"status": "error", "message": "Session not found"}), 404
    
    allowed, reason = ToolsRegistry.check_tool_access(
        'http_inspector',
        role=game_sessions[session_id].player_role,
        difficulty=game_sessions[session_id].difficulty
    )
    if not allowed:
        return jsonify({"status": "error", "message": reason}), 403
    
    data = request.json or {}
    target_url = data.get('target_url')
    if not target_url:
        return jsonify({"status": "error", "message": "No target_url provided"}), 400
    
    try:
        import requests as req
        resp = req.get(target_url, timeout=5, allow_redirects=True)
        headers_dict = dict(resp.headers)
        return jsonify({
            "status": "success",
            "result": {
                "url": resp.url,
                "status_code": resp.status_code,
                "headers": headers_dict,
                "body_snippet": resp.text[:500],
                "content_length": len(resp.text)
            }
        }), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# ============================================================================
# EXISTING TOOL ENDPOINTS — now difficulty-gated
# ============================================================================

@app.route('/api/tools/sqlmap/scan', methods=['POST'])
def tool_sqlmap_scan():
    data = request.json
    target_url = data.get('target_url')
    session_id = data.get('session_id')
    
    if not target_url:
        return jsonify({"status": "error", "message": "No target URL provided"}), 400
    
    # Difficulty gate
    if session_id and session_id in game_sessions:
        session = game_sessions[session_id]
        allowed, reason = ToolsRegistry.check_tool_access(
            'sqli_scanner', role=session.player_role, difficulty=session.difficulty
        )
        if not allowed:
            return jsonify({"status": "error", "message": reason}), 403
    
    # Use the built-in Python scanner first (fast and reliable)
    sqli_results = HackOpsScanner.scan_sqli(target_url)
    
    if sqli_results:
        output = f"[HackOps Scanner] SQL Injection scan complete!\n"
        output += f"Found {len(sqli_results)} vulnerability(ies):\n\n"
        for r in sqli_results:
            output += f"  [VULN] {r['type']} in parameter '{r['parameter']}'\n"
            output += f"  Payload: {r['payload']}\n"
            output += f"  Evidence: {r['evidence']}\n\n"
    else:
        # Fallback to sqlmap for deeper scan
        sqlmap_result = ToolsOrchestrator.run_sqlmap(target_url)
        output = sqlmap_result.get('output', 'No output') or sqlmap_result.get('error', 'Unknown error')
        sqli_results = []
    
    return jsonify({"status": "success", "result": {
        "output": output,
        "vulnerabilities": sqli_results,
        "found": len(sqli_results) > 0
    }})

@app.route('/api/tools/xss/scan', methods=['POST'])
def tool_xss_scan():
    data = request.json
    target_url = data.get('target_url')
    session_id = data.get('session_id')
    
    if not target_url:
        return jsonify({"status": "error", "message": "No target URL provided"}), 400
    
    # Difficulty gate
    if session_id and session_id in game_sessions:
        session = game_sessions[session_id]
        allowed, reason = ToolsRegistry.check_tool_access(
            'xss_scanner', role=session.player_role, difficulty=session.difficulty
        )
        if not allowed:
            return jsonify({"status": "error", "message": reason}), 403
    
    xss_results = HackOpsScanner.scan_xss(target_url)
    
    if xss_results:
        output = f"[HackOps XSS Scanner] Scan complete!\n"
        output += f"Found {len(xss_results)} XSS vulnerability(ies):\n\n"
        for r in xss_results:
            output += f"  [VULN] {r['type']} in parameter '{r['parameter']}'\n"
            output += f"  Payload: {r['payload']}\n"
            output += f"  Evidence: {r['evidence']}\n\n"
    else:
        output = "[HackOps XSS Scanner] No XSS vulnerabilities found on this page.\n"
        output += "This may mean the page is properly input-sanitizing, or the parameter is not reflected."
    
    return jsonify({"status": "success", "result": {
        "output": output,
        "vulnerabilities": xss_results,
        "found": len(xss_results) > 0
    }})

@app.route('/api/tools/zap/scan', methods=['POST'])
def tool_zap_scan():
    data = request.json
    target_url = data.get('target_url')
    session_id = data.get('session_id')
    
    if not target_url:
        return jsonify({"status": "error", "message": "No target URL provided"}), 400
    
    # Difficulty + role gate (defenders only, easy difficulty)
    if session_id and session_id in game_sessions:
        session = game_sessions[session_id]
        allowed, reason = ToolsRegistry.check_tool_access(
            'zap_scanner', role=session.player_role, difficulty=session.difficulty
        )
        if not allowed:
            return jsonify({"status": "error", "message": reason}), 403
        
    result = ToolsOrchestrator.run_zap_scan(target_url)
    return jsonify({"status": "success", "result": result})

@app.route('/api/tools/semgrep/scan', methods=['POST'])
def tool_semgrep_scan():
    data = request.json
    vuln_id = data.get('vuln_id')
    target_file = data.get('target_file')  # Optional: allow scanning an arbitrary file
    session_id = data.get('session_id')

    if not session_id or session_id not in game_sessions:
        return jsonify({"status": "error", "message": "Invalid session"}), 400

    if not vuln_id and not target_file:
        return jsonify({"status": "error", "message": "Either vuln_id or target_file must be provided"}), 400

    # Difficulty + role gate (defenders only, easy/medium)
    session = game_sessions[session_id]
    allowed, reason = ToolsRegistry.check_tool_access(
        'semgrep_sast', role=session.player_role, difficulty=session.difficulty
    )
    if not allowed:
        return jsonify({"status": "error", "message": reason}), 403

    code_to_scan = ""

    if target_file:
        # User requested to scan an arbitrary file directly from the container
        try:
            container = client.containers.get('hackops-target-1')
            # Ensure path is safe (starts with /)
            safe_path = target_file if target_file.startswith('/') else f'/{target_file}'
            file_path = f"/var/www/html{safe_path}"
            
            result = container.exec_run(f'cat {file_path}')
            if result.exit_code != 0:
                return jsonify({
                    "status": "error", 
                    "message": f"Could not read file {safe_path} from container: {result.output.decode()}"
                }), 400
            
            code_to_scan = result.output.decode('utf-8')
        except Exception as e:
             return jsonify({
                 "status": "error", 
                 "message": f"Container interaction failed: {str(e)}"
             }), 500
    else:
        # Original logic: scanning the currently viewed vulnerable code
        code_info = session.code_modifications.get(vuln_id)

        if not code_info:
            return jsonify({
                "status": "error",
                "message": "No code loaded. Call /api/code/view first to load the file."
            }), 400

        # Use the current live code from the container
        code_to_scan = code_info.get('modified_code') or code_info.get('original_code', '')

    if not code_to_scan:
        return jsonify({"status": "error", "message": "No code content available to scan"}), 400

    with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', suffix='.php', delete=False) as tmp:
        tmp.write(code_to_scan)
        tmp_path = tmp.name

    try:
        report = ToolsOrchestrator.run_semgrep(tmp_path)
        return jsonify({"status": "success", "report": report})
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)

# =========================================================================
# 🤖 FOUNDATION AGENT APIs (SAR Architecture)
# =========================================================================

@app.route('/api/agent/v1/recon/dom', methods=['GET'])
def agent_get_dom():
    """
    DOM Mapper API: Returns a clean JSON representation of the current page.
    Used by the RL Brain to 'see' the environment.
    """
    session_id = request.args.get('session_id')
    path = request.args.get('path', '/')
    
    # In a real scenario, we would use the session's controller
    # For now, we manually fetch from the target container
    try:
        container = get_target_container()
        if not container or container.status != 'running':
             return jsonify({"status": "error", "message": "Container not running or not found"}), 500
        
        # We need to preserve original DVWA session (cookies)? 
        # For simplicity, we just fetch a clean version or use a mock controller
        
        # Use DVWAController logic for consistent session handling
        controller = DVWAController(target_url="http://target") # Internal docker network name
        
        # If we had a session_id, we'd retrieve its specific cookies
        # response = controller.session.get(f"http://hackops-project-target-1{path}")
        
        # Simpler: Execute curl inside container to get raw HTML
        result = container.exec_run(f"curl -s http://localhost{path}")
        html = result.output.decode('utf-8', errors='ignore')
        
        soup = BeautifulSoup(html, 'html.parser')
        
        # Extract metadata
        page_info = DVWA_PAGES.get(path.lstrip('/'), {"name": "Unknown", "category": "unknown"})
        
        dom = {
            "page_metadata": page_info,
            "url": path,
            "forms": [],
            "links": [],
            "status": "ready"
        }
        
        # Parse forms
        for form in soup.find_all('form'):
            f = {
                "action": form.get('action'),
                "method": form.get('method', 'GET').upper(),
                "inputs": []
            }
            for inp in form.find_all(['input', 'textarea', 'select']):
                if inp.get('name'): # Skip purely decorative elements
                    f["inputs"].append({
                        "name": inp.get('name'),
                        "type": inp.get('type', 'text'),
                        "value": inp.get('value', '')
                    })
            dom["forms"].append(f)
            
        # Parse interactive links
        for link in soup.find_all('a'):
            href = link.get('href')
            if href and not href.startswith('#') and 'logout' not in href:
                dom["links"].append({
                    "text": link.get_text(strip=True),
                    "href": href
                })
                
        return jsonify({"status": "success", "dom": dom})
        
    except Exception as e:
        return jsonify({"status": "error", "message": f"DOM Extraction failed: {str(e)}"}), 500

@app.route('/api/agent/v1/exploit/atomic', methods=['POST'])
def agent_atomic_probe():
    """
    Atomic Worker API: Executes a single granular HTTP probe.
    Returns the 'JSON Delta' (reward signals) for the RL Brain.
    """
    data = request.json
    # Expected format: { "method": "GET/POST", "url": "...", "params": {...}, "payload": "..." }
    
    session_id = data.get('session_id')
    method = data.get('method', 'GET').upper()
    path = data.get('path', '/')
    payload = data.get('payload', '')
    param_name = data.get('param_name', 'id')
    
    try:
        # 1. Prepare Request
        params = {}
        if method == 'GET':
            params[param_name] = payload
        
        # 2. Execute via Container
        container = get_target_container()
        if not container or container.status != 'running':
             return jsonify({"status": "error", "message": "Container not running or not found"}), 500
        
        start_time = time.time()
        
        if method == 'GET':
            # Use curl to preserve precise response metrics
            cmd = f"curl -s -o /dev/null -w '%{{http_code}},%{{size_download}},%{{time_total}}' 'http://localhost{path}?{param_name}={payload}'"
        else:
            # POST version
            cmd = f"curl -s -o /dev/null -w '%{{http_code}},%{{size_download}},%{{time_total}}' -d '{param_name}={payload}' 'http://localhost{path}'"
            
        result = container.exec_run(cmd)
        output = result.output.decode().strip()
        
        # Parse curl metrics: status,size,time
        parts = output.split(',')
        status_code = int(parts[0]) if len(parts) > 0 else 0
        response_size = int(parts[1]) if len(parts) > 1 else 0
        time_taken = float(parts[2]) if len(parts) > 2 else 0.0
        
        # 3. Calculate Delta (Reward Signals)
        # In a real SAR setup, we'd compare this to a baseline
        delta = {
            "status_code": status_code,
            "response_length_diff": response_size, # Simplified for now
            "time_delta": time_taken,
            "success_probability": 0.8 if status_code == 200 else 0.1
        }
        
        return jsonify({
            "status": "success",
            "delta": delta,
            "action_executed": f"{method} on {path}"
        })
        
    except Exception as e:
        return jsonify({"status": "error", "message": f"Atomic Probe failed: {str(e)}"}), 500

if __name__ == '__main__':
    print("=" * 60)
    print("HackOps Flask API Bridge - Enhanced Version")
    print("=" * 60)
    print(f"Project root: {PROJECT_ROOT}")
    print(f"Config path: {CONFIG_PATH}")
    print(f"Logs path: {LOGS_PATH}")
    print()
    print("Starting on http://localhost:5000")
    print("API Endpoints:")
    print("  POST /api/environment/start")
    print("  POST /api/environment/stop")
    print("  GET  /api/environment/status")
    print("  GET  /api/session/<id>")
    print("  GET  /api/session/<id>/vulnerabilities")
    print("  POST /api/exploit/report")
    print("  POST /api/defense/apply")
    print("  GET  /api/logs")
    print("  NEW:")
    print("  GET  /api/code/view/<session_id>/<vuln_id>")
    print("  POST /api/code/update/<session_id>/<vuln_id>")
    print("  POST /api/code/test/<session_id>/<vuln_id>")
    print("  POST /api/ai/step") # Added AI endpoint to list
    print("=" * 60)
    
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)