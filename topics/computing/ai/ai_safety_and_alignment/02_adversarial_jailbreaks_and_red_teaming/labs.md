# Operational Verification Labs: 02 Adversarial Jailbreaks And Red Teaming

## Objective & Environment Setup

### Objective
The primary objective of this lab is to provide hands-on experience with adversarial jailbreaks and red teaming in the context of AI and AI safety. This lab will guide you through implementing, tuning, and verifying adversarial attacks on AI models, with a focus on understanding the mechanisms of jailbreaks and developing strategies to mitigate them.

### Environment Setup
Ensure you have a Python 3.11+ environment set up with the following packages:
- PyTorch
- HuggingFace Transformers
- NumPy
- Scikit-learn
- Ollama (or any other API harness for deploying AI models)
- Polars (for data manipulation, if needed)

You can install these packages using pip:
```bash
pip install torch transformers numpy scikit-learn ollama polars
```

Additionally, configure any necessary API keys or environment variables for Ollama or other services you plan to use.

## Exercise 1: Hands-On Implementation & Pipeline Execution

### Core Prompt/Model/Algorithm Implementation

In this exercise, we will implement a basic adversarial attack on a pre-trained language model using the HuggingFace Transformers library. We will use the Fast Gradient Sign Method (FGSM) to generate adversarial examples.

```python
import torch
import torch.nn.functional as F
from transformers import GPT2Tokenizer, GPT2LMHeadModel

# Load pre-trained model and tokenizer
model_name = 'gpt2'
tokenizer = GPT2Tokenizer.from_pretrained(model_name)
model = GPT2LMHeadModel.from_pretrained(model_name)
model.eval()

def generate_adversarial_example(prompt, epsilon=0.01):
    # Tokenize input
    input_ids = tokenizer.encode(prompt, return_tensors='pt')
    input_ids.requires_grad_(True)
    
    # Forward pass
    outputs = model(input_ids)
    loss = F.cross_entropy(outputs.logits[:, -1, :], input_ids[:, -1])
    
    # Backward pass
    model.zero_grad()
    loss.backward()
    
    # Generate adversarial example
    grad_sign = input_ids.grad.sign()
    perturbed_input = input_ids + epsilon * grad_sign
    perturbed_input = torch.clamp(perturbed_input, min=0, max=tokenizer.vocab_size - 1)
    
    # Decode adversarial example
    adversarial_text = tokenizer.decode(perturbed_input[0], skip_special_tokens=True)
    return adversarial_text

# Example usage
prompt = "The quick brown fox jumps over the lazy dog"
adversarial_text = generate_adversarial_example(prompt)
print(f"Original: {prompt}")
print(f"Adversarial: {adversarial_text}")
```

## Exercise 2: Hyperparameter Tuning & Empirical Benchmarking

### Benchmarking Code

In this exercise, we will benchmark the effectiveness of the adversarial attack by measuring accuracy, latency, and token costs.

```python
import time
import numpy as np

def benchmark_adversarial_attack(prompt, epsilon_values, num_trials=10):
    results = []
    for epsilon in epsilon_values:
        accuracies = []
        latencies = []
        token_costs = []
        
        for _ in range(num_trials):
            start_time = time.time()
            adversarial_text = generate_adversarial_example(prompt, epsilon)
            end_time = time.time()
            
            # Measure latency
            latency = end_time - start_time
            latencies.append(latency)
            
            # Measure token cost (number of tokens in adversarial text)
            token_cost = len(tokenizer.encode(adversarial_text))
            token_costs.append(token_cost)
            
            # Measure accuracy (similarity between original and adversarial text)
            original_tokens = set(tokenizer.encode(prompt))
            adversarial_tokens = set(tokenizer.encode(adversarial_text))
            accuracy = len(original_tokens.intersection(adversarial_tokens)) / len(original_tokens)
            accuracies.append(accuracy)
        
        results.append({
            'epsilon': epsilon,
            'mean_accuracy': np.mean(accuracies),
            'std_accuracy': np.std(accuracies),
            'mean_latency': np.mean(latencies),
            'std_latency': np.std(latencies),
            'mean_token_cost': np.mean(token_costs),
            'std_token_cost': np.std(token_costs)
        })
    
    return results

# Example usage
epsilon_values = [0.01, 0.05, 0.1]
results = benchmark_adversarial_attack(prompt, epsilon_values)
for result in results:
    print(f"Epsilon: {result['epsilon']}")
    print(f"Mean Accuracy: {result['mean_accuracy']:.4f} ± {result['std_accuracy']:.4f}")
    print(f"Mean Latency: {result['mean_latency']:.4f} ± {result['std_latency']:.4f} seconds")
    print(f"Mean Token Cost: {result['mean_token_cost']:.4f} ± {result['std_token_cost']:.4f} tokens")
    print()
```

## Exercise 3: Stress Testing, Edge Cases & Failure Mitigation

### Reproducing Failure Modes and Testing Edge Cases

In this exercise, we will test the adversarial attack on various edge cases and implement guardrails to mitigate failures.

```python
def test_edge_cases():
    edge_cases = [
        "A",
        "The quick brown fox jumps over the lazy dog",
        "This is a longer prompt that should test the robustness of the adversarial attack mechanism."
    ]
    
    for prompt in edge_cases:
        print(f"Testing prompt: {prompt}")
        adversarial_text = generate_adversarial_example(prompt)
        print(f"Adversarial: {adversarial_text}")
        print()

# Example usage
test_edge_cases()

def implement_guardrails(prompt, epsilon):
    try:
        adversarial_text = generate_adversarial_example(prompt, epsilon)
        return adversarial_text
    except Exception as e:
        print(f"Error generating adversarial example: {e}")
        return None

# Example usage
prompt = "The quick brown fox jumps over the lazy dog"
epsilon = 0.1
adversarial_text = implement_guardrails(prompt, epsilon)
if adversarial_text:
    print(f"Adversarial: {adversarial_text}")
```

## Verification Checklist & Quick Reference Cheat Sheet

### Essential Python Methods, Parameters, and Verification Flags

| Method/Parameter | Description |
|------------------|-------------|
| `generate_adversarial_example(prompt, epsilon)` | Generates an adversarial example using FGSM. |
| `benchmark_adversarial_attack(prompt, epsilon_values, num_trials)` | Benchmarks the adversarial attack across different epsilon values. |
| `test_edge_cases()` | Tests the adversarial attack on various edge cases. |
| `implement_guardrails(prompt, epsilon)` | Implements guardrails to handle potential errors during adversarial example generation. |
| `epsilon` | Perturbation factor for FGSM. |
| `num_trials` | Number of trials for benchmarking. |
| `prompt` | Input text for the adversarial attack. |

This lab provides a comprehensive hands-on experience with adversarial jailbreaks and red teaming in AI systems. By implementing, tuning, and verifying adversarial attacks, you will gain a deeper understanding of the challenges and strategies involved in AI safety and alignment.
