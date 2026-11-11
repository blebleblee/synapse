# Operational Verification Labs: Core

## Objective & Environment Setup

The objective of this lab is to provide hands-on experience with implementing, tuning, and verifying a core AI/ML pipeline. We will use a state-of-the-art language model from Hugging Face, and perform hyperparameter tuning, empirical benchmarking, and stress testing to ensure robustness and reliability. The lab assumes a Python 3.11+ environment with the following packages installed:

- PyTorch
- Hugging Face Transformers
- NumPy
- Scikit-learn
- Polars

To set up the environment, you can use the following commands:

```bash
# Create a virtual environment
python3.11 -m venv ai-lab-env

# Activate the virtual environment
source ai-lab-env/bin/activate

# Install required packages
pip install torch transformers numpy scikit-learn polars
```

## Exercise 1: Hands-On Implementation & Pipeline Execution

In this exercise, we will implement a pipeline that loads a pre-trained language model from Hugging Face, processes input text, and generates a response. The complete, runnable Python script is provided below:

```python
# Import necessary libraries
from transformers import pipeline

# Load a pre-trained language model
generator = pipeline('text-generation', model='gpt2')

# Define a function to generate text
def generate_text(prompt, max_length=50):
    """
    Generate text based on the given prompt using the pre-trained model.
    
    Args:
        prompt (str): The input text prompt.
        max_length (int): The maximum length of the generated text.
        
    Returns:
        str: The generated text.
    """
    result = generator(prompt, max_length=max_length, num_return_sequences=1)
    return result[0]['generated_text']

# Example usage
if __name__ == "__main__":
    prompt = "Once upon a time"
    generated_text = generate_text(prompt)
    print(f"Generated Text: {generated_text}")
```

## Exercise 2: Hyperparameter Tuning & Empirical Benchmarking

In this exercise, we will perform hyperparameter tuning and empirical benchmarking to measure the accuracy, latency, and token costs of the language model. We will use the `time` module to measure latency and `numpy` to compute statistics.

```python
# Import necessary libraries
import time
import numpy as np
from transformers import pipeline

# Load a pre-trained language model
generator = pipeline('text-generation', model='gpt2')

# Define a function to generate text and measure latency
def generate_text_with_latency(prompt, max_length=50, num_sequences=1):
    """
    Generate text based on the given prompt and measure the latency.
    
    Args:
        prompt (str): The input text prompt.
        max_length (int): The maximum length of the generated text.
        num_sequences (int): The number of sequences to generate.
        
    Returns:
        tuple: A tuple containing the generated text and the latency in seconds.
    """
    start_time = time.time()
    result = generator(prompt, max_length=max_length, num_return_sequences=num_sequences)
    end_time = time.time()
    latency = end_time - start_time
    return result, latency

# Define a function to benchmark the model
def benchmark_model(prompts, max_length=50, num_sequences=1, num_trials=10):
    """
    Benchmark the language model by generating text for multiple prompts and measuring latency.
    
    Args:
        prompts (list): A list of input text prompts.
        max_length (int): The maximum length of the generated text.
        num_sequences (int): The number of sequences to generate.
        num_trials (int): The number of trials to perform for each prompt.
        
    Returns:
        dict: A dictionary containing the average latency and standard deviation for each prompt.
    """
    results = {}
    for prompt in prompts:
        latencies = []
        for _ in range(num_trials):
            _, latency = generate_text_with_latency(prompt, max_length=max_length, num_sequences=num_sequences)
            latencies.append(latency)
        avg_latency = np.mean(latencies)
        std_latency = np.std(latencies)
        results[prompt] = {'avg_latency': avg_latency, 'std_latency': std_latency}
    return results

# Example usage
if __name__ == "__main__":
    prompts = ["Once upon a time", "In a galaxy far, far away", "The quick brown fox"]
    benchmark_results = benchmark_model(prompts)
    for prompt, result in benchmark_results.items():
        print(f"Prompt: {prompt}")
        print(f"Average Latency: {result['avg_latency']:.4f} seconds")
        print(f"Standard Deviation: {result['std_latency']:.4f} seconds")
        print()
```

## Exercise 3: Stress Testing, Edge Cases & Failure Mitigation

In this exercise, we will perform stress testing, reproduce failure modes, and implement guardrails or error handling to ensure the robustness of the pipeline. We will test edge cases such as very long prompts and invalid inputs.

```python
# Import necessary libraries
from transformers import pipeline

# Load a pre-trained language model
generator = pipeline('text-generation', model='gpt2')

# Define a function to generate text with error handling
def generate_text_with_error_handling(prompt, max_length=50):
    """
    Generate text based on the given prompt with error handling.
    
    Args:
        prompt (str): The input text prompt.
        max_length (int): The maximum length of the generated text.
        
    Returns:
        str: The generated text or an error message.
    """
    try:
        result = generator(prompt, max_length=max_length, num_return_sequences=1)
        return result[0]['generated_text']
    except Exception as e:
        return f"Error: {str(e)}"

# Define a function to perform stress testing
def stress_test_model(prompts, max_length=50):
    """
    Perform stress testing on the language model by generating text for multiple prompts.
    
    Args:
        prompts (list): A list of input text prompts.
        max_length (int): The maximum length of the generated text.
        
    Returns:
        dict: A dictionary containing the generated text or error message for each prompt.
    """
    results = {}
    for prompt in prompts:
        result = generate_text_with_error_handling(prompt, max_length=max_length)
        results[prompt] = result
    return results

# Example usage
if __name__ == "__main__":
    # Test with normal prompts
    normal_prompts = ["Once upon a time", "In a galaxy far, far away", "The quick brown fox"]
    normal_results = stress_test_model(normal_prompts)
    for prompt, result in normal_results.items():
        print(f"Prompt: {prompt}")
        print(f"Result: {result}")
        print()

    # Test with very long prompts
    long_prompt = "A" * 10000
    long_results = stress_test_model([long_prompt])
    for prompt, result in long_results.items():
        print(f"Prompt: {prompt[:50]}... (length: {len(prompt)})"
        print(f"Result: {result}")
        print()

    # Test with invalid inputs
    invalid_prompts = [None, 12345, ""]
    invalid_results = stress_test_model(invalid_prompts)
    for prompt, result in invalid_results.items():
        print(f"Prompt: {prompt}")
        print(f"Result: {result}")
        print()
```

## Verification Checklist & Quick Reference Cheat Sheet

Below is a table of essential Python methods, parameters, and verification flags for this topic:

| Method/Parameter | Description |
|------------------|-------------|
| `pipeline('text-generation', model='gpt2')` | Loads a pre-trained language model for text generation. |
| `generate_text(prompt, max_length=50)` | Generates text based on the given prompt with a specified maximum length. |
| `generate_text_with_latency(prompt, max_length=50, num_sequences=1)` | Generates text and measures the latency. |
| `benchmark_model(prompts, max_length=50, num_sequences=1, num_trials=10)` | Benchmarks the model by generating text for multiple prompts and measuring latency. |
| `generate_text_with_error_handling(prompt, max_length=50)` | Generates text with error handling for robustness. |
| `stress_test_model(prompts, max_length=50)` | Performs stress testing on the model by generating text for multiple prompts. |
| `time.time()` | Measures the current time in seconds since the epoch. |
| `np.mean(latencies)` | Computes the mean of the latency values. |
| `np.std(latencies)` | Computes the standard deviation of the latency values. |

This lab provides a comprehensive hands-on experience with implementing, tuning, and verifying a core AI/ML pipeline. By following the exercises, you will gain practical skills in using pre-trained models, performing hyperparameter tuning, benchmarking, and ensuring robustness through stress testing and error handling.
