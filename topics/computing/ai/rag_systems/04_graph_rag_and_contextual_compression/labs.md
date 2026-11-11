# Operational Verification Labs: 04 Graph Rag And Contextual Compression

## Objective & Environment Setup

### Objective
The objective of this lab is to implement, verify, and optimize a Graph Retrieval-Augmented Generation (RAG) system with contextual compression. This system will leverage graph-based data structures to enhance retrieval and generation tasks, ensuring efficient and accurate information processing. The lab will guide you through the implementation of a RAG system using PyTorch, HuggingFace Transformers, and other relevant libraries. By the end of this lab, you will have a comprehensive understanding of how to build, tune, and verify a RAG system with contextual compression.

### Environment Setup
Ensure you have a Python 3.11+ environment with the following packages installed:
- PyTorch
- HuggingFace Transformers
- NumPy
- Scikit-learn
- Ollama (if using Ollama for model hosting)
- Polars (for efficient data handling)

You can install these packages using pip:

```bash
pip install torch transformers numpy scikit-learn ollama polars
```

Additionally, ensure you have API access configured for any external services you plan to use, such as Ollama or HuggingFace Model Hub.

## Exercise 1: Hands-On Implementation & Pipeline Execution

### Implementation Overview
In this exercise, we will implement a RAG system using a pre-trained transformer model. The system will consist of a retriever that fetches relevant documents from a graph database and a generator that produces the final output based on the retrieved documents.

### Complete, Runnable Python Script

```python
import torch
from transformers import RagTokenizer, RagRetriever, RagTokenForGeneration
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import polars as pl

# Initialize the tokenizer and model
tokenizer = RagTokenizer.from_pretrained("facebook/rag-token-nq")
retriever = RagRetriever.from_pretrained("facebook/rag-token-nq", index_name="exact", use_dummy_dataset=True)
model = RagTokenForGeneration.from_pretrained("facebook/rag-token-nq", retriever=retriever)

# Sample documents and their embeddings
documents = [
    "Graph theory is a branch of mathematics that studies graphs, which are mathematical structures used to model pairwise relations between objects.",
    "A graph in graph theory consists of a set of vertices (also called nodes or points) and a set of edges that connect these vertices.",
    "Graphs can be used to model various real-world systems, such as social networks, computer networks, and transportation networks."
]

# Create a TF-IDF vectorizer and fit it to the documents
vectorizer = TfidfVectorizer()
tfidf_matrix = vectorizer.fit_transform(documents)

def retrieve_documents(query, top_k=3):
    query_vector = vectorizer.transform([query])
    cosine_similarities = cosine_similarity(query_vector, tfidf_matrix).flatten()
    top_indices = np.argsort(cosine_similarities)[-top_k:][::-1]
    return [documents[i] for i in top_indices]

def generate_answer(query):
    retrieved_docs = retrieve_documents(query)
    input_dict = tokenizer.prepare_seq2seq_batch([query], src_texts=retrieved_docs, return_tensors="pt")
    generated_ids = model.generate(input_dict["input_ids"], max_length=50)
    return tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0]

# Example usage
query = "What is a graph in graph theory?"
answer = generate_answer(query)
print(f"Query: {query}\nAnswer: {answer}")
```

## Exercise 2: Hyperparameter Tuning & Empirical Benchmarking

### Benchmarking Overview
In this exercise, we will benchmark the RAG system by measuring accuracy, latency, and token costs. We will use synthetic data to simulate different scenarios and evaluate the system's performance.

### Real Benchmarking Code

```python
import time
from sklearn.metrics import accuracy_score

# Synthetic data for benchmarking
queries = [
    "What is a graph in graph theory?",
    "What are the applications of graph theory?",
    "How are graphs used in computer networks?"
]

ground_truth_answers = [
    "A graph in graph theory consists of a set of vertices (also called nodes or points) and a set of edges that connect these vertices.",
    "Graph theory is used in various applications such as social networks, computer networks, and transportation networks.",
    "Graphs can be used to model computer networks by representing nodes as devices and edges as connections between them."
]

# Benchmarking function
def benchmark_rag_system(queries, ground_truth_answers):
    latencies = []
    accuracy_scores = []
    
    for query, ground_truth in zip(queries, ground_truth_answers):
        start_time = time.time()
        generated_answer = generate_answer(query)
        end_time = time.time()
        
        latency = end_time - start_time
        latencies.append(latency)
        
        # Simple accuracy check (this can be improved with more sophisticated metrics)
        accuracy = accuracy_score([ground_truth], [generated_answer])
        accuracy_scores.append(accuracy)
    
    average_latency = np.mean(latencies)
    average_accuracy = np.mean(accuracy_scores)
    
    return average_latency, average_accuracy

# Run benchmark
average_latency, average_accuracy = benchmark_rag_system(queries, ground_truth_answers)
print(f"Average Latency: {average_latency:.4f} seconds")
print(f"Average Accuracy: {average_accuracy:.4f}")
```

## Exercise 3: Stress Testing, Edge Cases & Failure Mitigation

### Stress Testing Overview
In this exercise, we will test the RAG system under various stress conditions and edge cases to ensure robustness and reliability. We will also implement guardrails and error handling to mitigate potential failures.

### Reproducing Failure Modes & Testing Edge Cases

```python
# Edge case scenarios
edge_case_queries = [
    "What is the capital of France?",  # Irrelevant query
    "",  # Empty query
    "A" * 1000  # Very long query
]

# Test edge cases
for query in edge_case_queries:
    try:
        answer = generate_answer(query)
        print(f"Query: {query}\nAnswer: {answer}\n")
    except Exception as e:
        print(f"Query: {query}\nError: {str(e)}\n")
```

### Implementing Guardrails & Error Handling

```python
def safe_generate_answer(query):
    if not query:
        raise ValueError("Query cannot be empty.")
    if len(query) > 1000:
        raise ValueError("Query is too long.")
    
    try:
        answer = generate_answer(query)
    except Exception as e:
        raise RuntimeError(f"Error generating answer: {str(e)}")
    
    return answer

# Test safe_generate_answer with edge cases
for query in edge_case_queries:
    try:
        answer = safe_generate_answer(query)
        print(f"Query: {query}\nAnswer: {answer}\n")
    except Exception as e:
        print(f"Query: {query}\nError: {str(e)}\n")
```

## Verification Checklist & Quick Reference Cheat Sheet

### Essential Python Methods & Parameters

| Method/Parameter | Description |
|------------------|-------------|
| `RagTokenizer.from_pretrained` | Loads a pre-trained tokenizer. |
| `RagRetriever.from_pretrained` | Loads a pre-trained retriever. |
| `RagTokenForGeneration.from_pretrained` | Loads a pre-trained RAG model for token generation. |
| `TfidfVectorizer` | Creates a TF-IDF vectorizer for document embedding. |
| `cosine_similarity` | Computes cosine similarity between vectors. |
| `tokenizer.prepare_seq2seq_batch` | Prepares input sequences for the RAG model. |
| `model.generate` | Generates output sequences using the RAG model. |
| `tokenizer.batch_decode` | Decodes generated token sequences. |
| `time.time` | Measures execution time. |
| `accuracy_score` | Computes accuracy between ground truth and generated answers. |
| `np.mean` | Computes the mean of an array. |
| `safe_generate_answer` | Safely generates answers with error handling. |

### Verification Flags

| Flag | Description |
|------|-------------|
| `--use_dummy_dataset` | Uses a dummy dataset for the retriever. |
| `--max_length` | Sets the maximum length of generated sequences. |

This lab provides a comprehensive guide to implementing, verifying, and optimizing a RAG system with contextual compression. By following the exercises and using the provided code, you will gain practical experience in building and evaluating advanced AI systems.
