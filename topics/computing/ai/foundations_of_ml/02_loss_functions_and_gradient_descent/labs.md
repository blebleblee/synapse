# Operational Verification Labs: 02 Loss Functions And Gradient Descent

## Objective & Environment Setup

The objective of this lab is to gain hands-on experience with implementing and verifying loss functions and gradient descent algorithms. This lab will guide you through the process of creating a simple neural network, defining loss functions, and applying gradient descent to minimize the loss. We will use PyTorch, a popular deep learning library, for this purpose.

### Environment Setup

Ensure you have Python 3.11+ installed on your system. You can install the required packages using pip:

```bash
pip install torch numpy scikit-learn matplotlib
```

## Exercise 1: Hands-On Implementation & Pipeline Execution

In this exercise, we will implement a simple linear regression model using PyTorch. We will define a mean squared error (MSE) loss function and use gradient descent to minimize the loss.

### Complete, Runnable Python Script

```python
import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
import matplotlib.pyplot as plt

# Generate synthetic data
np.random.seed(0)
X = 2 * np.random.rand(100, 1)
y = 4 + 3 * X + np.random.randn(100, 1)

# Convert to PyTorch tensors
X_tensor = torch.tensor(X, dtype=torch.float32)
y_tensor = torch.tensor(y, dtype=torch.float32)

# Define a simple linear model
class LinearModel(nn.Module):
    def __init__(self):
        super(LinearModel, self).__init__()
        self.linear = nn.Linear(1, 1)  # One input and one output

    def forward(self, x):
        return self.linear(x)

# Instantiate the model, define the loss function, and the optimizer
model = LinearModel()
criterion = nn.MSELoss()
optimizer = optim.SGD(model.parameters(), lr=0.01)

# Training loop
num_epochs = 100
loss_history = []

for epoch in range(num_epochs):
    # Forward pass: Compute predicted y by passing X to the model
    y_pred = model(X_tensor)

    # Compute and store the loss
    loss = criterion(y_pred, y_tensor)
    loss_history.append(loss.item())

    # Zero gradients, perform a backward pass, and update the weights
    optimizer.zero_grad()
    loss.backward()
    optimizer.step()

    if (epoch+1) % 10 == 0:
        print(f'Epoch [{epoch+1}/{num_epochs}], Loss: {loss.item():.4f}')

# Plot the loss over epochs
plt.plot(loss_history)
plt.xlabel('Epoch')
plt.ylabel('Loss')
plt.title('Training Loss Over Epochs')
plt.show()

# Plot the fitted line
predicted = model(X_tensor).detach().numpy()
plt.scatter(X, y, label='Original data')
plt.plot(X, predicted, color='red', label='Fitted line')
plt.xlabel('X')
plt.ylabel('y')
plt.title('Linear Regression Fit')
plt.legend()
plt.show()
```

## Exercise 2: Hyperparameter Tuning & Empirical Benchmarking

In this exercise, we will perform hyperparameter tuning by adjusting the learning rate and the number of epochs. We will also benchmark the model's performance by measuring the final loss and plotting the convergence curve.

### Real Benchmarking Code

```python
import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
import matplotlib.pyplot as plt

# Generate synthetic data
np.random.seed(0)
X = 2 * np.random.rand(100, 1)
y = 4 + 3 * X + np.random.randn(100, 1)

# Convert to PyTorch tensors
X_tensor = torch.tensor(X, dtype=torch.float32)
y_tensor = torch.tensor(y, dtype=torch.float32)

# Define a simple linear model
class LinearModel(nn.Module):
    def __init__(self):
        super(LinearModel, self).__init__()
        self.linear = nn.Linear(1, 1)  # One input and one output

    def forward(self, x):
        return self.linear(x)

# Hyperparameter tuning
learning_rates = [0.001, 0.01, 0.1]
num_epochs = 100

for lr in learning_rates:
    model = LinearModel()
    criterion = nn.MSELoss()
    optimizer = optim.SGD(model.parameters(), lr=lr)

    loss_history = []

    for epoch in range(num_epochs):
        y_pred = model(X_tensor)
        loss = criterion(y_pred, y_tensor)
        loss_history.append(loss.item())

        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

    plt.plot(loss_history, label=f'LR={lr}')

plt.xlabel('Epoch')
plt.ylabel('Loss')
plt.title('Convergence Curves for Different Learning Rates')
plt.legend()
plt.show()
```

## Exercise 3: Stress Testing, Edge Cases & Failure Mitigation

In this exercise, we will test the model with edge cases, such as very small or very large input values, and implement guardrails to handle potential failures.

### Reproducing Failure Modes, Testing Edge Cases, and Implementing Guardrails

```python
import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
import matplotlib.pyplot as plt

# Generate synthetic data
np.random.seed(0)
X = 2 * np.random.rand(100, 1)
y = 4 + 3 * X + np.random.randn(100, 1)

# Convert to PyTorch tensors
X_tensor = torch.tensor(X, dtype=torch.float32)
y_tensor = torch.tensor(y, dtype=torch.float32)

# Define a simple linear model
class LinearModel(nn.Module):
    def __init__(self):
        super(LinearModel, self).__init__()
        self.linear = nn.Linear(1, 1)  # One input and one output

    def forward(self, x):
        return self.linear(x)

# Instantiate the model, define the loss function, and the optimizer
model = LinearModel()
criterion = nn.MSELoss()
optimizer = optim.SGD(model.parameters(), lr=0.01)

# Training loop with guardrails
num_epochs = 100
loss_history = []

for epoch in range(num_epochs):
    y_pred = model(X_tensor)
    loss = criterion(y_pred, y_tensor)
    loss_history.append(loss.item())

    optimizer.zero_grad()
    loss.backward()
    optimizer.step()

    # Guardrail: Check for NaN or Inf loss
    if torch.isnan(loss) or torch.isinf(loss):
        print(f'Loss became NaN or Inf at epoch {epoch+1}. Stopping training.')
        break

    if (epoch+1) % 10 == 0:
        print(f'Epoch [{epoch+1}/{num_epochs}], Loss: {loss.item():.4f}')

# Plot the loss over epochs
plt.plot(loss_history)
plt.xlabel('Epoch')
plt.ylabel('Loss')
plt.title('Training Loss Over Epochs')
plt.show()

# Test with edge cases
edge_cases = np.array([[-10], [10]])
edge_cases_tensor = torch.tensor(edge_cases, dtype=torch.float32)
predicted_edge_cases = model(edge_cases_tensor).detach().numpy()

plt.scatter(X, y, label='Original data')
plt.plot(X, predicted, color='red', label='Fitted line')
plt.scatter(edge_cases, predicted_edge_cases, color='green', label='Edge cases')
plt.xlabel('X')
plt.ylabel('y')
plt.title('Linear Regression Fit with Edge Cases')
plt.legend()
plt.show()
```

## Verification Checklist & Quick Reference Cheat Sheet

| Method/Parameter | Description |
|------------------|-------------|
| `torch.tensor`   | Creates a tensor from a NumPy array. |
| `nn.Linear`      | Defines a linear layer in the neural network. |
| `nn.MSELoss`     | Mean squared error loss function. |
| `optim.SGD`      | Stochastic gradient descent optimizer. |
| `model.forward`  | Defines the forward pass of the model. |
| `loss.backward`  | Computes the gradient of the loss with respect to the model parameters. |
| `optimizer.step` | Updates the model parameters based on the computed gradients. |
| `torch.isnan`    | Checks if the tensor contains NaN values. |
| `torch.isinf`    | Checks if the tensor contains Inf values. |

This lab provides a comprehensive hands-on experience with implementing and verifying loss functions and gradient descent algorithms using PyTorch. By following the exercises, you will gain a deeper understanding of these fundamental concepts in machine learning.
