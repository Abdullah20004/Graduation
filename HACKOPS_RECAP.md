# HackOps: AI-Powered Cybersecurity Simulation Platform
*Comprehensive Project Architecture & Final Implementation Report*

## 1. Executive Summary & Project Vision

**HackOps** was successfully launched as a fully functional, gamified cyber warfare lab. Built to resolve the static nature of traditional cybersecurity education, the platform acts as an automated sandbox where human players can compete against, or learn from, autonomous Red (Attacker) and Blue (Defender) AI agents battling in real-time.

The architecture was completed across three tightly integrated layers:
- **Vulnerable Web Application Layer**: An isolated dockerized environment running the Damn Vulnerable Web Application (DVWA) via PHP 7.4/Apache and MariaDB.
- **AI Agent Intelligence Layer**: A dual-brain infrastructure utilizing Reinforcement Learning (PPO) for strategic decision-making and a fine-tuned Large Language Model (LLM Actioner) for tactile exploit generation.
- **Interactive UI & Mentor System**: A React-based glassmorphic dashboard featuring complete Mission Control, Real-Time Logs, and an embedded **AI Mentor Model** that provides real-time Explainable AI (xAI) analysis of the agents' behavior.

---

## 2. Infrastructure & Dynamic Vulnerability Engine

The foundation of the project required a stable, reproducible, and unpredictable environment to ensure the AI actually learned cybersecurity logic rather than memorizing static flags.

- **Dynamic Injection Engine**: Engineered a custom runtime injection system (`generate_vulns.py` & `apply_vulns.php`) that autonomously seeds 5-15 random vulnerabilities (SQLi, XSS, RCE, LFI) directly into the DVWA application source on startup, guaranteeing a unique state every mission.
- **Flask API Orchestrator**: Developed a Python Flask backend to handle Docker lifecycle management, map complex CybORG continuous space actions to raw HTTP protocols, and broadcast live system logs to the React frontend.
- **React UI Dashboard**: Delivered a highly responsive, immersive mission dashboard where users can map application topology, trigger specific scans, execute exploits, and watch the AI agents maneuver in real-time.

---

## 3. Strategic RL Brain: The Core Decision Engine

To create intelligent agents capable of sophisticated penetration testing workflows (Reconnaissance -> Verification -> Exploitation), we wrapped the DVWA environment into an OpenAI Gymnasium specification utilizing the **CybORG** simulation framework.

We successfully evaluated, trained, and deployed multiple reinforcement learning paradigms using Stable Baselines3:

- **Algorithm Selection & Baseline Validation**: We established a random-agent baseline achieving a mean reward of `525.68`. Against this floor, we trained two agent architectures side-by-side:
  - **Vanilla PPO (MlpPolicy)**: Trained over `200,000` timesteps (~15.7 mins). Achieved a mean tournament reward of `814.84` (+55% improvement). While fast and reactive, it lacked the inter-step memory necessary for multi-step exploit sequencing.
  - **Recurrent PPO (LSTM Memory Policy)**: Trained over `500,000` timesteps (~17.9 hours). Achieved a dominant mean tournament reward of `1,096.21`—an astonishing **+108.5% strategic improvement over the baseline**.
- **The Power of Memory**: Implementing LSTM capabilities allowed the Red Agent to drastically reduce blind exploitation penalties (-15.0 pts). The Recurrent PPO routinely executed the perfect professional sequence: fuzzing a target page, retaining the discovered vulnerability signal in its hidden state, and instantly executing the correct targeted exploit on the subsequent turn for the +500.0 pt jackpot.

---

## 4. Tactical Layer: The LLM Actioner

To completely eliminate pre-programmed "cheating" and hardcoded lookup payloads, we stripped away static exploit templates and established a novel custom **LLM Actioner** pipeline.

- **Fine-Tuned Payload Generator**: We replaced static `random.choice()` payloads with a fine-tuned `Qwen2.5-3B-Instruct` model leveraging Low-Rank Adaptation (LoRA) suited for local GPU inference.
- **Zero-Knowledge Capabilities**: The LLM Actioner was rigorously trained to generate valid, context-aware exploit payloads directly from raw, observable HTML forms and HTTP headers, receiving zero internal application states or backend cheat IDs.
- **Scale & Robustness**: By passing the RL Brain's strategy directly to the LLM Actioner via structured Task Packets, the agent is now capable of bypassing basic WAFs, dynamically pivoting encodings, and adapting its payload formats against entirely unseen architectures.

---

## 5. Explainable AI (xAI) & The Mentor Model

Understanding *why* the AI makes a move is an absolute necessity for cybersecurity education. To bridge this gap, we engineered the **Mentor Model**, a robust Explainable AI (xAI) reflection module designed to coach platform users.

- **Chain-of-Thought (CoT) Enforcement**: Before the LLM Actioner translates a tactical action into a raw HTTP exploit, it is forced to explicitly document its reasoning chain through the Mentor Model.
- **Live Educational Insights**: The Mentor dynamically interprets both the RL Brain's strategic selection (e.g., "Why did the Red Agent choose to fuzz `/search.php` instead of `/login.php`?") and the contextual payload execution (e.g., "The server returned a MariaDB error on single-quote injection; forming a tautology payload to achieve auth bypass.").
- **Real-Time Coaching UI**: This logic stream is broadcast directly to the human player's dashboard. It effectively transforms HackOps from a simple red vs. blue simulation into a transparent, living mentor platform that proactively teaches penetration testing methodologies and system administration defense tactics live during combat.
