# Operational Verification Labs: 03 Evaluation Loops And Benchmarks

## Objective & Environment Setup

This lab aims to provide hands-on experience in implementing evaluation loops and benchmarks for AI models. You will learn to set up a comprehensive pipeline for evaluating AI models, including hyperparameter tuning, empirical benchmarking, stress testing, and failure mitigation. The lab assumes a Python 3.11+ environment with the following packages installed:

- PyTorch
- HuggingFace Transformers
- NumPy
- Scikit-learn
- Ollama
- Polars

Install these packages using pip:

```bash
pip install torch transformers numpy scikit-learn ollama polars
```

Ensure that you have API access configured for any external services you plan to use, such as HuggingFace's model hub.

## Exercise 1: Hands-On Implementation & Pipeline Execution

In this exercise, we implement a core evaluation loop for a text classification model using the HuggingFace Transformers library. The model will be fine-tuned on a sample dataset, and its performance will be evaluated using accuracy metrics.

### Step-by-Step Implementation

First, import the required libraries:

```python
import torch
from torch.utils.data import DataLoader, Dataset
from transformers import BertTokenizer, BertForSequenceClassification, Trainer, TrainingArguments
from sklearn.metrics import accuracy_score
from datasets import load_dataset
```

Load and preprocess the dataset:

```python
# Load a sample dataset
dataset = load_dataset('imdb')

# Initialize tokenizer
tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')

# Tokenize the dataset
def tokenize_function(examples):
    return tokenizer(examples['text'], padding='max_length', truncation=True)

tokenized_datasets = dataset.map(tokenize_function, batched=True)
tokenized_datasets = tokenized_datasets.remove_columns(['text'])
tokenized_datasets = tokenized_datasets.rename_column('label', 'labels')
tokenized_datasets.set_format('torch')
```

Define a custom dataset class:

```python
class TextClassificationDataset(Dataset):
    def __init__(self, dataset):
        self.dataset = dataset

    def __len__(self):
        return len(self.dataset)

    def __getitem__(self, idx):
        return {key: torch.tensor(val[idx]) for key, val in self.dataset[idx].items()}
```

Initialize the model and data loaders:

```python
# Initialize model
model = BertForSequenceClassification.from_pretrained('bert-base-uncased', num_labels=2)

# Create DataLoaders
train_dataset = TextClassificationDataset(tokenized_datasets['train'])
eval_dataset = TextClassificationDataset(tokenized_datasets['test'])

train_loader = DataLoader(train_dataset, batch_size=8, shuffle=True)
eval_loader = DataLoader(eval_dataset, batch_size=8, shuffle=False)
```

Define evaluation metrics:

```python
def compute_metrics(eval_pred):
    logits, labels = eval_pred
    predictions = torch.argmax(logits, dim=-1)
    return {'accuracy': accuracy_score(labels, predictions)}
```

Set up training arguments and the Trainer:

```python
training_args = TrainingArguments(
    output_dir='./results',
    evaluation_strategy='epoch',
    learning_rate=2e-5,
    per_device_train_batch_size=8,
    per_device_eval_batch_size=8,
    num_train_epochs=3,
    weight_decay=0.01,
    logging_dir='./logs',
    logging_steps=10,
)

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=train_dataset,
    eval_dataset=eval_dataset,
    compute_metrics=compute_metrics,
)
```

Train and evaluate the model:

```python
# Train the model
trainer.train()

# Evaluate the model
eval_results = trainer.evaluate()
print(eval_results)
```

## Exercise 2: Hyperparameter Tuning & Empirical Benchmarking

In this exercise, we perform hyperparameter tuning and empirical benchmarking to measure the model's accuracy, latency, and convergence curves.

### Hyperparameter Tuning

We use the `Trainer` class's built-in hyperparameter tuning capabilities with Optuna.

Install Optuna:

```bash
pip install optuna
```

Define the hyperparameter search space:

```python
import optuna
from transformers import TrainingArguments

def objective(trial):
    learning_rate = trial.suggest_loguniform('learning_rate', 1e-5, 5e-5)
    per_device_train_batch_size = trial.suggest_categorical('per_device_train_batch_size', [8, 16, 32])
    num_train_epochs = trial.suggest_int('num_train_epochs', 2, 4)

    training_args = TrainingArguments(
        output_dir='./results',
        evaluation_strategy='epoch',
        learning_rate=learning_rate,
        per_device_train_batch_size=per_device_train_batch_size,
        per_device_eval_batch_size=per_device_train_batch_size,
        num_train_epochs=num_train_epochs,
        weight_decay=0.01,
        logging_dir='./logs',
        logging_steps=10,
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=eval_dataset,
        compute_metrics=compute_metrics,
    )

    trainer.train()
    eval_results = trainer.evaluate()
    return eval_results['eval_accuracy']
```

Run the hyperparameter search:

```python
study = optuna.create_study(direction='maximize')
study.optimize(objective, n_trials=5)

print("Best trial:")
trial = study.best_trial

print(f"  Value: {trial.value}")
print("  Params: ")
for key, value in trial.params.items():
    print(f"    {key}: {value}")
```

### Empirical Benchmarking

We measure the model's latency and convergence curves.

Measure inference latency:

```python
import time

# Measure inference latency
model.eval()
with torch.no_grad():
    start_time = time.time()
    for batch in eval_loader:
        outputs = model(**batch)
    end_time = time.time()

latency = (end_time - start_time) / len(eval_loader)
print(f"Inference latency: {latency} seconds per batch")
```

Plot convergence curves:

```python
import matplotlib.pyplot as plt

# Plot training and evaluation loss
training_loss = trainer.state.log_history[::2]
eval_loss = trainer.state.log_history[1::2]

plt.figure(figsize=(10, 5))
plt.plot([entry['loss'] for entry in training_loss], label='Training Loss')
plt.plot([entry['eval_loss'] for entry in eval_loss], label='Evaluation Loss')
plt.xlabel('Epoch')
plt.ylabel('Loss')
plt.legend()
plt.title('Convergence Curves')
plt.show()
```

## Exercise 3: Stress Testing, Edge Cases & Failure Mitigation

In this exercise, we test the model under stress conditions, handle edge cases, and implement guardrails to mitigate failures.

### Stress Testing

Simulate high load:

```python
import threading

def simulate_load():
    with torch.no_grad():
        for _ in range(100):
            for batch in eval_loader:
                outputs = model(**batch)

threads = [threading.Thread(target=simulate_load) for _ in range(10)]

start_time = time.time()
for thread in threads:
    thread.start()
```
