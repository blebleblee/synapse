# Operational Verification Labs: Core

## Objective & Environment Setup

### Objective
The primary objective of this lab is to provide hands-on experience in implementing, tuning, and verifying a core AI/ML pipeline. This lab will guide you through the process of setting up a robust AI/ML environment, implementing a machine learning model, tuning its hyperparameters, benchmarking its performance, and ensuring it handles edge cases and failures gracefully.

### Environment Setup
Ensure you have a Python 3.11+ environment with the following packages installed:

- PyTorch
- HuggingFace Transformers
- NumPy
- Scikit-learn
- Ollama (if applicable)
- Polars (if applicable)

You can install these packages using pip:

```sh
pip install torch transformers numpy scikit-learn ollama polars
```

Additionally, ensure you have API access configured for any external services you plan to use, such as HuggingFace's model hub.

## Exercise 1: Hands-On Implementation & Pipeline Execution

In this exercise, we will implement a simple text classification pipeline using a pre-trained transformer model from HuggingFace. We will fine-tune this model on a sample dataset and then deploy it for inference.

### Implementation

Here is a complete, runnable Python script that implements the core prompt/model/algorithm for this topic:

```python
import torch
from torch.utils.data import DataLoader, Dataset
from transformers import BertTokenizer, BertForSequenceClassification, Trainer, TrainingArguments
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_recall_fscore_support
import numpy as np

# Sample dataset
class TextDataset(Dataset):
    def __init__(self, texts, labels, tokenizer, max_length):
        self.texts = texts
        self.labels = labels
        self.tokenizer = tokenizer
        self.max_length = max_length

    def __len__(self):
        return len(self.texts)

    def __getitem__(self, idx):
        text = self.texts[idx]
        label = self.labels[idx]
        encoding = self.tokenizer.encode_plus(
            text,
            add_special_tokens=True,
            max_length=self.max_length,
            return_token_type_ids=False,
            padding='max_length',
            return_attention_mask=True,
            return_tensors='pt',
        )
        return {
            'text': text,
            'input_ids': encoding['input_ids'].flatten(),
            'attention_mask': encoding['attention_mask'].flatten(),
            'labels': torch.tensor(label, dtype=torch.long)
        }

# Sample data
texts = [
    "I love programming in Python!",
    "Python is a great language for data science.",
    "I dislike bugs in the code.",
    "Debugging is fun!",
    "I enjoy working with machine learning models.",
    "Data preprocessing is crucial for model performance."
]
labels = [1, 1, 0, 1, 1, 1]  # 1: positive, 0: negative

# Split data
train_texts, val_texts, train_labels, val_labels = train_test_split(texts, labels, test_size=0.2, random_state=42)

# Tokenizer and model
tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')
model = BertForSequenceClassification.from_pretrained('bert-base-uncased', num_labels=2)

# Datasets
train_dataset = TextDataset(train_texts, train_labels, tokenizer, max_length=128)
val_dataset = TextDataset(val_texts, val_labels, tokenizer, max_length=128)

# DataLoaders
train_loader = DataLoader(train_dataset, batch_size=8, shuffle=True)
val_loader = DataLoader(val_dataset, batch_size=8, shuffle=False)

# Metrics
def compute_metrics(pred):
    labels = pred.label_ids
    preds = pred.predictions.argmax(-1)
    precision, recall, f1, _ = precision_recall_fscore_support(labels, preds, average='binary')
    acc = accuracy_score(labels, preds)
    return {
        'accuracy': acc,
        'f1': f1,
        'precision': precision,
        'recall': recall
    }

# Training arguments
training_args = TrainingArguments(
    output_dir='./results',
    num_train_epochs=3,
    per_device_train_batch_size=8,
    per_device_eval_batch_size=8,
    warmup_steps=500,
    weight_decay=0.01,
    logging_dir='./logs',
    logging_steps=10,
    evaluation_strategy="epoch"
)

# Trainer
trainer = Trainer(
    model=model,
    args=training_args,
    compute_metrics=compute_metrics,
    train_dataset=train_dataset,
    eval_dataset=val_dataset
)

# Train the model
trainer.train()

# Evaluate the model
trainer.evaluate()
```

## Exercise 2: Hyperparameter Tuning & Empirical Benchmarking

In this exercise, we will perform hyperparameter tuning and benchmark the performance of the model in terms of accuracy, latency, and convergence.

### Hyperparameter Tuning

We will use a simple grid search approach to tune the learning rate and batch size.

```python
from sklearn.model_selection import ParameterGrid

# Define parameter grid
param_grid = {
    'learning_rate': [2e-5, 3e-5, 5e-5],
    'per_device_train_batch_size': [8, 16]
}

# Perform grid search
best_score = 0
best_params = None

for params in ParameterGrid(param_grid):
    print(f"Trying params: {params}")
    
    # Update training arguments
    training_args.learning_rate = params['learning_rate']
    training_args.per_device_train_batch_size = params['per_device_train_batch_size']
    
    # Initialize model and trainer
    model = BertForSequenceClassification.from_pretrained('bert-base-uncased', num_labels=2)
    trainer = Trainer(
        model=model,
        args=training_args,
        compute_metrics=compute_metrics,
        train_dataset=train_dataset,
        eval_dataset=val_dataset
    )
    
    # Train and evaluate
    trainer.train()
    eval_results = trainer.evaluate()
    
    # Check if this is the best score
    if eval_results['eval_accuracy'] > best_score:
        best_score = eval_results['eval_accuracy']
        best_params = params

print(f"Best parameters: {best_params}")
print(f"Best accuracy: {best_score}")
```

### Benchmarking

We will measure the latency of the model inference.

```python
import time

# Measure inference latency
model.eval()
with torch.no_grad():
    start_time = time.time()
    for batch in val_loader:
        outputs = model(input_ids=batch['input_ids'], attention_mask=batch['attention_mask'])
    end_time = time.time()

latency = (end_time - start_time) / len(val_loader)
print(f"Inference latency: {latency} seconds per batch")
```

## Exercise 3: Stress Testing, Edge Cases & Failure Mitigation

In this exercise, we will test the model on edge cases and implement guardrails to handle potential failures.

### Stress Testing

We will test the model with very long and very short texts.

```python
# Test with very long text
long_text = " ".join(["This is a very long text"] * 100)
long_input = tokenizer.encode_plus(
    long_text,
    add_special_tokens=True,
    max_length=128,
    return_token_type_ids=False,
    padding='max_length',
    return_attention_mask=True,
    return_tensors='pt',
)
long_output = model(input_ids=long_input['input_ids'], attention_mask=long_input['attention_mask'])
print(f"Prediction for long text: {long_output.logits.argmax(-1).item()}")

# Test with very short text
short_text = "Hi"
short_input = tokenizer.encode_plus(
    short_text,
    add_special_tokens=True,
    max_length=128,
    return_token_type_ids=False,
    padding='max_length',
    return_attention_mask=True,
    return_tensors='pt',
)
short_output = model(input_ids=short_input['input_ids'], attention_mask=short_input['attention_mask'])
print(f"Prediction for short text: {short_output.logits.argmax(-1).item()}")
```

### Edge Cases

We will handle cases where the input text is empty or contains only special tokens.

```python
# Test with empty text
empty_text = ""
empty_input = tokenizer.encode_plus(
    empty_text,
    add_special_tokens=True,
    max_length=128,
    return_token_type_ids=False,
    padding='max_length',
    return_attention_mask=True,
    return_tensors='pt',
)
empty_output = model(input_ids=empty_input['input_ids'], attention_mask=empty_input['attention_mask'])
print(f"Prediction for empty text: {empty_output.logits.argmax(-1).item()}")

# Test with only special tokens
special_text = "[CLS] [SEP]"
special_input = tokenizer.encode_plus(
    special_text,
    add_special_tokens=True,
    max_length=128,
    return_token_type_ids=False,
    padding='max_length',
    return_attention_mask=True,
    return_tensors='pt',
)
special_output = model(input_ids=special_input['input_ids'], attention_mask=special_input['attention_mask'])
print(f"Prediction for special tokens: {special_output.logits.argmax(-1).item()}")
```

### Failure Mitigation

We will implement guardrails to handle potential failures, such as invalid inputs.

```python
def predict(text):
    if not text or text.strip() == "":
        raise ValueError("Input text cannot be empty or contain only whitespace.")
    
    input = tokenizer.encode_plus(
        text,
        add_special_tokens=True,
        max_length=128,
        return_token_type_ids=False,
        padding='max_length',
        return_attention_mask=True,
        return_tensors='pt',
    )
    output = model(input_ids=input['input_ids'], attention_mask=input['attention_mask'])
    return output.logits.argmax(-1).item()

# Test guardrails
try:
    predict("")
except ValueError as e:
    print(e)

try:
    predict("   ")
except ValueError as e:
    print(e)

# Valid prediction
print(f"Prediction for valid text: {predict('I love machine learning!')}")
```

## Verification Checklist & Quick Reference Cheat Sheet

### Essential Python Methods & Parameters

| Method/Parameter | Description |
|------------------|-------------|
| `TextDataset`    | Custom dataset class for text data. |
| `BertTokenizer`  | Tokenizer for BERT models. |
| `BertForSequenceClassification` | BERT model for sequence classification tasks. |
| `Trainer`        | HuggingFace Trainer for training and evaluating models. |
| `TrainingArguments` | Configuration for training arguments. |
| `compute_metrics` | Function to compute evaluation metrics. |
| `ParameterGrid`  | Grid search for hyperparameter tuning. |
| `predict`        | Function to perform inference with guardrails. |

### Verification Flags

| Flag             | Description |
|------------------|-------------|
| `learning_rate`  | Learning rate for the optimizer. |
| `per_device_train_batch_size` | Batch size for training. |
| `per_device_eval_batch_size` | Batch size for evaluation. |
| `warmup_steps`   | Number of warmup steps for learning rate scheduler. |
| `weight_decay`   | Weight decay for optimizer. |
| `logging_dir`    | Directory for logging. |
| `logging_steps`  | Logging frequency. |
| `evaluation_strategy` | Evaluation strategy (e.g., epoch). |

By completing this lab, you will have a solid understanding of implementing, tuning, and verifying a core AI/ML pipeline. This will serve as a foundation for more complex and production-ready AI/ML systems.
