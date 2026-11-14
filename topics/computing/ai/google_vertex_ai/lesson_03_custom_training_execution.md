# Lesson 3: Custom Training Execution

## 1. First-Principles Intuition & Invariants

The history of large-scale machine learning is, at its core, a history of compute orchestration. When a model fits on a single GPU and trains in minutes, the machinery of distributed execution is invisible: you write a training loop, call `model.fit()`, and the hardware obliges. The moment your model grows beyond a single accelerator's memory budget, or your dataset requires days of single-device training, the abstraction collapses. What remains is the raw problem: how do you decompose a mathematical computation across dozens or hundreds of heterogeneous accelerators, synchronize state correctly, tolerate partial failures, and do all of this without writing a distributed systems framework from scratch?

Google Vertex AI's Custom Training service is the answer to that question at production scale. It is not a managed notebook, nor a drag-and-drop AutoML pipeline. It is an infrastructure layer that accepts a containerized training workload and schedules it across Google's accelerator fleet — A100s, V100s, TPU v4 pods, and beyond — with a job orchestration model that separates *what* your training code does from *where* and *how* it runs. This separation is the central invariant of the entire system, and understanding it deeply changes how you architect training pipelines.

The fundamental abstraction Vertex AI enforces is the **Custom Job**, which maps your training code, its hardware requirements, and its runtime environment into a single declarative unit. This declarative model is not incidental. It allows the Vertex AI control plane to schedule, preempt, restart, and parallelize your workload without coupling itself to the semantics of your training loop. Your container is a black box; the platform concerns itself only with the resource graph, the environment variables it injects, and the lifecycle events it emits. This design philosophy — borrowed from Kubernetes but extended with accelerator-aware scheduling — means you can reason about training jobs as state machines: `PENDING` → `RUNNING` → `SUCCEEDED` or `FAILED`, with a well-defined set of transitions and observable signals at each boundary.

Three first-principles invariants govern every serious custom training deployment on Vertex AI. The first is **hermeticity**: your training container must be entirely self-contained, carrying its own Python runtime, library dependencies, and entrypoint. It should produce the same result when run locally on a single GPU as when run on a 64-node distributed cluster, modulo the parallelism strategy. Any external dependency that isn't expressed in the container image or mounted via Cloud Storage is a latent failure waiting to surface at hour 47 of a 48-hour training run. The second invariant is **checkpoint atomicity**: because Vertex AI can preempt spot (preemptible) training workers, your loop must write checkpoints to Cloud Storage in a transactionally safe manner. A partial checkpoint written during a preemption is worse than no checkpoint at all; it corrupts your recovery path. The third invariant is **rank-awareness**: in any distributed training configuration, each worker must know its global rank, its local rank, and the total world size. Vertex AI injects this topology via environment variables, but your code must consume them correctly, or gradient synchronization breaks silently — the worst class of distributed training bug, because the model continues to train but on increasingly inconsistent gradient estimates.

The computational reason distributed training is hard reduces to one equation. In synchronous data-parallel training, the theoretical speedup from $N$ workers is $N$, but the practical speedup is bounded by Amdahl's Law and by the communication overhead of averaging gradients across the ring. If your all-reduce communication takes time $T_{comm}$ and your forward-backward pass takes $T_{compute}$, your efficiency is $T_{compute} / (T_{compute} + T_{comm})$. As models grow deeper and wider, $T_{compute}$ grows with the floating-point operation count, but $T_{comm}$ grows with parameter count. For large language models where parameter counts reach hundreds of billions, this ratio collapses unless you employ topology-aware communication (NCCL over NVLink, TPU ICI fabric) and overlap computation with communication through asynchronous gradient prefetching. Vertex AI's infrastructure is designed around this constraint: the accelerators it provisions for multi-worker jobs are colocated in the same datacenter zone, connected via Google's Jupiter network fabric at bandwidths that can sustain the all-reduce traffic of large model training.

---

## 2. Core Architecture & Mechanics

### The Custom Job Execution Model

A Vertex AI Custom Training Job is specified as a `CustomJobSpec` containing one or more `WorkerPoolSpec` objects. This is not a cosmetic API choice. The worker pool model directly reflects the logical topology of distributed training: a chief worker that coordinates checkpointing and logging, a set of homogeneous compute workers, a parameter server pool for asynchronous training, and an evaluator. Each pool specifies its machine type, accelerator configuration, replica count, and container specification independently. This means you can, and often should, give your parameter servers CPU-only `n1-highmem-16` machines while your workers run on `a2-highgpu-8g` nodes with eight A100s each.

```
┌─────────────────────────────────────────────────────────────────┐
│                    Vertex AI Control Plane                      │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                   CustomJobSpec                           │  │
│  │                                                           │  │
│  │  ┌─────────────────┐    ┌─────────────────────────────┐  │  │
│  │  │  WorkerPoolSpec │    │      WorkerPoolSpec         │  │  │
│  │  │  (Chief / 0)    │    │      (Workers / 1)          │  │  │
│  │  │                 │    │                             │  │  │
│  │  │  replica: 1     │    │  replica: 8                 │  │  │
│  │  │  a2-highgpu-1g  │    │  a2-highgpu-8g              │  │  │
│  │  │  1x A100        │    │  8x A100 each               │  │  │
│  │  │  container: gcr │    │  container: gcr             │  │  │
│  │  └────────┬────────┘    └──────────────┬──────────────┘  │  │
│  └───────────│─────────────────────────────│─────────────────┘  │
└──────────────│─────────────────────────────│─────────────────────┘
               │  TF_CONFIG / MASTER_ADDR    │
               │  Injected via env vars      │
               ▼                             ▼
     ┌──────────────────┐         ┌──────────────────────────┐
     │   Chief Worker   │◄────────│     Worker Nodes (x8)    │
     │   Rank 0         │ AllReduce│     Rank 1–8             │
     │   Checkpoint IO  │◄────────│     Gradient Sync        │
     └──────────────────┘ NCCL   └──────────────────────────┘
              │
              ▼
     ┌────────────────┐
     │  Cloud Storage │
     │  (GCS Bucket)  │
     │  Checkpoints   │
     │  Artifacts     │
     └────────────────┘
```

When you submit a Custom Job, the Vertex AI control plane resolves the worker pool topology, provisions the VMs via GCE, pulls your container images from Artifact Registry, and injects the distributed training environment. For TensorFlow workloads, it populates the `TF_CONFIG` JSON environment variable on each worker, encoding the cluster specification and the current worker's task type and index. For PyTorch workloads using `torch.distributed`, it injects `MASTER_ADDR`, `MASTER_PORT`, `WORLD_SIZE`, and `RANK`. Your training code reads these at startup to initialize the process group and begin collective communication.

The clean Python SDK for constructing this job looks as follows. Notice that every field is explicitly specified — no reliance on defaults that could silently change between SDK versions:

```python
# vertex_custom_job.py
# Requires: google-cloud-aiplatform>=1.38.0, Python 3.10+
# Usage: python vertex_custom_job.py --project my-project --region us-central1

import argparse
from google.cloud import aiplatform
from google.cloud.aiplatform import gapic as aip_gapic

def submit_distributed_training_job(project: str, region: str, staging_bucket: str):
    aiplatform.init(project=project, location=region, staging_bucket=staging_bucket)

    # Define the container specification shared across all worker pools.
    # The image must exist in Artifact Registry before job submission.
    container_spec = aip_gapic.ContainerSpec(
        image_uri=f"us-central1-docker.pkg.dev/{project}/training/resnet-trainer:v1.4.2",
        command=["python", "-m", "trainer.task"],
        args=[
            "--epochs=120",
            "--batch-size=256",
            "--learning-rate=0.1",
            "--output-dir=gs://my-training-bucket/jobs/resnet50-run-001/",
            "--checkpoint-dir=gs://my-training-bucket/checkpoints/resnet50-run-001/",
            "--data-dir=gs://my-training-data/imagenet/tfrecords/",
        ],
        env=[
            aip_gapic.EnvVar(name="NCCL_DEBUG", value="INFO"),
            aip_gapic.EnvVar(name="NCCL_SOCKET_IFNAME", value="eth0"),
            aip_gapic.EnvVar(name="OMP_NUM_THREADS", value="8"),
        ],
    )

    # Chief worker: coordinates checkpointing, runs evaluation, writes summaries.
    chief_pool = aip_gapic.WorkerPoolSpec(
        machine_spec=aip_gapic.MachineSpec(
            machine_type="a2-highgpu-1g",
            accelerator_type=aip_gapic.AcceleratorType.NVIDIA_TESLA_A100,
            accelerator_count=1,
        ),
        replica_count=1,
        container_spec=container_spec,
        disk_spec=aip_gapic.DiskSpec(
            boot_disk_type="pd-ssd",
            boot_disk_size_gb=200,
        ),
    )

    # Worker pool: data-parallel compute nodes, each with 8x A100 for intra-node NVLink.
    worker_pool = aip_gapic.WorkerPoolSpec(
        machine_spec=aip_gapic.MachineSpec(
            machine_type="a2-highgpu-8g",
            accelerator_type=aip_gapic.AcceleratorType.NVIDIA_TESLA_A100,
            accelerator_count=8,
        ),
        replica_count=8,
        container_spec=container_spec,
        disk_spec=aip_gapic.DiskSpec(
            boot_disk_type="pd-ssd",
            boot_disk_size_gb=500,
        ),
    )

    custom_job = aiplatform.CustomJob(
        display_name="resnet50-imagenet-distributed-v1.4.2",
        worker_pool_specs=[chief_pool, worker_pool],
        base_output_dir=f"gs://my-training-bucket/jobs/resnet50-run-001/",
    )

    custom_job.run(
        service_account="vertex-training-sa@my-project.iam.gserviceaccount.com",
        network="projects/123456789/global/networks/vertex-training-vpc",
        timeout=86400,  # 24-hour wall-clock timeout
        restart_job_on_worker_restart=True,
        enable_web_access=False,
    )

    print(f"Job resource name: {custom_job.resource_name}")
    return custom_job.resource_name


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", required=True)
    parser.add_argument("--region", default="us-central1")
    parser.add_argument("--staging-bucket", required=True)
    args = parser.parse_args()
    submit_distributed_training_job(args.project, args.region, args.staging_bucket)
```

### Distributed Training Strategies: Data, Model, and Pipeline Parallelism

The choice of parallelism strategy is not aesthetic — it is a direct function of your model's arithmetic intensity and your accelerator's memory capacity relative to model size.

**Data parallelism** is the simplest and most broadly applicable strategy. Each worker holds a complete replica of the model in its accelerator memory. The global minibatch is sharded across workers: if your batch size is 2048 and you have 64 GPUs, each GPU processes 32 samples per step. After each backward pass, gradients are averaged across all workers via an all-reduce collective. The model weights are then updated identically on every worker, maintaining consistency. PyTorch's `DistributedDataParallel` (DDP) implements this with bucketed gradient communication, where gradients are grouped into buckets that begin their all-reduce as soon as the backward pass populates them, overlapping the remaining backward computation with network communication. This overlap is the single most important optimization in data-parallel training and can recover 15–30% of wall-clock time for large models.

The following training task module demonstrates a production-grade PyTorch distributed training loop designed to execute correctly when launched by Vertex AI:

```python
# trainer/task.py
# Complete, executable distributed training entrypoint for Vertex AI Custom Jobs.
# Handles: rank initialization, GCS checkpointing, TensorBoard logging, graceful NCCL teardown.

import argparse
import os
import time
import logging
import torch
import torch.distributed as dist
import torch.nn as nn
from torch.nn.parallel import DistributedDataParallel as DDP
from torch.utils.data import DataLoader, DistributedSampler
from torch.utils.tensorboard import SummaryWriter
from torchvision import datasets, models, transforms
from google.cloud import storage

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def parse_args():
    parser = argparse.ArgumentParser(description="Distributed ResNet-50 Training on Vertex AI")
    parser.add_argument("--epochs", type=int, default=90)
    parser.add_argument("--batch-size", type=int, default=256)
    parser.add_argument("--learning-rate", type=float, default=0.1)
    parser.add_argument("--weight-decay", type=float, default=1e-4)
    parser.add_argument("--momentum", type=float, default=0.9)
    parser.add_argument("--warmup-epochs", type=int, default=5)
    parser.add_argument("--checkpoint-interval", type=int, default=5)
    parser.add_argument("--output-dir", type=str, required=True)
    parser.add_argument("--checkpoint-dir", type=str, required=True)
    parser.add_argument("--data-dir", type=str, required=True)
    parser.add_argument("--num-workers", type=int, default=8)
    return parser.parse_args()


def gcs_upload(local_path: str, gcs_uri: str):
    """Upload a local file to a GCS path atomically via a tmp-then-rename pattern."""
    client = storage.Client()
    # Parse gs://bucket/blob/path
    without_prefix = gcs_uri[len("gs://"):]
    bucket_name, blob_path = without_prefix.split("/", 1)
    bucket = client.bucket(bucket_name)
    # Write to a tmp blob first, then copy to final destination for atomicity.
    tmp_blob_path = blob_path + ".tmp"
    tmp_blob = bucket.blob(tmp_blob_path)
    tmp_blob.upload_from_filename(local_path)
    # Compose copy (server-side rename)
    final_blob = bucket.blob(blob_path)
    bucket.copy_blob(tmp_blob, bucket, blob_path)
    tmp_blob.delete()
    logger.info(f"Uploaded {local_path} → {gcs_uri}")


def gcs_download(gcs_uri: str, local_path: str) -> bool:
    """Download a GCS blob to a local path. Returns False if the blob does not exist."""
    client = storage.Client()
    without_prefix = gcs_uri[len("gs://"):]
    bucket_name, blob_path = without_prefix.split("/", 1)
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_path)
    if not blob.exists():
        return False
    blob.download_to_filename(local_path)
    logger.info(f"Downloaded {gcs_uri} → {local_path}")
    return True


def setup_distributed():
    """
    Initialize the torch.distributed process group using environment variables
    injected by Vertex AI. MASTER_ADDR, MASTER_PORT, WORLD_SIZE, and RANK are
    set automatically for multi-worker CustomJob deployments.
    """
    rank = int(os.environ.get("RANK", 0))
    local_rank = int(os.environ.get("LOCAL_RANK", 0))
    world_size = int(os.environ.get("WORLD_SIZE", 1))
    master_addr = os.environ.get("MASTER_ADDR", "localhost")
    master_port = os.environ.get("MASTER_PORT", "12355")

    os.environ["MASTER_ADDR"] = master_addr
    os.environ["MASTER_PORT"] = master_port

    dist.init_process_group(
        backend="nccl",        # NCCL for GPU-to-GPU collective communication
        init_method="env://",
        world_size=world_size,
        rank=rank,
    )

    torch.cuda.set_device(local_rank)
    logger.info(f"Process group initialized: rank={rank}, local_rank={local_rank}, world_size={world_size}")
    return rank, local_rank, world_size


def build_model(num_classes: int = 1000) -> nn.Module:
    model = models.resnet50(weights=None)
    model.fc = nn.Linear(model.fc.in_features, num_classes)
    return model


def cosine_schedule_with_warmup(optimizer, warmup_epochs: int, total_epochs: int, steps_per_epoch: int):
    """Linear warmup for `warmup_epochs`, then cosine decay to 0."""
    total_steps = total_epochs * steps_per_epoch
    warmup_steps = warmup_epochs * steps_per_epoch

    def lr_lambda(step: int) -> float:
        if step < warmup_steps:
            return float(step) / float(max(1, warmup_steps))
        progress = float(step - warmup_steps) / float(max(1, total_steps - warmup_steps))
        import math
        return max(0.0, 0.5 * (1.0 + math.cos(math.pi * progress)))

    return torch.optim.lr_scheduler.LambdaLR(optimizer, lr_lambda)


def save_checkpoint(state: dict, epoch: int, checkpoint_dir: str, rank: int):
    """Only the chief (rank 0) writes checkpoints to avoid GCS write contention."""
    if rank != 0:
        return
    local_path = f"/tmp/checkpoint_epoch_{epoch:04d}.pt"
    torch.save(state, local_path)
    gcs_path = f"{checkpoint_dir.rstrip('/')}/checkpoint_epoch_{epoch:04d}.pt"
    gcs_upload(local_path, gcs_path)
    # Always maintain a 'latest' pointer for fast resume.
    latest_local = "/tmp/checkpoint_latest.pt"
    torch.save(state, latest_local)
    gcs_upload(latest_local, f"{checkpoint_dir.rstrip('/')}/checkpoint_latest.pt")


def load_latest_checkpoint(checkpoint_dir: str, model: nn.Module, optimizer: torch.optim.Optimizer,
                            scheduler, local_rank: int) -> int:
    """Resume from the latest checkpoint in GCS if it exists. Returns the starting epoch."""
    gcs_latest = f"{checkpoint_dir.rstrip('/')}/checkpoint_latest.pt"
    local_path = "/tmp/checkpoint_latest.pt"
    if not gcs_download(gcs_latest, local_path):
        logger.info("No checkpoint found. Training from scratch.")
        return 0
    map_location = {"cuda:0": f"cuda:{local_rank}"}
    state = torch.load(local_path, map_location=map_location)
    model.load_state_dict(state["model"])
    optimizer.load_state_dict(state["optimizer"])
    scheduler.load_state_dict(state["scheduler"])
    start_epoch = state["epoch"] + 1
    logger.info(f"Resumed from checkpoint at epoch {state['epoch']}. Continuing from epoch {start_epoch}.")
    return start_epoch


def train(args):
    rank, local_rank, world_size = setup_distributed()
    device = torch.device(f"cuda:{local_rank}")

    # Build model and wrap in DDP. find_unused_parameters=False is critical for performance
    # and correctness when all parameters participate in every forward pass.
    model = build_model(num_classes=1000).to(device)
    model = DDP(model, device_ids=[local_rank], output_device=local_rank, find_unused_parameters=False)

    optimizer = torch.optim.SGD(
        model.parameters(),
        lr=args.learning_rate,
        momentum=args.momentum,
        weight_decay=args.weight_decay,
        nesterov=True,
    )
    criterion = nn.CrossEntropyLoss(label_smoothing=0.1).to(device)

    # Datasets: each worker reads its own shard; DistributedSampler partitions indices.
    normalize = transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    train_transform = transforms.Compose([
        transforms.RandomResizedCrop(224),
        transforms.RandomHorizontalFlip(),
        transforms.ToTensor(),
        normalize,
    ])
    # In production, replace ImageFolder with a GCS-aware dataset (e.g., TFRecord loader
    # or a custom WebDataset loader reading shards from GCS via FUSE mount).
    train_dataset = datasets.ImageFolder(root=f"{args.data_dir}/train", transform=train_transform)
    train_sampler = DistributedSampler(train_dataset, num_replicas=world_size, rank=rank, shuffle=True)
    train_loader = DataLoader(
        train_dataset,
        batch_size=args.batch_size // world_size,  # Per-worker batch size
        sampler=train_sampler,
        num_workers=args.num_workers,
        pin_memory=True,
        persistent_workers=True,
    )

    steps_per_epoch = len(train_loader)
    scheduler = cosine_schedule_with_warmup(optimizer, args.warmup_epochs, args.epochs, steps_per_epoch)

    start_epoch = load_latest_checkpoint(args.checkpoint_dir, model.module, optimizer, scheduler, local_rank)

    # TensorBoard writer: only rank 0 writes summaries to avoid duplicate events.
    writer = SummaryWriter(log_dir=f"/tmp/tb_logs") if rank == 0 else None

    for epoch in range(start_epoch, args.epochs):
        train_sampler.set_epoch(epoch)  # Reseed sampler per epoch for correct shuffling
        model.train()

        epoch_loss = 0.0
        epoch_correct = 0
        epoch_total = 0
        t0 = time.time()

        for step, (images, labels) in enumerate(train_loader):
            images = images.to(device, non_blocking=True)
            labels = labels.to(device, non_blocking=True)

            optimizer.zero_grad(set_to_none=True)  # set_to_none avoids memset overhead
            with torch.amp.autocast(device_type="cuda", dtype=torch.float16):
                outputs = model(images)
                loss = criterion(outputs, labels)

            # GradScaler handles fp16 gradient unscaling and overflow detection.
            scaler.scale(loss).backward()
            scaler.unscale_(optimizer)
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            scaler.step(optimizer)
            scaler.update()
            scheduler.step()

            with torch.no_grad():
                epoch_loss += loss.item()
                preds = outputs.argmax(dim=1)
                epoch_correct += (preds == labels).sum().item()
                epoch_total += labels.size(0)

            global_step = epoch * steps_per_epoch + step
            if rank == 0 and step % 50 == 0:
                lr_now = scheduler.get_last_lr()[0]
                logger.info(f"[Epoch {epoch}/{args.epochs}][Step {step}/{steps_per_epoch}] "
                            f"Loss: {loss.item():.4f} | LR: {lr_now:.6f}")
                if writer:
                    writer.add_scalar("train/loss", loss.item(), global_step)
                    writer.add_scalar("train/lr", lr_now, global_step)

        epoch_time = time.time() - t0
        avg_loss = epoch_loss / steps_per_epoch
        accuracy = epoch_correct / epoch_total

        if rank == 0:
            logger.info(f"Epoch {epoch} complete | Loss: {avg_loss:.4f} | "
                        f"Accuracy: {accuracy:.4f} | Time: {epoch_time:.1f}s")
            if writer:
                writer.add_scalar("train/epoch_loss", avg_loss, epoch)
                writer.add_scalar("train/epoch_accuracy", accuracy, epoch)

        if rank == 0 and (epoch + 1) % args.checkpoint_interval == 0:
            save_checkpoint({
                "epoch": epoch,
                "model": model.module.state_dict(),
                "optimizer": optimizer.state_dict(),
                "scheduler": scheduler.state_dict(),
                "loss": avg_loss,
            }, epoch, args.checkpoint_dir, rank)

    # Final model export
    if rank == 0:
        final_model_path = "/tmp/model_final.pt"
        torch.save(model.module.state_dict(), final_model_path)
        gcs_upload(final_model_path, f"{args.output_dir.rstrip('/')}/model_final.pt")
        if writer:
            writer.close()

    dist.destroy_process_group()
    logger.info("Training complete.")


if __name__ == "__main__":
    args = parse_args()
    scaler = torch.cuda.amp.GradScaler()
    train(args)
```

**Model parallelism** becomes necessary when a single model layer, or a collection of them, exceeds single-accelerator memory. The canonical case is a transformer language model with hundreds of billions of parameters. In tensor parallelism, the weight matrix of each attention head or MLP block is split across a row or column dimension across multiple GPUs. Matrix-vector multiply becomes a partial computation on each GPU, followed by an all-reduce across the tensor-parallel group. Megatron-LM pioneered this approach, and it remains the standard for GPT-class models. Vertex AI's integration with Megatron and DeepSpeed means you can run tensor-parallel jobs by configuring the worker pool replicas to match your tensor-parallel degree and providing the appropriate launcher flags.

**Pipeline parallelism** partitions the model's layer sequence across devices, treating the forward and backward passes as micro-batch streams through a pipeline of stages. Each stage holds a contiguous block of layers. A microbatch flows forward through stage 0, its activations are passed to stage 1, and so on until stage N produces the loss. Gradients flow backward through the same pipeline. The key challenge is bubble overhead: the first and last stages are idle while intermediate stages are filling. GPipe addresses this by increasing the number of microbatches per minibatch so that the pipeline is nearly always full. PipeDream addresses it by allowing different microbatches to be in different pipeline stages simultaneously, at the cost of weight staleness that must be managed carefully. In practice, pipeline parallelism is combined with both data and tensor parallelism in a 3D parallelism configuration, where the total worker count equals `data_parallel_degree × tensor_parallel_degree × pipeline_parallel_degree`.

### TPU Training on Vertex AI

Training on Cloud TPU v4 Pods through Vertex AI follows a structurally similar job submission model, but the execution mechanics differ substantially. TPU workers communicate via the **Interconnect** (ICI) fabric, which is a custom high-bandwidth, low-latency torus network internal to the TPU pod. All-reduce operations on this fabric operate at measured bandwidths exceeding 1.2 Tbps inside a v4 pod, which is roughly two orders of magnitude faster than GPU clusters connected via Ethernet. This bandwidth changes the communication-to-computation ratio fundamentally: on a TPU pod, gradient synchronization is rarely the bottleneck. Data ingestion and preprocessing become the dominant constraint.

The XLA compiler, which underlies both TensorFlow's `tf.function` and JAX's JIT compilation on TPU, converts your computation into a hardware-optimized HLO (High-Level Operations) graph. XLA performs operation fusion, layout assignment (determining the optimal tensor memory layout for TPU matrix units), and rematerialization (recomputing activations during the backward pass rather than storing them, to reduce HBM pressure). This means that the same Python model code can produce materially different HLO graphs depending on how you annotate it, and understanding the XLA compilation pipeline is not academic knowledge for TPU practitioners — it directly determines throughput.

```python
# tpu_training_vertex.py
# Submits a TPU v4-32 Custom Job to Vertex AI using the Python SDK.
# Requires a TPU-compatible container image with JAX or TensorFlow configured for TPU.

from google.cloud import aiplatform
from google.cloud.aiplatform import gapic as aip_gapic


def submit_tpu_training_job(project: str, region: str):
    aiplatform.init(project=project, location=region)

    tpu_container_spec = aip_gapic.ContainerSpec(
        image_uri=f"us-central1-docker.pkg.dev/{project}/training/jax-trainer-tpu:v2.1.0",
        command=["python", "-m", "trainer.tpu_task"],
        args=[
            "--epochs=50",
            "--global-batch-size=4096",
            "--learning-rate=1e-3",
            "--output-dir=gs://my-training-bucket/tpu-jobs/bert-large-001/",
            "--checkpoint-dir=gs://my-training-bucket/tpu-checkpoints/bert-large-001/",
            "--data-dir=gs://my-training-data/c4/tfrecords/",
            "--model-name=bert-large-uncased",
        ],
    )

    # TPU v4-32 provides 32 TPU cores (8 chips × 4 cores per chip) across 4 TPU VMs.
    # Each VM in the worker pool drives 8 TPU cores via the TPU runtime.
    tpu_worker_pool = aip_gapic.WorkerPoolSpec(
        machine_spec=aip_gapic.MachineSpec(
            machine_type="cloud-tpu",
            accelerator_type=aip_gapic.AcceleratorType.TPU_V4,
            accelerator_count=32,  # Total TPU cores; Vertex maps this to the right pod slice
        ),
        replica_count=4,
        container_spec=tpu_container_spec,
        disk_spec=aip_gapic.DiskSpec(
            boot_disk_type="pd-ssd",
            boot_disk_size_gb=200,
        ),
    )

    custom_job = aiplatform.CustomJob(
        display_name="bert-large-tpu-v4-32-pretraining-v2.1.0",
        worker_pool_specs=[tpu_worker_pool],
        base_output_dir="gs://my-training-bucket/tpu-jobs/bert-large-001/",
    )

    custom_job.run(
        service_account="vertex-tpu-sa@my-project.iam.gserviceaccount.com",
        network="projects/123456789/global/networks/vertex-training-vpc",
        timeout=172800,  # 48-hour timeout for pretraining runs
        restart_job_on_worker_restart=True,
    )

    return custom_job.resource_name
```

### Hyperparameter Tuning with Vertex AI Vizier

Vertex AI Hyperparameter Tuning wraps Vertex AI Vizier, Google's internal Bayesian optimization service, as a first-class job type. Rather than running grid or random search over the hyperparameter space, Vizier models the objective surface as a Gaussian Process and selects trial parameter combinations that maximize expected improvement over the current optimum. This reduces the number of trials required to reach a near-optimal configuration by an order of magnitude compared to grid search for high-dimensional spaces.

The integration mechanism is elegant. You define a `HyperparameterTuningJob` with a search space and an objective metric name. Each trial is a full Custom Job execution. Your training code reports the metric to Vertex AI via the `google.cloud.aiplatform.hyperparameter_tuning` module, which writes it to a JSON file in a path that Vertex's metric collection agent reads at the end of each trial. The controlling job terminates trials early if they diverge from the current Pareto front, via a median stopping rule or a custom early stopping callback.

```python
# hparam_tuning_job.py
# Vertex AI Hyperparameter Tuning job submission.
# The training container must call aiplatform.log_metrics() or write to AIP_HP_METRIC_TAG path.

from google.cloud import aiplatform
from google.cloud.aiplatform import hyperparameter_tuning as hpt


def submit_hparam_job(project: str, region: str):
    aiplatform.init(project=project, location=region)

    # Define the hyperparameter search space. Vertex Vizier supports:
    # DoubleParameterSpec, IntegerParameterSpec, CategoricalParameterSpec, DiscreteParameterSpec.
    parameter_spec = {
        "learning_rate": hpt.DoubleParameterSpec(min=1e-5, max=1e-1, scale="log"),
        "weight_decay": hpt.DoubleParameterSpec(min=1e-6, max=1e-2, scale="log"),
        "batch_size": hpt.DiscreteParameterSpec(values=[64, 128, 256, 512], scale="linear"),
        "dropout_rate": hpt.DoubleParameterSpec(min=0.0, max=0.5, scale="linear"),
        "warmup_steps_ratio": hpt.DoubleParameterSpec(min=0.01, max=0.1, scale="linear"),
    }

    # The metric name must match the key passed to aiplatform.log_metrics() inside the container.
    metric_spec = {"val_accuracy": "maximize"}

    # Worker pool for each trial. Keep this modest: tuning explores many configurations,
    # so single-node trials with 1–2 GPUs maximize trial throughput per dollar.
    worker_pool_spec = [{
        "machine_spec": {
            "machine_type": "n1-standard-8",
            "accelerator_type": "NVIDIA_TESLA_T4",
            "accelerator_count": 2,
        },
        "replica_count": 1,
        "container_spec": {
            "image_uri": f"us-central1-docker.pkg.dev/{project}/training/hparam-trainer:v1.0.0",
            "command": ["python", "-m", "trainer.hparam_task"],
            "args": [
                "--output-dir=gs://my-training-bucket/hparam-trials/",
                "--data-dir=gs://my-training-data/cifar10/",
                "--epochs=30",
            ],
        },
    }]

    tuning_job = aiplatform.HyperparameterTuningJob(
        display_name="resnet50-cifar10-vizier-tuning-v1.0.0",
        custom_job=aiplatform.CustomJob.from_local_script(
            display_name="trial-worker",
            script_path="trainer/hparam_task.py",
            container_uri=f"us-central1-docker.pkg.dev/{project}/training/hparam-trainer:v1.0.0",
            requirements=["torch==2.1.0", "torchvision==0.16.0", "google-cloud-aiplatform>=1.38.0"],
            machine_type="n1-standard-8",
            accelerator_type="NVIDIA_TESLA_T4",
            accelerator_count=2,
        ),
        metric_spec=metric_spec,
        parameter_spec=parameter_spec,
        max_trial_count=100,
        parallel_trial_count=10,          # 10 concurrent trials; adjust to budget
        max_failed_trial_count=5,          # Abort the tuning job after 5 consecutive failures
        search_algorithm=None,             # None defaults to Bayesian (Gaussian Process) optimization
        measurement_selection="best",
    )

    tuning_job.run(service_account="vertex-training-sa@my-project.iam.gserviceaccount.com")
    print(f"Best trial: {tuning_job.best_trial}")
    return tuning_job.resource_name
```

Inside the training container for a hyperparameter trial, reporting the metric requires a single SDK call that the Vertex agent intercepts:

```python
# trainer/hparam_task.py  (metric reporting portion)
# This runs inside the container for each Vizier trial.

import os
import argparse
from google.cloud import aiplatform


def report_metric(metric_name: str, value: float):
    """Report a scalar metric to Vertex AI Vizier for Bayesian optimization feedback."""
    aiplatform.log_metrics({metric_name: value})


def train_trial(args):
    # args.learning_rate, args.weight_decay, args.batch_size, etc. are injected
    # by Vertex AI as environment variables prefixed with AIP_HP_, which the SDK
    # parses and passes as CLI arguments to the training script.

    model = build_model()
    optimizer = build_optimizer(model, lr=args.learning_rate, wd=args.weight_decay)
    train_loader, val_loader = build_dataloaders(args.data_dir, args.batch_size)

    for epoch in range(args.epochs):
        train_one_epoch(model, optimizer, train_loader)
        val_acc = evaluate(model, val_loader)

    # Report only the final validation accuracy. For multi-fidelity tuning,
    # call report_metric after each epoch with the intermediate value.
    report_metric("val_accuracy", val_acc)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--learning-rate", type=float, required=True)
    parser.add_argument("--weight-decay", type=float, required=True)
    parser.add_argument("--batch-size", type=int, required=True)
    parser.add_argument("--dropout-rate", type=float, default=0.1)
    parser.add_argument("--warmup-steps-ratio", type=float, default=0.05)
    parser.add_argument("--output-dir", type=str, required=True)
    parser.add_argument("--data-dir", type=str, required=True)
    parser.add_argument("--epochs", type=int, default=30)
    args = parser.parse_args()

    aiplatform.init()
    train_trial(args)
```

### Experiment Tracking with Vertex AI Experiments

Every Custom Job and Hyperparameter Tuning trial generates metrics, parameters, and artifacts. Vertex AI Experiments provides a managed MLflow-compatible tracking layer that persists these artifacts in Cloud Storage and indexes them in Vertex AI's metadata store. Each experiment run records its configuration, metric time series, and output artifact URIs, making it possible to compare dozens of training runs in the Vertex AI Console or programmatically query the best configuration for promotion to a serving model.

```python
# experiment_tracking.py
# Integrates Vertex AI Experiments into a standard training loop.
# This code runs inside the training container.

import os
from google.cloud import aiplatform


def setup_experiment(project: str, region: str, experiment_name: str, run_name: str):
    aiplatform.init(project=project, location=region, experiment=experiment_name)
    aiplatform.start_run(run=run_name)


def log_training_step(step: int, loss: float, lr: float, grad_norm: float):
    """Log step-level metrics. Vertex Experiments stores these as a time series."""
    aiplatform.log_metrics({
        "train/loss": loss,
        "train/learning_rate": lr,
        "train/gradient_norm": grad_norm,
    }, step=step)


def log_epoch_metrics(epoch: int, train_loss: float, val_loss: float, val_accuracy: float):
    aiplatform.log_metrics({
        "epoch/train_loss": train_loss,
        "epoch/val_loss": val_loss,
        "epoch/val_accuracy": val_accuracy,
    }, step=epoch)


def log_hyperparameters(params: dict):
    """Log the full hyperparameter configuration for this run."""
    aiplatform.log_params(params)


def log_model_artifact(gcs_model_uri: str, model_display_name: str):
    """Register the trained model artifact with the Vertex metadata store."""
    model = aiplatform.Model.upload(
        display_name=model_display_name,
        artifact_uri=gcs_model_uri,
        serving_container_image_uri="us-docker.pkg.dev/vertex-ai/prediction/pytorch-gpu.1-13:latest",
    )
    aiplatform.log_metrics({"artifact/model_resource_name": model.resource_name})
    return model


def end_experiment():
    aiplatform.end_run()
```

---

## 3. High-Performance Optimization & Failure Modes

### Data Pipeline Throughput as the Hidden Bottleneck

Senior practitioners often optimize gradient communication and mixed-precision arithmetic while leaving their data pipeline as the actual limiting constraint. On a cluster of eight A100s processing ImageNet at a global batch size of 2048, each GPU needs roughly 32 samples per step, and with NCCL-optimized all-reduce, a step might complete in 180ms. If your DataLoader workers take 250ms to decode and augment a batch, your GPU utilization collapses to roughly 70% — not because of gradient communication, but because accelerators are idle waiting for data.

The correct architecture for data-intensive Vertex AI jobs uses a Cloud Storage FUSE mount (`gcsfuse`) or, better, a streaming dataset format such as WebDataset or TFRecord shards. TFRecord with `tf.data`'s parallel map and prefetch pipeline is particularly effective: its `AUTOTUNE` buffer sizing dynamically maximizes prefetch depth based on observed step latency. For PyTorch, WebDataset's shard-based streaming architecture reads directly from GCS over HTTP range requests, bypassing the POSIX filesystem layer entirely and saturating GCS bandwidth across all workers simultaneously.

The diagnostic command to confirm whether your GPU is data-starved rather than compute-bound is to watch the `sm_active_cycles` counter via `nvidia-smi dmon` during training:

```bash
# Monitor GPU utilization, memory bandwidth, and SM activity during a training run.
# Run this on one of the Vertex training workers via SSH (enabled by --enable-web-access).
watch -n 1 nvidia-smi dmon -s pucvmet -d 1 -c 60
```

A healthy GPU-bound training run shows `sm_active` above 85% continuously. A data-starved run shows burst patterns where `sm_active` spikes to 100% for 100ms then drops to near zero while the CPU DataLoader prepopulates the next batch.

### Mixed-Precision Training and Numerical Stability

The standard production configuration for A100 training is automatic mixed precision (AMP) with `torch.float16` for forward and backward passes, and `torch.float32` for the optimizer state and master weights. The A100's TF32 tensor cores offer a third option: they perform matrix multiply in a reduced-mantissa format that is compatible with the `float32` data type but uses only 10 bits of mantissa rather than 23. TF32 is enabled by default on A100 when `torch.backends.cuda.matmul.allow_tf32 = True` and delivers roughly 10× throughput compared to full float32 matrix multiply, with no code changes required beyond enabling the flag.

The failure mode to watch for in mixed-precision training is gradient underflow. When gradients are small and their float16 representation rounds to zero, the optimizer receives zero gradients and the model's weights stop updating in those directions. GradScaler addresses this by scaling the loss upward by a factor $S$ before the backward pass, multiplying all gradients by $S$. After the backward pass, GradScaler checks for infinities or NaN values in the gradient tensor. If none are found, it unscales the gradients by dividing by $S$ before passing them to the optimizer. If overflow is detected, the optimizer step is skipped entirely and $S$ is reduced. Over time, GradScaler's adaptive scaling factor converges to a value that keeps gradients in the representable float16 range without overflow.

### Checkpoint Recovery Under Preemption

Vertex AI Spot (preemptible) VMs offer 60–70% cost reduction compared to standard VMs, at the cost of arbitrary preemption with two minutes of notice. For long training runs, this tradeoff is almost always favorable if your checkpoint recovery path is robust. The critical implementation detail is checkpoint frequency relative to expected preemption interval. If your machine has a mean time to preemption of three hours and your checkpoint interval is one epoch at 90 minutes, your expected wasted compute at any preemption is 45 minutes — roughly 25% overhead. At five-epoch intervals of seven and a half hours, expected waste exceeds the MTTP, meaning you will almost certainly lose more work than you save by writing checkpoints less frequently.

A sophisticated recovery strategy uses epoch-level checkpoints supplemented by mid-epoch step-level checkpoints written every 500 steps. The step-level checkpoint includes the dataloader's random state and the sampler's current position so that recovery resumes exactly where preemption occurred, with no repeated samples in the current epoch. The epoch-level checkpoint is a full serialization of model, optimizer, and scheduler state; the step-level checkpoint saves only the differential state (gradients, optimizer momentum buffers) since the last epoch checkpoint. This two-tier scheme balances GCS write bandwidth against recovery granularity.

```python
# checkpoint_manager.py
# Two-tier checkpoint manager: epoch-level full state + step-level differential state.

import os
import torch
import logging
from google.cloud import storage

logger = logging.getLogger(__name__)

class TieredCheckpointManager:
    def __init__(self, gcs_base_dir: str, rank: int,
                 epoch_interval: int = 5, step_interval: int = 500):
        self.gcs_base_dir = gcs_base_dir.rstrip("/")
        self.rank = rank
        self.epoch_interval = epoch_interval
        self.step_interval = step_interval
        self.gcs_client = storage.Client()
        bucket_path = gcs_base_dir[len("gs://"):]
        self.bucket_name, self.base_blob = bucket_path.split("/", 1)

    def _upload(self, local_path: str, blob_suffix: str):
        if self.rank != 0:
            return
        bucket = self.gcs_client.bucket(self.bucket_name)
        final_path = f"{self.base_blob}/{blob_suffix}"
        tmp_path = final_path + ".tmp"
        # Write to tmp, then server-side copy for atomicity.
        tmp_blob = bucket.blob(tmp_path)
        tmp_blob.upload_from_filename(local_path)
        bucket.copy_blob(tmp_blob, bucket, final_path)
        tmp_blob.delete()
        logger.info(f"Checkpoint uploaded: gs://{self.bucket_name}/{final_path}")

    def save_epoch_checkpoint(self, epoch: int, model: torch.nn.Module,
                              optimizer: torch.optim.Optimizer, scheduler,
                              loss: float):
        if self.rank != 0:
            return
        if (epoch + 1) % self.epoch_interval != 0:
            return
        state = {
            "type": "epoch",
            "epoch": epoch,
            "model": model.state_dict(),
            "optimizer": optimizer.state_dict(),
            "scheduler": scheduler.state_dict(),
            "loss": loss,
        }
        local_path = f"/tmp/epoch_ckpt_{epoch:04d}.pt"
        torch.save(state, local_path)
        self._upload(local_path, f"epoch/checkpoint_{epoch:04d}.pt")
        self._upload(local_path, "epoch/checkpoint_latest.pt")

    def save_step_checkpoint(self, epoch: int, step: int, model: torch.nn.Module,
                             optimizer: torch.optim.Optimizer, scheduler,
                             rng_state: dict):
        if self.rank != 0:
            return
        if step % self.step_interval != 0:
            return
        state = {
            "type": "step",
            "epoch": epoch,
            "step": step,
            "model": model.state_dict(),
            "optimizer": optimizer.state_dict(),
            "scheduler": scheduler.state_dict(),
            "rng_state": rng_state,
        }
        local_path = "/tmp/step_ckpt_latest.pt"
        torch.save(state, local_path)
        self._upload(local_path, "step/checkpoint_latest.pt")

    def load_latest(self, model: torch.nn.Module, optimizer: torch.optim.Optimizer,
                    scheduler, local_rank: int) -> tuple[int, int]:
        """
        Returns (start_epoch, start_step). Prefers the step checkpoint if it is
        newer than the epoch checkpoint.
        """
        map_location = {"cuda:0": f"cuda:{local_rank}"}
        step_path = "step/checkpoint_latest.pt"
        epoch_path = "epoch/checkpoint_latest.pt"

        step_state = self._download_state(step_path, map_location)
        epoch_state = self._download_state(epoch_path, map_location)

        # Choose the most recent checkpoint by (epoch, step) tuple.
        if step_state and epoch_state:
            se, ss = step_state["epoch"], step_state.get("step", 0)
            ee = epoch_state["epoch"]
            if (se, ss) > (ee, 0):
                state = step_state
            else:
                state = epoch_state
        elif step_state:
            state = step_state
        elif epoch_state:
            state = epoch_state
        else:
            logger.info("No checkpoint found. Training from epoch 0, step 0.")
            return 0, 0

        model.load_state_dict(state["model"])
        optimizer.load_state_dict(state["optimizer"])
        scheduler.load_state_dict(state["scheduler"])
        start_epoch = state["epoch"]
        start_step = state.get("step", 0) if state["type"] == "step" else 0
        logger.info(f"Resumed from {state['type']} checkpoint: epoch={start_epoch}, step={start_step}")
        return start_epoch, start_step

    def _download_state(self, blob_suffix: str, map_location: dict) -> dict | None:
        bucket = self.gcs_client.bucket(self.bucket_name)
        blob = bucket.blob(f"{self.base_blob}/{blob_suffix}")
        if not blob.exists():
            return None
        local_path = f"/tmp/dl_ckpt_{blob_suffix.replace('/', '_')}"
        blob.download_to_filename(local_path)
        return torch.load(local_path, map_location=map_location)
```

### Computational Graph Optimization: `torch.compile` and XLA

PyTorch 2.0's `torch.compile` applies TorchInductor, a deep learning compiler backend, to your model's computational graph. At its core, `torch.compile` traces your model using TorchDynamo — a Python bytecode rewriter that extracts subgraphs of pure PyTorch operations — and compiles them through Triton, NVIDIA's GPU kernel language, to generate fused CUDA kernels. The practical effect is that sequences of elementwise operations (activation functions, normalization, dropout) that would otherwise each launch a separate CUDA kernel are fused into a single kernel, eliminating kernel launch overhead and dramatically reducing memory round-trips.

On A100s, `torch.compile` with `mode="max-autotune"` delivers 15–40% throughput improvement on transformer architectures, primarily by fusing the attention softmax computation and eliminating the intermediate memory writes that the unfused version requires. The compile step takes 60–90 seconds on the first training step, during which the Triton JIT compiles the generated kernels to PTX. Subsequent steps use the cached compiled kernels. For long training runs, this startup cost is negligible.

```python
# compile_integration.py
# torch.compile integration inside a Vertex AI training container.
# Requires torch>=2.0.0 and CUDA>=11.7.

import torch
import torch.nn as nn


def compile_model_for_training(model: nn.Module, compile_mode: str = "max-autotune") -> nn.Module:
    """
    Compile the model with TorchInductor for maximum training throughput.
    compile_mode options:
      "default"       — Balanced compile time and runtime performance.
      "reduce-overhead" — Minimizes kernel launch overhead; good for small batch sizes.
      "max-autotune"  — Full autotuning of Triton kernels; best throughput, longest compile.
    """
    compiled = torch.compile(
        model,
        mode=compile_mode,
        fullgraph=True,       # Fail if the graph cannot be fully captured (no Python fallback)
        dynamic=False,        # Static shapes enable better Triton kernel generation
    )
    return compiled


def compile_loss_fn(loss_fn: nn.Module) -> nn.Module:
    """Compile the loss function separately to fuse label smoothing and softmax."""
    return torch.compile(loss_fn, mode="max-autotune", fullgraph=True)


# In your training setup:
# model = build_model().to(device)
# model = DDP(model, device_ids=[local_rank])
# model.module = compile_model_for_training(model.module)
# Note: compile the inner module, not the DDP wrapper, to preserve DDP's
# gradient hook mechanism which torch.compile does not understand natively.
```

For JAX workloads on TPU, XLA's `jit` compilation performs analogous graph optimization. The key difference is that XLA operates on the full HLO graph at compile time, before any execution, whereas `torch.compile` operates lazily at first execution. XLA's ahead-of-time compilation allows more aggressive optimization: layout reassignment, memory planning across the entire forward-backward pass, and cross-operation rematerialization are all globally optimal in a way that JIT compilation cannot achieve. The tradeoff is that XLA requires static shapes throughout the computation graph. Dynamic shapes, such as variable-length sequence batches, require padding to the maximum length in the batch, which introduces wasted computation — a design constraint that shapes how production TPU training pipelines are built.

### Failure Mode Taxonomy

The failure modes in distributed training fall into three categories by their diagnostic difficulty. The first and easiest to identify are **hard failures**: NCCL communication timeouts, OOM errors from misconfigured per-worker batch sizes, or container image pull failures from misconfigured Artifact Registry IAM bindings. These produce clear error messages in the job logs, accessible via `gcloud ai custom-jobs stream-logs JOB_ID --region=us-central1` or in the Cloud Logging console.

The second category, **silent divergence**, is substantially more dangerous. It occurs when gradient synchronization proceeds correctly from NCCL's perspective but produces incorrect gradient estimates due to implementation errors in the distributed sampler or inconsistent augmentation seeds. The diagnostic signal is a training loss curve that decreases more slowly than expected or reaches a higher final loss than single-device training with the same effective batch size. The fix is to always set `train_sampler.set_epoch(epoch)` before iterating each epoch, ensuring that the DistributedSampler reseeds its index permutation differently on each epoch while remaining consistent across workers within an epoch.

The third category, **resource-induced instability**, appears as gradient explosions or loss spikes at irregular intervals. These are often caused by the interaction between mixed-precision training, large learning rates, and the specific numerical properties of a model at a particular training stage. The correct mitigation is gradient clipping — `torch.nn.utils.clip_grad_norm_` with a `max_norm` of 1.0 is standard for transformer models — combined with logging the pre-clip gradient norm at every step. A sudden spike in gradient norm before clipping, followed by normal behavior after, is the signature of a true gradient explosion. A spike in loss without a corresponding spike in gradient norm points instead to a data corruption issue in the batch or a checkpoint integrity failure on resume.

Understanding these failure modes at the mechanical level — not as a checklist but as cause-and-effect relationships between distributed execution topology, numerical precision, and training dynamics — is what separates practitioners who can debug a production training job at hour 36 from those who restart from scratch and hope for better luck the second time.
