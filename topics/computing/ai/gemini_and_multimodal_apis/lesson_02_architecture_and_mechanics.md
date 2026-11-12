# Lesson 2: Core Architecture & Algorithmic Mechanics

## 1. Tensor Transformations & Dimensional Flows

Tensor transformations are the backbone of modern deep learning architectures. Understanding the mechanics of tensor operations is crucial for designing efficient and effective neural networks. In this section, we'll delve into the fundamental principles of tensor transformations, exploring the intricacies of dimensional flows, reshaping, and broadcasting.

Tensor operations are typically performed on multi-dimensional arrays, where each dimension represents a specific aspect of the data. When working with tensors, it's essential to understand the concept of dimensionality, which is often denoted by the number of dimensions (D) or the tensor's shape (e.g., (3, 224, 224) for a 3D tensor with dimensions 3, 224, and 224). The dimensionality of a tensor determines the number of elements it contains, and it's a critical factor in determining the computational complexity of tensor operations.

One of the most fundamental tensor operations is reshaping, which involves rearranging the elements of a tensor to conform to a new shape. Reshaping is often used to transform data between different formats, such as converting a 3D tensor to a 2D tensor or vice versa. The reshaping operation is typically performed using the `tf.reshape()` function in TensorFlow or the `torch.reshape()` function in PyTorch.

Another essential tensor operation is broadcasting, which allows tensors with different shapes to be combined element-wise. Broadcasting is a powerful mechanism for performing operations on tensors with different dimensions, and it's widely used in deep learning architectures. The broadcasting rules are as follows:

* If the two tensors have the same shape, they can be broadcasted element-wise.
* If one tensor has a shape of (a, b, c) and the other has a shape of (a, b), they can be broadcasted along the c dimension.
* If one tensor has a shape of (a, b) and the other has a shape of (a), they can be broadcasted along the b dimension.

Broadcasting is often used in conjunction with reshaping to perform complex tensor operations. For example, when computing the convolutional output of a neural network, the input tensor is typically reshaped to conform to the kernel shape, and then broadcasted to match the output shape.

To illustrate the mechanics of tensor transformations, let's consider a simple example. Suppose we have a 3D tensor `x` with shape (3, 224, 224) representing an image, and we want to compute the convolutional output using a kernel with shape (5, 5). We can perform the convolution operation by reshaping the input tensor to conform to the kernel shape, and then broadcasting the result to match the output shape.

```python
import tensorflow as tf

# Define the input tensor
x = tf.random.normal((3, 224, 224))

# Define the kernel
kernel = tf.random.normal((5, 5))

# Reshape the input tensor
x_reshaped = tf.reshape(x, (3, 224, 224, 1))

# Perform the convolution operation
output = tf.nn.conv2d(x_reshaped, kernel, strides=[1, 1, 1, 1], padding='SAME')

# Print the output shape
print(output.shape)
```

## 2. Loss Surfaces, Gradients & Optimization Dynamics

Loss surfaces are a fundamental concept in deep learning, representing the landscape of possible solutions to a given optimization problem. In this section, we'll delve into the mechanics of loss surfaces, exploring the intricacies of gradient descent, optimization dynamics, and convergence.

Loss surfaces are typically represented as a function of the model parameters, and they can be visualized using techniques such as contour plots or 3D surface plots. The loss surface is often characterized by its curvature, which determines the rate of convergence of the optimization algorithm.

One of the most widely used optimization algorithms in deep learning is stochastic gradient descent (SGD), which iteratively updates the model parameters based on the gradient of the loss function. The gradient is computed using the chain rule, which states that the derivative of a composite function is the product of the derivatives of the individual components.

The gradient descent algorithm can be formulated as follows:

* Initialize the model parameters `w` to a random value.
* Compute the gradient of the loss function `L` with respect to the model parameters `w` using the chain rule.
* Update the model parameters `w` using the gradient descent update rule: `w = w - α ∇L(w)`, where `α` is the learning rate.

The gradient descent algorithm is widely used in deep learning due to its simplicity and effectiveness. However, it can be slow to converge, especially for large models or complex loss functions. To address this issue, various optimization algorithms have been developed, including momentum-based methods, Nesterov acceleration, and Adam.

To illustrate the mechanics of loss surfaces and gradient descent, let's consider a simple example. Suppose we have a linear regression model with a single parameter `w`, and we want to minimize the mean squared error (MSE) loss function. We can compute the gradient of the loss function using the chain rule, and then update the model parameter using the gradient descent update rule.

```python
import numpy as np

# Define the loss function
def loss(w):
    return np.mean((w * x - y) ** 2)

# Compute the gradient of the loss function
def gradient(w):
    return np.mean(2 * (w * x - y) * x)

# Initialize the model parameter
w = np.random.rand()

# Perform gradient descent
for i in range(1000):
    w = w - 0.01 * gradient(w)
    print(f"Iteration {i+1}: w = {w}")
```

## 3. Attention Maps, Kernel Mechanics & Latent Geometry

Attention mechanisms are a fundamental component of modern deep learning architectures, enabling models to selectively focus on specific parts of the input data. In this section, we'll delve into the mechanics of attention maps, exploring the intricacies of kernel mechanics and latent geometry.

Attention mechanisms typically involve computing a weighted sum of the input features, where the weights are learned during training. The attention weights are often computed using a softmax function, which ensures that the weights sum to 1.

One of the most widely used attention mechanisms is the transformer attention mechanism, which involves computing the attention weights as a function of the input features and the model parameters. The attention weights are then used to compute the weighted sum of the input features, which is used as input to the next layer.

To illustrate the mechanics of attention maps, let's consider a simple example. Suppose we have a sequence of input features `x = [x1, x2, ..., xn]`, and we want to compute the attention weights using the transformer attention mechanism. We can compute the attention weights as follows:

```python
import numpy as np

# Define the input features
x = np.random.rand(10, 128)

# Compute the attention weights
attention_weights = np.softmax(np.dot(x, x.T) / np.sqrt(x.shape[1]))

# Print the attention weights
print(attention_weights)
```

This code computes the attention weights as a function of the input features `x` and the model parameters. The attention weights are then printed to the console.

Note that this is a simplified example, and in practice, the attention mechanism is often used in conjunction with other components, such as convolutional layers and recurrent layers.
