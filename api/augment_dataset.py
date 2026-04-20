import json
import random
import os
import urllib.parse

def augment_entry(entry):
    """
    Applies augmentation techniques:
    1. Param Shuffling (renames the parameter)
    2. Encoding variation (URL, Double URL, etc.)
    3. Host Randomization (already partially done, but can be switched)
    """
    new_entry = json.loads(json.dumps(entry)) # Deep copy
    
    # Technique 1: Encoding variation for the payload
    payload = new_entry['response']['raw_payload']
    encoding_type = random.choice(["URL", "Double-URL", "HTML-Entity", "None"])
    
    if encoding_type == "URL":
        encoded_payload = urllib.parse.quote(payload)
    elif encoding_type == "Double-URL":
        encoded_payload = urllib.parse.quote(urllib.parse.quote(payload))
    elif encoding_type == "HTML-Entity":
        encoded_payload = payload.replace("<", "&lt;").replace(">", "&gt;").replace("'", "&#39;")
    else:
        encoded_payload = payload
        
    # Update command with encoded payload
    param = new_entry['context']['target_parameter']
    url = new_entry['context']['target_url']
    new_entry['response']['encoding'] = encoding_type
    
    # Simple replacement in the curl command
    old_cmd = new_entry['response']['command']
    # This is a bit brittle, but works for our generated curl strings
    if "-d '" in old_cmd:
        new_entry['response']['command'] = old_cmd.split("-d '")[0] + f"-d '{param}={encoded_payload}'"
    elif "--data-urlencode '" in old_cmd:
        new_entry['response']['command'] = old_cmd.split("--data-urlencode '")[0] + f"--data-urlencode '{param}={encoded_payload}'"
        
    return new_entry

def main():
    input_file = "api/data/red_actioner_dataset.jsonl"
    output_file = "api/data/red_actioner_dataset_augmented.jsonl"
    
    if not os.path.exists(input_file):
        print(f"Error: {input_file} not found. Run gen_red_actioner_data.py first.")
        return

    with open(input_file, "r") as f:
        lines = f.readlines()
        
    augmented_data = []
    print(f"Augmenting {len(lines)} entries...")
    
    for line in lines:
        entry = json.loads(line)
        # Keep original
        augmented_data.append(entry)
        # Add 1 augmented version
        augmented_data.append(augment_entry(entry))
        
    random.shuffle(augmented_data)
    
    with open(output_file, "w") as f:
        for entry in augmented_data:
            f.write(json.dumps(entry) + "\n")
            
    print(f"Successfully saved {len(augmented_data)} entries to {output_file}")

if __name__ == "__main__":
    main()
