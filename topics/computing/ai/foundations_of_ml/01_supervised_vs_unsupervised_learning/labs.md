# Operational Verification Labs: Supervised vs. Unsupervised Learning

## Objective & Environment Setup

This lab guides hands-on AI engineers and practitioners through the implementation and evaluation of supervised and unsupervised learning algorithms. To complete this lab, ensure you have a Python 3.11+ environment set up with the following packages installed:

- PyTorch
- HuggingFace Transformers
- NumPy
- Scikit-learn
- Polars

Additionally, configure your API settings according to your specific requirements.

## Exercise 1: Hands-On Implementation & Pipeline Execution

Implement a supervised learning algorithm (e.g., logistic regression) and an unsupervised learning algorithm (e.g., k-means clustering) using PyTorch and HuggingFace Transformers. The following Python script serves as a starting point:

```python
import torch
import torch.nn as nn
import torch.optim as optim
from transformers import AutoModelForSequenceClassification, AutoTokenizer
from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

# Load dataset
iris = load_iris()
X_train, X_test, y_train, y_test = train_test_split(iris.data, iris.target, test_size=0.2, random_state=42)

# Initialize model and optimizer
model = AutoModelForSequenceClassification.from_pretrained('distilbert-base-uncased')
tokenizer = AutoTokenizer.from_pretrained('distilbert-base-uncased')
criterion = nn.CrossEntropyLoss()
optimizer = optim.Adam(model.parameters(), lr=1e-5)

# Train supervised model
for epoch in range(5):
    model.train()
    optimizer.zero_grad()
    inputs = tokenizer(X_train, return_tensors='pt', padding=True)
    outputs = model(**inputs)
    loss = criterion(outputs.logits, torch.tensor(y_train))
    loss.backward()
    optimizer.step()

# Evaluate supervised model
model.eval()
with torch.no_grad():
    inputs = tokenizer(X_test, return_tensors='pt', padding=True)
    outputs = model(**inputs)
    predictions = torch.argmax(outputs.logits, dim=1)
    accuracy = accuracy_score(y_test, predictions)
    print(f'Supervised model accuracy: {accuracy:.4f}')

# Implement unsupervised model
from sklearn.cluster import KMeans
kmeans = KMeans(n_clusters=3)
kmeans.fit(X_train)
labels = kmeans.predict(X_test)

# Evaluate unsupervised model
accuracy = accuracy_score(y_test, labels)
print(f'Unsupervised model accuracy: {accuracy:.4f}')
```

## Exercise 2: Hyperparameter Tuning & Empirical Benchmarking

Measure the accuracy, latency distributions, token costs, or convergence curves of both supervised and unsupervised models. The following Python script provides a starting point for benchmarking:

```python
import time
import numpy as np

# Define benchmarking function
def benchmark(model, X_test, y_test):
    model.eval()
    with torch.no_grad():
        inputs = tokenizer(X_test, return_tensors='pt', padding=True)
        outputs = model(**inputs)
        predictions = torch.argmax(outputs.logits, dim=1)
        accuracy = accuracy_score(y_test, predictions)
        return accuracy

# Benchmark supervised model
supervised_accuracy = benchmark(model, X_test, y_test)
print(f'Supervised model accuracy: {supervised_accuracy:.4f}')

# Benchmark unsupervised model
unsupervised_accuracy = accuracy_score(y_test, labels)
print(f'Unsupervised model accuracy: {unsupervised_accuracy:.4f}')

# Measure latency distributions
latencies = []
for _ in range(100):
    start_time = time.time()
    inputs = tokenizer(X_test, return_tensors='pt', padding=True)
    outputs = model(**inputs)
    end_time = time.time()
    latency = end_time - start_time
    latencies.append(latency)

print(f'Latency distribution: mean={np.mean(latencies):.4f} seconds, std={np.std(latencies):.4f} seconds')
```

## Exercise 3: Stress Testing, Edge Cases & Failure Mitigation

Reproduce failure modes, test edge cases, and implement guardrails or error handling for both supervised and unsupervised models. The following Python script provides a starting point for stress testing:

```python
import torch
import torch.nn as nn
import torch.optim as optim

# Define stress testing function
def stress_test(model, X_test, y_test):
    model.eval()
    with torch.no_grad():
        inputs = tokenizer(X_test, return_tensors='pt', padding=True)
        outputs = model(**inputs)
        predictions = torch.argmax(outputs.logits, dim=1)
        accuracy = accuracy_score(y_test, predictions)
        return accuracy

# Stress test supervised model
supervised_accuracy = stress_test(model, X_test, y_test)
print(f'Supervised model accuracy: {supervised_accuracy:.4f}')

# Stress test unsupervised model
unsupervised_accuracy = accuracy_score(y_test, labels)
print(f'Unsupervised model accuracy: {unsupervised_accuracy:.4f}')

# Implement guardrails for edge cases
def guardrails(model, X_test, y_test):
    model.eval()
    with torch.no_grad():
        inputs = tokenizer(X_test, return_tensors='pt', padding=True)
        outputs = model(**inputs)
        predictions = torch.argmax(outputs.logits, dim=1)
        accuracy = accuracy_score(y_test, predictions)
        if accuracy < 0.5:
            print(f'Warning: accuracy below 0.5')
        return accuracy

# Implement error handling for failure modes
try:
    model.eval()
    with torch.no_grad():
        inputs = tokenizer(X_test, return_tensors='pt', padding=True)
        outputs = model(**inputs)
        predictions = torch.argmax(outputs.logits, dim=1)
        accuracy = accuracy_score(y_test, predictions)
except Exception as e:
    print(f'Error: {e}')
```

## Verification Checklist & Quick Reference Cheat Sheet

| **Verification Flag** | **Description** | **Python Method** |
| --- | --- | --- |
| `--supervised` | Train supervised model | `model.train()` |
| `--unsupervised` | Train unsupervised model | `kmeans.fit(X_train)` |
| `--accuracy` | Evaluate model accuracy | `accuracy_score(y_test, predictions)` |
| `--latency` | Measure latency distributions | `time.time()` |
| `--guardrails` | Implement guardrails for edge cases | `guardrails(model, X_test, y_test)` |
| `--error-handling` | Implement error handling for failure modes | `try-except` block |

Note: This is a starting point for the lab guide, and you should modify the code to suit your specific requirements and experiment with different hyperparameters, models, and evaluation metrics.
