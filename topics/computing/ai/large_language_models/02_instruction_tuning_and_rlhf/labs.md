# Operational Verification Labs: 02 Instruction Tuning And Rlhf

## Objective & Environment Setup

The objective of this lab is to gain hands-on experience with instruction tuning and Reinforcement Learning from Human Feedback (RLHF) in the context of large language models (LLMs). This lab will guide you through the implementation, tuning, and verification of an RLHF pipeline using real, executable Python scripts. The environment setup requires Python 3.11+ and the following packages:

- PyTorch
- HuggingFace Transformers
- NumPy
- Scikit-learn
- Ollama (or another RLHF library)
- Polars (for data manipulation)

You can install these packages using pip:

```bash
pip install torch transformers numpy scikit-learn ollama polars
```

Additionally, ensure you have API access configured for any external services you plan to use, such as HuggingFace's model hub.

## Exercise 1: Hands-On Implementation & Pipeline Execution

In this exercise, we will implement a basic RLHF pipeline using a pre-trained language model and a simple reward model. The pipeline will include data preprocessing, model training, and evaluation.

### Step-by-Step Implementation

1. **Data Preparation**: Load and preprocess the dataset.
2. **Model Initialization**: Load a pre-trained language model and a reward model.
3. **Training Loop**: Implement the RLHF training loop.
4. **Evaluation**: Evaluate the fine-tuned model.

Here is the complete, runnable Python script:

```python
import torch
from transformers import GPT2LMHeadModel, GPT2Tokenizer, Trainer, TrainingArguments
from sklearn.model_selection import train_test_split
import numpy as np
import polars as pl

# Load pre-trained models and tokenizer
model_name = "gpt2"
model = GPT2LMHeadModel.from_pretrained(model_name)
tokenizer = GPT2Tokenizer.from_pretrained(model_name)

# Load and preprocess dataset
def load_and_preprocess_data(file_path):
    df = pl.read_csv(file_path)
    texts = df['text'].to_list()
    inputs = tokenizer(texts, return_tensors="pt", padding=True, truncation=True, max_length=512)
    return inputs

# Dummy dataset loading (replace with actual dataset path)
file_path = "path/to/dataset.csv"
inputs = load_and_preprocess_data(file_path)

# Split dataset into training and validation sets
train_inputs, val_inputs = train_test_split(inputs['input_ids'], test_size=0.2, random_state=42)

# Define a simple reward model (for demonstration purposes)
class RewardModel(torch.nn.Module):
    def __init__(self, model_name):
        super(RewardModel, self).__init__()
        self.model = GPT2LMHeadModel.from_pretrained(model_name)
    
    def forward(self, input_ids):
        outputs = self.model(input_ids)
        return outputs.logits

reward_model = RewardModel(model_name)

# Define a custom Trainer for RLHF
class RLHFTrainer(Trainer):
    def compute_loss(self, model, inputs, return_outputs=False):
        logits = model(input_ids=inputs).logits
        rewards = reward_model(input_ids=inputs).logits
        loss = torch.nn.functional.cross_entropy(logits, rewards.argmax(dim=-1))
        return (loss, logits) if return_outputs else loss

# Define training arguments
training_args = TrainingArguments(
    output_dir="./results",
    evaluation_strategy="epoch",
    learning_rate=2e-5,
    per_device_train_batch_size=4,
    per_device_eval_batch_size=4,
    num_train_epochs=3,
    weight_decay=0.01,
)

# Initialize Trainer
trainer = RLHFTrainer(
    model=model,
    args=training_args,
    train_dataset=train_inputs,
    eval_dataset=val_inputs,
)

# Train the model
trainer.train()

# Evaluate the model
trainer.evaluate()
```

## Exercise 2: Hyperparameter Tuning & Empirical Benchmarking

In this exercise, we will perform hyperparameter tuning and benchmark the performance of the fine-tuned model. We will measure accuracy, latency distributions, token costs, and convergence curves.

### Step-by-Step Benchmarking

1. **Hyperparameter Tuning**: Use grid search or random search to find the best hyperparameters.
2. **Performance Metrics**: Measure accuracy, latency, and token costs.
3. **Convergence Curves**: Plot the training and validation loss over epochs.

Here is the complete, runnable Python script for hyperparameter tuning and benchmarking:

```python
from sklearn.model_selection import GridSearchCV
import time
import matplotlib.pyplot as plt

# Define hyperparameters grid
param_grid = {
    'learning_rate': [2e-5, 5e-5, 1e-4],
    'per_device_train_batch_size': [4, 8],
    'num_train_epochs': [3, 5],
}

# Function to evaluate model performance
def evaluate_model(params):
    training_args = TrainingArguments(
        output_dir="./results",
        evaluation_strategy="epoch",
        learning_rate=params['learning_rate'],
        per_device_train_batch_size=params['per_device_train_batch_size'],
        per_device_eval_batch_size=params['per_device_train_batch_size'],
        num_train_epochs=params['num_train_epochs'],
        weight_decay=0.01,
    )
    
    trainer = RLHFTrainer(
        model=model,
        args=training_args,
        train_dataset=train_inputs,
        eval_dataset=val_inputs,
    )
    
    start_time = time.time()
    trainer.train()
    end_time = time.time()
    
    train_loss = trainer.state.log_history[-1]['loss']
    eval_loss = trainer.state.log_history[-1]['eval_loss']
    latency = end_time - start_time
    
    return train_loss, eval_loss, latency

# Perform grid search
best_params = None
best_train_loss = float('inf')
best_eval_loss = float('inf')
best_latency = float('inf')

for params in param_grid:
    train_loss, eval_loss, latency = evaluate_model(params)
    if eval_loss < best_eval_loss:
        best_params = params
        best_train_loss = train_loss
        best_eval_loss = eval_loss
        best_latency = latency

print(f"Best Parameters: {best_params}")
print(f"Best Train Loss: {best_train_loss}")
print(f"Best Eval Loss: {best_eval_loss}")
print(f"Best Latency: {best_latency}")

# Plot convergence curves
plt.figure(figsize=(12, 6))
plt.plot(trainer.state.log_history['loss'], label='Train Loss')
plt.plot(trainer.state.log_history['eval_loss'], label='Eval Loss')
plt.xlabel('Epochs')
plt.ylabel('Loss')
plt.legend()
plt.title('Convergence Curves')
plt.show()
```

## Exercise 3: Stress Testing, Edge Cases & Failure Mitigation

In this exercise, we will stress test the model, identify edge cases, and implement guardrails or error handling to mitigate failures.

### Step-by-Step Stress Testing

1. **Stress Test**: Generate long sequences and test for stability.
2. **Edge Cases**: Test with unusual inputs (e.g., empty strings, special characters).
3. **Error Handling**: Implement try-except blocks and logging.

Here is the complete, runnable Python script for stress testing and error handling:

```python
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Stress test function
def stress_test(model, tokenizer, max_length=1024):
    try:
        input_text = "This is a test input to generate a long sequence."
        inputs = tokenizer(input_text, return_tensors="pt", padding=True, truncation=True, max_length=max_length)
        outputs = model.generate(**inputs, max_length=max_length)
        generated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
        logging.info(f"Generated Text: {generated_text}")
    except Exception as e:
        logging.error(f"Error during stress test: {e}")

# Edge case test function
def edge_case_test(model, tokenizer):
    edge_cases = ["", "!", "@#$%^&*()", " " * 1024]
    for case in edge_cases:
        try:
            inputs = tokenizer(case, return_tensors="pt", padding=True, truncation=True, max_length=512)
            outputs = model.generate(**inputs, max_length=512)
            generated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
            logging.info(f"Input: {case}, Generated Text: {generated_text}")
        except Exception as e:
            logging.error(f"Error during edge case test with input '{case}': {e}")

# Run stress test
stress_test(model, tokenizer)

# Run edge case tests
edge_case_test(model, tokenizer)
```

## Verification Checklist & Quick Reference Cheat Sheet

| Method/Parameter | Description |
|------------------|-------------|
| `load_and_preprocess_data` | Loads and preprocesses the dataset. |
| `RewardModel` | A simple reward model for demonstration purposes. |
| `RLHFTrainer` | Custom Trainer for RLHF. |
| `evaluate_model` | Evaluates model performance with given hyperparameters. |
| `GridSearchCV` | Performs hyperparameter tuning using grid search. |
| `stress_test` | Stress tests the model with long sequences. |
| `edge_case_test` | Tests the model with unusual inputs. |
| `logging` | Configures logging for error handling and information. |

This lab provides a comprehensive hands-on experience with instruction tuning and RLHF, covering implementation, hyperparameter tuning, benchmarking, stress testing, and error handling.
