# Lesson 2: Core Architecture & Algorithmic Mechanics

## 1. Tensor Transformations & Dimensional Flows

Tensors are the fundamental data structures in deep learning, and understanding their transformations is crucial for grasping the underlying mechanics of neural networks. A tensor is a multi-dimensional array of numerical values, and its dimensions can be thought of as the number of features or attributes that it represents.

When performing operations on tensors, such as matrix multiplication or convolution, we are essentially transforming the data from one representation to another. This transformation is governed by the rules of linear algebra, which dictate how the tensor's dimensions change under different operations.

For example, when performing a matrix multiplication between two tensors, the resulting tensor has dimensions that are the product of the input tensors' dimensions. This is because each element in the output tensor is computed by taking the dot product of corresponding elements from the input tensors.

```python
import torch

# Define two tensors
x = torch.randn(3, 4)
y = torch.randn(4, 5)

# Perform matrix multiplication
z = torch.matmul(x, y)

print(z.shape)  # Output: torch.Size([3, 5])
```

In this example, the input tensors `x` and `y` have dimensions `(3, 4)` and `(4, 5)` respectively. The resulting tensor `z` has dimensions `(3, 5)`, which is the product of the input tensors' dimensions.

Another important aspect of tensor transformations is the concept of dimensional flows. When performing operations on tensors, the data flows through the dimensions of the tensor, and understanding these flows is crucial for optimizing the performance of neural networks.

For instance, in a convolutional neural network (CNN), the data flows through the spatial dimensions of the input tensor, and the convolutional kernel slides over these dimensions to compute the output. Understanding the dimensional flows in a CNN is essential for optimizing the performance of the network.

## 2. Loss Surfaces, Gradients & Optimization Dynamics

The loss surface of a neural network is the landscape of possible loss values that the network can achieve for a given dataset. Understanding the shape and structure of the loss surface is crucial for optimizing the performance of the network.

The loss surface is typically a non-convex function, meaning that it has multiple local minima and maxima. The goal of optimization algorithms is to find the global minimum of the loss surface, which corresponds to the optimal set of model parameters.

The gradient of the loss function with respect to the model parameters is a critical component of optimization algorithms. The gradient points in the direction of the steepest increase of the loss function, and optimization algorithms use this information to update the model parameters.

One of the most widely used optimization algorithms is stochastic gradient descent (SGD), which updates the model parameters based on the gradient of the loss function with respect to the current parameters. The update rule for SGD is given by:

$$\theta_{t+1} = \theta_t - \alpha \nabla L(\theta_t)$$

where $\theta_t$ is the current set of model parameters, $\alpha$ is the learning rate, and $\nabla L(\theta_t)$ is the gradient of the loss function with respect to the current parameters.

```python
import torch
import torch.nn as nn
import torch.optim as optim

# Define a neural network model
model = nn.Sequential(
    nn.Linear(784, 256),
    nn.ReLU(),
    nn.Linear(256, 10)
)

# Define a loss function and an optimizer
criterion = nn.CrossEntropyLoss()
optimizer = optim.SGD(model.parameters(), lr=0.01)

# Perform optimization
for epoch in range(10):
    optimizer.zero_grad()
    outputs = model(inputs)
    loss = criterion(outputs, labels)
    loss.backward()
    optimizer.step()
```

In this example, we define a neural network model, a loss function, and an optimizer. We then perform optimization for 10 epochs, updating the model parameters based on the gradient of the loss function with respect to the current parameters.

## 3. Attention Maps, Kernel Mechanics & Latent Geometry

Attention mechanisms are a type of neural network component that allows the model to focus on specific parts of the input data when computing the output. Attention maps are the output of attention mechanisms, which represent the importance of each input element in computing the output.

Attention mechanisms are typically used in sequence-to-sequence models, such as machine translation and text summarization. They allow the model to focus on specific parts of the input sequence when computing the output, rather than treating all input elements equally.

Kernel mechanics are a critical component of attention mechanisms. The kernel is a small window of input elements that the model focuses on when computing the output. The kernel is typically a small matrix or tensor that is convolved with the input data to compute the output.

Latent geometry is a type of representation learning that allows the model to learn a low-dimensional representation of the input data. Latent geometry is typically used in generative models, such as variational autoencoders (VAEs) and generative adversarial networks (GANs).

In VAEs, the latent space is a low-dimensional representation of the input data that is learned through a probabilistic encoder and decoder. The encoder maps the input data to a probability distribution over the latent space, and the decoder maps the latent space back to the input data.

In GANs, the latent space is a low-dimensional representation of the input data that is learned through a generator and discriminator. The generator maps the latent space to a synthetic input data, and the discriminator maps the input data to a probability distribution over the latent space.

```python
import torch
import torch.nn as nn

# Define a VAE model
class VAE(nn.Module):
    def __init__(self):
        super(VAE, self).__init__()
        self.encoder = nn.Sequential(
            nn.Linear(784, 256),
            nn.ReLU(),
            nn.Linear(256, 128)
        )
        self.decoder = nn.Sequential(
            nn.Linear(128, 256),
            nn.ReLU(),
            nn.Linear(256, 784)
        )

    def encode(self, x):
        z = self.encoder(x)
        return z

    def decode(self, z):
        x = self.decoder(z)
        return x

# Define a GAN model
class GAN(nn.Module):
    def __init__(self):
        super(GAN, self).__init__()
        self.generator = nn.Sequential(
            nn.Linear(128, 256),
            nn.ReLU(),
            nn.Linear(256, 784)
        )
        self.discriminator = nn.Sequential(
            nn.Linear(784, 256),
            nn.ReLU(),
            nn.Linear(256, 128)
        )

    def generate(self, z):
        x = self.generator(z)
        return x

    def discriminate(self, x):
        z = self.discriminator(x)
        return z
```
