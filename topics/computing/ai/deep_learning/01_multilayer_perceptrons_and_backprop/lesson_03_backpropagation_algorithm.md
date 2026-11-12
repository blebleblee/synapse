# Lesson 3: Backpropagation Algorithm

## 1. First-Principles Intuition & Invariants

At the heart of modern machine learning lies a mathematical procedure that mirrors the way biological neural networks adapt and learn from experience: the backpropagation algorithm. This algorithm is not merely a computational trick—it is a fundamental mechanism for optimizing differentiable functions by leveraging the chain rule of calculus. To understand backpropagation, one must grasp the nature of the problem it solves: the minimization of a loss function over a set of parameters in a neural network.

Consider a multilayer perceptron (MLP), a feedforward neural network composed of an input layer, one or more hidden layers, and an output layer. Each node in a layer is connected to every node in the subsequent layer, forming a directed acyclic graph. The network computes a mapping from input features to outputs through a series of weighted linear transformations followed by nonlinear activation functions. The goal of training such a network is to adjust the weights and biases so that the network's predictions closely approximate the true labels in the training dataset.

The loss function, typically defined as the mean squared error or cross-entropy, quantifies the discrepancy between the network's predictions and the actual labels. Minimizing this loss function is the objective of training. However, the loss function is a high-dimensional, nonlinear function of the network’s parameters—weights and biases. Gradient-based optimization methods, such as stochastic gradient descent (SGD), are employed to iteratively update these parameters in the direction of steepest descent of the loss function.

The backpropagation algorithm is the computational engine that enables gradient computation in this context. It operates by propagating the error from the output layer backward through the network, layer by layer, to compute the gradient of the loss function with respect to each parameter. This process is predicated on the chain rule of calculus, which allows the computation of complex derivatives by decomposing them into simpler, local derivatives.

Mathematically, let us define a simple MLP with one hidden layer. Let `x` be the input vector, `W^(1)` and `b^(1)` be the weights and biases of the first layer, and `W^(2)` and `b^(2)` be the weights and biases of the second layer. Let `σ` be the activation function, such as the sigmoid or ReLU. The forward pass computes:

```
z^(1) = W^(1) * x + b^(1)
a^(1) = σ(z^(1))
z^(2) = W^(2) * a^(1) + b^(2)
y = σ(z^(2))
```

Here, `y` is the network’s output, and `y*` is the true label. The loss function `L` is typically defined as:

```
L = 0.5 * || y - y* ||^2
```

The backpropagation algorithm computes the gradients `∂L/∂W^(1)`, `∂L/∂b^(1)`, `∂L/∂W^(2)`, and `∂L/∂b^(2)`. These gradients are then used to update the parameters via gradient descent:

```
W^(l) = W^(l) - η * ∂L/∂W^(l)
b^(l) = b^(l) - η * ∂L/∂b^(l)
```

where `η` is the learning rate.

The invariants of backpropagation are rooted in the differentiability of the activation functions and the structure of the network. The algorithm assumes that the activation functions are differentiable, allowing for the application of the chain rule. It also assumes that the network is fully connected and that the loss function is differentiable with respect to the parameters. These assumptions ensure that the gradients computed are meaningful and can be used to update the parameters effectively.

## 2. Core Architecture & Mechanics

The backpropagation algorithm is a recursive process that operates on the computational graph of the neural network. Each node in the graph corresponds to a computation, such as a matrix-vector product or an activation function application. The algorithm computes the gradient of the loss function with respect to each node's input and output, enabling the gradient of the loss with respect to each parameter to be derived.

The algorithm proceeds in two phases: the forward pass and the backward pass. During the forward pass, the network computes the activations for each layer, storing intermediate values such as `z^(1)`, `a^(1)`, `z^(2)`, and `y`. These stored values are essential for the backward pass.

In the backward pass, the algorithm starts from the output layer and computes the error signal, or gradient of the loss with respect to the layer's output. For a single output neuron, the error is:

```
δ^(2) = ∂L/∂z^(2) = ∂L/∂y * ∂y/∂z^(2) = (y - y*) * σ'(z^(2))
```

This error signal is then propagated backward to compute the error for the hidden layer:

```
δ^(1) = ∂L/∂z^(1) = (W^(2))^T * δ^(2) * σ'(z^(1))
```

From these error signals, the gradients of the loss with respect to the parameters are computed:

```
∂L/∂W^(2) = δ^(2) * (a^(1))^T
∂L/∂b^(2) = δ^(2)
∂L/∂W^(1) = δ^(1) * x^T
∂L/∂b^(1) = δ^(1)
```

These gradients are then used to update the parameters in the direction of steepest descent.

The architecture of backpropagation is inherently sequential in its computation of gradients, but the computation of each gradient is independent of others, allowing for parallelization. For instance, the computation of `δ^(2)` and `δ^(1)` can be done in parallel, as can the computation of the gradients for each layer. This parallelization is crucial for performance in large networks and is typically implemented using optimized libraries such as TensorFlow or PyTorch.

The core invariants of the backpropagation algorithm are the preservation of differentiability and the correct application of the chain rule. The algorithm must ensure that the computation of gradients is consistent with the forward pass, and that the gradients are computed with respect to the correct parameters. These invariants are enforced through careful implementation and validation of the algorithm.
