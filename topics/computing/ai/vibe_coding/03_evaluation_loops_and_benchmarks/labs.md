# Operational Verification Labs: 03 Evaluation Loops And Benchmarks

## Objective & Environment Setup

The objective of this lab is to provide hands-on experience with implementing evaluation loops and benchmarks for AI models. This will involve setting up a Python environment with necessary libraries, implementing a core evaluation pipeline, tuning hyperparameters, benchmarking performance, and handling edge cases. The lab assumes a Python 3.11+ environment with the following packages installed:

- PyTorch
- HuggingFace Transformers
- NumPy
- Scikit-learn
- Polars

To set up the environment, you can use the following commands:

```bash
pip install torch transformers numpy scikit-learn polars
```

Additionally, ensure that you have access to any necessary API keys or configurations for models hosted on platforms like HuggingFace.

## Exercise 1: Hands-On Implementation & Pipeline Execution

In this exercise, we will implement a core evaluation pipeline for a text classification model using a pre-trained BERT model from HuggingFace. The pipeline will include data loading, model inference, and accuracy calculation.

### Step-by-Step Implementation

1. **Import Necessary Libraries**

```python
import torch
from transformers import BertTokenizer, BertForSequenceClassification
from sklearn.metrics import accuracy_score
from torch.utils.data import DataLoader, Dataset
import numpy as np
import polars as pl
```

2. **Define a Custom Dataset Class**

```python
class TextClassificationDataset(Dataset):
    def __init__(self, dataframe, tokenizer, max_length):
        self.dataframe = dataframe
        self.tokenizer = tokenizer
        self.max_length = max_length

    def __len__(self):
        return len(self.dataframe)

    def __getitem__(self, idx):
        text = self.dataframe['text'][idx]
        label = self.dataframe['label'][idx]
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
```

3. **Load Data and Create DataLoader**

```python
# Sample data using Polars
data = pl.DataFrame({
    'text': ["I love programming", "Python is great", "I dislike bugs", "Debugging is fun"],
    'label': [1, 1, 0, 1]  # 1 for positive, 0 for negative
})

tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')
dataset = TextClassificationDataset(dataframe=data, tokenizer=tokenizer, max_length=128)
dataloader = DataLoader(dataset, batch_size=2, shuffle=True)
```

4. **Load Pre-trained BERT Model**

```python
model = BertForSequenceClassification.from_pretrained('bert-base-uncased', num_labels=2)
model.eval()
```

5. **Define Evaluation Loop**

```python
def evaluate_model(model, dataloader, device):
    model.to(device)
    model.eval()
    predictions, true_labels = [], []

    with torch.no_grad():
        for batch in dataloader:
            input_ids = batch['input_ids'].to(device)
            attention_mask = batch['attention_mask'].to(device)
            labels = batch['labels'].to(device)

            outputs = model(input_ids, attention_mask=attention_mask)
            logits = outputs.logits
            logits = logits.detach().cpu().numpy()
            label_ids = labels.to('cpu').numpy()

            predictions.extend(np.argmax(logits, axis=1).flatten())
            true_labels.extend(label_ids)

    return accuracy_score(true_labels, predictions)
```

6. **Execute Evaluation Loop**

```python
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
accuracy = evaluate_model(model, dataloader, device)
print(f'Accuracy: {accuracy}')
```

## Exercise 2: Hyperparameter Tuning & Empirical Benchmarking

In this exercise, we will perform hyperparameter tuning and benchmark the model's performance in terms of accuracy and latency.

### Hyperparameter Tuning

We will use a simple grid search to tune the `max_length` parameter of the tokenizer.

```python
from sklearn.model_selection import ParameterGrid

param_grid = {
    'max_length': [128, 256, 512]
}

best_accuracy = 0
best_params = {}

for params in ParameterGrid(param_grid):
    dataset = TextClassificationDataset(dataframe=data, tokenizer=tokenizer, max_length=params['max_length'])
    dataloader = DataLoader(dataset, batch_size=2, shuffle=True)
    accuracy = evaluate_model(model, dataloader, device)
    print(f'Params: {params}, Accuracy: {accuracy}')
    
    if accuracy > best_accuracy:
        best_accuracy = accuracy
        best_params = params

print(f'Best Params: {best_params}, Best Accuracy: {best_accuracy}')
```

### Benchmarking Performance

We will measure the latency of the model inference.

```python
import time

def benchmark_model(model, dataloader, device, num_samples=100):
    model.to(device)
    model.eval()
    latencies = []

    with torch.no_grad():
        for _ in range(num_samples):
            batch = next(iter(dataloader))
            input_ids = batch['input_ids'].to(device)
            attention_mask = batch['attention_mask'].to(device)

            start_time = time.time()
            _ = model(input_ids, attention_mask=attention_mask)
            end_time = time.time()

            latencies.append(end_time - start_time)

    return np.mean(latencies), np.std(latencies)

mean_latency, std_latency = benchmark_model(model, dataloader, device)
print(f'Mean Latency: {mean_latency}, Std Latency: {std_latency}')
```

## Exercise 3: Stress Testing, Edge Cases & Failure Mitigation

In this exercise, we will test the model on edge cases and implement guardrails to handle potential failures.

### Stress Testing

We will test the model with very long and very short texts.

```python
# Test with very long text
long_text = " ".join(["This is a very long sentence"] * 100)
long_data = pl.DataFrame({
    'text': [long_text],
    'label': [1]
})
long_dataset = TextClassificationDataset(dataframe=long_data, tokenizer=tokenizer, max_length=512)
long_dataloader = DataLoader(long_dataset, batch_size=1, shuffle=False)
long_accuracy = evaluate_model(model, long_dataloader, device)
print(f'Long Text Accuracy: {long_accuracy}')

# Test with very short text
short_text = "Hi"
short_data = pl.DataFrame({
    'text': [short_text],
    'label': [1]
})
short_dataset = TextClassificationDataset(dataframe=short_data, tokenizer=tokenizer, max_length=512)
short_dataloader = DataLoader(short_dataset, batch_size=1, shuffle=False)
short_accuracy = evaluate_model(model, short_dataloader, device)
print(f'Short Text Accuracy: {short_accuracy}')
```

### Implementing Guardrails

We will add error handling to manage potential issues during inference.

```python
def safe_evaluate_model(model, dataloader, device):
    model.to(device)
    model.eval()
    predictions, true_labels = [], []

    with torch.no_grad():
        for batch in dataloader:
            try:
                input_ids = batch['input_ids'].to(device)
                attention_mask = batch['attention_mask'].to(device)
                labels = batch['labels'].to(device)

                outputs = model(input_ids, attention_mask=attention_mask)
                logits = outputs.logits
                logits = logits.detach().cpu().numpy()
                label_ids = labels.to('cpu').numpy()

                predictions.extend(np.argmax(logits, axis=1).flatten())
                true_labels.extend(label_ids)
            except Exception as e:
                print(f'Error processing batch: {e}')
                continue

    return accuracy_score(true_labels, predictions)

safe_accuracy = safe_evaluate_model(model, dataloader, device)
print(f'Safe Accuracy: {safe_accuracy}')
```

## Verification Checklist & Quick Reference Cheat Sheet

| Method/Parameter | Description |
|------------------|-------------|
| `evaluate_model` | Evaluates the model on a given dataloader and returns accuracy. |
| `ParameterGrid`  | Used for hyperparameter tuning with grid search. |
| `benchmark_model`| Measures the mean and standard deviation of model inference latency. |
| `safe_evaluate_model` | Evaluates the model with error handling to manage potential issues. |
| `max_length`     | Hyperparameter for the maximum length of tokenized input. |
| `batch_size`     | Number of samples per batch in the dataloader. |
| `device`         | Specifies the device (CPU or GPU) for model execution. |

This lab provides a comprehensive hands-on experience with implementing evaluation loops, hyperparameter tuning, benchmarking, and handling edge cases in AI model evaluation.
