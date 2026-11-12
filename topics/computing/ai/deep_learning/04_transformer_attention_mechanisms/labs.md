# Operational Verification Labs: 04 Transformer Attention Mechanisms

## Objective & Environment Setup

The objective of this lab is to provide hands-on experience with implementing and verifying transformer attention mechanisms, a core component of modern deep learning models such as BERT, GPT, and T5. This lab will guide you through the implementation of a transformer attention mechanism, hyperparameter tuning, empirical benchmarking, and stress testing. The environment setup requires a Python 3.11+ environment with the following packages installed:

- PyTorch
- HuggingFace Transformers
- NumPy
- Scikit-learn
- Matplotlib

You can set up the environment using the following commands:

```bash
pip install torch transformers numpy scikit-learn matplotlib
```

## Exercise 1: Hands-On Implementation & Pipeline Execution

In this exercise, we will implement a simple transformer attention mechanism from scratch using PyTorch. The transformer attention mechanism is a fundamental building block that allows the model to weigh the importance of different words in a sequence when making predictions.

Here is a complete, runnable Python script implementing the core prompt/model/algorithm for this topic:

```python
import torch
import torch.nn as nn
import torch.nn.functional as F

class Attention(nn.Module):
    def __init__(self, embed_size, heads):
        super(Attention, self).__init__()
        self.embed_size = embed_size
        self.heads = heads
        self.head_dim = embed_size // heads

        assert (self.head_dim * heads == embed_size), "Embedding size needs to be divisible by heads"

        self.values = nn.Linear(self.head_dim, self.head_dim, bias=False)
        self.keys = nn.Linear(self.head_dim, self.head_dim, bias=False)
        self.queries = nn.Linear(self.head_dim, self.head_dim, bias=False)
        self.fc_out = nn.Linear(heads * self.head_dim, embed_size)

    def forward(self, values, keys, query, mask):
        N = query.shape[0]
        value_len, key_len, query_len = values.shape[1], keys.shape[1], query.shape[1]

        # Split the embedding into self.heads different pieces
        values = values.reshape(N, value_len, self.heads, self.head_dim)
        keys = keys.reshape(N, key_len, self.heads, self.head_dim)
        queries = query.reshape(N, query_len, self.heads, self.head_dim)

        values = self.values(values)
        keys = self.keys(keys)
        queries = self.queries(queries)

        energy = torch.einsum("nqhd,nkhd->nhqk", [queries, keys])
        # queries shape: (N, query_len, heads, heads_dim)
        # keys shape: (N, key_len, heads, heads_dim)
        # energy shape: (N, heads, query_len, key_len)

        if mask is not None:
            energy = energy.masked_fill(mask == 0, float("-1e20"))

        attention = torch.softmax(energy / (self.embed_size ** (1/2)), dim=3)

        out = torch.einsum("nhql,nlhd->nqhd", [attention, values]).reshape(
            N, query_len, self.heads * self.head_dim
        )
        # attention shape: (N, heads, query_len, key_len)
        # values shape: (N, value_len, heads, heads_dim)
        # out after matrix multiply: (N, query_len, heads, head_dim), then flatten last two dimensions

        out = self.fc_out(out)
        return out, attention

class TransformerBlock(nn.Module):
    def __init__(self, embed_size, heads, dropout, forward_expansion):
        super(TransformerBlock, self).__init__()
        self.attention = Attention(embed_size, heads)
        self.norm1 = nn.LayerNorm(embed_size)
        self.norm2 = nn.LayerNorm(embed_size)

        self.feed_forward = nn.Sequential(
            nn.Linear(embed_size, forward_expansion * embed_size),
            nn.ReLU(),
            nn.Linear(forward_expansion * embed_size, embed_size),
        )

        self.dropout = nn.Dropout(dropout)

    def forward(self, value, key, query, mask):
        attention, _ = self.attention(value, key, query, mask)

        # Add skip connection, run through normalization and finally dropout
        x = self.dropout(self.norm1(attention + query))
        forward = self.feed_forward(x)
        out = self.dropout(self.norm2(forward + x))
        return out

class Encoder(nn.Module):
    def __init__(
        self,
        src_vocab_size,
        embed_size,
        num_layers,
        heads,
        device,
        forward_expansion,
        dropout,
        max_length,
    ):
        super(Encoder, self).__init__()
        self.embed_size = embed_size
        self.device = device
        self.word_embedding = nn.Embedding(src_vocab_size, embed_size)
        self.position_embedding = nn.Embedding(max_length, embed_size)

        self.layers = nn.ModuleList(
            [
                TransformerBlock(
                    embed_size,
                    heads,
                    dropout=dropout,
                    forward_expansion=forward_expansion,
                )
                for _ in range(num_layers)
            ]
        )

        self.dropout = nn.Dropout(dropout)

    def forward(self, x, mask):
        N, seq_length = x.shape
        positions = torch.arange(0, seq_length).expand(N, seq_length).to(self.device)
        out = self.dropout((self.word_embedding(x) + self.position_embedding(positions)))
        for layer in self.layers:
            out = layer(out, out, out, mask)
        return out

class DecoderBlock(nn.Module):
    def __init__(self, embed_size, heads, forward_expansion, dropout, device):
        super(DecoderBlock, self).__init__()
        self.attention = Attention(embed_size, heads)
        self.norm = nn.LayerNorm(embed_size)
        self.transformer_block = TransformerBlock(
            embed_size, heads, dropout, forward_expansion
        )
        self.dropout = nn.Dropout(dropout)

    def forward(self, x, value, key, src_mask, trg_mask):
        attention, _ = self.attention(x, x, x, trg_mask)
        query = self.dropout(self.norm(attention + x))
        out = self.transformer_block(value, key, query, src_mask)
        return out

class Decoder(nn.Module):
    def __init__(
        self,
        trg_vocab_size,
        embed_size,
        num_layers,
        heads,
        forward_expansion,
        dropout,
        device,
        max_length,
    ):
        super(Decoder, self).__init__()
        self.device = device
        self.word_embedding = nn.Embedding(trg_vocab_size, embed_size)
        self.position_embedding = nn.Embedding(max_length, embed_size)

        self.layers = nn.ModuleList(
            [
                DecoderBlock(embed_size, heads, forward_expansion, dropout, device)
                for _ in range(num_layers)
            ]
        )

        self.fc_out = nn.Linear(embed_size, trg_vocab_size)
        self.dropout = nn.Dropout(dropout)

    def forward(self, x, enc_out, src_mask, trg_mask):
        N, seq_length = x.shape
        positions = torch.arange(0, seq_length).expand(N, seq_length).to(self.device)
        x = self.dropout((self.word_embedding(x) + self.position_embedding(positions)))
        for layer in self.layers:
            x = layer(x, enc_out, enc_out, src_mask, trg_mask)
        out = self.fc_out(x)
        return out

class Transformer(nn.Module):
    def __init__(
        self,
        src_vocab_size,
        trg_vocab_size,
        src_pad_idx,
        trg_pad_idx,
        embed_size=512,
        num_layers=6,
        forward_expansion=4,
        heads=8,
        dropout=0,
        device="cpu",
        max_length=100,
    ):
        super(Transformer, self).__init__()
        self.encoder = Encoder(
            src_vocab_size,
            embed_size,
            num_layers,
            heads,
            device,
            forward_expansion,
            dropout,
            max_length,
        )
        self.decoder = Decoder(
            trg_vocab_size,
            embed_size,
            num_layers,
            heads,
            forward_expansion,
            dropout,
            device,
            max_length,
        )
        self.src_pad_idx = src_pad_idx
        self.trg_pad_idx = trg_pad_idx
        self.device = device

    def make_src_mask(self, src):
        src_mask = (src != self.src_pad_idx).unsqueeze(1).unsqueeze(2)
        # (N, 1, 1, src_len)
        return src_mask.to(self.device)

    def make_trg_mask(self, trg):
        N, trg_len = trg.shape
        trg_mask = torch.tril(torch.ones((trg_len, trg_len))).expand(
            N, 1, trg_len, trg_len
        )
        return trg_mask.to(self.device)

    def forward(self, src, trg):
        src_mask = self.make_src_mask(src)
        trg_mask = self.make_trg_mask(trg)
        enc_src = self.encoder(src, src_mask)
        out = self.decoder(trg, enc_src, src_mask, trg_mask)
        return out

# Example usage
if __name__ == "__main__":
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(device)

    src_vocab_size = 10
    trg_vocab_size = 10
    src_pad_idx = 0
    trg_pad_idx = 0
    model = Transformer(src_vocab_size, trg_vocab_size, src_pad_idx, trg_pad_idx).to(device)

    src = torch.LongTensor([[1, 2, 3, 4, 5], [5, 4, 3, 2, 1]]).to(device)
    trg = torch.LongTensor([[1, 2, 3, 4, 5], [5, 4, 3, 2, 1]]).to(device)

    output = model(src, trg[:, :-1])
    print(output.shape)
```

## Exercise 2: Hyperparameter Tuning & Empirical Benchmarking

In this exercise, we will perform hyperparameter tuning and empirical benchmarking of the transformer model. We will measure accuracy, latency distributions, and convergence curves.

Here is the benchmarking code measuring accuracy, latency distributions, and convergence curves:

```python
import time
import numpy as np
from sklearn.metrics import accuracy_score

def benchmark_model(model, src, trg, num_iterations=100):
    model.eval()
    latencies = []
    predictions = []

    with torch.no_grad():
        for _ in range(num_iterations):
            start_time = time.time()
            output = model(src, trg[:, :-1])
            end_time = time.time()
            latencies.append(end_time - start_time)

            # Assuming output is logits, we take the argmax to get the predicted class
            predicted = torch.argmax(output, dim=-1)
            predictions.append(predicted.cpu().numpy())

    # Calculate accuracy
    true_labels = trg[:, 1:].cpu().numpy()
    all_predictions = np.concatenate(predictions)
    accuracy = accuracy_score(true_labels.flatten(), all_predictions.flatten())

    # Calculate latency statistics
    avg_latency = np.mean(latencies)
    std_latency = np.std(latencies)
    max_latency = np.max(latencies)
    min_latency = np.min(latencies)

    return accuracy, avg_latency, std_latency, max_latency, min_latency

# Example usage
if __name__ == "__main__":
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(device)

    src_vocab_size = 10
    trg_vocab_size = 10
    src_pad_idx = 0
    trg_pad_idx = 0
    model = Transformer(src_vocab_size, trg_vocab_size, src_pad_idx, trg_pad_idx).to(device)

    src = torch.LongTensor([[1, 2, 3, 4, 5], [5, 4, 3, 2, 1]]).to(device)
    trg = torch.LongTensor([[1, 2, 3, 4, 5], [5, 4, 3, 2, 1]]).to(device)

    accuracy, avg_latency, std_latency, max_latency, min_latency = benchmark_model(model, src, trg)
    print(f"Accuracy: {accuracy}")
    print(f"Average Latency: {avg_latency} seconds")
    print(f"Standard Deviation of Latency: {std_latency} seconds")
    print(f"Maximum Latency: {max_latency} seconds")
    print(f"Minimum Latency: {min_latency} seconds")
```

## Exercise 3: Stress Testing, Edge Cases & Failure Mitigation

In this exercise, we will reproduce failure modes, test edge cases, and implement guardrails or error handling.

Here is the code for stress testing, edge cases, and failure mitigation:

```python
def stress_test_model(model, src, trg, num_iterations=1000):
    model.eval()
    for _ in range(num_iterations):
        try:
            output = model(src, trg[:, :-1])
            predicted = torch.argmax(output, dim=-1)
        except Exception as e:
            print(f"Error during stress test: {e}")
            return False
    return True

def test_edge_cases(model, src, trg):
    model.eval()
    edge_cases = [
        (torch.LongTensor([[0, 0, 0, 0, 0]]).to(device), torch.LongTensor([[0, 0, 0, 0, 0]]).to(device)),
        (torch.LongTensor([[1, 2, 3, 4, 5]]).to(device), torch.LongTensor([[1, 2, 3, 4, 5]]).to(device)),
        (torch.LongTensor([[9, 9, 9, 9, 9]]).to(device), torch.LongTensor([[9, 9, 9, 9, 9]]).to(device)),
    ]

    for src_case, trg_case in edge_cases:
        try:
            output = model(src_case, trg_case[:, :-1])
            predicted = torch.argmax(output, dim=-1)
        except Exception as e:
            print(f"Error during edge case test: {e}")
            return False
    return True

# Example usage
if __name__ == "__main__":
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(device)

    src_vocab_size = 10
    trg_vocab_size = 10
    src_pad_idx = 0
    trg_pad_idx = 0
    model = Transformer(src_vocab_size, trg_vocab_size, src_pad_idx, trg_pad_idx).to(device)

    src = torch.LongTensor([[1, 2, 3, 4, 5], [5, 4, 3, 2, 1]]).to(device)
    trg = torch.LongTensor([[1, 2, 3, 4, 5], [5, 4, 3, 2, 1]]).to(device)

    stress_test_passed = stress_test_model(model, src, trg)
    print(f"Stress Test Passed: {stress_test_passed}")

    edge_cases_passed = test_edge_cases(model, src, trg)
    print(f"Edge Cases Passed: {edge_cases_passed}")
```

## Verification Checklist & Quick Reference Cheat Sheet

| Method/Parameter | Description |
|------------------|-------------|
| `Attention`      | Implements the attention mechanism. |
| `TransformerBlock` | Implements a single transformer block. |
| `Encoder`        | Implements the encoder part of the transformer. |
| `DecoderBlock`   | Implements a single decoder block. |
| `Decoder`        | Implements the decoder part of the transformer. |
| `Transformer`    | Implements the full transformer model. |
| `make_src_mask`  | Creates a mask for the source sequence. |
| `make_trg_mask`  | Creates a mask for the target sequence. |
| `forward`        | Forward pass through the model. |
| `benchmark_model`| Benchmarks the model for accuracy and latency. |
| `stress_test_model` | Performs stress testing on the model. |
| `test_edge_cases` | Tests the model with edge cases. |
| `accuracy_score` | Calculates the accuracy of the model predictions. |
| `torch.no_grad`  | Disables gradient calculation for inference. |
| `torch.argmax`   | Returns the indices of the maximum values along a dimension. |
| `torch.device`   | Specifies the device (CPU/GPU) for tensor operations. |
| `torch.LongTensor` | Creates a tensor of type `Long`. |
| `torch.cuda.is_available` | Checks if CUDA is available. |

This lab provides a comprehensive hands-on experience with transformer attention mechanisms, including implementation, benchmarking, and stress testing. By the end of this lab, you should have a solid understanding of how transformer models work and how to evaluate their performance.
