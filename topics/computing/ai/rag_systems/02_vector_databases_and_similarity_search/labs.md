# Operational Verification Labs: 02 Vector Databases And Similarity Search

## Objective & Environment Setup

### Objective
The objective of this lab is to gain hands-on experience with vector databases and similarity search techniques. We will implement a similarity search pipeline using a vector database, perform hyperparameter tuning and empirical benchmarking, and conduct stress testing to ensure robustness. This lab will cover the entire lifecycle of deploying a similarity search system, from implementation to verification.

### Environment Setup
Ensure you have a Python 3.11+ environment set up. Install the required packages using pip:

```bash
pip install torch transformers numpy scikit-learn faiss-cpu
```

Additionally, you may need to configure API keys or tokens for any external services you use, such as Hugging Face for model access.

## Exercise 1: Hands-On Implementation & Pipeline Execution

In this exercise, we will implement a similarity search pipeline using a vector database. We will use the Faiss library for efficient similarity search and the Hugging Face Transformers library to generate embeddings from text data.

### Step-by-Step Implementation

1. **Import Required Libraries**

    ```python
    import torch
    from transformers import AutoTokenizer, AutoModel
    import numpy as np
    import faiss
    ```

2. **Load Pre-trained Model and Tokenizer**

    ```python
    model_name = "sentence-transformers/all-MiniLM-L6-v2"
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModel.from_pretrained(model_name)
    ```

3. **Generate Embeddings**

    ```python
    def generate_embeddings(texts):
        inputs = tokenizer(texts, padding=True, truncation=True, return_tensors="pt")
        with torch.no_grad():
            outputs = model(**inputs)
        embeddings = outputs.last_hidden_state.mean(dim=1).numpy()
        return embeddings
    ```

4. **Build the Vector Database**

    ```python
    def build_vector_database(texts):
        embeddings = generate_embeddings(texts)
        dimension = embeddings.shape[1]
        index = faiss.IndexFlatL2(dimension)
        index.add(embeddings)
        return index, embeddings
    ```

5. **Search for Similar Documents**

    ```python
    def search_similar_documents(index, query, top_k=5):
        query_embedding = generate_embeddings([query])
        distances, indices = index.search(query_embedding, top_k)
        return distances, indices
    ```

6. **Example Usage**

    ```python
    documents = [
        "The quick brown fox jumps over the lazy dog.",
        "A fast brown fox leaps over a sleepy dog.",
        "The lazy dog dreams of chasing the quick fox.",
        "A dog and a fox are playing in the park.",
        "The fox is quick and the dog is lazy."
    ]

    index, embeddings = build_vector_database(documents)

    query = "A quick fox jumping over a dog."
    distances, indices = search_similar_documents(index, query)

    for i, idx in enumerate(indices[0]):
        print(f"Similarity {i+1}: {documents[idx]} (Distance: {distances[0][i]})")
    ```

## Exercise 2: Hyperparameter Tuning & Empirical Benchmarking

In this exercise, we will perform hyperparameter tuning and empirical benchmarking to measure the accuracy, latency, and token costs of our similarity search pipeline.

### Step-by-Step Benchmarking

1. **Generate Benchmark Data**

    ```python
    import time
    import random

    def generate_benchmark_data(num_samples=1000):
        sample_texts = [
            "The quick brown fox jumps over the lazy dog.",
            "A fast brown fox leaps over a sleepy dog.",
            "The lazy dog dreams of chasing the quick fox.",
            "A dog and a fox are playing in the park.",
            "The fox is quick and the dog is lazy."
        ]
        benchmark_texts = [random.choice(sample_texts) for _ in range(num_samples)]
        return benchmark_texts
    ```

2. **Benchmark Search Latency**

    ```python
    def benchmark_search_latency(index, benchmark_texts, num_queries=100):
        query_texts = random.sample(benchmark_texts, num_queries)
        latencies = []

        for query in query_texts:
            start_time = time.time()
            search_similar_documents(index, query)
            end_time = time.time()
            latencies.append(end_time - start_time)

        return latencies
    ```

3. **Calculate Metrics**

    ```python
    def calculate_metrics(latencies):
        avg_latency = np.mean(latencies)
        max_latency = np.max(latencies)
        min_latency = np.min(latencies)
        return avg_latency, max_latency, min_latency
    ```

4. **Example Usage**

    ```python
    benchmark_texts = generate_benchmark_data()
    latencies = benchmark_search_latency(index, benchmark_texts)
    avg_latency, max_latency, min_latency = calculate_metrics(latencies)

    print(f"Average Latency: {avg_latency:.4f} seconds")
    print(f"Maximum Latency: {max_latency:.4f} seconds")
    print(f"Minimum Latency: {min_latency:.4f} seconds")
    ```

## Exercise 3: Stress Testing, Edge Cases & Failure Mitigation

In this exercise, we will conduct stress testing to ensure our similarity search pipeline can handle high loads and edge cases. We will also implement guardrails and error handling to mitigate failures.

### Step-by-Step Stress Testing

1. **Simulate High Load**

    ```python
    def simulate_high_load(index, benchmark_texts, num_queries=1000):
        query_texts = random.sample(benchmark_texts, num_queries)
        latencies = []

        for query in query_texts:
            start_time = time.time()
            search_similar_documents(index, query)
            end_time = time.time()
            latencies.append(end_time - start_time)

        return latencies
    ```

2. **Handle Edge Cases**

    ```python
    def handle_edge_cases(index, edge_cases):
        for query in edge_cases:
            try:
                distances, indices = search_similar_documents(index, query)
                print(f"Query: {query}")
                for i, idx in enumerate(indices[0]):
                    print(f"Similarity {i+1}: {documents[idx]} (Distance: {distances[0][i]})")
            except Exception as e:
                print(f"Error processing query '{query}': {e}")
    ```

3. **Example Usage**

    ```python
    edge_cases = [
        "",
        " ",
        "This is a very long query that should not match any document in the database and is designed to test the system's ability to handle edge cases gracefully.",
        "A quick brown fox jumps over the lazy dog."
    ]

    high_load_latencies = simulate_high_load(index, benchmark_texts)
    handle_edge_cases(index, edge_cases)
    ```

## Verification Checklist & Quick Reference Cheat Sheet

### Essential Python Methods and Parameters

| Method/Parameter | Description |
|------------------|-------------|
| `generate_embeddings(texts)` | Generates embeddings for a list of text documents. |
| `build_vector_database(texts)` | Builds a vector database from a list of text documents. |
| `search_similar_documents(index, query, top_k=5)` | Searches for similar documents in the vector database. |
| `generate_benchmark_data(num_samples=1000)` | Generates benchmark data for performance testing. |
| `benchmark_search_latency(index, benchmark_texts, num_queries=100)` | Benchmarks the search latency of the vector database. |
| `calculate_metrics(latencies)` | Calculates performance metrics from latency data. |
| `simulate_high_load(index, benchmark_texts, num_queries=1000)` | Simulates high load on the vector database. |
| `handle_edge_cases(index, edge_cases)` | Handles edge cases and errors in the vector database. |

### Verification Flags

| Flag | Description |
|------|-------------|
| `top_k` | Number of top similar documents to return. |
| `num_samples` | Number of samples to generate for benchmark data. |
| `num_queries` | Number of queries to use for benchmarking and stress testing. |

By completing this lab, you will have a solid understanding of how to implement, benchmark, and verify a similarity search pipeline using vector databases. This hands-on experience will equip you with the skills needed to deploy robust similarity search systems in real-world applications.
