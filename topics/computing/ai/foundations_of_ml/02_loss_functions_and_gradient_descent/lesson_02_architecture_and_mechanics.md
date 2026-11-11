# Lesson 2: Core Architecture & Algorithmic Mechanics

## 1. Internal Representations & Data Structures

In the realm of machine learning, particularly within the context of deep learning frameworks, the internal representations and data structures play a pivotal role in the efficiency and effectiveness of model training and inference. These structures are meticulously designed to optimize memory usage, computational speed, and the ability to handle large-scale data. Let us delve into the core components of these representations, starting with vector embeddings, token structures, attention matrices, and parameter layouts.

### Vector Embeddings

Vector embeddings are a fundamental concept in natural language processing (NLP) and other domains where data is inherently high-dimensional and complex. An embedding is a mapping from discrete objects, such as words or phrases, into numerical vectors of fixed size. These vectors capture semantic relationships between the objects, enabling models to perform tasks like classification, clustering, and translation more effectively.

Consider a simple example of a word embedding. Suppose we have a vocabulary of 10,000 words, and we choose to represent each word as a 300-dimensional vector. The embedding matrix, denoted as \( E \), would be a \( 10,000 \times 300 \) matrix. Each row of this matrix corresponds to the vector representation of a word. During the forward pass of a neural network, the word indices are used to index into this matrix to retrieve the corresponding word vectors.

```
E = [
    [e_11, e_12, ..., e_1300],  # Vector for word 1
    [e_21, e_22, ..., e_2300],  # Vector for word 2
    ...
    [e_10000_1, e_10000_2, ..., e_10000_300]  # Vector for word 10,000
]
```

### Token Structures

Token structures are closely related to vector embeddings but pertain more to the preprocessing stage of text data. Tokenization is the process of breaking down text into smaller units, or tokens, which can be words, subwords, or characters. These tokens are then mapped to indices in the embedding matrix. The choice of tokenization strategy can significantly impact the performance of a model.

For instance, consider a sentence: "The quick brown fox jumps over the lazy dog." A simple word-level tokenization would yield the tokens: ["The", "quick", "brown", "fox", "jumps", "over", "the", "lazy", "dog"]. Each token is then mapped to an index in the embedding matrix. However, subword tokenization, as used in models like BERT, can capture morphological information more effectively. For example, the word "unhappiness" might be tokenized into ["un", "happy", "ness"], allowing the model to leverage the embeddings of "happy" and "ness" to understand "unhappiness."

### Attention Matrices

Attention mechanisms have revolutionized the field of NLP by enabling models to focus on relevant parts of the input data. The attention matrix is a key component of attention mechanisms, capturing the relationships between different elements in the input sequence. In the context of the Transformer architecture, the attention matrix is computed using the scaled dot-product attention formula:

\[
\text{Attention}(Q, K, V) = \text{softmax}\left(\frac{QK^T}{\sqrt{d_k}}\right)V
\]

Here, \( Q \) (query), \( K \) (key), and \( V \) (value) are matrices derived from the input embeddings. The attention matrix is a square matrix where each element \( \alpha_{ij} \) represents the attention score between the \( i \)-th query and the \( j \)-th key. This matrix is then used to weight the value vectors, allowing the model to focus on relevant parts of the input sequence.

```
Q = [
    [q_11, q_12, ..., q_1d_k],
    [q_21, q_22, ..., q_2d_k],
    ...
    [q_n1, q_n2, ..., q_nd_k]
]

K = [
    [k_11, k_12, ..., k_1d_k],
    [k_21, k_22, ..., k_2d_k],
    ...
    [k_m1, k_m2, ..., k_md_k]
]

V = [
    [v_11, v_12, ..., v_1d_v],
    [v_21, v_22, ..., v_2d_v],
    ...
    [v_m1, v_m2, ..., v_md_v]
]

Attention = softmax((QK^T) / sqrt(d_k)) * V
```

### Parameter Layouts

The layout of model parameters is crucial for efficient computation and memory management. In deep learning models, parameters are organized into layers, each with its own set of weights and biases. The layout of these parameters can significantly impact the performance of the model, particularly in terms of memory access patterns and computational efficiency.

Consider a simple feedforward neural network with two hidden layers. The parameter layout would consist of weight matrices and bias vectors for each layer. For example, if the input layer has 784 neurons (e.g., for a 28x28 pixel image), the first hidden layer has 128 neurons, and the second hidden layer has 64 neurons, the parameter layout would be as follows:

```
W1 = [
    [w1_11, w1_12, ..., w1_1128],
    [w1_21, w1_22, ..., w1_2128],
    ...
    [w1_7841, w1_7842, ..., w1_784128]
]

b1 = [b1_1, b1_2, ..., b1_128]

W2 = [
    [w2_11, w2_12, ..., w2_164],
    [w2_21, w2_22, ..., w2_264],
    ...
    [w2_1281, w2_1282, ..., w2_12864]
]

b2 = [b2_1, b2_2, ..., b2_64]
```

## 2. Forward Pass & Algorithmic Execution Lifecycle

The forward pass is the process of computing the output of a neural network given an input. It involves a series of mathematical operations that transform the input data through the layers of the network, ultimately producing the desired output. Let us trace the forward pass through a simple feedforward neural network with two hidden layers.

### Step-by-Step Mathematical Trace

Consider a feedforward neural network with the following architecture:

- Input layer: 784 neurons (e.g., for a 28x28 pixel image)
- First hidden layer: 128 neurons
- Second hidden layer: 64 neurons
- Output layer: 10 neurons (e.g., for a 10-class classification task)

The forward pass can be broken down into the following steps:

1. **Input Layer to First Hidden Layer:**

   The input vector \( x \) is multiplied by the weight matrix \( W1 \) and added to the bias vector \( b1 \). The result is passed through an activation function, such as the ReLU (Rectified Linear Unit) function.

   \[
   z1 = W1 \cdot x + b1
   \]
   \[
   a1 = \text{ReLU}(z1)
   \]

2. **First Hidden Layer to Second Hidden Layer:**

   The output of the first hidden layer \( a1 \) is multiplied by the weight matrix \( W2 \) and added to the bias vector \( b2 \). The result is passed through the ReLU activation function.

   \[
   z2 = W2 \cdot a1 + b2
   \]
   \[
   a2 = \text{ReLU}(z2)
   \]

3. **Second Hidden Layer to Output Layer:**

   The output of the second hidden layer \( a2 \) is multiplied by the weight matrix \( W3 \) and added to the bias vector \( b3 \). The result is passed through a softmax activation function to produce the final output probabilities.

   \[
   z3 = W3 \cdot a2 + b3
   \]
   \[
   \hat{y} = \text{softmax}(z3)
   \]

### Detailed Execution

Let us walk through a concrete example. Suppose the input vector \( x \) is a 784-dimensional vector representing a 28x28 pixel image. The weight matrices and bias vectors are initialized as follows:

```
W1 = [
    [w1_11, w1_12, ..., w1_1128],
    [w1_21, w1_22, ..., w1_2128],
    ...
    [w1_7841, w1_7842, ..., w1_784128]
]

b1 = [b1_1, b1_2, ..., b1_128]

W2 = [
    [w2_11, w2_12, ..., w2_164],
    [w2_21, w2_22, ..., w2_264],
    ...
    [w2_1281, w2_1282, ..., w2_12864]
]

b2 = [b2_1, b2_2, ..., b2_64]

W3 = [
    [w3_11, w3_12, ..., w3_110],
    [w3_21, w3_22, ..., w3_210],
    ...
    [w3_641, w3_642, ..., w3_6410]
]

b3 = [b3_1, b3_2, ..., b3_10]
```

The forward pass can be computed as follows:

1. **Input Layer to First Hidden Layer:**

   \[
   z1 = W1 \cdot x + b1
   \]
   \[
   a1 = \text{ReLU}(z1)
   \]

   Here, \( z1 \) is a 128-dimensional vector, and \( a1 \) is also a 128-dimensional vector after applying the ReLU activation function.

2. **First Hidden Layer to Second Hidden Layer:**

   \[
   z2 = W2 \cdot a1 + b2
   \]
   \[
   a2 = \text{ReLU}(z2)
   \]

   Here, \( z2 \) is a 64-dimensional vector, and \( a2 \) is also a 64-dimensional vector after applying the ReLU activation function.

3. **Second Hidden Layer to Output Layer:**

   \[
   z3 = W3 \cdot a2 + b3
   \]
   \[
   \hat{y} = \text{softmax}(z3)
   \]

   Here, \( z3 \) is a 10-dimensional vector, and \( \hat{y} \) is a 10-dimensional vector representing the output probabilities for each class.

## 3. Memory Footprint & Computational Complexity

The memory footprint and computational complexity of a neural network are critical factors that determine its efficiency and scalability. These factors are influenced by the architecture of the network, the size of the input data, and the hardware resources available.

### Memory Footprint

The memory footprint of a neural network is determined by the size of the model parameters and the intermediate activations during the forward pass. For a feedforward neural network with two hidden layers, the memory footprint can be calculated as follows:

- **Model Parameters:**

  The memory required to store the model parameters is determined by the size of the weight matrices and bias vectors. For example, the weight matrix \( W1 \) has a size of \( 784 \times 128 \), the bias vector \( b1 \) has a size of 128, the weight matrix \( W2 \) has a size of \( 128 \times 64 \), the bias vector \( b2 \) has a size of 64, the weight matrix \( W3 \) has a size of \( 64 \times 10 \), and the bias vector \( b3 \) has a size of 10.

  ```
  Memory for W1 = 784 * 128 * 4 bytes = 401,408 bytes
  Memory for b1 = 128 * 4 bytes = 512 bytes
  Memory for W2 = 128 * 64 * 4 bytes = 32,768 bytes
  Memory for b2 = 64 * 4 bytes = 256 bytes
  Memory for W3 = 64 * 10 * 4 bytes = 2,560 bytes
  Memory for b3 = 10 * 4 bytes = 40 bytes
  Total memory for parameters = 435,544 bytes
  ```

- **Intermediate Activations:**

  The memory required to store the intermediate activations during the forward pass is determined by the size of the activation vectors. For example, the activation vector \( a1 \) has a size of 128, the activation vector \( a2 \) has a size of 64, and the output vector \( \hat{y} \) has a size of 10.

  ```
  Memory for a1 = 128 * 4 bytes = 512 bytes
  Memory for a2 = 64 * 4 bytes = 256 bytes
  Memory for z3 = 10 * 4 bytes = 40 bytes
  Memory for \hat{y} = 10 * 4 bytes = 40 bytes
  Total memory for activations = 856 bytes
  ```

  The total memory footprint for the model is the sum of the memory required to store the model parameters and the intermediate activations.

  ```
  Total memory footprint = 435,544 bytes + 856 bytes = 436,400 bytes
  ```

### Computational Complexity

The computational complexity of a neural network is determined by the number of operations required to perform the forward pass and backward pass. For a feedforward neural network with two hidden layers, the computational complexity can be calculated as follows:

- **Forward Pass:**

  The forward pass involves matrix multiplications and element-wise operations. The computational complexity of the forward pass is determined by the number of multiplications and additions required to compute the intermediate activations.

  - **Input Layer to First Hidden Layer:**

    The computational complexity of the matrix multiplication \( W1 \cdot x \) is \( 784 \times 128 \), and the computational complexity of the element-wise addition \( z1 + b1 \) is \( 128 \). The computational complexity of the ReLU activation function is \( 128 \).

    ```
    Computational complexity for W1 \cdot x = 784 * 128 = 100,352
    Computational complexity for z1 + b1 = 128
    Computational complexity for ReLU(z1) = 128
    Total computational complexity for input to first hidden layer = 100,640
    ```

  - **First Hidden Layer to Second Hidden Layer:**

    The computational complexity of the matrix multiplication \( W2 \cdot a1 \) is \( 128 \times 64 \), and the computational complexity of the element-wise addition \( z2 + b2 \) is \( 64 \). The computational complexity of the ReLU activation function is \( 64 \).

    ```
    Computational complexity for W2 \cdot a1 = 128 * 64 = 8,192
    Computational complexity for z2 + b2 = 64
    Computational complexity for ReLU(z2) = 64
    Total computational complexity for first hidden layer to second hidden layer = 8,320
    ```

  - **Second Hidden Layer to Output Layer:**

    The computational complexity of the matrix multiplication \( W3 \cdot a2 \) is \( 64 \times 10 \), and the computational complexity of the element-wise addition \( z3 + b3 \) is \( 10 \). The computational complexity of the softmax activation function is \( 10 \).

    ```
    Computational complexity for W3 \cdot a2 = 64 * 10 = 640
    Computational complexity for z3 + b3 = 10
    Computational complexity for softmax(z3) = 10
    Total computational complexity for second hidden layer to output layer = 660
    ```

    The total computational complexity of the forward pass is the sum of the computational complexities of the individual layers.

    ```
    Total computational complexity for forward pass = 100,640 + 8,320 + 660 = 109,620
    ```

- **Backward Pass:**

  The backward pass involves computing the gradients of the loss function with respect to the model parameters. The computational complexity of the backward pass is determined by the number of operations required to compute the gradients.

  - **Output Layer to Second Hidden Layer:**

    The computational complexity of the matrix multiplication \( W3^T \cdot \delta3 \) is \( 10 \times 64 \), and the computational complexity of the element-wise multiplication \( \delta3 \cdot \text{ReLU}'(z3) \) is \( 10 \).

    ```
    Computational complexity for W3^T \cdot \delta3 = 10 * 64 = 640
    Computational complexity for \delta3 \cdot \text{ReLU}'(z3) = 10
    Total computational complexity for output layer to second hidden layer = 650
    ```

  - **Second Hidden Layer to First Hidden Layer:**

    The computational complexity of the matrix multiplication \( W2^T \cdot \delta2 \) is \( 64 \times 128 \), and the computational complexity of the element-wise multiplication \( \delta2 \cdot \text{ReLU}'(z2) \) is \( 64 \).

    ```
    Computational complexity for W2^T \cdot \delta2 = 64 * 128 = 8,192
    Computational complexity for \delta2 \cdot \text{ReLU}'(z2) = 64
    Total computational complexity for second hidden layer to first hidden layer = 8,256
    ```

  - **First Hidden Layer to Input Layer:**

    The computational complexity of the matrix multiplication \( W1^T \cdot \delta1 \) is \( 128 \times 784 \), and the computational complexity of the element-wise multiplication \( \delta1 \cdot \text{ReLU}'(z1) \) is \( 128 \).

    ```
    Computational complexity for W1^T \cdot \delta1 = 128 * 784 = 100,352
    Computational complexity for \delta1 \cdot \text{ReLU}'(z1) = 128
    Total computational complexity for first hidden layer to input layer = 100,480
    ```

    The total computational complexity of the backward pass is the sum of the computational complexities of the individual layers.

    ```
    Total computational complexity for backward pass = 650 + 8,256 + 100,480 = 109,386
    ```

### Hardware Accelerator Mapping

The computational complexity of a neural network can be significantly reduced by leveraging hardware accelerators such as GPUs and TPUs. These accelerators are designed to perform parallel computations, which can significantly speed up the forward and backward passes of a neural network.

For example, a GPU can perform matrix multiplications and element-wise operations in parallel, which can significantly reduce the computational complexity of the forward and backward passes. The memory footprint of a neural network can also be optimized by using techniques such as memory pooling and data compression.

In conclusion, the internal representations and data structures, forward pass execution lifecycle, memory footprint, and computational complexity are critical components of a neural network. Understanding these components is essential for designing efficient and effective machine learning models. By leveraging hardware accelerators and optimizing memory usage, we can significantly improve the performance of neural networks and enable the training of larger and more complex models.
