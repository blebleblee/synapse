# Lesson 1: Tokenization Methods

## 1. First-Principles Intuition & Invariants

Tokenization is a foundational process in the construction and deployment of large language models (LLMs). It involves the segmentation of text into discrete units, or tokens, which serve as the basic building blocks for model training and inference. The choice of tokenization method significantly influences the model's ability to understand and generate human-like text, as well as its efficiency in terms of computational resources and memory usage.

At the heart of tokenization lies the need to balance granularity and coverage. Granularity refers to the level of detail at which text is segmented. For instance, character-level tokenization captures the most granular details but can lead to a vast vocabulary size, increasing computational complexity. On the other hand, word-level tokenization reduces vocabulary size but may fail to capture the nuances of subword units, such as morphemes or affixes, which are crucial for understanding language structure and semantics.

The problem space of tokenization is further complicated by the need to handle out-of-vocabulary (OOV) words, which are words that do not appear in the training data. Effective tokenization methods must be able to handle OOV words gracefully, either by decomposing them into known subword units or by employing fallback strategies that minimize the impact of OOV occurrences.

Mathematically, tokenization can be framed as a problem of finding an optimal segmentation of text into tokens that minimizes a loss function. This loss function typically includes terms that penalize vocabulary size, encourage coverage of training data, and ensure that tokens are semantically meaningful. The challenge lies in designing algorithms that can efficiently explore the vast space of possible segmentations and converge to near-optimal solutions.

System invariants in tokenization include the requirement for determinism, meaning that the same input text should always produce the same token sequence. This invariant is crucial for reproducibility and consistency across different stages of model training and deployment. Additionally, tokenization methods must be robust to variations in input text, such as different punctuation styles or capitalization, to ensure that the model can generalize well to unseen data.

## 2. Core Architecture & Mechanics

Several tokenization methods have been developed to address the challenges outlined above. Among the most prominent are Byte Pair Encoding (BPE), WordPiece, and SentencePiece. Each of these methods employs distinct algorithms and data structures to segment text into tokens, and understanding their mechanics is essential for selecting the right tokenization strategy for a given application.

### Byte Pair Encoding (BPE)

Byte Pair Encoding is a subword tokenization method that iteratively merges the most frequent pairs of bytes (or characters) in the training data until a predefined vocabulary size is reached. The algorithm begins by treating each character in the text as a separate token and then iteratively identifies the most frequent pair of adjacent tokens. This pair is then merged into a single token, and the process is repeated until the desired vocabulary size is achieved.

The core data structure in BPE is the frequency table, which keeps track of the frequency of each token pair in the training data. The algorithm iteratively updates this table as pairs are merged, ensuring that the most frequent pairs are always considered for merging. The resulting vocabulary consists of a combination of characters and subword units, allowing BPE to handle OOV words by decomposing them into known subword units.

The mechanics of BPE can be illustrated with a simple example. Suppose we have the following training data:

```
low
lower
newer
news
```

The initial frequency table would look like this:

```
l o w 2
l o w e r 1
n e w e r 1
n e w s 1
```

The most frequent pair is `ow`, which appears twice. This pair is merged into a single token `ow`, and the frequency table is updated:

```
l o 1
ow 2
l o w e r 1
n e w e r 1
n e w s 1
```

The process continues until the desired vocabulary size is reached. The final vocabulary might look like this:

```
l
o
w
ow
er
n
e
new
s
```

### WordPiece

WordPiece is another subword tokenization method that builds on the principles of BPE but introduces a few key differences. Unlike BPE, which merges the most frequent pairs of tokens, WordPiece merges the most frequent subword units that minimize the loss function. The loss function in WordPiece is defined as the negative log probability of the training data given the current vocabulary, and the algorithm iteratively updates the vocabulary to minimize this loss.

The core data structure in WordPiece is the vocabulary, which is initialized with a set of characters and then expanded by iteratively adding the most frequent subword units. The algorithm uses a greedy approach to identify the subword units that minimize the loss function, ensuring that the vocabulary remains as small as possible while still providing good coverage of the training data.

The mechanics of WordPiece can be illustrated with the same training data as the BPE example:

```
low
lower
newer
news
```

The initial vocabulary consists of the characters in the training data:

```
l
o
w
e
r
n
s
```

The algorithm then iteratively identifies the most frequent subword units and adds them to the vocabulary. For example, the subword unit `ow` appears twice and is added to the vocabulary:

```
l
o
w
ow
e
r
n
s
```

The process continues until the desired vocabulary size is reached. The final vocabulary might look like this:

```
l
o
w
ow
er
n
e
new
s
```

### SentencePiece

SentencePiece is a more recent tokenization method that combines the strengths of BPE and WordPiece while introducing additional flexibility. SentencePiece uses a single algorithm to train a vocabulary that can be used for both character-level and subword-level tokenization. The algorithm is based on the Expectation-Maximization (EM) framework and iteratively updates the vocabulary to minimize the loss function.

The core data structure in SentencePiece is the vocabulary, which is initialized with a set of characters and then expanded by iteratively adding the most frequent subword units. The algorithm uses a probabilistic approach to identify the subword units that minimize the loss function, ensuring that the vocabulary remains as small as possible while still providing good coverage of the training data.

The mechanics of SentencePiece can be illustrated with the same training data as the BPE and WordPiece examples:

```
low
lower
newer
news
```

The initial vocabulary consists of the characters in the training data:

```
l
o
w
e
r
n
s
```

The algorithm then iteratively identifies the most frequent subword units and adds them to the vocabulary. For example, the subword unit `ow` appears twice and is added to the vocabulary:

```
l
o
w
ow
e
r
n
s
```

The process continues until the desired vocabulary size is reached. The final vocabulary might look like this:

```
l
o
w
ow
er
n
e
new
s
```

## 3. High-Performance Optimization & Failure Modes

The performance of tokenization methods is influenced by several factors, including vocabulary size, computational complexity, and memory usage. Optimizing these factors is crucial for ensuring that tokenization is efficient and scalable, especially for large-scale LLMs.

### Vocabulary Size

Vocabulary size is a critical factor in tokenization, as it directly impacts the computational complexity and memory usage of the model. A larger vocabulary requires more memory to store the embeddings and increases the computational complexity of the model. On the other hand, a smaller vocabulary may lead to OOV words and reduce the model's ability to understand and generate human-like text.

To optimize vocabulary size, tokenization methods must balance granularity and coverage. This can be achieved by using subword tokenization methods, such as BPE, WordPiece, and SentencePiece, which allow for a more flexible segmentation of text into tokens. These methods can handle OOV words by decomposing them into known subword units, reducing the impact of OOV occurrences.

### Computational Complexity

Computational complexity is another critical factor in tokenization, as it directly impacts the training and inference times of the model. Tokenization methods must be efficient and scalable to handle large-scale LLMs, which can have millions of parameters and require significant computational resources.

To optimize computational complexity, tokenization methods must be designed to minimize the number of operations required to segment text into tokens. This can be achieved by using efficient data structures and algorithms, such as the frequency table in BPE and the vocabulary in WordPiece and SentencePiece. These data structures and algorithms allow for efficient identification and merging of token pairs, reducing the computational complexity of the tokenization process.

### Memory Usage

Memory usage is a critical factor in tokenization, as it directly impacts the memory footprint of the model. A larger vocabulary requires more memory to store the embeddings, increasing the memory footprint of the model. On the other hand, a smaller vocabulary may lead to OOV words and reduce the model's ability to understand and generate human-like text.

To optimize memory usage, tokenization methods must balance vocabulary size and coverage. This can be achieved by using subword tokenization methods, such as BPE, WordPiece, and SentencePiece, which allow for a more flexible segmentation of text into tokens. These methods can handle OOV words by decomposing them into known subword units, reducing the impact of OOV occurrences.

### Failure Modes

Tokenization methods can fail in several ways, including OOV words, segmentation errors, and computational inefficiencies. OOV words occur when the tokenization method fails to recognize a word in the input text, leading to a loss of information and reduced model performance. Segmentation errors occur when the tokenization method fails to segment the input text correctly, leading to incorrect token sequences and reduced model performance. Computational inefficiencies occur when the tokenization method is not optimized for performance, leading to increased training and inference times.

To mitigate these failure modes, tokenization methods must be designed to handle OOV words gracefully, either by decomposing them into known subword units or by employing fallback strategies that minimize the impact of OOV occurrences. Additionally, tokenization methods must be optimized for performance, using efficient data structures and algorithms to minimize the computational complexity and memory usage of the tokenization process.
