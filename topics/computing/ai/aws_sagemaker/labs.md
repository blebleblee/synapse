# Operational Verification Labs: AWS SageMaker

## Objective & Environment Setup

AWS SageMaker occupies a singular position in the production ML landscape: it is simultaneously a managed training cluster, a model registry, a real-time inference fleet, and a feature engineering platform, all unified under a single IAM boundary and billing surface. For the working AI engineer, SageMaker's value is not in its console UI but in its Python SDK, which lets you express training jobs, hyperparameter searches, and endpoint deployments as first-class Python objects that serialize to API calls against SageMaker's control plane. The objective of these labs is to build real, end-to-end operational competence — not theoretical familiarity — with SageMaker's core execution loop: data preparation to S3, training job submission, HPO sweep, endpoint deployment, and live inference verification.

These labs deliberately avoid the SageMaker Studio notebook environment. Every script runs from your local terminal against the SageMaker API over the network, which mirrors how production ML pipelines are actually triggered — from CI/CD runners, Airflow DAGs, or engineer workstations. This forces you to reason about IAM roles, S3 prefixes, and container image URIs as explicit, versioned artifacts rather than ambient environment assumptions.

### Environment Prerequisites

You will need an AWS account with a SageMaker execution role that has `AmazonSageMakerFullAccess` and `AmazonS3FullAccess` attached. The role ARN is the single most critical configuration value in every script below. You will also need an S3 bucket in the same region as your SageMaker endpoint; cross-region data transfer adds latency and cost to every training job.

Create and activate a clean Python 3.11 virtual environment, then install the full dependency set:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install torch==2.3.0 transformers==4.41.0 datasets==2.19.0 \
    accelerate==0.30.0 numpy==1.26.4 polars==0.20.31 \
    sagemaker==2.219.0 boto3==1.34.100 scikit-learn==1.5.0 \
    wandb==0.17.0 pytest==8.2.0
```

Export the following environment variables. Replace each value with your actual account resources:

```bash
export AWS_DEFAULT_REGION="us-east-1"
export SAGEMAKER_ROLE_ARN="arn:aws:iam::123456789012:role/SageMakerExecutionRole"
export S3_BUCKET="your-sagemaker-lab-bucket"
export S3_PREFIX="sagemaker-labs"
```

Verify that your AWS credentials resolve correctly and that the SageMaker client can describe the execution role:

```bash
python -c "
import boto3, os
iam = boto3.client('iam')
role_name = os.environ['SAGEMAKER_ROLE_ARN'].split('/')[-1]
resp = iam.get_role(RoleName=role_name)
print('Role ARN confirmed:', resp['Role']['Arn'])
print('Max session duration (s):', resp['Role']['MaxSessionDuration'])
"
```

The output should confirm your role ARN without raising a `NoCredentialsError`. If you are running from an EC2 instance or a CI runner with an instance profile, `boto3` resolves credentials from the instance metadata service at `http://169.254.169.254/latest/meta-data/iam/security-credentials/`. From a local workstation, it uses `~/.aws/credentials` or environment variables. Both paths are valid; the scripts below are credential-source agnostic.

---

## Exercise 1: Hands-On Implementation & Pipeline Execution

### 1.1 — Dataset Preparation and S3 Staging

The foundation of every SageMaker training job is data staged in S3. SageMaker's training containers mount S3 data via one of two channel modes: `File` mode, which downloads the entire dataset to the container's local NVMe storage before training begins, and `FastFile` mode, which streams data directly from S3 using a FUSE-mounted filesystem. For this lab, you will prepare a text classification dataset, serialize it to Parquet (which Polars reads significantly faster than CSV at scale), and upload it to S3 with a channel-aware prefix structure.

The dataset used here is the AG News corpus, a four-class news topic classifier. It is small enough to iterate quickly but realistic enough that the training dynamics — class balance, sequence length distribution, tokenizer padding strategy — are non-trivial.

Create the file `prepare_dataset.py`:

```python
#!/usr/bin/env python3
"""
prepare_dataset.py

Downloads AG News, splits into train/val/test, serializes to Parquet,
and uploads all three splits to S3 under a versioned prefix.

Usage:
    python prepare_dataset.py
"""

import os
import hashlib
import boto3
import polars as pl
from datasets import load_dataset
from pathlib import Path

BUCKET = os.environ["S3_BUCKET"]
PREFIX = os.environ["S3_PREFIX"]
DATA_VERSION = "v1"
LOCAL_DIR = Path("./data/agnews")
LOCAL_DIR.mkdir(parents=True, exist_ok=True)

s3 = boto3.client("s3")


def compute_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def upload_file(local_path: Path, s3_key: str) -> None:
    print(f"Uploading {local_path} → s3://{BUCKET}/{s3_key}")
    s3.upload_file(str(local_path), BUCKET, s3_key)
    checksum = compute_sha256(local_path)
    s3.put_object_tagging(
        Bucket=BUCKET,
        Key=s3_key,
        Tagging={"TagSet": [{"Key": "sha256", "Value": checksum}]},
    )
    print(f"  SHA-256: {checksum}")


def main():
    print("Loading AG News dataset from HuggingFace Hub...")
    raw = load_dataset("ag_news")

    # ag_news has 'train' (120000) and 'test' (7600); we carve a val split
    train_hf = raw["train"].train_test_split(test_size=0.1, seed=42)
    splits = {
        "train": train_hf["train"],
        "val": train_hf["test"],
        "test": raw["test"],
    }

    for split_name, hf_split in splits.items():
        df = pl.from_dict(
            {
                "text": hf_split["text"],
                "label": hf_split["label"],
            }
        )

        # AG News labels: 0=World, 1=Sports, 2=Business, 3=Sci/Tech
        label_map = {0: "World", 1: "Sports", 2: "Business", 3: "Sci/Tech"}
        df = df.with_columns(
            pl.col("label").replace(label_map).alias("label_name")
        )

        # Print class distribution
        dist = df.group_by("label_name").agg(pl.len().alias("count")).sort("label_name")
        print(f"\n{split_name} split ({len(df)} rows):")
        print(dist)

        # Serialize to Parquet — column-oriented, Snappy compressed
        parquet_path = LOCAL_DIR / f"{split_name}.parquet"
        df.write_parquet(str(parquet_path), compression="snappy")
        print(f"Serialized → {parquet_path} ({parquet_path.stat().st_size / 1024:.1f} KB)")

        # Upload to versioned S3 prefix
        s3_key = f"{PREFIX}/datasets/agnews/{DATA_VERSION}/{split_name}.parquet"
        upload_file(parquet_path, s3_key)

    print("\nDataset preparation complete.")
    print(f"S3 base path: s3://{BUCKET}/{PREFIX}/datasets/agnews/{DATA_VERSION}/")


if __name__ == "__main__":
    main()
```

Run the preparation script:

```bash
python prepare_dataset.py
```

Verify the uploads reach S3 without corruption by checking the object tags:

```bash
python -c "
import boto3, os
s3 = boto3.client('s3')
bucket = os.environ['S3_BUCKET']
prefix = os.environ['S3_PREFIX']
paginator = s3.get_paginator('list_objects_v2')
for page in paginator.paginate(Bucket=bucket, Prefix=f'{prefix}/datasets/agnews/v1/'):
    for obj in page.get('Contents', []):
        tags_resp = s3.get_object_tagging(Bucket=bucket, Key=obj['Key'])
        sha = next((t['Value'] for t in tags_resp['TagSet'] if t['Key'] == 'sha256'), 'MISSING')
        print(f\"{obj['Key']}  size={obj['Size']}B  sha256={sha[:16]}...\")
"
```

### 1.2 — Training Script and Container Entry Point

SageMaker's managed training infrastructure executes a Python script inside a managed container. The container environment provides the framework (PyTorch, TensorFlow, MXNet), and your script is injected via the `source_dir` mechanism. SageMaker passes hyperparameters as command-line arguments and injects environment variables (`SM_CHANNEL_TRAIN`, `SM_CHANNEL_VAL`, `SM_MODEL_DIR`, `SM_OUTPUT_DATA_DIR`) that resolve to container-local filesystem paths backed by the S3 channels you configured.

Create the directory `training_code/` and place the following script at `training_code/train.py`:

```python
#!/usr/bin/env python3
"""
training_code/train.py

SageMaker entry point for AG News text classification using
DistilBERT fine-tuning. SageMaker injects all SM_* env vars.

Hyperparameters passed via --arg syntax from the Estimator:
    --epochs, --learning-rate, --batch-size, --max-length,
    --warmup-ratio, --weight-decay
"""

import argparse
import json
import logging
import os
import sys
from pathlib import Path

import numpy as np
import polars as pl
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from torch.optim import AdamW
from torch.optim.lr_scheduler import OneCycleLR
from transformers import (
    DistilBertForSequenceClassification,
    DistilBertTokenizerFast,
    get_linear_schedule_with_warmup,
)
from sklearn.metrics import classification_report, confusion_matrix

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

LABEL_NAMES = ["World", "Sports", "Business", "Sci/Tech"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    # SageMaker injects these via environment variables too; CLI args take precedence
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--learning-rate", type=float, default=2e-5)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--max-length", type=int, default=128)
    parser.add_argument("--warmup-ratio", type=float, default=0.06)
    parser.add_argument("--weight-decay", type=float, default=0.01)
    parser.add_argument(
        "--model-name", type=str, default="distilbert-base-uncased"
    )

    # SageMaker-injected paths
    parser.add_argument(
        "--train", type=str, default=os.environ.get("SM_CHANNEL_TRAIN", "./data/agnews")
    )
    parser.add_argument(
        "--val", type=str, default=os.environ.get("SM_CHANNEL_VAL", "./data/agnews")
    )
    parser.add_argument(
        "--model-dir", type=str, default=os.environ.get("SM_MODEL_DIR", "./model_output")
    )
    parser.add_argument(
        "--output-data-dir",
        type=str,
        default=os.environ.get("SM_OUTPUT_DATA_DIR", "./output"),
    )

    return parser.parse_args()


class AGNewsDataset(Dataset):
    def __init__(self, parquet_path: str, tokenizer, max_length: int):
        df = pl.read_parquet(parquet_path)
        self.texts = df["text"].to_list()
        self.labels = df["label"].to_list()
        self.tokenizer = tokenizer
        self.max_length = max_length

    def __len__(self) -> int:
        return len(self.texts)

    def __getitem__(self, idx: int) -> dict:
        encoding = self.tokenizer(
            self.texts[idx],
            max_length=self.max_length,
            padding="max_length",
            truncation=True,
            return_tensors="pt",
        )
        return {
            "input_ids": encoding["input_ids"].squeeze(0),
            "attention_mask": encoding["attention_mask"].squeeze(0),
            "labels": torch.tensor(self.labels[idx], dtype=torch.long),
        }


def evaluate(model: nn.Module, loader: DataLoader, device: torch.device) -> dict:
    model.eval()
    all_preds, all_labels, total_loss = [], [], 0.0

    with torch.no_grad():
        for batch in loader:
            input_ids = batch["input_ids"].to(device)
            attention_mask = batch["attention_mask"].to(device)
            labels = batch["labels"].to(device)

            outputs = model(
                input_ids=input_ids,
                attention_mask=attention_mask,
                labels=labels,
            )
            total_loss += outputs.loss.item()
            preds = torch.argmax(outputs.logits, dim=-1)
            all_preds.extend(preds.cpu().numpy().tolist())
            all_labels.extend(labels.cpu().numpy().tolist())

    avg_loss = total_loss / len(loader)
    report = classification_report(
        all_labels, all_preds, target_names=LABEL_NAMES, output_dict=True
    )
    return {
        "loss": avg_loss,
        "accuracy": report["accuracy"],
        "macro_f1": report["macro avg"]["f1-score"],
        "report": report,
        "confusion_matrix": confusion_matrix(all_labels, all_preds).tolist(),
    }


def main():
    args = parse_args()
    logger.info("SageMaker Training Job started with args: %s", vars(args))

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    logger.info("Compute device: %s", device)

    if device.type == "cuda":
        logger.info("CUDA device: %s", torch.cuda.get_device_name(0))
        logger.info("VRAM total: %.2f GB", torch.cuda.get_device_properties(0).total_memory / 1e9)

    Path(args.model_dir).mkdir(parents=True, exist_ok=True)
    Path(args.output_data_dir).mkdir(parents=True, exist_ok=True)

    logger.info("Loading tokenizer: %s", args.model_name)
    tokenizer = DistilBertTokenizerFast.from_pretrained(args.model_name)

    train_path = str(Path(args.train) / "train.parquet")
    val_path = str(Path(args.val) / "val.parquet")
    logger.info("Train data: %s", train_path)
    logger.info("Val data: %s", val_path)

    train_dataset = AGNewsDataset(train_path, tokenizer, args.max_length)
    val_dataset = AGNewsDataset(val_path, tokenizer, args.max_length)
    logger.info("Train samples: %d | Val samples: %d", len(train_dataset), len(val_dataset))

    train_loader = DataLoader(
        train_dataset, batch_size=args.batch_size, shuffle=True,
        num_workers=4, pin_memory=(device.type == "cuda")
    )
    val_loader = DataLoader(
        val_dataset, batch_size=args.batch_size * 2, shuffle=False,
        num_workers=4, pin_memory=(device.type == "cuda")
    )

    logger.info("Loading model: %s (num_labels=4)", args.model_name)
    model = DistilBertForSequenceClassification.from_pretrained(
        args.model_name, num_labels=4
    )
    model.to(device)

    total_steps = len(train_loader) * args.epochs
    warmup_steps = int(total_steps * args.warmup_ratio)
    logger.info("Total optimization steps: %d | Warmup steps: %d", total_steps, warmup_steps)

    optimizer = AdamW(
        model.parameters(), lr=args.learning_rate, weight_decay=args.weight_decay
    )
    scheduler = get_linear_schedule_with_warmup(
        optimizer, num_warmup_steps=warmup_steps, num_training_steps=total_steps
    )

    best_val_f1 = 0.0
    history = []

    for epoch in range(1, args.epochs + 1):
        model.train()
        epoch_loss = 0.0
        correct = 0
        total = 0

        for step, batch in enumerate(train_loader, 1):
            input_ids = batch["input_ids"].to(device)
            attention_mask = batch["attention_mask"].to(device)
            labels = batch["labels"].to(device)

            optimizer.zero_grad()
            outputs = model(
                input_ids=input_ids,
                attention_mask=attention_mask,
                labels=labels,
            )
            outputs.loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            optimizer.step()
            scheduler.step()

            epoch_loss += outputs.loss.item()
            preds = torch.argmax(outputs.logits, dim=-1)
            correct += (preds == labels).sum().item()
            total += labels.size(0)

            if step % 100 == 0:
                running_acc = correct / total
                logger.info(
                    "Epoch %d/%d | Step %d/%d | Loss: %.4f | Acc: %.4f | LR: %.2e",
                    epoch, args.epochs, step, len(train_loader),
                    epoch_loss / step, running_acc,
                    scheduler.get_last_lr()[0],
                )

        # Epoch-level validation
        val_metrics = evaluate(model, val_loader, device)
        train_metrics = {
            "epoch": epoch,
            "train_loss": epoch_loss / len(train_loader),
            "train_acc": correct / total,
            "val_loss": val_metrics["loss"],
            "val_acc": val_metrics["accuracy"],
            "val_macro_f1": val_metrics["macro_f1"],
        }
        history.append(train_metrics)

        logger.info(
            "Epoch %d complete | train_loss=%.4f | val_loss=%.4f | val_acc=%.4f | val_f1=%.4f",
            epoch, train_metrics["train_loss"], val_metrics["loss"],
            val_metrics["accuracy"], val_metrics["macro_f1"],
        )

        # Save best model checkpoint
        if val_metrics["macro_f1"] > best_val_f1:
            best_val_f1 = val_metrics["macro_f1"]
            checkpoint_path = Path(args.model_dir) / "best_model"
            model.save_pretrained(str(checkpoint_path))
            tokenizer.save_pretrained(str(checkpoint_path))
            logger.info("New best model saved (val_f1=%.4f) → %s", best_val_f1, checkpoint_path)

        # Emit SageMaker metric line for HPO parsing
        # SageMaker HPO parses stdout for lines matching the metric regex
        print(f"val_macro_f1={val_metrics['macro_f1']:.6f};")
        print(f"val_accuracy={val_metrics['accuracy']:.6f};")

    # Save final model (last epoch)
    final_path = Path(args.model_dir) / "final_model"
    model.save_pretrained(str(final_path))
    tokenizer.save_pretrained(str(final_path))

    # Write training history and final metrics to output_data_dir
    history_path = Path(args.output_data_dir) / "training_history.json"
    with open(history_path, "w") as f:
        json.dump({"history": history, "best_val_f1": best_val_f1}, f, indent=2)
    logger.info("Training history written to %s", history_path)

    # GPU memory summary (if available)
    if device.type == "cuda":
        logger.info("GPU memory summary:\n%s", torch.cuda.memory_summary())

    logger.info("Training complete. Best val_macro_f1=%.4f", best_val_f1)


if __name__ == "__main__":
    main()
```

The metric emission lines (`print(f"val_macro_f1=...")`) deserve attention. SageMaker's HPO service works by spawning a log scraper alongside each training container. It parses `stdout` and `stderr` using a regular expression you define at job submission time. By printing metrics in a consistent, scannable format, your training script feeds directly into SageMaker's Bayesian optimization loop without any additional instrumentation code. This is the idiomatic pattern for SageMaker HPO integration.

### 1.3 — Submitting the Training Job

The SageMaker Python SDK's `PyTorch` estimator is the primary abstraction for managed training. It encapsulates the container image URI, instance type, IAM role, hyperparameter map, and S3 channel definitions into a single Python object whose `.fit()` method submits the job to SageMaker's control plane and blocks (or not, with `wait=False`) until completion.

Create `submit_training_job.py`:

```python
#!/usr/bin/env python3
"""
submit_training_job.py

Submits a SageMaker managed training job for AG News classification.
Streams live logs to stdout and blocks until the job completes.

Usage:
    python submit_training_job.py
"""

import os
import time
import boto3
import sagemaker
from sagemaker.pytorch import PyTorch
from sagemaker.inputs import TrainingInput

ROLE = os.environ["SAGEMAKER_ROLE_ARN"]
BUCKET = os.environ["S3_BUCKET"]
PREFIX = os.environ["S3_PREFIX"]
REGION = os.environ.get("AWS_DEFAULT_REGION", "us-east-1")

session = sagemaker.Session(boto_session=boto3.Session(region_name=REGION))

DATA_S3_URI = f"s3://{BUCKET}/{PREFIX}/datasets/agnews/v1"


def build_estimator(
    job_name_suffix: str = "baseline",
    instance_type: str = "ml.g4dn.xlarge",
    epochs: int = 3,
    learning_rate: float = 2e-5,
    batch_size: int = 32,
    max_length: int = 128,
    warmup_ratio: float = 0.06,
    weight_decay: float = 0.01,
) -> tuple[PyTorch, str]:
    job_name = f"agnews-distilbert-{job_name_suffix}-{int(time.time())}"

    estimator = PyTorch(
        entry_point="train.py",
        source_dir="./training_code",
        role=ROLE,
        instance_type=instance_type,
        instance_count=1,
        # PyTorch 2.1.0 on Python 3.10, Deep Learning Container
        framework_version="2.1.0",
        py_version="py310",
        output_path=f"s3://{BUCKET}/{PREFIX}/model-artifacts/",
        base_job_name=job_name,
        sagemaker_session=session,
        hyperparameters={
            "epochs": epochs,
            "learning-rate": learning_rate,
            "batch-size": batch_size,
            "max-length": max_length,
            "warmup-ratio": warmup_ratio,
            "weight-decay": weight_decay,
        },
        metric_definitions=[
            {"Name": "val_macro_f1", "Regex": r"val_macro_f1=([0-9\.]+);"},
            {"Name": "val_accuracy", "Regex": r"val_accuracy=([0-9\.]+);"},
        ],
        environment={
            "TOKENIZERS_PARALLELISM": "false",
            "HF_DATASETS_CACHE": "/tmp/hf_cache",
        },
        # Enable SageMaker Managed Spot Training for ~70% cost reduction
        use_spot_instances=False,  # Set True for cost savings; adds interruption risk
        volume_size=50,            # EBS volume size in GB
        max_run=7200,              # 2 hour wall-clock timeout
    )
    return estimator, job_name


def main():
    print("Building SageMaker PyTorch Estimator...")
    estimator, job_name = build_estimator(
        job_name_suffix="baseline",
        epochs=3,
        learning_rate=2e-5,
        batch_size=32,
    )

    # Define input channels: SageMaker downloads each channel
    # to the container at SM_CHANNEL_<NAME> (uppercased)
    train_input = TrainingInput(
        s3_data=DATA_S3_URI,
        content_type="application/x-parquet",
        s3_data_type="S3Prefix",
        input_mode="File",          # Downloads to NVMe before training
    )

    print(f"Submitting training job: {job_name}")
    print(f"Instance type: ml.g4dn.xlarge (1x NVIDIA T4 16GB)")
    print(f"Input data: {DATA_S3_URI}")

    # wait=True streams CloudWatch logs to stdout in real time
    estimator.fit(
        inputs={"train": train_input, "val": train_input},
        wait=True,
        logs="All",
    )

    print("\nTraining job complete.")
    print(f"Model artifact: {estimator.model_data}")
    print(f"Job name: {estimator.latest_training_job.name}")

    # Write job metadata for downstream scripts
    import json
    metadata = {
        "job_name": estimator.latest_training_job.name,
        "model_artifact_s3": estimator.model_data,
        "instance_type": "ml.g4dn.xlarge",
        "hyperparameters": estimator.hyperparameters(),
    }
    with open("training_job_metadata.json", "w") as f:
        json.dump(metadata, f, indent=2)
    print("Metadata saved → training_job_metadata.json")


if __name__ == "__main__":
    main()
```

Execute the job submission:

```bash
python submit_training_job.py 2>&1 | tee training_job.log
```

SageMaker will provision the `ml.g4dn.xlarge` instance (1x NVIDIA T4 GPU, 16 GB VRAM, 4 vCPUs), pull the PyTorch Deep Learning Container from ECR, copy your `source_dir` into the container, download the S3 channels to `/opt/ml/input/data/train/`, and execute `train.py`. The entire provisioning overhead is typically 3–6 minutes, independent of the training workload itself. This cold-start cost is the fundamental economic argument for using larger instance types on longer jobs — the per-hour rate is proportionally cheaper than the fixed provisioning overhead on tiny jobs.

### 1.4 — Deploying the Inference Endpoint

Once the training job completes, the model artifact (`model.tar.gz`) is stored in S3. Deploying it to a real-time endpoint requires a `PyTorchModel` wrapper that specifies the inference server script, and a `.deploy()` call that provisions the endpoint instance. Create `inference_code/inference.py`:

```python
#!/usr/bin/env python3
"""
inference_code/inference.py

SageMaker inference entry point.
Loaded by the PyTorch serving container.

Required functions: model_fn, input_fn, predict_fn, output_fn
"""

import json
import os
import torch
from transformers import DistilBertForSequenceClassification, DistilBertTokenizerFast

LABEL_NAMES = ["World", "Sports", "Business", "Sci/Tech"]
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")


def model_fn(model_dir: str):
    """Load model and tokenizer from model_dir (extracted from model.tar.gz)."""
    best_model_path = os.path.join(model_dir, "best_model")
    if not os.path.exists(best_model_path):
        best_model_path = os.path.join(model_dir, "final_model")

    tokenizer = DistilBertTokenizerFast.from_pretrained(best_model_path)
    model = DistilBertForSequenceClassification.from_pretrained(best_model_path)
    model.to(DEVICE)
    model.eval()
    return {"model": model, "tokenizer": tokenizer}


def input_fn(request_body: str, content_type: str) -> list:
    """Parse incoming request. Accepts JSON with a 'texts' list."""
    if content_type != "application/json":
        raise ValueError(f"Unsupported content type: {content_type}")
    data = json.loads(request_body)
    if isinstance(data, str):
        return [data]
    if isinstance(data, list):
        return data
    if isinstance(data, dict) and "texts" in data:
        return data["texts"]
    raise ValueError("Input must be a string, list of strings, or {'texts': [...]}")


def predict_fn(texts: list, model_bundle: dict) -> list:
    """Run inference on a list of text strings."""
    model = model_bundle["model"]
    tokenizer = model_bundle["tokenizer"]

    encoding = tokenizer(
        texts,
        max_length=128,
        padding="max_length",
        truncation=True,
        return_tensors="pt",
    )
    input_ids = encoding["input_ids"].to(DEVICE)
    attention_mask = encoding["attention_mask"].to(DEVICE)

    with torch.no_grad():
        outputs = model(input_ids=input_ids, attention_mask=attention_mask)
        probs = torch.softmax(outputs.logits, dim=-1)
        preds = torch.argmax(probs, dim=-1)

    results = []
    for i in range(len(texts)):
        pred_idx = preds[i].item()
        results.append(
            {
                "label": LABEL_NAMES[pred_idx],
                "label_id": pred_idx,
                "confidence": probs[i][pred_idx].item(),
                "probabilities": {
                    LABEL_NAMES[j]: probs[i][j].item() for j in range(4)
                },
            }
        )
    return results


def output_fn(predictions: list, accept: str) -> tuple:
    """Serialize predictions to JSON."""
    return json.dumps(predictions), "application/json"
```

Now create the deployment script `deploy_endpoint.py`:

```python
#!/usr/bin/env python3
"""
deploy_endpoint.py

Deploys the trained AG News classifier to a SageMaker real-time endpoint.
Reads training_job_metadata.json written by submit_training_job.py.

Usage:
    python deploy_endpoint.py
"""

import json
import os
import time
import boto3
import sagemaker
from sagemaker.pytorch import PyTorchModel

ROLE = os.environ["SAGEMAKER_ROLE_ARN"]
REGION = os.environ.get("AWS_DEFAULT_REGION", "us-east-1")

session = sagemaker.Session(boto_session=boto3.Session(region_name=REGION))

ENDPOINT_NAME = f"agnews-classifier-{int(time.time())}"


def main():
    with open("training_job_metadata.json") as f:
        metadata = json.load(f)

    model_artifact_s3 = metadata["model_artifact_s3"]
    print(f"Model artifact: {model_artifact_s3}")
    print(f"Deploying to endpoint: {ENDPOINT_NAME}")

    model = PyTorchModel(
        model_data=model_artifact_s3,
        role=ROLE,
        entry_point="inference.py",
        source_dir="./inference_code",
        framework_version="2.1.0",
        py_version="py310",
        sagemaker_session=session,
        env={"TOKENIZERS_PARALLELISM": "false"},
    )

    # Deploy to ml.m5.xlarge: 4 vCPU, 16GB RAM — adequate for DistilBERT CPU inference
    # For higher throughput, use ml.g4dn.xlarge (GPU) and increase instance_count
    predictor = model.deploy(
        initial_instance_count=1,
        instance_type="ml.m5.xlarge",
        endpoint_name=ENDPOINT_NAME,
        wait=True,
    )

    print(f"\nEndpoint deployed: {ENDPOINT_NAME}")

    # Smoke test immediately after deployment
    test_payload = {
        "texts": [
            "Apple reports record quarterly earnings driven by iPhone sales",
            "Champions League final: Real Madrid defeats Bayern Munich 3-1",
            "NASA's Artemis program delays moon landing to 2026",
            "Federal Reserve holds interest rates steady amid inflation concerns",
        ]
    }

    import json as json_module
    response = predictor.predict(
        data=json_module.dumps(test_payload),
        initial_args={"ContentType": "application/json", "Accept": "application/json"},
    )
    predictions = json_module.loads(response)

    print("\nSmoke test predictions:")
    for text, pred in zip(test_payload["texts"], predictions):
        print(f"  [{pred['label']:10s}  {pred['confidence']:.3f}]  {text[:70]}")

    # Persist endpoint name for downstream eval script
    with open("endpoint_metadata.json", "w") as f:
        json.dump({"endpoint_name": ENDPOINT_NAME, "instance_type": "ml.m5.xlarge"}, f, indent=2)
    print(f"\nEndpoint metadata saved → endpoint_metadata.json")


if __name__ == "__main__":
    main()
```

```bash
python deploy_endpoint.py
```

---

## Exercise 2: Hyperparameter Tuning & Empirical Benchmarking

### 2.1 — Automated HPO with SageMaker Automatic Model Tuning

Manual hyperparameter search over a learning rate / batch size grid is methodologically unsound at scale. SageMaker's Automatic Model Tuning (AMT) service implements Bayesian optimization over a continuous or categorical search space, using a Gaussian Process surrogate model to predict which hyperparameter configuration is most likely to improve the objective metric, given the results of all previously evaluated configurations. Bayesian optimization often outperforms random search, especially as the number of trials grows and the GP model's uncertainty estimates guide exploration toward high-probability regions of the hyperparameter surface, though the crossover point depends on problem structure and noise.

Create `hpo_job.py`:

```python
#!/usr/bin/env python3
"""
hpo_job.py

Launches a SageMaker Automatic Model Tuning (HPO) job over
learning rate, batch size, warmup ratio, and weight decay.

Optimization objective: maximize val_macro_f1 (parsed from stdout).

Usage:
    python hpo_job.py
"""

import os
import time
import json
import boto3
import sagemaker
from sagemaker.pytorch import PyTorch
from sagemaker.inputs import TrainingInput
from sagemaker.tuner import (
    HyperparameterTuner,
    ContinuousParameter,
    IntegerParameter,
    CategoricalParameter,
)

ROLE = os.environ["SAGEMAKER_ROLE_ARN"]
BUCKET = os.environ["S3_BUCKET"]
PREFIX = os.environ["S3_PREFIX"]
REGION = os.environ.get("AWS_DEFAULT_REGION", "us-east-1")

session = sagemaker.Session(boto_session=boto3.Session(region_name=REGION))
DATA_S3_URI = f"s3://{BUCKET}/{PREFIX}/datasets/agnews/v1"


def main():
    # Base estimator with fixed hyperparameters (the non-tuned ones)
    base_estimator = PyTorch(
        entry_point="train.py",
        source_dir="./training_code",
        role=ROLE,
        instance_type="ml.g4dn.xlarge",
        instance_count=1,
        framework_version="2.1.0",
        py_version="py310",
        output_path=f"s3://{BUCKET}/{PREFIX}/hpo-artifacts/",
        base_job_name=f"agnews-hpo-{int(time.time())}",
        sagemaker_session=session,
        hyperparameters={
            "epochs": 2,           # Shorter epochs for HPO speed
            "max-length": 128,
            "model-name": "distilbert-base-uncased",
        },
        metric_definitions=[
            {"Name": "val_macro_f1", "Regex": r"val_macro_f1=([0-9\.]+);"},
            {"Name": "val_accuracy", "Regex": r"val_accuracy=([0-9\.]+);"},
        ],
        environment={"TOKENIZERS_PARALLELISM": "false"},
        max_run=3600,
    )

    # Define the search space
    # ContinuousParameter uses log-scale internally for learning rate
    hyperparameter_ranges = {
        "learning-rate": ContinuousParameter(1e-5, 5e-5, scaling_type="Logarithmic"),
        "batch-size": CategoricalParameter([16, 32, 48]),
        "warmup-ratio": ContinuousParameter(0.03, 0.15),
        "weight-decay": ContinuousParameter(0.0, 0.05),
    }

    tuner = HyperparameterTuner(
        estimator=base_estimator,
        objective_metric_name="val_macro_f1",
        hyperparameter_ranges=hyperparameter_ranges,
        max_jobs=12,                # Total number of training jobs to run
        max_parallel_jobs=3,        # Run 3 jobs simultaneously
        objective_type="Maximize",  # We want to maximize F1
        strategy="Bayesian",        # GP-based Bayesian optimization
        early_stopping_type="Auto", # Kill unpromising trials early
    )

    train_input = TrainingInput(
        s3_data=DATA_S3_URI,
        content_type="application/x-parquet",
        s3_data_type="S3Prefix",
        input_mode="File",
    )

    hpo_job_name = f"agnews-hpo-tuner-{int(time.time())}"
    print(f"Starting HPO job: {hpo_job_name}")
    print(f"Max jobs: 12 | Max parallel: 3 | Strategy: Bayesian")
    print(f"Search space: lr=[1e-5,5e-5], batch=[16,32,48], warmup=[0.03,0.15], wd=[0,0.05]")

    tuner.fit(
        inputs={"train": train_input, "val": train_input},
        job_name=hpo_job_name,
        wait=True,
        logs="All",
    )

    # Retrieve best training job and its hyperparameters
    best_job = tuner.best_training_job()
    sm_client = boto3.client("sagemaker", region_name=REGION)
    best_job_desc = sm_client.describe_training_job(TrainingJobName=best_job)

    best_hps = best_job_desc["HyperParameters"]
    best_metrics = {
        m["MetricName"]: m["Value"]
        for m in best_job_desc.get("FinalMetricDataList", [])
    }

    print(f"\nBest training job: {best_job}")
    print(f"Best hyperparameters: {json.dumps(best_hps, indent=2)}")
    print(f"Best metrics: {json.dumps(best_metrics, indent=2)}")

    # Save HPO results for downstream analysis
    hpo_results = {
        "hpo_job_name": hpo_job_name,
        "best_training_job": best_job,
        "best_hyperparameters": best_hps,
        "best_metrics": best_metrics,
        "model_artifact_s3": best_job_desc["ModelArtifacts"]["S3ModelArtifacts"],
    }
    with open("hpo_results.json", "w") as f:
        json.dump(hpo_results, f, indent=2)
    print("\nHPO results saved → hpo_results.json")


if __name__ == "__main__":
    main()
```

```bash
python hpo_job.py 2>&1 | tee hpo_job.log
```

### 2.2 — Post-HPO Benchmarking Harness

After the HPO job completes, you need a rigorous evaluation harness that measures the best model against the held-out test split, computes per-class metrics, and benchmarks inference latency at the deployed endpoint. This is the step most practitioners skip, to their detriment — the validation F1 from the HPO objective does not equal test F1, and the gap is diagnostic of overfitting to the validation set through repeated evaluation.

Create `eval_pipeline.py`:

```python
#!/usr/bin/env python3
"""
eval_pipeline.py

Comprehensive evaluation harness for the deployed SageMaker endpoint.
Measures:
  - Test-set accuracy, macro F1, per-class precision/recall/F1
  - Confusion matrix
  - Inference latency (p50, p90, p99) via batched endpoint calls
  - Throughput (samples/sec)

Usage:
    python eval_pipeline.py --benchmark
    python eval_pipeline.py --benchmark --batch-size 16
"""

import argparse
import json
import os
import time
from pathlib import Path

import boto3
import numpy as np
import polars as pl
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    accuracy_score,
    f1_score,
)

REGION = os.environ.get("AWS_DEFAULT_REGION", "us-east-1")
BUCKET = os.environ["S3_BUCKET"]
PREFIX = os.environ["S3_PREFIX"]

LABEL_NAMES = ["World", "Sports", "Business", "Sci/Tech"]


def load_test_data(local_path: str = "./data/agnews/test.parquet") -> tuple:
    """Load test split from local Parquet."""
    if not Path(local_path).exists():
        # Download from S3 if not cached locally
        import boto3 as b3
        s3 = b3.client("s3", region_name=REGION)
        Path(local_path).parent.mkdir(parents=True, exist_ok=True)
        s3_key = f"{PREFIX}/datasets/agnews/v1/test.parquet"
        print(f"Downloading test split from s3://{BUCKET}/{s3_key}")
        s3.download_file(BUCKET, s3_key, local_path)

    df = pl.read_parquet(local_path)
    return df["text"].to_list(), df["label"].to_list()


def invoke_endpoint_batch(
    runtime_client,
    endpoint_name: str,
    texts: list,
) -> list:
    """
    Call SageMaker endpoint with a batch of texts.
    Returns list of prediction dicts.
    """
    payload = json.dumps({"texts": texts})
    response = runtime_client.invoke_endpoint(
        EndpointName=endpoint_name,
        ContentType="application/json",
        Accept="application/json",
        Body=payload.encode("utf-8"),
    )
    return json.loads(response["Body"].read())


def run_full_evaluation(
    endpoint_name: str,
    texts: list,
    true_labels: list,
    batch_size: int = 32,
    benchmark: bool = True,
) -> dict:
    runtime = boto3.client("sagemaker-runtime", region_name=REGION)

    all_preds = []
    all_confidences = []
    latencies_ms = []

    n_samples = len(texts)
    n_batches = (n_samples + batch_size - 1) // batch_size

    print(f"\nRunning evaluation: {n_samples} samples | batch_size={batch_size} | {n_batches} batches")
    eval_start = time.perf_counter()

    for i in range(0, n_samples, batch_size):
        batch_texts = texts[i : i + batch_size]
        t0 = time.perf_counter()
        preds = invoke_endpoint_batch(runtime, endpoint_name, batch_texts)
        t1 = time.perf_counter()

        latencies_ms.append((t1 - t0) * 1000.0)
        all_preds.extend([p["label_id"] for p in preds])
        all_confidences.extend([p["confidence"] for p in preds])

        if (i // batch_size + 1) % 10 == 0:
            print(
                f"  Batch {i // batch_size + 1}/{n_batches} | "
                f"Running avg latency: {np.mean(latencies_ms):.1f}ms"
            )

    eval_end = time.perf_counter()
    total_wall_time = eval_end - eval_start
    throughput = n_samples / total_wall_time

    # Classification metrics
    acc = accuracy_score(true_labels, all_preds)
    macro_f1 = f1_score(true_labels, all_preds, average="macro")
    report = classification_report(
        true_labels, all_preds,
        target_names=LABEL_NAMES,
        output_dict=True,
        digits=4,
    )
    cm = confusion_matrix(true_labels, all_preds)
    avg_confidence = np.mean(all_confidences)

    # Latency percentiles (per-batch)
    lat_arr = np.array(latencies_ms)
    # Per-sample latency
    sample_lat = lat_arr / batch_size

    results = {
        "endpoint_name": endpoint_name,
        "n_samples": n_samples,
        "batch_size": batch_size,
        "accuracy": float(acc),
        "macro_f1": float(macro_f1),
        "avg_confidence": float(avg_confidence),
        "per_class": {
            cls: {
                "precision": report[cls]["precision"],
                "recall": report[cls]["recall"],
                "f1-score": report[cls]["f1-score"],
                "support": report[cls]["support"],
            }
            for cls in LABEL_NAMES
        },
        "confusion_matrix": cm.tolist(),
        "latency_ms": {
            "batch_p50": float(np.percentile(lat_arr, 50)),
            "batch_p90": float(np.percentile(lat_arr, 90)),
            "batch_p99": float(np.percentile(lat_arr, 99)),
            "batch_mean": float(np.mean(lat_arr)),
            "sample_p50_ms": float(np.percentile(sample_lat, 50)),
            "sample_p90_ms": float(np.percentile(sample_lat, 90)),
            "sample_p99_ms": float(np.percentile(sample_lat, 99)),
        },
        "throughput_samples_per_sec": float(throughput),
        "total_eval_time_sec": float(total_wall_time),
    }

    return results


def print_results(results: dict) -> None:
    print("\n" + "=" * 70)
    print("EVALUATION RESULTS")
    print("=" * 70)
    print(f"Endpoint:            {results['endpoint_name']}")
    print(f"Samples evaluated:   {results['n_samples']}")
    print(f"Accuracy:            {results['accuracy']:.4f}")
    print(f"Macro F1:            {results['macro_f1']:.4f}")
    print(f"Avg Confidence:      {results['avg_confidence']:.4f}")
    print()
    print("Per-Class Metrics:")
    print(f"  {'Class':<12} {'Precision':>10} {'Recall':>10} {'F1':>10} {'Support':>10}")
    print("  " + "-" * 46)
    for cls in LABEL_NAMES:
        m = results["per_class"][cls]
        print(
            f"  {cls:<12} {m['precision']:>10.4f} {m['recall']:>10.4f} "
            f"{m['f1-score']:>10.4f} {int(m['support']):>10d}"
        )
    print()
    print("Confusion Matrix (rows=true, cols=predicted):")
    header = f"  {'':>12}" + "".join(f"{lbl:>10}" for lbl in LABEL_NAMES)
    print(header)
    for i, row in enumerate(results["confusion_matrix"]):
        row_str = f"  {LABEL_NAMES[i]:<12}" + "".join(f"{v:>10d}" for v in row)
        print(row_str)
    print()
    print("Latency Benchmarks:")
    lat = results["latency_ms"]
    print(f"  Batch p50/p90/p99:  {lat['batch_p50']:.1f}ms / {lat['batch_p90']:.1f}ms / {lat['batch_p99']:.1f}ms")
    print(f"  Sample p50/p90/p99: {lat['sample_p50_ms']:.2f}ms / {lat['sample_p90_ms']:.2f}ms / {lat['sample_p99_ms']:.2f}ms")
    print(f"  Throughput:         {results['throughput_samples_per_sec']:.1f} samples/sec")
    print(f"  Total eval time:    {results['total_eval_time_sec']:.1f}s")
    print("=" * 70)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--benchmark", action="store_true", help="Run full benchmark suite")
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument(
        "--endpoint-name",
        type=str,
        default=None,
        help="Override endpoint name (default: read from endpoint_metadata.json)",
    )
    args = parser.parse_args()

    if args.endpoint_name:
        endpoint_name = args.endpoint_name
    else:
        with open("endpoint_metadata.json") as f:
            endpoint_name = json.load(f)["endpoint_name"]

    print(f"Target endpoint: {endpoint_name}")
    texts, true_labels = load_test_data()
    print(f"Test split loaded: {len(texts)} samples")

    results = run_full_evaluation(
        endpoint_name=endpoint_name,
        texts=texts,
        true_labels=true_labels,
        batch_size=args.batch_size,
        benchmark=args.benchmark,
    )

    print_results(results)

    output_path = "eval_results.json"
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nFull results saved → {output_path}")


if __name__ == "__main__":
    main()
```

Execute the evaluation harness against the deployed endpoint:

```bash
python eval_pipeline.py --benchmark --batch-size 32
```

You should observe test accuracy between 0.93 and 0.95 on AG News with DistilBERT, with macro F1 within 0.5–1.0 points of the validation F1 from training. A gap larger than 1 F1 point is a signal to inspect your val/test split methodology or to verify that the data loading order in your training script is not introducing a systematic shuffle bias.

### 2.3 — HPO Results Analysis

After the HPO job, analyze the results across all 12 trials to understand the shape of the hyperparameter response surface:

```python
#!/usr/bin/env python3
"""
analyze_hpo.py

Fetches all HPO trial results and builds a Polars DataFrame
for analysis. Prints correlation between hyperparameters and objective.

Usage:
    python analyze_hpo.py
"""

import json
import os
import boto3
import polars as pl

REGION = os.environ.get("AWS_DEFAULT_REGION", "us-east-1")


def main():
    with open("hpo_results.json") as f:
        hpo_data = json.load(f)

    hpo_job_name = hpo_data["hpo_job_name"]
    sm = boto3.client("sagemaker", region_name=REGION)

    # List all training jobs under this HPO tuner
    paginator = sm.get_paginator("list_training_jobs_for_hyper_parameter_tuning_job")
    all_jobs = []
    for page in paginator.paginate(HyperParameterTuningJobName=hpo_job_name):
        all_jobs.extend(page["TrainingJobSummaries"])

    print(f"Total HPO trials: {len(all_jobs)}")

    rows = []
    for job_summary in all_jobs:
        job_name = job_summary["TrainingJobName"]
        # Describe each job to get final metrics and HPs
        desc = sm.describe_training_job(TrainingJobName=job_name)
        hps = desc.get("HyperParameters", {})
        metrics = {
            m["MetricName"]: float(m["Value"])
            for m in desc.get("FinalMetricDataList", [])
        }
        rows.append(
            {
                "job_name": job_name,
                "status": desc["TrainingJobStatus"],
                "learning_rate": float(hps.get("learning-rate", "nan")),
                "batch_size": int(float(hps.get("batch-size", "0"))),
                "warmup_ratio": float(hps.get("warmup-ratio", "nan")),
                "weight_decay": float(hps.get("weight-decay", "nan")),
                "val_macro_f1": metrics.get("val_macro_f1", float("nan")),
                "val_accuracy": metrics.get("val_accuracy", float("nan")),
            }
        )

    df = pl.DataFrame(rows).sort("val_macro_f1", descending=True)

    print("\nAll HPO trials (sorted by val_macro_f1):")
    print(df.to_pandas().to_string(index=False))

    # Pearson correlation of each HP with objective
    print("\nCorrelation with val_macro_f1:")
    for col in ["learning_rate", "batch_size", "warmup_ratio", "weight_decay"]:
        valid = df.filter(pl.col("val_macro_f1").is_not_nan()).with_columns(pl.col(col).cast(pl.Float64))
        valid = valid.filter(pl.col(col).is_not_nan())
        if len(valid) >= 3:
            corr = valid.select(pl.pearson_corr(col, "val_macro_f1")).item()
            print(f"  {col:<18}: r = {corr:+.4f}")

    best = df.head(1)
    print(f"\nBest configuration:")
    print(f"  Learning rate: {best['learning_rate'][0]:.2e}")
    print(f"  Batch size:    {best['batch_size'][0]}")
    print(f"  Warmup ratio:  {best['warmup_ratio'][0]:.4f}")
    print(f"  Weight decay:  {best['weight_decay'][0]:.5f}")
    print(f"  Val macro F1:  {best['val_macro_f1'][0]:.4f}")

    df.write_parquet("hpo_analysis.parquet")
    print("\nHPO analysis saved → hpo_analysis.parquet")


if __name__ == "__main__":
    main()
```

```bash
python analyze_hpo.py
```

---

## Exercise 3: Stress Testing, Edge Cases & Failure Mitigation

### 3.1 — Endpoint Stress Test: Concurrency and Latency Under Load

A single `ml.m5.xlarge` endpoint instance running DistilBERT CPU inference has a throughput ceiling. Under concurrent load, requests queue at the HTTP frontend inside the container, and tail latency (p99) degrades sharply when queue depth exceeds the number of inference threads. This test quantifies that ceiling using Python's `concurrent.futures.ThreadPoolExecutor` to issue parallel requests and measures how latency and error rate evolve with concurrency level. Create `stress_test.py`:

```python
#!/usr/bin/env python3
"""
stress_test.py

Stress tests the SageMaker endpoint at increasing concurrency levels.
Measures latency (p50, p90, p99), throughput, and error rate at each level.

Usage:
    python stress_test.py
"""

import concurrent.futures
import json
import os
import time
from collections import defaultdict

import boto3
import numpy as np

REGION = os.environ.get("AWS_DEFAULT_REGION", "us-east-1")

TEST_TEXTS = [
    "Global leaders meet at UN summit to discuss climate policy agreements",
    "Manchester City clinches Premier League title in dramatic final-day win",
    "Federal Reserve raises interest rates by 25 basis points amid inflation",
    "SpaceX successfully launches crewed mission to International Space Station",
    "Amazon announces record Black Friday sales exceeding previous year by 23%",
    "New study links air pollution to increased risk of cardiovascular disease",
    "Tech stocks rally after inflation data shows cooling consumer price index",
    "Olympic committee confirms Paris 2024 venue construction on schedule",
]


def invoke_once(runtime_client, endpoint_name: str, texts: list) -> dict:
    """Single endpoint invocation with error capture."""
    t0 = time.perf_counter()
    try:
        response = runtime_client.invoke_endpoint(
            EndpointName=endpoint_name,
            ContentType="application/json",
            Accept="application/json",
            Body=json.dumps({"texts": texts}).encode("utf-8"),
        )
        body = json.loads(response["Body"].read())
        t1 = time.perf_counter()
        return {
            "success": True,
            "latency_ms": (t1 - t0) * 1000.0,
            "n_predictions": len(body),
            "error": None,
        }
    except Exception as exc:
        t1 = time.perf_counter()
        return {
            "success": False,
            "latency_ms": (t1 - t0) * 1000.0,
            "n_predictions": 0,
            "error": str(exc),
        }


def run_concurrency_level(
    endpoint_name: str,
    concurrency: int,
    n_requests: int,
    batch_size: int = 4,
) -> dict:
    runtime = boto3.client("sagemaker-runtime", region_name=REGION)

    # Build fixed-size batches from TEST_TEXTS
    texts = (TEST_TEXTS * ((batch_size // len(TEST_TEXTS)) + 1))[:batch_size]
    results = []

    wall_start = time.perf_counter()
    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as pool:
        futures = [
            pool.submit(invoke_once, runtime, endpoint_name, texts)
            for _ in range(n_requests)
        ]
        for future in concurrent.futures.as_completed(futures):
            results.append(future.result())
    wall_end = time.perf_counter()

    successes = [r for r in results if r["success"]]
    failures = [r for r in results if not r["success"]]
    latencies = np.array([r["latency_ms"] for r in successes])

    total_samples = sum(r["n_predictions"] for r in successes)
    wall_time = wall_end - wall_start

    return {
        "concurrency": concurrency,
        "n_requests": n_requests,
        "batch_size": batch_size,
        "success_count": len(successes),
        "error_count": len(failures),
        "error_rate": len(failures) / n_requests,
        "p50_ms": float(np.percentile(latencies, 50)) if len(latencies) > 0 else float("nan"),
        "p90_ms": float(np.percentile(latencies, 90)) if len(latencies) > 0 else float("nan"),
        "p99_ms": float(np.percentile(latencies, 99)) if len(latencies) > 0 else float("nan"),
        "mean_ms": float(np.mean(latencies)) if len(latencies) > 0 else float("nan"),
        "throughput_samples_per_sec": total_samples / wall_time if wall_time > 0 else 0.0,
        "wall_time_sec": wall_time,
        "errors": [f["error"] for f in failures[:5]],  # Sample first 5 error messages
    }


def main():
    with open("endpoint_metadata.json") as f:
        endpoint_name = json.load(f)["endpoint_name"]

    print(f"Stress testing endpoint: {endpoint_name}")
    print(f"Instance type: ml.m5.xlarge (CPU inference)")

    concurrency_levels = [1, 2, 4, 8, 16, 32]
    n_requests_per_level = 50
    batch_size = 4

    all_results = []
    print(
        f"\n{'Concurrency':>12} {'p50_ms':>8} {'p90_ms':>8} {'p99_ms':>8} "
        f"{'Throughput':>12} {'ErrorRate':>10}"
    )
    print("-" * 65)

    for c in concurrency_levels:
        # Warm up with 5 requests at this concurrency level
        run_concurrency_level(endpoint_name, concurrency=c, n_requests=5, batch_size=batch_size)
        # Actual measurement
        result = run_concurrency_level(
            endpoint_name,
            concurrency=c,
            n_requests=n_requests_per_level,
            batch_size=batch_size,
        )
        all_results.append(result)

        print(
            f"{c:>12d} {result['p50_ms']:>8.1f} {result['p90_ms']:>8.1f} "
            f"{result['p99_ms']:>8.1f} {result['throughput_samples_per_sec']:>10.1f}/s "
            f"{result['error_rate']:>10.1%}"
        )

        if result["error_count"] > 0:
            print(f"  → Errors at concurrency {c}: {result['errors'][0]}")

        # Back off if error rate exceeds 10%
        if result["error_rate"] > 0.10:
            print(f"  → Error rate exceeded 10% at concurrency={c}. Stopping sweep.")
            break

        # Inter-level cooldown to let the endpoint drain its queue
        time.sleep(5.0)

    # Find the saturation point: largest concurrency where p99 < 2000ms
    saturation = None
    for r in all_results:
        if r["p99_ms"] < 2000.0 and r["error_rate"] < 0.05:
            saturation = r["concurrency"]

    print(f"\nSaturation point (p99 < 2000ms, error < 5%): concurrency={saturation}")

    with open("stress_test_results.json", "w") as f:
        json.dump(all_results, f, indent=2)
    print("Stress test results saved → stress_test_results.json")


if __name__ == "__main__":
    main()
```

```bash
python stress_test.py
```

### 3.2 — Edge Case Verification: Adversarial and Boundary Inputs

Production inference endpoints fail in predictable ways when inputs violate the assumptions embedded in the training distribution. The four most common failure modes for sequence classification endpoints are: empty strings (zero-token sequences), strings that exceed `max_length` and lose semantic content through truncation, Unicode characters outside the tokenizer's vocabulary (resulting in excessive `[UNK]` tokens), and mixed-language inputs where the model was trained monolingually. Create `edge_case_tests.py`:

```python
#!/usr/bin/env python3
"""
edge_case_tests.py

Systematic edge case verification for the AG News endpoint.
Tests empty inputs, over-length inputs, Unicode, adversarial text,
and injection attempts, then validates response structure invariants.

Usage:
    python -m pytest edge_case_tests.py -v
"""

import json
import os
import pytest
import boto3

REGION = os.environ.get("AWS_DEFAULT_REGION", "us-east-1")


@pytest.fixture(scope="module")
def runtime_client():
    return boto3.client("sagemaker-runtime", region_name=REGION)


@pytest.fixture(scope="module")
def endpoint_name():
    with open("endpoint_metadata.json") as f:
        return json.load(f)["endpoint_name"]


def invoke(runtime_client, endpoint_name: str, texts: list) -> list:
    response = runtime_client.invoke_endpoint(
        EndpointName=endpoint_name,
        ContentType="application/json",
        Accept="application/json",
        Body=json.dumps({"texts": texts}).encode("utf-8"),
    )
    return json.loads(response["Body"].read())


LABEL_NAMES = {"World", "Sports", "Business", "Sci/Tech"}


def assert_valid_prediction(pred: dict) -> None:
    """Assert structural invariants on a single prediction dict."""
    assert "label" in pred, "Missing 'label' key in prediction"
    assert pred["label"] in LABEL_NAMES, f"Unknown label: {pred['label']}"
    assert "label_id" in pred, "Missing 'label_id' key"
    assert pred["label_id"] in {0, 1, 2, 3}, f"label_id out of range: {pred['label_id']}"
    assert "confidence" in pred, "Missing 'confidence' key"
    assert 0.0 <= pred["confidence"] <= 1.0, f"Confidence out of [0,1]: {pred['confidence']}"
    assert "probabilities" in pred, "Missing 'probabilities' key"
    prob_sum = sum(pred["probabilities"].values())
    assert abs(prob_sum - 1.0) < 1e-4, f"Probabilities do not sum to 1: {prob_sum}"


class TestNormalInputs:
    def test_single_news_article(self, runtime_client, endpoint_name):
        texts = ["Apple announces new MacBook Pro with M4 chip at higher price point"]
        preds = invoke(runtime_client, endpoint_name, texts)
        assert len(preds) == 1
        assert_valid_prediction(preds[0])
        # Business or Sci/Tech is most likely; both are acceptable
        assert preds[0]["label"] in {"Business", "Sci/Tech"}

    def test_batch_of_four(self, runtime_client, endpoint_name):
        texts = [
            "Brazil defeats Argentina 2-1 in Copa America semifinal",
            "Central bank cuts rates by 50 basis points to stimulate growth",
            "New COVID-19 variant detected in Southeast Asia draws WHO attention",
            "Intel releases next-generation AI accelerator chip for data centers",
        ]
        preds = invoke(runtime_client, endpoint_name, texts)
        assert len(preds) == 4
        for pred in preds:
            assert_valid_prediction(pred)
        expected = ["Sports", "Business", "World", "Sci/Tech"]
        for i, (pred, exp) in enumerate(zip(preds, expected)):
            assert pred["label"] == exp, (
                f"Sample {i}: expected '{exp}', got '{pred['label']}' "
                f"(confidence={pred['confidence']:.3f})"
            )


class TestEdgeCaseInputs:
    def test_very_short_input(self, runtime_client, endpoint_name):
        """Single-word inputs should return a valid (possibly low-confidence) prediction."""
        texts = ["Economy"]
        preds = invoke(runtime_client, endpoint_name, texts)
        assert len(preds) == 1
        assert_valid_prediction(preds[0])
        # Confidence will be low; just verify structure

    def test_maximum_length_truncation(self, runtime_client, endpoint_name):
        """~400-word article gets truncated to max_length=128 tokens; must not crash."""
        long_text = (
            "The government announced a sweeping new economic policy today. " * 40
        )
        assert len(long_text.split()) > 300
        texts = [long_text]
        preds = invoke(runtime_client, endpoint_name, texts)
        assert len(preds) == 1
        assert_valid_prediction(preds[0])

    def test_unicode_non_ascii(self, runtime_client, endpoint_name):
        """Unicode and emoji in text should not cause 500 errors."""
        texts = [
            "日本の株式市場は本日、大幅な上昇を記録しました",  # Japanese: Stock market rose
            "Empresa brasileira anuncia fusão com grupo europeu €2B 🇧🇷",
        ]
        preds = invoke(runtime_client, endpoint_name, texts)
        assert len(preds) == 2
        for pred in preds:
            assert_valid_prediction(pred)

    def test_repeated_whitespace_and_newlines(self, runtime_client, endpoint_name):
        """Excessive whitespace should be handled by the tokenizer's normalization."""
        texts = ["    Scientists   discover   new   exoplanet   \n\n   in   Andromeda   "]
        preds = invoke(runtime_client, endpoint_name, texts)
        assert len(preds) == 1
        assert_valid_prediction(preds[0])

    def test_numeric_only_input(self, runtime_client, endpoint_name):
        """Purely numeric input should return a valid, albeit uncertain, prediction."""
        texts = ["12345 67890 11111 99999"]
        preds = invoke(runtime_client, endpoint_name, texts)
        assert len(preds) == 1
        assert_valid_prediction(preds[0])

    def test_special_characters_and_html(self, runtime_client, endpoint_name):
        """HTML entities and special characters should not crash the tokenizer."""
        texts = [
            "<b>Breaking:</b> &amp; stocks fall 3% after &lt;earnings miss&gt; $AAPL",
            "Stock ↑ 12% | Revenue: $4.2B | Growth: 23% YoY — analysts bullish",
        ]
        preds = invoke(runtime_client, endpoint_name, texts)
        assert len(preds) == 2
        for pred in preds:
            assert_valid_prediction(pred)

    def test_mixed_language_code_switch(self, runtime_client, endpoint_name):
        """Code-switching (English + Spanish) tests OOV robustness."""
        texts = ["El presidente announced nuevas políticas económicas para combat inflation"]
        preds = invoke(runtime_client, endpoint_name, texts)
        assert len(preds) == 1
        assert_valid_prediction(preds[0])


class TestBatchSizeBoundaries:
    def test_single_item_batch(self, runtime_client, endpoint_name):
        preds = invoke(runtime_client, endpoint_name, ["NASA launches new telescope"])
        assert len(preds) == 1
        assert_valid_prediction(preds[0])

    def test_max_practical_batch(self, runtime_client, endpoint_name):
        """64-item batch tests container memory and HTTP body size limits."""
        base_text = "Scientists at MIT develop new quantum computing architecture"
        texts = [base_text] * 64
        preds = invoke(runtime_client, endpoint_name, texts)
        assert len(preds) == 64
        for pred in preds:
            assert_valid_prediction(pred)
        # All identical inputs must yield identical predictions
        assert all(p["label"] == preds[0]["label"] for p in preds)
        assert all(abs(p["confidence"] - preds[0]["confidence"]) < 1e-5 for p in preds)

    def test_determinism(self, runtime_client, endpoint_name):
        """Two identical requests must return bit-identical predictions (model in eval mode)."""
        text = ["Inflation rises to 4.2% as energy prices surge globally"]
        pred1 = invoke(runtime_client, endpoint_name, text)[0]
        pred2 = invoke(runtime_client, endpoint_name, text)[0]
        assert pred1["label"] == pred2["label"]
        assert abs(pred1["confidence"] - pred2["confidence"]) < 1e-5, (
            f"Non-deterministic output: {pred1['confidence']} vs {pred2['confidence']}"
        )
```

Execute the full test suite:

```bash
python -m pytest edge_case_tests.py -v --tb=short 2>&1 | tee edge_case_results.txt
```

### 3.3 — Failure Mitigation: Automated Endpoint Health and Rollback

A deployed endpoint can fail silently: the HTTP 200 response code may still arrive while the model returns nonsensical predictions if a corrupted model artifact was deployed or if a container environment variable was misconfigured. The correct mitigation is a continuous health check that validates not just the HTTP status code but the semantic content of predictions against a small golden test set. If health checks fail three consecutive times, the script emits a critical alert requiring manual rollback via update_endpoint(). Create `endpoint_health_check.py`:

```python
#!/usr/bin/env python3
"""
endpoint_health_check.py

Continuous semantic health check for the SageMaker endpoint.
Validates that golden test examples are classified correctly.
Triggers CloudWatch alarm simulation on failure.

Usage:
    python endpoint_health_check.py              # run once
    python endpoint_health_check.py --loop 60   # run every 60 seconds
"""

import argparse
import json
import os
import time
import logging
import sys
import boto3

REGION = os.environ.get("AWS_DEFAULT_REGION", "us-east-1")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

# Golden test set: (text, expected_label)
# These are high-confidence, unambiguous examples drawn from class centroids.
GOLDEN_TESTS = [
    ("Brazil wins FIFA World Cup final against France in penalty shootout", "Sports"),
    ("Federal Reserve announces quarter-point rate hike to combat inflation", "Business"),
    ("Terrorist attack in capital city kills dozens, government declares emergency", "World"),
    ("NVIDIA releases new H200 GPU with 141GB HBM3e memory for AI training", "Sci/Tech"),
    ("LeBron James breaks NBA all-time scoring record in historic night", "Sports"),
    ("Apple reports record quarterly revenue of 97 billion dollars", "Business"),
]

FAILURE_THRESHOLD = 2   # Number of wrong predictions to trigger alert
CONSECUTIVE_FAIL_LIMIT = 3  # Consecutive failed health checks before rollback


def run_health_check(runtime_client, endpoint_name: str) -> dict:
    texts = [t for t, _ in GOLDEN_TESTS]
    expected = [e for _, e in GOLDEN_TESTS]

    try:
        response = runtime_client.invoke_endpoint(
            EndpointName=endpoint_name,
            ContentType="application/json",
            Accept="application/json",
            Body=json.dumps({"texts": texts}).encode("utf-8"),
        )
        preds = json.loads(response["Body"].read())
    except Exception as exc:
        return {
            "status": "ENDPOINT_UNREACHABLE",
            "error": str(exc),
            "passed": 0,
            "failed": len(GOLDEN_TESTS),
            "details": [],
        }

    details = []
    n_failed = 0
    for i, (pred, exp) in enumerate(zip(preds, expected)):
        correct = pred["label"] == exp
        if not correct:
            n_failed += 1
        details.append(
            {
                "text": texts[i][:60],
                "expected": exp,
                "got": pred["label"],
                "confidence": pred["confidence"],
                "correct": correct,
            }
        )

    n_passed = len(GOLDEN_TESTS) - n_failed
    status = "HEALTHY" if n_failed < FAILURE_THRESHOLD else "DEGRADED"

    return {
        "status": status,
        "passed": n_passed,
        "failed": n_failed,
        "details": details,
        "error": None,
    }


def put_cloudwatch_metric(cw_client, endpoint_name: str, health_score: float) -> None:
    """Emit a custom CloudWatch metric for the health score (0.0–1.0)."""
    cw_client.put_metric_data(
        Namespace="SageMaker/EndpointHealth",
        MetricData=[
            {
                "MetricName": "GoldenSetAccuracy",
                "Dimensions": [{"Name": "EndpointName", "Value": endpoint_name}],
                "Value": health_score,
                "Unit": "None",
            }
        ],
    )


def trigger_alert(endpoint_name: str, check_result: dict) -> None:
    logger.error(
        "HEALTH CHECK ALERT: Endpoint '%s' is DEGRADED. "
        "Passed %d/%d golden tests. Failed examples: %s",
        endpoint_name,
        check_result["passed"],
        len(GOLDEN_TESTS),
        [d for d in check_result["details"] if not d["correct"]],
    )
    # In production: publish to SNS, PagerDuty, Slack webhook, etc.


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--loop",
        type=int,
        default=None,
        help="Interval in seconds for continuous checking (omit for single run)",
    )
    args = parser.parse_args()

    with open("endpoint_metadata.json") as f:
        endpoint_name = json.load(f)["endpoint_name"]

    runtime = boto3.client("sagemaker-runtime", region_name=REGION)
    cw = boto3.client("cloudwatch", region_name=REGION)

    consecutive_failures = 0

    def run_once():
        nonlocal consecutive_failures
        result = run_health_check(runtime, endpoint_name)
        health_score = result["passed"] / len(GOLDEN_TESTS)

        try:
            put_cloudwatch_metric(cw, endpoint_name, health_score)
        except Exception as e:
            logger.warning("CloudWatch metric push failed: %s", e)

        if result["status"] == "HEALTHY":
            logger.info(
                "Health check PASSED: %d/%d golden tests correct (score=%.2f)",
                result["passed"], len(GOLDEN_TESTS), health_score,
            )
            consecutive_failures = 0
        else:
            consecutive_failures += 1
            trigger_alert(endpoint_name, result)
            logger.warning(
                "Health check FAILED: %d consecutive failures (threshold=%d)",
                consecutive_failures, CONSECUTIVE_FAIL_LIMIT,
            )

            if consecutive_failures >= CONSECUTIVE_FAIL_LIMIT:
                logger.critical(
                    "CONSECUTIVE FAILURE LIMIT REACHED (%d). "
                    "Manual intervention required: "
                    "1) Check endpoint logs in CloudWatch "
                    "2) Verify model artifact integrity in S3 "
                    "3) Consider rolling back via update_endpoint(). "
                    "Endpoint: %s",
                    CONSECUTIVE_FAIL_LIMIT, endpoint_name,
                )
                # In production: invoke AWS SDK update_endpoint() with previous config

        return result

    if args.loop is None:
        result = run_once()
        sys.exit(0 if result["status"] == "HEALTHY" else 1)
    else:
        logger.info("Starting continuous health check loop (interval=%ds)", args.loop)
        while True:
            run_once()
            time.sleep(args.loop)


if __name__ == "__main__":
    main()
```

```bash
# Single run
python endpoint_health_check.py

# Continuous monitoring every 60 seconds
python endpoint_health_check.py --loop 60
```

### 3.4 — Teardown

Always delete SageMaker endpoints when not in use. An `ml.m5.xlarge` endpoint costs approximately $0.23/hour regardless of traffic. Create `teardown.py`:

```python
#!/usr/bin/env python3
"""
teardown.py

Deletes the SageMaker endpoint and optionally cleans up S3 artifacts.

Usage:
    python teardown.py
    python teardown.py --delete-s3  # also removes S3 artifacts
"""

import argparse
import json
import os
import boto3

REGION = os.environ.get("AWS_DEFAULT_REGION", "us-east-1")
BUCKET = os.environ["S3_BUCKET"]
PREFIX = os.environ["S3_PREFIX"]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--delete-s3", action="store_true", help="Delete S3 artifacts")
    args = parser.parse_args()

    sm = boto3.client("sagemaker", region_name=REGION)

    with open("endpoint_metadata.json") as f:
        endpoint_name = json.load(f)["endpoint_name"]

    print(f"Deleting endpoint: {endpoint_name}")
    sm.delete_endpoint(EndpointName=endpoint_name)

    # Wait for deletion to confirm
    import time
    for _ in range(30):
        try:
            sm.describe_endpoint(EndpointName=endpoint_name)
            print("  Waiting for deletion...")
            time.sleep(10)
        except sm.exceptions.ClientError:
            print(f"  Endpoint {endpoint_name} deleted.")
            break

    if args.delete_s3:
        s3 = boto3.client("s3", region_name=REGION)
        paginator = s3.get_paginator("list_objects_v2")
        deleted = 0
        for page in paginator.paginate(Bucket=BUCKET, Prefix=PREFIX):
            objects = [{"Key": obj["Key"]} for obj in page.get("Contents", [])]
            if objects:
                s3.delete_objects(Bucket=BUCKET, Delete={"Objects": objects})
                deleted += len(objects)
        print(f"Deleted {deleted} S3 objects under s3://{BUCKET}/{PREFIX}/")

    print("Teardown complete.")


if __name__ == "__main__":
    main()
```

```bash
python teardown.py
```

---

## ML Diagnostic Cheat Sheet & Verification Checklist

### Quick Diagnostic Commands

Verify your AWS session is live and resolves the correct account identity before submitting any job:

```bash
aws sts get-caller-identity
aws sagemaker list-training-jobs --max-results 5 --sort-by CreationTime --sort-order Descending
aws sagemaker describe-endpoint --endpoint-name $(python -c "import json; print(json.load(open('endpoint_metadata.json'))['endpoint_name'])")
```

Tail CloudWatch logs for a training job in real time (requires `awslogs` or the AWS CLI log streaming):

```bash
aws logs tail /aws/sagemaker/TrainingJobs \
    --log-stream-name-prefix $(python -c "import json; print(json.load(open('training_job_metadata.json'))['job_name'])") \
    --follow
```

Inspect the model artifact structure inside the `.tar.gz` without downloading the full file:

```bash
MODEL_S3=$(python -c "import json; print(json.load(open('training_job_metadata.json'))['model_artifact_s3'])")
aws s3 cp $MODEL_S3 /tmp/model.tar.gz && tar -tzf /tmp/model.tar.gz | head -30
```

Check endpoint invocation metrics directly from CloudWatch:

```bash
aws cloudwatch get-metric-statistics \
    --namespace AWS/SageMaker \
    --metric-name Invocations \
    --dimensions Name=EndpointName,Value=$(python -c "import json; print(json.load(open('endpoint_metadata.json'))['endpoint_name'])") \
                 Name=VariantName,Value=AllTraffic \
    --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%SZ 2>/dev/null || date -u -v-1H +%Y-%m-%dT%H:%M:%SZ) \
    --end-time $(date -u +%Y-%m-%dT%H:%M:%SZ) \
    --period 300 \
    --statistics Sum
```

### Verification Checklist

The following checklist maps every critical invariant in these labs to a concrete, scriptable verification step. Work through it in order after completing each exercise.

**Data Pipeline Integrity**

Confirm that S3 object tags contain the `sha256` checksum and that the computed hash of the downloaded file matches. A mismatch indicates S3 upload corruption, an S3 replication issue, or a data-at-rest integrity failure. Run `python prepare_dataset.py` and inspect the printed checksums against the S3 object tags to verify they are identical.

**Training Job Completion and Metric Emission**

After `submit_training_job.py` exits, check that `training_job_metadata.json` exists and that the `model_artifact_s3` URI points to a non-zero-size `.tar.gz` object in S3. Verify that the job status is `Completed` (not `Failed` or `Stopped`) by running `aws sagemaker describe-training-job --training-job-name <name> --query 'TrainingJobStatus'`.

**HPO Convergence**

After `hpo_job.py`, run `python analyze_hpo.py` and confirm that `val_macro_f1` is monotonically non-decreasing across the top-5 trials sorted by submission time. If convergence plateaus or improvement slows, increase `max_jobs` beyond 12 to at least 20 for real-world HPO campaigns.

**Endpoint Health Baseline**

Before stress testing, run `python endpoint_health_check.py` and verify 6/6 golden tests pass. If fewer than 6 pass, the model deployment is faulty: check whether `best_model/` was saved correctly by verifying that `config.json` exists inside the model artifact via `tar -tzf /tmp/model.tar.gz | grep config.json`.

**Latency Regression Gate**

After any re-deployment, run `python eval_pipeline.py --benchmark --batch-size 32` and confirm that `sample_p99_ms` is below 50ms for `ml.m5.xlarge` CPU inference. Values above 100ms indicate container resource contention, an oversized batch, or an inference script regression. Use `torch.cuda.memory_summary()` on GPU instances to rule out VRAM pressure.

**Determinism Under Load**

Run the `test_determinism` test from `edge_case_tests.py` both before and after the stress test to confirm that the endpoint's model weights were not modified in-place (a theoretical risk if `model.train()` was accidentally called in `inference.py`). The test verifies confidence values match to within `1e-5`.

**Cost Verification**

After teardown, confirm the endpoint is no longer billed by checking `aws sagemaker describe-endpoint` returns a `ClientError` with code `ValidationException`. Confirm S3 storage costs by listing remaining objects: any residual `.tar.gz` files in the `model-artifacts/` prefix continue to incur S3 storage charges at approximately $0.023/GB/month.

---

| Diagnostic | Command / Script | Expected Result |
|---|---|---|
| AWS credential validity | `aws sts get-caller-identity` | Returns account ID, user ARN |
| S3 upload integrity | `python prepare_dataset.py` (checksum output) | Local SHA-256 == S3 object tag |
| Training job status | `aws sagemaker describe-training-job` | `TrainingJobStatus: Completed` |
| Endpoint in service | `aws sagemaker describe-endpoint` | `EndpointStatus: InService` |
| Semantic health check | `python endpoint_health_check.py` | `6/6 golden tests correct` |
| Full evaluation | `python eval_pipeline.py --benchmark` | `accuracy >= 0.930`, `macro_f1 >= 0.928` |
| Stress test saturation | `python stress_test.py` | `p99 < 2000ms at concurrency ≤ 8` |
| Edge cases | `python -m pytest edge_case_tests.py -v` | All 11 tests pass |
| HPO best F1 | `python analyze_hpo.py` | `best val_macro_f1 >= 0.930` |
| Endpoint teardown | `python teardown.py` then `aws sagemaker describe-endpoint` | `ClientError: ValidationException` |

The end-to-end pipeline you have built in these labs represents the operational core of production ML deployment on SageMaker: reproducible data staging with integrity verification, instrumented training jobs that emit HPO-compatible metrics, Bayesian hyperparameter search, real-time endpoint deployment with structured inference contracts, adversarial and boundary-condition test coverage, and continuous semantic health monitoring. Every component is independently verifiable, which is the property that makes the system maintainable — not by its author, but by any engineer who inherits it six months from now.
