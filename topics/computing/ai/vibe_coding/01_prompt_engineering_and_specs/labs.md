# Operational Verification Labs

## Objective & Environment Setup

To complete these labs, you will need a Python 3.11+ environment with the following packages installed: PyTorch, Hugging Face Transformers, NumPy, Scikit-learn, Ollama, and Polars. Additionally, configure your API keys and credentials for the respective services.

### Required Packages

PyTorch can be installed using the command `pip install torch torchvision`. Hugging Face Transformers is installed via `pip install transformers`. NumPy is installed with `pip install numpy`. Scikit-learn is installed using `pip install scikit-learn`. Ollama is installed with `pip install ollama`, and Polars is installed using `pip install polars`.

### API Configuration

Setting up your API keys and credentials involves creating accounts, generating API keys, and configuring environment variables for the respective services.

## Exercise 1: Hands-On Implementation & Pipeline Execution

Implement the core prompt/model/algorithm for this topic using a real, executable Python script. Ensure the script has no placeholders and is fully runnable.

### Example Code

```python
import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from ollama import OllamaModel
import pandas as pd

# Load pre-trained model and tokenizer
model_name = "distilbert-base-uncased"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSequenceClassification.from_pretrained(model_name)

# Load dataset and preprocess
dataset = pd.read_csv("data.csv")
le = LabelEncoder()
dataset["label"] = le.fit_transform(dataset["label"])

# Split dataset into training and testing sets
train_text, test_text, train_labels, test_labels = train_test_split(dataset["text"], dataset["label"], test_size=0.2, random_state=42)

# Create data loaders
train_encodings = tokenizer(train_text.tolist(), truncation=True, padding=True, max_length=512, return_tensors="pt")
test_encodings = tokenizer(test_text.tolist(), truncation=True, padding=True, max_length=512, return_tensors="pt")

train_dataset = torch.utils.data.TensorDataset(train_encodings["input_ids"], train_encodings["attention_mask"], torch.tensor(train_labels))
test_dataset = torch.utils.data.TensorDataset(test_encodings["input_ids"], test_encodings["attention_mask"], torch.tensor(test_labels))

train_dataloader = torch.utils.data.DataLoader(train_dataset, batch_size=32, shuffle=True)
test_dataloader = torch.utils.data.DataLoader(test_dataset, batch_size=32, shuffle=False)

# Train model
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model.to(device)
criterion = torch.nn.CrossEntropyLoss()
optimizer = torch.optim.Adam(model.parameters(), lr=1e-5)

for epoch in range(5):
    model.train()
    total_loss = 0
    for batch in train_dataloader:
        input_ids, attention_mask, labels = [t.to(device) for t in batch]
        optimizer.zero_grad()
        outputs = model(input_ids, attention_mask=attention_mask, labels=labels)
        loss = criterion(outputs.logits, labels)
        loss.backward()
        optimizer.step()
        total_loss += loss.item()
    print(f"Epoch {epoch+1}, Loss: {total_loss / len(train_dataloader)}")

model.eval()
test_loss = 0
correct = 0
with torch.no_grad():
    for batch in test_dataloader:
        input_ids, attention_mask, labels = [t.to(device) for t in batch]
        outputs = model(input_ids, attention_mask=attention_mask, labels=labels)
        loss = criterion(outputs.logits, labels)
        test_loss += loss.item()
        _, predicted = torch.max(outputs.logits, dim=1)
        correct += (predicted == labels).sum().item()

accuracy = correct / len(test_labels)
print(f"Test Accuracy: {accuracy:.4f}")
```

## Exercise 2: Hyperparameter Tuning & Empirical Benchmarking

Measure the accuracy, latency distributions, token costs, or convergence curves of the implemented model. Use real benchmarking code to evaluate the performance.

### Example Code

```python
import time
import numpy as np
from sklearn.model_selection import GridSearchCV
from sklearn.metrics import accuracy_score

# Define hyperparameter tuning space
param_grid = {
    "learning_rate": [1e-5, 1e-4, 1e-3],
    "batch_size": [16, 32, 64],
    "epochs": [5, 10, 15]
}

# Perform grid search
grid_search = GridSearchCV(model, param_grid, cv=5, scoring="accuracy")
grid_search.fit(train_text, train_labels)

# Get best hyperparameters and evaluate on test set
best_params = grid_search.best_params_
best_model = grid_search.best_estimator_
test_accuracy = accuracy_score(test_labels, best_model.predict(test_text))
print(f"Best Hyperparameters: {best_params}")
print(f"Test Accuracy: {test_accuracy:.4f}")

# Measure latency distributions
latencies = []
for batch in test_dataloader:
    input_ids, attention_mask, labels = [t.to(device) for t in batch]
    start_time = time.time()
    outputs = best_model(input_ids, attention_mask=attention_mask, labels=labels)
    end_time = time.time()
    latencies.append(end_time - start_time)

latency_distribution = np.array(latencies)
print(f"Latency Distribution: Mean = {latency_distribution.mean():.4f}, Std Dev = {latency_distribution.std():.4f}")
```

## Exercise 3: Stress Testing, Edge Cases & Failure Mitigation

Reproduce failure modes, test edge cases, and implement guardrails or error handling to ensure robustness.

### Example Code

```python
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder

# Load dataset and preprocess
dataset = pd.read_csv("data.csv")
le = LabelEncoder()
dataset["label"] = le.fit_transform(dataset["label"])

# Split dataset into training and testing sets
train_text, test_text, train_labels, test_labels = train_test_split(dataset["text"], dataset["label"], test_size=0.2, random_state=42)

# Create data loaders
train_encodings = tokenizer(train_text.tolist(), truncation=True, padding=True, max_length=512, return_tensors="pt")
test_encodings = tokenizer(test_text.tolist(), truncation=True, padding=True, max_length=512, return_tensors="pt")

train_dataset = torch.utils.data.TensorDataset(train_encodings["input_ids"], train_encodings["attention_mask"], torch.tensor(train_labels))
test_dataset = torch.utils.data.TensorDataset(test_encodings["input_ids"], test_encodings["attention_mask"], torch.tensor(test_labels))

train_dataloader = torch.utils.data.DataLoader(train_dataset, batch_size=32, shuffle=True)
test_dataloader = torch.utils.data.DataLoader(test_dataset, batch_size=32, shuffle=False)

# Implement guardrails for edge cases
def preprocess_text(text):
    try:
        input_ids = tokenizer.encode_plus(text, add_special_tokens=True, max_length=512, return_attention_mask=True, return_tensors="pt")
        return input_ids["input_ids"], input_ids["attention_mask"]
    except Exception as e:
        print(f"Error preprocessing text: {e}")
        return None, None

# Implement error handling for failure modes
try:
    model.train()
    for batch in train_dataloader:
        input_ids, attention_mask, labels = [t.to(device) for t in batch]
        optimizer.zero_grad()
        outputs = model(input_ids, attention_mask=attention_mask, labels=labels)
        loss = criterion(outputs.logits, labels)
        loss.backward()
        optimizer.step()
except Exception as e:
    print(f"Error training model: {e}")
```

These labs provide hands-on experience with prompt engineering, model implementation, and pipeline execution. By completing these exercises, you will gain a deeper understanding of the underlying concepts and develop practical skills in AI coding.
