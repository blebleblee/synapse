# Operational Verification Labs: 01 Document Chunking And Embedding Models

## Objective & Environment Setup

### Objective
The primary objective of this lab is to gain hands-on experience with document chunking and embedding models. You will implement a pipeline that processes documents, chunks them into manageable segments, and generates embeddings for each chunk. This lab will cover the entire process from data ingestion to model evaluation, including hyperparameter tuning and stress testing.

### Environment Setup
Ensure you have a Python 3.11+ environment set up. You will need the following packages:
- `transformers` (Hugging Face)
- `torch` (PyTorch)
- `numpy`
- `scikit-learn`
- `pandas`
- `tqdm` (for progress bars)

You can install these packages using pip:

```bash
pip install transformers torch numpy scikit-learn pandas tqdm
```

Additionally, ensure you have an API key for a model hosting service like Hugging Face or Ollama if you plan to use their models.

## Exercise 1: Hands-On Implementation & Pipeline Execution

In this exercise, we will implement a complete pipeline for document chunking and embedding. The pipeline will include:
1. Document loading and preprocessing.
2. Chunking the document into smaller segments.
3. Generating embeddings for each chunk using a pre-trained model.
4. Saving the embeddings for further use.

### Complete, Runnable Python Script

```python
import os
import numpy as np
import pandas as pd
from transformers import AutoTokenizer, AutoModel
from sklearn.metrics.pairwise import cosine_similarity
from tqdm import tqdm

# Configuration
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
CHUNK_SIZE = 512  # Maximum number of tokens per chunk
OVERLAP = 64      # Overlap between chunks

# Load pre-trained model and tokenizer
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModel.from_pretrained(MODEL_NAME)

def load_document(file_path):
    """Load a document from a file."""
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()

def chunk_document(document, chunk_size, overlap):
    """Chunk a document into smaller segments."""
    tokens = tokenizer.tokenize(document)
    chunks = []
    for i in range(0, len(tokens), chunk_size - overlap):
        chunk = tokens[i:i + chunk_size]
        chunks.append(' '.join(chunk))
    return chunks

def generate_embeddings(chunks):
    """Generate embeddings for each chunk."""
    embeddings = []
    for chunk in tqdm(chunks, desc="Generating embeddings"):
        inputs = tokenizer(chunk, return_tensors='pt', truncation=True, padding=True)
        with torch.no_grad():
            outputs = model(**inputs)
        embeddings.append(outputs.last_hidden_state.mean(dim=1).numpy())
    return np.vstack(embeddings)

def save_embeddings(embeddings, output_path):
    """Save embeddings to a file."""
    np.save(output_path, embeddings)

def main():
    # Load document
    document = load_document("example_document.txt")
    
    # Chunk document
    chunks = chunk_document(document, CHUNK_SIZE, OVERLAP)
    
    # Generate embeddings
    embeddings = generate_embeddings(chunks)
    
    # Save embeddings
    save_embeddings(embeddings, "embeddings.npy")

if __name__ == "__main__":
    main()
```

### Explanation
1. **Loading the Document**: The `load_document` function reads the document from a file.
2. **Chunking the Document**: The `chunk_document` function tokenizes the document and chunks it into smaller segments with a specified overlap.
3. **Generating Embeddings**: The `generate_embeddings` function uses a pre-trained model to generate embeddings for each chunk.
4. **Saving Embeddings**: The `save_embeddings` function saves the generated embeddings to a file.

## Exercise 2: Hyperparameter Tuning & Empirical Benchmarking

In this exercise, we will benchmark the performance of our document chunking and embedding pipeline. We will measure accuracy, latency, and token costs.

### Benchmarking Code

```python
import time
import torch

def benchmark_pipeline():
    # Load document
    document = load_document("example_document.txt")
    
    # Measure chunking time
    start_time = time.time()
    chunks = chunk_document(document, CHUNK_SIZE, OVERLAP)
    chunking_time = time.time() - start_time
    
    # Measure embedding generation time
    start_time = time.time()
    embeddings = generate_embeddings(chunks)
    embedding_time = time.time() - start_time
    
    # Calculate token costs
    total_tokens = sum(len(tokenizer.tokenize(chunk)) for chunk in chunks)
    token_cost = total_tokens * 0.0001  # Hypothetical cost per token
    
    # Print results
    print(f"Chunking Time: {chunking_time:.4f} seconds")
    print(f"Embedding Generation Time: {embedding_time:.4f} seconds")
    print(f"Total Tokens: {total_tokens}")
    print(f"Estimated Token Cost: ${token_cost:.4f}")

if __name__ == "__main__":
    benchmark_pipeline()
```

### Explanation
1. **Chunking Time**: Measures the time taken to chunk the document.
2. **Embedding Generation Time**: Measures the time taken to generate embeddings for each chunk.
3. **Token Costs**: Calculates the total number of tokens and estimates the cost based on a hypothetical rate.

## Exercise 3: Stress Testing, Edge Cases & Failure Mitigation

In this exercise, we will test the pipeline under various stress conditions and edge cases, and implement guardrails to handle failures.

### Stress Testing and Edge Cases

```python
def stress_test_pipeline():
    # Test with a very large document
    large_document = " ".join(["This is a test sentence."] * 10000)
    chunks = chunk_document(large_document, CHUNK_SIZE, OVERLAP)
    embeddings = generate_embeddings(chunks)
    print(f"Large Document: {len(chunks)} chunks, {embeddings.shape[0]} embeddings")
    
    # Test with an empty document
    empty_document = ""
    chunks = chunk_document(empty_document, CHUNK_SIZE, OVERLAP)
    embeddings = generate_embeddings(chunks)
    print(f"Empty Document: {len(chunks)} chunks, {embeddings.shape[0]} embeddings")
    
    # Test with a document containing only special characters
    special_document = "!" * 1000
    chunks = chunk_document(special_document, CHUNK_SIZE, OVERLAP)
    embeddings = generate_embeddings(chunks)
    print(f"Special Characters Document: {len(chunks)} chunks, {embeddings.shape[0]} embeddings")

if __name__ == "__main__":
    stress_test_pipeline()
```

### Explanation
1. **Large Document**: Tests the pipeline with a very large document to ensure it can handle large inputs.
2. **Empty Document**: Tests the pipeline with an empty document to ensure it handles empty inputs gracefully.
3. **Special Characters Document**: Tests the pipeline with a document containing only special characters to ensure it handles such cases.

### Failure Mitigation

```python
def generate_embeddings_safe(chunks):
    """Generate embeddings for each chunk with error handling."""
    embeddings = []
    for chunk in tqdm(chunks, desc="Generating embeddings"):
        try:
            inputs = tokenizer(chunk, return_tensors='pt', truncation=True, padding=True)
            with torch.no_grad():
                outputs = model(**inputs)
            embeddings.append(outputs.last_hidden_state.mean(dim=1).numpy())
        except Exception as e:
            print(f"Error processing chunk: {chunk[:50]}... - {e}")
            embeddings.append(np.zeros((1, model.config.hidden_size)))
    return np.vstack(embeddings)

def main_safe():
    # Load document
    document = load_document("example_document.txt")
    
    # Chunk document
    chunks = chunk_document(document, CHUNK_SIZE, OVERLAP)
    
    # Generate embeddings with error handling
    embeddings = generate_embeddings_safe(chunks)
    
    # Save embeddings
    save_embeddings(embeddings, "embeddings_safe.npy")

if __name__ == "__main__":
    main_safe()
```

### Explanation
1. **Error Handling**: The `generate_embeddings_safe` function includes error handling to manage exceptions during embedding generation.

## Verification Checklist & Quick Reference Cheat Sheet

### Essential Python Methods and Parameters

| Method/Parameter | Description |
|------------------|-------------|
| `load_document`  | Loads a document from a file. |
| `chunk_document` | Chunks a document into smaller segments. |
| `generate_embeddings` | Generates embeddings for each chunk. |
| `save_embeddings` | Saves embeddings to a file. |
| `benchmark_pipeline` | Benchmarks the pipeline for performance. |
| `stress_test_pipeline` | Tests the pipeline under stress conditions. |
| `generate_embeddings_safe` | Generates embeddings with error handling. |

### Verification Flags

| Flag | Description |
|------|-------------|
| `CHUNK_SIZE` | Maximum number of tokens per chunk. |
| `OVERLAP` | Overlap between chunks. |
| `MODEL_NAME` | Name of the pre-trained model. |

### CLI Commands

1. **Run the main pipeline**:
    ```bash
    python document_chunking_embedding.py
    ```

2. **Run the benchmarking pipeline**:
    ```bash
    python benchmark_pipeline.py
    ```

3. **Run the stress testing pipeline**:
    ```bash
    python stress_test_pipeline.py
    ```

This lab provides a comprehensive hands-on experience with document chunking and embedding models, covering implementation, benchmarking, and failure mitigation.
