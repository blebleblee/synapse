# Operational Verification Labs: 02 Agentic Workflows And Tools

## Objective & Environment Setup

The objective of this lab is to provide hands-on experience with agentic workflows and tools in the context of AI and machine learning. This lab will guide you through implementing, tuning, and verifying an AI model using real, executable Python scripts. We will use a combination of popular libraries such as PyTorch, HuggingFace, NumPy, Scikit-learn, and Ollama. Ensure you have a Python 3.11+ environment set up with the following packages installed:

```bash
pip install torch transformers numpy scikit-learn ollama polars
```

Additionally, configure any necessary API keys or tokens for services like HuggingFace or Ollama.

## Exercise 1: Hands-On Implementation & Pipeline Execution

In this exercise, we will implement a simple text classification pipeline using a pre-trained transformer model from HuggingFace. The pipeline will take a text input, preprocess it, pass it through the model, and output the predicted class.

```python
from transformers import pipeline

# Load a pre-trained text classification model
classifier = pipeline("sentiment-analysis")

# Define a function to classify text
def classify_text(text):
    result = classifier(text)
    return result

# Example usage
if __name__ == "__main__":
    text = "I love using AI to solve complex problems!"
    classification_result = classify_text(text)
    print(f"Classification Result: {classification_result}")
```

This script loads a sentiment analysis model and defines a function to classify text. The `__main__` block demonstrates how to use this function with a sample text.

## Exercise 2: Hyperparameter Tuning & Empirical Benchmarking

In this exercise, we will perform hyperparameter tuning and benchmark the performance of our model. We will measure accuracy, latency, and token costs. For simplicity, we will use a synthetic dataset and a smaller model.

```python
import numpy as np
import time
from sklearn.metrics import accuracy_score
from transformers import AutoTokenizer, AutoModelForSequenceClassification, Trainer, TrainingArguments
from datasets import load_dataset

# Load a smaller dataset
dataset = load_dataset("imdb", split="train[:1000]")

# Load a smaller model
model_name = "distilbert-base-uncased"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSequenceClassification.from_pretrained(model_name, num_labels=2)

# Tokenize the dataset
def tokenize_function(examples):
    return tokenizer(examples["text"], padding="max_length", truncation=True)

tokenized_datasets = dataset.map(tokenize_function, batched=True)

# Define training arguments
training_args = TrainingArguments(
    output_dir="./results",
    evaluation_strategy="epoch",
    learning_rate=2e-5,
    per_device_train_batch_size=8,
    per_device_eval_batch_size=8,
    num_train_epochs=1,
    weight_decay=0.01,
)

# Define a simple Trainer
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=tokenized_datasets,
    eval_dataset=tokenized_datasets,
)

# Benchmark the training process
start_time = time.time()
trainer.train()
end_time = time.time()

# Measure latency
latency = end_time - start_time
print(f"Training Latency: {latency} seconds")

# Evaluate the model
eval_results = trainer.evaluate()
accuracy = eval_results["eval_accuracy"]
print(f"Accuracy: {accuracy}")

# Measure token costs (simplified)
token_costs = np.mean([len(tokenizer.encode(example["text"])) for example in dataset])
print(f"Average Token Cost: {token_costs}")
```

This script loads a smaller dataset and model, tokenizes the dataset, and sets up a training pipeline using the `Trainer` API. It measures training latency, accuracy, and average token costs.

## Exercise 3: Stress Testing, Edge Cases & Failure Mitigation

In this exercise, we will stress test our model with edge cases and implement guardrails to handle potential failures. We will test the model with very short and very long texts, as well as texts with special characters.

```python
def test_edge_cases():
    edge_cases = [
        "a",  # Very short text
        "This is a very long text that should test the model's ability to handle long inputs. " * 10,
        "Special characters: !@#$%^&*()_+{}|:\"<>?`~\\-=[];',./",
        "Mixed case: UPPER lower Mixed",
        "Numbers: 1234567890",
        "URL: https://www.example.com",
        "Email: example@example.com",
    ]

    for text in edge_cases:
        try:
            result = classify_text(text)
            print(f"Text: {text}\nClassification Result: {result}\n")
        except Exception as e:
            print(f"Text: {text}\nError: {str(e)}\n")

# Run edge case tests
if __name__ == "__main__":
    test_edge_cases()
```

This script defines a set of edge cases and tests the `classify_text` function with each case. It includes try-except blocks to handle any potential errors gracefully.

## Verification Checklist & Quick Reference Cheat Sheet

| Method/Parameter | Description |
|------------------|-------------|
| `pipeline("sentiment-analysis")` | Loads a pre-trained sentiment analysis model. |
| `classifier(text)` | Classifies the given text using the loaded model. |
| `AutoTokenizer.from_pretrained(model_name)` | Loads a tokenizer for the specified model. |
| `AutoModelForSequenceClassification.from_pretrained(model_name, num_labels=2)` | Loads a sequence classification model for the specified number of labels. |
| `tokenize_function(examples)` | Tokenizes the dataset examples. |
| `TrainingArguments` | Defines training arguments for the `Trainer` API. |
| `Trainer` | Manages the training and evaluation of the model. |
| `trainer.train()` | Trains the model. |
| `trainer.evaluate()` | Evaluates the model. |
| `accuracy_score(y_true, y_pred)` | Computes the accuracy score. |
| `tokenizer.encode(example["text"])` | Encodes the text into tokens. |
| `np.mean()` | Computes the mean of an array. |
| `time.time()` | Returns the current time in seconds since the epoch. |

This lab provides a comprehensive hands-on experience with agentic workflows and tools in AI and machine learning. By implementing, tuning, and verifying an AI model, you will gain practical insights into the entire pipeline from data preprocessing to model evaluation.
