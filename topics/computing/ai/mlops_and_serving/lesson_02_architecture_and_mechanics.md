# Lesson 2: Core Architecture & Algorithmic Mechanics

## 1. Tensor Transformations & Dimensional Flows

Tensor transformations are the backbone of modern neural networks, enabling efficient computation and memory management. At their core, tensors are multi-dimensional arrays of numerical values, with operations performed on them governed by strict rules of dimensional flow.

When a tensor undergoes a transformation, its dimensions are either preserved, reduced, or expanded. This is achieved through a combination of three fundamental operations: contraction, expansion, and reshaping. Contraction involves reducing the dimensionality of a tensor by merging adjacent indices, while expansion increases the dimensionality by introducing new indices. Reshaping, on the other hand, rearranges the dimensions of a tensor without altering its overall size.

To illustrate this, consider a 3D tensor `A` with dimensions `(m, n, p)`. When we contract `A` along the first two dimensions, we obtain a 2D tensor `B` with dimensions `(n, p)`. Conversely, expanding `B` along the first dimension yields a 3D tensor `C` with dimensions `(m, n, p)`.

```python
import torch

# Define a 3D tensor A with dimensions (m, n, p)
A = torch.randn(3, 4, 5)

# Contract A along the first two dimensions to obtain a 2D tensor B
B = torch.einsum('ijk, jk->ik', A, A)

# Expand B along the first dimension to obtain a 3D tensor C
C = torch.einsum('ik, ikj->ijk', B, A)
```

## 2. Loss Surfaces, Gradients & Optimization Dynamics

The loss surface of a neural network is a complex, high-dimensional landscape that guides the optimization process. At its core, the loss surface is defined by the sum of squared errors between the predicted and actual outputs. However, this simplistic view belies the intricate dynamics at play, as the loss surface is shaped by the interplay between multiple factors, including the network architecture, regularization, and optimization algorithm.

As we descend the loss surface, the gradients of the loss function with respect to the model parameters play a crucial role. The gradient descent algorithm iteratively updates the model parameters to minimize the loss, with each update governed by the chain rule. However, the gradient descent algorithm is not without its limitations, as it can get stuck in local minima or saddle points, leading to suboptimal performance.

To mitigate these issues, various optimization algorithms have been developed, including stochastic gradient descent (SGD), Adam, and RMSProp. These algorithms introduce noise into the gradient descent process, allowing the model to escape local minima and converge to a better solution.

```python
import torch
import torch.nn as nn
import torch.optim as optim

# Define a neural network model
model = nn.Sequential(
    nn.Linear(5, 10),
    nn.ReLU(),
    nn.Linear(10, 5)
)

# Define a loss function and optimizer
criterion = nn.MSELoss()
optimizer = optim.Adam(model.parameters(), lr=0.001)

# Train the model
for epoch in range(100):
    optimizer.zero_grad()
    output = model(torch.randn(10, 5))
    loss = criterion(output, torch.randn(10, 5))
    loss.backward()
    optimizer.step()
```

## 3. Attention Maps, Kernel Mechanics & Latent Geometry

Attention mechanisms have revolutionized the field of natural language processing, enabling models to focus on relevant parts of the input sequence. At its core, attention is a weighted sum of the input elements, with the weights determined by a learnable attention map.

The attention map is typically computed using a combination of the input elements and a set of learnable parameters. This computation is often performed using a softmax function, which ensures that the weights sum to 1. The resulting attention weights are then used to compute the weighted sum of the input elements.

Kernel mechanics play a crucial role in understanding the attention mechanism, as they govern the interaction between the input elements and the attention weights. The kernel is typically a small, fixed-size window that slides over the input sequence, computing a weighted sum of the input elements at each position.

Latent geometry is another key aspect of attention mechanisms, as it governs the relationship between the input elements and the attention weights. The latent space is typically a high-dimensional space that captures the underlying structure of the input data.

```python
import torch
import torch.nn as nn

# Define an attention mechanism
class Attention(nn.Module):
    def __init__(self, num_heads, hidden_size):
        super(Attention, self).__init__()
        self.num_heads = num_heads
        self.hidden_size = hidden_size
        self.query_key_value = nn.Linear(hidden_size, 3 * hidden_size)

    def forward(self, input):
        # Compute the attention weights
        query_key_value = self.query_key_value(input)
        query, key, value = query_key_value.chunk(3, dim=-1)
        attention_weights = torch.matmul(query, key.transpose(-1, -2)) / math.sqrt(self.hidden_size)
        attention_weights = torch.softmax(attention_weights, dim=-1)

        # Compute the weighted sum of the input elements
        output = torch.matmul(attention_weights, value)

        return output
```

This concludes Lesson 2: Core Architecture & Algorithmic Mechanics. In this lesson, we have dissected the internal algorithms, tensor operations, parameter scaling, and execution paths of modern neural networks. We have also explored the attention mechanism, kernel mechanics, and latent geometry, providing a deeper understanding of the underlying mechanics of neural networks.
