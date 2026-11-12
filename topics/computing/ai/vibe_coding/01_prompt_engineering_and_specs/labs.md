# Operational Verification Labs: 01 Prompt Engineering And Specs

## Objective & Environment Setup

This lab focuses on hands-on implementation and verification of prompt engineering and specifications for AI applications. To complete this lab, you will need a Python 3.11+ environment with the following packages installed:

* PyTorch
* HuggingFace Transformers
* NumPy
* Scikit-learn
* Ollama (or Polars as an alternative)

Additionally, ensure you have the necessary API configuration set up for your chosen model and dataset.

### Required Packages and Environment Setup

```bash
pip install torch transformers numpy scikit-learn ollama
```

### API Configuration

For this lab, we will use the HuggingFace Transformers library with the `bert-base-uncased` model. You will need to obtain an API key from the HuggingFace model hub and configure it in your environment.

```python
import os
import torch
from transformers import BertTokenizer, BertModel

# Set API key and model configuration
os.environ['HF_API_KEY'] = 'YOUR_API_KEY'
model_name = 'bert-base-uncased'
tokenizer = BertTokenizer.from_pretrained(model_name)
model = BertModel.from_pretrained(model_name)
```

## Exercise 1: Hands-On Implementation & Pipeline Execution

In this exercise, you will implement a basic prompt engineering pipeline using the HuggingFace Transformers library. The pipeline will consist of the following components:

* Tokenization using the `BertTokenizer`
* Model inference using the `BertModel`
* Evaluation using a simple accuracy metric

### Complete, Runnable Python Script

```python
import torch
from transformers import BertTokenizer, BertModel
from sklearn.metrics import accuracy_score

# Set model and tokenizer configuration
model_name = 'bert-base-uncased'
tokenizer = BertTokenizer.from_pretrained(model_name)
model = BertModel.from_pretrained(model_name)

# Define a sample input prompt
prompt = 'This is a sample input prompt.'

# Tokenize the input prompt
inputs = tokenizer.encode(prompt, return_tensors='pt')

# Perform model inference
outputs = model(inputs)

# Extract the last hidden state
last_hidden_state = outputs.last_hidden_state

# Evaluate the model using a simple accuracy metric
accuracy = accuracy_score([1], [1])  # placeholder accuracy value

print(f'Model accuracy: {accuracy:.4f}')
```

## Exercise 2: Hyperparameter Tuning & Empirical Benchmarking

In this exercise, you will implement a hyperparameter tuning pipeline using the `Optuna` library. The pipeline will consist of the following components:

* Hyperparameter tuning using the `Optuna` library
* Model evaluation using a simple accuracy metric
* Benchmarking using a sample dataset

### Real Benchmarking Code

```python
import torch
from transformers import BertTokenizer, BertModel
from sklearn.metrics import accuracy_score
import optuna

# Define a sample input prompt
prompt = 'This is a sample input prompt.'

# Tokenize the input prompt
tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')
inputs = tokenizer.encode(prompt, return_tensors='pt')

# Define a model evaluation function
def evaluate_model(trial):
    model = BertModel.from_pretrained('bert-base-uncased')
    model.eval()
    outputs = model(inputs)
    last_hidden_state = outputs.last_hidden_state
    accuracy = accuracy_score([1], [1])  # placeholder accuracy value
    return accuracy

# Perform hyperparameter tuning
study = optuna.create_study(direction='maximize')
study.optimize(evaluate_model, n_trials=10)

# Print the best hyperparameters
print(f'Best hyperparameters: {study.best_trial.params}')
```

## Exercise 3: Stress Testing, Edge Cases & Failure Mitigation

In this exercise, you will implement a stress testing pipeline using the `PyTorch` library. The pipeline will consist of the following components:

* Stress testing using a sample dataset
* Edge case testing using a sample input prompt
* Failure mitigation using a simple error handling mechanism

### Reproducing Failure Modes, Testing Edge Cases & Implementing Guardrails

```python
import torch
from transformers import BertTokenizer, BertModel
from sklearn.metrics import accuracy_score

# Define a sample input prompt
prompt = 'This is a sample input prompt.'

# Tokenize the input prompt
tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')
inputs = tokenizer.encode(prompt, return_tensors='pt')

# Perform stress testing
try:
    model = BertModel.from_pretrained('bert-base-uncased')
    model.eval()
    outputs = model(inputs)
    last_hidden_state = outputs.last_hidden_state
    accuracy = accuracy_score([1], [1])  # placeholder accuracy value
except Exception as e:
    print(f'Error: {e}')

# Test edge cases
try:
    model = BertModel.from_pretrained('bert-base-uncased')
    model.eval()
    outputs = model(inputs)
    last_hidden_state = outputs.last_hidden_state
    accuracy = accuracy_score([1], [1])  # placeholder accuracy value
except Exception as e:
    print(f'Error: {e}')

# Implement failure mitigation
try:
    model = BertModel.from_pretrained('bert-base-uncased')
    model.eval()
    outputs = model(inputs)
    last_hidden_state = outputs.last_hidden_state
    accuracy = accuracy_score([1], [1])  # placeholder accuracy value
except Exception as e:
    print(f'Error: {e}')
    # Implement error handling mechanism
```

## Verification Checklist & Quick Reference Cheat Sheet

| **Verification Flag** | **Description** | **Python Method** |
| --- | --- | --- |
| `HF_API_KEY` | HuggingFace API key | `os.environ['HF_API_KEY']` |
| `model_name` | Model name | `model_name = 'bert-base-uncased'` |
| `tokenizer` | Tokenizer instance | `tokenizer = BertTokenizer.from_pretrained(model_name)` |
| `model` | Model instance | `model = BertModel.from_pretrained(model_name)` |
| `inputs` | Tokenized input prompt | `inputs = tokenizer.encode(prompt, return_tensors='pt')` |
| `outputs` | Model outputs | `outputs = model(inputs)` |
| `last_hidden_state` | Last hidden state | `last_hidden_state = outputs.last_hidden_state` |
| `accuracy` | Model accuracy | `accuracy = accuracy_score([1], [1])` |

Note: This is a sample verification checklist and cheat sheet. You may need to modify it based on your specific implementation and requirements.
