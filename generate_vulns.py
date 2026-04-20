#!/usr/bin/env python3
"""
HackOps Dynamic Vulnerability Generator
Randomizes vulnerabilities across all pages using feature-based selection.
Specifically targets login and signup to ensure realistic coverage.
"""
import random
import json
import os
import sys
import logging
from datetime import datetime

# Add api directory to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(current_dir, 'api'))

from dvwa_pages import DVWA_PAGES

# Setup logging
log_file = os.path.join(current_dir, 'logs', 'vulnerabilities.log')
os.makedirs(os.path.dirname(log_file), exist_ok=True)
logging.basicConfig(
    filename=log_file,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

console = logging.StreamHandler()
console.setLevel(logging.INFO)
logging.getLogger('').addHandler(console)

# ============================================================================
# VULNERABILITY CATALOG - COMPREHENSIVE
# ============================================================================

VULNERABILITY_CATALOG = {
    "sqli": [
        {
            "id": "sqli_auth",
            "type": "sqli",
            "severity": "critical",
            "description": "SQL Injection in authentication bypass",
            "required_features": ["user_input", "database_query", "authentication"],
            "cve": "CVE-2024-1001",
            "hint": "Username: admin' OR '1'='1",
            "exploit_pattern": "' OR '1'='1",
            "fix_command": "patch_sqli_{page}"
        },
        {
            "id": "sqli_generic",
            "type": "sqli",
            "severity": "high",
            "description": "SQL Injection in database query",
            "required_features": ["user_input", "database_query"],
            "cve": "CVE-2024-1002",
            "hint": "Check the ID or input parameter",
            "exploit_pattern": "' OR 1=1--",
            "fix_command": "patch_sqli_{page}"
        },
        {
            "id": "sqli_stored",
            "type": "sqli",
            "severity": "high",
            "description": "SQL Injection in record creation",
            "required_features": ["user_input", "database_write"],
            "cve": "CVE-2024-1003",
            "hint": "Injecting into INSERT/UPDATE fields",
            "exploit_pattern": "admin'--",
            "fix_command": "patch_sqli_{page}"
        }
    ],
    "xss": [
        {
            "id": "xss_reflected",
            "type": "xss",
            "severity": "high",
            "description": "Reflected XSS in page output",
            "required_features": ["user_input", "display_results"],
            "cve": "CVE-2024-2001",
            "hint": "Payload mirrored in response",
            "exploit_pattern": "<script>alert(1)</script>",
            "fix_command": "patch_xss_{page}"
        },
        {
            "id": "xss_echo",
            "type": "xss",
            "severity": "low",
            "description": "Reflected XSS in status message",
            "required_features": ["user_input", "form_echo"],
            "cve": None,
            "hint": "Check error or success messages",
            "exploit_pattern": "<script>alert('XSS')</script>",
            "fix_command": "patch_xss_{page}"
        },
        {
            "id": "xss_stored",
            "type": "xss",
            "severity": "high",
            "description": "Stored XSS in database records",
            "required_features": ["user_input", "database_write", "display_results"],
            "cve": "CVE-2024-2002",
            "hint": "Persistent payload in reviews or support",
            "exploit_pattern": "<img src=x onerror=alert(1)>",
            "fix_command": "patch_xss_{page}"
        }
    ],
    "rce": [
        {
            "id": "rce_upload",
            "type": "rce",
            "severity": "critical",
            "description": "RCE via unsafe file upload",
            "required_features": ["user_input", "payment_processing"],  # Repurposing for sensitive areas
            "cve": "CVE-2024-3001",
            "hint": "Upload a PHP shell",
            "exploit_pattern": "<?php system($_GET['cmd']); ?>",
            "fix_command": "patch_rce_{page}"
        }
    ],
    "idor": [
        {
            "id": "idor_generic",
            "type": "idor",
            "severity": "high",
            "description": "Insecure Direct Object Reference",
            "required_features": ["database_query", "display_user_data"],
            "cve": "CVE-2024-4001",
            "hint": "Scale the ID parameter",
            "exploit_pattern": "?id=5",
            "fix_command": "patch_idor_{page}"
        }
    ]
}

def find_compatible_pages(vuln):
    """Find pages compatible with a vulnerability's required features"""
    required = vuln.get("required_features", [])
    compatible_pages = []
    
    for page_path, page_info in DVWA_PAGES.items():
        page_features = set(page_info.get("features", []))
        if all(feature in page_features for feature in required):
            compatible_pages.append(page_path)
    
    return compatible_pages

def generate_vulnerabilities(min_vulns=4, max_vulns=8, seed=None):
    """Generate vulnerabilities with random but weighted page assignments"""
    if seed is None:
        seed = os.getenv('VULN_SEED') or int(datetime.now().timestamp())
    
    try:
        seed = int(seed)
    except:
        pass
        
    random.seed(seed)
    logging.info(f"Generating vulnerabilities with seed: {seed}")
    
    # Flatten catalog
    all_templates = []
    for vtype in VULNERABILITY_CATALOG:
        all_templates.extend(VULNERABILITY_CATALOG[vtype])
    
    # Reset
    for t in all_templates: t["enabled"] = False
    
    # Pick a random set to enable
    num_to_enable = random.randint(min_vulns, min(max_vulns, len(all_templates)))
    enabled_templates = random.sample(all_templates, num_to_enable)
    
    for t in enabled_templates: t["enabled"] = True
    
    # Assign pages
    assigned_vulns = []
    page_load = {}
    
    # Priority pages that MUST be generated for the shop to function
    CORE_PAGES = ["index.php", "products.php", "search.php", "product_detail.php", "cart.php", "orders.php", "login.php"]
    
    for vuln in all_templates:
        if not vuln["enabled"]:
            assigned_vulns.append(vuln)
            continue
            
        compatible = find_compatible_pages(vuln)
        if not compatible:
            logging.warning(f"No compatible pages for {vuln['id']}, skipping")
            vuln["enabled"] = False
            assigned_vulns.append(vuln)
            continue
            
        # Prioritize core pages if they haven't been assigned yet
        unassigned_core = [p for p in CORE_PAGES if p in compatible and p not in page_load]
        if unassigned_core:
            selected_page = random.choice(unassigned_core)
        else:
            selected_page = random.choice(compatible)
        
        vuln["location"] = "/" + selected_page
        page_load[selected_page] = page_load.get(selected_page, 0) + 1
        
        # Update fix command
        page_name = selected_page.replace(".php", "").replace(".html", "")
        vuln["fix_command"] = vuln.get("fix_command", "patch_{page}").replace("{page}", page_name)
        
        assigned_vulns.append(vuln)
        
    # Ensure remaining core pages are at least present as SQLi (our functional logic)
    for core_page in CORE_PAGES:
        if core_page not in page_load:
            # Add a nominal/generic SQLi to make it functional
            nominal_sqli = VULNERABILITY_CATALOG["sqli"][1].copy() # sqli_generic
            nominal_sqli["enabled"] = True
            nominal_sqli["location"] = "/" + core_page
            nominal_sqli["id"] = f"sqli_core_{core_page.replace('.php', '')}"
            page_name = core_page.replace(".php", "").replace(".html", "")
            nominal_sqli["fix_command"] = f"patch_sqli_{page_name}"
            assigned_vulns.append(nominal_sqli)
            page_load[core_page] = 1
            
    return assigned_vulns, seed

def save_config(vulns, seed, output_path=None):
    if output_path is None:
        # Priority: 1. Environment Variable, 2. Container standard path (if writable), 3. Relative host path
        env_path = os.environ.get('VULNS_JSON_PATH')
        container_path = '/var/www/html/config/vulns.json'
        
        if env_path:
            output_path = env_path
        elif os.path.exists(os.path.dirname(container_path)) and os.access(os.path.dirname(container_path), os.W_OK):
            output_path = container_path
        else:
            # Fallback for host-side execution
            output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config', 'vulns.json')
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    config = {
        "seed": seed,
        "generated_at": datetime.now().isoformat(),
        "vulnerabilities": vulns,
        "summary": {
            "total": len(vulns),
            "enabled": len([v for v in vulns if v["enabled"]]),
            "by_severity": {
                "critical": len([v for v in vulns if v["enabled"] and v["severity"] == "critical"]),
                "high": len([v for v in vulns if v["enabled"] and v["severity"] == "high"]),
                "medium": len([v for v in vulns if v["enabled"] and v["severity"] == "medium"]),
                "low": len([v for v in vulns if v["enabled"] and v["severity"] == "low"])
            },
            "by_type": {}
        }
    }
    
    for v in [v for v in vulns if v["enabled"]]:
        config["summary"]["by_type"][v["type"]] = config["summary"]["by_type"].get(v["type"], 0) + 1
        
    with open(output_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    logging.info(f"Vulnerabilities saved to {output_path}")
    return config

if __name__ == "__main__":
    vulns, seed = generate_vulnerabilities()
    config = save_config(vulns, seed)
    
    # Print summary to console
    print("\n" + "="*50)
    print(f"HACKOPS DYNAMIC VULN GENERATOR")
    print("="*50)
    print(f"Seed: {seed}")
    print(f"Enabled: {config['summary']['enabled']}")
    print("\nLocations:")
    for v in [v for v in vulns if v["enabled"]]:
        print(f"  [{v['severity'].upper()}] {v['type'].upper()} -> {v['location']}")
    print("="*50 + "\n")