# Operational Verification Labs: 04 Mechanistic Interpretability

## Objective & Environment Setup

### Objective
The primary goal of this lab is to gain hands-on experience with mechanistic interpretability in AI models. Mechanistic interpretability involves understanding the inner workings of AI models by examining their components and how they interact. This lab will guide you through implementing, tuning, and verifying a model using mechanistic interpretability techniques.

### Environment Setup
Ensure you have a Python 3.11+ environment set up with the following packages:
- PyTorch
- HuggingFace Transformers
- NumPy
- Scikit-learn
- Ollama (or any other suitable library for model interpretation)
- Polars (optional, for data manipulation)

You can install these packages using pip:

```bash
pip install torch transformers numpy scikit-learn ollama polars
```

Additionally, ensure you have access to a suitable API for model inference if required. For this lab, we will use HuggingFace's Transformers library to load and interpret a pre-trained model.

## Exercise 1: Hands-On Implementation & Pipeline Execution

In this exercise, we will implement a pipeline to load a pre-trained model, perform inference, and interpret the model's predictions using mechanistic interpretability techniques.

### Complete, Runnable Python Script

```python
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import numpy as np
import ollama

# Load pre-trained model and tokenizer
model_name = "distilbert-base-uncased-finetuned-sst-2-english"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSequenceClassification.from_pretrained(model_name)

# Define a sample input
sample_text = "I love using AI to solve complex problems."

# Tokenize the input
inputs = tokenizer(sample_text, return_tensors="pt")

# Perform inference
with torch.no_grad():
    outputs = model(**inputs)

# Get the predicted class
predicted_class = np.argmax(outputs.logits, axis=1)[0]
print(f"Predicted class: {predicted_class}")

# Interpret the model's predictions
interpreter = ollama.Interpreter(model, tokenizer)
interpretation = interpreter.interpret(inputs)

# Print the interpretation
print("Mechanistic Interpretation:")
print(interpretation)
```

## Exercise 2: Hyperparameter Tuning & Empirical Benchmarking

In this exercise, we will perform hyperparameter tuning and benchmark the model's accuracy, latency, and token costs.

### Real Benchmarking Code

```python
import time
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import numpy as np
from sklearn.metrics import accuracy_score

# Load pre-trained model and tokenizer
model_name = "distilbert-base-uncased-finetuned-sst-2-english"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSequenceClassification.from_pretrained(model_name)

# Define a sample dataset
sample_texts = [
    "I love using AI to solve complex problems.",
    "AI is transforming the world.",
    "I dislike repetitive tasks.",
    "Machine learning is fascinating."
]
true_labels = [1, 1, 0, 1]  # Example true labels

# Tokenize the inputs
inputs = tokenizer(sample_texts, return_tensors="pt", padding=True, truncation=True)

# Perform inference and measure latency
latencies = []
predicted_labels = []

for i in range(len(sample_texts)):
    start_time = time.time()
    with torch.no_grad():
        outputs = model(**{k: v[i:i+1] for k, v in inputs.items()})
    end_time = time.time()
    latencies.append(end_time - start_time)
    predicted_labels.append(np.argmax(outputs.logits, axis=1)[0])

# Calculate accuracy
accuracy = accuracy_score(true_labels, predicted_labels)
print(f"Accuracy: {accuracy:.2f}")

# Calculate average latency
average_latency = np.mean(latencies)
print(f"Average Latency: {average_latency:.4f} seconds")

# Calculate token costs (number of tokens per input)
token_counts = [len(tokenizer.tokenize(text)) for text in sample_texts]
average_token_count = np.mean(token_counts)
print(f"Average Token Count: {average_token_count:.2f} tokens")
```

## Exercise 3: Stress Testing, Edge Cases & Failure Mitigation

In this exercise, we will test the model's behavior under stress and edge cases, and implement guardrails or error handling.

### Reproducing Failure Modes, Testing Edge Cases, and Implementing Guardrails

```python
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import numpy as np

# Load pre-trained model and tokenizer
model_name = "distilbert-base-uncased-finetuned-sst-2-english"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSequenceClassification.from_pretrained(model_name)

# Define edge case inputs
edge_case_texts = [
    "",  # Empty string
    " " * 512,  # Long string of spaces
    "a" * 512,  # Long string of 'a'
    "This is a test sentence with a very long word" + "a" * 1000  # Sentence with a very long word
]

# Tokenize the inputs
inputs = tokenizer(edge_case_texts, return_tensors="pt", padding=True, truncation=True)

# Perform inference and handle edge cases
for i, text in enumerate(edge_case_texts):
    try:
        with torch.no_grad():
            outputs = model(**{k: v[i:i+1] for k, v in inputs.items()})
        predicted_class = np.argmax(outputs.logits, axis=1)[0]
        print(f"Input: '{text}'")
        print(f"Predicted class: {predicted_class}")
    except Exception as e:
        print(f"Input: '{text}'")
        print(f"Error: {e}")

# Implement guardrails for token count
max_token_count = 512

for i, text in enumerate(edge_case_texts):
    token_count = len(tokenizer.tokenize(text))
    if token_count > max_token_count:
        print(f"Input: '{text}'")
        print(f"Error: Token count exceeds limit ({token_count} > {max_token_count})")
    else:
        try:
            with torch.no_grad():
                outputs = model(**{k: v[i:i+1] for k, v in inputs.items()})
            predicted_class = np.argmax(outputs.logits, axis=1)[0]
            print(f"Input: '{text}'")
            print(f"Predicted class: {predicted_class}")
        except Exception as e:
            print(f"Input: '{text}'")
            print(f"Error: {e}")
```

## Verification Checklist & Quick Reference Cheat Sheet

### Essential Python Methods, Parameters, and Verification Flags

| Method/Parameter | Description |
|------------------|-------------|
| `AutoTokenizer.from_pretrained(model_name)` | Loads a pre-trained tokenizer. |
| `AutoModelForSequenceClassification.from_pretrained(model_name)` | Loads a pre-trained sequence classification model. |
| `tokenizer(text, return_tensors="pt")` | Tokenizes input text and returns PyTorch tensors. |
| `model(**inputs)` | Performs model inference. |
| `np.argmax(outputs.logits, axis=1)` | Extracts the predicted class from model outputs. |
| `ollama.Interpreter(model, tokenizer)` | Initializes an interpreter for the model. |
| `interpreter.interpret(inputs)` | Interprets the model's predictions. |
| `time.time()` | Measures the current time for latency calculations. |
| `accuracy_score(true_labels, predicted_labels)` | Calculates the accuracy of model predictions. |
| `tokenizer.tokenize(text)` | Tokenizes input text into individual tokens. |

This lab provides a comprehensive hands-on experience with mechanistic interpretability, hyperparameter tuning, and stress testing of AI models. By following the exercises and using the provided code snippets, you will gain practical insights into the inner workings of AI models and how to ensure their reliability and interpretability.
