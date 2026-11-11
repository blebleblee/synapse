# Operational Verification Labs: Core

## Objective & Environment Setup

### Objective
The primary objective of this lab is to provide hands-on experience with implementing, tuning, and verifying a core AI/Generative Model (Gemini) and multimodal APIs. This lab will guide you through the process of setting up a robust environment, implementing a core model, performing hyperparameter tuning, conducting empirical benchmarking, and stress testing the system to ensure reliability and performance.

### Environment Setup
Ensure you have a Python 3.11+ environment with the following packages installed. You can set up a virtual environment and install the necessary packages using the following commands:

```bash
# Create a virtual environment
python3.11 -m venv ai_gemini_env

# Activate the virtual environment
source ai_gemini_env/bin/activate

# Install required packages
pip install torch transformers numpy scikit-learn ollama polars
```

Additionally, you will need to configure API keys and endpoints for any external services you plan to use. For this lab, we will assume you have access to a Gemini API endpoint. Ensure you have your API key ready and stored securely.

## Exercise 1: Hands-On Implementation & Pipeline Execution

In this exercise, we will implement a core prompt/model/algorithm using the HuggingFace Transformers library. We will use a pre-trained model and fine-tune it on a custom dataset.

### Step-by-Step Implementation

1. **Import Required Libraries**

    ```python
    import torch
    from transformers import GPT2LMHeadModel, GPT2Tokenizer, Trainer, TrainingArguments
    from datasets import load_dataset
    import numpy as np
    ```

2. **Load and Preprocess Dataset**

    For this example, we will use the HuggingFace `datasets` library to load a sample dataset. You can replace this with your custom dataset.

    ```python
    # Load dataset
    dataset = load_dataset('wikitext', 'wikitext-2-raw-v1')

    # Tokenize dataset
    tokenizer = GPT2Tokenizer.from_pretrained('gpt2')

    def tokenize_function(examples):
        return tokenizer(examples['text'], padding='max_length', truncation=True)

    tokenized_datasets = dataset.map(tokenize_function, batched=True)
    ```

3. **Load Pre-trained Model**

    ```python
    model = GPT2LMHeadModel.from_pretrained('gpt2')
    ```

4. **Define Training Arguments**

    ```python
    training_args = TrainingArguments(
        output_dir='./results',
        evaluation_strategy='epoch',
        learning_rate=2e-5,
        per_device_train_batch_size=4,
        per_device_eval_batch_size=4,
        num_train_epochs=3,
        weight_decay=0.01,
    )
    ```

5. **Define Trainer**

    ```python
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized_datasets['train'],
        eval_dataset=tokenized_datasets['validation'],
    )
    ```

6. **Train Model**

    ```python
    trainer.train()
    ```

7. **Save Model**

    ```python
    model.save_pretrained('./fine_tuned_gpt2')
    tokenizer.save_pretrained('./fine_tuned_gpt2')
    ```

## Exercise 2: Hyperparameter Tuning & Empirical Benchmarking

In this exercise, we will perform hyperparameter tuning and benchmark the model's performance in terms of accuracy, latency, and token costs.

### Step-by-Step Benchmarking

1. **Hyperparameter Tuning**

    We will use `scikit-learn` to perform grid search for hyperparameter tuning.

    ```python
    from sklearn.model_selection import GridSearchCV
    from sklearn.metrics import make_scorer, accuracy_score

    # Define a simple scorer for demonstration
    def simple_scorer(y_true, y_pred):
        return accuracy_score(y_true, y_pred)

    scorer = make_scorer(simple_scorer)

    # Define parameter grid
    param_grid = {
        'learning_rate': [2e-5, 3e-5, 5e-5],
        'per_device_train_batch_size': [4, 8],
        'num_train_epochs': [2, 3],
    }

    # Perform grid search
    grid_search = GridSearchCV(estimator=trainer, param_grid=param_grid, scoring=scorer, cv=2)
    grid_search.fit(tokenized_datasets['train'])
    ```

2. **Benchmarking**

    We will measure the model's accuracy, latency, and token costs.

    ```python
    import time
    import torch

    # Load fine-tuned model
    model = GPT2LMHeadModel.from_pretrained('./fine_tuned_gpt2')
    tokenizer = GPT2Tokenizer.from_pretrained('./fine_tuned_gpt2')

    # Define a sample input
    input_text = "Once upon a time"
    inputs = tokenizer(input_text, return_tensors='pt')

    # Measure latency
    start_time = time.time()
    outputs = model.generate(**inputs)
    end_time = time.time()
    latency = end_time - start_time

    # Measure token cost
    token_cost = len(outputs[0])

    # Print results
    print(f"Latency: {latency} seconds")
    print(f"Token Cost: {token_cost} tokens")
    ```

## Exercise 3: Stress Testing, Edge Cases & Failure Mitigation

In this exercise, we will test the model under stress conditions, handle edge cases, and implement guardrails to ensure robustness.

### Step-by-Step Stress Testing

1. **Stress Testing**

    We will simulate high-load conditions by generating predictions for a large number of inputs.

    ```python
    import random

    # Generate random inputs
    random_inputs = [" ".join(random.choices(tokenizer.get_vocab().keys(), k=10)) for _ in range(100)]

    # Measure latency and token cost for each input
    for input_text in random_inputs:
        inputs = tokenizer(input_text, return_tensors='pt')
        start_time = time.time()
        outputs = model.generate(**inputs)
        end_time = time.time()
        latency = end_time - start_time
        token_cost = len(outputs[0])
        print(f"Input: {input_text}")
        print(f"Latency: {latency} seconds")
        print(f"Token Cost: {token_cost} tokens")
    ```

2. **Edge Cases**

    We will test the model with edge cases such as empty strings and very long inputs.

    ```python
    # Test with empty string
    empty_input = ""
    inputs = tokenizer(empty_input, return_tensors='pt')
    outputs = model.generate(**inputs)
    print(f"Output for empty input: {tokenizer.decode(outputs[0])}")

    # Test with very long input
    long_input = " ".join(random.choices(tokenizer.get_vocab().keys(), k=1000))
    inputs = tokenizer(long_input, return_tensors='pt')
    outputs = model.generate(**inputs)
    print(f"Output for long input: {tokenizer.decode(outputs[0])}")
    ```

3. **Failure Mitigation**

    We will implement guardrails to handle potential failures such as timeouts and memory errors.

    ```python
    import signal

    # Define timeout handler
    def timeout_handler(signum, frame):
        raise TimeoutError("Timeout occurred")

    # Set timeout
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(5)  # Set timeout to 5 seconds

    try:
        # Generate prediction with timeout
        outputs = model.generate(**inputs)
        print(f"Output: {tokenizer.decode(outputs[0])}")
    except TimeoutError as e:
        print(e)
    finally:
        signal.alarm(0)  # Disable timeout
    ```

## Verification Checklist & Quick Reference Cheat Sheet

### Essential Python Methods and Parameters

| Method/Parameter | Description |
|------------------|-------------|
| `load_dataset`   | Loads a dataset from the HuggingFace datasets library. |
| `GPT2Tokenizer`  | Tokenizer for GPT-2 model. |
| `GPT2LMHeadModel`| Pre-trained GPT-2 language model. |
| `Trainer`        | Trainer class for training and evaluating models. |
| `TrainingArguments` | Configuration for training arguments. |
| `GridSearchCV`   | Grid search for hyperparameter tuning. |
| `make_scorer`    | Creates a scorer for evaluation. |
| `accuracy_score` | Computes accuracy score. |
| `generate`       | Generates text from the model. |
| `decode`         | Decodes tokenized output to human-readable text. |
| `signal.alarm`   | Sets a timeout for a block of code. |

### Verification Flags

| Flag/Parameter | Description |
|----------------|-------------|
| `evaluation_strategy` | Strategy for evaluation during training. |
| `learning_rate` | Learning rate for the optimizer. |
| `per_device_train_batch_size` | Batch size for training. |
| `per_device_eval_batch_size` | Batch size for evaluation. |
| `num_train_epochs` | Number of training epochs. |
| `weight_decay` | Weight decay for optimizer. |

This lab provides a comprehensive hands-on experience with implementing, tuning, and verifying a core AI/Generative Model and multimodal APIs. By following the steps outlined in this guide, you will gain practical skills in AI engineering and model deployment.
