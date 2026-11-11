# Operational Verification Labs: 03 Multi Agent Orchestration And Delegation

## Objective & Environment Setup

### Objective
The objective of this lab is to gain hands-on experience with multi-agent orchestration and delegation in the context of AI and AI agents. You will implement a system where multiple AI agents collaborate to solve a complex problem, perform hyperparameter tuning, conduct empirical benchmarking, and implement stress testing and failure mitigation strategies.

### Environment Setup
Ensure you have a Python 3.11+ environment set up. Install the necessary packages using pip:

```bash
pip install torch transformers numpy scikit-learn polars
```

Additionally, configure any required API keys or tokens for services like HuggingFace or Ollama. For this lab, we will use the HuggingFace Transformers library to load pre-trained models.

## Exercise 1: Hands-On Implementation & Pipeline Execution

### Core Prompt/Model/Algorithm Implementation

In this exercise, we will implement a multi-agent system where each agent is responsible for a different task in a collaborative pipeline. For simplicity, let's assume we have a text generation task that can be broken down into three sub-tasks: text preprocessing, text generation, and text post-processing.

#### Step-by-Step Implementation

1. **Text Preprocessing Agent:**
   - Tokenizes the input text.
   - Cleans the text by removing unwanted characters.

2. **Text Generation Agent:**
   - Uses a pre-trained language model to generate text based on the preprocessed input.

3. **Text Post-processing Agent:**
   - Formats the generated text.
   - Ensures the text meets certain quality criteria.

Below is a complete, runnable Python script implementing the above pipeline:

```python
import torch
from transformers import GPT2Tokenizer, GPT2LMHeadModel
import numpy as np

class TextPreprocessingAgent:
    def __init__(self, tokenizer):
        self.tokenizer = tokenizer

    def preprocess(self, text):
        # Tokenize and clean the text
        cleaned_text = text.strip().replace('\n', ' ')
        tokenized_text = self.tokenizer(cleaned_text, return_tensors='pt')
        return tokenized_text

class TextGenerationAgent:
    def __init__(self, model):
        self.model = model

    def generate(self, input_ids, max_length=50):
        # Generate text using the model
        output = self.model.generate(input_ids, max_length=max_length, num_return_sequences=1)
        return output

class TextPostprocessingAgent:
    def postprocess(self, generated_ids, tokenizer):
        # Decode and format the generated text
        generated_text = tokenizer.decode(generated_ids[0], skip_special_tokens=True)
        formatted_text = generated_text.strip()
        return formatted_text

def main():
    # Initialize tokenizer and model
    tokenizer = GPT2Tokenizer.from_pretrained('gpt2')
    model = GPT2LMHeadModel.from_pretrained('gpt2')

    # Create agents
    preprocessing_agent = TextPreprocessingAgent(tokenizer)
    generation_agent = TextGenerationAgent(model)
    postprocessing_agent = TextPostprocessingAgent()

    # Input text
    input_text = "Once upon a time"

    # Preprocess the text
    preprocessed_text = preprocessing_agent.preprocess(input_text)

    # Generate text
    generated_ids = generation_agent.generate(preprocessed_text['input_ids'])

    # Postprocess the generated text
    final_text = postprocessing_agent.postprocess(generated_ids, tokenizer)

    print("Generated Text:", final_text)

if __name__ == "__main__":
    main()
```

## Exercise 2: Hyperparameter Tuning & Empirical Benchmarking

### Benchmarking Code

In this exercise, we will perform hyperparameter tuning and empirical benchmarking to measure the accuracy, latency, and token costs of the text generation process.

#### Step-by-Step Benchmarking

1. **Hyperparameter Tuning:**
   - Vary the `max_length` parameter in the `generate` method.
   - Measure the impact on the quality and length of the generated text.

2. **Empirical Benchmarking:**
   - Measure the latency of the text generation process.
   - Measure the token usage and associated costs.

Below is a complete, runnable Python script implementing the above benchmarking:

```python
import time
import torch
from transformers import GPT2Tokenizer, GPT2LMHeadModel
import numpy as np

def benchmark(max_length):
    # Initialize tokenizer and model
    tokenizer = GPT2Tokenizer.from_pretrained('gpt2')
    model = GPT2LMHeadModel.from_pretrained('gpt2')

    # Create agents
    preprocessing_agent = TextPreprocessingAgent(tokenizer)
    generation_agent = TextGenerationAgent(model)
    postprocessing_agent = TextPostprocessingAgent()

    # Input text
    input_text = "Once upon a time"

    # Preprocess the text
    preprocessed_text = preprocessing_agent.preprocess(input_text)

    # Measure latency
    start_time = time.time()
    generated_ids = generation_agent.generate(preprocessed_text['input_ids'], max_length=max_length)
    end_time = time.time()

    # Postprocess the generated text
    final_text = postprocessing_agent.postprocess(generated_ids, tokenizer)

    # Calculate latency and token usage
    latency = end_time - start_time
    token_usage = len(generated_ids[0])

    return latency, token_usage, final_text

def main():
    max_lengths = [30, 50, 70, 90, 110]
    results = []

    for max_length in max_lengths:
        latency, token_usage, final_text = benchmark(max_length)
        results.append((max_length, latency, token_usage, final_text))
        print(f"Max Length: {max_length}, Latency: {latency:.4f}s, Token Usage: {token_usage}, Generated Text: {final_text}")

if __name__ == "__main__":
    main()
```

## Exercise 3: Stress Testing, Edge Cases & Failure Mitigation

### Stress Testing and Edge Cases

In this exercise, we will perform stress testing and handle edge cases to ensure the robustness of the multi-agent system.

#### Step-by-Step Stress Testing

1. **Stress Testing:**
   - Generate text with very large `max_length` values.
   - Measure the system's response and resource usage.

2. **Edge Cases:**
   - Handle empty input text.
   - Handle input text with special characters or non-ASCII characters.

Below is a complete, runnable Python script implementing the above stress testing and edge case handling:

```python
import time
import torch
from transformers import GPT2Tokenizer, GPT2LMHeadModel
import numpy as np

def stress_test(max_length):
    # Initialize tokenizer and model
    tokenizer = GPT2Tokenizer.from_pretrained('gpt2')
    model = GPT2LMHeadModel.from_pretrained('gpt2')

    # Create agents
    preprocessing_agent = TextPreprocessingAgent(tokenizer)
    generation_agent = TextGenerationAgent(model)
    postprocessing_agent = TextPostprocessingAgent()

    # Input text
    input_text = "Once upon a time" * 100  # Large input text

    # Preprocess the text
    preprocessed_text = preprocessing_agent.preprocess(input_text)

    # Measure latency
    start_time = time.time()
    generated_ids = generation_agent.generate(preprocessed_text['input_ids'], max_length=max_length)
    end_time = time.time()

    # Postprocess the generated text
    final_text = postprocessing_agent.postprocess(generated_ids, tokenizer)

    # Calculate latency and token usage
    latency = end_time - start_time
    token_usage = len(generated_ids[0])

    return latency, token_usage, final_text

def edge_case_handling():
    # Initialize tokenizer and model
    tokenizer = GPT2Tokenizer.from_pretrained('gpt2')
    model = GPT2LMHeadModel.from_pretrained('gpt2')

    # Create agents
    preprocessing_agent = TextPreprocessingAgent(tokenizer)
    generation_agent = TextGenerationAgent(model)
    postprocessing_agent = TextPostprocessingAgent()

    # Edge case 1: Empty input text
    input_text_empty = ""
    preprocessed_text_empty = preprocessing_agent.preprocess(input_text_empty)
    generated_ids_empty = generation_agent.generate(preprocessed_text_empty['input_ids'], max_length=50)
    final_text_empty = postprocessing_agent.postprocess(generated_ids_empty, tokenizer)
    print(f"Edge Case 1 (Empty Input): Generated Text: {final_text_empty}")

    # Edge case 2: Input text with special characters
    input_text_special = "Once upon a time! @#%&*()"
    preprocessed_text_special = preprocessing_agent.preprocess(input_text_special)
    generated_ids_special = generation_agent.generate(preprocessed_text_special['input_ids'], max_length=50)
    final_text_special = postprocessing_agent.postprocess(generated_ids_special, tokenizer)
    print(f"Edge Case 2 (Special Characters): Generated Text: {final_text_special}")

def main():
    # Stress test with large max_length
    max_length_stress = 1000
    latency, token_usage, final_text = stress_test(max_length_stress)
    print(f"Stress Test (Max Length: {max_length_stress}): Latency: {latency:.4f}s, Token Usage: {token_usage}, Generated Text: {final_text}")

    # Edge case handling
    edge_case_handling()

if __name__ == "__main__":
    main()
```

## Verification Checklist & Quick Reference Cheat Sheet

### Essential Python Methods and Parameters

| Method/Parameter | Description |
|------------------|-------------|
| `preprocess`     | Preprocesses the input text by tokenizing and cleaning it. |
| `generate`       | Generates text using the pre-trained model with specified `max_length`. |
| `postprocess`    | Postprocesses the generated text by decoding and formatting it. |
| `max_length`     | Maximum length of the generated text. |
| `latency`        | Time taken to generate the text. |
| `token_usage`    | Number of tokens used in the generated text. |
| `input_text`     | Input text provided to the system. |
| `final_text`     | Final generated and post-processed text. |

### Verification Flags

| Flag           | Description |
|----------------|-------------|
| `--max_length` | Specifies the maximum length of the generated text. |
| `--stress_test`| Runs stress testing with a large `max_length`. |
| `--edge_cases` | Handles edge cases with empty and special character inputs. |

This lab provides a comprehensive hands-on experience with multi-agent orchestration and delegation in AI systems. By implementing, benchmarking, and testing the system, you will gain a deeper understanding of how to build robust and efficient multi-agent architectures.
