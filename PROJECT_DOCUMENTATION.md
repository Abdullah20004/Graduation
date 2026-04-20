# HackOps: AI-Powered Cybersecurity Simulation Platform
## Complete Project Documentation

---

## Table of Contents
1. [Project Vision](#project-vision)
2. [What We're Building](#what-were-building)
3. [System Architecture](#system-architecture)
4. [Core Technologies](#core-technologies)
5. [Key Components](#key-components)
6. [AI Agent System](#ai-agent-system)
7. [Dynamic Vulnerability System](#dynamic-vulnerability-system)
8. [User Interface & Experience](#user-interface--experience)
9. [Training Pipeline](#training-pipeline)
10. [How Everything Works Together](#how-everything-works-together)
11. [Technical Implementation Details](#technical-implementation-details)
12. [Future Vision](#future-vision)

---

## Project Vision

HackOps is a **gamified cybersecurity training platform** where AI-powered agents compete in real-time cyber warfare scenarios. Think of it as a game where one AI tries to break into a website and another AI tries to fix it in real-time.

### Why This Matters

**The Problem:**
- Cybersecurity is hard to learn and practice safely
- Developers often leave security holes in their code
- Traditional security training is static and boring
- Real-world practice environments are dangerous or illegal

**Our Solution:**
- Create a safe, legal "cyber warfare lab"
- Use AI to simulate realistic attack and defense scenarios
- Make security training interactive and engaging
- Provide instant feedback on security decisions
- Generate unlimited unique scenarios for practice

---

## What We're Building

### The Core Concept

HackOps is a **three-layer system**:

1. **Vulnerable Web Application Layer**: A real, running web application (DVWA) with intentionally planted vulnerabilities
2. **AI Agent Layer**: Intelligent agents that can attack (Red Team) or defend (Blue Team) the application
3. **Interactive Dashboard**: A beautiful web interface where users can observe, control, and learn from the AI battle

### The Players

#### 🔴 Red Agent (Attacker)
- **Role**: Simulates a malicious hacker
- **Capabilities**:
  - Scans web pages for vulnerabilities
  - Identifies SQL injection, XSS, and other attack vectors
  - Crafts and executes exploit payloads
  - Learns from successful attacks
- **Goal**: Find and exploit as many vulnerabilities as possible

#### 🔵 Blue Agent (Defender)
- **Role**: Simulates a security engineer
- **Capabilities**:
  - Monitors system activity for suspicious behavior
  - Scans code for security flaws
  - Applies patches to fix vulnerabilities
  - Learns defensive strategies
- **Goal**: Secure the system before vulnerabilities are exploited

#### 👤 Human Player
- Can play as either Red or Blue team
- Competes against the AI opponent
- Learns real cybersecurity skills through gameplay

---

## System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    USER INTERFACE LAYER                      │
│  ┌────────────────────────────────────────────────────────┐ │
│  │         React Frontend (Port 3000)                     │ │
│  │  - Mission Dashboard                                   │ │
│  │  - Real-time Activity Logs                            │ │
│  │  - Code Editor                                         │ │
│  │  - AI Control Panel                                    │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                            ↕ HTTP/REST API
┌─────────────────────────────────────────────────────────────┐
│                  APPLICATION LOGIC LAYER                     │
│  ┌────────────────────────────────────────────────────────┐ │
│  │         Flask API Server (Port 5000)                   │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌─────────────┐ │ │
│  │  │   Session    │  │      AI      │  │   Docker    │ │ │
│  │  │  Management  │  │ Orchestrator │  │  Controller │ │ │
│  │  └──────────────┘  └──────────────┘  └─────────────┘ │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌─────────────┐ │ │
│  │  │ Vulnerability│  │    Action    │  │    Logs     │ │ │
│  │  │  Generator   │  │    Mapper    │  │   Manager   │ │ │
│  │  └──────────────┘  └──────────────┘  └─────────────┘ │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                            ↕ Docker API
┌─────────────────────────────────────────────────────────────┐
│                   SIMULATION LAYER                           │
│  ┌────────────────────────────────────────────────────────┐ │
│  │    Docker Containers (Isolated Environment)            │ │
│  │  ┌──────────────────────┐  ┌──────────────────────┐   │ │
│  │  │  DVWA Web Server     │  │   MariaDB Database   │   │ │
│  │  │  (Port 8080)         │  │                      │   │ │
│  │  │  - PHP Application   │  │  - User Data         │   │ │
│  │  │  - Vulnerabilities   │  │  - Session Storage   │   │ │
│  │  └──────────────────────┘  └──────────────────────┘   │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                            ↕
┌─────────────────────────────────────────────────────────────┐
│                      AI TRAINING LAYER                       │
│  ┌────────────────────────────────────────────────────────┐ │
│  │         CybORG Simulation Environment                  │ │
│  │  - Custom DVWA Environment Wrapper                     │ │
│  │  - Reinforcement Learning Training Loop               │ │
│  │  - Stable Baselines3 (PPO Algorithm)                  │ │
│  │  - Model Checkpointing & Evaluation                   │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

---

## Core Technologies

### Frontend Stack
- **React 18**: Modern UI framework
- **Lucide Icons**: Beautiful, consistent iconography
- **Vanilla CSS**: Custom styling with glassmorphism and dark themes
- **WebSockets (planned)**: Real-time updates

### Backend Stack
- **Flask**: Python web framework for API
- **Docker & Docker Compose**: Container orchestration
- **Python 3.10+**: Core programming language

### AI/ML Stack
- **CybORG**: Cyber operations research gym (simulation framework)
- **Stable Baselines3**: State-of-the-art RL algorithms
- **Gymnasium**: OpenAI Gym interface for RL environments
- **PPO (Proximal Policy Optimization)**: The RL algorithm we use
- **Jupyter Notebooks**: Interactive training and visualization

### Vulnerable Application
- **DVWA (Damn Vulnerable Web Application)**: PHP-based intentionally vulnerable web app
- **MariaDB**: Database backend
- **Apache/PHP**: Web server stack

---

## Key Components

### 1. Frontend Application (`frontend/`)

**Main Component: `App.jsx`**
- **Mission Control Dashboard**: Central hub for starting/stopping missions
- **Real-time Log Panels**:
  - DVWA Activity Log: Shows all HTTP requests and responses
  - AI Agent Activity Log: Shows AI decision-making process
- **Pages Panel**: Visual representation of application architecture
- **Mission Intel Panel**: Shows mission parameters and objectives
- **Attack/Defense Console**: Interactive interface for human players
- **AI Control Panel**: Toggle AI opponent on/off, see AI actions

**Key Features**:
- Dark, cyber-themed aesthetic with purple/cyan accents
- Smooth animations and transitions
- Responsive design
- Real-time data polling (2-3 second intervals)
- Code editor with syntax highlighting

### 2. Backend API (`api/app.py`)

**Core Responsibilities**:
- Session management (create, track, end missions)
- Docker container lifecycle management
- AI agent orchestration
- Vulnerability generation and tracking
- Action validation and scoring
- Log aggregation and serving

**Key Endpoints**:
```
POST /api/environment/start     - Start Docker containers
POST /api/environment/stop      - Stop containers
GET  /api/session/{id}          - Get session details
GET  /api/session/{id}/logs/*   - Get various log types
POST /api/attacker/test         - Test an exploit
POST /api/defender/scan         - Scan for vulnerabilities
POST /api/defender/patch        - Apply a security patch
```

### 3. AI Integration (`api/ai_integration.py`)

**AIOrchestrator Class**:
- Loads trained RL models from disk
- Manages AI agent lifecycle
- Translates between CybORG observations and DVWA state
- Executes AI decisions as real actions
- Logs AI decision-making process

**Key Methods**:
- `_initialize_agents()`: Load trained models
- `get_ai_action()`: Get next action from AI
- `_get_observation()`: Convert DVWA state to CybORG observation
- `_execute_action()`: Execute AI decision in DVWA

### 4. CybORG Integration (`api/cyborg_integration.py`)

**DVWAEnv Class**:
- Custom Gymnasium environment
- Wraps DVWA in a reinforcement learning interface
- Defines observation space (what AI can see)
- Defines action space (what AI can do)
- Implements reward function (how AI learns)

**Observation Space**:
```python
{
    'current_page': Box(0, num_pages),
    'vulnerabilities_found': Box(0, 1, shape=(max_vulns,)),
    'vulnerabilities_patched': Box(0, 1, shape=(max_vulns,)),
    'exploits_successful': Box(0, 1, shape=(max_vulns,)),
    'session_time': Box(0, inf),
    'score': Box(-inf, inf)
}
```

**Action Space**:
- Navigate to page
- Scan for vulnerabilities
- Attempt exploit
- Apply patch

### 5. Vulnerability System

**Dynamic Generation (`generate_vulns.py`)**:
- Uses random seed for reproducibility
- Generates 5-15 vulnerabilities per mission
- Supports 25+ vulnerability types
- Creates realistic exploit scenarios

**Vulnerability Types**:
- SQL Injection (various contexts)
- Cross-Site Scripting (XSS)
- Remote Code Execution (RCE)
- Local File Inclusion (LFI)
- Server-Side Request Forgery (SSRF)
- XML External Entity (XXE)
- Cross-Site Request Forgery (CSRF)
- Insecure Direct Object Reference (IDOR)
- And many more...

**Application (`apply_vulns.php`)**:
- Reads generated vulnerability config
- Modifies DVWA source code at runtime
- Injects vulnerabilities into specific locations
- Maintains exploit metadata

### 6. Docker Environment

**Target Container (`Dockerfile`)**:
- Based on PHP 7.4 with Apache
- Installs DVWA and dependencies
- Runs vulnerability generation on startup
- Exposes port 8080

**Database Container**:
- MariaDB 10.5
- Stores user data and sessions
- Health checks for reliability

**Networking**:
- Isolated bridge network
- Containers communicate internally
- Only web port exposed to host

---

## AI Agent System

### Training Architecture

**The Training Loop**:
1. **Initialize Environment**: Create DVWA instance with random vulnerabilities
2. **Reset Episode**: Start fresh mission
3. **Observation**: AI sees current state (pages, vulns, score)
4. **Decision**: AI chooses action based on policy
5. **Execution**: Action is performed in DVWA
6. **Reward**: AI receives feedback (+/- points)
7. **Learning**: AI updates its policy
8. **Repeat**: Continue until episode ends

### Reinforcement Learning Details

**Algorithm: PPO (Proximal Policy Optimization)**
- **Why PPO?**: Stable, sample-efficient, works well for discrete actions
- **Policy Network**: Neural network that maps observations → actions
- **Value Network**: Estimates expected future rewards
- **Training**: On-policy learning with clipped objective

**Reward Structure**:

For **Blue Agent (Defender)**:
```
+50  : Successfully patch a vulnerability
+30  : Proactive patch (before exploitation)
+10  : Discover a vulnerability
-20  : Vulnerability gets exploited
-5   : Invalid action
```

For **Red Agent (Attacker)**:
```
+100 : Successfully exploit critical vulnerability
+50  : Exploit high severity vulnerability
+25  : Exploit medium severity vulnerability
+10  : Discover a vulnerability
-10  : Failed exploit attempt
-5   : Invalid action
```

**Training Process**:

1. **Data Collection**: Agent interacts with environment for N steps
2. **Batch Processing**: Collect trajectories (state, action, reward sequences)
3. **Advantage Estimation**: Calculate how good each action was
4. **Policy Update**: Adjust neural network weights
5. **Evaluation**: Test on validation scenarios
6. **Checkpointing**: Save best models

### Training Tools

**Jupyter Notebook (`HackOps_Training.ipynb`)**:
- Interactive training interface
- Live progress bars and metrics
- Real-time plotting of rewards, success rates
- Model evaluation tools
- Easy hyperparameter tuning

**CLI Training Script (`train_sb3.py`)**:
- Headless training for long runs
- Command-line arguments for configuration
- TensorBoard logging
- Automatic checkpointing

**Example Training Command**:
```bash
python train_sb3.py --agent blue --timesteps 100000 --learning-rate 0.0003
```

### Model Deployment

**Trained Models** (stored in `api/models/`):
- `blue_agent_final.zip`: Trained defender
- `red_agent_final.zip`: Trained attacker
- Checkpoints saved during training

**Loading in Production**:
```python
from stable_baselines3 import PPO
model = PPO.load("models/blue_agent_final.zip")
action, _states = model.predict(observation)
```

---

## Dynamic Vulnerability System

### How It Works

**1. Seed-Based Generation**:
- User provides optional seed (or random is generated)
- Seed ensures reproducibility (same seed = same vulnerabilities)
- Python's `random` module seeded for deterministic generation

**2. Vulnerability Selection**:
```python
# Pseudocode
random.seed(user_seed)
num_vulns = random.randint(5, 15)
vuln_types = random.sample(ALL_VULN_TYPES, num_vulns)
```

**3. Configuration Generation**:
Creates JSON config with:
- Vulnerability ID
- Type (sqli, xss, etc.)
- Severity (critical, high, medium, low)
- Location (which page/file)
- Exploit details
- Patch hints

**4. Runtime Injection**:
- PHP script reads config
- Modifies DVWA source code in memory
- Injects vulnerable code snippets
- Maintains original functionality

**Example Vulnerability Config**:
```json
{
  "id": "sqli_001",
  "type": "sqli",
  "severity": "critical",
  "location": "/login.php",
  "description": "SQL Injection in login form",
  "exploit": {
    "parameter": "username",
    "payload": "' OR '1'='1"
  },
  "patch_hint": "Use prepared statements"
}
```

---

## User Interface & Experience

### Design Philosophy

**Visual Identity**:
- **Dark Theme**: Reduces eye strain, looks professional
- **Cyber Aesthetic**: Purple/cyan/red color scheme
- **Glassmorphism**: Translucent panels with backdrop blur
- **Micro-animations**: Smooth transitions, hover effects
- **Premium Feel**: High-quality, polished interface

### Key UI Components

**1. Mission Dashboard**:
- Start/stop mission controls
- Seed input for reproducible scenarios
- Role selection (Red/Blue)
- Real-time mission timer
- Score display

**2. Activity Logs**:
- **DVWA Log**: Every HTTP request, response, exploit attempt
- **AI Log**: AI's thought process, decisions, actions
- Color-coded by action type
- Auto-scrolling with manual override
- Filterable and searchable

**3. Pages Panel**:
- Visual map of application structure
- Categorized by function (Auth, Shopping, Admin, etc.)
- Color-coded by security status:
  - 🟢 Green: Fully secured
  - 🟡 Yellow: Partially patched
  - 🔴 Red: Vulnerable
  - ⚫ Gray: Exploited

**4. Attack/Defense Console**:
- **Attack Mode**:
  - Target page selection
  - Attack vector chooser (SQLi, XSS, etc.)
  - Payload editor with hints
  - Live testing against DVWA
  - Success/failure feedback
  
- **Defense Mode**:
  - Vulnerability scanner
  - Discovered vulnerabilities list
  - Code editor for patching
  - Patch validation
  - Proactive defense bonuses

**5. AI Control Panel**:
- Enable/disable AI opponent
- View AI's latest action
- See AI's current page/target
- Monitor AI decision-making

### User Workflows

**Starting a Mission**:
1. User opens dashboard
2. Selects role (Red/Blue)
3. Optionally enters seed
4. Clicks "Launch Mission"
5. System starts Docker containers
6. Vulnerabilities are generated
7. Mission begins, timer starts

**Playing as Attacker**:
1. Browse available pages
2. Select target page
3. Choose attack vector
4. Craft payload (with hints)
5. Test exploit
6. Receive feedback and points
7. AI defender may patch vulnerabilities

**Playing as Defender**:
1. Scan pages for vulnerabilities
2. Review discovered vulnerabilities
3. Open code editor
4. Apply security patches
5. Validate fixes
6. Earn points (bonus for proactive)
7. AI attacker may find new exploits

---

## Training Pipeline

### Complete Training Workflow

**Phase 1: Environment Setup**
```bash
# Create virtual environment
cd api
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Verify installation
python test_cyborg_comprehensive.py
```

**Phase 2: Training Configuration**

Edit training parameters in notebook or CLI:
```python
TRAINING_CONFIG = {
    'agent_type': 'blue',  # or 'red'
    'total_timesteps': 100000,
    'learning_rate': 0.0003,
    'batch_size': 64,
    'n_epochs': 10,
    'gamma': 0.99,  # discount factor
    'clip_range': 0.2,  # PPO clipping
}
```

**Phase 3: Training Execution**

Option A - Jupyter Notebook:
```bash
jupyter notebook
# Open HackOps_Training.ipynb
# Run cells, use interactive controls
```

Option B - CLI:
```bash
python train_sb3.py --agent blue --timesteps 100000
```

**Phase 4: Monitoring**

During training, monitor:
- **Episode Rewards**: Should increase over time
- **Success Rate**: % of successful actions
- **Episode Length**: How long agent survives
- **Loss Values**: Should decrease and stabilize

**Phase 5: Evaluation**

After training:
```python
# Load trained model
model = PPO.load("models/blue_agent_final.zip")

# Evaluate on test scenarios
mean_reward, std_reward = evaluate_policy(model, env, n_eval_episodes=10)
```

**Phase 6: Deployment**

Copy trained model to production:
```bash
cp api/models/blue_agent_final.zip api/models/
# Restart Flask API
python app.py
```

### Training Metrics

**Key Performance Indicators**:
- **Mean Episode Reward**: Average points per episode
- **Success Rate**: % of actions that succeed
- **Vulnerability Discovery Rate**: How fast agent finds vulns
- **Patch/Exploit Efficiency**: Actions per successful outcome
- **Episode Length**: How long before mission ends

**Visualization**:
- Real-time plots in Jupyter
- TensorBoard logs for detailed analysis
- CSV exports for custom analysis

---

## How Everything Works Together

### Complete Mission Flow

**1. Mission Initialization**:
```
User clicks "Launch Mission"
  ↓
Frontend sends POST to /api/environment/start
  ↓
Backend generates random seed (or uses provided)
  ↓
Docker containers start (DVWA + MariaDB)
  ↓
Vulnerability generator runs with seed
  ↓
Vulnerabilities injected into DVWA
  ↓
Session created in backend
  ↓
Frontend receives session ID
  ↓
Dashboard updates with mission info
```

**2. AI Agent Activation**:
```
User enables AI opponent
  ↓
AIOrchestrator loads trained model
  ↓
Timer starts (AI acts every 5-10 seconds)
  ↓
AI observes current state
  ↓
AI chooses action (navigate, scan, exploit, patch)
  ↓
Action mapped to DVWA operation
  ↓
Action executed via HTTP request
  ↓
Result logged and scored
  ↓
AI receives reward signal
  ↓
Repeat
```

**3. Human Player Action**:
```
User selects action in console
  ↓
Frontend validates input
  ↓
POST request to appropriate endpoint
  ↓
Backend validates action
  ↓
Action executed in DVWA
  ↓
Result captured and analyzed
  ↓
Points awarded/deducted
  ↓
Logs updated
  ↓
Frontend polls for updates
  ↓
UI refreshes with new data
```

**4. Real-time Updates**:
```
Frontend polls every 2 seconds
  ↓
GET /api/session/{id}/logs/activity
GET /api/session/{id}/logs/ai
GET /api/session/{id}/pages
  ↓
Backend aggregates latest data
  ↓
JSON response sent to frontend
  ↓
React state updated
  ↓
UI re-renders with new info
```

**5. Mission End**:
```
User clicks "End Mission"
  ↓
Final scores calculated
  ↓
Mission summary generated
  ↓
Docker containers stopped
  ↓
Logs archived
  ↓
Session marked as complete
  ↓
Results displayed to user
```

---

## Technical Implementation Details

### Session Management

**Session Object Structure**:
```python
{
    'session_id': 'session_1234567890',
    'seed': 42,
    'start_time': datetime,
    'role': 'blue',  # or 'red'
    'vulnerabilities': [...],
    'discovered_vulns': [...],
    'exploited_vulns': [...],
    'patched_vulns': [...],
    'score': {'attacker': 0, 'defender': 0},
    'logs': {
        'activity': [...],
        'ai': [...],
        'system': [...]
    }
}
```

### Action Mapping

**CybORG Actions → DVWA Operations**:

```python
# Example: Navigate action
cyborg_action = Navigate(page_id=5)
  ↓
dvwa_action = {
    'type': 'http_request',
    'url': 'http://localhost:8080/products.php',
    'method': 'GET'
}

# Example: Exploit action
cyborg_action = Exploit(vuln_id='sqli_001', payload="' OR '1'='1")
  ↓
dvwa_action = {
    'type': 'http_request',
    'url': 'http://localhost:8080/login.php',
    'method': 'POST',
    'data': {'username': "' OR '1'='1", 'password': 'anything'}
}
```

### Logging System

**Three Log Types**:

1. **Activity Logs**: DVWA HTTP traffic
   ```python
   {
       'timestamp': '2024-01-24T19:00:00',
       'action_type': 'exploit',
       'location': '/login.php',
       'description': 'SQL Injection attempt',
       'payload': "' OR '1'='1",
       'success': True
   }
   ```

2. **AI Logs**: Agent decision process
   ```python
   {
       'timestamp': '2024-01-24T19:00:05',
       'agent_type': 'red',
       'stage': 'decision',
       'details': 'Chose to exploit sqli_001',
       'current_page': '/login.php',
       'success': True
   }
   ```

3. **System Logs**: Infrastructure events
   ```python
   {
       'timestamp': '2024-01-24T19:00:00',
       'level': 'INFO',
       'message': 'Docker container started',
       'details': {...}
   }
   ```

### Scoring System

**Point Values**:
```python
POINTS = {
    'attacker': {
        'exploit_critical': 100,
        'exploit_high': 50,
        'exploit_medium': 25,
        'exploit_low': 10,
        'discover_vuln': 10,
        'failed_exploit': -10,
        'invalid_action': -5
    },
    'defender': {
        'patch_proactive': 50,
        'patch_reactive': 30,
        'discover_vuln': 10,
        'vuln_exploited': -20,
        'invalid_action': -5
    }
}
```

### Error Handling

**Graceful Degradation**:
- Docker failures → Clear error messages
- AI model errors → Fallback to random agent
- Network issues → Retry with exponential backoff
- Invalid actions → User feedback, no crash

---

## Future Vision

### Planned Features

**Short-term (Next 3 months)**:
- [ ] WebSocket support for true real-time updates
- [ ] More sophisticated Red Agent training
- [ ] Multiplayer mode (human vs human)
- [ ] Replay system (watch past missions)
- [ ] Leaderboard and achievements

**Medium-term (6 months)**:
- [ ] Support for other vulnerable apps (OWASP Juice Shop, etc.)
- [ ] Custom vulnerability creation tool
- [ ] Advanced AI techniques (multi-agent RL, curriculum learning)
- [ ] Mobile-responsive design
- [ ] Tutorial mode for beginners

**Long-term (1 year+)**:
- [ ] Cloud deployment (AWS/Azure)
- [ ] Collaborative team missions
- [ ] Integration with real CTF platforms
- [ ] AI vs AI tournaments
- [ ] Educational curriculum integration
- [ ] Certification program

### Research Opportunities

- **Transfer Learning**: Can agents trained on DVWA work on other apps?
- **Adversarial Training**: Train Red and Blue agents against each other
- **Explainable AI**: Visualize why AI makes certain decisions
- **Human-AI Collaboration**: Hybrid teams of humans and AI
- **Automated Patch Generation**: Can AI write secure code?

---

## Conclusion

HackOps represents a **new paradigm in cybersecurity education**: combining the engagement of gaming, the intelligence of AI, and the practicality of real-world scenarios. By making security training interactive, safe, and intelligent, we're creating a platform that can:

- **Educate** the next generation of security professionals
- **Research** new AI techniques for cyber defense
- **Demonstrate** the power of reinforcement learning in security
- **Inspire** interest in cybersecurity careers

This is not just a graduation project—it's a **foundation for the future of cybersecurity training**.

---

**Project Status**: Active Development  
**Current Version**: 1.0 Beta  
**Last Updated**: January 2026  
**Team**: HackOps Development Team  
**License**: Educational Use
