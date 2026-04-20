# Red Actioner: Re-Training & Fine-Tuning Guide

Follow these steps to update your fine-tuning notebook (`LLM_Actioner_FineTuning.ipynb`) after the dataset has been cleaned. These changes are designed to prevent the model from "memorizing" (overfitting) the data and to force it to complete the action phase.

## 1. Update Preparation Paths
In the cell where you call `prepare_data`, ensure it points to the new cleaned file:
```python
input_path = "api/data/red_actioner_distilled_cleaned.jsonl"
output_prefix = "api/data/red_actioner_sft"
```

## 2. Updated System Prompt
Replace the `system_msg` inside your preparation logic (or in the `prepare_training_data.py` file) with this more authoritative version:
```text
You are HackOps Red Actioner. You provide tactical security solutions. 
For every task, you MUST first analyze the scenario inside <thought> tags.
You MUST then conclude with a precise exploit payload inside <action> tags.
Never stop after the thinking process.
```

## 3. Calibrate Hyperparameters
In the **Training Arguments** cell, update the following values:

| Parameter | Recommended Value | Reasoning |
| :--- | :--- | :--- |
| `learning_rate` | `5e-5` | (Down from `2e-4`) This prevents the model from "shouting" and memorizing the few 80 samples. |
| `max_seq_length` | `2048` | (Up from `1024`) This ensures the model doesn't run out of "breath" and truncate the payload at the end. |
| `num_train_epochs` | `3` | Keep at 3, but the lower LR will make these 3 epochs much more meaningful for learning. |
| `per_device_train_batch_size` | `1` | Keep at 1 for VRAM stability. |
| `gradient_accumulation_steps` | `4` | Keep at 4. |

## 4. Execution Order
1. Run the **Preparation** cell to generate the new `.json` files.
2. Run the **Training** cell.
3. Monitor the `loss`. It should decrease more slowly and smoothly than before. 

> [!TIP]
> If the `loss` drops to 0.1 too quickly (within 10-20 steps), your Learning Rate is still too high for this small dataset.
