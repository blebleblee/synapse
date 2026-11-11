# Operational Verification Labs: 04 Pipeline Orchestration And Monitoring

## Objective & Environment Setup

### Objective
The objective of this lab is to gain hands-on experience with pipeline orchestration and monitoring in the context of AI/MLops and serving. You will implement a complete ML pipeline, perform hyperparameter tuning, conduct empirical benchmarking, and stress test the pipeline to identify and mitigate failure modes.

### Environment Setup
Ensure you have a Python 3.11+ environment set up with the following packages installed:
- PyTorch
- HuggingFace Transformers
- NumPy
- Scikit-learn
- Polars

You can install these packages using pip:

```bash
pip install torch transformers numpy scikit-learn polars
```

Additionally, ensure you have API access configured for any external services you plan to use, such as HuggingFace's model hub.

## Exercise 1: Hands-On Implementation & Pipeline Execution

In this exercise, we will implement a complete ML pipeline that includes data loading, model training, and evaluation. We will use a simple text classification task with a pre-trained transformer model from HuggingFace.

### Complete, Runnable Python Script

```python
import torch
from torch.utils.data import DataLoader
from transformers import BertTokenizer, BertForSequenceClassification, Trainer, TrainingArguments
from datasets import load_dataset

# Load dataset
dataset = load_dataset('imdb')

# Load tokenizer and model
tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')
model = BertForSequenceClassification.from_pretrained('bert-base-uncased', num_labels=2)

# Tokenize dataset
def tokenize_function(examples):
    return tokenizer(examples['text'], padding='max_length', truncation=True)

tokenized_datasets = dataset.map(tokenize_function, batched=True)
tokenized_datasets = tokenized_datasets.remove_columns(['text'])
tokenized_datasets = tokenized_datasets.rename_column('label', 'labels')
tokenized_datasets.set_format('torch', columns=['input_ids', 'attention_mask', 'labels'])

# Create data loaders
train_dataloader = DataLoader(tokenized_datasets['train'], batch_size=8, shuffle=True)
eval_dataloader = DataLoader(tokenized_datasets['test'], batch_size=8)

# Define training arguments
training_args = TrainingArguments(
    output_dir='./results',
    evaluation_strategy='epoch',
    learning_rate=2e-5,
    per_device_train_batch_size=8,
    per_device_eval_batch_size=8,
    num_train_epochs=3,
    weight_decay=0.01,
)

# Define Trainer
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=tokenized_datasets['train'],
    eval_dataset=tokenized_datasets['test'],
)

# Train and evaluate the model
trainer.train()
trainer.evaluate()
```

## Exercise 2: Hyperparameter Tuning & Empirical Benchmarking

In this exercise, we will perform hyperparameter tuning and conduct empirical benchmarking to measure the accuracy, latency, and convergence of our model.

### Real Benchmarking Code

```python
import time
import numpy as np
from sklearn.metrics import accuracy_score

# Hyperparameter tuning using grid search
def grid_search_hyperparameters(train_dataloader, eval_dataloader, model, training_args):
    learning_rates = [2e-5, 3e-5, 5e-5]
    batch_sizes = [8, 16, 32]
    best_accuracy = 0
    best_params = {}

    for lr in learning_rates:
        for bs in batch_sizes:
            training_args.learning_rate = lr
            training_args.per_device_train_batch_size = bs
            training_args.per_device_eval_batch_size = bs

            trainer = Trainer(
                model=model,
                args=training_args,
                train_dataset=tokenized_datasets['train'],
                eval_dataset=tokenized_datasets['test'],
            )

            start_time = time.time()
            trainer.train()
            eval_results = trainer.evaluate()
            end_time = time.time()

            latency = end_time - start_time
            accuracy = eval_results['eval_accuracy']

            print(f"Learning Rate: {lr}, Batch Size: {bs}, Accuracy: {accuracy}, Latency: {latency}")

            if accuracy > best_accuracy:
                best_accuracy = accuracy
                best_params = {'learning_rate': lr, 'batch_size': bs}

    return best_params, best_accuracy

# Benchmarking
best_params, best_accuracy = grid_search_hyperparameters(train_dataloader, eval_dataloader, model, training_args)
print(f"Best Parameters: {best_params}, Best Accuracy: {best_accuracy}")
```

## Exercise 3: Stress Testing, Edge Cases & Failure Mitigation

In this exercise, we will stress test the pipeline, identify edge cases, and implement guardrails or error handling to mitigate failure modes.

### Reproducing Failure Modes, Testing Edge Cases, and Implementing Guardrails

```python
import torch
from transformers import BertTokenizer, BertForSequenceClassification, Trainer, TrainingArguments
from datasets import load_dataset

# Load dataset
dataset = load_dataset('imdb')

# Load tokenizer and model
tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')
model = BertForSequenceClassification.from_pretrained('bert-base-uncased', num_labels=2)

# Tokenize dataset
def tokenize_function(examples):
    return tokenizer(examples['text'], padding='max_length', truncation=True)

tokenized_datasets = dataset.map(tokenize_function, batched=True)
tokenized_datasets = tokenized_datasets.remove_columns(['text'])
tokenized_datasets = tokenized_datasets.rename_column('label', 'labels')
tokenized_datasets.set_format('torch', columns=['input_ids', 'attention_mask', 'labels'])

# Create data loaders
train_dataloader = DataLoader(tokenized_datasets['train'], batch_size=8, shuffle=True)
eval_dataloader = DataLoader(tokenized_datasets['test'], batch_size=8)

# Define training arguments
training_args = TrainingArguments(
    output_dir='./results',
    evaluation_strategy='epoch',
    learning_rate=2e-5,
    per_device_train_batch_size=8,
    per_device_eval_batch_size=8,
    num_train_epochs=3,
    weight_decay=0.01,
)

# Define Trainer
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=tokenized_datasets['train'],
    eval_dataset=tokenized_datasets['test'],
)

# Stress testing by increasing the number of epochs
training_args.num_train_epochs = 10
trainer.train()

# Edge case: testing with empty input
empty_input = tokenizer("", return_tensors="pt")
output = model(**empty_input)
print(output)

# Implementing guardrails: checking for empty inputs
def safe_predict(text):
    if not text.strip():
        raise ValueError("Input text cannot be empty")
    inputs = tokenizer(text, return_tensors="pt")
    outputs = model(**inputs)
    return outputs

# Test guardrails
try:
    safe_predict("")
except ValueError as e:
    print(e)

try:
    safe_predict("This is a test.")
except ValueError as e:
    print(e)
```

## Verification Checklist & Quick Reference Cheat Sheet

### Essential Python Methods, Parameters, and Verification Flags

| Method/Parameter | Description |
|------------------|-------------|
| `load_dataset`   | Loads a dataset from the HuggingFace datasets library. |
| `BertTokenizer`  | Tokenizer for BERT models. |
| `BertForSequenceClassification` | BERT model for sequence classification tasks. |
| `DataLoader`     | Creates data loaders for training and evaluation. |
| `TrainingArguments` | Configuration for training arguments. |
| `Trainer`        | High-level interface for training and evaluating models. |
| `train`          | Trains the model. |
| `evaluate`       | Evaluates the model on the evaluation dataset. |
| `grid_search_hyperparameters` | Performs hyperparameter tuning using grid search. |
| `safe_predict`   | Safely predicts outputs while handling edge cases. |

### CLI Commands

- Install required packages:
  ```bash
  pip install torch transformers numpy scikit-learn polars
  ```

- Run the complete pipeline script:
  ```bash
  python pipeline_script.py
  ```

This lab provides a comprehensive hands-on experience with pipeline orchestration and monitoring, ensuring that you can implement, tune, benchmark, and stress test ML pipelines effectively.
