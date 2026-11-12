# Operational Verification Labs: 02 Loss Functions And Gradient Descent

## Objective & Environment Setup

This lab aims to provide hands-on experience with implementing and verifying loss functions and gradient descent algorithms in a machine learning context. Through this lab, you will build a simple neural network, define loss functions, and apply gradient descent to optimize the model. We will use Python 3.11+ with the PyTorch library, a popular choice for deep learning tasks.

### Environment Setup

Ensure you have the following environment setup:

- **Python 3.11+**: Install Python from the [official website](https://www.python.org/downloads/).
- **PyTorch**: Install PyTorch by following the instructions on the [official PyTorch website](https://pytorch.org/get-started/locally/).
- **NumPy**: Install NumPy using pip:
  ```bash
  pip install numpy
  ```
- **Matplotlib**: Install Matplotlib for plotting:
  ```bash
  pip install matplotlib
  ```

## Exercise 1: Hands-On Implementation & Pipeline Execution

In this exercise, we will implement a simple neural network using PyTorch, define a loss function, and apply gradient descent to optimize the model.

### Complete, Runnable Python Script

```python
import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
import matplotlib.pyplot as plt

# Generate synthetic data
np.random.seed(0)
X = np.random.rand(100, 1) * 10
y = 2 * X + 1 + np.random.randn(100, 1) * 2

# Convert to PyTorch tensors
X_tensor = torch.tensor(X, dtype=torch.float32)
y_tensor = torch.tensor(y, dtype=torch.float32)

# Define a simple linear model
class LinearModel(nn.Module):
    def __init__(self):
        super(LinearModel, self).__init__()
        self.linear = nn.Linear(1, 1)

    def forward(self, x):
        return self.linear(x)

# Instantiate the model, define the loss function, and optimizer
model = LinearModel()
criterion = nn.MSELoss()
optimizer = optim.SGD(model.parameters(), lr=0.01)

# Training loop
num_epochs = 100
losses = []

for epoch in range(num_epochs):
    # Forward pass
    outputs = model(X_tensor)
    loss = criterion(outputs, y_tensor)
    losses.append(loss.item())

    # Backward pass and optimization
    optimizer.zero_grad()
    loss.backward()
    optimizer.step()

    if (epoch+1) % 10 == 0:
        print(f'Epoch [{epoch+1}/{num_epochs}], Loss: {loss.item():.4f}')

# Plot the loss curve
plt.plot(losses)
plt.xlabel('Epoch')
plt.ylabel('Loss')
plt.title('Training Loss Curve')
plt.show()

# Plot the fitted line
predicted = model(X_tensor).detach().numpy()
plt.scatter(X, y, label='Original data')
plt.plot(X, predicted, color='red', label='Fitted line')
plt.xlabel('X')
plt.ylabel('y')
plt.title('Fitted Line')
plt.legend()
plt.show()
```

### Explanation

We generate synthetic data for a simple linear relationship \( y = 2x + 1 \) with some added noise. We define a simple linear model using PyTorch's `nn.Module`. The Mean Squared Error (MSE) is used as the loss function, and Stochastic Gradient Descent (SGD) is the optimizer. The training loop involves forward and backward passes, loss computation, and parameter updates. Finally, we visualize the training loss curve and the fitted line to assess the model's performance.

## Exercise 2: Hyperparameter Tuning & Empirical Benchmarking

In this exercise, we will benchmark the model's performance by tuning hyperparameters such as learning rate and number of epochs.

### Real Benchmarking Code

```python
import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
import matplotlib.pyplot as plt

# Generate synthetic data
np.random.seed(0)
X = np.random.rand(100, 1) * 10
y = 2 * X + 1 + np.random.randn(100, 1) * 2

# Convert to PyTorch tensors
X_tensor = torch.tensor(X, dtype=torch.float32)
y_tensor = torch.tensor(y, dtype=torch.float32)

# Define a simple linear model
class LinearModel(nn.Module):
    def __init__(self):
        super(LinearModel, self).__init__()
        self.linear = nn.Linear(1, 1)

    def forward(self, x):
        return self.linear(x)

# Hyperparameter tuning
learning_rates = [0.001, 0.01, 0.1]
num_epochs = 100

for lr in learning_rates:
    model = LinearModel()
    criterion = nn.MSELoss()
    optimizer = optim.SGD(model.parameters(), lr=lr)

    losses = []

    for epoch in range(num_epochs):
        outputs = model(X_tensor)
        loss = criterion(outputs, y_tensor)
        losses.append(loss.item())

        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

    plt.plot(losses, label=f'LR={lr}')

plt.xlabel('Epoch')
plt.ylabel('Loss')
plt.title('Training Loss Curves for Different Learning Rates')
plt.legend()
plt.show()
```

### Explanation

We test different learning rates to observe their impact on the training loss. By plotting the training loss curves for each learning rate, we can compare their performance and choose the most effective one.

## Exercise 3: Stress Testing, Edge Cases & Failure Mitigation

In this exercise, we will test the model's robustness by introducing edge cases and implementing guardrails or error handling.

### Reproducing Failure Modes, Testing Edge Cases, and Implementing Guardrails

```python
import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
import matplotlib.pyplot as plt

# Generate synthetic data
np.random.seed(0)
X = np.random.rand(100, 1) * 10
y = 2 * X + 1 + np.random.randn(100, 1) * 2

# Convert to PyTorch tensors
X_tensor = torch.tensor(X, dtype=torch.float32)
y_tensor = torch.tensor(y, dtype=torch.float32)

# Define a simple linear model
class LinearModel(nn.Module):
    def __init__(self):
        super(LinearModel, self).__init__()
        self.linear = nn.Linear(1, 1)

    def forward(self, x):
        return self.linear(x)

# Edge case: Empty input
def test_empty_input(model, criterion):
    try:
        empty_input = torch.tensor([], dtype=torch.float32).view(0, 1)
        outputs = model(empty_input)
        loss = criterion(outputs, torch.tensor([], dtype=torch.float32).view(0, 1))
        print(f'Loss for empty input: {loss.item()}')
    except Exception as e:
        print(f'Error for empty input: {e}')

# Edge case: NaN values in input
def test_nan_input(model, criterion):
    try:
        nan_input = torch.tensor([[np.nan]], dtype=torch.float32)
        outputs = model(nan_input)
        loss = criterion(outputs, torch.tensor([[np.nan]], dtype=torch.float32))
        print(f'Loss for NaN input: {loss.item()}')
    except Exception as e:
        print(f'Error for NaN input: {e}')

# Instantiate the model, define the loss function, and optimizer
model = LinearModel()
criterion = nn.MSELoss()
optimizer = optim.SGD(model.parameters(), lr=0.01)

# Training loop
num_epochs = 100
losses = []

for epoch in range(num_epochs):
    outputs = model(X_tensor)
    loss = criterion(outputs, y_tensor)
    losses.append(loss.item())

    optimizer.zero_grad()
    loss.backward()
    optimizer.step()

# Test edge cases
test_empty_input(model, criterion)
test_nan_input(model, criterion)
```

### Explanation

We introduce edge cases such as empty inputs and inputs containing NaN values to test the model's robustness. By implementing guardrails and error handling, we ensure the model can gracefully handle unexpected inputs.
