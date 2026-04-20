# HackOps Security Tools Integration Guide

This document provides a comprehensive overview of the security tools integrated into the HackOps platform. It is designed for cybersecurity professionals to test and verify the system's capabilities.

---

## 🛠️ Tool Categorization

### 👤 User Tools (Manual Operations)
These tools are available to the human player through the HackOps UI.

| Tool | Category | Description | How to Test |
| :--- | :--- | :--- | :--- |
| **Manual Exploitation** | Attack | Direct payload injection via the Vulnerability Detail views. | Select a vulnerability on the map, click "Open Detail", and submit a payload (e.g., `' OR '1'='1`). |
| **Evasion Lab** | Attack / Obfuscation | A sandbox to encode and obfuscate payloads to bypass simple filters. | Click the "Zap" icon in the bottom-right. Drag encoding steps (Base64, URL Encode) to see the transformed payload. |
| **Code Patching (SAST)** | Defense | Real-time code editor with integrated Semgrep (SAST) scanning. | Play as "Defender". Click a vulnerability to open the code editor. Modify the PHP code to fix the vuln and click "Save & Test". |
| **ZAP Recon** | Recon | Integrated OWASP ZAP results for site mapping. | View the "Attack Map" to see pages discovered and scanned by the automated proxy. |

### 🧠 AI Tools (Red/Blue Agents)
These actions are executed by the CybORG-integrated AI agents.

| Action | Role | Logic | How to Verify |
| :--- | :--- | :--- | :--- |
| **Auto-SQLi** | Red Agent | Automatically targets detected SQL injection points with a library of payloads. | Watch the AI Activity Log for `DVWAAutoSQLiAction` executions. |
| **Auto-XSS** | Red Agent | Automatically injects reflected and stored XSS payloads. | Watch for `DVWAAutoXSSAction` in the logs. |
| **Directory Discovery** | Red Agent | Fuzzes the environment to find hidden endpoints. | Look for `DVWADirectoryDiscoveryAction` in the AI logs. |
| **Network Port Scan** | Red Agent | Simulates Nmap-style scanning within the CybORG environment. | Look for `DVWAPortScanAction`. |

### 🤝 Shared Platform Features
Core infrastructure supporting both User and AI.

| Feature | Description | Testing |
| :--- | :--- | :--- |
| **Dynamic Vuln Engine** | Generates randomized vulnerabilities on every mission start. | Start a "New Mission" and observe different vulnerabilities appear in `vulns.json` and the UI. |
| **Action Mapping** | Translates CybORG RL actions into real-world HTTP payloads. | Review `api/action_mapper.py` to see how abstract actions become concrete attacks. |
| **Real-time Logging** | Centralized log system for AI decisions, mapping, and execution. | Monitor the "AI Agent Log" panel during active missions. |

---

## 🚀 How to Test the Integrated System

### 1. Verification of the "Victim" Environment
Ensure the DVWA container is applying vulnerabilities correctly:
- **Command**: `docker logs hackops-project-target-1`
- **Expected Output**: Should show "Applied X vulnerabilities successfully" and list endpoints like `/profile.php`.

### 2. Testing the Red AI Agent
Observe how the AI interacts with the real-world environment:
- Start a mission as **"Defender (Blue Team)"**.
- Enable the **AI Opponent** toggle (Red Agent).
- **Check the Logs**: Verify the AI moves through `Observation` -> `Decision` -> `Mapping` -> `Execution`.
- **Verify Mapping**: Confirm that an AI `Decision` (like `sqli_002`) results in a concrete `Execution` (payload like `' OR 1=1--`) in the log history.

### 3. Testing the Evasion Lab
- Open the **Evasion Lab** from the UI.
- Enter a malicious string: `<script>alert(1)</script>`.
- Add **URL Encode** and then **Base64 Encode**.
- Confirm the resulting string is correctly transformed.

### 4. Testing Software Patching (SAST Integration)
- Select a vulnerable page on the map.
- Open the **Code View**.
- Try to fix an SQL injection by adding `mysqli_real_escape_string()`.
- The system will run **Semgrep** against your changes and award points if the vulnerability pattern is no longer detected.

---

## 📁 Key Technical Components
- **`api/action_mapper.py`**: The bridge between AI logic and HTTP payloads.
- **`api/cyborg_integration.py`**: The interface between the CybORG gym environment and HackOps.
- **`apply_vulns.php`**: The dynamic PHP engine that creates vulnerabilities on the fly.
