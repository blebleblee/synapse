# Operational Verification Labs: 01 Multilayer Perceptrons And Backprop

## Objective & Environment Setup

The objective of this lab is to gain hands-on experience with implementing, tuning, and verifying a multilayer perceptron (MLP) using backpropagation. This lab will guide you through the process of building a simple MLP from scratch using PyTorch, tuning its hyperparameters, benchmarking its performance, and handling edge cases.

### Environment Setup

Ensure you have a Python 3.11+ environment set up with the following packages installed:

- PyTorch
- NumPy
- Scikit-learn
- Matplotlib

You can install these packages using pip:

```bash
pip install torch numpy scikit-learn matplotlib
```

## Exercise 1: Hands-On Implementation & Pipeline Execution

In this exercise, we will implement a simple multilayer perceptron using PyTorch. The MLP will consist of an input layer, one hidden layer, and an output layer. We will use the ReLU activation function for the hidden layer and the softmax function for the output layer. The dataset we will use is the MNIST dataset, which consists of 28x28 pixel grayscale images of handwritten digits.

### Complete, Runnable Python Script

```python
import torch
import torch.nn as nn
import torch.optim as optim
import torchvision
import torchvision.transforms as transforms
import matplotlib.pyplot as plt

# Define the MLP model
class MLP(nn.Module):
    def __init__(self, input_size, hidden_size, num_classes):
        super(MLP, self).__init__()
        self.fc1 = nn.Linear(input_size, hidden_size)
        self.relu = nn.ReLU()
        self.fc2 = nn.Linear(hidden_size, num_classes)
        self.softmax = nn.Softmax(dim=1)

    def forward(self, x):
        out = self.fc1(x)
        out = self.relu(out)
        out = self.fc2(out)
        out = self.softmax(out)
        return out

# Hyperparameters
input_size = 28 * 28
hidden_size = 128
num_classes = 10
num_epochs = 5
batch_size = 100
learning_rate = 0.001

# MNIST dataset
train_dataset = torchvision.datasets.MNIST(root='./data', 
                                           train=True, 
                                           transform=transforms.ToTensor(),  
                                           download=True)

test_dataset = torchvision.datasets.MNIST(root='./data', 
                                          train=False, 
                                          transform=transforms.ToTensor())

# Data loader
train_loader = torch.utils.data.DataLoader(dataset=train_dataset, 
                                           batch_size=batch_size, 
                                           shuffle=True)

test_loader = torch.utils.data.DataLoader(dataset=test_dataset, 
                                          batch_size=batch_size, 
                                          shuffle=False)

# Initialize the model
model = MLP(input_size, hidden_size, num_classes)

# Loss and optimizer
criterion = nn.CrossEntropyLoss()
optimizer = optim.Adam(model.parameters(), lr=learning_rate)

# Training loop
total_step = len(train_loader)
loss_history = []

for epoch in range(num_epochs):
    for i, (images, labels) in enumerate(train_loader):
        # Flatten the images
        images = images.view(-1, input_size)
        
        # Forward pass
        outputs = model(images)
        loss = criterion(outputs, labels)
        
        # Backward and optimize
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
        
        loss_history.append(loss.item())
        
        if (i+1) % 100 == 0:
            print(f'Epoch [{epoch+1}/{num_epochs}], Step [{i+1}/{total_step}], Loss: {loss.item():.4f}')

# Plot loss history
plt.plot(loss_history)
plt.xlabel('Step')
plt.ylabel('Loss')
plt.title('Training Loss')
plt.show()

# Test the model
model.eval()
with torch.no_grad():
    correct = 0
    total = 0
    for images, labels in test_loader:
        images = images.view(-1, input_size)
        outputs = model(images)
        _, predicted = torch.max(outputs.data, 1)
        total += labels.size(0)
        correct += (predicted == labels).sum().item()

    print(f'Accuracy of the model on the 10000 test images: {100 * correct / total:.2f}%')
```

## Exercise 2: Hyperparameter Tuning & Empirical Benchmarking

In this exercise, we will perform hyperparameter tuning and benchmark the performance of the MLP. We will measure the accuracy and convergence curves of the model.

### Real Benchmarking Code

```python
import numpy as np

# Define a function to evaluate the model
def evaluate_model(model, test_loader):
    model.eval()
    with torch.no_grad():
        correct = 0
        total = 0
        for images, labels in test_loader:
            images = images.view(-1, input_size)
            outputs = model(images)
            _, predicted = torch.max(outputs.data, 1)
            total += labels.size(0)
            correct += (predicted == labels).sum().item()
        return 100 * correct / total

# Hyperparameter tuning
learning_rates = [0.001, 0.0001, 0.00001]
hidden_sizes = [64, 128, 256]
num_epochs_list = [5, 10, 15]

best_accuracy = 0
best_params = {}

for lr in learning_rates:
    for hs in hidden_sizes:
        for epochs in num_epochs_list:
            model = MLP(input_size, hs, num_classes)
            criterion = nn.CrossEntropyLoss()
            optimizer = optim.Adam(model.parameters(), lr=lr)
            
            for epoch in range(epochs):
                for images, labels in train_loader:
                    images = images.view(-1, input_size)
                    outputs = model(images)
                    loss = criterion(outputs, labels)
                    optimizer.zero_grad()
                    loss.backward()
                    optimizer.step()
            
            accuracy = evaluate_model(model, test_loader)
            print(f'Learning Rate: {lr}, Hidden Size: {hs}, Epochs: {epochs}, Accuracy: {accuracy:.2f}%')
            
            if accuracy > best_accuracy:
                best_accuracy = accuracy
                best_params = {'learning_rate': lr, 'hidden_size': hs, 'num_epochs': epochs}

print(f'Best Parameters: {best_params}, Best Accuracy: {best_accuracy:.2f}%')
```

## Exercise 3: Stress Testing, Edge Cases & Failure Mitigation

In this exercise, we will test the model under various edge cases and implement guardrails to handle potential failures.

### Reproducing Failure Modes, Testing Edge Cases, and Implementing Guardrails

```python
# Test with a single image
def test_single_image(model, image):
    model.eval()
    with torch.no_grad():
        image = image.view(-1, input_size)
        outputs = model(image)
        _, predicted = torch.max(outputs.data, 1)
        return predicted.item()

# Load a single test image
single_image, single_label = test_dataset[0]
predicted_label = test_single_image(model, single_image)
print(f'Predicted Label: {predicted_label}, True Label: {single_label}')

# Test with an invalid input
def test_invalid_input(model, invalid_input):
    try:
        model.eval()
        with torch.no_grad():
            outputs = model(invalid_input)
            _, predicted = torch.max(outputs.data, 1)
            return predicted.item()
    except Exception as e:
        print(f'Error: {e}')
        return None

# Create an invalid input (wrong shape)
invalid_input = torch.randn(1, 28, 28)  # Missing the flatten step
predicted_label = test_invalid_input(model, invalid_input)

# Implement guardrails
def safe_test_single_image(model, image):
    if image.shape != (1, 28, 28):
        raise ValueError("Input image must have shape (1, 28, 28)")
    return test_single_image(model, image)

# Test with a valid input
valid_input = single_image.unsqueeze(0)  # Add batch dimension
predicted_label = safe_test_single_image(model, valid_input)
print(f'Predicted Label: {predicted_label}, True Label: {single_label}')

# Test with an invalid input
invalid_input = torch.randn(1, 28, 28)  # Missing the flatten step
predicted_label = safe_test_single_image(model, invalid_input)
```

## Verification Checklist & Quick Reference Cheat Sheet

### Essential Python Methods, Parameters, and Verification Flags

| Method/Parameter | Description |
|------------------|-------------|
| `MLP`            | Class defining the multilayer perceptron model. |
| `forward`        | Method defining the forward pass of the model. |
| `nn.Linear`      | Linear layer in the neural network. |
| `nn.ReLU`        | ReLU activation function. |
| `nn.Softmax`     | Softmax activation function for output layer. |
| `nn.CrossEntropyLoss` | Loss function for classification tasks. |
| `optim.Adam`     | Adam optimizer for training the model. |
| `evaluate_model` | Function to evaluate the model on a test dataset. |
| `test_single_image` | Function to test a single image. |
| `test_invalid_input` | Function to test an invalid input. |
| `safe_test_single_image` | Function to test a single image with guardrails. |

### Verification Flags

- `loss.item()` : Retrieves the scalar value of the loss tensor.
- `predicted.item()` : Retrieves the scalar value of the predicted label tensor.
- `accuracy` : Calculated accuracy of the model on the test dataset.

By completing this lab, you should have a solid understanding of implementing, tuning, and verifying a multilayer perceptron using backpropagation. This hands-on experience will help you build a strong foundation in deep learning and neural network architectures.
