import json
import os
import time
import argparse
import google.generativeai as genai
from typing import List, Dict
from dotenv import load_dotenv

# ============================================================================
# CONFIGURATION
# ============================================================================

# We load the prompt from the text file relative to this script
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROMPT_FILE = os.path.join(SCRIPT_DIR, "prompts", "teacher_prompt.txt")
DEFAULT_INPUT_FILE = os.path.join(SCRIPT_DIR, "data", "red_actioner_seeds.jsonl")
DEFAULT_OUTPUT_FILE = os.path.join(SCRIPT_DIR, "data", "red_actioner_distilled.jsonl")

# ============================================================================
# API SETUP & ROTATION
# ============================================================================

class KeyRotator:
    def __init__(self):
        load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))
        # Support both GEMINI_API_KEY (single) or GEMINI_API_KEYS (comma-separated list)
        keys_str = os.environ.get("GEMINI_API_KEYS") or os.environ.get("GEMINI_API_KEY")
        if not keys_str:
            raise ValueError("No API keys found in .env (Use GEMINI_API_KEY or GEMINI_API_KEYS)")
        
        self.keys = [k.strip() for k in keys_str.split(",") if k.strip()]
        self.current_index = 0
        self.model = self._configure_current()
        print(f"Loaded {len(self.keys)} API keys for rotation.")

    def _configure_current(self):
        key = self.keys[self.current_index]
        genai.configure(api_key=key)
        # Obfuscate key in output for safety
        display_key = f"{key[:5]}...{key[-5:]}"
        print(f"Switching to API Key {self.current_index + 1}: {display_key}")
        return genai.GenerativeModel("gemini-2.5-flash")

    def rotate(self):
        self.current_index = (self.current_index + 1) % len(self.keys)
        if self.current_index == 0:
            print("All keys exhausted once. Waiting 60 seconds to reset quota...")
            time.sleep(60)
        self.model = self._configure_current()

def distill_batch(rotator, seeds: List[Dict], teacher_prompt: str) -> List[Dict]:
    """Sends a batch of seeds to the Teacher LLM for expansion."""
    seeds_input = "\n".join([json.dumps(s) for s in seeds])
    full_prompt = f"{teacher_prompt}\n\n### SEEDS TO PROCESS\n{seeds_input}\n\n### OUTPUT"
    
    max_retries = len(rotator.keys) * 2
    for attempt in range(max_retries):
        try:
            response = rotator.model.generate_content(
                full_prompt,
                generation_config=genai.types.GenerationConfig(temperature=0.3)
            )
            response_text = response.text.strip()
            
            if response_text.startswith("```json"):
                response_text = response_text.replace("```json", "").replace("```", "").strip()
            
            try:
                results = json.loads(response_text)
                if isinstance(results, dict): results = [results]
            except json.JSONDecodeError:
                results = []
                for line in response_text.split("\n"):
                    if line.strip():
                        try: results.append(json.loads(line))
                        except: continue
            return results
        
        except Exception as e:
            error_str = str(e)
            if "429" in error_str or "quota" in error_str.lower() or "ResourceExhausted" in error_str:
                print(f"Rate limit reached on key {rotator.current_index + 1}. Rotating...")
                rotator.rotate()
                continue
            else:
                print(f"Error during distillation: {e}")
                return []
    return []

def main():
    parser = argparse.ArgumentParser(description="Distill red actioner seeds into high-fidelity training data.")
    parser.add_argument("--limit", type=int, default=10, help="Number of seeds to process.")
    parser.add_argument("--batch_size", type=int, default=5, help="Batch size for LLM processing.")
    args = parser.parse_args()

    if not os.path.exists(PROMPT_FILE):
        print(f"Error: {PROMPT_FILE} not found.")
        return
    with open(PROMPT_FILE, "r") as f:
        teacher_prompt = f.read()

    try:
        rotator = KeyRotator()
    except Exception as e:
        print(f"Setup Error: {e}")
        return

    if not os.path.exists(DEFAULT_INPUT_FILE):
        print(f"Error: {DEFAULT_INPUT_FILE} not found. Run gen_red_actioner_seeds.py first.")
        return
        
    seeds = []
    with open(DEFAULT_INPUT_FILE, "r") as f:
        for i, line in enumerate(f):
            if i >= args.limit: break
            seeds.append(json.loads(line))

    print(f"Distilling {len(seeds)} samples using {len(rotator.keys)} keys...")

    all_results = []
    for i in range(0, len(seeds), args.batch_size):
        batch = seeds[i : i + args.batch_size]
        print(f"Processing batch {i//args.batch_size + 1} of {(len(seeds) + args.batch_size - 1)//args.batch_size}...")
        results = distill_batch(rotator, batch, teacher_prompt)
        all_results.extend(results)
        time.sleep(1) # Graceful delay

    with open(DEFAULT_OUTPUT_FILE, "a") as f:
        for result in all_results:
            f.write(json.dumps(result) + "\n")

    print(f"Successfully distilled {len(all_results)} samples to {DEFAULT_OUTPUT_FILE}")

if __name__ == "__main__":
    main()
