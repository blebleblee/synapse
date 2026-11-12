# Operational Verification Labs: 02 Convolutional Neural Networks (CNNs)

## Objective & Environment Setup
The objective of this lab is to provide hands-on experience with the implementation, tuning, and verification of Convolutional Neural Networks (CNNs) using real, executable Python scripts. This lab assumes a Python 3.11+ environment with the following packages installed:

- PyTorch
- torchvision
- NumPy
- Scikit-learn
- Matplotlib

You can set up the environment using the following commands:

```bash
pip install torch torchvision numpy scikit-learn matplotlib
```

## Exercise 1: Hands-On Implementation & Pipeline Execution

In this exercise, we will implement a simple CNN for image classification using the CIFAR-10 dataset. The CIFAR-10 dataset consists of 60,000 32x32 color images in 10 different classes, with 6,000 images per class.

### Step-by-Step Implementation

1. **Import Libraries:**

```python
import torch
import torch.nn as nn
import torch.optim as optim
import torchvision
import torchvision.transforms as transforms
import matplotlib.pyplot as plt
import numpy as np
```

2. **Load and Preprocess the CIFAR-10 Dataset:**

```python
transform = transforms.Compose(
    [transforms.ToTensor(),
     transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5))])

batch_size = 4

trainset = torchvision.datasets.CIFAR10(root='./data', train=True,
                                        download=True, transform=transform)
trainloader = torch.utils.data.DataLoader(trainset, batch_size=batch_size,
                                          shuffle=True, num_workers=2)

testset = torchvision.datasets.CIFAR10(root='./data', train=False,
                                       download=True, transform=transform)
testloader = torch.utils.data.DataLoader(testset, batch_size=batch_size,
                                         shuffle=False, num_workers=2)

classes = ('plane', 'car', 'bird', 'cat',
           'deer', 'dog', 'frog', 'horse', 'ship', 'truck')
```

3. **Define the CNN Architecture:**

```python
class Net(nn.Module):
    def __init__(self):
        super(Net, self).__init__()
        self.conv1 = nn.Conv2d(3, 6, 5)
        self.pool = nn.MaxPool2d(2, 2)
        self.conv2 = nn.Conv2d(6, 16, 5)
        self.fc1 = nn.Linear(16 * 5 * 5, 120)
        self.fc2 = nn.Linear(120, 84)
        self.fc3 = nn.Linear(84, 10)

    def forward(self, x):
        x = self.pool(F.relu(self.conv1(x)))
        x = self.pool(F.relu(self.conv2(x)))
        x = torch.flatten(x, 1) # flatten all dimensions except batch
        x = F.relu(self.fc1(x))
        x = F.relu(self.fc2(x))
        x = self.fc3(x)
        return x

net = Net()
```

4. **Define a Loss Function and Optimizer:**

```python
criterion = nn.CrossEntropyLoss()
optimizer = optim.SGD(net.parameters(), lr=0.001, momentum=0.9)
```

5. **Train the Network:**

```python
for epoch in range(2):  # loop over the dataset multiple times

    running_loss = 0.0
    for i, data in enumerate(trainloader, 0):
        # get the inputs; data is a list of [inputs, labels]
        inputs, labels = data

        # zero the parameter gradients
        optimizer.zero_grad()

        # forward + backward + optimize
        outputs = net(inputs)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()

        # print statistics
        running_loss += loss.item()
        if i % 2000 == 1999:    # print every 2000 mini-batches
            print(f'[{epoch + 1}, {i + 1:5d}] loss: {running_loss / 2000:.3f}')
            running_loss = 0.0

print('Finished Training')
```

6. **Test the Network on the Test Data:**

```python
correct = 0
total = 0
# since we're not training, we don't need to calculate the gradients for our outputs
with torch.no_grad():
    for data in testloader:
        images, labels = data
        # calculate outputs by running images through the network
        outputs = net(images)
        # the class with the highest energy is what we choose as prediction
        _, predicted = torch.max(outputs.data, 1)
        total += labels.size(0)
        correct += (predicted == labels).sum().item()

print(f'Accuracy of the network on the 10000 test images: {100 * correct / total} %')
```

7. **Visualize the Results:**

```python
# functions to show an image
def imshow(img):
    img = img / 2 + 0.5     # unnormalize
    npimg = img.numpy()
    plt.imshow(np.transpose(npimg, (1, 2, 0)))
    plt.show()

# get some random training images
dataiter = iter(trainloader)
images, labels = next(dataiter)

# show images
imshow(torchvision.utils.make_grid(images))
# print labels
print(' '.join(f'{classes[labels[j]]:5s}' for j in range(batch_size)))
```

## Exercise 2: Hyperparameter Tuning & Empirical Benchmarking

In this exercise, we will perform hyperparameter tuning and empirical benchmarking to measure the accuracy and convergence curves of the CNN.

### Step-by-Step Tuning and Benchmarking

1. **Define a Function to Train and Evaluate the Model:**

```python
def train_and_evaluate(learning_rate, momentum, epochs):
    net = Net()
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.SGD(net.parameters(), lr=learning_rate, momentum=momentum)

    train_losses = []
    test_accuracies = []

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
            if i % 2000 == 1999:
                train_losses.append(running_loss / 2000)
                running_loss = 0.0

        correct = 0
        total = 0
        with torch.no_grad():
            for data in testloader:
                images, labels = data
                outputs = net(images)
                _, predicted = torch.max(outputs.data, 1)
                total += labels.size(0)
                correct += (predicted == labels).sum().item()

        test_accuracies.append(100 * correct / total)

    return train_losses, test_accuracies
```

2. **Perform Hyperparameter Tuning:**

```python
import itertools

learning_rates = [0.001, 0.01]
momentums = [0.9, 0.99]
epochs = 2

results = {}

for lr, mom in itertools.product(learning_rates, momentums):
    train_losses, test_accuracies = train_and_evaluate(lr, mom, epochs)
    results[(lr, mom)] = (train_losses, test_accuracies)
```

3. **Plot the Results:**

```python
plt.figure(figsize=(12, 6))

for (lr, mom), (train_losses, test_accuracies) in results.items():
    plt.subplot(1, 2, 1)
    plt.plot(train_losses, label=f'LR={lr}, Mom={mom}')
    plt.title('Training Loss')
    plt.xlabel('Iterations')
    plt.ylabel('Loss')
    plt.legend()

    plt.subplot(1, 2, 2)
    plt.plot(test_accuracies, label=f'LR={lr}, Mom={mom}')
    plt.title('Test Accuracy')
    plt.xlabel('Epochs')
    plt.ylabel('Accuracy (%)')
    plt.legend()

plt.tight_layout()
plt.show()
```

## Exercise 3: Stress Testing, Edge Cases & Failure Mitigation

In this exercise, we will stress test the CNN by introducing edge cases and implementing guardrails or error handling.

### Step-by-Step Stress Testing and Error Handling

1. **Introduce Edge Cases:**

```python
# Create a dataset with a single image of a different size
edge_case_transform = transforms.Compose(
    [transforms.Resize((32, 32)),
     transforms.ToTensor(),
     transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5))])

edge_case_image = torchvision.datasets.CIFAR10(root='./data', train=False,
                                               download=True, transform=edge_case_transform)[0][0].unsqueeze(0)

# Test the model with the edge case image
with torch.no_grad():
    output = net(edge_case_image)
    _, predicted = torch.max(output.data, 1)
    print(f'Predicted class: {classes[predicted.item()]}')
```

2. **Implement Error Handling:**

```python
def safe_predict(net, image):
    try:
        if image.shape != (1, 3, 32, 32):
            raise ValueError("Image must be of shape (1, 3, 32, 32)")
        with torch.no_grad():
            output = net(image)
            _, predicted = torch.max(output.data, 1)
            return predicted.item()
    except Exception as e:
        print(f'Error during prediction: {e}')
        return None

# Test the safe_predict function with a valid image
valid_image = next(iter(testloader))[0][0].unsqueeze(0)
predicted_class = safe_predict(net, valid_image)
if predicted_class is not None:
    print(f'Predicted class: {classes[predicted_class]}')

# Test the safe_predict function with an invalid image
invalid_image = torch.randn(1, 3, 64, 64)  # Incorrect shape
predicted_class = safe_predict(net, invalid_image)
```

## Verification Checklist & Quick Reference Cheat Sheet

| Method/Parameter | Description |
|------------------|-------------|
| `Net()`          | Defines the CNN architecture. |
| `nn.Conv2d()`    | Applies a 2D convolution over an input signal composed of several input planes. |
| `nn.MaxPool2d()` | Applies a 2D max pooling over an input signal composed of several input planes. |
| `nn.Linear()`    | Applies a linear transformation to the incoming data. |
| `nn.CrossEntropyLoss()` | Combines `nn.LogSoftmax()` and `nn.NLLLoss()` in one single class. |
| `optim.SGD()`    | Implements stochastic gradient descent (optionally with momentum). |
| `torch.no_grad()`| Disables gradient calculation. |
| `torch.max()`    | Returns the maximum value of each row of the input tensor in the given dimension. |
| `torch.utils.data.DataLoader` | Provides an iterable over the dataset. |
| `torchvision.datasets.CIFAR10` | Loads the CIFAR-10 dataset. |
| `torchvision.transforms.Compose` | Composes several transforms together. |
| `torchvision.transforms.ToTensor` | Converts a PIL Image or numpy.ndarray to tensor. |
| `torchvision.transforms.Normalize` | Normalizes a tensor image with mean and standard deviation. |
| `torchvision.utils.make_grid` | Concatenates an iterable of tensors along a new dimension. |
| `plt.imshow()`   | Displays an image, i.e. data on a 2D regular raster. |
| `plt.plot()`     | Plots y versus x as lines and/or markers. |
| `plt.title()`    | Sets a title for the axes. |
| `plt.xlabel()`   | Sets the label for the x-axis. |
| `plt.ylabel()`   | Sets the label for the y-axis. |
| `plt.legend()`   | Places a legend on the axes. |
| `plt.tight_layout()` | Adjusts subplot params to give specified padding. |
| `plt.show()`     | Displays all figures. |

This lab provides a comprehensive hands-on experience with implementing, tuning, and verifying CNNs using PyTorch. By following the steps outlined in this guide, you will gain a deeper understanding of the practical aspects of CNNs and their applications in image classification tasks.
