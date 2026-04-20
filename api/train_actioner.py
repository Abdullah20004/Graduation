import os
import torch
import json
import pandas as pd
from datasets import load_dataset
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
    TrainingArguments,
    pipeline,
    logging,
)
from peft import LoraConfig, PeftModel, prepare_model_for_kbit_training, get_peft_model
from trl import SFTTrainer
from dotenv import load_dotenv

# ============================================================================
# CONFIGURATION
# ============================================================================
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

MODEL_NAME = "mickelliu/Self-RedTeam-Qwen2.5-7B-Instruct"
TRAIN_FILE = "api/data/red_actioner_sft_train.json"
EVAL_FILE = "api/data/red_actioner_sft_eval.json"
OUTPUT_DIR = "api/checkpoints/red_actioner_7b"
LOGGING_DIR = "api/logs/red_actioner"

# ============================================================================
# 1. LOAD DATASET
# ============================================================================
dataset = load_dataset("json", data_files={"train": TRAIN_FILE, "test": EVAL_FILE})

# ============================================================================
# 2. CONFIGURE 4-BIT QUANTIZATION (For 8GB VRAM)
# ============================================================================
compute_dtype = getattr(torch, "float16")

bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=compute_dtype,
    bnb_4bit_use_double_quant=True,
)

# ============================================================================
# 3. LOAD MODEL & TOKENIZER
# ============================================================================
token = os.environ.get("HUGGINGFACE_TOKEN")

tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, trust_remote_code=True, token=token)
tokenizer.pad_token = tokenizer.eos_token
tokenizer.padding_side = "right"

model = AutoModelForCausalLM.from_pretrained(
    MODEL_NAME,
    quantization_config=bnb_config,
    device_map="auto",
    token=token,
    trust_remote_code=True
)

# Prepare for k-bit training (Gradient Checkpointing + Layer Norm freezing)
model = prepare_model_for_kbit_training(model)

# ============================================================================
# 4. CONFIGURE LoRA (PEFT)
# ============================================================================
peft_config = LoraConfig(
    lora_alpha=32,
    lora_dropout=0.05,
    r=16,
    bias="none",
    task_type="CAUSAL_LM",
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]
)

model = get_peft_model(model, peft_config)

# ============================================================================
# 5. TRAINING ARGUMENTS
# ============================================================================
training_arguments = TrainingArguments(
    output_dir=OUTPUT_DIR,
    num_train_epochs=3,
    per_device_train_batch_size=1,        # Must be 1 for 8GB VRAM
    gradient_accumulation_steps=4,       # Effective batch size = 4
    optim="paged_adamw_32bit",
    save_steps=50,
    logging_steps=10,
    learning_rate=2e-4,
    weight_decay=0.001,
    fp16=True,                           # Use mixed precision
    max_grad_norm=0.3,                   # Gradient clipping
    warmup_ratio=0.03,
    group_by_length=True,
    lr_scheduler_type="cosine",
    report_to="tensorboard",
    logging_dir=LOGGING_DIR,
    evaluation_strategy="steps",
    eval_steps=50,
    push_to_hub=False,
)

from transformers import TrainerCallback

class PrinterCallback(TrainerCallback):
    def on_log(self, args, state, control, logs=None, **kwargs):
        if logs is not None and "loss" in logs:
            csv_path = os.path.join(LOGGING_DIR, "results.csv")
            os.makedirs(LOGGING_DIR, exist_ok=True)
            # Append log to CSV
            df = pd.DataFrame([logs])
            df["step"] = state.global_step
            header = not os.path.exists(csv_path)
            df.to_csv(csv_path, mode='a', header=header, index=False)

# ============================================================================
# 6. INITIALIZE TRAINER
# ============================================================================
trainer = SFTTrainer(
    model=model,
    train_dataset=dataset["train"],
    eval_dataset=dataset["test"],
    peft_config=peft_config,
    dataset_text_field="messages",
    max_seq_length=1024,
    tokenizer=tokenizer,
    args=training_arguments,
    packing=False,
    callbacks=[PrinterCallback()],
)

# ============================================================================
# 7. EXECUTE TRAINING
# ============================================================================
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="Check setup without training.")
    args = parser.parse_args()

    if args.dry_run:
        print("[+] Model loaded and quantized successfully.")
        print(f"[+] VRAM Allocated: {torch.cuda.memory_allocated() / 1024**3:.2f} GB")
        print("[+] Starting Dry Run - everything seems in order.")
    else:
        print("[*] Starting Fine-tuning...")
        trainer.train()
        
        # Save final model
        trainer.model.save_pretrained(os.path.join(OUTPUT_DIR, "final_lora"))
        tokenizer.save_pretrained(os.path.join(OUTPUT_DIR, "final_lora"))
        print(f"[+] Training complete. Model saved to {OUTPUT_DIR}/final_lora")
