# HackOps Master Implementation Plan: Hybrid AI & Professional Simulation

This document serves as the **Definitive Technical Specification** for the HackOps Graduation Project. It merges the professional toolset (Milestone 1) with the advanced SAR (Strategy-Action-Reflection) AI architecture and a structured 5-week team schedule.

## 🏁 The Logic: "SAR" Hybrid Architecture

We avoid "simple automation" by implementing a hierarchical intelligence system:

1.  **The RL Brain (Strategy)**: PPO-based agent that selects *goals* (e.g., "Exploit DB").
2.  **The LLM+Mamba Actioner (Tactics)**: Translates goals into *sequences* of commands.
    - **LLM**: Provides the "Intuition" (e.g., "This looks like MariaDB, try time-based SQLi").
    - **Mamba**: Manages the high-frequency probe sequences (SSM architecture).
3.  **The Post-Session Mentor (Reflection)**: Analyzes logs to explain "Why" the outcome happened.

---

## 📅 Project Milestones & Team Schedule (Merged)

### Week 1: Foundation & Data Generation (Focus: Codebase & Data)
*Dependency: Dev Team must define use-case syntax for the AI Team by Day 3.*

| Role | Responsibility | Milestone / Deliverable |
|---|---|---|
| **AI A (Red)** | Attack Scenario Generation | `red_dataset.jsonl`: 1k+ "Goal -> Action Sequence" pairs. |
| **AI B (Blue)** | Defense Scenario Generation | `blue_dataset.jsonl`: 1k+ "Vuln -> Patch Logic" pairs. |
| **Dev C (UI)** | Aesthetic Refactor | Glassmorphism Dashboard, Dark Mode & Tool Output Modals. |
| **Dev D (Tools)** | Scanner Orchestration | Finalize `HackOpsScanner` & `ZAP` REST API wrappers. |
| **Dev E (API)** | Agent Bridge | Implement the `DOM Mapper` and `Atomic Worker` JSON APIs. |

### Week 2: Independent RL Training (Focus: The "Brains")
*Goal: Train the models to understand the 'SAR' strategy separately from execution.*

- **RL Training**: Use `StableBaselines3` (PPO) to train agents on high-level state representations.
- **Difficulty Checkpoints**:
    - **Easy**: Checkpoint at 5,000 steps (High reward for speed, ignore stealth).
    - **Medium**: Checkpoint at 50,000 steps (Balanced).
    - **Hard**: Checkpoint at 200,000 steps (High penalty for WAF triggers).

| Role | Milestone / Deliverable |
|---|---|
| **AI A & B** | `red_brain_v1.zip` & `blue_brain_v1.zip` (Converged Strategic Models). |
| **Dev C/D/E** | Full Console Integration: Native tools working via UI buttons. |

### Week 3: Fine-Tuning The Actioners (Focus: The "Hands")
*Goal: Fine-tune the LLM+Mamba models using LoRA to handle the tool syntax.*

- **Actioner Logic**: Input: `"SQLi on Search"`. Output: `{"payload": "' OR 1=1 --", "encoding": "URL"}`.
- **Model Architecture**: Mamba-based sequence model for long-context fuzzing memory.

| Role | Milestone / Deliverable |
|---|---|
| **AI A & B** | Fine-tuned Red/Blue Actioners (Mamba-based) that output valid JSON for the `Atomic Worker`. |
| **Dev All** | `AIOrchestrator` implementation: Connecting the RL Brain to the fine-tuned Actioner. |

### Week 4: Adversarial Self-Play & Mentorship (Focus: Reflection)
*Goal: Make the platform "Professional" with competitive agents and feedback.*

- **Self-Play**: Red Brain plays against Blue Brain to discover sophisticated evasion/detection patterns.
- **Mentor Training**: Fine-tune a specialized LLM on *Session Logs* to generate the "SAR Reflection" report.

| Role | Milestone / Deliverable |
|---|---|
| **AI A & B** | `red_agent_pro.zip` and the **Post-Session Reflection Model**. |
| **Dev All** | Feedback UI: Display the "AAR" (After Action Report) with tool-tips for improvement. |

### Week 5: Final Validation & Thesis Handover
- **Benchmarking**: Compare Human Success Rate vs. AI-Easy vs. AI-Hard.
- **Documentation**: Finalize the "Graduation Project Technical Thesis".

---

## 🛠️ Technical Toolset Mapping

| Layer | Tool / Model | Tech Stack | Role |
|---|---|---|---|
| **Strategic** | **RL Brain** | PyTorch / SB3 | Decision-making Policy |
| **Tactical** | **Mamba Actioner** | Mamba / SSM | High-speed sequence execution |
| **Intuitive** | **Local LLM** | Llama-3 / LoRA | Reasoning & Exploit design |
| **Offensive** | **sqlmap / RedScanner** | Python / HTTP | Target exploitation |
| **Defensive** | **ZAP / Semgrep** | Docker / REST | Vulnerability management |
| **Reflective** | **Post-Session LLM** | GPT-4/Claude API | "Why it failed" Analysis |

---

## 📶 Difficulty System (Checkpoint Selection)
The platform allows the user to select difficulty by loading different training snapshots of the models:
1.  **Easy**: Uses the early-epoch checkpoint (Loud & Direct).
2.  **Medium**: Uses the mid-convergence checkpoint (Standard best practices).
3.  **Hard**: Uses the fully-converged adversarial checkpoint (Professional Evasion).

---

## 📖 Terminology & Tool Roles (Human vs. AI)

To ensure the thesis clearly distinguishes between the two types of operators, we categorize tools by their primary "User Interface":

### 🤖 AI-Centric Tools (The "Internal" Intelligence)
These tools are designed for programmatic consumption (JSON APIs) and require no visual feedback:
- **Atomic Worker**: The **"Fingers"** of the AI. A granular API for sending single probes and receiving JSON deltas.
- **Mamba Actioner**: The **"Nervous System"**. A high-speed sequencer that chooses which atomic probes to send next.
- **RL Brain (PPO)**: The **"Strategic Core"**. Sets high-level objectives based on mission success and evasion rewards.

### 👤 Human-Centric Tools (The "External" Dashboard)
These tools are designed for visual analysis, manual decision-making, and educational feedback:
- **HackOpsScanner**: The **"Instant Scout"**. Provides immediate, color-coded status updates on the site's health for the Human player.
- **Evasion Lab**: The **"Crafting Station"**. A UI utility for humans to manually encode and test bypasses against the WAF.
- **Reflection Model (Hint LLM)**: The **"Post-Session Mentor"**. A human-readable report explaining the "Why" behind successes and failures.

### ⚒️ Hybrid Power Tools (Shared Infrastructure)
These are industry-standard tools repurposed for both types of users:
- **sqlmap**: Used by **Humans** via the Terminal UI; used by **AI** as a high-level "Finish" action once a vuln is confirmed.
- **OWASP ZAP**: Used by **Humans** for deep site auditing; used by **AI** as a "Background Radar" to generate the initial alert list.
- **Semgrep**: Used by **Humans** to find bugs in the patch editor; used by **AI** to perform rapid static analysis on defenders' source code.

---

## 🔬 AI Model Architecture & Communication Summary

This section details the "Intelligence Layer" of the HackOps platform, defining how each model is built and how they interact.

### 1. Model Specifications

| Model Name | Architecture | Source/Origin | Benchmark Metrics |
|---|---|---|---|
| **RL Strategic Brain** | Policy Network (PPO) | **From Scratch** | **Success Rate (%)**: Flags found / Sessions.<br>**Efficiency**: Average steps to exploit.<br>**Stealth**: WAF trigger rate (minimization). |
| **LLM Reasoning Agent** | Transformer (Llama-3-8B) | **Hugging Face** | **Pass@k**: Quality of exploit templates.<br>**Semantic Accuracy**: Logic alignment with vulnerability type. |
| **Mamba Actioner** | Selective State Space (SSM) | **Hugging Face** | **Command Validity**: % of valid tool syntax.<br>**Probe Throughput**: Requests per second.<br>**Precision**: Correct parameter targeting. |
| **Reflection Model** | Transformer (Large) | **HF / GPT-4** | **Usefulness Score**: Human expert rating (1-10).<br>**Informational Density**: Fact-per-sentence ratio in debriefs. |

### 2. Implementation Strategy (HF vs. Scratch)
- **Scratch-Built**: The **RL Strategic Brain** is built manually using `gymnasium` and `StableBaselines3` environments. This is because the "Rules of Engagement" are unique to HackOps.
- **Hugging Face (Fine-Tuned)**: The **LLM Reasoning** and **Mamba Actioner** utilize pre-trained models from Hugging Face, but are fine-tuned using **LoRA (Low-Rank Adaptation)** on our custom `red_dataset.jsonl` to understand tool syntax.

### 3. Communication Flow (The Hacking Pipeline)

1.  **State Observation**: The `DOM Mapper` sends page JSON to the **RL Strategic Brain**.
2.  **Strategic Decision**: **RL Brain** selects a **Goal** (e.g., "Exploit Login Form").
3.  **Logical Design**: **LLM Reasoning Agent** takes the Brain's Goal + Page JSON and designs an **Exploit Template**.
4.  **Tactical Execution**: **Mamba Actioner** takes the Template and streams **Atomic Probes** (probes -> results) in a tight loop via the **Atomic Worker**.
5.  **Learning Loop**: The **Atomic Worker** returns "Deltas" (rewards). If a flag is found, the **RL Brain** receives a $+1$ reward; if a WAF triggers, it receives a $-1$.
6.  **Final Debrief**: After the session, the **Reflection Model** reads the entire log history to generate the human-readable "After Action Report" (AAR).

### 🌉 The RL-to-Actioner Bridge (Goal Dispatching)

To move from "Strategy" to "Action", we use a structured **Goal Dispatcher** protocol:

1.  **Discrete Output**: The **RL Brain** outputs an Action Vector (e.g., `[Target: 5, Type: SQLi]`).
2.  **Prompt Synthesis**: A Python middleware takes this vector and pulls the corresponding HTML/JSON context for `Target 5` from the `DOM Mapper`.
3.  **Task Handover**: The Brain sends a **Task Packet** to the Actioner:
    ```json
    {
      "strategic_objective": "EXPLOIT_SQLI",
      "target": "form_search_q",
      "base_url": "http://target/search.php",
      "evasion_requirement": "STRICT_STEALTH"
    }
    ```
4.  **Tactical Expansion**: The **LLM/Mamba Actioner** receives this packet as a *system instruction* and generates the specific HTTP request sequences (Atomic Probes) to fulfill that specific objective.

---

## 🚀 Master TODO List (Execution Workflow)

This list defines the order of operations for a two-person AI team (**Member A** and **Member B**).

### Phase 1: Instrumentation & APIs (Week 1)
*Goal: Build the interfaces the AI needs to "see" and "act".*
- [Serial] **Member B**: Implement `DOM Mapper API` (Required for all AI observation).
- [Serial] **Member B**: Implement `Atomic Worker API` (Required for all AI execution).
- [Parallel] **Member A**: Build `gen_red_data.py` framework.
- [Parallel] **Member B**: Build `gen_blue_data.py` framework.

### Phase 2: Data Acquisition & Capture (Week 2)
*Goal: Generate the 1k+ dataset for fine-tuning.*
- [Parallel] **Member A**: Run Laboratory Fuzzing with `sqlmap`/`ZAP` and record 500 successful Red scenarios.
- [Parallel] **Member B**: Capture valid patch scenarios and record 500 successful Blue scenarios.
- [Parallel] **Both**: Use Data Augmentation scripts to expand datasets to 1.5k+ diverse entries.
- [Serial] **Both**: Final Data Cleaning & Consolidation (`red_dataset.jsonl`, `blue_dataset.jsonl`).

### Phase 3: Fine-Tuning the Actioners (Week 3)
*Goal: Create the "Tactical" models.*
- [Parallel] **Member A**: Fine-tune **Mamba Red Actioner** (LoRA) on Red Dataset.
- [Parallel] **Member B**: Fine-tune **Mamba Blue Actioner** (LoRA) on Blue Dataset.
- [Parallel] **Member B**: Fine-tune **LLM Hint Model** on the "Success vs. Failure" logic records.
- [Serial] **Both**: Verify actioner syntax reliability (Goal: >95% valid tool command output).

### Phase 4: Reinforcement Learning Strategy (Week 4)
*Goal: Train the "Strategic" Brains.*
- [Parallel] **Member A**: Train **Red RL Brain (Pytorch/SB3)** in the HackOps environment.
- [Parallel] **Member B**: Train **Blue RL Brain (Pytorch/SB3)** in the HackOps environment.
- [Parallel] **Both**: Export and save Checkpoints (Easy @ 5k steps, Medium @ 50k, Hard @ 200k+).

### Phase 5: Adversarial, Mentorship & Thesis (Week 5)
*Goal: Competition, reflection, and final delivery.*
- [Serial] **Both**: Setup **Adversarial Self-Play** loop: Red Brain attacking whereas Blue Brain patches.
- [Parallel] **Member A**: Generate Performance Benchmarks (Success Rate, Stealth).
- [Parallel] **Member B**: Integrate the **Post-Session Reflection UI** with the Hint Model.
- [Serial] **Both**: Final Project Demo & Thesis Documentation consolidation.

---

## 🏗️ Architectural Justification: Why each part is necessary?

To achieve **Autonomous Hacking**, we cannot rely on a single model. Each part serves a critical, non-redundant purpose:

- **DOM Mapper**: **Vision**. LLMs hallucinate when reading raw, messy HTML. The Mapper provides a clean, JSON-structured "map" that the AI can reliably parse.
- **RL Brain (Strategist)**: **Goal Selection**. A pure LLM lacks "patience" and can get stuck in loops. RL (PPO) is mathematically optimized to find the shortest path to a goal (the Flag) while maximizing "Stealth" (avoiding the WAF).
- **LLM Reasoning (Intuition)**: **Heuristics**. RL agents start as a "Blank Slate"—they don't know that a "Username" field is often vulnerable to SQLi. The LLM provides the common-sense security knowledge that skips thousands of wasted RL steps.
- **Mamba Actioner (Tactics)**: **Scalability**. Transformers (GPT/Llama) are slow and expensive for generating 1,000+ tiny fuzzer variations. **Mamba** is a Linear State Space model designed for high-frequency, long-sequence repetition with zero performance drop.
- **Atomic Worker (Feedback)**: **Granularity**. We need to know the *exact* outcome (bytes changed, time elapsed) of *one single probe* to calculate a reward for the RL Brain. Black-box tools like `sqlmap` hide this data.

---

## 🎓 The Training Pipeline (How we build the models)

The models are trained in four distinct phases to move from "General AI" to "Cybersecurity Expert":

### Phase 1: Supervised Fine-Tuning (SFT) - "The Classroom"
- **Models**: LLM Reasoning & Mamba Actioner.
- **Process**: Train on `red_dataset.jsonl` (1k+ pairs of "Vulnerability Context" -> "Correct Tool Command").
- **Goal**: Teach the models the "Grammar" of security tools so they never output a syntax error.

#### 📊 Data Acquisition & Synthesis Methodology
To generate the **1k+ high-quality training pairs**, we use a three-pronged approach:

1.  **LLM-Bootstrapping (Synthetic)**:
    - **Script**: `gen_red_data.py`.
    - **Process**: We feed a powerful model (GPT-4/Claude) the `vulns.json` schema and the `DOM Mapper` output format. We ask it to generate "Reasonable but diverse" attack scenarios for each vulnerability type.
    - **Output**: 500+ synthetic pairs of *"Form on Page X looks like SQLi"* ➔ *"Use sqlmap --level 5"*.

2.  **Laboratory Fuzzing (Capture)**:
    - **Process**: We run `sqlmap`, `ZAP`, and `HackOpsScanner` against our intentionally vulnerable environment (DVWA).
    - **Capture**: The `Atomic Worker` logs every request/response that leads to a "Success" (Flag found).
    - **Output**: 300+ "Real-world" sequences of successful exploits.

3.  **Data Augmentation (Variation)**:
    - **Process**: We take the "Real-world" sequences and use a script to randomly change table names, column names, and URL paths.
    - **Goal**: This prevents the AI from simply "Memorizing" DVWA. It forces the AI to learn the **Logic** of the attack rather than the specific strings.

---

### Phase 2: Environment Interaction (RL) - "The Practice Lab"
- **Model**: RL Strategic Brain.
- **Process**: Plug the Brain into a headless version of HackOps.
- **Rewards**: 
    - **+100**: Find a Flag.
    - **+10**: Identify a new hidden page.
    - **-50**: Trigger the WAF.
    - **-1**: Every wasted request (Efficiency Penalty).
- **Goal**: Optimize the "Policy" for the highest success rate with the lowest noise.

### Phase 3: Checkpointing - "Difficulty Scaling"
- **Process**: Take "Snapshots" of the RL Brain at different training intervals:
    - **Junior Level**: 5k steps (Finds obvious vulns, very noisy).
    - **Pro Level**: 50k steps (Strategic, uses basic bypasses).
    - **Elite Level**: 500k steps (Surgical precision, handles complex WAFs).

### Phase 4: Adversarial Self-Play - "The War"
- **Models**: Red RL Brain vs. Blue RL Brain.
- **Process**: The Red agent tries to exploit the system while the Blue agent tries to patch it in real-time.
- **Goal**: Hardening both agents against "Human-like" intelligent opposition.

---

## 📈 AI Training Process Metrics

To monitor the health and convergence of each model during the 5-week development cycle, the following technical metrics will be tracked using **Weights & Biases** or **Tensorboard**:

### 1. RL Strategic Brain (Training Metrics)
- **Mean Reward per Episode**: Steady increase indicates the agent is learning the objective.
- **Episode Length**: A decrease over time indicates the agent is finding more efficient (shorter) exploit paths.
- **Value Loss**: Measures the accuracy of the agent's state value estimations (Lower is better).
- **Policy Entropy**: Indicates exploration. It should start high and slowly decrease as the agent becomes confident in its actions.
- **Explained Variance**: Should ideally be close to $1.0$, indicating the value function is predicting rewards accurately.

### 2. LLM & Mamba Actioners (SFT Metrics)
- **Cross-Entropy Loss**: Measures how well the model predicts the correct next token in the `red_dataset.jsonl`.
- **Perplexity**: A measure of how "confused" the model is. Successful fine-tuning should see a sharp drop in perplexity.
- **Token Accuracy**: The percentage of tokens correctly predicted during training (Target: $>90%$ for security tool syntax).
- **Gradient Norm**: Monitor for stability to ensure the LoRA fine-tuning is not exploding or vanishing.

### 3. Reflection Model (Validation Metrics)
- **Log Reconstruction Score**: Ability of the model to correctly identify all "Critical Events" in a session log summary.
- **Inference Latency**: Ensuring the generation of the "AAR" report takes less than 30 seconds for a standard session.

---

## 🏆 System-Wide Evaluation Metrics

Beyond individual model benchmarks, the success of the HackOps platform is measured by these holistic system metrics:

### 1. Attacker Performance Metrics
- **Mean Time to Compromise (MTTC)**: The average duration from starting a session to capturing the first flag.
- **Exploit Success Rate (ESR)**: Percentage of identified vulnerabilities successfully exploited without manual intervention.
- **Stealth Index**: A ratio calculated as `(Successful Probes) / (WAF Triggers + 1)`. A higher score indicates professional evasion.

### 2. Defensive Performance Metrics
- **Mean Time to Detection (MTTD)**: How quickly the Blue AI identifies a Red Team probe.
- **Neutralization Rate**: Percentage of exploited "vulnerabilities" that are successfully patched by the Blue AI before the session ends.
- **False Positive Rate**: Frequency of legitimate traffic being blocked by the AI-managed WAF rules.

### 3. Holistic & Comparative Metrics
- **Human-AI Performance Gap**: A comparative delta measuring the Success Rate of Human Professionals vs. AI Agents (Easy, Medium, and Hard checkpoints).
- **Mentorship Turing Score**: A subjective score (1-10) based on user surveys evaluating whether the **Post-Session Reflection** provided advice indistinguishable from a human instructor.
- **Dataset Diversity Score**: A measure of how well the AI generalizes to new, unseen websites (out-of-distribution performance).
