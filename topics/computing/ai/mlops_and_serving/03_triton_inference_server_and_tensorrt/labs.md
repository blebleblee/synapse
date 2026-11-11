# Operational Verification Labs: 03 Triton Inference Server And TensorRT

## Objective & Environment Setup

### Objective
The objective of this lab is to gain hands-on experience with deploying and optimizing machine learning models using NVIDIA Triton Inference Server and TensorRT. You will implement a complete pipeline that includes model deployment, hyperparameter tuning, empirical benchmarking, stress testing, and failure mitigation. This lab will equip you with the skills to efficiently serve AI models in production environments.

### Environment Setup
Ensure you have the following environment and tools installed:

- **Python 3.11+**: The lab requires Python 3.11 or later.
- **NVIDIA Triton Inference Server**: Follow the official installation guide to set up Triton Inference Server.
- **TensorRT**: Install TensorRT following the NVIDIA documentation.
- **PyTorch**: Required for model training and conversion.
- **HuggingFace Transformers**: For accessing pre-trained models.
- **NumPy**: For numerical operations.
- **Scikit-learn**: For data preprocessing and evaluation.
- **Docker**: For containerizing the Triton Inference Server.

### Installation Commands
```bash
# Install Python 3.11
sudo apt update
sudo apt install python3.11 python3.11-venv python3.11-dev

# Create a virtual environment
python3.11 -m venv triton-env
source triton-env/bin/activate

# Install required Python packages
pip install torch transformers numpy scikit-learn

# Install Triton Inference Server and TensorRT
# Follow the official NVIDIA documentation for installation:
# https://docs.nvidia.com/deeplearning/triton-inference-server/user-guide/docs/install.html
# https://docs.nvidia.com/deeplearning/tensorrt/install-guide/index.html
```

## Exercise 1: Hands-On Implementation & Pipeline Execution

### Overview
In this exercise, you will implement a complete pipeline to deploy a pre-trained model using Triton Inference Server and TensorRT. The model will be a BERT-based text classification model from HuggingFace.

### Step-by-Step Implementation

1. **Download and Convert the Model**:
   - Download a pre-trained BERT model from HuggingFace.
   - Convert the model to TensorRT format.

2. **Prepare Triton Model Repository**:
   - Create the necessary directory structure for Triton Inference Server.
   - Save the TensorRT model in the appropriate format.

3. **Start Triton Inference Server**:
   - Use Docker to run Triton Inference Server with the model repository.

4. **Create a Client Script**:
   - Write a Python script to send inference requests to Triton Inference Server.

### Complete Python Script

```python
import torch
from transformers import BertTokenizer, BertForSequenceClassification
import tensorrt as trt
import numpy as np
import os
import subprocess

# Step 1: Download and Convert the Model
model_name = "bert-base-uncased"
tokenizer = BertTokenizer.from_pretrained(model_name)
model = BertForSequenceClassification.from_pretrained(model_name)

# Convert the model to ONNX format
dummy_input = torch.tensor([tokenizer.encode("Hello, world!", add_special_tokens=True)])
torch.onnx.export(model, dummy_input, "bert.onnx", opset_version=11, input_names=["input_ids"], output_names=["output"])

# Convert ONNX to TensorRT
TRT_LOGGER = trt.Logger(trt.Logger.WARNING)
with trt.Builder(TRT_LOGGER) as builder, builder.create_network(1 << int(trt.NetworkDefinitionCreationFlag.EXPLICIT_BATCH)) as network, trt.OnnxParser(network, TRT_LOGGER) as parser:
    builder.max_workspace_size = 1 << 30  # 1GB
    builder.max_batch_size = 1
    with open("bert.onnx", "rb") as model:
        if not parser.parse(model.read()):
            for error in range(parser.num_errors):
                print(parser.get_error(error))
            raise RuntimeError("Failed to parse ONNX model")

    engine = builder.build_cuda_engine(network)
    with open("bert.trt", "wb") as f:
        f.write(engine.serialize())

# Step 2: Prepare Triton Model Repository
model_repo = "model_repository"
os.makedirs(os.path.join(model_repo, "bert", "1"), exist_ok=True)
subprocess.run(["cp", "bert.trt", os.path.join(model_repo, "bert", "1", "model.plan")])

# Step 3: Start Triton Inference Server
subprocess.Popen(["tritonserver", "--model-repository", model_repo])

# Step 4: Create a Client Script
import tritonclient.http as httpclient
from tritonclient.utils import np_to_triton_dtype

def infer(input_text):
    client = httpclient.InferenceServerClient(url="localhost:8000")
    input_ids = tokenizer.encode(input_text, add_special_tokens=True)
    input_ids = np.array(input_ids, dtype=np.int32).reshape(1, -1)
    inputs = [httpclient.InferInput("input_ids", input_ids.shape, np_to_triton_dtype(input_ids.dtype))]
    inputs[0].set_data_from_numpy(input_ids)
    outputs = [httpclient.InferRequestedOutput("output")]
    response = client.infer("bert", inputs=inputs, outputs=outputs)
    return response.as_numpy("output")

# Example inference
result = infer("Hello, world!")
print(result)
```

## Exercise 2: Hyperparameter Tuning & Empirical Benchmarking

### Overview
In this exercise, you will perform hyperparameter tuning and empirical benchmarking to measure the accuracy, latency, and throughput of the deployed model.

### Benchmarking Code

```python
import time
import numpy as np
from tritonclient.http import InferenceServerClient, InferInput, InferRequestedOutput

# Initialize Triton client
client = InferenceServerClient(url="localhost:8000")

# Define a function to perform inference
def infer(input_text):
    input_ids = tokenizer.encode(input_text, add_special_tokens=True)
    input_ids = np.array(input_ids, dtype=np.int32).reshape(1, -1)
    inputs = [InferInput("input_ids", input_ids.shape, np_to_triton_dtype(input_ids.dtype))]
    inputs[0].set_data_from_numpy(input_ids)
    outputs = [InferRequestedOutput("output")]
    response = client.infer("bert", inputs=inputs, outputs=outputs)
    return response.as_numpy("output")

# Define a function to benchmark the model
def benchmark_model(num_requests=100):
    latencies = []
    for _ in range(num_requests):
        start_time = time.time()
        infer("Hello, world!")
        end_time = time.time()
        latencies.append(end_time - start_time)
    return latencies

# Perform benchmarking
latencies = benchmark_model()
print(f"Average Latency: {np.mean(latencies)} seconds")
print(f"Throughput: {1 / np.mean(latencies)} requests/second")
```

## Exercise 3: Stress Testing, Edge Cases & Failure Mitigation

### Overview
In this exercise, you will perform stress testing to identify failure modes and implement guardrails to handle edge cases and errors.

### Stress Testing Code

```python
import threading

# Define a function to perform concurrent inference
def concurrent_infer(input_text, results):
    try:
        result = infer(input_text)
        results.append(result)
    except Exception as e:
        results.append(str(e))

# Perform stress testing with multiple threads
num_threads = 10
threads = []
results = []

for _ in range(num_threads):
    thread = threading.Thread(target=concurrent_infer, args=("Hello, world!", results))
    threads.append(thread)
    thread.start()

for thread in threads:
    thread.join()

# Print results
for result in results:
    print(result)
```

### Edge Cases and Failure Mitigation

1. **Invalid Input Handling**:
   - Ensure the model handles invalid inputs gracefully.
   - Implement input validation in the client script.

2. **Error Handling**:
   - Implement try-except blocks to catch and handle exceptions.
   - Log errors for further analysis.

3. **Resource Management**:
   - Monitor GPU and memory usage.
   - Implement resource limits and alerts.

### Example of Input Validation

```python
def validate_input(input_text):
    if not isinstance(input_text, str):
        raise ValueError("Input must be a string")
    if len(input_text) == 0:
        raise ValueError("Input cannot be empty")
    return input_text

# Example usage
try:
    input_text = validate_input("Hello, world!")
    result = infer(input_text)
    print(result)
except ValueError as e:
    print(f"Validation Error: {e}")
```

## Verification Checklist & Quick Reference Cheat Sheet

### Essential Python Methods and Parameters

| Method/Parameter | Description |
|------------------|-------------|
| `tokenizer.encode` | Encodes input text into token IDs. |
| `torch.onnx.export` | Exports a PyTorch model to ONNX format. |
| `trt.Builder` | Builds a TensorRT engine from an ONNX model. |
| `httpclient.InferenceServerClient` | Client for interacting with Triton Inference Server. |
| `InferInput` | Represents an input tensor for inference. |
| `InferRequestedOutput` | Represents an output tensor for inference. |
| `client.infer` | Sends an inference request to the server. |
| `np.mean` | Computes the mean of an array. |
| `threading.Thread` | Creates and manages threads for concurrent execution. |

### Verification Flags

| Flag | Description |
|------|-------------|
| `--model-repository` | Specifies the path to the model repository for Triton Inference Server. |
| `--max_workspace_size` | Sets the maximum workspace size for TensorRT engine. |
| `--max_batch_size` | Sets the maximum batch size for TensorRT engine. |

By completing this lab, you will have a comprehensive understanding of deploying and optimizing machine learning models using Triton Inference Server and TensorRT. This knowledge will be invaluable for serving AI models in production environments.
