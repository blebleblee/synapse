# Operational Verification Labs: 01 Multilayer Perceptrons And Backpropagation

## Objective & Environment Setup

This lab aims to implement, verify, and optimize a multilayer perceptron (MLP) using backpropagation. Through this exercise, you will build a simple neural network from scratch, train it on a dataset, and evaluate its performance. The lab utilizes Python 3.11+ alongside PyTorch, NumPy, and Scikit-learn.

### Environment Setup

Ensure your environment includes the following:

- Python 3.11+
- PyTorch
- NumPy
- Scikit-learn

Install the required packages using pip:

```bash
pip install torch numpy scikit-learn
```

## Exercise 1: Hands-On Implementation & Pipeline Execution

In this exercise, we will implement a simple multilayer perceptron using PyTorch. The MLP consists of an input layer, one hidden layer, and an output layer. The ReLU activation function is used for the hidden layer, and the softmax function is applied to the output layer. The Iris dataset, a classic dataset for classification tasks, will serve as our training and testing data.

### Complete, Runnable Python Script

```python
import torch
import torch.nn as nn
import torch.optim as optim
from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder
from sklearn.preprocessing import StandardScaler
import numpy as np

# Load and preprocess the Iris dataset
iris = load_iris()
X = iris.data
y = iris.target.reshape(-1, 1)

# One-hot encode the target variable
encoder = OneHotEncoder(sparse=False)
y_encoded = encoder.fit_transform(y)

# Standardize the features
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# Split the dataset into training and testing sets
X_train, X_test, y_train, y_test = train_test_split(X_scaled, y_encoded, test_size=0.2, random_state=42)

# Convert to PyTorch tensors
X_train_tensor = torch.tensor(X_train, dtype=torch.float32)
y_train_tensor = torch.tensor(y_train, dtype=torch.float32)
X_test_tensor = torch.tensor(X_test, dtype=torch.float32)
y_test_tensor = torch.tensor(y_test, dtype=torch.float32)

# Define the MLP model
class MLP(nn.Module):
    def __init__(self, input_size, hidden_size, output_size):
        super(MLP, self).__init__()
        self.fc1 = nn.Linear(input_size, hidden_size)
        self.relu = nn.ReLU()
        self.fc2 = nn.Linear(hidden_size, output_size)
        self.softmax = nn.Softmax(dim=1)

    def forward(self, x):
        out = self.fc1(x)
        out = self.relu(out)
        out = self.fc2(out)
        out = self.softmax(out)
        return out

# Initialize the model, loss function, and optimizer
input_size = X_train.shape[1]
hidden_size = 10
output_size = y_train.shape[1]
model = MLP(input_size, hidden_size, output_size)
criterion = nn.CrossEntropyLoss()
optimizer = optim.SGD(model.parameters(), lr=0.01)

# Training loop
num_epochs = 100
for epoch in range(num_epochs):
    # Forward pass
    outputs = model(X_train_tensor)
    loss = criterion(outputs, torch.argmax(y_train_tensor, dim=1))

    # Backward pass and optimization
    optimizer.zero_grad()
    loss.backward()
    optimizer.step()

    if (epoch+1) % 10 == 0:
        print(f'Epoch [{epoch+1}/{num_epochs}], Loss: {loss.item():.4f}')

# Evaluation
model.eval()
with torch.no_grad():
    outputs = model(X_test_tensor)
    _, predicted = torch.max(outputs.data, 1)
    _, true_labels = torch.max(y_test_tensor, 1)
    accuracy = (predicted == true_labels).sum().item() / len(y_test_tensor)
    print(f'Accuracy: {accuracy:.4f}')
```

## Exercise 2: Hyperparameter Tuning & Empirical Benchmarking

In this exercise, we will perform hyperparameter tuning and benchmark the performance of our MLP model. We will measure the accuracy and convergence curves of the model.

### Real Benchmarking Code

```python
import matplotlib.pyplot as plt

# Hyperparameter tuning
learning_rates = [0.001, 0.01, 0.1]
hidden_sizes = [5, 10, 20]
results = {}

for lr in learning_rates:
    for hs in hidden_sizes:
        model = MLP(input_size, hs, output_size)
        criterion = nn.CrossEntropyLoss()
        optimizer = optim.SGD(model.parameters(), lr=lr)
        
        losses = []
        for epoch in range(num_epochs):
            outputs = model(X_train_tensor)
            loss = criterion(outputs, torch.argmax(y_train_tensor, dim=1))
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            losses.append(loss.item())
        
        with torch.no_grad():
            outputs = model(X_test_tensor)
            _, predicted = torch.max(outputs.data, 1)
            _, true_labels = torch.max(y_test_tensor, 1)
            accuracy = (predicted == true_labels).sum().item() / len(y_test_tensor)
        
        results[(lr, hs)] = {'accuracy': accuracy, 'losses': losses}

# Plotting convergence curves
plt.figure(figsize=(12, 6))
for (lr, hs), data in results.items():
    plt.plot(data['losses'], label=f'LR={lr}, HS={hs}')
plt.xlabel('Epochs')
plt.ylabel('Loss')
plt.title('Convergence Curves')
plt.legend()
plt.show()

# Print accuracies
for (lr, hs), data in results.items():
    print(f'Learning Rate: {lr}, Hidden Size: {hs}, Accuracy: {data["accuracy"]:.4f}')
```

## Exercise 3: Stress Testing, Edge Cases & Failure Mitigation

In this exercise, we will test the model on edge cases and implement guardrails to handle potential failures.

### Reproducing Failure Modes, Testing Edge Cases, and Implementing Guardrails

```python
# Testing edge cases
def test_edge_cases(model, X_test_tensor, y_test_tensor):
    # Test with a single sample
    single_sample = X_test_tensor[0].unsqueeze(0)
    with torch.no_grad():
        output = model(single_sample)
        _, predicted = torch.max(output.data, 1)
        _, true_label = torch.max(y_test_tensor[0], dim=0)
        print(f'Single Sample Prediction: {predicted.item()}, True Label: {true_label.item()}')

    # Test with an invalid input (e.g., incorrect number of features)
    invalid_input = torch.randn(1, input_size + 1)
    try:
        with torch.no_grad():
            output = model(invalid_input)
    except RuntimeError as e:
        print(f'Error with invalid input: {e}')

# Implementing guardrails
def predict_with_guardrails(model, input_tensor):
    if input_tensor.shape[1] != input_size:
        raise ValueError(f'Input tensor must have {input_size} features')
    with torch.no_grad():
        output = model(input_tensor)
        _, predicted = torch.max(output.data, 1)
    return predicted.item()

# Run edge case tests
test_edge_cases(model, X_test_tensor, y_test_tensor)

# Test guardrails
try:
    print(f'Guardrails Prediction: {predict_with_guardrails(model, X_test_tensor[0].unsqueeze(0))}')
    print(f'Guardrails Prediction with invalid input: {predict_with_guardrails(model, torch.randn(1, input_size + 1))}')
except ValueError as e:
    print(f'Guardrails Error: {e}')
```

## Verification
