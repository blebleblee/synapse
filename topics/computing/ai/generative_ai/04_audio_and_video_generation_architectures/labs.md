# Operational Verification Labs: 04 Audio And Video Generation Architectures

## Objective & Environment Setup

In this lab, we explore the operational verification of audio and video generation architectures using generative AI models. The goal is to implement, benchmark, and stress-test real-world generative pipelines that produce audio and video outputs from textual prompts or other inputs. This lab assumes a working Python 3.11+ environment with access to GPU acceleration (CUDA) for efficient model inference.

We will use the following core libraries:
- **PyTorch** for deep learning model execution
- **Hugging Face Transformers** for model loading and inference
- **Diffusers** for diffusion-based generation models
- **SoundFile / Librosa** for audio processing
- **OpenCV / Pillow** for video generation and manipulation
- **TorchAudio** for audio-specific operations
- **Ollama** for local LLM integration (optional)
- **Polars** for data processing and benchmarking

### Environment Setup

To begin, create a virtual environment and install the required packages:

```bash
python -m venv genai-lab
source genai-lab/bin/activate
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
pip install transformers diffusers accelerate soundfile librosa opencv-python pillow torch-audio
pip install ollama polars
```

Ensure that your system has access to a CUDA-capable GPU with at least 8GB VRAM for optimal performance during model inference.

## Exercise 1: Hands-On Implementation & Pipeline Execution

In this exercise, we implement a complete pipeline for generating audio and video from text prompts using a diffusion-based model architecture. The pipeline includes prompt encoding, latent space generation, and output decoding.

### Audio Generation Pipeline

We will use the `audioldm` model from Hugging Face to generate audio from text prompts. This model leverages a latent diffusion framework to map textual descriptions into audio waveforms.

```python
# audio_generation_pipeline.py

import torch
from diffusers import AudioLDMPipeline
from transformers import CLIPTokenizer, CLIPTextModel
import soundfile as sf
import numpy as np

# Initialize the pipeline
model_id = "cvssp/audioldm-s-full-v2"
pipe = AudioLDMPipeline.from_pretrained(model_id, torch_dtype=torch.float16)
pipe = pipe.to("cuda")

# Define a sample prompt
prompt = "A serene forest with birds chirping and gentle wind rustling through leaves"

# Generate audio
audio = pipe(prompt, num_inference_steps=25, audio_length_in_s=10).audios[0]

# Save the generated audio
sf.write("generated_audio.wav", audio, samplerate=16000)
print("Audio generated and saved as 'generated_audio.wav'")
```

### Video Generation Pipeline

For video generation, we use the `stable-video-diffusion` model, which generates short videos from text prompts using a latent diffusion approach.

```python
# video_generation_pipeline.py

import torch
from diffusers import StableVideoDiffusionPipeline
from diffusers.utils import load_image
from PIL import Image
import numpy as np
import os

# Initialize the pipeline
model_id = "stabilityai/stable-video-diffusion-img2vid-xt"
pipe = StableVideoDiffusionPipeline.from_pretrained(
    model_id,
    torch_dtype=torch.float16,
    variant="fp16"
)
pipe = pipe.to("cuda")

# Define a sample image and prompt
image_path = "sample_image.jpg"
prompt = "A cinematic shot of a futuristic cityscape at sunset, with flying vehicles and neon lights"

# Load and preprocess the image
image = load_image(image_path)
image = image.resize((1024, 576))

# Generate video
frames = pipe(
    image,
    prompt=prompt,
    num_inference_steps=25,
    decode_chunk_size=8,
    motion_bucket_id=127,
    fps=7,
    augmentation_factor=0
).frames[0]

# Save the video frames
output_dir = "generated_video_frames"
os.makedirs(output_dir, exist_ok=True)
for i, frame in enumerate(frames):
    frame.save(os.path.join(output_dir, f"frame_{i:03d}.png"))
print("Video frames generated and saved to 'generated_video_frames/'")
```

### Execution Command

Run the audio generation pipeline:

```bash
python audio_generation_pipeline.py
```

Run the video generation pipeline:

```bash
python video_generation_pipeline.py
```

## Exercise 2: Hyperparameter Tuning & Empirical Benchmarking

In this exercise, we benchmark the performance of the audio and video generation pipelines under varying hyperparameters. We measure latency, quality, and resource utilization.

### Audio Generation Benchmarking

```python
# audio_benchmark.py

import time
import torch
from diffusers import AudioLDMPipeline
import soundfile as sf
import pandas as pd

model_id = "cvssp/audioldm-s-full-v2"
pipe = AudioLDMPipeline.from_pretrained(model_id, torch_dtype=torch.float16)
pipe = pipe.to("cuda")

prompts = [
    "A gentle breeze through a meadow",
    "A thunderstorm at night",
    "A child laughing in a playground"
]

results = []

for prompt in prompts:
    start_time = time.time()
    audio = pipe(prompt, num_inference_steps=25, audio_length_in_s=10).audios[0]
    end_time = time.time()
    
    latency = end_time - start_time
    results.append({
        "prompt": prompt,
        "latency_seconds": latency,
        "audio_length_seconds": 10
    })

df = pd.DataFrame(results)
print(df)
df.to_csv("audio_benchmark_results.csv", index=False)
```

### Video Generation Benchmarking

```python
# video_benchmark.py

import time
import torch
from diffusers import StableVideoDiffusionPipeline
from diffusers.utils import load_image
import pandas as pd
import os

model_id = "stabilityai/stable-video-diffusion-img2vid-xt"
pipe = StableVideoDiffusionPipeline.from_pretrained(
    model_id,
    torch_dtype=torch.float16,
    variant="fp16"
)
pipe = pipe.to("cuda")

image_path = "sample_image.jpg"
image = load_image(image_path)
image = image.resize((1024, 576))

prompts = [
    "A serene forest with birds chirping",
    "A bustling city street at night",
    "A calm ocean with waves gently crashing"
]

results = []

for prompt in prompts:
    start_time = time.time()
    frames = pipe(
        image,
        prompt=prompt,
        num_inference_steps=25,
        decode_chunk_size=8,
        motion_bucket_id=127,
        fps=7,
        augmentation_factor=0
    ).frames[0]
    end_time = time.time()
    
    latency = end_time - start_time
    results.append({
        "prompt": prompt,
        "latency_seconds": latency,
        "frame_count": len(frames)
    })

df = pd.DataFrame(results)
print(df)
df.to_csv("video_benchmark_results.csv", index=False)
```

### Execution Command

Run the audio benchmark:

```bash
python audio_benchmark.py
```

Run the video benchmark:

```bash
python video_benchmark.py
```

## Exercise 3: Stress Testing, Edge Cases & Failure Mitigation

In this exercise, we test the robustness of the pipelines by introducing edge cases and failure scenarios. We implement error handling and guardrails to ensure graceful degradation.

### Audio Generation with Error Handling

```python
# audio_stress_test.py

import torch
from diffusers import AudioLDMPipeline
import soundfile as sf
import traceback

model_id = "cvssp/audioldm-s-full-v2"
pipe = AudioLDMPipeline.from_pretrained(model_id, torch_dtype=torch.float16)
pipe = pipe.to("cuda")

# Test cases including edge cases
test_cases = [
    "A very long prompt that exceeds typical token limits",
    "A prompt with special characters: !@#$%^&*()",
    "A prompt with no meaningful content: 'xyz abc def'",
    "A prompt with repeated words: 'hello hello hello hello'",
    "A prompt with very short length: 'short'",
    "A prompt with empty string: ''"
]

for i, prompt in enumerate(test_cases):
    try:
        print(f"Testing prompt {i+1}: {prompt[:50]}...")
        audio = pipe(prompt, num_inference_steps=25, audio_length_in_s=10).audios[0]
        sf.write(f"test_audio_{i}.wav", audio, samplerate=16000)
        print(f"Generated audio for test case {i+1}")
    except Exception as e:
        print(f"Error in test case {i+1}: {str(e)}")
        traceback.print_exc()
```

### Video Generation with Edge Case Handling

```python
# video_stress_test.py

import torch
from diffusers import StableVideoDiffusionPipeline
from diffusers.utils import load_image
import traceback
import os

model_id = "stabilityai/stable-video-diffusion-img2vid-xt"
pipe = StableVideoDiffusionPipeline.from_pretrained(
    model_id,
    torch_dtype=torch.float16,
    variant="fp16"
)
pipe = pipe.to("cuda")

# Load a sample image
image_path = "sample_image.jpg"
image = load_image(image_path)
image = image.resize((1024, 576))

# Test cases including edge cases
test_cases = [
    "A very long prompt that exceeds typical token limits and may cause tokenization issues",
    "A prompt with special characters: !@#$%^&*()",
    "A prompt with no meaningful content: 'xyz abc def'",
    "A prompt with repeated words: 'movie movie movie movie'",
    "A prompt with very short length: 'short'",
    "A prompt with empty string: ''"
]

for i, prompt in enumerate(test_cases):
    try:
        print(f"Testing video prompt {i+1}: {prompt[:50]}...")
        frames = pipe(
            image,
            prompt=prompt,
            num_inference_steps=25,
            decode_chunk_size=8,
            motion_bucket_id=127,
            fps=7,
            augmentation_factor=0
        ).frames[0]
        output_dir = f"test_video_{i}"
        os.makedirs(output_dir, exist_ok=True)
        for j, frame in enumerate(frames):
            frame.save(os.path.join(output_dir, f"frame_{j:03d}.png"))
        print(f"Generated video frames for test case {i+1}")
    except Exception as e:
        print(f"Error in test case {i+1}: {str(e)}")
        traceback.print_exc()
```

### Execution Command

Run the audio stress test:

```bash
python audio_stress_test.py
```

Run the video stress test:

```bash
python video_stress_test.py
```

## Verification Checklist & Quick Reference Cheat Sheet

| Component | Method/Function | Parameter | Description |
|----------|----------------|-----------|-------------|
| Audio Pipeline | `AudioLDMPipeline.from_pretrained()` | `model_id`, `torch_dtype` | Initializes the audio generation pipeline |
| Audio Generation | `pipe(prompt, num_inference_steps, audio_length_in_s)` | `prompt`, `num_inference_steps`, `audio_length_in_s` | Generates audio from text prompt |
| Video Pipeline | `StableVideoDiffusionPipeline.from_pretrained()` | `model_id`, `torch_dtype`, `variant` | Initializes the video generation pipeline |
| Video Generation | `pipe(image, prompt, num_inference_steps, decode_chunk_size)` | `image`, `prompt`, `num_inference_steps`, `decode_chunk_size` | Generates video from image and text prompt |
| Audio Saving | `soundfile.write()` | `filename`, `audio_data`, `samplerate` | Saves generated audio to file |
| Video Frame Saving | `frame.save()` | `filename` | Saves individual video frames |
| Benchmarking | `time.time()` | `start_time`, `end_time` | Measures latency of generation |
| Error Handling | `try/except` | `Exception` | Catches and logs errors during generation |
| Prompt Validation | `len(prompt)` | `prompt` | Checks for valid prompt length |
| Resource Monitoring | `torch.cuda.memory_allocated()` | `device` | Monitors GPU memory usage |

This lab provides a comprehensive operational verification framework for audio and video generation architectures, enabling practitioners to implement, benchmark, and test robust generative AI pipelines in real-world scenarios.
