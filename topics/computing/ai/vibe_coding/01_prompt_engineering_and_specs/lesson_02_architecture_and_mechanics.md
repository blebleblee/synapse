# Lesson 2: Core Architecture & Algorithmic Mechanics

## 1. Internal Representations & Data Structures

In the realm of machine learning, particularly within the context of deep learning frameworks, understanding the internal representations and data structures is paramount. These structures underpin the efficiency and effectiveness of model inference and training. We will delve into vector embeddings, token structures, attention matrices, and parameter layouts, providing a comprehensive view of how data is represented and manipulated within these systems.

### Vector Embeddings

Vector embeddings are a fundamental concept in modern machine learning, especially in natural language processing (NLP). They represent words, phrases, or even entire documents as dense vectors in a continuous vector space. This transformation allows for the capture of semantic relationships between entities, enabling tasks such as sentiment analysis, machine translation, and information retrieval.

Consider a simple example where we have a vocabulary of 10,000 words. Each word is represented as a 300-dimensional vector. This representation can be visualized as follows:

```
Word Embedding Matrix:
[
  [0.123, -0.456, 0.789, ..., 0.987],  # Embedding for word 1
  [-0.234, 0.567, -0.890, ..., -0.876], # Embedding for word 2
  ...
  [0.345, -0.678, 0.901, ..., 0.765]   # Embedding for word 10,000
]
```

Each row in the matrix corresponds to a word in the vocabulary, and each column represents a dimension in the embedding space. The values in the matrix are learned during the training process and capture the semantic relationships between words.

### Token Structures

Token structures are another critical component in NLP models. Tokens are the smallest units of text that a model can process, and they can be as simple as individual characters or as complex as subwords or entire words. Tokenization is the process of converting raw text into these tokens, and it significantly impacts the performance and accuracy of a model.

For instance, consider the sentence "The quick brown fox jumps over the lazy dog." A simple tokenization approach might split this sentence into individual words:

```
Tokens: ["The", "quick", "brown", "fox", "jumps", "over", "the", "lazy", "dog"]
```

However, more sophisticated tokenization methods, such as Byte Pair Encoding (BPE), can split words into subwords to handle out-of-vocabulary words and improve model performance:

```
Tokens: ["The", "qu", "##ick", "br", "##own", "fox", "jump", "##s", "over", "the", "la", "##zy", "dog"]
```

In this example, "##" denotes a subword continuation. The token structure is crucial for models like BERT, which rely on subword tokenization to capture the nuances of language.

### Attention Matrices

Attention mechanisms have revolutionized the field of NLP by allowing models to focus on different parts of the input sequence when making predictions. The attention matrix is a key component of these mechanisms, capturing the relationships between different tokens in the input sequence.

Consider a sequence of tokens \( \mathbf{X} = [x_1, x_2, \ldots, x_n] \). The attention matrix \( \mathbf{A} \) is computed as follows:

1. **Query, Key, and Value Vectors**: For each token \( x_i \), compute query \( \mathbf{Q}_i \), key \( \mathbf{K}_i \), and value \( \mathbf{V}_i \) vectors using learned linear transformations.

2. **Attention Scores**: Compute the attention scores using the dot product between query and key vectors:

   \[
   \mathbf{A}_{ij} = \frac{\mathbf{Q}_i \cdot \mathbf{K}_j}{\sqrt{d_k}}
   \]

   where \( d_k \) is the dimensionality of the key vectors.

3. **Softmax Normalization**: Apply the softmax function to the attention scores to obtain the attention weights:

   \[
   \alpha_{ij} = \text{softmax}(\mathbf{A}_{ij})
   \]

4. **Context Vectors**: Compute the context vectors by taking a weighted sum of the value vectors using the attention weights:

   \[
   \mathbf{C}_i = \sum_{j=1}^{n} \alpha_{ij} \mathbf{V}_j
   \]

The attention matrix \( \mathbf{A} \) captures the relationships between different tokens, allowing the model to focus on relevant parts of the input sequence when making predictions.

### Parameter Layouts

The layout of model parameters is another critical aspect of model architecture. Parameters are the weights and biases that are learned during training and are used to make predictions. The layout of these parameters can significantly impact the efficiency and performance of model inference.

Consider a simple feedforward neural network with an input layer, a hidden layer, and an output layer. The parameter layout can be visualized as follows:

```
Input Layer: [x1, x2, ..., xn]
Hidden Layer: [h1, h2, ..., hm]
Output Layer: [y1, y2, ..., yo]

Weights:
W_input_hidden = [
  [w11, w12, ..., w1m],
  [w21, w22, ..., w2m],
  ...
  [wn1, wn2, ..., wnm]
]

W_hidden_output = [
  [w11', w12', ..., w1o],
  [w21', w22', ..., w2o],
  ...
  [wm1', wm2', ..., wmo]
]

Biases:
b_hidden = [b1, b2, ..., bm]
b_output = [b1', b2', ..., bo]
```

In this example, \( W_{\text{input\_hidden}} \) and \( W_{\text{hidden\_output}} \) are weight matrices, and \( b_{\text{hidden}} \) and \( b_{\text{output}} \) are bias vectors. The layout of these parameters is crucial for efficient computation and memory management.

## 2. Forward Pass & Algorithmic Execution Lifecycle

The forward pass is the process of computing the output of a model given an input. It involves a series of mathematical operations that transform the input through the layers of the model. We will trace the forward pass through a simple feedforward neural network to understand the algorithmic execution lifecycle.

### Step-by-Step Mathematical Trace

Consider a feedforward neural network with an input layer, a hidden layer, and an output layer. The forward pass can be traced as follows:

1. **Input Layer**: The input vector \( \mathbf{x} \) is passed to the model.

2. **Hidden Layer**: The input vector is transformed using the weight matrix \( W_{\text{input\_hidden}} \) and the bias vector \( b_{\text{hidden}} \):

   \[
   \mathbf{z}_{\text{hidden}} = W_{\text{input\_hidden}} \mathbf{x} + b_{\text{hidden}}
   \]

   The hidden layer activations are computed using a non-linear activation function, such as the ReLU function:

   \[
   \mathbf{h} = \text{ReLU}(\mathbf{z}_{\text{hidden}})
   \]

3. **Output Layer**: The hidden layer activations are transformed using the weight matrix \( W_{\text{hidden\_output}} \) and the bias vector \( b_{\text{output}} \):

   \[
   \mathbf{z}_{\text{output}} = W_{\text{hidden\_output}} \mathbf{h} + b_{\text{output}}
   \]

   The output layer activations are computed using a non-linear activation function, such as the softmax function for classification tasks:

   \[
   \mathbf{y} = \text{softmax}(\mathbf{z}_{\text{output}})
   \]

The forward pass involves a series of matrix multiplications, additions, and non-linear transformations. These operations are performed in a sequential manner, with the output of each layer serving as the input to the next layer.

### Algorithmic Execution Lifecycle

The algorithmic execution lifecycle of a forward pass can be broken down into the following steps:

1. **Initialization**: Initialize the model parameters, including weight matrices and bias vectors.

2. **Input Processing**: Preprocess the input data, such as normalizing or tokenizing text.

3. **Layer Operations**: Perform the operations for each layer, including matrix multiplications, additions, and non-linear transformations.

4. **Output Generation**: Generate the final output of the model, such as class probabilities for classification tasks.

5. **Postprocessing**: Postprocess the output data, such as converting class probabilities to class labels.

The algorithmic execution lifecycle is a critical aspect of model inference, and understanding it is essential for optimizing model performance and efficiency.

## 3. Memory Footprint & Computational Complexity

The memory footprint and computational complexity of a model are crucial factors that impact its performance and scalability. We will explore the memory footprint and computational complexity of key components, such as KV-cache scaling, parameter memory allocation, and hardware accelerator mapping.

### KV-Cache Scaling

KV-cache scaling is a critical aspect of models with attention mechanisms, such as transformers. The KV-cache stores the key and value vectors for each token in the input sequence, allowing the model to efficiently compute attention scores.

Consider a transformer model with a sequence length of \( n \) and a hidden dimension of \( d \). The KV-cache can be visualized as follows:

```
KV-Cache:
[
  [k11, k12, ..., k1d], [v11, v12, ..., v1d],  # KV-pair for token 1
  [k21, k22, ..., k2d], [v21, v22, ..., v2d],  # KV-pair for token 2
  ...
  [kn1, kn2, ..., knd], [vn1, vn2, ..., vnd]   # KV-pair for token n
]
```

In this example, each row in the KV-cache corresponds to a token in the input sequence, and each column represents a dimension in the hidden space. The memory footprint of the KV-cache is proportional to the sequence length and the hidden dimension.

### Parameter Memory Allocation

Parameter memory allocation is another critical aspect of model architecture. The memory footprint of model parameters is determined by the number of parameters and their dimensions. Efficient memory allocation is essential for optimizing model performance and scalability.

Consider a simple feedforward neural network with an input layer, a hidden layer, and an output layer. The memory footprint of the model parameters can be visualized as follows:

```
Parameter Memory Allocation:
[
  W_input_hidden: [n, m],  # Weight matrix for input to hidden layer
  b_hidden: [m],            # Bias vector for hidden layer
  W_hidden_output: [m, o], # Weight matrix for hidden to output layer
  b_output: [o]             # Bias vector for output layer
]
```

In this example, \( W_{\text{input\_hidden}} \) and \( W_{\text{hidden\_output}} \) are weight matrices, and \( b_{\text{hidden}} \) and \( b_{\text{output}} \) are bias vectors. The memory footprint of the model parameters is proportional to the number of parameters and their dimensions.

### Computational Complexity

The computational complexity of a model is determined by the number of operations required to perform the forward pass and backward pass. Efficient computational complexity is essential for optimizing model performance and scalability.

Consider a simple feedforward neural network with an input layer, a hidden layer, and an output layer. The computational complexity of the forward pass can be visualized as follows:

```
Computational Complexity:
[
  Matrix Multiplication: O(n * m),  # Input to hidden layer
  Addition: O(m),                 # Hidden layer bias
  Non-linear Transformation: O(m),  # Hidden layer activation
  Matrix Multiplication: O(m * o),  # Hidden to output layer
  Addition: O(o),                 # Output layer bias
  Non-linear Transformation: O(o)   # Output layer activation
]
```

In this example, the computational complexity of the forward pass is determined by the number of operations required to perform matrix multiplications, additions, and non-linear transformations. Efficient computational complexity is essential for optimizing model performance and scalability.

### Hardware Accelerator Mapping

Hardware accelerators, such as GPUs and TPUs, can significantly improve the performance and scalability of model inference. Efficient hardware accelerator mapping is essential for optimizing model performance and scalability.

Consider a simple feedforward neural network with an input layer, a hidden layer, and an output layer. The hardware accelerator mapping can be visualized as follows:

```
Hardware Accelerator Mapping:
[
  Input Layer: CPU,
  Hidden Layer: GPU,
  Output Layer: GPU
]
```

In this example, the input layer is processed on the CPU, while the hidden and output layers are processed on the GPU. Efficient hardware accelerator mapping is essential for optimizing model performance and scalability.

In conclusion, understanding the internal representations and data structures, the forward pass and algorithmic execution lifecycle, and the memory footprint and computational complexity is crucial for optimizing model performance and scalability. By delving into these concepts, we can gain a deeper understanding of the core architecture and algorithmic mechanics of machine learning models.
