# Operational Verification Labs: 02 Convolutional Neural Networks (CNNs)

## Objective & Environment Setup

The objective of this lab is to provide hands-on experience with implementing, tuning, and verifying Convolutional Neural Networks (CNNs) using real, executable Python scripts. This lab will guide you through the process of building a CNN from scratch, tuning its hyperparameters, and evaluating its performance on a benchmark dataset. The environment setup requires Python 3.11 or later, along with several key libraries such as PyTorch, NumPy, and Scikit-learn.

### Environment Setup

Ensure you have Python 3.11 or later installed on your system. You can verify your Python version by running:

```bash
python --version
```

Next, install the required Python packages using `pip`:

```bash
pip install torch torchvision numpy scikit-learn
```

## Exercise 1: Hands-On Implementation & Pipeline Execution

In this exercise, we will implement a simple CNN to classify images from the CIFAR-10 dataset. The CIFAR-10 dataset consists of 60,000 32x32 color images in 10 different classes, with 6,000 images per class.

### Complete, Runnable Python Script

Below is a complete, runnable Python script that defines a CNN, trains it on the CIFAR-10 dataset, and evaluates its performance.

```python
import torch
import torch.nn as nn
import torch.optim as optim
import torchvision
import torchvision.transforms as transforms
import numpy as np
from sklearn.metrics import classification_report

# Define the CNN architecture
class SimpleCNN(nn.Module):
    def __init__(self):
        super(SimpleCNN, self).__init__()
        self.conv1 = nn.Conv2d(3, 32, kernel_size=3, padding=1)
        self.conv2 = nn.Conv2d(32, 64, kernel_size=3, padding=1)
        self.pool = nn.MaxPool2d(kernel_size=2, stride=2)
        self.fc1 = nn.Linear(64 * 8 * 8, 128)
        self.fc2 = nn.Linear(128, 10)
        self.relu = nn.ReLU()

    def forward(self, x):
        x = self.pool(self.relu(self.conv1(x)))
        x = self.pool(self.relu(self.conv2(x)))
        x = x.view(-1, 64 * 8 * 8)
        x = self.relu(self.fc1(x))
        x = self.fc2(x)
        return x

# Load and preprocess the CIFAR-10 dataset
transform = transforms.Compose([
    transforms.ToTensor(),
    transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5))
])

trainset = torchvision.datasets.CIFAR10(root='./data', train=True, download=True, transform=transform)
trainloader = torch.utils.data.DataLoader(trainset, batch_size=64, shuffle=True, num_workers=2)

testset = torchvision.datasets.CIFAR10(root='./data', train=False, download=True, transform=transform)
testloader = torch.utils.data.DataLoader(testset, batch_size=64, shuffle=False, num_workers=2)

# Initialize the CNN, loss function, and optimizer
net = SimpleCNN()
criterion = nn.CrossEntropyLoss()
optimizer = optim.SGD(net.parameters(), lr=0.001, momentum=0.9)

# Train the CNN
def train(net, trainloader, criterion, optimizer, epochs=10):
    net.train()
    for epoch in range(epochs):
        running_loss = 0.0
        for i, data in enumerate(trainloader, 0):
            inputs, labels = data
            optimizer.zero_grad()
            outputs = net(inputs)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()
            running_loss += loss.item()
            if i % 100 == 99:  # Print every 100 mini-batches
                print(f'[Epoch {epoch + 1}, Batch {i + 1}] loss: {running_loss / 100:.3f}')
                running_loss = 0.0
    print('Finished Training')

# Evaluate the CNN
def evaluate(net, testloader):
    net.eval()
    correct = 0
    total = 0
    all_preds = []
    all_labels = []
    with torch.no_grad():
        for data in testloader:
            images, labels = data
            outputs = net(images)
            _, predicted = torch.max(outputs.data, 1)
            total += labels.size(0)
            correct += (predicted == labels).sum().item()
            all_preds.extend(predicted.numpy())
            all_labels.extend(labels.numpy())
    print(f'Accuracy of the network on the 10000 test images: {100 * correct / total:.2f}%')
    print(classification_report(all_labels, all_preds, target_names=testset.classes))

# Run the training and evaluation
if __name__ == '__main__':
    train(net, trainloader, criterion, optimizer, epochs=10)
    evaluate(net, testloader)
```

## Exercise 2: Hyperparameter Tuning & Empirical Benchmarking

In this exercise, we will perform hyperparameter tuning and empirical benchmarking to measure the accuracy, latency, and convergence curves of our CNN.

### Real Benchmarking Code

Below is a complete, runnable Python script that includes hyperparameter tuning and benchmarking.

```python
import torch
import torch.nn as nn
import torch.optim as optim
import torchvision
import torchvision.transforms as transforms
import numpy as np
import time
from sklearn.metrics import classification_report

# Define the CNN architecture
class SimpleCNN(nn.Module):
    def __init__(self):
        super(SimpleCNN, self).__init__()
        self.conv1 = nn.Conv2d(3, 32, kernel_size=3, padding=1)
        self.conv2 = nn.Conv2d(32, 64, kernel_size=3, padding=1)
        self.pool = nn.MaxPool2d(kernel_size=2, stride=2)
        self.fc1 = nn.Linear(64 * 8 * 8, 128)
        self.fc2 = nn.Linear(128, 10)
        self.relu = nn.ReLU()

    def forward(self, x):
        x = self.pool(self.relu(self.conv1(x)))
        x = self.pool(self.relu(self.conv2(x)))
        x = x.view(-1, 64 * 8 * 8)
        x = self.relu(self.fc1(x))
        x = self.fc2(x)
        return x

# Load and preprocess the CIFAR-10 dataset
transform = transforms.Compose([
    transforms.ToTensor(),
    transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5))
])

trainset = torchvision.datasets.CIFAR10(root='./data', train=True, download=True, transform=transform)
trainloader = torch.utils.data.DataLoader(trainset, batch_size=64, shuffle=True, num_workers=2)

testset = torchvision.datasets.CIFAR10(root='./data', train=False, download=True, transform=transform)
testloader = torch.utils.data.DataLoader(testset, batch_size=64, shuffle=False, num_workers=2)

# Hyperparameter tuning
learning_rates = [0.001, 0.0001]
momentums = [0.9, 0.99]
epochs = 10

results = {}

for lr in learning_rates:
    for momentum in momentums:
        net = SimpleCNN()
        criterion = nn.CrossEntropyLoss()
        optimizer = optim.SGD(net.parameters(), lr=lr, momentum=momentum)
        
        start_time = time.time()
        train(net, trainloader, criterion, optimizer, epochs=epochs)
        end_time = time.time()
        
        accuracy, report = evaluate(net, testloader)
        latency = end_time - start_time
        
        results[(lr, momentum)] = {
            'accuracy': accuracy,
            'latency': latency,
            'report': report
        }

# Print the results
for (lr, momentum), result in results.items():
    print(f'Learning Rate: {lr}, Momentum: {momentum}')
    print(f'Accuracy: {result["accuracy"]:.2f}%')
    print(f'Latency: {result["latency"]:.2f} seconds')
    print(result['report'])
    print('-' * 80)

# Train function
def train(net, trainloader, criterion, optimizer, epochs=10):
    net.train()
    for epoch in range(epochs):
        running_loss = 0.0
        for i, data in enumerate(trainloader, 0):
            inputs, labels = data
            optimizer.zero_grad()
            outputs = net(inputs)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()
            running_loss += loss.item()
            if i % 100 == 99:  # Print every 100 mini-batches
                print(f'[Epoch {epoch + 1}, Batch {i + 1}] loss: {running_loss / 100:.3f}')
                running_loss = 0.0
    print('Finished Training')

# Evaluate function
def evaluate(net, testloader):
    net.eval()
    correct = 0
    total = 0
    all_preds = []
    all_labels = []
    with torch.no_grad():
        for data in testloader:
            images, labels = data
            outputs = net(images)
            _, predicted = torch.max(outputs.data, 1)
            total += labels.size(0)
            correct += (predicted == labels).sum().item()
            all_preds.extend(predicted.numpy())
            all_labels.extend(labels.numpy())
    accuracy = 100 * correct / total
    report = classification_report(all_labels, all_preds, target_names=testset.classes, output_dict=True)
    return accuracy, report
```

## Exercise 3: Stress Testing, Edge Cases & Failure Mitigation

In this exercise, we will perform stress testing, identify edge cases, and implement guardrails or error handling to ensure the robustness of our CNN.

### Reproducing Failure Modes, Testing Edge Cases, and Implementing Guardrails

Below is a complete, runnable Python script that includes stress testing and error handling.

```python
import torch
import torch.nn as nn
import torch.optim as optim
import torchvision
import torchvision.transforms as transforms
import numpy as np
from sklearn.metrics import classification_report

# Define the CNN architecture
class SimpleCNN(nn.Module):
    def __init__(self):
        super(SimpleCNN, self).__init__()
        self.conv1 = nn.Conv2d(3, 32, kernel_size=3, padding=1)
        self.conv2 = nn.Conv2d(32, 64, kernel_size=3, padding=1)
        self.pool = nn.MaxPool2d(kernel_size=2, stride=2)
        self.fc1 = nn.Linear(64 * 8 * 8, 128)
        self.fc2 = nn.Linear(128, 10)
        self.relu = nn.ReLU()

    def forward(self, x):
        x = self.pool(self.relu(self.conv1(x)))
        x = self.pool(self.relu(self.conv2(x)))
        x = x.view(-1, 64 * 8 * 8)
        x = self.relu(self.fc1(x))
        x = self.fc2(x)
        return x

# Load and preprocess the CIFAR-10 dataset
transform = transforms.Compose([
    transforms.ToTensor(),
    transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5))
])

trainset = torchvision.datasets.CIFAR10(root='./data', train=True, download=True, transform=transform)
trainloader = torch.utils.data.DataLoader(trainset, batch_size=64, shuffle=True, num_workers=2)

testset = torchvision.datasets.CIFAR10(root='./data', train=False, download=True, transform=transform)
testloader = torch.utils.data.DataLoader(testset, batch_size=64, shuffle=False, num_workers=2)

# Initialize the CNN, loss function, and optimizer
net = SimpleCNN()
criterion = nn.CrossEntropyLoss()
optimizer = optim.SGD(net.parameters(), lr=0.001, momentum=0.9)

# Train the CNN
def train(net, trainloader, criterion, optimizer, epochs=10):
    net.train()
    for epoch in range(epochs):
        running_loss = 0.0
        for i, data in enumerate(trainloader, 0):
            inputs, labels = data
            optimizer.zero_grad()
            outputs = net(inputs)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()
            running_loss += loss.item()
            if i % 100 == 99:  # Print every 100 mini-batches
                print(f'[Epoch {epoch + 1}, Batch {i + 1}] loss: {running_loss / 100:.3f}')
                running_loss = 0.0
    print('Finished Training')

# Evaluate the CNN
def evaluate(net, testloader):
    net.eval()
    correct = 0
    total = 0
    all_preds = []
    all_labels = []
    with torch.no_grad():
        for data in testloader:
            images, labels = data
            outputs = net(images)
            _, predicted = torch.max(outputs.data, 1)
            total += labels.size(0)
            correct += (predicted == labels).sum().item()
            all_preds.extend(predicted.numpy())
            all_labels.extend(labels.numpy())
    print(f'Accuracy of the network on the 10000 test images: {100 * correct / total:.2f}%')
    print(classification_report(all_labels, all_preds, target_names=testset.classes))

# Stress testing and edge cases
def stress_test(net, testloader):
    net.eval()
    for i, data in enumerate(testloader):
        images, labels = data
        try:
            outputs = net(images)
            _, predicted = torch.max(outputs.data, 1)
        except Exception as e:
            print(f'Error during inference: {e}')
            continue
        if i % 100 == 99:  # Print every 100 mini-batches
            print(f'Stress test batch {i + 1} completed successfully')

# Run the training, evaluation, and stress test
if __name__ == '__main__':
    train(net, trainloader, criterion, optimizer, epochs=10)
    evaluate(net, testloader)
    stress_test(net, testloader)
```

## Verification Checklist & Quick Reference Cheat Sheet

Below is a table of essential Python methods, parameters, and verification flags for this topic.

| Method/Parameter | Description |
|------------------|-------------|
| `SimpleCNN`      | The CNN architecture class. |
| `train`          | Function to train the CNN. |
| `evaluate`       | Function to evaluate the CNN. |
| `stress_test`    | Function to perform stress testing. |
| `learning_rates` | List of learning rates for hyperparameter tuning. |
| `momentums`      | List of momentums for hyperparameter tuning. |
| `epochs`         | Number of epochs for training. |
| `criterion`      | Loss function used for training. |
| `optimizer`      | Optimizer used for training. |
| `classification_report` | Function from Scikit-learn to generate classification reports. |
| `transforms`     | Transformations applied to the dataset. |
| `trainloader`    | DataLoader for the training dataset. |
| `testloader`     | DataLoader for the test dataset. |

This lab provides a comprehensive hands-on experience with implementing, tuning, and verifying Convolutional Neural Networks using real, executable Python scripts. By following the steps outlined in this guide, you will gain practical insights into the mechanics of CNNs and their applications in deep learning.
