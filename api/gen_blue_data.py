import json
import random
import os

# Configuration: Simulation Parameters
# We use lists to ensure variety and generalization
VULNERABILITY_TYPES = [
    "SQL Injection", "XSS (Cross-Site Scripting)", "Remote Code Execution (RCE)", 
    "Path Traversal", "Insecure Deserialization", "Brute Force"
]

# Random filenames to prevent overfitting (Generalization Strategy)
TARGET_FILES = [
    "login.php", "index.php", "search.php", "upload_handler.py", 
    "api_v1_user.js", "admin_panel.html", "config.xml", "database_connect.php",
    "legacy_module.c", "payment_gateway.rb"
]

# Random contexts to simulate real game logs
CONTEXTS = [
    "Detected by passive scan.", "Critical alert from IDS.", 
    "User reported anomalous behavior.", "Routine audit finding.",
    "Failed exploit attempt logged."
]

def generate_patch_command(vuln, target):
    """
    The 'Logic Center': Maps a vulnerability to a specific shell command.
    THIS is the function we update if the Dev Team changes tools.
    """
    if vuln == "SQL Injection":
        # Example: Using sed to replace vulnerable mysql_query with protected one
        return f"sed -i 's/mysql_query/pdo_execute/g' {target}"
    elif vuln == "XSS (Cross-Site Scripting)":
        return f"sed -i 's/echo $_GET/echo htmlspecialchars($_GET)/g' {target}"
    elif vuln == "Brute Force":
        return f"iptables -A INPUT -p tcp --dport 80 -m recent --update --seconds 60 --hitcount 10 -j DROP"
    else:
        # Generic patcher tool for other vulns
        return f"run_security_patcher --vuln '{vuln}' --target {target} --severity high"

def generate_dataset(num_examples=100):
    dataset = []
    
    for _ in range(num_examples):
        vuln = random.choice(VULNERABILITY_TYPES)
        target = random.choice(TARGET_FILES)
        context_desc = random.choice(CONTEXTS)
        
        # 1. The Input (What the Brain/Log says)
        # We vary the phrasing slightly to make the model robust
        phrasings = [
            f"Action: Patch {vuln} found in {target}.",
            f"Fix the {vuln} vulnerability located at {target}.",
            f"Remediate {vuln} issue. Target file: {target}.",
            f"Security Alert: {vuln} detected in {target}. Apply fix."
        ]
        instruction = random.choice(phrasings)
        
        # 2. The Context (Background info)
        context = f"System Context: {context_desc} Environment: Production."
        
        # 3. The Output (The Command)
        response = generate_patch_command(vuln, target)
        
        entry = {
            "instruction": instruction,
            "context": context,
            "response": response
        }
        dataset.append(entry)
        
    return dataset

if __name__ == "__main__":
    # Ensure api directory exists (just in case)
    output_dir = "api/data"  # Keeping it in api folder for consistency with project structure
    os.makedirs(output_dir, exist_ok=True)
    
    file_path = os.path.join(output_dir, "blue_dataset_preview.jsonl")
    
    data = generate_dataset(1200) # Generate 1200 examples to meet Phase 2 goals
    
    print(f"Generating {len(data)} examples to {file_path}...")
    
    with open(file_path, "w", encoding='utf-8') as f:
        for entry in data:
            f.write(json.dumps(entry) + "\n")
            
    print("Done! Preview of first 3 entries:")
    print("-" * 50)
    for i in range(3):
        print(json.dumps(data[i], indent=2))
    print("-" * 50)
