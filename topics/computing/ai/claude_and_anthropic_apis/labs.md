# Operational Verification Labs: Core

## Objective & Environment Setup

The objective of this lab is to provide hands-on experience with implementing, tuning, and verifying AI models using real, executable Python scripts. This lab will guide you through the process of setting up a Python environment, implementing a core AI model, tuning hyperparameters, benchmarking performance, and handling edge cases. The environment setup requires Python 3.11+ and several popular AI and data science libraries.

### Environment Setup

1. **Install Python 3.11+**:
   Ensure you have Python 3.11 or later installed on your system. You can download it from the [official Python website](https://www.python.org/downloads/).

2. **Install Required Libraries**:
   Use `pip` to install the necessary libraries. Open a terminal and run the following commands:

   ```bash
   pip install torch transformers numpy scikit-learn polars
   ```

3. **API Configuration**:
   For this lab, we will use the Hugging Face Transformers library to access pre-trained models. Ensure you have an API token from Hugging Face. You can obtain one by signing up on the [Hugging Face website](https://huggingface.co/). Set the token as an environment variable:

   ```bash
   export HUGGING_FACE_HUB_TOKEN='your_hugging_face_token'
   ```

## Exercise 1: Hands-On Implementation & Pipeline Execution

In this exercise, we will implement a simple text classification pipeline using a pre-trained BERT model from Hugging Face. The pipeline will classify text inputs into predefined categories.

### Complete, Runnable Python Script

```python
import torch
from transformers import pipeline

# Load a pre-trained BERT model for text classification
classifier = pipeline("text-classification", model="distilbert-base-uncased-finetuned-sst-2-english")

# Define a list of text samples
texts = [
    "I love programming in Python!",
    "This is the worst experience I have ever had.",
    "The movie was fantastic and the acting was superb.",
    "I hate waiting in long queues."
]

# Classify the text samples
results = classifier(texts)

# Print the classification results
for text, result in zip(texts, results):
    print(f"Text: {text}\nClassification: {result['label']}, Score: {result['score']:.4f}\n")
```

### Execution

Save the script to a file, for example, `text_classification.py`, and run it using Python:

```bash
python text_classification.py
```

## Exercise 2: Hyperparameter Tuning & Empirical Benchmarking

In this exercise, we will perform hyperparameter tuning and benchmark the performance of the text classification model. We will measure accuracy, latency, and token costs.

### Real Benchmarking Code

```python
import time
import numpy as np
from transformers import pipeline

# Load a pre-trained BERT model for text classification
classifier = pipeline("text-classification", model="distilbert-base-uncased-finetuned-sst-2-english")

# Define a list of text samples
texts = [
    "I love programming in Python!",
    "This is the worst experience I have ever had.",
    "The movie was fantastic and the acting was superb.",
    "I hate waiting in long queues."
] * 100  # Repeat samples for benchmarking

# Benchmarking function
def benchmark_model(texts):
    start_time = time.time()
    results = classifier(texts)
    end_time = time.time()
    
    # Calculate latency
    latency = end_time - start_time
    latency_per_sample = latency / len(texts)
    
    # Calculate accuracy (assuming true labels are known)
    true_labels = ["POSITIVE", "NEGATIVE", "POSITIVE", "NEGATIVE"] * 100
    predicted_labels = [result['label'] for result in results]
    accuracy = np.mean(np.array(true_labels) == np.array(predicted_labels))
    
    # Calculate token costs (assuming a cost per token)
    token_costs = sum(len(text.split()) for text in texts) * 0.001  # Hypothetical cost
    
    return accuracy, latency, latency_per_sample, token_costs

# Run the benchmark
accuracy, latency, latency_per_sample, token_costs = benchmark_model(texts)

# Print the benchmark results
print(f"Accuracy: {accuracy:.4f}")
print(f"Total Latency: {latency:.4f} seconds")
print(f"Latency per Sample: {latency_per_sample:.4f} seconds")
print(f"Token Costs: ${token_costs:.4f}")
```

### Execution

Save the script to a file, for example, `benchmark_text_classification.py`, and run it using Python:

```bash
python benchmark_text_classification.py
```

## Exercise 3: Stress Testing, Edge Cases & Failure Mitigation

In this exercise, we will test the model under stress conditions, handle edge cases, and implement guardrails or error handling.

### Reproducing Failure Modes, Testing Edge Cases, and Implementing Guardrails

```python
import torch
from transformers import pipeline

# Load a pre-trained BERT model for text classification
classifier = pipeline("text-classification", model="distilbert-base-uncased-finetuned-sst-2-english")

# Define a list of stress test cases and edge cases
stress_tests = [
    "a" * 512,  # Very long text
    "",         # Empty string
    None,       # None value
    12345,      # Integer input
    " " * 512,  # Whitespace only
    "This is a normal sentence."
]

# Function to handle edge cases and stress tests
def handle_edge_cases(texts):
    results = []
    for text in texts:
        try:
            if not isinstance(text, str) or not text.strip():
                raise ValueError("Invalid input: text must be a non-empty string.")
            result = classifier(text)
            results.append(result[0])
        except Exception as e:
            results.append({"label": "ERROR", "score": 0.0, "message": str(e)})
    return results

# Run the edge case handler
results = handle_edge_cases(stress_tests)

# Print the results
for text, result in zip(stress_tests, results):
    print(f"Input: {text}\nResult: {result}\n")
```

### Execution

Save the script to a file, for example, `stress_test_text_classification.py`, and run it using Python:

```bash
python stress_test_text_classification.py
```

## Verification Checklist & Quick Reference Cheat Sheet

### Essential Python Methods, Parameters, and Verification Flags

| Method/Parameter | Description |
|------------------|-------------|
| `pipeline`       | Hugging Face Transformers pipeline for loading and using pre-trained models. |
| `classifier`     | The loaded text classification model. |
| `texts`          | List of text samples for classification. |
| `results`        | Classification results from the model. |
| `accuracy`       | Accuracy of the model based on true labels. |
| `latency`        | Total latency of the model execution. |
| `latency_per_sample` | Latency per text sample. |
| `token_costs`    | Hypothetical token costs for the model execution. |
| `stress_tests`   | List of stress test cases and edge cases. |
| `handle_edge_cases` | Function to handle edge cases and stress tests. |

This lab provides a comprehensive hands-on experience with implementing, tuning, and verifying AI models using Python and the Hugging Face Transformers library. By following the exercises, you will gain practical skills in AI model deployment, performance benchmarking, and robustness testing.
