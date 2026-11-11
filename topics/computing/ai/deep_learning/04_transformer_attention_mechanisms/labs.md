# Operational Verification Labs: 04 Transformer Attention Mechanisms

## Objective & Environment Setup

### Objective
The primary objective of this lab is to provide hands-on experience with implementing and verifying transformer attention mechanisms. This lab will guide you through the process of building a transformer model, tuning its hyperparameters, benchmarking its performance, and handling edge cases. By the end of this lab, you will have a solid understanding of how transformer attention mechanisms work and how to apply them in practical scenarios.

### Environment Setup
Ensure you have a Python 3.11+ environment set up with the following packages installed:

- PyTorch
- HuggingFace Transformers
- NumPy
- Scikit-learn
- Matplotlib
- Ollama (optional, for API integration)
- Polars (optional, for data manipulation)

You can install these packages using pip:

```bash
pip install torch transformers numpy scikit-learn matplotlib ollama polars
```

## Exercise 1: Hands-On Implementation & Pipeline Execution

In this exercise, we will implement a simple transformer model using PyTorch and the HuggingFace Transformers library. We will then execute a pipeline to process input data through this model.

### Complete, Runnable Python Script

```python
import torch
from torch import nn
from transformers import BertTokenizer, BertModel
import numpy as np
import matplotlib.pyplot as plt

# Define a simple transformer model
class SimpleTransformer(nn.Module):
    def __init__(self, input_dim, hidden_dim, output_dim, num_heads, num_layers):
        super(SimpleTransformer, self).__init__()
        self.embedding = nn.Embedding(input_dim, hidden_dim)
        self.transformer = nn.Transformer(d_model=hidden_dim, nhead=num_heads, num_encoder_layers=num_layers, num_decoder_layers=num_layers)
        self.fc = nn.Linear(hidden_dim, output_dim)

    def forward(self, src, tgt):
        src = self.embedding(src)
        tgt = self.embedding(tgt)
        output = self.transformer(src, tgt)
        output = self.fc(output)
        return output

# Load pre-trained BERT tokenizer and model
tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')
model = BertModel.from_pretrained('bert-base-uncased')

# Example input
text = "Hello, how are you?"
inputs = tokenizer(text, return_tensors='pt')

# Get the last hidden-state is the first element of the output tuple
with torch.no_grad():
    outputs = model(**inputs)
    last_hidden_states = outputs.last_hidden_state

# Print the shape of the last hidden states
print(f"Shape of last hidden states: {last_hidden_states.shape}")

# Define a simple transformer model
input_dim = tokenizer.vocab_size
hidden_dim = 768
output_dim = 768
num_heads = 12
num_layers = 6

transformer_model = SimpleTransformer(input_dim, hidden_dim, output_dim, num_heads, num_layers)

# Example input and target sequences
src = torch.randint(0, input_dim, (1, 10))
tgt = torch.randint(0, input_dim, (1, 10))

# Forward pass
output = transformer_model(src, tgt)
print(f"Output shape: {output.shape}")

# Plotting the attention weights
attention_weights = transformer_model.transformer.encoder.layers[0].self_attn.attn_output_weights
plt.figure(figsize=(10, 8))
plt.imshow(attention_weights.squeeze().cpu().numpy(), cmap='viridis')
plt.title('Attention Weights')
plt.xlabel('Target Sequence')
plt.ylabel('Source Sequence')
plt.colorbar()
plt.show()
```

## Exercise 2: Hyperparameter Tuning & Empirical Benchmarking

In this exercise, we will perform hyperparameter tuning and benchmark the performance of our transformer model. We will measure accuracy, latency distributions, and convergence curves.

### Real Benchmarking Code

```python
import time
from sklearn.metrics import accuracy_score
from torch.utils.data import DataLoader, TensorDataset
import torch.optim as optim

# Generate synthetic data
num_samples = 1000
input_dim = tokenizer.vocab_size
seq_length = 10
X = torch.randint(0, input_dim, (num_samples, seq_length))
y = torch.randint(0, input_dim, (num_samples, seq_length))

# Create DataLoader
dataset = TensorDataset(X, y)
dataloader = DataLoader(dataset, batch_size=32, shuffle=True)

# Define loss function and optimizer
criterion = nn.CrossEntropyLoss()
optimizer = optim.Adam(transformer_model.parameters(), lr=1e-4)

# Training loop with benchmarking
num_epochs = 5
latencies = []
accuracies = []

for epoch in range(num_epochs):
    epoch_start_time = time.time()
    epoch_loss = 0.0
    correct = 0
    total = 0

    for batch_idx, (src, tgt) in enumerate(dataloader):
        optimizer.zero_grad()
        start_time = time.time()
        output = transformer_model(src, tgt)
        loss = criterion(output.view(-1, output_dim), tgt.view(-1))
        loss.backward()
        optimizer.step()
        end_time = time.time()
        latencies.append(end_time - start_time)

        # Calculate accuracy
        _, predicted = torch.max(output.data, 2)
        total += tgt.size(0) * tgt.size(1)
        correct += (predicted == tgt).sum().item()
        epoch_loss += loss.item()

    epoch_end_time = time.time()
    epoch_time = epoch_end_time - epoch_start_time
    accuracy = correct / total
    accuracies.append(accuracy)

    print(f"Epoch [{epoch+1}/{num_epochs}], Loss: {epoch_loss/len(dataloader):.4f}, Accuracy: {accuracy:.4f}, Time: {epoch_time:.2f}s")

# Plotting latency distribution
plt.figure(figsize=(10, 6))
plt.hist(latencies, bins=50, color='blue', alpha=0.7)
plt.title('Latency Distribution')
plt.xlabel('Latency (s)')
plt.ylabel('Frequency')
plt.show()

# Plotting accuracy over epochs
plt.figure(figsize=(10, 6))
plt.plot(range(1, num_epochs+1), accuracies, marker='o', linestyle='-')
plt.title('Accuracy Over Epochs')
plt.xlabel('Epoch')
plt.ylabel('Accuracy')
plt.grid(True)
plt.show()
```

## Exercise 3: Stress Testing, Edge Cases & Failure Mitigation

In this exercise, we will test the transformer model under various stress conditions, handle edge cases, and implement guardrails or error handling.

### Reproducing Failure Modes, Testing Edge Cases, and Implementing Guardrails

```python
# Stress test with long sequences
long_seq_length = 1000
long_src = torch.randint(0, input_dim, (1, long_seq_length))
long_tgt = torch.randint(0, input_dim, (1, long_seq_length))

try:
    with torch.no_grad():
        long_output = transformer_model(long_src, long_tgt)
    print(f"Output shape for long sequence: {long_output.shape}")
except RuntimeError as e:
    print(f"Runtime error for long sequence: {e}")

# Edge case with empty input
empty_src = torch.tensor([], dtype=torch.long)
empty_tgt = torch.tensor([], dtype=torch.long)

try:
    with torch.no_grad():
        empty_output = transformer_model(empty_src, empty_tgt)
    print(f"Output shape for empty input: {empty_output.shape}")
except RuntimeError as e:
    print(f"Runtime error for empty input: {e}")

# Implementing guardrails
def safe_forward(model, src, tgt):
    if src.size(1) == 0 or tgt.size(1) == 0:
        raise ValueError("Input sequences cannot be empty.")
    if src.size(1) > 1000 or tgt.size(1) > 1000:
        raise ValueError("Input sequences are too long.")
    return model(src, tgt)

# Test guardrails
try:
    safe_output = safe_forward(transformer_model, long_src, long_tgt)
except ValueError as e:
    print(f"Guardrail triggered for long sequence: {e}")

try:
    safe_output = safe_forward(transformer_model, empty_src, empty_tgt)
except ValueError as e:
    print(f"Guardrail triggered for empty input: {e}")
```

## Verification Checklist & Quick Reference Cheat Sheet

### Essential Python Methods, Parameters, and Verification Flags

| Method/Parameter | Description |
|------------------|-------------|
| `SimpleTransformer` | Custom transformer model class |
| `BertTokenizer` | HuggingFace tokenizer for BERT model |
| `BertModel` | Pre-trained BERT model from HuggingFace |
| `nn.Embedding` | Embedding layer for input sequences |
| `nn.Transformer` | Transformer layer with encoder and decoder |
| `nn.Linear` | Fully connected layer for output |
| `tokenizer(text, return_tensors='pt')` | Tokenize input text and return PyTorch tensors |
| `model(**inputs)` | Forward pass through the pre-trained BERT model |
| `transformer_model(src, tgt)` | Forward pass through the custom transformer model |
| `criterion(output.view(-1, output_dim), tgt.view(-1))` | Compute cross-entropy loss |
| `optimizer.zero_grad()` | Zero the gradients before backward pass |
| `loss.backward()` | Backward pass to compute gradients |
| `optimizer.step()` | Update model parameters |
| `torch.no_grad()` | Disable gradient calculation for inference |
| `plt.hist(latencies, bins=50, color='blue', alpha=0.7)` | Plot latency distribution |
| `plt.plot(range(1, num_epochs+1), accuracies, marker='o', linestyle='-')` | Plot accuracy over epochs |
| `safe_forward(model, src, tgt)` | Guardrails for safe model execution |

This lab provides a comprehensive hands-on experience with transformer attention mechanisms, from implementation to verification. By following the exercises, you will gain practical insights into the inner workings of transformers and how to optimize and robustify them for real-world applications.
