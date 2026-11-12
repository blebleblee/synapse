# Lesson 2: Core Architecture & Algorithmic Mechanics
=====================================================

## 1. Tensor Transformations & Dimensional Flows

Tensors are the fundamental data structures in deep learning, enabling efficient computation and storage of high-dimensional data. A tensor is a multi-dimensional array of numerical values, and its transformations play a crucial role in the forward and backward passes of neural networks.

A tensor transformation is a linear operation that maps an input tensor to an output tensor through a set of weights and biases. This process can be viewed as a series of matrix multiplications, where the input tensor is represented as a column vector, and the weights and biases are encoded in a matrix. The resulting output tensor is then computed by taking the dot product of the input vector and the weight matrix.

One of the key aspects of tensor transformations is dimensional flow. In a typical neural network, the input data flows through a series of layers, each with its own set of weights and biases. As the data flows through these layers, its dimensionality changes, and the tensor transformations must adapt to accommodate these changes.

For instance, in a convolutional neural network (CNN), the input data flows through a series of convolutional and pooling layers, which reduce the spatial dimensions of the data while increasing its depth.

To illustrate this concept, consider a simple example of a 2D convolutional layer. Suppose we have an input tensor of size 28x28x3, representing a 28x28 image with 3 color channels. The convolutional layer applies a set of 5x5 filters to the input data, producing an output tensor of size 24x24x64.

The dimensional flow in this example is as follows:

* The input tensor has a spatial dimension of 28x28 and a depth dimension of 3.
* The convolutional layer reduces the spatial dimensions to 24x24 while increasing the depth dimension to 64.
* The resulting output tensor has a spatial dimension of 24x24 and a depth dimension of 64.

### Example Code

```python
import torch
import torch.nn as nn

class Conv2d(nn.Module):
    def __init__(self, in_channels, out_channels, kernel_size):
        super(Conv2d, self).__init__()
        self.conv = nn.Conv2d(in_channels, out_channels, kernel_size)

    def forward(self, x):
        return self.conv(x)

input_tensor = torch.randn(1, 3, 28, 28)
conv_layer = Conv2d(3, 64, 5)
output_tensor = conv_layer(input_tensor)
print(output_tensor.shape)  # Output: torch.Size([1, 64, 24, 24])
```

## 2. Loss Surfaces, Gradients & Optimization Dynamics

The loss surface of a neural network is a critical concept in deep learning, representing the landscape of possible solutions to the optimization problem. Understanding the properties of the loss surface is essential for designing effective optimization algorithms and training deep neural networks.

The loss surface is a function of the model parameters, which are updated through the optimization process. The loss function is typically defined as the mean squared error (MSE) or cross-entropy loss between the predicted output and the true label. The goal of optimization is to find the optimal set of model parameters that minimize the loss function.

One of the key aspects of the loss surface is its curvature. The curvature of the loss surface determines the rate at which the model parameters converge to the optimal solution. A flat loss surface indicates a slow convergence rate, while a steep loss surface indicates a fast convergence rate.

To illustrate this concept, consider a simple example of a linear regression model. Suppose we have a dataset of 100 samples with two features and one target variable. We define a linear regression model with two parameters (slope and intercept) and a mean squared error loss function.

```python
import numpy as np

X = np.random.rand(100, 2)
y = np.random.rand(100)

def linear_regression(X, w):
    return np.dot(X, w)

def mse_loss(y_pred, y):
    return np.mean((y_pred - y) ** 2)

w = np.random.rand(2)
loss = mse_loss(linear_regression(X, w), y)
print(loss)  # Output: a scalar value representing the loss
```

### Example Code

```python
import torch
import torch.optim as optim

class LinearRegression(nn.Module):
    def __init__(self, in_features, out_features):
        super(LinearRegression, self).__init__()
        self.linear = nn.Linear(in_features, out_features)

    def forward(self, x):
        return self.linear(x)

X = torch.randn(100, 2)
y = torch.randn(100)
model = LinearRegression(2, 1)
criterion = nn.MSELoss()
optimizer = optim.SGD(model.parameters(), lr=0.01)
loss = criterion(model(X), y)
print(loss)  # Output: a scalar value representing the loss
```

## 3. Attention Maps, Kernel Mechanics & Latent Geometry

Attention mechanisms are a critical component of deep learning models, enabling the model to focus on specific regions of the input data. Understanding the mechanics of attention maps and kernel functions is essential for designing effective attention-based models.

An attention mechanism is a function that maps the input data to a set of attention weights. These attention weights are then used to compute the weighted sum of the input data, producing a weighted output. The attention mechanism can be viewed as a kernel function that maps the input data to a set of attention weights.

One of the key aspects of attention mechanisms is their ability to capture long-range dependencies in the input data. Attention mechanisms can be used to model complex relationships between different regions of the input data, enabling the model to capture subtle patterns and structures.

To illustrate this concept, consider a simple example of a self-attention mechanism. Suppose we have a sequence of 10 tokens, each with a fixed-size embedding. We define a self-attention mechanism that computes the attention weights for each token based on the input embeddings.

```python
import torch
import torch.nn as nn

class SelfAttention(nn.Module):
    def __init__(self, embed_dim):
        super(SelfAttention, self).__init__()
        self.query = nn.Linear(embed_dim, embed_dim)
        self.key = nn.Linear(embed_dim, embed_dim)
        self.value = nn.Linear(embed_dim, embed_dim)

    def forward(self, x):
        query = self.query(x)
        key = self.key(x)
        value = self.value(x)
        attention_weights = torch.matmul(query, key.T) / math.sqrt(embed_dim)
        output = torch.matmul(attention_weights, value)
        return output

embed_dim = 128
x = torch.randn(10, embed_dim)
attention = SelfAttention(embed_dim)
output = attention(x)
print(output.shape)  # Output: torch.Size([10, 128])
```

Note that the above code is a simplified example and may not be directly applicable to real-world scenarios. In practice, attention mechanisms are often used in conjunction with other components, such as recurrent neural networks or transformers, to model complex relationships between input data.
