# HackOps LLM Actioner: Comprehensive Training Plan

> **Purpose**: This document is the definitive technical specification for training the **LLM Actioner** — the "Tactical Hands" of the HackOps AI system. It covers data generation, model architecture, training methodology, anti-cheating safeguards, and integration with the existing RL+PPO Strategic Brain.

---

## Table of Contents

1. [System Context: Where the LLM Fits](#1-system-context-where-the-llm-fits)
2. [The Anti-Cheating Philosophy](#2-the-anti-cheating-philosophy)
3. [Data Generation Pipeline](#3-data-generation-pipeline)
4. [Data Format Specification](#4-data-format-specification)
5. [Model Architecture and Selection](#5-model-architecture-and-selection)
6. [Training Methodology](#6-training-methodology)
7. [Integration with the RL+PPO Brain](#7-integration-with-the-rlppo-brain)
8. [Explainability & Trust (xAI) Strategy](#8-explainability--trust-xai-strategy)
9. [Evaluation and Validation](#9-evaluation-and-validation)
10. [Deployment Architecture](#10-deployment-architecture)
11. [File Deliverables](#11-file-deliverables)

---

## 1. System Context: Where the LLM Fits

The HackOps AI operates as a **three-layer hierarchy**:

**Layer 1 — RL Strategic Brain (PPO / RecurrentPPO)**
- Input: Observation vector (fuzz signals, vuln status)
- Output: Strategic Decision (action index)
- Example: "Fuzz /search.php for SQLi", "SmartExploit /login.php with SQLi"
- Models: `red_agent_final.zip` (Vanilla PPO), `red_agent_lstm_final.zip` (RecurrentPPO)

**Layer 2 — LLM Actioner (THIS MODEL)**
- Input: Task Packet from Brain + Page Context (HTML/features)
- Output: Concrete attack payload or tool command
- Example: `curl -s -G 'http://target/search.php' --data-urlencode 'q=\' UNION SELECT 1,username,password FROM users--'`

**Layer 3 — Atomic Worker / DVWA Controller**
- Executes the payload against the target
- Returns the raw HTTP response / success signal

### What the LLM Does NOT Do
- It does **NOT** decide *what* to attack — that is the RL Brain's job.
- It does **NOT** evaluate success — that is the Atomic Worker's job.
- It **ONLY** translates a strategic objective into a concrete, syntactically valid payload.

### Why We Need It
The RL Brain outputs discrete action indices (e.g., action `37` = "SmartExploit /login.php with SQLi"). But a discrete index is not a real HTTP request. The LLM bridges this gap by generating the **actual exploit payload** that a real penetration testing tool would use. Without it, we are limited to a hardcoded lookup table of payloads (which is what `ActionMapper._map_smart_exploit()` does today with `random.choice()` — and that IS cheating).

---

## 2. The Anti-Cheating Philosophy

The current system has a critical weakness: `ActionMapper` uses a **static catalog of payloads** selected via `random.choice()`. This means:

- The "AI" is not generating payloads — it is picking from a pre-written list.
- The payloads are DVWA-specific and would fail on any other target.
- There is zero reasoning about WHY a payload works against a specific page.

### Our Anti-Cheating Rules

| Rule | Description |
|------|-------------|
| **No Vuln-ID Leakage** | The LLM must NEVER receive a vulnerability ID (`sqli_login`, `xss_stored_review`). It only receives observable information: page URL, HTML structure, form fields, HTTP headers. |
| **No Direct Answer Injection** | Training data must not contain pairs like "Page has SQLi -> Use `' OR 1=1`". Instead, pairs must include the **reasoning chain**: "Page has a login form -> form submits to SQL backend -> try authentication bypass -> `' OR '1'='1' --`". |
| **No Target-Specific Memorization** | All training examples must use **randomized** hostnames, paths, parameter names, and table structures. The model must learn the *pattern* of SQLi, not the *strings* of DVWA. |
| **Observable-Only Input** | The LLM receives only what a real attacker would see: HTTP response fragments, form HTML, error messages — never internal database schemas or source code. |
| **Tool Syntax Validity** | Every generated command must be syntactically valid and executable. We measure this with a syntax validator during evaluation. |

---

## 3. Data Generation Pipeline

We generate training data from **four independent sources** to maximize diversity and prevent overfitting.

### Source 1: Synthetic Scenario Generation (Primary — 40% of dataset)

**Script**: `gen_red_actioner_data.py` (to be created)

This generator creates diverse attack scenarios by combining:
- Randomized target URLs (not just DVWA pages)
- Randomized parameter names
- Randomized backend technologies (MySQL, PostgreSQL, MSSQL, SQLite)
- Multiple evasion levels (none, basic encoding, WAF bypass)

**Generation Logic**:

    For each scenario:
      1. Pick a vulnerability class (SQLi, XSS, RCE, LFI, etc.)
      2. Generate a random target context:
         - Random hostname (e.g., shop.example.com, api.corp.internal)
         - Random page path (e.g., /api/v2/users, /checkout, /search)
         - Random parameter names (e.g., q, user_id, term, keyword)
         - Random backend technology hints (MySQL error, MSSQL error, etc.)
      3. Generate the "Observable Context" (what a real scanner would see):
         - HTTP response snippet with error message or reflection
         - Form HTML with input fields
         - HTTP headers (Server, X-Powered-By, etc.)
      4. Generate the correct tool command or payload
      5. Generate the reasoning chain (WHY this payload works)

### Source 2: Real Tool Output Capture (25% of dataset)

**Process**: Run actual security tools against our DVWA Docker environment and record the successful sequences.

**Tools to capture from**:
- `sqlmap` — Record the exact probe sequences and final payloads for confirmed SQLi.
- `XSStrike` / manual XSS — Record successful reflections with context.
- `gobuster` / `ffuf` — Record directory discovery patterns.

**Capture format**:

    For each successful exploit:
      1. Record the HTTP request/response chain (sanitized)
      2. Record the final working payload
      3. Record the tool flags used (e.g., --level 5, --risk 3)
      4. Anonymize all DVWA-specific identifiers

### Source 3: Public Vulnerability Databases (20% of dataset)

**Sources**:
- HackerOne disclosed reports (public)
- OWASP Testing Guide examples
- PortSwigger Web Security Academy labs
- CVE descriptions with proof-of-concept payloads

**Process**:
1. Extract the vulnerability description + context
2. Extract the working payload
3. Format into our standard training format
4. Ensure no copyrighted content — only use freely available public data

### Source 4: Data Augmentation (15% of dataset)

**Augmentation techniques applied to Sources 1-3**:

| Technique | Description | Example |
|-----------|-------------|---------|
| **Host Randomization** | Replace hostnames with random domains | `dvwa.local` -> `shop.acme.io` |
| **Parameter Shuffling** | Rename parameters | `id=1` -> `product_id=1`, `uid=1` |
| **Backend Variation** | Change DB-specific syntax | MySQL `SLEEP(5)` -> PostgreSQL `pg_sleep(5)` |
| **Encoding Variation** | Apply different encodings | `<script>` -> `%3Cscript%3E` -> `&#60;script&#62;` |
| **WAF Evasion Layer** | Add bypass techniques | `' OR 1=1--` -> `'/*!50000OR*/1=1--` |
| **Comment Style Variation** | Different SQL comment styles | `--` -> `#` -> `/**/` |

---

## 4. Data Format Specification

Every training example follows a strict **Instruction -> Context -> Response** format, designed for supervised fine-tuning (SFT).

### 4.1 Red Actioner (Attack) Data Format

```json
{
  "instruction": "Generate a SQL injection payload to bypass authentication on the target login form.",
  "context": {
    "strategic_objective": "EXPLOIT_SQLI",
    "target_url": "http://shop.acme.io/login.php",
    "target_parameter": "username",
    "http_method": "POST",
    "observable_context": {
      "form_html": "<form method='POST' action='login.php'><input name='username'><input name='password'><button>Login</button></form>",
      "server_headers": {
        "Server": "Apache/2.4.41",
        "X-Powered-By": "PHP/7.4.3"
      },
      "error_on_single_quote": "You have an error in your SQL syntax; check the manual that corresponds to your MariaDB server version",
      "fuzz_signal": "SQL_ERROR_DETECTED"
    },
    "evasion_level": "none",
    "backend_hint": "MariaDB"
  },
  "reasoning": "The login form submits a username parameter via POST to a PHP backend connected to MariaDB. The server returned a SQL syntax error when a single quote was injected, confirming unsanitized input is concatenated into a SQL query. An authentication bypass payload using OR-based tautology will make the WHERE clause always true.",
  "response": {
    "tool": "curl",
    "command": "curl -s -X POST 'http://shop.acme.io/login.php' -d 'username=admin%27+OR+%271%27%3D%271&password=anything'",
    "raw_payload": "admin' OR '1'='1",
    "encoding": "URL",
    "attack_class": "auth_bypass",
    "confidence": 0.85
  }
}
```

### 4.2 Blue Actioner (Defense) Data Format

```json
{
  "instruction": "Generate a patch command to fix the SQL injection vulnerability in the login handler.",
  "context": {
    "strategic_objective": "PATCH_SQLI",
    "target_file": "login.php",
    "vulnerability_type": "sqli",
    "observable_context": {
      "vulnerable_code_snippet": "$query = 'SELECT * FROM users WHERE username=' . $_POST['username'];",
      "framework": "PHP/PDO",
      "database": "MySQL"
    }
  },
  "reasoning": "The code directly concatenates user input into a SQL query string. The fix must use parameterized queries (prepared statements) to separate code from data.",
  "response": {
    "tool": "code_patch",
    "fix_type": "prepared_statement",
    "patched_code": "$stmt = $pdo->prepare('SELECT * FROM users WHERE username = ?'); $stmt->execute([$_POST['username']]);",
    "confidence": 0.95
  }
}
```

### 4.3 Key Design Decisions in the Format

1. **`reasoning` field**: This is the Chain-of-Thought (CoT). During training, we include it in the target output so the model learns to "think" before generating the payload. During inference, we can optionally request it or skip it for speed.

2. **`observable_context`**: This replaces the cheating `vuln_id` field. It contains ONLY information that a real scanner/fuzzer would produce: error messages, form HTML, headers. The model must learn to *infer* the vulnerability type from these signals.

3. **`evasion_level`**: This connects to the RL Brain's difficulty setting. The Brain can request `"none"`, `"basic"`, or `"waf_bypass"` depending on the scenario.

4. **`confidence`**: The model outputs its confidence in the payload. Low confidence payloads can trigger the Brain to try a different approach.

---

## 5. Model Architecture and Selection

### 5.1 Base Model Selection

Given the project's GPU constraints (single GPU with ~4-8GB VRAM for training), we recommend:

| Model | Parameters | VRAM (LoRA) | Pros | Cons |
|-------|-----------|-------------|------|------|
| **Qwen2.5-3B-Instruct** | 3B | ~6GB | Excellent instruction following, strong code generation, MIT license | Slightly slower than Phi |
| **Phi-3-mini-4k-instruct** | 3.8B | ~7GB | Very strong reasoning for size, Microsoft-backed | Slightly larger |
| **TinyLlama-1.1B-Chat** | 1.1B | ~3GB | Ultra-lightweight, fast | Lower quality outputs |

**Recommendation**: **Qwen2.5-3B-Instruct** — best balance of quality, VRAM usage, and license freedom for a graduation project.

### 5.2 Fine-Tuning Strategy: LoRA (Low-Rank Adaptation)

We use LoRA to avoid retraining all 3B parameters:

    Base Model (3B params, FROZEN)
        |
        +---> LoRA Adapter (r=16, ~4M trainable params)
                |
                +---> Merged Model (for inference)

**LoRA Configuration**:

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| `r` (rank) | 16 | Good balance for domain adaptation |
| `lora_alpha` | 32 | Standard 2x multiplier |
| `lora_dropout` | 0.05 | Light regularization |
| `target_modules` | `q_proj, k_proj, v_proj, o_proj` | Standard attention modules |
| `bias` | `none` | Simpler, less overfitting risk |

### 5.3 Why NOT Mamba?

The original `AI_IMPLEMENTATION_PLAN.md` proposed a Mamba (SSM) model for high-frequency fuzzing. After analysis:

- **Mamba** excels at long-sequence generation (thousands of tokens of repetitive probes).
- **Our use case** requires short, precise payloads (10-50 tokens) with strong reasoning.
- **Practical constraint**: Mamba models on HuggingFace are limited and less mature for instruction-following tasks.

**Decision**: Use a Transformer-based LLM with LoRA for the Actioner. If future work requires high-frequency fuzzing (generating 1000+ probe variations), Mamba can be added as a separate "Fuzzer Module" downstream.

---

## 6. Training Methodology

### 6.1 Phase 1: Data Collection and Cleaning (Week 1)

**Target**: 3,000+ training examples

| Source | Count | Script |
|--------|-------|--------|
| Synthetic Generation | 1,200 | `gen_red_actioner_data.py` |
| Tool Capture (sqlmap/XSStrike) | 750 | Manual + `capture_tool_output.py` |
| Public Vuln Databases | 600 | Manual curation |
| Data Augmentation | 450 | `augment_dataset.py` |

**Quality Gates**:
- Every example must pass a JSON schema validator.
- Every `command` field must be syntactically valid (checked by `shlex.split()`).
- No duplicate `(target_url, payload)` pairs.
- At least 30% of examples must use non-DVWA hostnames.

### 6.2 Phase 2: Supervised Fine-Tuning (SFT) (Week 2)

**Training Configuration**:

```python
training_args = {
    "num_train_epochs": 3,
    "per_device_train_batch_size": 4,
    "gradient_accumulation_steps": 4,  # Effective batch size = 16
    "learning_rate": 2e-4,
    "lr_scheduler_type": "cosine",
    "warmup_ratio": 0.05,
    "weight_decay": 0.01,
    "max_seq_length": 1024,
    "logging_steps": 10,
    "save_steps": 100,
    "eval_steps": 50,
    "fp16": True,  # Mixed precision for VRAM savings
}
```

**Prompt Template** (applied during tokenization):

    SYSTEM: You are HackOps Red Actioner, a cybersecurity expert that generates
    precise exploit payloads based on observable evidence. You NEVER guess — you
    only act on confirmed signals. You output your reasoning first, then the
    concrete command.

    USER: {instruction}
    Context: {context_json}

    ASSISTANT: Reasoning: {reasoning}
    Command: {response_json}

### 6.3 Phase 3: Validation and Iteration (Week 3)

**Validation Split**: 80% train / 10% validation / 10% test (held-out)

**Key Metrics During Training**:
| Metric | Target | Description |
|--------|--------|-------------|
| **Cross-Entropy Loss** | < 0.5 | How well the model predicts the next token |
| **Perplexity** | < 10 | How "confused" the model is (lower = better) |
| **Token Accuracy** | > 90% | Percentage of correctly predicted tokens |
| **Gradient Norm** | Stable | No explosions or vanishing gradients |

**Overfitting Detection**:
- If val loss increases while train loss decreases for 3+ checkpoints → Stop early.
- If model starts outputting DVWA-specific strings on non-DVWA test inputs → Data augmentation is insufficient.

---

## 7. Integration with the RL+PPO Brain

This section explains exactly how the trained LLM Actioner connects to our two existing RL models.

### 7.1 The Two RL Brain Variants

We have two trained RL models, each with different strengths:

| Model | File | Architecture | Strength |
|-------|------|-------------|----------|
| **Vanilla PPO** | `red_agent_final.zip` | Standard MLP Policy | Fast, reactive decisions. Best for single-step exploits where the optimal action is clear from the current observation. |
| **Recurrent PPO (LSTM)** | `red_agent_lstm_final.zip` | LSTM-based Policy | Remembers past actions across the episode. Better at multi-step attack chains (e.g., "Fuzz first, then exploit the specific signal found"). |

### 7.2 Which Brain to Use When?

The LLM Actioner does NOT choose the Brain — the **HackOps Orchestrator** (`AIOrchestrator` in `ai_integration.py`) selects the Brain based on the difficulty level:

| Difficulty | Brain Selection | Reasoning |
|------------|----------------|-----------|
| **Easy** | Vanilla PPO | Simple, direct attacks. No need for memory. |
| **Medium** | Vanilla PPO | Balanced approach. Standard attack patterns. |
| **Hard** | Recurrent PPO (LSTM) | The LSTM's memory enables multi-step evasion chains: fuzz silently → identify signal → craft precise exploit → avoid WAF. |

### 7.3 The Bridge Protocol (Brain -> LLM)

When the RL Brain selects an action, the bridge translates it into a **Task Packet** for the LLM:

**Step 1: Brain outputs action index**

The Brain's action space (defined in `DVWAFlatWrapper`) maps indices to `DVWASmartExploitAction` objects. Example: action index `42` maps to `SmartExploit /search.php (SQLi)`.

**Step 2: ActionMapper builds Task Packet**

The current `_map_smart_exploit()` method in `action_mapper.py` will be replaced:

```python
# BEFORE (cheating — random.choice from static list):
payload = random.choice(self.payloads.get(attack_type, ["' OR 1=1 --"]))

# AFTER (LLM generates based on context):
task_packet = {
    "strategic_objective": f"EXPLOIT_{attack_type.upper()}",
    "target_url": f"http://target{location}",
    "target_parameter": self._infer_parameter(location),
    "observable_context": self._gather_page_context(location),
    "evasion_level": self._get_evasion_level()
}
llm_response = self.llm_actioner.generate(task_packet)
payload = llm_response["raw_payload"]
```

**Step 3: LLM generates payload**

The LLM receives the Task Packet, reasons about the observable context, and outputs a concrete payload.

**Step 4: Atomic Worker executes**

The payload is sent to the DVWA Controller for execution, and the result (success/failure) feeds back to the Brain as a reward signal.

### 7.4 The Context Gathering System

For the LLM to work on real targets (not just DVWA), we need a **Context Gatherer** that collects observable information about a target page:

```python
class PageContextGatherer:
    """Gathers observable context from a target page for the LLM"""

    def gather(self, target_url: str) -> dict:
        """
        Makes a real HTTP request and extracts:
        1. Form HTML (input fields, action URLs, methods)
        2. Server headers (Server, X-Powered-By, etc.)
        3. Error responses (inject a single quote and observe)
        4. Reflection tests (inject a marker string and check for echo)
        """
        return {
            "form_html": self._extract_forms(target_url),
            "server_headers": self._get_headers(target_url),
            "error_on_single_quote": self._probe_sqli(target_url),
            "reflection_test": self._probe_xss(target_url),
            "fuzz_signal": self._classify_signal(...)
        }
```

This is what makes the system **real-world capable**: the LLM never relies on internal knowledge of DVWA — it uses the same observable signals available against any web application.

### 7.5 The Brain Does NOT Need Retraining

> **Critical Point**: The LLM Actioner slot replaces `random.choice()` in the ActionMapper. The Brain's action space does NOT change. Therefore, neither PPO model (`red_agent_final.zip` nor `red_agent_lstm_final.zip`) needs to be retrained.

The Brain already learned: "When Fuzz reveals SQLi signal on /search.php -> use SmartExploit /search.php (SQLi)". That strategic decision is correct regardless of whether the payload is `' OR 1=1--` (from a static list) or `' UNION SELECT NULL,username,password FROM users WHERE '1'='1` (from the LLM).

---

## 8. Explainability & Trust (xAI) Strategy

A common flaw in AI-driven cybersecurity tools is the "black box" problem: the AI generates a payload, but the operator has no idea *why*. For a professional tool, the model must be **explainable**. We achieve xAI through four built-in mechanisms:

### 8.1 Chain-of-Thought (CoT) Reasoning Generation
Instead of generating a payload directly from the context, the model is trained to output a `reasoning` block *first*. This forces the LLM to explicitly state the logical steps it took. 
* **Opaque**: "Here is the SQLi payload: `' OR 1=1--`"
* **Explainable (Our approach)**: "The page has a login form. Fuzzing produced a MySQL syntax error when a single quote was sent to the 'username' parameter. This indicates early quote termination. I will craft a tautology payload to bypass the WHERE clause."

### 8.2 Exact Context Citation
We prevent hallucinations by forcing the model to cite the exact observable evidence.
In the training data, the reasoning chain explicitly references keys from the `observable_context` (e.g., "Because the server_headers contained 'PHP/7.4'..."). If the model generates a payload but provides a reasoning chain that references non-existent evidence, the orchestrator can flag it as a hallucination.

### 8.3 Confidence Calibration & Logprobs
The JSON format requires the model to output a self-assessed `"confidence"` score (e.g., 0.85). 
* During deployment, we extract the actual **log-probabilities (logprobs)** of the payload tokens.
* If the generated confidence score does not align with the actual token logprobs (e.g., the model claims 0.99 confidence but the token probabilities are very low), the system recognizes the model is wildly guessing (uncertainty quantification) and rejects the generation.

### 8.4 Deterministic Semantic Parsing
By enforcing the output into strict JSON categories (`attack_class`, `encoding`, `tool`), the operator doesn't have to manually parse a paragraph of text to understand the payload's intent. The intent is explicitly categorized and can be displayed in a UI dashboard, showing exactly what evasion mechanisms the agent applied.

---

## 9. Evaluation and Validation

### 9.1 Automated Evaluation Suite

We evaluate the LLM on three axes:

#### Axis 1: Syntax Validity (Is the output valid?)

| Test | Method | Target |
|------|--------|--------|
| JSON Schema | Validate output against response schema | 100% pass rate |
| Command Syntax | Parse with `shlex.split()` | >95% valid |
| Encoding Correctness | Verify URL/HTML encoding | >90% correct |

#### Axis 2: Semantic Accuracy (Is the output correct?)

| Test | Method | Target |
|------|--------|--------|
| Attack Class Match | Does the payload match the requested vulnerability type? | >85% accuracy |
| Parameter Targeting | Does the payload target the correct parameter? | >90% accuracy |
| Backend Compatibility | Is the SQL syntax correct for the indicated DB? | >80% accuracy |

#### Axis 3: Generalization (Does it work outside DVWA?)

| Test | Method | Target |
|------|--------|--------|
| Non-DVWA Hostnames | Test with completely new URLs | >80% valid payloads |
| Unseen Parameter Names | Test with novel parameter names | >85% valid payloads |
| Cross-DB Payloads | Test MySQL model on PostgreSQL context | >70% valid payloads |

### 8.2 Live Integration Test

After LLM training, we run a **full end-to-end test**:

1. Start a fresh DVWA Docker environment.
2. Load the RL Brain (`red_agent_final.zip`).
3. Connect the LLM Actioner (replacing the static ActionMapper).
4. Run 50 episodes and measure:
   - **Exploit Success Rate (ESR)**: Successful exploits / Total attempts
   - **Mean Time to Compromise (MTTC)**: Average steps to first successful exploit
   - **Payload Diversity**: Number of unique payloads generated (should be >> 4, which is our current static catalog)
   - **Syntax Error Rate**: Invalid payloads / Total generated

### 8.3 Baseline Comparison

| Metric | Static Catalog (Current) | LLM Actioner (Target) |
|--------|--------------------------|----------------------|
| Unique Payloads | 4 per vuln type | 50+ per vuln type |
| Generalization | DVWA only | Any PHP/MySQL/Apache target |
| Reasoning | None | Chain-of-Thought |
| Adaptation to WAF | None | WAF-bypass variations |
| Exploit Success Rate | ~70% (hardcoded) | >60% (with reasoning) |

> Note: The LLM ESR may initially be lower than the static catalog because the static catalog is "pre-verified" against DVWA. The LLM's strength is **generalization** — it will work on targets the static catalog has never seen.

---

## 10. Deployment Architecture

### 10.1 Inference Pipeline

```
GameSession.ai_step()
    |
    v
AIOrchestrator.step(agent_type='red')
    |
    v
RL Brain: model.predict(observation) --> action_index
    |
    v
ActionMapper._map_smart_exploit(action)
    |
    v
LLMActioner.generate(task_packet)   <-- NEW: Replaces random.choice()
    |
    |  1. Build prompt from task_packet
    |  2. Run inference (model.generate())
    |  3. Parse structured JSON response
    |  4. Validate syntax
    |  5. Return payload
    |
    v
DVWAController.execute_action(payload)
    |
    v
HTTP Request -> DVWA -> HTTP Response -> Reward
```

### 9.2 Model Loading Strategy

```python
class LLMActioner:
    def __init__(self, model_path="models/red_actioner_lora"):
        from transformers import AutoModelForCausalLM, AutoTokenizer
        from peft import PeftModel

        # Load base + LoRA adapter
        self.tokenizer = AutoTokenizer.from_pretrained("Qwen/Qwen2.5-3B-Instruct")
        base_model = AutoModelForCausalLM.from_pretrained(
            "Qwen/Qwen2.5-3B-Instruct",
            torch_dtype=torch.float16,
            device_map="auto"
        )
        self.model = PeftModel.from_pretrained(base_model, model_path)
        self.model.eval()

    def generate(self, task_packet: dict) -> dict:
        prompt = self._build_prompt(task_packet)
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)
        outputs = self.model.generate(**inputs, max_new_tokens=256, temperature=0.3)
        response_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        return self._parse_response(response_text)
```

### 9.3 Fallback Strategy

If the LLM fails (syntax error, timeout, OOM), the system falls back gracefully:

    1. LLM generates payload -----> SUCCESS? Use it.
                                      |
                                      NO (parse error / timeout)
                                      |
                                      v
    2. Static catalog fallback -----> Use random.choice() as today.
                                      |
                                      v
    3. Log the failure for retraining data collection.

---

## 11. File Deliverables

### 11.1 Scripts to Create

| File | Purpose |
|------|---------|
| `api/gen_red_actioner_data.py` | Synthetic data generator with randomization |
| `api/augment_dataset.py` | Data augmentation (host/param/encoding shuffling) |
| `api/train_llm.py` | Main LoRA fine-tuning script (SFT with HuggingFace `trl`) |
| `api/LLM_Actioner_Training.ipynb` | Jupyter notebook for visual training monitoring |
| `api/llm_actioner.py` | Inference wrapper class (loads model, generates payloads) |
| `api/validate_actioner.py` | Automated evaluation suite (syntax + semantic + generalization) |

### 10.2 Model Artifacts

| File | Description |
|------|-------------|
| `models/red_actioner_lora/` | LoRA adapter weights (small, ~50MB) |
| `models/red_actioner_merged/` | Merged full model (for deployment without base model download) |
| `api/data/red_actioner_dataset.jsonl` | Final curated training dataset |
| `api/data/red_actioner_eval.jsonl` | Held-out evaluation dataset |

### 10.3 Dependencies to Install

```
transformers>=4.40.0
peft>=0.10.0
trl>=0.8.0
bitsandbytes>=0.43.0  (for 4-bit quantization support)
datasets>=2.19.0
accelerate>=0.29.0
```

---

## Appendix A: Comparison with Current System

| Aspect | Current (`ActionMapper`) | LLM Actioner (Proposed) |
|--------|--------------------------|------------------------|
| Payload Source | `random.choice()` from 4 hardcoded strings | Generated by fine-tuned LLM based on context |
| Reasoning | None | Chain-of-Thought before payload |
| Generalization | DVWA-only | Any web application |
| WAF Handling | None | Evasion-level-aware encoding |
| Learning | Static | Can improve with more training data |
| Latency | Instant (<1ms) | ~200-500ms per generation |
| VRAM | 0 | ~4GB (quantized inference) |

## Appendix B: Risk Analysis

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| LLM generates invalid syntax | Medium | Low | Fallback to static catalog + syntax validator |
| LLM memorizes DVWA strings | High | High | Data augmentation with >30% non-DVWA targets |
| VRAM insufficient for training | Low | High | Use 4-bit quantization + gradient checkpointing |
| Model too slow for real-time game | Medium | Medium | Quantize to INT8, cache common payloads |
| Training data quality too low | Medium | High | Manual review of 10% sample before training |

## Appendix C: Timeline

| Week | Milestone | Deliverable |
|------|-----------|-------------|
| **Week 1** | Data generation + cleaning | `red_actioner_dataset.jsonl` (3000+ examples) |
| **Week 2** | LoRA fine-tuning | `models/red_actioner_lora/` + training curves |
| **Week 3** | Integration + evaluation | LLM connected to ActionMapper, evaluation report |
| **Week 4** | Polish + thesis documentation | Final benchmarks, comparison plots |
