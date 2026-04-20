import json
import torch
import os
import matplotlib.pyplot as plt
import pandas as pd
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from peft import PeftModel
from dotenv import load_dotenv

# ============================================================================
# CONFIGURATION
# ============================================================================
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))
TOKEN = os.environ.get("HUGGINGFACE_TOKEN")
MODEL_NAME = "mickelliu/Self-RedTeam-Qwen2.5-7B-Instruct"
TEST_DATA = "api/data/red_actioner_sft_eval.json"
CHECKPOINT_PATH = "api/checkpoints/red_actioner_7b/final_lora"

# ============================================================================
# 1. MODEL LOADER
# ============================================================================
def load_actioner(is_tuned=False):
    print(f"[*] Loading model (Tuned={is_tuned})...")
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.float16,
        bnb_4bit_use_double_quant=True,
    )
    
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, token=TOKEN)
    base_model = AutoModelForCausalLM.from_pretrained(
        MODEL_NAME,
        quantization_config=bnb_config,
        device_map="auto",
        token=TOKEN
    )
    
    if is_tuned:
        model = PeftModel.from_pretrained(base_model, CHECKPOINT_PATH)
        return model, tokenizer
    return base_model, tokenizer

# ============================================================================
# 2. EVALUATION LOGIC
# ============================================================================
def run_benchmark(model, tokenizer, num_samples=5):
    with open(TEST_DATA, "r") as f:
        eval_data = json.load(f)
    
    samples = eval_data[:num_samples]
    results = []

    print(f"[*] Running benchmark on {len(samples)} samples...")
    for entry in samples:
        # Construct prompt
        messages = entry["messages"][:-1] # Remove Assistant Answer
        prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        
        inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
        
        with torch.no_grad():
            outputs = model.generate(**inputs, max_new_tokens=512, temperature=0.1)
        
        response = tokenizer.decode(outputs[0], skip_special_tokens=False)
        
        # Simple extraction of think and answer
        think_match = ""
        answer_match = ""
        if "<think>" in response and "</think>" in response:
            think_match = response.split("<think>")[1].split("</think>")[0].strip()
        if "<answer>" in response and "</answer>" in response:
            answer_match = response.split("<answer>")[1].split("</answer>")[0].strip()
            
        results.append({
            "prompt": messages[-1]["content"],
            "expected": entry["messages"][-1]["content"],
            "generated_think": think_match,
            "generated_answer": answer_match
        })
        
    return results

# ============================================================================
# 3. PLOTTING LOGIC
# ============================================================================
def plot_training_results(log_dir="api/logs/red_actioner"):
    """
    Note: Requires a CSV export or logic to read tensorboard.
    For simplicity, assume training script saves 'metrics.csv'.
    """
    csv_path = os.path.join(log_dir, "results.csv")
    if not os.path.exists(csv_path):
        print(f"Error: {csv_path} not found. Run training first.")
        return
        
    df = pd.read_csv(csv_path)
    plt.figure(figsize=(10, 5))
    plt.plot(df['step'], df['loss'], label='Training Loss')
    plt.title('Fine-tuning Progress')
    plt.xlabel('Step')
    plt.ylabel('Loss')
    plt.legend()
    plt.grid(True)
    plt.savefig(os.path.join(log_dir, "loss_plot.png"))
    print(f"[+] Plot saved to {log_dir}/loss_plot.png")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["baseline", "tuned", "plot"], default="baseline")
    args = parser.parse_args()

    if args.mode == "plot":
        plot_training_results()
    else:
        model, tokenizer = load_actioner(is_tuned=(args.mode == "tuned"))
        results = run_benchmark(model, tokenizer)
        for r in results:
            print("\n" + "="*50)
            print(f"PROMPT: {r['prompt'][:100]}...")
            print(f"THINK: {r['generated_think'][:200]}...")
            print(f"ANSWER: {r['generated_answer']}")
