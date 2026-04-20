#!/usr/bin/env python3
"""
E-Commerce DVWA Vulnerability Generator
Focuses on SQL Injection and XSS with realistic random page assignments
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

from dvwa_pages import DVWA_PAGES, get_compatible_pages

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
# VULNERABILITY CATALOG - SQLi and XSS ONLY
# ============================================================================

VULNERABILITY_CATALOG = {
    "sqli": [
        {
            "id": "sqli_login",
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
            "id": "sqli_search",
            "type": "sqli",
            "severity": "high",
            "description": "SQL Injection in search functionality",
            "required_features": ["user_input", "database_query", "display_results"],
            "cve": "CVE-2024-1002",
            "hint": "Search: ' UNION SELECT NULL,username,password FROM users--",
            "exploit_pattern": "' UNION SELECT 1,2,3--",
            "fix_command": "patch_sqli_{page}"
        },
        {
            "id": "sqli_detail",
            "type": "sqli",
            "severity": "high",
            "description": "SQL Injection in ID parameter",
            "required_features": ["user_input", "database_query"],
            "cve": "CVE-2024-1003",
            "hint": "ID: 1' AND 1=1--",
            "exploit_pattern": "' OR 1=1--",
            "fix_command": "patch_sqli_{page}"
        },
        {
            "id": "sqli_filter",
            "type": "sqli",
            "severity": "medium",
            "description": "SQL Injection in filtering/sorting",
            "required_features": ["user_input", "database_query", "display_results"],
            "cve": None,
            "hint": "Sort: name' OR '1'='1",
            "exploit_pattern": "' ORDER BY 1--",
            "fix_command": "patch_sqli_{page}"
        },
        {
            "id": "sqli_blind",
            "type": "sqli",
            "severity": "high",
            "description": "Blind SQL Injection (time-based)",
            "required_features": ["user_input", "database_query"],
            "cve": "CVE-2024-1004",
            "hint": "1' AND SLEEP(5)--",
            "exploit_pattern": "' AND SLEEP(5)--",
            "fix_command": "patch_sqli_{page}"
        },
        {
            "id": "sqli_admin",
            "type": "sqli",
            "severity": "critical",
            "description": "SQL Injection in admin panel",
            "required_features": ["user_input", "database_query", "privileged"],
            "cve": "CVE-2024-1005",
            "hint": "Admin bypass",
            "exploit_pattern": "admin' --",
            "fix_command": "patch_sqli_{page}"
        }
    ],
    
    "xss": [
        {
            "id": "xss_reflected_search",
            "type": "xss",
            "severity": "high",
            "description": "Reflected XSS in search results",
            "required_features": ["user_input", "display_results"],
            "cve": "CVE-2024-2001",
            "hint": "Search: <script>alert('XSS')</script>",
            "exploit_pattern": "<script>alert(1)</script>",
            "fix_command": "patch_xss_{page}"
        },
        {
            "id": "xss_stored_review",
            "type": "xss",
            "severity": "high",
            "description": "Stored XSS in user content",
            "required_features": ["user_input", "database_write", "display_results"],
            "cve": "CVE-2024-2002",
            "hint": "Review: <img src=x onerror='alert(1)'>",
            "exploit_pattern": "<img src=x onerror=alert(1)>",
            "fix_command": "patch_xss_{page}"
        },
        {
            "id": "xss_reflected_profile",
            "type": "xss",
            "severity": "medium",
            "description": "Reflected XSS in profile fields",
            "required_features": ["user_input", "display_user_data"],
            "cve": "CVE-2024-2003",
            "hint": "Name: <svg onload=alert(1)>",
            "exploit_pattern": "<svg onload=alert(1)>",
            "fix_command": "patch_xss_{page}"
        },
        {
            "id": "xss_reflected_error",
            "type": "xss",
            "severity": "medium",
            "description": "Reflected XSS in error messages",
            "required_features": ["user_input", "display_results"],
            "cve": None,
            "hint": "Invalid input echoed unsafely",
            "exploit_pattern": "<script>alert(document.cookie)</script>",
            "fix_command": "patch_xss_{page}"
        },
        {
            "id": "xss_dom",
            "type": "xss",
            "severity": "medium",
            "description": "DOM-based XSS in client-side",
            "required_features": ["client_side_processing"],
            "cve": "CVE-2024-2004",
            "hint": "#<img src=x onerror=alert(1)>",
            "exploit_pattern": "#<img src=x onerror=alert(1)>",
            "fix_command": "patch_xss_{page}"
        },
        {
            "id": "xss_stored_support",
            "type": "xss",
            "severity": "high",
            "description": "Stored XSS in support messages",
            "required_features": ["user_input", "display_results"],
            "cve": "CVE-2024-2005",
            "hint": "Message: <iframe src=javascript:alert(1)>",
            "exploit_pattern": "<iframe src=javascript:alert(1)>",
            "fix_command": "patch_xss_{page}"
        },
        {
            "id": "sqli_register",
            "type": "sqli",
            "severity": "high",
            "description": "SQL Injection in registration form",
            "required_features": ["user_input", "database_write"],
            "cve": "CVE-2024-1006",
            "hint": "Register: admin'--",
            "exploit_pattern": "admin'--",
            "fix_command": "patch_sqli_{page}"
        },
        {
            "id": "xss_reflected_login",
            "type": "xss",
            "severity": "low",
            "description": "Reflected XSS in login error",
            "required_features": ["user_input", "form_echo"],
            "cve": None,
            "hint": "?error=<script>alert(1)</script>",
            "exploit_pattern": "<script>alert(1)</script>",
            "fix_command": "patch_xss_{page}"
        },
        {
            "id": "xss_reflected_register",
            "type": "xss",
            "severity": "low",
            "description": "Reflected XSS in registration success message",
            "required_features": ["user_input", "form_echo"],
            "cve": None,
            "hint": "?msg=<script>alert(1)</script>",
            "exploit_pattern": "<script>alert(1)</script>",
            "fix_command": "patch_xss_{page}"
        }
    ]
}


def find_compatible_pages(vuln):
    """Find pages compatible with a vulnerability's required features"""
    required = vuln.get("required_features", [])
    compatible_pages = []
    
    for page_path, page_info in DVWA_PAGES.items():
        page_features = set(page_info.get("features", []))
        # Check if page has ALL required features
        if all(feature in page_features for feature in required):
            compatible_pages.append(page_path)
    
    return compatible_pages


def assign_vulnerabilities_to_pages(vulns, seed):
    """
    Randomly assign each vulnerability to a compatible page
    Returns list of vulnerabilities with assigned locations
    """
    random.seed(seed)
    
    assigned_vulns = []
    page_load = {}  # Track how many vulns per page
    
    for vuln in vulns:
        if not vuln.get("enabled"):
            assigned_vulns.append(vuln)
            continue
        
        # Find compatible pages
        compatible = find_compatible_pages(vuln)
        
        if not compatible:
            logging.warning(f"No compatible pages for {vuln['id']}, skipping")
            vuln["enabled"] = False
            assigned_vulns.append(vuln)
            continue
        
        # Prefer pages with fewer vulnerabilities (load balancing)
        page_weights = []
        for page in compatible:
            load = page_load.get(page, 0)
            # Weight inversely proportional to load
            weight = 1.0 / (load + 1)
            page_weights.append(weight)
        
        # Select random page
        selected_page = random.choice(compatible)
        
        # Assign page
        vuln["location"] = "/" + selected_page
        page_load[selected_page] = page_load.get(selected_page, 0) + 1
        
        # Update fix command with actual page
        page_name = selected_page.replace(".php", "")
        vuln["fix_command"] = vuln["fix_command"].replace("{page}", page_name)
        
        assigned_vulns.append(vuln)
    
    return assigned_vulns


def generate_vulnerabilities(min_vulns=3, max_vulns=6, seed=None):
    """
    Generate vulnerabilities with random page assignments
    Only SQLi and XSS
    """
    # Use argument, then environment variable, then timestamp
    if seed is None:
        val = os.getenv('VULN_SEED')
        if val:
            seed = val
        else:
            seed = int(datetime.now().timestamp())
            
    # Ensure seed is int/hashable
    try:
        seed = int(seed)
    except:
        pass # use string if not int
        
    random.seed(seed)
    logging.info(f"Using seed: {seed}")
    
    # Collect all vulnerabilities
    all_vulnerabilities = []
    all_vulnerabilities.extend(VULNERABILITY_CATALOG["sqli"])
    all_vulnerabilities.extend(VULNERABILITY_CATALOG["xss"])
    
    # Set all to disabled initially
    for vuln in all_vulnerabilities:
        vuln["enabled"] = False
    
    # Randomly select how many to enable
    num_vulns = random.randint(min_vulns, min(max_vulns, len(all_vulnerabilities)))
    
    # Randomly enable vulnerabilities
    enabled_vulns = random.sample(all_vulnerabilities, num_vulns)
    for vuln in enabled_vulns:
        vuln["enabled"] = True
    
    # Assign to compatible pages
    all_vulnerabilities = assign_vulnerabilities_to_pages(all_vulnerabilities, seed)
    
    return all_vulnerabilities, seed


def save_vulnerability_config(vulns, seed, output_path=None):
    """Save vulnerability configuration to JSON file"""
    if output_path is None:
        # Priority: 1. Environment Variable, 2. Container standard path, 3. Relative host path
        env_path = os.environ.get('VULNS_JSON_PATH')
        container_path = '/var/www/html/config/vulns.json'
        
        if env_path:
            output_path = env_path
        elif os.path.exists(os.path.dirname(container_path)) and os.access(os.path.dirname(container_path), os.W_OK):
            output_path = container_path
        else:
            output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config', 'vulns.json')
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    config = {
        "seed": seed,
        "generated_at": datetime.now().isoformat(),
        "vulnerabilities": vulns,
        "summary": {
            "total": len(vulns),
            "enabled": len([v for v in vulns if v["enabled"]]),
            "by_severity": {},
            "by_type": {}
        }
    }
    
    # Count by severity and type
    for vuln in [v for v in vulns if v["enabled"]]:
        sev = vuln["severity"]
        vtype = vuln["type"]
        config["summary"]["by_severity"][sev] = config["summary"]["by_severity"].get(sev, 0) + 1
        config["summary"]["by_type"][vtype] = config["summary"]["by_type"].get(vtype, 0) + 1
    
    with open(output_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    logging.info(f"Saved vulnerability configuration to {output_path}")
    return config


def log_vulnerability_summary(config):
    """Log a summary of enabled vulnerabilities"""
    enabled = [v for v in config["vulnerabilities"] if v["enabled"]]
    
    logging.info("=" * 60)
    logging.info("E-COMMERCE VULNERABILITY SUMMARY (SQLi & XSS)")
    logging.info("=" * 60)
    logging.info(f"Seed: {config['seed']}")
    logging.info(f"Total Enabled: {len(enabled)} / {len(config['vulnerabilities'])}")
    logging.info("")
    
    logging.info("By Severity:")
    for severity, count in config["summary"]["by_severity"].items():
        logging.info(f"  {severity.upper()}: {count}")
    
    logging.info("")
    logging.info("By Type:")
    for vuln_type, count in config["summary"]["by_type"].items():
        logging.info(f"  {vuln_type}: {count}")
    
    logging.info("")
    logging.info("Enabled Vulnerabilities:")
    for vuln in enabled:
        cve_info = f" ({vuln['cve']})" if vuln.get('cve') else ""
        logging.info(f"  [{vuln['severity'].upper()}] {vuln['id']}: {vuln['description']}{cve_info}")
        logging.info(f"    Location: {vuln['location']}")
        logging.info(f"    Fix: {vuln['fix_command']}")
    
    logging.info("=" * 60)


def main():
    """Main execution function"""
    try:
        logging.info("Starting E-Commerce vulnerability generation (SQLi & XSS only)...")
        
        # Generate vulnerabilities with random page assignments
        vulns, seed = generate_vulnerabilities(min_vulns=3, max_vulns=6)
        
        # Save configuration
        config = save_vulnerability_config(vulns, seed)
        
        # Log summary
        log_vulnerability_summary(config)
        
        logging.info("Vulnerability generation completed successfully!")
        
    except Exception as e:
        logging.error(f"Error generating vulnerabilities: {str(e)}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
