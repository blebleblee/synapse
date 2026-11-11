# Operational Verification Labs: 03 Feature Engineering And Regularization

## Objective & Environment Setup

This lab focuses on hands-on implementation and verification of feature engineering and regularization techniques in machine learning. To complete this lab, you will need a Python 3.11+ environment with the following packages installed:

* PyTorch
* HuggingFace
* NumPy
* Scikit-learn
* Ollama
* Polars

Additionally, ensure that your API configuration is set up for the chosen library or framework.

### Required Packages and Environment Setup

```bash
pip install torch transformers numpy scikit-learn ollama polars
```

### API Configuration

For this lab, we will use the HuggingFace Transformers library. Ensure that you have the necessary API keys and configuration set up for the chosen model.

```python
import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
from ollama import Ollama
from polars import DataFrame
```

## Exercise 1: Hands-On Implementation & Pipeline Execution

In this exercise, you will implement a basic feature engineering and regularization pipeline using PyTorch and HuggingFace Transformers. The goal is to train a sequence classification model on a sample dataset and evaluate its performance.

### Sample Dataset

For this lab, we will use the IMDB dataset, which is a binary sentiment classification task.

```python
import pandas as pd
from sklearn.datasets import fetch_imdb
from sklearn.model_selection import train_test_split

# Load IMDB dataset
imdb = fetch_imdb()
df = pd.DataFrame(imdb.data, columns=imdb.feature_names)
y = pd.Series(imdb.target)

# Split dataset into training and testing sets
X_train, X_test, y_train, y_test = train_test_split(df, y, test_size=0.2, random_state=42)
```

### Feature Engineering and Regularization Pipeline

```python
# Define feature engineering and regularization pipeline
class FeatureEngineeringAndRegularizationPipeline:
    def __init__(self, model, tokenizer, scaler):
        self.model = model
        self.tokenizer = tokenizer
        self.scaler = scaler

    def preprocess(self, text):
        inputs = self.tokenizer.encode_plus(
            text,
            add_special_tokens=True,
            max_length=512,
            return_attention_mask=True,
            return_tensors='pt',
        )
        return inputs['input_ids'], inputs['attention_mask']

    def train(self, X_train, y_train):
        self.model.train()
        optimizer = torch.optim.Adam(self.model.parameters(), lr=1e-5)
        for epoch in range(5):
            for i, (text, label) in enumerate(zip(X_train, y_train)):
                inputs, attention_mask = self.preprocess(text)
                optimizer.zero_grad()
                outputs = self.model(inputs, attention_mask=attention_mask)
                loss = outputs.loss
                loss.backward()
                optimizer.step()
            print(f'Epoch {epoch+1}, Loss: {loss.item()}')

    def evaluate(self, X_test, y_test):
        self.model.eval()
        predictions = []
        with torch.no_grad():
            for text, label in zip(X_test, y_test):
                inputs, attention_mask = self.preprocess(text)
                outputs = self.model(inputs, attention_mask=attention_mask)
                predictions.append(outputs.logits.argmax(dim=1).item())
        accuracy = accuracy_score(y_test, predictions)
        print(f'Accuracy: {accuracy:.4f}')

# Initialize pipeline
model = AutoModelForSequenceClassification.from_pretrained('distilbert-base-uncased')
tokenizer = AutoTokenizer.from_pretrained('distilbert-base-uncased')
scaler = StandardScaler()
pipeline = FeatureEngineeringAndRegularizationPipeline(model, tokenizer, scaler)

# Train and evaluate pipeline
pipeline.train(X_train, y_train)
pipeline.evaluate(X_test, y_test)
```

## Exercise 2: Hyperparameter Tuning & Empirical Benchmarking

In this exercise, you will perform hyperparameter tuning and empirical benchmarking of the feature engineering and regularization pipeline.

### Hyperparameter Tuning

```python
from sklearn.model_selection import GridSearchCV

# Define hyperparameter search space
param_grid = {
    'model': ['distilbert-base-uncased', 'bert-base-uncased'],
    'learning_rate': [1e-5, 1e-6],
    'batch_size': [16, 32],
}

# Perform hyperparameter tuning
grid_search = GridSearchCV(pipeline.model, param_grid, cv=5, scoring='accuracy')
grid_search.fit(X_train, y_train)

# Print best hyperparameters
print(f'Best Hyperparameters: {grid_search.best_params_}')
```

### Empirical Benchmarking

```python
# Evaluate pipeline with best hyperparameters
best_model = grid_search.best_estimator_
best_model.eval()
predictions = []
with torch.no_grad():
    for text, label in zip(X_test, y_test):
        inputs, attention_mask = pipeline.preprocess(text)
        outputs = best_model(inputs, attention_mask=attention_mask)
        predictions.append(outputs.logits.argmax(dim=1).item())
accuracy = accuracy_score(y_test, predictions)
print(f'Accuracy: {accuracy:.4f}')
```

## Exercise 3: Stress Testing, Edge Cases & Failure Mitigation

In this exercise, you will perform stress testing, edge case testing, and implement failure mitigation for the feature engineering and regularization pipeline.

### Stress Testing

```python
# Perform stress testing
import torch.nn.functional as F

# Simulate large input size
large_input = torch.randn(1024, 512)
attention_mask = torch.ones(1024, 512)

# Evaluate pipeline with large input
outputs = pipeline.model(large_input, attention_mask=attention_mask)
loss = F.cross_entropy(outputs.logits, torch.zeros(1024))
print(f'Stress Testing Loss: {loss.item()}')
```

### Edge Case Testing

```python
# Perform edge case testing
import torch.nn.functional as F

# Simulate edge case input
edge_case_input = torch.randn(1, 512)
attention_mask = torch.ones(1, 512)

# Evaluate pipeline with edge case input
outputs = pipeline.model(edge_case_input, attention_mask=attention_mask)
loss = F.cross_entropy(outputs.logits, torch.zeros(1))
print(f'Edge Case Testing Loss: {loss.item()}')
```

### Failure Mitigation

```python
# Implement failure mitigation
class FailureMitigationPipeline:
    def __init__(self, model, tokenizer, scaler):
        self.model = model
        self.tokenizer = tokenizer
        self.scaler = scaler

    def preprocess(self, text):
        # Implement input validation and normalization
        inputs = self.tokenizer.encode_plus(
            text,
            add_special_tokens=True,
            max_length=512,
            return_attention_mask=True,
            return_tensors='pt',
        )
        return inputs['input_ids'], inputs['attention_mask']

    def train(self, X_train, y_train):
        # Implement robust training loop
        self.model.train()
        optimizer = torch.optim.Adam(self.model.parameters(), lr=1e-5)
        for epoch in range(5):
            for i, (text, label) in enumerate(zip(X_train, y_train)):
                inputs, attention_mask = self.preprocess(text)
                optimizer.zero_grad()
                outputs = self.model(inputs, attention_mask=attention_mask)
                loss = outputs.loss
                loss.backward()
                optimizer.step()
            print(f'Epoch {epoch+1}, Loss: {loss.item()}')

    def evaluate(self, X_test, y_test):
        # Implement robust evaluation loop
        self.model.eval()
        predictions = []
        with torch.no_grad():
            for text, label in zip(X_test, y_test):
                inputs, attention_mask = self.preprocess(text)
                outputs = self.model(inputs, attention_mask=attention_mask)
                predictions.append(outputs.logits.argmax(dim=1).item())
        accuracy = accuracy_score(y_test, predictions)
        print(f'Accuracy: {accuracy:.4f}')

# Initialize pipeline with failure mitigation
model = AutoModelForSequenceClassification.from_pretrained('distilbert-base-uncased')
tokenizer = AutoTokenizer.from_pretrained('distilbert-base-uncased')
scaler = StandardScaler()
pipeline = FailureMitigationPipeline(model, tokenizer, scaler)

# Train and evaluate pipeline with failure mitigation
pipeline.train(X_train, y_train)
pipeline.evaluate(X_test, y_test)
```

## Verification Checklist & Quick Reference Cheat Sheet

| **Verification Flag** | **Description** | **Python Method** |
| --- | --- | --- |
| `--help` | Display help message | `print_help()` |
| `--version` | Display version number | `print_version()` |
| `--debug` | Enable debug mode | `set_debug_mode(True)` |
| `--verbose` | Enable verbose mode | `set_verbose_mode(True)` |
| `--quiet` | Disable verbose mode | `set_verbose_mode(False)` |

| **Parameter** | **Description** | **Python Method** |
| --- | --- | --- |
| `model` | Model architecture | `AutoModelForSequenceClassification.from_pretrained()` |
| `tokenizer` | Tokenizer architecture | `AutoTokenizer.from_pretrained()` |
| `scaler` | Scaler architecture | `StandardScaler()` |
| `learning_rate` | Learning rate | `torch.optim.Adam()` |
| `batch_size` | Batch size | `torch.nn.DataParallel()` |

Note: This is a sample lab guide and may require modifications to fit specific requirements.
