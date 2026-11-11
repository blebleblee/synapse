# Operational Verification Labs: Core

## Objective & Environment Setup

### Objective
The primary objective of this lab is to provide hands-on experience in implementing, tuning, and verifying a core AI/LLM (Large Language Model) system. This lab will guide you through the process of building a complete pipeline, from model implementation to stress testing and failure mitigation. By the end of this lab, you will have a solid understanding of how to operationalize AI/LLM systems in a robust and efficient manner.

### Environment Setup
Ensure you have a Python 3.11+ environment set up on your machine. You will need to install the following packages:

- PyTorch
- HuggingFace Transformers
- NumPy
- Scikit-learn
- Ollama (or another LLM framework of your choice)
- Polars (for data manipulation)

You can install these packages using pip:

```bash
pip install torch transformers numpy scikit-learn ollama polars
```

Additionally, you will need to configure any necessary API keys or tokens for accessing external services or models. For example, if you are using HuggingFace, you will need to set up an API token:

```bash
export HUGGINGFACE_API_TOKEN='your_huggingface_api_token'
```

## Exercise 1: Hands-On Implementation & Pipeline Execution

In this exercise, we will implement a simple AI pipeline using a pre-trained LLM from HuggingFace. We will fine-tune the model on a small dataset and then use it to generate text.

### Complete, Runnable Python Script

```python
import torch
from transformers import GPT2LMHeadModel, GPT2Tokenizer, Trainer, TrainingArguments
from datasets import load_dataset

# Load a pre-trained GPT-2 model and tokenizer
model_name = 'gpt2'
model = GPT2LMHeadModel.from_pretrained(model_name)
tokenizer = GPT2Tokenizer.from_pretrained(model_name)

# Load a small dataset for fine-tuning
dataset = load_dataset('wikitext', 'wikitext-2-raw-v1', split='train[:5%]')

# Tokenize the dataset
def tokenize_function(examples):
    return tokenizer(examples['text'], padding='max_length', truncation=True)

tokenized_datasets = dataset.map(tokenize_function, batched=True)

# Define training arguments
training_args = TrainingArguments(
    output_dir='./results',
    evaluation_strategy='epoch',
    learning_rate=2e-5,
    per_device_train_batch_size=4,
    per_device_eval_batch_size=4,
    num_train_epochs=3,
    weight_decay=0.01,
)

# Define the Trainer
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=tokenized_datasets,
    eval_dataset=tokenized_datasets,
)

# Train the model
trainer.train()

# Generate text using the fine-tuned model
input_text = "Once upon a time"
input_ids = tokenizer.encode(input_text, return_tensors='pt')
output = model.generate(input_ids, max_length=50, num_return_sequences=1)

# Decode and print the generated text
generated_text = tokenizer.decode(output[0], skip_special_tokens=True)
print(generated_text)
```

## Exercise 2: Hyperparameter Tuning & Empirical Benchmarking

In this exercise, we will perform hyperparameter tuning and benchmark the model's performance in terms of accuracy, latency, and token costs.

### Real Benchmarking Code

```python
import time
import numpy as np
from sklearn.metrics import accuracy_score

# Function to measure latency
def measure_latency(model, tokenizer, input_text, num_runs=10):
    latencies = []
    for _ in range(num_runs):
        start_time = time.time()
        input_ids = tokenizer.encode(input_text, return_tensors='pt')
        _ = model.generate(input_ids, max_length=50, num_return_sequences=1)
        end_time = time.time()
        latencies.append(end_time - start_time)
    return np.mean(latencies), np.std(latencies)

# Function to measure token cost
def measure_token_cost(model, tokenizer, input_text):
    input_ids = tokenizer.encode(input_text, return_tensors='pt')
    output = model.generate(input_ids, max_length=50, num_return_sequences=1)
    return len(output[0])

# Benchmark the model
input_text = "Once upon a time"
mean_latency, std_latency = measure_latency(model, tokenizer, input_text)
token_cost = measure_token_cost(model, tokenizer, input_text)

print(f"Mean Latency: {mean_latency:.4f} seconds")
print(f"Latency Std Dev: {std_latency:.4f} seconds")
print(f"Token Cost: {token_cost} tokens")
```

## Exercise 3: Stress Testing, Edge Cases & Failure Mitigation

In this exercise, we will test the model under various stress conditions and implement guardrails to handle edge cases and failures.

### Reproducing Failure Modes, Testing Edge Cases, and Implementing Guardrails

```python
# Function to handle edge cases
def handle_edge_cases(input_text):
    if not input_text:
        raise ValueError("Input text cannot be empty")
    if len(input_text) > 1024:
        raise ValueError("Input text is too long")
    return input_text

# Stress test the model with edge cases
try:
    edge_case_text = ""
    handle_edge_cases(edge_case_text)
    input_ids = tokenizer.encode(edge_case_text, return_tensors='pt')
    _ = model.generate(input_ids, max_length=50, num_return_sequences=1)
except ValueError as e:
    print(f"Edge Case Handling: {e}")

try:
    edge_case_text = "a" * 2048
    handle_edge_cases(edge_case_text)
    input_ids = tokenizer.encode(edge_case_text, return_tensors='pt')
    _ = model.generate(input_ids, max_length=50, num_return_sequences=1)
except ValueError as e:
    print(f"Edge Case Handling: {e}")

# Implement guardrails for token cost
def generate_text_with_guardrails(model, tokenizer, input_text, max_token_cost=100):
    input_text = handle_edge_cases(input_text)
    input_ids = tokenizer.encode(input_text, return_tensors='pt')
    output = model.generate(input_ids, max_length=50, num_return_sequences=1)
    token_cost = len(output[0])
    if token_cost > max_token_cost:
        raise ValueError("Token cost exceeds maximum allowed")
    return tokenizer.decode(output[0], skip_special_tokens=True)

# Test guardrails
try:
    input_text = "Once upon a time in a land far, far away"
    generated_text = generate_text_with_guardrails(model, tokenizer, input_text)
    print(generated_text)
except ValueError as e:
    print(f"Guardrail Handling: {e}")
```

## Verification Checklist & Quick Reference Cheat Sheet

### Essential Python Methods, Parameters, and Verification Flags

| Method/Parameter | Description |
|------------------|-------------|
| `load_dataset`   | Loads a dataset from the HuggingFace datasets library. |
| `map`            | Applies a function to all elements of a dataset. |
| `encode`         | Encodes text into token IDs. |
| `generate`       | Generates text from token IDs. |
| `decode`         | Decodes token IDs into text. |
| `TrainingArguments` | Defines training arguments for the Trainer. |
| `Trainer`        | Manages the training loop. |
| `measure_latency` | Measures the average and standard deviation of latency. |
| `measure_token_cost` | Measures the number of tokens used in the generated text. |
| `handle_edge_cases` | Handles edge cases such as empty or too long input text. |
| `generate_text_with_guardrails` | Generates text with guardrails to handle token cost. |

### Verification Flags

- `evaluation_strategy`: Specifies when to evaluate the model during training.
- `learning_rate`: Specifies the learning rate for the optimizer.
- `per_device_train_batch_size`: Specifies the batch size for training.
- `per_device_eval_batch_size`: Specifies the batch size for evaluation.
- `num_train_epochs`: Specifies the number of training epochs.
- `weight_decay`: Specifies the weight decay for the optimizer.

By following this lab guide, you will have a comprehensive understanding of how to implement, tune, and verify AI/LLM systems in a robust and efficient manner.
