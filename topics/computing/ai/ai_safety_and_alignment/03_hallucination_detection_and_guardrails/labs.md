# Operational Verification Labs: 03 Hallucination Detection And Guardrails

## Objective & Environment Setup

### Objective
The primary objective of this lab is to implement, test, and verify a hallucination detection system for AI models. Hallucination in AI models refers to the generation of outputs that are factually incorrect or inconsistent with the input or training data. This lab will guide you through the process of building a system that can detect such hallucinations and implement guardrails to mitigate their impact.

### Environment Setup
Ensure you have a Python 3.11+ environment set up with the following packages:
- PyTorch
- HuggingFace Transformers
- NumPy
- Scikit-learn
- Ollama (or any other API harness for AI models)
- Polars (for data manipulation)

You can install these packages using pip:

```bash
pip install torch transformers numpy scikit-learn ollama polars
```

Additionally, configure any necessary API keys or credentials for the AI model service you are using.

## Exercise 1: Hands-On Implementation & Pipeline Execution

In this exercise, we will implement a basic hallucination detection system using a pre-trained language model. The system will compare the generated output against a set of known facts to identify any hallucinations.

### Step-by-Step Implementation

1. **Load a Pre-trained Model:**
   We will use a pre-trained language model from HuggingFace's Transformers library.

2. **Define Known Facts:**
   Create a dataset of known facts that the model can be compared against.

3. **Generate Output:**
   Use the model to generate text based on a given prompt.

4. **Detect Hallucinations:**
   Compare the generated output against the known facts to detect any hallucinations.

Here is the complete, runnable Python script for this exercise:

```python
import torch
from transformers import pipeline
import numpy as np
import polars as pl

# Load a pre-trained model
model_name = "gpt2"
generator = pipeline('text-generation', model=model_name)

# Define known facts
known_facts = [
    "The capital of France is Paris.",
    "The largest planet in our solar system is Jupiter.",
    "Water boils at 100 degrees Celsius at sea level."
]

# Convert known facts to a Polars DataFrame for easy comparison
known_facts_df = pl.DataFrame({"fact": known_facts})

# Function to generate text
def generate_text(prompt, max_length=50):
    result = generator(prompt, max_length=max_length, num_return_sequences=1)
    return result[0]['generated_text']

# Function to detect hallucinations
def detect_hallucinations(generated_text, known_facts_df):
    hallucinations = []
    for fact in known_facts_df['fact']:
        if fact not in generated_text:
            hallucinations.append(fact)
    return hallucinations

# Example prompt
prompt = "Tell me about the solar system and water properties."

# Generate text
generated_text = generate_text(prompt)
print("Generated Text:")
print(generated_text)

# Detect hallucinations
hallucinations = detect_hallucinations(generated_text, known_facts_df)
if hallucinations:
    print("\nDetected Hallucinations:")
    for hallucination in hallucinations:
        print(f"- {hallucination}")
else:
    print("\nNo hallucinations detected.")
```

## Exercise 2: Hyperparameter Tuning & Empirical Benchmarking

In this exercise, we will tune the hyperparameters of the model and benchmark the performance in terms of accuracy, latency, and token costs.

### Step-by-Step Benchmarking

1. **Tune Hyperparameters:**
   Experiment with different hyperparameters such as `max_length`, `temperature`, and `top_k` to find the optimal settings for hallucination detection.

2. **Measure Performance:**
   Use Scikit-learn to measure the accuracy of the hallucination detection system. Measure latency and token costs using Polars for data manipulation.

Here is the complete, runnable Python script for this exercise:

```python
import time
from sklearn.metrics import accuracy_score
import polars as pl

# Define hyperparameters to tune
hyperparameters = [
    {"max_length": 50, "temperature": 0.7, "top_k": 50},
    {"max_length": 60, "temperature": 0.5, "top_k": 40},
    {"max_length": 70, "temperature": 0.3, "top_k": 30}
]

# Function to generate text with hyperparameters
def generate_text_with_params(prompt, params):
    result = generator(prompt, max_length=params['max_length'], num_return_sequences=1, temperature=params['temperature'], top_k=params['top_k'])
    return result[0]['generated_text']

# Function to evaluate hallucinations
def evaluate_hallucinations(generated_text, known_facts_df):
    hallucinations = detect_hallucinations(generated_text, known_facts_df)
    return len(hallucinations) == 0

# Benchmarking
results = []
for params in hyperparameters:
    start_time = time.time()
    generated_text = generate_text_with_params(prompt, params)
    end_time = time.time()
    latency = end_time - start_time
    token_count = len(generated_text.split())
    accuracy = evaluate_hallucinations(generated_text, known_facts_df)
    results.append({
        "params": params,
        "latency": latency,
        "token_count": token_count,
        "accuracy": accuracy
    })

# Convert results to Polars DataFrame
results_df = pl.DataFrame(results)

# Display results
print("\nBenchmarking Results:")
print(results_df)
```

## Exercise 3: Stress Testing, Edge Cases & Failure Mitigation

In this exercise, we will test the system under various stress conditions and edge cases, and implement guardrails to mitigate failures.

### Step-by-Step Stress Testing

1. **Stress Test with Long Prompts:**
   Test the system with very long prompts to see how it handles large inputs.

2. **Edge Cases:**
   Test the system with edge cases such as empty prompts, prompts with special characters, and prompts with no factual content.

3. **Implement Guardrails:**
   Implement guardrails to handle failures gracefully, such as setting a maximum token limit and providing fallback responses.

Here is the complete, runnable Python script for this exercise:

```python
# Stress Test with Long Prompts
long_prompt = " ".join(["The solar system is vast and contains many planets. " for _ in range(100)])
generated_text_long = generate_text_with_params(long_prompt, hyperparameters[0])
print("\nGenerated Text for Long Prompt:")
print(generated_text_long)

# Edge Cases
edge_cases = [
    "",
    "!!!",
    "This prompt has no factual content."
]

for edge_case in edge_cases:
    generated_text_edge = generate_text_with_params(edge_case, hyperparameters[0])
    print(f"\nGenerated Text for Edge Case '{edge_case}':")
    print(generated_text_edge)

# Implement Guardrails
def generate_text_with_guardrails(prompt, params, max_tokens=1000):
    if len(prompt) == 0:
        return "No prompt provided."
    if len(prompt) > max_tokens:
        return "Prompt too long."
    generated_text = generate_text_with_params(prompt, params)
    if len(generated_text.split()) > max_tokens:
        return "Generated text too long."
    return generated_text

# Test Guardrails
test_prompts = [
    "",
    "!!!",
    "This prompt has no factual content.",
    long_prompt
]

for test_prompt in test_prompts:
    generated_text_guardrails = generate_text_with_guardrails(test_prompt, hyperparameters[0])
    print(f"\nGenerated Text with Guardrails for Prompt '{test_prompt}':")
    print(generated_text_guardrails)
```

## Verification Checklist & Quick Reference Cheat Sheet

### Essential Python Methods, Parameters, and Verification Flags

| Method/Parameter | Description |
|------------------|-------------|
| `generate_text`  | Generates text based on a given prompt and parameters. |
| `detect_hallucinations` | Detects hallucinations in the generated text by comparing it against known facts. |
| `evaluate_hallucinations` | Evaluates the accuracy of hallucination detection. |
| `generate_text_with_params` | Generates text with specified hyperparameters. |
| `generate_text_with_guardrails` | Generates text with guardrails to handle edge cases and failures. |
| `hyperparameters` | List of hyperparameters to tune the model. |
| `known_facts_df` | Polars DataFrame containing known facts for comparison. |
| `results_df` | Polars DataFrame containing benchmarking results. |

### CLI Commands

- Install required packages:
  ```bash
  pip install torch transformers numpy scikit-learn ollama polars
  ```

- Run the complete lab script:
  ```bash
  python lab_hallucination_detection.py
  ```

This lab provides a comprehensive hands-on experience in implementing, testing, and verifying a hallucination detection system for AI models. By following the exercises, you will gain a deeper understanding of the challenges and solutions in AI safety and alignment.
