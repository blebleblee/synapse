# Operational Verification Labs: 03 Parameter Efficient Fine Tuning LoRA

## Objective & Environment Setup

### Objective
The objective of this lab is to gain hands-on experience with Parameter Efficient Fine-Tuning using Low-Rank Adaptation (LoRA) for Large Language Models (LLMs). We will implement a complete pipeline that includes model fine-tuning, hyperparameter tuning, empirical benchmarking, and stress testing. This lab will equip you with the skills to efficiently adapt pre-trained LLMs to specific tasks while minimizing computational overhead.

### Environment Setup
Ensure you have a Python 3.11+ environment with the following packages installed:
- PyTorch
- HuggingFace Transformers
- NumPy
- Scikit-learn
- Ollama (optional, for model hosting and inference)
- Polars (optional, for data manipulation)

You can set up your environment using the following commands:

```bash
# Create a virtual environment
python3.11 -m venv lora-env
source lora-env/bin/activate

# Install required packages
pip install torch transformers numpy scikit-learn ollama polars
```

## Exercise 1: Hands-On Implementation & Pipeline Execution

In this exercise, we will implement the core prompt/model/algorithm for LoRA fine-tuning. We will use the HuggingFace Transformers library to load a pre-trained model and apply LoRA to fine-tune it on a specific task.

### Complete, Runnable Python Script

```python
import torch
from torch.utils.data import DataLoader, Dataset
from transformers import AutoModelForCausalLM, AutoTokenizer, get_linear_schedule_with_warmup, AdamW
from peft import LoraConfig, get_peft_model, TaskType

# Define a simple dataset class
class SimpleTextDataset(Dataset):
    def __init__(self, texts, tokenizer, max_length=512):
        self.texts = texts
        self.tokenizer = tokenizer
        self.max_length = max_length

    def __len__(self):
        return len(self.texts)

    def __getitem__(self, idx):
        text = self.texts[idx]
        encoding = self.tokenizer(
            text,
            return_tensors="pt",
            padding="max_length",
            truncation=True,
            max_length=self.max_length
        )
        return {
            "input_ids": encoding["input_ids"].squeeze(),
            "attention_mask": encoding["attention_mask"].squeeze(),
            "labels": encoding["input_ids"].squeeze()
        }

# Load pre-trained model and tokenizer
model_name = "gpt2"
model = AutoModelForCausalLM.from_pretrained(model_name)
tokenizer = AutoTokenizer.from_pretrained(model_name)

# Define LoRA configuration
lora_config = LoraConfig(
    task_type=TaskType.CAUSAL_LM,
    r=8,
    lora_alpha=32,
    lora_dropout=0.1,
    target_modules=["q_proj", "v_proj"]
)

# Apply LoRA to the model
model = get_peft_model(model, lora_config)

# Prepare dataset
texts = ["Example text 1", "Example text 2", "Example text 3"]
dataset = SimpleTextDataset(texts, tokenizer)
dataloader = DataLoader(dataset, batch_size=2, shuffle=True)

# Define optimizer and scheduler
optimizer = AdamW(model.parameters(), lr=5e-5)
num_epochs = 3
num_training_steps = num_epochs * len(dataloader)
lr_scheduler = get_linear_schedule_with_warmup(optimizer, num_warmup_steps=0, num_training_steps=num_training_steps)

# Training loop
model.train()
for epoch in range(num_epochs):
    for batch in dataloader:
        optimizer.zero_grad()
        outputs = model(input_ids=batch["input_ids"], attention_mask=batch["attention_mask"], labels=batch["labels"])
        loss = outputs.loss
        loss.backward()
        optimizer.step()
        lr_scheduler.step()
        print(f"Epoch {epoch + 1}, Loss: {loss.item()}")

# Save the fine-tuned model
model.save_pretrained("fine-tuned-lora-model")
tokenizer.save_pretrained("fine-tuned-lora-model")
```

## Exercise 2: Hyperparameter Tuning & Empirical Benchmarking

In this exercise, we will perform hyperparameter tuning and benchmark the fine-tuned model for accuracy, latency, and token costs.

### Benchmarking Code

```python
import time
import numpy as np
from sklearn.metrics import accuracy_score
from transformers import pipeline

# Load the fine-tuned model
model_path = "fine-tuned-lora-model"
model = AutoModelForCausalLM.from_pretrained(model_path)
tokenizer = AutoTokenizer.from_pretrained(model_path)

# Define a simple evaluation function
def evaluate_model(model, tokenizer, texts, expected_outputs):
    model.eval()
    predictions = []
    latencies = []

    for text, expected in zip(texts, expected_outputs):
        start_time = time.time()
        inputs = tokenizer(text, return_tensors="pt")
        outputs = model.generate(**inputs, max_length=50)
        end_time = time.time()

        prediction = tokenizer.decode(outputs[0], skip_special_tokens=True)
        predictions.append(prediction)
        latencies.append(end_time - start_time)

    accuracy = accuracy_score(expected_outputs, predictions)
    avg_latency = np.mean(latencies)
    return accuracy, avg_latency

# Prepare evaluation data
texts = ["Example text 1", "Example text 2", "Example text 3"]
expected_outputs = ["Expected output 1", "Expected output 2", "Expected output 3"]

# Evaluate the model
accuracy, avg_latency = evaluate_model(model, tokenizer, texts, expected_outputs)
print(f"Accuracy: {accuracy}, Average Latency: {avg_latency} seconds")
```

## Exercise 3: Stress Testing, Edge Cases & Failure Mitigation

In this exercise, we will test the model under various stress conditions and edge cases, and implement guardrails or error handling.

### Stress Testing and Edge Cases

```python
# Define stress test cases
stress_texts = [
    "A very long text that should test the model's ability to handle long inputs and generate coherent outputs.",
    "A short text with special characters: @#$%^&*() to test the model's robustness.",
    "A text with a mix of languages: English, Spanish, French to test multilingual capabilities."
]

# Define expected outputs for stress tests
stress_expected_outputs = [
    "Expected output for long text",
    "Expected output for special characters",
    "Expected output for multilingual text"
]

# Evaluate stress test cases
stress_accuracy, stress_avg_latency = evaluate_model(model, tokenizer, stress_texts, stress_expected_outputs)
print(f"Stress Test Accuracy: {stress_accuracy}, Stress Test Average Latency: {stress_avg_latency} seconds")
```

### Implementing Guardrails or Error Handling

```python
# Define a function to handle errors during inference
def safe_generate(model, tokenizer, text, max_length=50):
    try:
        inputs = tokenizer(text, return_tensors="pt")
        outputs = model.generate(**inputs, max_length=max_length)
        prediction = tokenizer.decode(outputs[0], skip_special_tokens=True)
        return prediction
    except Exception as e:
        print(f"Error during inference: {e}")
        return None

# Test the safe_generate function with a valid and invalid input
valid_text = "A valid input text"
invalid_text = "A very long text that exceeds the model's maximum input length" * 100

valid_prediction = safe_generate(model, tokenizer, valid_text)
invalid_prediction = safe_generate(model, tokenizer, invalid_text)

print(f"Valid Prediction: {valid_prediction}")
print(f"Invalid Prediction: {invalid_prediction}")
```

## Verification Checklist & Quick Reference Cheat Sheet

### Essential Python Methods and Parameters

| Method/Parameter | Description |
|------------------|-------------|
| `LoraConfig`     | Configuration for LoRA adaptation. |
| `get_peft_model` | Applies LoRA to the model. |
| `AutoModelForCausalLM` | Loads a pre-trained causal language model. |
| `AutoTokenizer`  | Loads a tokenizer for the model. |
| `AdamW`          | Optimizer for training the model. |
| `get_linear_schedule_with_warmup` | Learning rate scheduler. |
| `DataLoader`     | Loads data in batches for training. |
| `evaluate_model` | Evaluates the model's accuracy and latency. |
| `safe_generate`  | Safely generates text with error handling. |

### Verification Flags

| Flag/Parameter | Description |
|----------------|-------------|
| `r`            | Rank of the low-rank matrices. |
| `lora_alpha`   | Scaling factor for the low-rank matrices. |
| `lora_dropout` | Dropout rate for the low-rank matrices. |
| `target_modules` | Modules to apply LoRA to. |
| `max_length`   | Maximum length of generated text. |
| `num_epochs`   | Number of training epochs. |
| `batch_size`   | Batch size for training. |

By completing this lab, you will have a solid understanding of how to implement, fine-tune, and evaluate parameter-efficient models using LoRA. This knowledge will be invaluable for adapting LLMs to specific tasks in a resource-efficient manner.
