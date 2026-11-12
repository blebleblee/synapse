# Operational Verification Labs: 02 Agentic Workflows And Tools

## Objective & Environment Setup

This lab guides you through implementing and verifying agentic workflows using Python 3.11+ and popular AI libraries. Ensure you have the following packages installed:

- PyTorch
- HuggingFace Transformers
- NumPy
- Scikit-learn
- Ollama
- Polars

Configure your API keys for HuggingFace and other services as required.

## Exercise 1: Hands-On Implementation & Pipeline Execution

Implement the core prompt/model/algorithm for this topic using the following Python script:

```python
import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
from sklearn.preprocessing import LabelEncoder
import numpy as np

# Load pre-trained model and tokenizer
model_name = "bert-base-uncased"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSequenceClassification.from_pretrained(model_name, num_labels=2)

# Load dataset and preprocess
train_data, val_data = train_test_split(np.array([["example text", 0], ["another example", 1]]), test_size=0.2, random_state=42)
le = LabelEncoder()
train_labels = le.fit_transform(train_data[:, -1])
val_labels = le.transform(val_data[:, -1])

# Define pipeline
def pipeline(text):
    inputs = tokenizer.encode_plus(
        text,
        add_special_tokens=True,
        max_length=512,
        return_attention_mask=True,
        return_tensors="pt",
    )
    outputs = model(inputs["input_ids"], attention_mask=inputs["attention_mask"])
    logits = outputs.logits
    return torch.argmax(logits)

# Execute pipeline on validation set
val_preds = []
for text in val_data[:, 0]:
    val_preds.append(pipeline(text))
val_preds = torch.tensor(val_preds)

# Evaluate pipeline
accuracy = accuracy_score(val_labels, val_preds)
print(f"Validation Accuracy: {accuracy:.4f}")
```

Replace the example dataset with your actual data.

## Exercise 2: Hyperparameter Tuning & Empirical Benchmarking

Measure accuracy, latency distributions, token costs, or convergence curves using the following Python script:

```python
import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
from sklearn.preprocessing import LabelEncoder
import numpy as np
import time

# Load pre-trained model and tokenizer
model_name = "bert-base-uncased"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSequenceClassification.from_pretrained(model_name, num_labels=2)

# Load dataset and preprocess
train_data, val_data = train_test_split(np.array([["example text", 0], ["another example", 1]]), test_size=0.2, random_state=42)
le = LabelEncoder()
train_labels = le.fit_transform(train_data[:, -1])
val_labels = le.transform(val_data[:, -1])

# Define benchmarking function
def benchmark(text):
    inputs = tokenizer.encode_plus(
        text,
        add_special_tokens=True,
        max_length=512,
        return_attention_mask=True,
        return_tensors="pt",
    )
    start_time = time.time()
    outputs = model(inputs["input_ids"], attention_mask=inputs["attention_mask"])
    end_time = time.time()
    return torch.argmax(outputs.logits), end_time - start_time

# Run benchmarking on validation set
val_preds = []
latencies = []
for text in val_data[:, 0]:
    pred, latency = benchmark(text)
    val_preds.append(pred)
    latencies.append(latency)
val_preds = torch.tensor(val_preds)

# Evaluate benchmarking results
accuracy = accuracy_score(val_labels, val_preds)
print(f"Validation Accuracy: {accuracy:.4f}")
print(f"Average Latency: {np.mean(latencies):.4f} seconds")
```

Replace the example dataset with your actual data.

## Exercise 3: Stress Testing, Edge Cases & Failure Mitigation

Reproduce failure modes, test edge cases, and implement guardrails or error handling using the following Python script:

```python
import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
from sklearn.preprocessing import LabelEncoder
import numpy as np

# Load pre-trained model and tokenizer
model_name = "bert-base-uncased"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSequenceClassification.from_pretrained(model_name, num_labels=2)

# Load dataset and preprocess
train_data, val_data = train_test_split(np.array([["example text", 0], ["another example", 1]]), test_size=0.2, random_state=42)
le = LabelEncoder()
train_labels = le.fit_transform(train_data[:, -1])
val_labels = le.transform(val_data[:, -1])

# Define stress testing function
def stress_test(text):
    try:
        inputs = tokenizer.encode_plus(
            text,
            add_special_tokens=True,
            max_length=512,
            return_attention_mask=True,
            return_tensors="pt",
        )
        outputs = model(inputs["input_ids"], attention_mask=inputs["attention_mask"])
        return torch.argmax(outputs.logits)
    except Exception as e:
        print(f"Error processing text: {text}")
        return None

# Run stress testing on validation set
val_preds = []
for text in val_data[:, 0]:
    pred = stress_test(text)
    if pred is not None:
        val_preds.append(pred)
val_preds = torch.tensor(val_preds)

# Evaluate stress testing results
accuracy = accuracy_score(val_labels, val_preds)
print(f"Validation Accuracy: {accuracy:.4f}")
```

Replace the example dataset with your actual data.

## Verification Checklist & Quick Reference Cheat Sheet

| Python Method | Parameters | Verification Flags |
| --- | --- | --- |
| `torch.argmax` | `outputs.logits` | `--debug` |
| `tokenizer.encode_plus` | `text`, `add_special_tokens=True`, `max_length=512` | `--verbose` |
| `model(inputs["input_ids"], attention_mask=inputs["attention_mask"])` | `inputs["input_ids"]`, `attention_mask=inputs["attention_mask"]` | `--profile` |
| `accuracy_score` | `val_labels`, `val_preds` | `--eval` |

Ensure you replace the example dataset with your actual data and adjust the script as needed for your specific use case.
