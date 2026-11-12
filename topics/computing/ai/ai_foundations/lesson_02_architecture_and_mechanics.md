# Lesson 2: Core Architecture & Algorithmic Mechanics

## 1. Tensor Transformations & Dimensional Flows

Tensor transformations are the fundamental building blocks of neural network computations. At their core, they involve the manipulation of multidimensional arrays, or tensors, through a series of linear and non-linear operations. Understanding the mechanics of tensor transformations requires grasping the concept of dimensional flows.

Dimensional flows refer to the way data flows through a neural network, from input to output, and how the dimensions of the tensors change at each stage. In a typical neural network, the input data is a tensor with a specific shape, such as a 3D image or a 1D time series. As the data flows through the network, it is transformed by a series of convolutional, pooling, and fully connected layers. Each layer applies a set of linear and non-linear transformations to the input tensor, resulting in a new tensor with a different shape.

To illustrate this concept, consider a simple convolutional neural network (CNN) with a 2D input image. The input image is a tensor with shape `(batch_size, height, width, channels)`. The first convolutional layer applies a set of filters to the input image, resulting in a tensor with shape `(batch_size, height, width, num_filters)`. The pooling layer then reduces the spatial dimensions of the tensor, resulting in a tensor with shape `(batch_size, height/2, width/2, num_filters)`.

The key insight here is that the dimensions of the tensor change at each stage of the network. The batch dimension remains constant, but the spatial dimensions (height and width) are reduced by the pooling layer. This dimensional flow is a fundamental aspect of neural network computations, and understanding it is crucial for designing efficient and effective neural network architectures.

### Code Example: Convolutional Neural Network (CNN)

```python
import torch
import torch.nn as nn

class ConvNet(nn.Module):
    def __init__(self):
        super(ConvNet, self).__init__()
        self.conv1 = nn.Conv2d(1, 10, kernel_size=5)
        self.pool = nn.MaxPool2d(2, 2)
        self.fc1 = nn.Linear(320, 50)

    def forward(self, x):
        out = self.pool(nn.functional.relu(self.conv1(x)))
        out = out.view(-1, 320)
        out = self.fc1(out)
        return out
```

This code defines a simple CNN with a single convolutional layer, a pooling layer, and a fully connected layer. The `forward` method defines the forward pass through the network, which involves applying the convolutional and pooling layers to the input tensor.

## 2. Loss Surfaces, Gradients & Optimization Dynamics

The loss surface of a neural network is a multidimensional function that represents the error between the predicted output and the true output. The loss surface is typically a complex, non-convex function that has multiple local minima and saddle points. The goal of optimization algorithms is to find the global minimum of the loss surface, which corresponds to the optimal set of model parameters.

To understand the mechanics of optimization algorithms, it's essential to grasp the concept of gradients. The gradient of a function is a vector that points in the direction of the steepest ascent of the function. In the context of neural networks, the gradient of the loss function with respect to the model parameters is used to update the parameters during training.

The most common optimization algorithms used in neural networks are stochastic gradient descent (SGD), Adam, and RMSProp. These algorithms update the model parameters based on the gradient of the loss function, but they differ in the way they compute the gradient and update the parameters.

### Code Example: Stochastic Gradient Descent (SGD)

```python
import torch
import torch.optim as optim

class SGD:
    def __init__(self, model, lr):
        self.model = model
        self.lr = lr
        self.optimizer = optim.SGD(model.parameters(), lr=lr)

    def step(self):
        self.optimizer.step()
```

This code defines a simple SGD optimizer that updates the model parameters based on the gradient of the loss function. The `step` method updates the model parameters using the `optimizer.step()` method.

## 3. Attention Maps, Kernel Mechanics & Latent Geometry

Attention mechanisms are a type of neural network component that allows the model to focus on specific parts of the input data. Attention maps are used to compute the attention weights, which are then used to compute the weighted sum of the input data.

Kernel mechanics refer to the way the attention weights are computed. The attention weights are typically computed using a dot product between the query and key vectors, followed by a softmax normalization.

Latent geometry refers to the way the attention weights are used to compute the weighted sum of the input data. The weighted sum is typically computed using a dot product between the attention weights and the input data.

### Code Example: Attention Mechanism

```python
import torch
import torch.nn as nn

class Attention(nn.Module):
    def __init__(self, num_heads):
        super(Attention, self).__init__()
        self.num_heads = num_heads
        self.query_key_value = nn.Linear(128, 128 * 3)

    def forward(self, x):
        query, key, value = self.query_key_value(x).split(128, dim=2)
        attention_weights = torch.matmul(query, key.transpose(1, 2)) / math.sqrt(128)
        attention_weights = nn.functional.softmax(attention_weights, dim=2)
        weighted_sum = torch.matmul(attention_weights, value)
        return weighted_sum
```

This code defines a simple attention mechanism that computes the attention weights using a dot product between the query and key vectors, followed by a softmax normalization. The weighted sum is then computed using a dot product between the attention weights and the input data.

Note: I've corrected the code examples to use the correct syntax and formatting. I've also removed the unnecessary comments and added some minor improvements to the text.
