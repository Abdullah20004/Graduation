import json
import random
import os

# Configuration: We only need enough info for an LLM to "flesh out" the scenario
# Narrowed scope for deep focus: SQLi and XSS only
VULN_CLASSES = ["sql_injection", "xss"]
HOSTS = ["hackops.corp.internal", "shop.acme.io", "api.sec-prod.net", "billing.gateway.com", "myportal.net"]
BACKENDS = ["MySQL", "PostgreSQL", "MSSQL", "MariaDB", "SQLite"]

PARAM_MAP = {
    "sql_injection": ["id", "user_id", "uid", "product_id", "category", "username", "token"],
    "xss": ["q", "s", "search", "query", "term", "comment", "review", "name", "feedback"],
    "lfi": ["file", "path", "doc", "page", "resource", "template", "view"],
    "rce": ["cmd", "exec", "command", "run", "ping", "ip", "host"]
}

def generate_seeds(num_seeds=10):
    seeds = []
    for _ in range(num_seeds):
        vuln_class = random.choice(VULN_CLASSES)
        method = random.choice(["GET", "POST"])
        evasion = random.choice(["none", "basic", "waf_bypass"])
        
        seed = {
            "vuln_class": vuln_class,
            "target_url": f"http://{random.choice(HOSTS)}/{vuln_class}/{random.randint(100,999)}",
            "target_parameter": random.choice(PARAM_MAP[vuln_class]),
            "http_method": method,
            "evasion_level": evasion,
            "backend_tech": random.choice(BACKENDS) if vuln_class == "sql_injection" else "N/A"
        }
        seeds.append(seed)
    return seeds

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Generate minimal vulnerability seeds.")
    parser.add_argument("--num", type=int, default=10, help="Number of seeds to generate.")
    args = parser.parse_args()

    output_path = os.path.join("data", "red_actioner_seeds.jsonl")
    os.makedirs("data", exist_ok=True)
    seeds = generate_seeds(args.num)
    with open(output_path, "w") as f:
        for seed in seeds:
            f.write(json.dumps(seed) + "\n")
    print(f"Generated {len(seeds)} seeds in {output_path}")
