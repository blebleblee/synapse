Operational Verification Labs: 02 Loss Functions And Gradient Descent
===========================================================

### Objective & Environment Setup

This lab guides hands-on AI engineers and practitioners through the implementation and verification of loss functions and gradient descent. To complete this lab, you will need a Python 3.11+ environment with the following packages installed:

* PyTorch
* HuggingFace
* NumPy
* Scikit-learn
* Ollama
* Polars

Additionally, you will need to configure the API for your chosen deep learning framework.

### Exercise 1: Hands-On Implementation & Pipeline Execution

**Implementing Loss Functions and Gradient Descent**

```python
import torch
import torch.nn as nn
import torch.optim as optim

# Define a simple neural network model
class Net(nn.Module):
    def __init__(self):
        super(Net, self).__init__()
        self.fc1 = nn.Linear(5, 10)  # input layer (5) -> hidden layer (10)
        self.fc2 = nn.Linear(10, 5)  # hidden layer (10) -> output layer (5)

    def forward(self, x):
        x = torch.relu(self.fc1(x))  # activation function for hidden layer
        x = self.fc2(x)
        return x

# Initialize the model, loss function, and optimizer
model = Net()
criterion = nn.MSELoss()
optimizer = optim.SGD(model.parameters(), lr=0.01)

# Generate some random input data
input_data = torch.randn(10, 5)

# Forward pass
output = model(input_data)
loss = criterion(output, torch.randn(10, 5))

# Backward pass
optimizer.zero_grad()
loss.backward()
optimizer.step()
```

This code defines a simple neural network model, initializes the loss function and optimizer, and performs a forward and backward pass using the PyTorch API.

### Exercise 2: Hyperparameter Tuning & Empirical Benchmarking

**Hyperparameter Tuning and Benchmarking**

```python
import numpy as np
import time
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

# Generate some random data for benchmarking
np.random.seed(0)
X = np.random.rand(1000, 5)
y = np.random.randint(0, 2, 1000)

# Split the data into training and testing sets
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Define a function to train the model and evaluate its performance
def train_and_evaluate(model, X_train, y_train, X_test, y_test):
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    return accuracy

# Define a range of hyperparameters to tune
hyperparameters = {
    'learning_rate': [0.01, 0.1, 1.0],
    'batch_size': [10, 50, 100]
}

# Perform hyperparameter tuning and benchmarking
best_accuracy = 0
best_hyperparameters = None
for learning_rate in hyperparameters['learning_rate']:
    for batch_size in hyperparameters['batch_size']:
        model = Net()
        optimizer = optim.SGD(model.parameters(), lr=learning_rate)
        model.fit(X_train, y_train, batch_size=batch_size)
        accuracy = accuracy_score(y_test, model.predict(X_test))
        if accuracy > best_accuracy:
            best_accuracy = accuracy
            best_hyperparameters = {'learning_rate': learning_rate, 'batch_size': batch_size}

print(f'Best hyperparameters: {best_hyperparameters}')
print(f'Best accuracy: {best_accuracy:.2f}%')
```

This code defines a function to train the model and evaluate its performance, and then performs hyperparameter tuning and benchmarking using a range of hyperparameters.

### Exercise 3: Stress Testing, Edge Cases & Failure Mitigation

**Stress Testing and Edge Cases**

```python
import torch
import torch.nn as nn
import torch.optim as optim

# Define a simple neural network model
class Net(nn.Module):
    def __init__(self):
        super(Net, self).__init__()
        self.fc1 = nn.Linear(5, 10)  # input layer (5) -> hidden layer (10)
        self.fc2 = nn.Linear(10, 5)  # hidden layer (10) -> output layer (5)

    def forward(self, x):
        x = torch.relu(self.fc1(x))  # activation function for hidden layer
        x = self.fc2(x)
        return x

# Initialize the model, loss function, and optimizer
model = Net()
criterion = nn.MSELoss()
optimizer = optim.SGD(model.parameters(), lr=0.01)

# Generate some random input data
input_data = torch.randn(1000, 5)

# Perform a forward pass with a large input size
output = model(input_data)

# Check for NaN values in the output
if torch.isnan(output).any():
    print('NaN values detected in output')
else:
    print('No NaN values detected in output')

# Perform a backward pass with a large input size
optimizer.zero_grad()
loss = criterion(output, torch.randn(1000, 5))
loss.backward()
if torch.isnan(loss).any():
    print('NaN values detected in loss')
else:
    print('No NaN values detected in loss')
```

This code defines a simple neural network model and performs a forward and backward pass with a large input size, checking for NaN values in the output and loss.

### Verification Checklist & Quick Reference Cheat Sheet

| **Method** | **Parameter** | **Verification Flag** |
| --- | --- | --- |
| `torch.nn.Linear` | `in_features`, `out_features` | `None` |
| `torch.nn.ReLU` | `None` | `None` |
| `torch.optim.SGD` | `lr`, `momentum` | `None` |
| `torch.nn.MSELoss` | `None` | `None` |
| `model.fit` | `X_train`, `y_train`, `batch_size` | `None` |
| `model.predict` | `X_test` | `None` |
| `accuracy_score` | `y_test`, `y_pred` | `None` |

Note: This is not an exhaustive list of methods, parameters, and verification flags, but rather a selection of key concepts and techniques used in this lab.
