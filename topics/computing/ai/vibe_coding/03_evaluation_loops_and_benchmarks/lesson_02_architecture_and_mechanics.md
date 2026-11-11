# Lesson 2: Core Architecture & Algorithmic Mechanics

## 1. Internal Representations & Data Structures

In the realm of machine learning, the internal representations and data structures are the foundational elements that underpin the architecture and performance of models. These structures are not merely abstract constructs but are deeply intertwined with the computational mechanics that drive inference and training. Let us delve into the core components, starting with vector embeddings, token structures, attention matrices, and parameter layouts.

### Vector Embeddings

Vector embeddings are a cornerstone of modern machine learning, particularly in natural language processing (NLP) and computer vision. They provide a dense, continuous representation of discrete data, such as words or images, in a high-dimensional space. Each element in the vector space is a real number that encodes semantic or syntactic information about the data point. For instance, in word embeddings, words with similar meanings are mapped to nearby points in the vector space, facilitating tasks like semantic similarity and analogy reasoning.

Consider a simple example of a word embedding space. Suppose we have a vocabulary of 10,000 words, and each word is represented by a 512-dimensional vector. The embedding matrix, denoted as \( E \), is a \( 10,000 \times 512 \) matrix where each row corresponds to a word's embedding. Mathematically, this can be represented as:

\[
E = \begin{bmatrix}
e_1 \\
e_2 \\
\vdots \\
e_{10000}
\end{bmatrix}
\]

where \( e_i \) is the 512-dimensional vector for the \( i \)-th word in the vocabulary. The embeddings are typically learned during the training process through backpropagation, where the model adjusts the vectors to minimize a loss function.

### Token Structures

Token structures are another critical component in the representation of input data, especially in sequence-based models like transformers. Tokens are the smallest units of data that the model processes, and they can be as simple as individual characters or as complex as subword units. The choice of tokenization strategy significantly impacts the model's performance and efficiency.

For example, in the case of Byte Pair Encoding (BPE), the input text is recursively split into pairs of bytes until a predefined vocabulary size is achieved. Each token in the vocabulary is assigned a unique integer index, which is used to look up its corresponding embedding in the embedding matrix. The tokenization process can be visualized as follows:

```
Input Text: "hello world"
Tokenized Sequence: [123, 456, 789, 1011, 1213]
```

In this example, the input text "hello world" is tokenized into a sequence of integers, where each integer corresponds to a token in the vocabulary. The tokenized sequence is then used to index into the embedding matrix to obtain the corresponding embeddings.

### Attention Matrices

Attention mechanisms are a key innovation in transformer architectures, enabling models to weigh the importance of different parts of the input sequence when making predictions. The attention matrix captures the relationships between tokens, allowing the model to focus on relevant information and ignore irrelevant details.

The attention mechanism can be broken down into several steps. First, the query, key, and value vectors are computed for each token in the sequence. These vectors are typically derived from the token embeddings through linear transformations. The attention scores are then computed as the dot product between the query and key vectors, followed by a softmax normalization to obtain the attention weights. Finally, the weighted sum of the value vectors is computed to produce the output of the attention mechanism.

Mathematically, the attention mechanism can be represented as:

\[
\text{Attention}(Q, K, V) = \text{softmax}\left(\frac{QK^T}{\sqrt{d_k}}\right)V
\]

where \( Q \), \( K \), and \( V \) are the query, key, and value matrices, respectively, and \( d_k \) is the dimensionality of the key vectors. The attention matrix, denoted as \( A \), is the output of the softmax function, and it captures the relationships between tokens in the sequence.

### Parameter Layouts

The parameter layout of a machine learning model refers to the organization and arrangement of its learnable parameters. The layout is crucial for efficient computation and memory management, as it determines how the parameters are stored and accessed during inference and training. In transformer architectures, the parameters are organized into layers, where each layer consists of a self-attention mechanism and a feedforward neural network.

The parameter layout can be visualized as a hierarchical structure, where each layer contains its own set of parameters. For example, in a transformer with 12 layers, the parameter layout can be represented as:

```
Layer 1: [Query Weights, Key Weights, Value Weights, Feedforward Weights]
Layer 2: [Query Weights, Key Weights, Value Weights, Feedforward Weights]
...
Layer 12: [Query Weights, Key Weights, Value Weights, Feedforward Weights]
```

In this example, each layer contains its own set of query, key, value, and feedforward weights, which are learned during the training process. The parameter layout is designed to facilitate efficient computation and memory access, ensuring that the model can process input sequences quickly and accurately.

## 2. Forward Pass & Algorithmic Execution Lifecycle

The forward pass is the process of computing the output of a machine learning model given an input sequence. It involves a series of algorithmic operations that transform the input data through the layers of the model, producing the final output. In this section, we will trace the forward pass through a transformer architecture, examining the step-by-step mathematical operations that underpin the inference process.

### Input Embedding

The forward pass begins with the input embedding, where the tokenized input sequence is mapped to its corresponding embeddings in the embedding matrix. The input embeddings are then passed through a positional encoding layer, which adds information about the position of each token in the sequence. The positional encoding is necessary because transformers do not have a built-in notion of sequence order, and the positional encoding helps the model to capture the sequential dependencies in the input data.

Mathematically, the input embedding can be represented as:

\[
X = E \cdot T + P
\]

where \( E \) is the embedding matrix, \( T \) is the tokenized input sequence, and \( P \) is the positional encoding matrix. The input embeddings \( X \) are then passed through the layers of the transformer.

### Self-Attention Mechanism

The self-attention mechanism is a key component of the transformer architecture, enabling the model to weigh the importance of different parts of the input sequence when making predictions. The self-attention mechanism consists of several steps, including the computation of query, key, and value vectors, the computation of attention scores, and the weighted sum of value vectors.

The query, key, and value vectors are computed through linear transformations of the input embeddings. Mathematically, the query, key, and value vectors can be represented as:

\[
Q = X \cdot W_Q
\]
\[
K = X \cdot W_K
\]
\[
V = X \cdot W_V
\]

where \( W_Q \), \( W_K \), and \( W_V \) are the query, key, and value weight matrices, respectively. The attention scores are then computed as the dot product between the query and key vectors, followed by a softmax normalization to obtain the attention weights. Mathematically, the attention scores can be represented as:

\[
A = \text{softmax}\left(\frac{QK^T}{\sqrt{d_k}}\right)
\]

where \( d_k \) is the dimensionality of the key vectors. The weighted sum of the value vectors is computed to produce the output of the self-attention mechanism. Mathematically, the output can be represented as:

\[
\text{Output} = AV
\]

### Feedforward Neural Network

The output of the self-attention mechanism is then passed through a feedforward neural network, which applies a series of linear transformations and non-linear activation functions to the input. The feedforward neural network is designed to capture complex relationships between the tokens in the sequence, enabling the model to make accurate predictions.

Mathematically, the feedforward neural network can be represented as:

\[
\text{Output} = \text{ReLU}(X \cdot W_1 + b_1) \cdot W_2 + b_2
\]

where \( W_1 \) and \( W_2 \) are the weight matrices, and \( b_1 \) and \( b_2 \) are the bias vectors. The feedforward neural network is applied to each token in the sequence independently, producing the output of the layer.

### Layer Normalization

The output of the feedforward neural network is then passed through a layer normalization layer, which normalizes the activations to have zero mean and unit variance. Layer normalization is necessary to stabilize the training process and improve the convergence of the model. Mathematically, layer normalization can be represented as:

\[
\text{Output} = \frac{\text{Input} - \mu}{\sigma} \cdot \gamma + \beta
\]

where \( \mu \) and \( \sigma \) are the mean and standard deviation of the input, and \( \gamma \) and \( \beta \) are the learnable scale and shift parameters, respectively.

### Residual Connections

The output of the layer normalization layer is then added to the input of the layer through a residual connection. Residual connections are a key innovation in transformer architectures, enabling the model to learn complex relationships between the tokens in the sequence without suffering from vanishing gradient problems. Mathematically, the residual connection can be represented as:

\[
\text{Output} = \text{Input} + \text{Layer Normalization}(\text{Feedforward}(\text{Self-Attention}(\text{Input})))
\]

The residual connection is applied to each layer independently, producing the output of the layer.

### Multi-Head Attention

The self-attention mechanism and feedforward neural network are repeated for each layer in the transformer. However, in practice, the self-attention mechanism is often implemented using multi-head attention, which allows the model to capture multiple relationships between the tokens in the sequence simultaneously. Multi-head attention consists of several parallel self-attention mechanisms, each with its own set of query, key, and value weights. The outputs of the parallel self-attention mechanisms are then concatenated and passed through a linear transformation to produce the final output.

Mathematically, multi-head attention can be represented as:

\[
\text{MultiHead}(Q, K, V) = \text{Concat}(\text{head}_1, \ldots, \text{head}_h) \cdot W_O
\]

where \( \text{head}_i = \text{Attention}(QW_i^Q, KW_i^K, VW_i^V) \), \( W_i^Q \), \( W_i^K \), and \( W_i^V \) are the query, key, and value weight matrices for the \( i \)-th head, \( W_O \) is the output weight matrix, and \( h \) is the number of heads. Multi-head attention allows the model to capture multiple relationships between the tokens in the sequence simultaneously, improving the performance of the model.

### Final Output

The output of the final layer in the transformer is then passed through a linear transformation and a softmax activation function to produce the final output of the model. The final output can be represented as:

\[
\text{Output} = \text{softmax}(X \cdot W + b)
\]

where \( W \) is the output weight matrix, and \( b \) is the bias vector. The final output of the model is a probability distribution over the possible output classes, which can be used to make predictions.

## 3. Memory Footprint & Computational Complexity

The memory footprint and computational complexity of a machine learning model are critical factors that determine its performance and efficiency. In this section, we will examine the memory footprint and computational complexity of transformer architectures, focusing on the key data structures and algorithmic operations that impact the performance of the model.

### Memory Footprint

The memory footprint of a transformer architecture is determined by the size of the embedding matrix, the number of layers, and the dimensionality of the hidden states. The embedding matrix is the largest data structure in the model, and its size is determined by the vocabulary size and the dimensionality of the embeddings. The number of layers and the dimensionality of the hidden states also impact the memory footprint, as they determine the size of the weight matrices and the intermediate activations.

The memory footprint of a transformer can be estimated as follows:

\[
\text{Memory Footprint} = \text{Vocabulary Size} \times \text{Embedding Dimension} + \text{Number of Layers} \times (\text{Hidden Dimension} \times \text{Hidden Dimension} + \text{Hidden Dimension} \times \text{Embedding Dimension})
\]

where the vocabulary size is the number of unique tokens in the input data, the embedding dimension is the dimensionality of the embeddings, the number of layers is the number of layers in the transformer, and the hidden dimension is the dimensionality of the hidden states.

### Computational Complexity

The computational complexity of a transformer architecture is determined by the number of operations required to compute the forward pass and the backward pass. The forward pass involves a series of matrix multiplications, element-wise operations, and non-linear activation functions, while the backward pass involves the computation of gradients through backpropagation.

The computational complexity of the forward pass can be estimated as follows:

\[
\text{Forward Pass Complexity} = \text{Vocabulary Size} \times \text{Embedding Dimension} + \text{Number of Layers} \times (\text{Hidden Dimension} \times \text{Hidden Dimension} + \text{Hidden Dimension} \times \text{Embedding Dimension})
\]

where the vocabulary size is the number of unique tokens in the input data, the embedding dimension is the dimensionality of the embeddings, the number of layers is the number of layers in the transformer, and the hidden dimension is the dimensionality of the hidden states.

The computational complexity of the backward pass is similar to the forward pass, but it involves additional operations to compute the gradients of the loss function with respect to the parameters. The backward pass can be estimated as follows:

\[
\text{Backward Pass Complexity} = \text{Vocabulary Size} \times \text{Embedding Dimension} + \text{Number of Layers} \times (\text{Hidden Dimension} \times \text{Hidden Dimension} + \text{Hidden Dimension} \times \text{Embedding Dimension})
\]

where the vocabulary size is the number of unique tokens in the input data, the embedding dimension is the dimensionality of the embeddings, the number of layers is the number of layers in the transformer, and the hidden dimension is the dimensionality of the hidden states.

### KV-Cache Scaling

KV-cache scaling is a technique used to improve the efficiency of transformer architectures by caching the key and value vectors during the forward pass. The key and value vectors are computed once for each input sequence and can be reused for subsequent sequences, reducing the computational complexity of the forward pass. KV-cache scaling is particularly useful in scenarios where the input sequences are similar, such as in language modeling and translation tasks.

The KV-cache scaling can be estimated as follows:

\[
\text{KV-Cache Scaling} = \text{Number of Sequences} \times \text{Sequence Length} \times \text{Hidden Dimension}
\]

where the number of sequences is the number of input sequences, the sequence length is the length of each input sequence, and the hidden dimension is the dimensionality of the hidden states.

### Parameter Memory Allocation

The parameter memory allocation of a transformer architecture is determined by the size of the weight matrices and the bias vectors. The weight matrices and bias vectors are learned during the training process and are used to compute the output of the model. The parameter memory allocation can be estimated as follows:

\[
\text{Parameter Memory Allocation} = \text{Number of Layers} \times (\text{Hidden Dimension} \times \text{Hidden Dimension} + \text{Hidden Dimension} \times \text{Embedding Dimension})
\]

where the number of layers is the number of layers in the transformer, the hidden dimension is the dimensionality of the hidden states, and the embedding dimension is the dimensionality of the embeddings.

### Hardware Accelerator Mapping

The hardware accelerator mapping of a transformer architecture is determined by the choice of hardware accelerators, such as GPUs and TPUs, and the optimization techniques used to map the model onto the hardware. Hardware accelerators provide specialized hardware resources, such as parallel processing units and memory hierarchies, that can significantly improve the performance of the model. The hardware accelerator mapping can be estimated as follows:

\[
\text{Hardware Accelerator Mapping} = \text{Number of Accelerators} \times \text{Accelerator Capacity}
\]

where the number of accelerators is the number of hardware accelerators used to run the model, and the accelerator capacity is the computational capacity of each accelerator.

In conclusion, the core architecture and algorithmic mechanics of transformer architectures are deeply intertwined with the internal representations and data structures, the forward pass and algorithmic execution lifecycle, and the memory footprint and computational complexity. By understanding these components, machine learning engineers and AI practitioners can design and optimize transformer architectures for a wide range of applications, from natural language processing to computer vision.
