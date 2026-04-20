import json
import random
import os

def format_entry(entry):
    """
    Formats a single dataset entry into the HackOps Red Actioner chat format.
    """
    # System message: Clear instructions on the <thought>/<action> requirement
    system_msg = (
        "You are HackOps Red Actioner. You provide tactical security solutions.\n"
        "For every task, you MUST first analyze the scenario inside <thought> tags.\n"
        "You MUST then conclude with a precise exploit payload inside <action> tags.\n"
        "Never stop after the thinking process."
    )
    
    # User message: The Task Packet
    context = entry["context"]
    user_query = (
        f"Generate an exploit payload.\n\n"
        f"Target URL: {context['target_url']}\n"
        f"Target Parameter: {context['target_parameter']}\n"
        f"HTTP Method: {context['http_method']}\n"
        f"Observable Context: {json.dumps(context['observable_context'])}\n"
        f"Evasion Level: {context['evasion_level']}\n"
        f"Backend Hint: {context['backend_hint']}"
    )

    # Assistant message: Structured Thinking + Action
    assistant_content = (
        f"<thought>\n{entry['reasoning']}\n</thought>\n"
        f"<action>\n{json.dumps(entry['response'], ensure_ascii=False)}\n</action>"
    )

    return {
        "messages": [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_query},
            {"role": "assistant", "content": assistant_content}
        ]
    }

def prepare_data(input_file, output_prefix, eval_split=0.1):
    if not os.path.exists(input_file):
        print(f"Error: {input_file} not found.")
        return

    with open(input_file, "r", encoding="utf-8") as f:
        lines = f.readlines()
    
    data = [json.loads(line) for line in lines if line.strip()]
    random.shuffle(data)

    # Format all entries
    formatted_data = [format_entry(e) for e in data]

    # Split
    split_idx = int(len(formatted_data) * (1 - eval_split))
    train_set = formatted_data[:split_idx]
    eval_set = formatted_data[split_idx:]

    # Save as JSON (HuggingFace datasets format)
    with open(f"{output_prefix}_train.json", "w", encoding="utf-8") as f:
        json.dump(train_set, f, indent=2, ensure_ascii=False)
    with open(f"{output_prefix}_eval.json", "w", encoding="utf-8") as f:
        json.dump(eval_set, f, indent=2, ensure_ascii=False)

    print(f"Prepared {len(train_set)} training samples and {len(eval_set)} evaluation samples.")
    print(f"Files saved: {output_prefix}_train.json, {output_prefix}_eval.json")

if __name__ == "__main__":
    input_path = "api/data/red_actioner_distilled_cleaned.jsonl"
    output_prefix = "api/data/red_actioner_sft"
    prepare_data(input_path, output_prefix)
