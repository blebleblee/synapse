# Operational Verification Labs

## Objective & Environment Setup

This lab aims to provide hands-on experience in implementing, benchmarking, and verifying AI models and algorithms. Through this lab, you will gain practical knowledge of setting up a comprehensive evaluation pipeline, encompassing hyperparameter tuning, empirical benchmarking, and stress testing. The exercises will utilize a Python 3.11+ environment, leveraging popular libraries such as PyTorch, HuggingFace Transformers, NumPy, Scikit-learn, and Polars. Additionally, we will interact with an API, such as OpenAI's GPT-3.5-turbo, to demonstrate real-world application.

To begin, ensure you have Python 3.11+ installed on your system. Verify your Python version by running:

```bash
python --version
```

Next, install the required packages using pip:

```bash
pip install torch transformers numpy scikit-learn polars openai
```

For API access, sign up for an API key from OpenAI and configure it in your environment by setting the API key as an environment variable:

```bash
export OPENAI_API_KEY='your-api-key-here'
```

## Exercise 1: Hands-On Implementation & Pipeline Execution

In this exercise, we will implement a simple text classification pipeline using a pre-trained transformer model from HuggingFace. We will fine-tune the model on a small dataset and evaluate its performance.

First, import the necessary libraries and load a pre-trained model and tokenizer:

```python
import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer, Trainer, TrainingArguments
from datasets import load_dataset
import numpy as np
from sklearn.metrics import accuracy_score, precision_recall_fscore_support

# Load a pre-trained model and tokenizer
model_name = "distilbert-base-uncased"
model = AutoModelForSequenceClassification.from_pretrained(model_name, num_labels=2)
tokenizer = AutoTokenizer.from_pretrained(model_name)

# Load a small dataset for demonstration
dataset = load_dataset("imdb", split="train[:1000]")

# Tokenize the dataset
def tokenize_function(examples):
    return tokenizer(examples["text"], padding="max_length", truncation=True)

tokenized_datasets = dataset.map(tokenize_function, batched=True)

# Define a compute_metrics function for evaluation
def compute_metrics(eval_pred):
    logits, labels = eval_pred
    predictions = np.argmax(logits, axis=-1)
    precision, recall, f1, _ = precision_recall_fscore_support(labels, predictions, average="binary")
    acc = accuracy_score(labels, predictions)
    return {"accuracy": acc, "f1": f1, "precision": precision, "recall": recall}

# Define training arguments
training_args = TrainingArguments(
    output_dir="./results",
    evaluation_strategy="epoch",
    learning_rate=2e-5,
    per_device_train_batch_size=8,
    per_device_eval_batch_size=8,
    num_train_epochs=3,
    weight_decay=0.01,
)

# Initialize the Trainer
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=tokenized_datasets,
    eval_dataset=tokenized_datasets,
    compute_metrics=compute_metrics,
)

# Train the model
trainer.train()
```

This script loads a pre-trained DistilBERT model, tokenizes a small subset of the IMDb dataset, and fine-tunes the model using the HuggingFace Trainer API. The `compute_metrics` function calculates accuracy, F1 score, precision, and recall for evaluation.

## Exercise 2: Hyperparameter Tuning & Empirical Benchmarking

In this exercise, we will perform hyperparameter tuning and empirical benchmarking to measure the model's accuracy, latency, and convergence curves. We will use Optuna, a hyperparameter optimization framework, to find the best hyperparameters for our model.

First, install Optuna:

```bash
pip install optuna
```

Next, implement the hyperparameter tuning and benchmarking pipeline:

```python
import optuna
from transformers import Trainer, TrainingArguments
import numpy as np
from sklearn.metrics import accuracy_score, precision_recall_fscore_support
import time

# Define the objective function for Optuna
def objective(trial):
    # Suggest hyperparameters
    learning_rate = trial.suggest_loguniform("learning_rate", 1e-5, 5e-5)
    per_device_train_batch_size = trial.suggest_categorical("per_device_train_batch_size", [8, 16, 32])
    per_device_eval_batch_size = trial.suggest_categorical("per_device_eval_batch_size", [8, 16, 32])
    num_train_epochs = trial.suggest_int("num_train_epochs", 2, 4)
    weight_decay = trial.suggest_loguniform("weight_decay", 1e-4, 1e-2)

    # Define training arguments
    training_args = TrainingArguments(
        output_dir="./results",
        evaluation_strategy="epoch",
        learning_rate=learning_rate,
        per_device_train_batch_size=per_device_train_batch_size,
        per_device_eval_batch_size=per_device_eval_batch_size,
        num_train_epochs=num_train_epochs,
        weight_decay=weight_decay,
    )

    # Initialize the Trainer
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized_datasets,
        eval_dataset=tokenized_datasets,
        compute_metrics=compute_metrics,
    )

    # Measure training time
    start_time = time.time()
    trainer.train()
    end_time = time.time()
    training_time = end_time - start_time

    # Evaluate the model
    eval_results = trainer.evaluate()
    accuracy = eval_results["eval_accuracy"]

    # Log additional metrics
    trial.set_user_attr("training_time", training_time)
    trial.set_user_attr("f1", eval_results["eval_f1"])
    trial.set_user_attr("precision", eval_results["eval_precision"])
    trial.set_user_attr("recall", eval_results["eval_recall"])

    return accuracy

# Run hyperparameter optimization
study = optuna.create_study(direction="maximize")
study.optimize(objective, n_trials=10)

# Print the best hyperparameters and corresponding metrics
print("Best hyperparameters:", study.best_params)
print("Best accuracy:", study.best_value)
print("Training time:", study.best_trial.user_attrs["training_time"])
print("F1 score:", study.best_trial.user_attrs["f1"])
print("Precision:", study.best_trial.user_attrs["precision"])
print("Recall:", study.best_trial.user_attrs["recall"])
```

This script uses Optuna to perform hyperparameter tuning on the learning rate, batch size, number of epochs, and weight decay. It measures the model's accuracy, training time, and other evaluation metrics for each trial.

## Exercise 3: Stress Testing, Edge Cases & Failure Mitigation

In this exercise, we will perform stress testing, identify edge cases, and implement guardrails or error handling to ensure the robustness of our model. We will simulate high-load scenarios and test the model's performance under various conditions.

First, implement a stress testing script to evaluate the model's performance under high-load conditions:

```python
import time
import threading
from transformers import pipeline

# Load the fine-tuned model
classifier = pipeline("text-classification", model="distilbert-base-uncased", tokenizer="distilbert-base-uncased")

# Define a function to perform classification
def classify_text(text):
    return classifier(text)

# Define a function to simulate high-load conditions
def stress_test():
    texts = ["This movie was fantastic!", "I did not like this movie at all."] * 1000
    start_time = time.time()
    threads = []
    for text in texts:
        thread = threading.Thread(target=classify_text, args=(text,))
        threads.append(thread)
        thread.start()
    for thread in threads:
        thread.join()
    end_time = time.time()
    print(f"Stress test completed in {end_time - start_time} seconds")

# Run the stress test
stress_test()
```

This script simulates high-load conditions by creating multiple threads to classify text concurrently, thereby testing the model's performance under stress.
