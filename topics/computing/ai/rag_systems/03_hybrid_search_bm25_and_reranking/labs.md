# Operational Verification Labs: 03 Hybrid Search BM25 and Reranking

## Objective & Environment Setup

The objective of this lab is to implement and verify a hybrid search system that combines BM25 (Best Matching 25) with a reranking model. This hybrid approach leverages the strengths of traditional information retrieval methods (BM25) and machine learning-based reranking to improve search quality. The lab will guide you through the implementation, hyperparameter tuning, and stress testing of this system.

### Environment Setup

Ensure you have a Python 3.11+ environment with the following packages installed:

- `torch`
- `transformers` (Hugging Face)
- `numpy`
- `scikit-learn`
- `faiss-cpu` or `faiss-gpu`
- `pandas`
- `requests`

You can install these packages using pip:

```bash
pip install torch transformers numpy scikit-learn faiss-cpu pandas requests
```

Additionally, you will need access to a pre-trained reranking model from Hugging Face. For this lab, we will use the `cross-encoder/ms-marco-MiniLM-L-6-v2` model.

## Exercise 1: Hands-On Implementation & Pipeline Execution

In this exercise, we will implement the core components of the hybrid search system, including the BM25 retrieval and the reranking model.

### Step 1: Implement BM25 Retrieval

First, we need to implement the BM25 retrieval component. We will use the `scikit-learn` library for this purpose.

```python
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel
import numpy as np

class BM25Retriever:
    def __init__(self, documents, k1=1.2, b=0.75):
        self.documents = documents
        self.vectorizer = TfidfVectorizer(use_idf=True, norm=None, smooth_idf=False)
        self.doc_term_matrix = self.vectorizer.fit_transform(documents)
        self.avgdl = np.mean(self.doc_term_matrix.sum(axis=1))
        self.k1 = k1
        self.b = b

    def _bm25_score(self, query_vec, doc_vec, doc_len):
        score = 0
        for i in range(len(query_vec)):
            if query_vec[i] == 0:
                continue
            idf = np.log((len(self.documents) - np.count_nonzero(doc_vec[i]) + 0.5) / (np.count_nonzero(doc_vec[i]) + 0.5))
            score += idf * (query_vec[i] * (self.k1 + 1) / (query_vec[i] + self.k1 * (1 - self.b + self.b * doc_len / self.avgdl)))
        return score

    def search(self, query, top_k=10):
        query_vec = self.vectorizer.transform([query])
        scores = []
        for i in range(len(self.documents)):
            doc_vec = self.doc_term_matrix[i]
            doc_len = doc_vec.sum()
            score = self._bm25_score(query_vec.toarray()[0], doc_vec.toarray()[0], doc_len)
            scores.append((i, score))
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_k]
```

### Step 2: Implement Reranking Model

Next, we will implement the reranking model using a pre-trained cross-encoder from Hugging Face.

```python
from transformers import AutoModelForSequenceClassification, AutoTokenizer
import torch

class Reranker:
    def __init__(self, model_name='cross-encoder/ms-marco-MiniLM-L-6-v2'):
        self.model = AutoModelForSequenceClassification.from_pretrained(model_name)
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.model.to(self.device)

    def rerank(self, query, documents):
        inputs = self.tokenizer([[query, doc] for doc in documents], return_tensors='pt', padding=True, truncation=True)
        inputs = {key: value.to(self.device) for key, value in inputs.items()}
        with torch.no_grad():
            outputs = self.model(**inputs)
        scores = outputs.logits.squeeze().cpu().numpy()
        return scores
```

### Step 3: Combine BM25 and Reranking

Now, we will combine the BM25 retrieval and the reranking model to form the hybrid search system.

```python
class HybridSearch:
    def __init__(self, documents):
        self.bm25_retriever = BM25Retriever(documents)
        self.reranker = Reranker()

    def search(self, query, top_k=10):
        # Step 1: BM25 Retrieval
        bm25_results = self.bm25_retriever.search(query, top_k)
        bm25_docs = [self.bm25_retriever.documents[i] for i, _ in bm25_results]
        
        # Step 2: Reranking
        rerank_scores = self.reranker.rerank(query, bm25_docs)
        rerank_results = list(zip(bm25_docs, rerank_scores))
        rerank_results.sort(key=lambda x: x[1], reverse=True)
        
        return rerank_results
```

### Step 4: Execute the Hybrid Search Pipeline

Finally, we will execute the hybrid search pipeline with a sample query.

```python
if __name__ == "__main__":
    documents = [
        "The quick brown fox jumps over the lazy dog.",
        "Never jump over the lazy dog quickly.",
        "A quick brown dog outpaces a quick fox.",
        "The lazy dog is not amused."
    ]
    
    hybrid_search = HybridSearch(documents)
    query = "quick fox"
    results = hybrid_search.search(query, top_k=3)
    
    for doc, score in results:
        print(f"Document: {doc}\nScore: {score}\n")
```

## Exercise 2: Hyperparameter Tuning & Empirical Benchmarking

In this exercise, we will perform hyperparameter tuning and empirical benchmarking to evaluate the performance of our hybrid search system.

### Step 1: Define Benchmarking Metrics

We will define metrics such as accuracy, latency, and token costs.

```python
import time
import pandas as pd

def benchmark_search(hybrid_search, queries, documents, top_k=10):
    results = []
    for query in queries:
        start_time = time.time()
        rerank_results = hybrid_search.search(query, top_k)
        end_time = time.time()
        latency = end_time - start_time
        results.append({
            'query': query,
            'results': rerank_results,
            'latency': latency
        })
    return results
```

### Step 2: Perform Hyperparameter Tuning

We will perform hyperparameter tuning for the BM25 parameters `k1` and `b`.

```python
def hyperparameter_tuning(documents, queries, top_k=10):
    best_k1, best_b, best_latency = None, None, float('inf')
    for k1 in [1.0, 1.2, 1.5]:
        for b in [0.5, 0.75, 1.0]:
            bm25_retriever = BM25Retriever(documents, k1=k1, b=b)
            hybrid_search = HybridSearch(documents)
            hybrid_search.bm25_retriever = bm25_retriever
            results = benchmark_search(hybrid_search, queries, documents, top_k)
            avg_latency = sum(result['latency'] for result in results) / len(results)
            if avg_latency < best_latency:
                best_k1, best_b, best_latency = k1, b, avg_latency
    return best_k1, best_b, best_latency
```

### Step 3: Execute Benchmarking

We will execute the benchmarking pipeline with a set of sample queries.

```python
if __name__ == "__main__":
    documents = [
        "The quick brown fox jumps over the lazy dog.",
        "Never jump over the lazy dog quickly.",
        "A quick brown dog outpaces a quick fox.",
        "The lazy dog is not amused."
    ]
    queries = [
        "quick fox",
        "lazy dog",
        "brown dog"
    ]
    
    best_k1, best_b, best_latency = hyperparameter_tuning(documents, queries)
    print(f"Best k1: {best_k1}, Best b: {best_b}, Best Latency: {best_latency}")
    
    hybrid_search = HybridSearch(documents)
    hybrid_search.bm25_retriever = BM25Retriever(documents, k1=best_k1, b=best_b)
    results = benchmark_search(hybrid_search, queries, documents)
    
    for result in results:
        print(f"Query: {result['query']}")
        print(f"Latency: {result['latency']}")
        for doc, score in result['results']:
            print(f"Document: {doc}\nScore: {score}\n")
```

## Exercise 3: Stress Testing, Edge Cases & Failure Mitigation

In this exercise, we will perform stress testing, handle edge cases, and implement guardrails or error handling.

### Step 1: Stress Testing

We will perform stress testing by running the hybrid search system with a large number of queries.

```python
def stress_test(hybrid_search, queries, documents, top_k=10):
    for query in queries:
        hybrid_search.search(query, top_k)
```

### Step 2: Handle Edge Cases

We will handle edge cases such as empty queries and documents.

```python
def handle_edge_cases(hybrid_search):
    # Empty query
    try:
        hybrid_search.search("", top_k=3)
    except Exception as e:
        print(f"Error with empty query: {e}")
    
    # Empty documents
    try:
        hybrid_search = HybridSearch([])
        hybrid_search.search("quick fox", top_k=3)
    except Exception as e:
        print(f"Error with empty documents: {e}")
```

### Step 3: Implement Guardrails

We will implement guardrails to ensure the system handles invalid inputs gracefully.

```python
class GuardedHybridSearch(HybridSearch):
    def search(self, query, top_k=10):
        if not query:
            raise ValueError("Query cannot be empty")
        if not self.documents:
            raise ValueError("Documents cannot be empty")
        return super().search(query, top_k)
```

### Step 4: Execute Stress Testing and Edge Case Handling

We will execute the stress testing and edge case handling pipeline.

```python
if __name__ == "__main__":
    documents = [
        "The quick brown fox jumps over the lazy dog.",
        "Never jump over the lazy dog quickly.",
        "A quick brown dog outpaces a quick fox.",
        "The lazy dog is not amused."
    ]
    queries = [
        "quick fox",
        "lazy dog",
        "brown dog"
    ]
    large_queries = ["quick fox"] * 1000
    
    hybrid_search = GuardedHybridSearch(documents)
    stress_test(hybrid_search, large_queries, documents)
    handle_edge_cases(hybrid_search)
```

## Verification Checklist & Quick Reference Cheat Sheet

### Essential Python Methods and Parameters

- `BM25Retriever.__init__`: Initializes the BM25 retriever with documents and parameters `k1` and `b`.
- `BM25Retriever.search`: Searches for documents using BM25 and returns the top `k` results.
- `Reranker.__init__`: Initializes the reranker with a pre-trained model.
- `Reranker.rerank`: Reranks documents using the cross-encoder model.
- `HybridSearch.__init__`: Initializes the hybrid search system with documents.
- `HybridSearch.search`: Combines BM25 retrieval and reranking to return the top `k` results.
- `benchmark_search`: Benchmarks the hybrid search system with a set of queries.
- `hyperparameter_tuning`: Performs hyperparameter tuning for BM25 parameters `k1` and `b`.
- `stress_test`: Performs stress testing with a large number of queries.
- `handle_edge_cases`: Handles edge cases such as empty queries and documents.
- `GuardedHybridSearch.search`: Implements guardrails to handle invalid inputs.

### Verification Flags

- `k1`: BM25 parameter controlling the term frequency saturation.
- `b`: BM25 parameter controlling the document length normalization.
- `top_k`: Number of top results to return from the search.
- `latency`: Time taken to perform the search.

By following this lab guide, you will have a comprehensive understanding of implementing, tuning, and verifying a hybrid search system that combines BM25 and reranking.
