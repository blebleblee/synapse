# Operational Verification Labs: 01 Tokenization And Pretraining Objectives

## Objective & Environment Setup

The primary objective of this lab is to gain hands-on experience with tokenization and pretraining of large language models (LLMs). We will implement a tokenization pipeline, pretrain a small LLM, and evaluate its performance. The lab requires a Python 3.11+ environment with the following packages installed:

- PyTorch
- HuggingFace Transformers
- NumPy
- Scikit-learn
- Ollama (optional for model deployment)
- Polars (optional for data manipulation)

To set up the environment, execute the following commands:

```bash
# Create a virtual environment
python3.11 -m venv llm-lab-env

# Activate the virtual environment
source llm-lab-env/bin/activate

# Install required packages
pip install torch transformers numpy scikit-learn ollama polars
```

## Exercise 1: Hands-On Implementation & Pipeline Execution

In this exercise, we will implement a tokenization pipeline and pretrain a small LLM using the HuggingFace Transformers library. We will use a simple dataset for demonstration purposes.

### Tokenization Pipeline

First, we will tokenize a sample text dataset using the `BytePairEncoding` tokenizer from HuggingFace.

```python
from transformers import AutoTokenizer
from datasets import load_dataset

# Load a sample dataset
dataset = load_dataset('wikitext', 'wikitext-2-raw-v1', split='train[:10%]')

# Initialize the tokenizer
tokenizer = AutoTokenizer.from_pretrained('gpt2')

# Tokenize the dataset
def tokenize_function(examples):
    return tokenizer(examples['text'], padding='max_length', truncation=True)

tokenized_datasets = dataset.map(tokenize_function, batched=True)

# Save the tokenizer
tokenizer.save_pretrained('./tokenizer')
```

### Pretraining the Model

Next, we will pretrain a small GPT-2 model using the tokenized dataset.

```python
from transformers import GPT2LMHeadModel, Trainer, TrainingArguments

# Load the pre-trained model
model = GPT2LMHeadModel.from_pretrained('gpt2')

# Define training arguments
training_args = TrainingArguments(
    output_dir='./results',
    overwrite_output_dir=True,
    num_train_epochs=1,
    per_device_train_batch_size=2,
    save_steps=10_000,
    save_total_limit=2,
    prediction_loss_only=True,
)

# Initialize the Trainer
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=tokenized_datasets,
)

# Train the model
trainer.train()
```

## Exercise 2: Hyperparameter Tuning & Empirical Benchmarking

In this exercise, we will perform hyperparameter tuning and benchmark the pre-trained model's performance in terms of accuracy, latency, and token costs.

### Hyperparameter Tuning

We will use the `Optuna` library for hyperparameter tuning. First, install Optuna:

```bash
pip install optuna
```

Then, implement the hyperparameter tuning pipeline:

```python
import optuna
from transformers import GPT2LMHeadModel, Trainer, TrainingArguments

def objective(trial):
    # Suggest hyperparameters
    learning_rate = trial.suggest_loguniform('learning_rate', 1e-5, 5e-5)
    per_device_train_batch_size = trial.suggest_categorical('per_device_train_batch_size', [2, 4, 8])
    
    # Define training arguments
    training_args = TrainingArguments(
        output_dir='./results',
        overwrite_output_dir=True,
        num_train_epochs=1,
        per_device_train_batch_size=per_device_train_batch_size,
        learning_rate=learning_rate,
        save_steps=10_000,
        save_total_limit=2,
        prediction_loss_only=True,
    )
    
    # Load the pre-trained model
    model = GPT2LMHeadModel.from_pretrained('gpt2')
    
    # Initialize the Trainer
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized_datasets,
    )
    
    # Train the model
    trainer.train()
    
    # Evaluate the model
    eval_results = trainer.evaluate()
    return eval_results['eval_loss']

# Run the hyperparameter tuning
study = optuna.create_study(direction='minimize')
study.optimize(objective, n_trials=5)
```

### Benchmarking

We will benchmark the model's performance using the `time` module to measure latency and `scikit-learn` for accuracy.

```python
import time
from sklearn.metrics import accuracy_score
import torch

# Load the tokenizer and model
tokenizer = AutoTokenizer.from_pretrained('./tokenizer')
model = GPT2LMHeadModel.from_pretrained('./results/checkpoint-10000')

# Prepare the input text
input_text = "This is a sample text for benchmarking."
inputs = tokenizer(input_text, return_tensors='pt')

# Measure latency
start_time = time.time()
with torch.no_grad():
    outputs = model(**inputs)
end_time = time.time()
latency = end_time - start_time

# Calculate accuracy (simplified example)
predicted_ids = torch.argmax(outputs.logits, dim=-1)
accuracy = accuracy_score(inputs['input_ids'].flatten(), predicted_ids.flatten())

print(f'Latency: {latency} seconds')
print(f'Accuracy: {accuracy}')
```

## Exercise 3: Stress Testing, Edge Cases & Failure Mitigation

In this exercise, we will test the model's robustness by simulating stress conditions and edge cases, and implementing guardrails to handle failures.

### Stress Testing

We will simulate stress testing by generating text with a large context length.

```python
# Generate text with a large context length
long_input_text = " ".join([input_text] * 100)
long_inputs = tokenizer(long_input_text, return_tensors='pt')

# Measure latency
start_time = time.time()
with torch.no_grad():
    long_outputs = model.generate(**long_inputs, max_length=500)
end_time = time.time()
long_latency = end_time - start_time

print(f'Long text latency: {long_latency} seconds')
```

### Edge Cases

We will test the model's behavior with edge cases such as empty input and special characters.

```python
# Test with empty input
empty_inputs = tokenizer("", return_tensors='pt')
with torch.no_grad():
    empty_outputs = model.generate(**empty_inputs, max_length=50)

print(f'Empty input output: {tokenizer.decode(empty_outputs[0])}')

# Test with special characters
special_char_inputs = tokenizer("!@#$%^&*()", return_tensors='pt')
with torch.no_grad():
    special_char_outputs = model.generate(**special_char_inputs, max_length=50)

print(f'Special characters output: {tokenizer.decode(special_char_outputs[0])}')
```

### Failure Mitigation

We will implement guardrails to handle potential failures, such as input validation and exception handling.

```python
def generate_text(model, tokenizer, input_text):
    try:
        # Validate input
        if not isinstance(input_text, str) or not input_text.strip():
            raise ValueError("Input text must be a non-empty string.")
        
        # Tokenize input
        inputs = tokenizer(input_text, return_tensors='pt')
        
        # Generate text
        with torch.no_grad():
            outputs = model.generate(**inputs, max_length=50)
        
        return tokenizer.decode(outputs[0])
    
    except Exception as e:
        print(f'Error generating text: {e}')
        return None

# Test guardrails
print(generate_text(model, tokenizer, ""))  # Should handle empty input
print(generate_text(model, tokenizer, "Valid input"))  # Should generate text
```

## Verification Checklist & Quick Reference Cheat Sheet

| Method/Parameter | Description |
|------------------|-------------|
| `AutoTokenizer.from_pretrained` | Loads a pre-trained tokenizer. |
| `GPT2LMHeadModel.from_pretrained` | Loads a pre-trained GPT-2 model. |
| `Trainer` | Manages the training loop. |
| `TrainingArguments` | Defines training arguments. |
| `optuna.create_study` | Creates an Optuna study for hyperparameter tuning. |
| `study.optimize` | Optimizes hyperparameters using the objective function. |
| `tokenizer.encode` | Encodes input text into token IDs. |
| `model.generate` | Generates text from token IDs. |
| `time.time` | Measures execution time. |
| `accuracy_score` | Calculates accuracy between true and predicted labels. |
| `torch.no_grad` | Disables gradient calculation for inference. |

This lab provides a comprehensive hands-on experience with tokenization and pretraining of LLMs, including hyperparameter tuning, benchmarking, stress testing, and failure mitigation.
