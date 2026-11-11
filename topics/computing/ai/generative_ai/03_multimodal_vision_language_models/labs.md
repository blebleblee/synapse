# Operational Verification Labs: 03 Multimodal Vision Language Models

## Objective & Environment Setup

This lab is designed for AI engineers and practitioners seeking to operationalize multimodal vision-language models (VLMs) in real-world applications. The objective is to implement, benchmark, and stress-test a multimodal model pipeline using PyTorch, Hugging Face Transformers, and a suite of evaluation tools. The environment must support Python 3.11 or higher, with GPU acceleration enabled for efficient model inference.

### Prerequisites

Install the following Python packages in a virtual environment:

```bash
pip install torch torchvision torchaudio transformers datasets accelerate
pip install numpy scikit-learn matplotlib seaborn
pip install ollama pillow
```

Ensure that your system has a CUDA-capable GPU with at least 8GB VRAM for optimal performance. If using CPU-only inference, expect significantly slower execution times.

### API Configuration

For this lab, we will interact with Hugging Face's model hub and use the `transformers` library to load pre-trained models. Additionally, we'll use `ollama` for local inference testing if required.

To configure Ollama locally, ensure it's running:

```bash
ollama serve
```

You can verify the service is up by running:

```bash
ollama list
```

This should return a list of available models, including `llama3`, `mistral`, or others.

## Exercise 1: Hands-On Implementation & Pipeline Execution

In this exercise, we implement a minimal but complete multimodal pipeline that accepts an image and text prompt, processes them through a vision-language model, and generates a response. We will use the `Blip2` model from Hugging Face, which is a strong baseline for vision-language tasks.

### Complete Python Script

```python
# lab_vlm_pipeline.py

import torch
from PIL import Image
from transformers import Blip2Processor, Blip2ForConditionalGeneration
from transformers import set_seed

# Initialize model and processor
model_name = "Salesforce/blip2-opt-2.7b"
processor = Blip2Processor.from_pretrained(model_name)
model = Blip2ForConditionalGeneration.from_pretrained(model_name, torch_dtype=torch.float16)
model.to("cuda")

# Set seed for reproducibility
set_seed(42)

# Load an example image
image_path = "sample_image.jpg"
image = Image.open(image_path).convert("RGB")

# Define prompt
prompt = "A detailed description of the image."

# Process inputs
inputs = processor(images=image, text=prompt, return_tensors="pt").to("cuda")

# Generate response
generated_ids = model.generate(**inputs, max_new_tokens=20)
generated_text = processor.batch_decode(generated_ids, skip_special_tokens=True)[0].strip()

print("Generated Text:", generated_text)
```

### Execution Steps

1. Place a sample image named `sample_image.jpg` in the working directory.
2. Run the script:

```bash
python lab_vlm_pipeline.py
```

This script initializes the BLIP-2 model, loads an image, and generates a text response based on the prompt. The output will be printed to the console.

## Exercise 2: Hyperparameter Tuning & Empirical Benchmarking

In this exercise, we evaluate the performance of the VLM pipeline under various hyperparameters and measure key metrics such as accuracy, latency, and token efficiency.

### Benchmarking Script

```python
# benchmark_vlm.py

import time
import torch
from PIL import Image
from transformers import Blip2Processor, Blip2ForConditionalGeneration
from datasets import load_dataset
import numpy as np

# Load dataset
dataset = load_dataset("coco", split="train[:100]")  # Sample 100 images for benchmarking

# Initialize model and processor
model_name = "Salesforce/blip2-opt-2.7b"
processor = Blip2Processor.from_pretrained(model_name)
model = Blip2ForConditionalGeneration.from_pretrained(model_name, torch_dtype=torch.float16)
model.to("cuda")

# Benchmark parameters
max_new_tokens_list = [10, 20, 50]
latency_results = []
accuracy_results = []

# Function to measure latency
def measure_latency(prompt, image):
    inputs = processor(images=image, text=prompt, return_tensors="pt").to("cuda")
    start_time = time.time()
    generated_ids = model.generate(**inputs, max_new_tokens=20)
    end_time = time.time()
    return end_time - start_time

# Benchmark loop
for max_tokens in max_new_tokens_list:
    latencies = []
    for i, example in enumerate(dataset):
        image = Image.open(example["image"]).convert("RGB")
        prompt = "Describe this image."
        latency = measure_latency(prompt, image)
        latencies.append(latency)
        if i >= 9:  # Limit to first 10 samples
            break
    avg_latency = np.mean(latencies)
    latency_results.append((max_tokens, avg_latency))
    print(f"Max New Tokens: {max_tokens}, Average Latency: {avg_latency:.4f}s")

# Print results
print("\nLatency Results:")
for tokens, latency in latency_results:
    print(f"  {tokens} tokens: {latency:.4f}s")
```

### Execution Steps

1. Ensure the `sample_image.jpg` file exists in the working directory.
2. Run the benchmark script:

```bash
python benchmark_vlm.py
```

This script evaluates the model's latency across different `max_new_tokens` values and prints the average latency for each setting.

## Exercise 3: Stress Testing, Edge Cases & Failure Mitigation

In this exercise, we simulate failure scenarios and edge cases to ensure robustness in the VLM pipeline. We test for invalid inputs, memory constraints, and error handling.

### Stress Testing Script

```python
# stress_test_vlm.py

import torch
from PIL import Image
from transformers import Blip2Processor, Blip2ForConditionalGeneration
import traceback

# Initialize model and processor
model_name = "Salesforce/blip2-opt-2.7b"
processor = Blip2Processor.from_pretrained(model_name)
model = Blip2ForConditionalGeneration.from_pretrained(model_name, torch_dtype=torch.float16)
model.to("cuda")

# Test cases
test_cases = [
    {"name": "Valid Input", "image": "sample_image.jpg", "prompt": "Describe this image."},
    {"name": "Empty Prompt", "image": "sample_image.jpg", "prompt": ""},
    {"name": "Very Long Prompt", "image": "sample_image.jpg", "prompt": "A" * 1000},
    {"name": "Invalid Image Path", "image": "nonexistent.jpg", "prompt": "Describe this image."},
]

# Function to test each case
def test_case(name, image_path, prompt):
    try:
        image = Image.open(image_path).convert("RGB")
        inputs = processor(images=image, text=prompt, return_tensors="pt").to("cuda")
        generated_ids = model.generate(**inputs, max_new_tokens=20)
        generated_text = processor.batch_decode(generated_ids, skip_special_tokens=True)[0].strip()
        print(f"[PASS] {name}: {generated_text}")
    except Exception as e:
        print(f"[FAIL] {name}: {str(e)}")
        traceback.print_exc()

# Run tests
for case in test_cases:
    test_case(case["name"], case["image"], case["prompt"])
```

### Execution Steps

1. Ensure the `sample_image.jpg` file exists in the working directory.
2. Run the stress test script:

```bash
python stress_test_vlm.py
```

This script tests various edge cases including empty prompts, very long prompts, and invalid image paths, ensuring that the pipeline handles errors gracefully.

## Verification Checklist & Quick Reference Cheat Sheet

| Component | Method/Parameter | Description |
|-----------|------------------|-------------|
| Model Loading | `Blip2ForConditionalGeneration.from_pretrained()` | Loads the pre-trained model |
| Processor Initialization | `Blip2Processor.from_pretrained()` | Initializes the processor for input handling |
| Input Processing | `processor(images=image, text=prompt, return_tensors="pt")` | Encodes image and text for model input |
| Inference | `model.generate(**inputs, max_new_tokens=N)` | Generates text from image and prompt |
| Device Placement | `.to("cuda")` | Moves model to GPU for faster inference |
| Latency Measurement | `time.time()` | Measures execution time for performance analysis |
| Error Handling | `try-except` blocks | Catches and logs exceptions during processing |
| Dataset Loading | `load_dataset("coco")` | Loads COCO dataset for benchmarking |
| Token Efficiency | `max_new_tokens` | Controls the length of generated text |
| Reproducibility | `set_seed(42)` | Ensures consistent results across runs |

This lab provides a comprehensive framework for understanding and operationalizing multimodal vision-language models. By following these exercises, practitioners can build, test, and deploy robust VLM pipelines with confidence in their performance and reliability.
