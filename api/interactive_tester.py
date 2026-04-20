import torch
import os
import json
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from peft import PeftModel
from dotenv import load_dotenv

# ============================================================================
# CONFIGURATION
# ============================================================================
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))
TOKEN = os.environ.get("HUGGINGFACE_TOKEN")
MODEL_NAME = "mickelliu/Self-RedTeam-Qwen2.5-7B-Instruct"
CHECKPOINT_PATH = "api/checkpoints/red_actioner_7b/final_lora"

# ============================================================================
# INTERACTIVE INFERENCE
# ============================================================================
class ActionerTester:
    def __init__(self, is_tuned=True):
        print(f"[*] Loading Actioner (Tuned={is_tuned})...")
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_use_double_quant=True,
        )
        
        self.tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, token=TOKEN)
        base_model = AutoModelForCausalLM.from_pretrained(
            MODEL_NAME,
            quantization_config=bnb_config,
            device_map="auto",
            token=TOKEN
        )
        
        if is_tuned and os.path.exists(CHECKPOINT_PATH):
            print(f"[+] Applying LoRA Adapter from {CHECKPOINT_PATH}")
            self.model = PeftModel.from_pretrained(base_model, CHECKPOINT_PATH)
        else:
            print("[!] Using base model (No adapter found or requested).")
            self.model = base_model
            
        self.model.eval()

    def test_scenario(self, url, parameter, context_snippet, evasion="none"):
        system_msg = (
            "You are HackOps Red Actioner, a cybersecurity expert. "
            "You first think about the reasoning process in the mind and then provide the answer. "
            "The reasoning process and answer are enclosed within <think> </think> and <answer> </answer> tags."
        )
        
        user_query = (
            f"Generate an exploit payload.\n\n"
            f"Target URL: {url}\n"
            f"Target Parameter: {parameter}\n"
            f"HTTP Method: POST\n"
            f"Observable Context: {json.dumps({'fuzz_signal': context_snippet})}\n"
            f"Evasion Level: {evasion}\n"
            f"Backend Hint: MySQL"
        )
        
        messages = [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": f"User: {user_query}"}
        ]
        
        prompt = self.tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)
        
        print("\n" + "*"*60)
        print("GENERTING RESPONSE...")
        print("*"*60)
        
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs, 
                max_new_tokens=1024, 
                temperature=0.3,
                repetition_penalty=1.1
            )
        
        response = self.tokenizer.decode(outputs[0], skip_special_tokens=False)
        
        # Parse Response
        if "<think>" in response:
            think = response.split("<think>")[1].split("</think>")[0].strip()
            print(f"\n🧠 THOUGHT PROCESS:\n{think}")
            
        if "<answer>" in response:
            answer = response.split("<answer>")[1].split("</answer>")[0].strip()
            print(f"\n🎯 FINAL PAYLOAD:\n{answer}")
        else:
            print(f"\n[!] Raw Output:\n{response}")

if __name__ == "__main__":
    tester = ActionerTester(is_tuned=True)
    
    # Test Scenario
    tester.test_scenario(
        url="http://billing.internal/invoice.php",
        parameter="id",
        context_snippet="SQL_ERROR: You have an error in your SQL syntax near ''' at line 1",
        evasion="waf_bypass"
    )
