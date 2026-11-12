# Operational Verification Labs: 01 Prompt Engineering And Specs

## Objective & Environment Setup

This lab focuses on hands-on implementation and verification of prompt engineering techniques for AI models. To complete this lab, you will need a Python 3.11+ environment with the following packages installed: PyTorch, HuggingFace Transformers, NumPy, Scikit-learn, Ollama, and Polars. Additionally, you will need to configure your API settings for the HuggingFace library. This can be done by creating a `transformers` configuration file in your home directory, e.g., `~/.transformers/config.json`. For this lab, we will use the `bert-base-uncased` model.

```python
import os
import torch
from transformers import BertTokenizer, BertModel
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split
from ollama import Ollama
from polars import DataFrame

# Set up API configuration
os.environ['TRANSFORMERS_CACHE'] = '~/.transformers/cache'
os.environ['TRANSFORMERS_PRETRAINED'] = 'bert-base-uncased'

# Load pre-trained model and tokenizer
tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')
model = BertModel.from_pretrained('bert-base-uncased')
```

## Exercise 1: Hands-On Implementation & Pipeline Execution

In this exercise, you will implement a basic prompt engineering pipeline using the HuggingFace library. You will create a custom dataset class, implement a data loader, and train a model using the `BertForSequenceClassification` class.

```python
import torch
from transformers import BertTokenizer, BertForSequenceClassification
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split
from torch.utils.data import DataLoader, Dataset

# Define custom dataset class
class PromptEngineeringDataset(Dataset):
    def __init__(self, data, labels, tokenizer):
        self.data = data
        self.labels = labels
        self.tokenizer = tokenizer

    def __getitem__(self, idx):
        inputs = self.tokenizer.encode_plus(
            self.data[idx],
            add_special_tokens=True,
            max_length=512,
            return_attention_mask=True,
            return_tensors='pt'
        )
        return {
            'input_ids': inputs['input_ids'].flatten(),
            'attention_mask': inputs['attention_mask'].flatten(),
            'labels': torch.tensor(self.labels[idx])
        }

    def __len__(self):
        return len(self.data)

# Load dataset and create data loader
data = ["example sentence 1", "example sentence 2"]  # Replace with actual data
labels = [0, 1]  # Replace with actual labels
dataset = PromptEngineeringDataset(data, labels, tokenizer)
data_loader = DataLoader(dataset, batch_size=32, shuffle=True)

# Train model using BertForSequenceClassification
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
model = BertForSequenceClassification.from_pretrained('bert-base-uncased')
model.to(device)
criterion = torch.nn.CrossEntropyLoss()
optimizer = torch.optim.Adam(model.parameters(), lr=1e-5)

for epoch in range(5):
    model.train()
    total_loss = 0
    for batch in data_loader:
        input_ids = batch['input_ids'].to(device)
        attention_mask = batch['attention_mask'].to(device)
        labels = batch['labels'].to(device)
        optimizer.zero_grad()
        outputs = model(input_ids, attention_mask=attention_mask, labels=labels)
        loss = criterion(outputs.logits, labels)
        loss.backward()
        optimizer.step()
        total_loss += loss.item()
    print(f'Epoch {epoch+1}, Loss: {total_loss / len(data_loader)}')

model.eval()
```

## Exercise 2: Hyperparameter Tuning & Empirical Benchmarking

In this exercise, you will implement hyperparameter tuning using the `Optuna` library and empirical benchmarking using the `Polars` library.

```python
import optuna
from polars import DataFrame
from sklearn.metrics import accuracy_score

# Define objective function for hyperparameter tuning
def objective(trial):
    learning_rate = trial.suggest_loguniform('learning_rate', 1e-6, 1e-3)
    num_epochs = trial.suggest_int('num_epochs', 1, 10)
    model = BertForSequenceClassification.from_pretrained('bert-base-uncased')
    model.to(device)
    criterion = torch.nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)

    for epoch in range(num_epochs):
        model.train()
        total_loss = 0
        for batch in data_loader:
            input_ids = batch['input_ids'].to(device)
            attention_mask = batch['attention_mask'].to(device)
            labels = batch['labels'].to(device)
            optimizer.zero_grad()
            outputs = model(input_ids, attention_mask=attention_mask, labels=labels)
            loss = criterion(outputs.logits, labels)
            loss.backward()
            optimizer.step()
            total_loss += loss.item()

    model.eval()
    predictions = []
    true_labels = []
    with torch.no_grad():
        for batch in data_loader:
            input_ids = batch['input_ids'].to(device)
            attention_mask = batch['attention_mask'].to(device)
            labels = batch['labels'].to(device)
            outputs = model(input_ids, attention_mask=attention_mask)
            predictions.extend(torch.argmax(outputs.logits, dim=1).cpu().numpy())
            true_labels.extend(labels.cpu().numpy())

    return accuracy_score(true_labels, predictions)

# Perform hyperparameter tuning
study = optuna.create_study(direction='maximize')
study.optimize(objective, n_trials=10)

# Perform empirical benchmarking
df = DataFrame(data)
predictions = model.predict(torch.tensor(data).to(device)).logits.argmax(dim=1).cpu().numpy()
accuracy = accuracy_score(labels, predictions)
print(f'Accuracy: {accuracy:.4f}')
```

## Exercise 3: Stress Testing, Edge Cases & Failure Mitigation

In this exercise, you will implement stress testing using the `Locust` library and edge case testing using the `Hypothesis` library.

```python
import locust
from hypothesis import given
from hypothesis.strategies import text
import torch

# Define Locust task for stress testing
class PromptEngineeringTask(locust.TaskSet):
    def on_start(self):
        self.model = BertForSequenceClassification.from_pretrained('bert-base-uncased')
        self.model.to(device)

    @locust.task
    def run(self):
        input_ids = torch.randint(0, 10000, (1, 512))
        attention_mask = torch.ones(1, 512)
        labels = torch.randint(0, 2, (1,))
        self.model(input_ids.to(device), attention_mask=attention_mask.to(device), labels=labels.to(device))

# Define Hypothesis strategy for edge case testing
@given(text())
def test_edge_case(prompt):
    inputs = tokenizer.encode_plus(prompt, add_special_tokens=True, max_length=512, return_attention_mask=True, return_tensors='pt')
    input_ids = inputs['input_ids'].flatten().to(device)
    attention_mask = inputs['attention_mask'].flatten().to(device)
    labels = torch.tensor(0).to(device)
    model(input_ids, attention_mask=attention_mask, labels=labels)

# Run Locust task for stress testing
# locust.main(['-f', 'prompt_engineering_task.py'])

# Run Hypothesis test for edge case testing
# hypothesis.main(['-f', 'prompt_engineering_test.py'])
```

## Verification Checklist & Quick Reference Cheat Sheet

| Python Method | Description | Parameters |
| --- | --- | --- |
| `BertTokenizer.encode_plus` | Tokenize input text | `input_text`, `add_special_tokens`, `max_length`, `return_attention_mask`, `return_tensors` |
| `BertModel.forward` | Forward pass through model | `input_ids`, `attention_mask`, `labels` |
| `torch.nn.CrossEntropyLoss` | Cross-entropy loss function | `output`, `target` |
| `torch.optim.Adam` | Adam optimizer | `parameters`, `lr` |
| `optuna.create_study` | Create Optuna study | `direction` |
| `optuna.optimize` | Optimize objective function | `objective`, `n_trials` |
| `polars.DataFrame` | Create Polars DataFrame | `data` |
| `sklearn.metrics.accuracy_score` | Calculate accuracy score | `y_true`, `y_pred` |

Note: This is a basic implementation of the prompt engineering pipeline and is intended to serve as a starting point for further development and experimentation.
