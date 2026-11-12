# Lesson 2: Core Architecture & Algorithmic Mechanics

## 1. Internal Representations & Data Structures

In the realm of machine learning, the internal representations and data structures are the bedrock upon which the edifice of neural networks and other models is constructed. These structures are not merely containers for data but are deeply intertwined with the algorithms that manipulate them, influencing both the efficiency and the effectiveness of the learning process.

### Vector Embeddings

Vector embeddings are a fundamental concept in modern machine learning, particularly in natural language processing (NLP). They provide a way to represent discrete data, such as words or phrases, in a continuous vector space. Each word or token is mapped to a high-dimensional vector, where the dimensions capture semantic and syntactic relationships between the words. For instance, in a well-trained word embedding, the vectors for "king" and "queen" might be close to each other, reflecting their semantic similarity, while the vector for "king" minus the vector for "man" plus the vector for "woman" might be close to the vector for "queen," illustrating the model's ability to capture analogies.

Consider a simple example of a word embedding matrix. Suppose we have a vocabulary of 10,000 words, and each word is represented by a 300-dimensional vector. The embedding matrix would be a 10,000 by 300 matrix, where each row corresponds to a word in the vocabulary. This matrix can be visualized as follows:

```
[ [0.1, -0.2, 0.3, ..., 0.4],  # Embedding for word 1
  [0.2, 0.1, -0.3, ..., -0.2], # Embedding for word 2
  ...
  [-0.1, 0.3, 0.2, ..., 0.1]   # Embedding for word 10,000
]
```

Each entry in the matrix is a floating-point number that encodes the semantic and syntactic properties of the corresponding word. The choice of 300 dimensions is somewhat arbitrary but has become a standard in the field due to its balance between expressiveness and computational efficiency.

### Token Structures

Token structures are another critical component in the representation of data, especially in sequence-based models like recurrent neural networks (RNNs) and transformers. Tokens are the basic units of input to these models, and they can represent words, subwords, or even characters, depending on the tokenization strategy. For example, in a word-level tokenization, the sentence "The quick brown fox" would be represented as a sequence of tokens: ["The", "quick", "brown", "fox"]. In contrast, a subword-level tokenization might break down the sentence into smaller units, such as ["The", "qui", "ck", "brown", "fox"], which can help capture morphological information and reduce the vocabulary size.

The tokenization process is often accompanied by a vocabulary mapping, which assigns a unique integer index to each token. This mapping is essential for converting the input sequence into a format that can be processed by the model. For instance, if the vocabulary consists of 10,000 tokens, each token would be represented by an integer between 0 and 9,999. The input sequence ["The", "quick", "brown", "fox"] would be converted to a sequence of indices, such as [1, 2, 3, 4].

### Attention Matrices

Attention mechanisms have revolutionized the field of machine learning, particularly in NLP, by allowing models to focus on different parts of the input sequence when making predictions. The attention mechanism computes a weighted sum of the input vectors, where the weights are determined by the relevance of each input element to the current context. This mechanism is particularly powerful in transformer models, where it enables the model to capture long-range dependencies and complex relationships between the input elements.

The attention mechanism can be visualized as a matrix, where each entry represents the attention score between a pair of input elements. For example, in a transformer model with a sequence length of 10, the attention matrix would be a 10 by 10 matrix, where the entry at position (i, j) represents the attention score between the i-th and j-th input elements. This matrix can be visualized as follows:

```
[ [0.1, 0.2, 0.05, ..., 0.01],  # Attention scores for element 1
  [0.05, 0.1, 0.2, ..., 0.02], # Attention scores for element 2
  ...
  [0.01, 0.02, 0.05, ..., 0.1]   # Attention scores for element 10
]
```

Each entry in the matrix is a floating-point number between 0 and 1, representing the attention score. The attention scores are typically computed using a softmax function, which ensures that the scores sum to 1 for each row, reflecting the model's focus on different parts of the input sequence.

### Parameter Layouts

The parameters of a machine learning model are the weights and biases that are learned during training. These parameters are organized into layers, where each layer performs a specific transformation on the input data. The layout of the parameters is crucial for the efficiency and effectiveness of the model, as it determines how the parameters are accessed and updated during training.

Consider a simple feedforward neural network with two hidden layers. The parameter layout would consist of the weights and biases for each layer. For example, if the input layer has 100 neurons, the first hidden layer has 50 neurons, and the second hidden layer has 20 neurons, the parameter layout would be as follows:

- Weights for the input to first hidden layer: a 100 by 50 matrix
- Biases for the first hidden layer: a 50-dimensional vector
- Weights for the first hidden to second hidden layer: a 50 by 20 matrix
- Biases for the second hidden layer: a 20-dimensional vector

The parameter layout can be visualized as follows:

```
[ [ [w11, w12, ..., w150],  # Weights for input to first hidden layer
    [w21, w22, ..., w250],
    ...
    [w1001, w1002, ..., w10050]
  ],
  [b1, b2, ..., b50],         # Biases for first hidden layer
  [ [w11, w12, ..., w120],  # Weights for first hidden to second hidden layer
    [w21, w22, ..., w220],
    ...
    [w501, w502, ..., w5020]
  ],
  [b1, b2, ..., b20]          # Biases for second hidden layer
]
```

Each entry in the parameter layout is a floating-point number, representing a weight or bias. The weights and biases are updated during training using gradient descent, which adjusts the parameters to minimize the loss function.

## 2. Forward Pass & Algorithmic Execution Lifecycle

The forward pass is the process of computing the output of a machine learning model given an input. It involves a series of transformations, where each layer applies a specific function to the input data, and the output of one layer becomes the input to the next layer. The forward pass is a critical component of the training and inference processes, as it determines how the input data is transformed into the final output.

### Mathematical Trace of Inference/Execution

To understand the forward pass, let's consider a simple feedforward neural network with two hidden layers. The forward pass can be broken down into a series of mathematical operations, where each layer applies a linear transformation followed by a non-linear activation function. For example, if the input layer has 100 neurons, the first hidden layer has 50 neurons, and the second hidden layer has 20 neurons, the forward pass can be visualized as follows:

1. **Input Layer**: The input data is represented as a 100-dimensional vector, denoted as \( \mathbf{x} \).
2. **First Hidden Layer**: The input data is transformed using the weights and biases of the first hidden layer. The linear transformation is given by \( \mathbf{z}_1 = \mathbf{W}_1 \mathbf{x} + \mathbf{b}_1 \), where \( \mathbf{W}_1 \) is a 100 by 50 matrix of weights, and \( \mathbf{b}_1 \) is a 50-dimensional vector of biases. The non-linear activation function is applied to the linear transformation, resulting in the output of the first hidden layer, denoted as \( \mathbf{a}_1 = \sigma(\mathbf{z}_1) \), where \( \sigma \) is the activation function (e.g., ReLU, sigmoid, or tanh).
3. **Second Hidden Layer**: The output of the first hidden layer is transformed using the weights and biases of the second hidden layer. The linear transformation is given by \( \mathbf{z}_2 = \mathbf{W}_2 \mathbf{a}_1 + \mathbf{b}_2 \), where \( \mathbf{W}_2 \) is a 50 by 20 matrix of weights, and \( \mathbf{b}_2 \) is a 20-dimensional vector of biases. The non-linear activation function is applied to the linear transformation, resulting in the output of the second hidden layer, denoted as \( \mathbf{a}_2 = \sigma(\mathbf{z}_2) \).
4. **Output Layer**: The output of the second hidden layer is transformed using the weights and biases of the output layer. The linear transformation is given by \( \mathbf{z}_3 = \mathbf{W}_3 \mathbf{a}_2 + \mathbf{b}_3 \), where \( \mathbf{W}_3 \) is a 20 by 1 matrix of weights, and \( \mathbf{b}_3 \) is a 1-dimensional vector of biases. The final output of the model is obtained by applying the output activation function, denoted as \( \mathbf{y} = \sigma(\mathbf{z}_3) \).

The forward pass can be summarized as follows:

\[
\mathbf{z}_1 = \mathbf{W}_1 \mathbf{x} + \mathbf{b}_1
\]
\[
\mathbf{a}_1 = \sigma(\mathbf{z}_1)
\]
\[
\mathbf{z}_2 = \mathbf{W}_2 \mathbf{a}_1 + \mathbf{b}_2
\]
\[
\mathbf{a}_2 = \sigma(\mathbf{z}_2)
\]
\[
\mathbf{z}_3 = \mathbf{W}_3 \mathbf{a}_2 + \mathbf{b}_3
\]
\[
\mathbf{y} = \sigma(\mathbf{z}_3)
\]

Each step in the forward pass involves a series of matrix-vector multiplications and element-wise operations, which are performed using efficient linear algebra libraries. The choice of activation function and the architecture of the network determine the properties of the forward pass, such as the non-linearity and the capacity of the model.

### Step-by-Step Mathematical Trace

To illustrate the forward pass in more detail, let's consider a simple example with specific values. Suppose the input data is a 100-dimensional vector, denoted as \( \mathbf{x} = [x_1, x_2, \ldots, x_{100}] \). The weights and biases of the first hidden layer are given by \( \mathbf{W}_1 = [w_{ij}] \) and \( \mathbf{b}_1 = [b_1, b_2, \ldots, b_{50}] \), where \( w_{ij} \) is the weight connecting the i-th input neuron to the j-th hidden neuron, and \( b_j \) is the bias of the j-th hidden neuron. The linear transformation is given by:

\[
z_{1j} = \sum_{i=1}^{100} w_{ij} x_i + b_j
\]

The non-linear activation function is applied to the linear transformation, resulting in the output of the first hidden layer, denoted as \( \mathbf{a}_1 = [a_{11}, a_{12}, \ldots, a_{150}] \), where \( a_{1j} = \sigma(z_{1j}) \).

The weights and biases of the second hidden layer are given by \( \mathbf{W}_2 = [w_{ij}] \) and \( \mathbf{b}_2 = [b_1, b_2, \ldots, b_{20}] \), where \( w_{ij} \) is the weight connecting the i-th hidden neuron to the j-th hidden neuron, and \( b_j \) is the bias of the j-th hidden neuron. The linear transformation is given by:

\[
z_{2j} = \sum_{i=1}^{50} w_{ij} a_{1i} + b_j
\]

The non-linear activation function is applied to the linear transformation, resulting in the output of the second hidden layer, denoted as \( \mathbf{a}_2 = [a_{21}, a_{22}, \ldots, a_{220}] \), where \( a_{2j} = \sigma(z_{2j}) \).

The weights and biases of the output layer are given by \( \mathbf{W}_3 = [w_{ij}] \) and \( \mathbf{b}_3 = [b_1] \), where \( w_{ij} \) is the weight connecting the i-th hidden neuron to the output neuron, and \( b_1 \) is the bias of the output neuron. The linear transformation is given by:

\[
z_{31} = \sum_{i=1}^{20} w_{i1} a_{2i} + b_1
\]

The final output of the model is obtained by applying the output activation function, denoted as \( y = \sigma(z_{31}) \).

The forward pass can be summarized as follows:

\[
z_{1j} = \sum_{i=1}^{100} w_{ij} x_i + b_j
\]
\[
a_{1j} = \sigma(z_{1j})
\]
\[
z_{2j} = \sum_{i=1}^{50} w_{ij} a_{1i} + b_j
\]
\[
a_{2j} = \sigma(z_{2j})
\]
\[
z_{31} = \sum_{i=1}^{20} w_{i1} a_{2i} + b_1
\]
\[
y = \sigma(z_{31})
\]

Each step in the forward pass involves a series of matrix-vector multiplications and element-wise operations, which are performed using efficient linear algebra libraries. The choice of activation function and the architecture of the network determine the properties of the forward pass, such as the non-linearity and the capacity of the model.

## 3. Memory Footprint & Computational Complexity

The memory footprint and computational complexity of a machine learning model are critical factors that determine its efficiency and scalability. The memory footprint refers to the amount of memory required to store the model parameters and intermediate activations, while the computational complexity refers to the amount of computational resources required to perform the forward and backward passes.

### KV-Cache Scaling

In transformer models, the key-value (KV) cache is a crucial component that stores the intermediate activations of the attention mechanism. The KV cache is used to speed up the inference process by avoiding redundant computations. The size of the KV cache is determined by the sequence length and the number of attention heads, and it can have a significant impact on the memory footprint and computational complexity of the model.

Consider a transformer model with a sequence length of 1024 and 16 attention heads. The KV cache would store the intermediate activations for each attention head, resulting in a memory footprint of approximately 16 * 1024 * 1024 * 4 bytes, assuming each activation is represented by a 32-bit floating-point number. This memory footprint can be further reduced by using techniques such as quantization, which reduces the precision of the activations, or by using sparse attention mechanisms, which only store the activations for a subset of the input elements.

### Parameter Memory Allocation

The memory footprint of a machine learning model is also determined by the number of parameters, which are stored in the parameter layout. The parameter layout is organized into layers, where each layer stores the weights and biases for a specific transformation. The memory footprint of the parameter layout is determined by the size of the weights and biases, which are typically represented by 32-bit or 16-bit floating-point numbers.

Consider a simple feedforward neural network with two hidden layers. The parameter layout would consist of the weights and biases for each layer. For example, if the input layer has 100 neurons, the first hidden layer has 50 neurons, and the second hidden layer has 20 neurons, the parameter layout would be as follows:

- Weights for the input to first hidden layer: a 100 by 50 matrix, requiring 100 * 50 * 4 bytes
- Biases for the first hidden layer: a 50-dimensional vector, requiring 50 * 4 bytes
- Weights for the first hidden to second hidden layer: a 50 by 20 matrix, requiring 50 * 20 * 4 bytes
- Biases for the second hidden layer: a 20-dimensional vector, requiring 20 * 4 bytes

The total memory footprint of the parameter layout would be approximately 100 * 50 * 4 + 50 * 4 + 50 * 20 * 4 + 20 * 4 bytes, assuming each weight and bias is represented by a 32-bit floating-point number. The memory footprint can be further reduced by using techniques such as quantization, which reduces the precision of the weights and biases, or by using sparse parameterizations, which only store the non-zero weights and biases.

### Computational Complexity O(...) Bounds

The computational complexity of a machine learning model is determined by the number of operations required to perform the forward and backward passes. The computational complexity is typically expressed using Big O notation, which provides an upper bound on the number of operations required as a function of the input size.

Consider a simple feedforward neural network with two hidden layers. The forward pass involves a series of matrix-vector multiplications and element-wise operations, where each layer applies a specific transformation to the input data. The computational complexity of the forward pass is determined by the size of the matrices and vectors, and it can be expressed using Big O notation as follows:

- Matrix-vector multiplication for input to first hidden layer: O(100 * 50)
- Element-wise operation for first hidden layer: O(50)
- Matrix-vector multiplication for first hidden to second hidden layer: O(50 * 20)
- Element-wise operation for second hidden layer: O(20)
- Matrix-vector multiplication for second hidden to output layer: O(20 * 1)
- Element-wise operation for output layer: O(1)

The total computational complexity of the forward pass would be approximately O(100 * 50 + 50 + 50 * 20 + 20 + 20 * 1 + 1) = O(5221) operations. The computational complexity can be further reduced by using techniques such as parallelization, which distributes the operations across multiple processors, or by using approximate algorithms, which trade off accuracy for speed.

### Hardware Accelerator Mapping

The memory footprint and computational complexity of a machine learning model can be further optimized by mapping the operations to hardware accelerators, such as GPUs or TPUs. Hardware accelerators are specialized processors that are designed to perform specific operations, such as matrix-vector multiplications, more efficiently than general-purpose CPUs. The mapping of operations to hardware accelerators can significantly reduce the memory footprint and computational complexity of the model, enabling faster training and inference.

Consider a simple feedforward neural network with two hidden layers. The forward pass involves a series of matrix-vector multiplications and element-wise operations, which can be mapped to hardware accelerators using libraries such as cuBLAS or cuDNN. The mapping of operations to hardware accelerators can be performed using techniques such as tensor tiling, which divides the matrices and vectors into smaller tiles that can be processed in parallel, or by using automatic differentiation, which generates efficient code for the forward and backward passes.

The mapping of operations to hardware accelerators can significantly reduce the memory footprint and computational complexity of the model, enabling faster training and inference. For example, a simple feedforward neural network with two hidden layers can be mapped to a GPU using cuBLAS, resulting in a memory footprint of approximately 100 * 50 * 4 + 50 * 4 + 50 * 20 * 4 + 20 * 4 bytes and a computational complexity of approximately O(5221) operations, assuming each weight and bias is represented by a 32-bit floating-point number and each operation is performed in parallel on the GPU.

In summary, the internal representations and data structures, forward pass, memory footprint, and computational complexity are critical components of the core architecture and algorithmic mechanics of machine learning models. The choice of internal representations and data structures determines the efficiency and effectiveness of the model, while the forward pass determines how the input data is transformed into the final output. The memory footprint and computational complexity determine the efficiency and scalability of the model, and they can be optimized using techniques such as quantization, parallelization, and hardware acceleration. By understanding these components, machine learning engineers and AI practitioners can design and implement models that are both efficient and effective.
