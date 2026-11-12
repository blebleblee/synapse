# Lesson 2: Core Architecture & Algorithmic Mechanics

## 1. Tensor Transformations & Dimensional Flows

Tensor transformations are the backbone of modern neural networks, enabling efficient computation and manipulation of high-dimensional data. At their core, tensors are multi-dimensional arrays of numerical values, often represented as matrices or higher-order tensors. The fundamental operations on tensors are element-wise multiplication, addition, and convolution, which are used to build complex neural network architectures.

Understanding tensor transformations requires grasping the concept of dimensional flow. Dimensional flow refers to the way data flows through the network, from input to output, while maintaining its structural properties. This flow is governed by the tensor's dimensions, which are manipulated through various operations such as reshaping, transposing, and flattening.

One of the most critical tensor operations is convolution, which is used extensively in convolutional neural networks (CNNs). Convolution involves sliding a kernel (a small tensor) over the input data, computing the dot product at each position, and accumulating the results. This process is equivalent to a series of matrix multiplications, where the kernel is treated as a matrix and the input data is treated as a vector.

To illustrate the mechanics of convolution, consider a 2D image represented as a 4D tensor (batch size, height, width, channels). The convolution operation involves sliding a 2D kernel (e.g., 3x3) over the image, computing the dot product at each position, and accumulating the results. This process is repeated for each channel, resulting in a new 4D tensor representing the feature maps.

```python
import torch
import torch.nn as nn

# Define a 2D kernel (3x3)
kernel = nn.Conv2d(1, 1, kernel_size=3, padding=1)

# Define a 4D tensor (batch size, height, width, channels)
input_data = torch.randn(1, 28, 28, 1)

# Perform convolution
output = kernel(input_data)
```

## 2. Loss Surfaces, Gradients & Optimization Dynamics

Loss surfaces are a fundamental concept in machine learning, representing the relationship between model parameters and the objective function (e.g., mean squared error). The loss surface is typically visualized as a 3D plot, with the x and y axes representing the model parameters and the z-axis representing the loss value.

The gradient of the loss function with respect to the model parameters is a critical component of optimization algorithms. The gradient represents the direction of steepest ascent in the loss surface, indicating the direction in which the model parameters should be updated to minimize the loss.

One of the most widely used optimization algorithms is stochastic gradient descent (SGD), which iteratively updates the model parameters based on the gradient of the loss function. The update rule for SGD is given by:

$$\theta_{t+1} = \theta_t - \alpha \nabla L(\theta_t)$$

where $\theta_t$ is the current model parameter, $\alpha$ is the learning rate, and $\nabla L(\theta_t)$ is the gradient of the loss function with respect to the model parameter.

```python
import torch
import torch.optim as optim

# Define a model and loss function
model = torch.nn.Linear(5, 3)
criterion = torch.nn.MSELoss()

# Define a dataset and optimizer
dataset = torch.randn(100, 5)
optimizer = optim.SGD(model.parameters(), lr=0.01)

# Perform optimization
for i in range(100):
    optimizer.zero_grad()
    output = model(dataset)
    loss = criterion(output, torch.randn(100, 3))
    loss.backward()
    optimizer.step()
```

## 3. Attention Maps, Kernel Mechanics & Latent Geometry

Attention mechanisms are a key component of modern neural networks, enabling the model to focus on specific regions of the input data. Attention maps represent the weights assigned to each input element, indicating the importance of each element in the computation.

One of the most widely used attention mechanisms is the self-attention mechanism, which computes the attention weights based on the similarity between input elements. The self-attention mechanism is typically implemented using a dot product attention, which computes the attention weights as follows:

$$\text{Attention}(Q, K, V) = \text{softmax}\left(\frac{QK^T}{\sqrt{d}}\right)V$$

where $Q$ is the query tensor, $K$ is the key tensor, $V$ is the value tensor, and $d$ is the dimensionality of the input data.

Kernel mechanics refer to the way the attention mechanism computes the attention weights. The kernel is typically represented as a matrix, and the attention weights are computed by taking the dot product of the query and key matrices.

Latent geometry refers to the way the attention mechanism represents the input data in a lower-dimensional space. The attention mechanism typically uses a linear transformation to map the input data to a lower-dimensional space, where the attention weights are computed.

```python
import torch
import torch.nn as nn

class SelfAttention(nn.Module):
    def __init__(self, num_heads, hidden_dim):
        super(SelfAttention, self).__init__()
        self.num_heads = num_heads
        self.hidden_dim = hidden_dim
        self.query_linear = nn.Linear(hidden_dim, hidden_dim)
        self.key_linear = nn.Linear(hidden_dim, hidden_dim)
        self.value_linear = nn.Linear(hidden_dim, hidden_dim)

    def forward(self, x):
        # Compute query, key, and value tensors
        query = self.query_linear(x)
        key = self.key_linear(x)
        value = self.value_linear(x)

        # Compute attention weights
        attention_weights = torch.matmul(query, key.T) / math.sqrt(self.hidden_dim)

        # Compute output
        output = torch.matmul(attention_weights, value)

        return output
```

Note that this is a simplified example, and in practice, you would need to implement the self-attention mechanism using a more complex architecture, such as a transformer encoder.
