# Lesson 3: MLOps — Pipeline Orchestration, Model Serving, and Operational Reliability

---

## 1. First-Principles Foundations

### What Makes ML Systems Categorically Different

A conventional software service has a fixed, deterministic relationship between code and behavior: given the same binary, the same request produces the same response. An ML system breaks this invariant at the foundational level. The *behavior* of an ML system is encoded not in source code but in learned parameters — a 175-billion-element floating-point tensor in the case of a large language model — derived from a dataset that is itself a snapshot of a world that changes continuously.

This creates three classes of problems with no direct analog in classical software engineering:

**Data distribution shift.** A model trained on data from Q1 may silently degrade in Q3 as the statistical properties of its inputs evolve. No code change occurred; no deployment happened. The system broke because the world changed and the model did not. Detecting this requires continuous statistical comparison between the training distribution and the live serving distribution.

**Non-deterministic reproducibility.** ML training involves floating-point arithmetic across distributed hardware with non-associative reduction operations (e.g., `AllReduce` over float16). Two training runs with identical seeds on identical code may produce models with measurably different accuracy if executed on different hardware topologies or with different batch orderings — a consequence of IEEE 754 non-determinism and NCCL collective operation ordering. True reproducibility requires tracking not just code and data hashes but also framework versions, CUDA versions, hardware topology, and random seeds.

**Artifact dependency complexity.** A serving model depends on: the training dataset (versioned), the feature engineering logic (versioned), the preprocessing pipeline (versioned), the model architecture (versioned), the training hyperparameters (versioned), and the serving infrastructure (versioned). Any of these changing without the others being re-validated can silently corrupt predictions. This is the **artifact dependency graph** — the core data structure that MLOps systems must manage.

### The Fundamental Invariants

These are the invariants that any production MLOps system must enforce. They are architectural constraints, not aspirational guidelines:

**Lineage completeness.** Every model artifact in production must have a complete, traversable provenance graph back to its source data. If you cannot answer "which rows of which dataset version trained this model?", you cannot diagnose regressions, comply with data deletion requirements (GDPR's right to erasure requires knowing which models were trained on which users' data), or reproduce the model.

**Semantic idempotency.** Re-running a pipeline stage with the same versioned inputs must produce a bit-for-bit identical output artifact, or the system must explicitly declare why it cannot (stochastic training) and provide statistical equivalence guarantees instead.

**Separation of experimentation from production.** The code path for a data scientist exploring features in a Jupyter notebook must be strictly isolated from the code path for a production training run. This is enforced architecturally, not by convention, through separate execution environments, separate artifact registries, and separate monitoring namespaces.

**Fail-closed validation gates.** A model transition from staging to production must pass through explicit, automated validation checkpoints. The default behavior on ambiguous results must be to block promotion, not to allow it.

---

## 2. The MLOps Architecture Stack

### Layered Architecture Overview

```mermaid
graph TB
    subgraph sub_data_plane ["Data Plane"]
        DS[("Data Sources\n(S3, GCS, Kafka,\nSnowflake, Delta Lake)")]
        FS[("Feature Store\n(Feast / Tecton)")]
        AR[("Artifact Registry\n(MLflow / DVC)")]
    end

    subgraph sub_orchestration_plane ["Orchestration Plane"]
        OE["Orchestration Engine\n(Airflow / Kubeflow / Prefect)"]
        TR["Training Cluster\n(Ray / Horovod / FSDP)"]
        VAL["Validation Gate\n(Great Expectations /\nEvidently AI)"]
    end

    subgraph sub_serving_plane ["Serving Plane"]
        MR[("Model Registry\n(MLflow Model Registry)")]
        IS["Inference Server\n(Triton / TorchServe /\nvLLM)"]
        GW["API Gateway\n(Envoy / Kong)"]
    end

    subgraph sub_observability_plane ["Observability Plane"]
        MT["Metrics Store\n(Prometheus / Thanos)"]
        DD["Drift Detector\n(Evidently / NannyML)"]
        TR2["Trace Store\n(Jaeger / Tempo)"]
        AL["Alert Manager"]
    end

    DS -->|"versioned snapshots"| FS
    FS -->|"training features"| OE
    OE -->|"schedules"| TR
    TR -->|"model artifacts + metrics"| AR
    AR -->|"candidate model"| VAL
    VAL -->|"pass: promote"| MR
    VAL -->|"fail: block + alert"| AL
    MR -->|"model weights + schema"| IS
    IS -->|"predictions"| GW
    IS -->|"prediction logs"| MT
    MT -->|"feature statistics"| DD
    DD -->|"drift signal"| AL
    AL -->|"retrain trigger"| OE
    IS -->|"request traces"| TR2
```

### The Task Graph Is Not a DAG

The dominant mental model for ML pipeline orchestration — the directed acyclic graph — is a necessary but insufficient abstraction. A production ML system requires a **multi-dimensional dependency hypergraph** that tracks four distinct dependency types simultaneously:

**Execution dependencies** (the classic DAG): task B cannot start until task A completes. This is what Airflow's `>>` operator models.

**Data artifact dependencies**: task B's output is semantically invalid if its input artifact was produced by a code version that has since been patched. This requires tracking artifact lineage, not just task completion state.

**Resource dependencies**: task B requires 8× A100 GPUs. If the cluster is at capacity, B must queue regardless of execution dependency satisfaction.

**Temporal dependencies**: the validation job must run on model artifacts where the training data cutoff is within 7 days of wall-clock time. Stale artifacts should trigger re-training, not re-use.

The orchestration engines most deployed in production — Apache Airflow 2.x, Kubeflow Pipelines v2, Prefect 2, and Metaflow — each handle these dependency types with varying degrees of native support. Kubeflow Pipelines v2 introduced first-class artifact typing (via its ML Metadata store backed by Google's MLMD library) specifically to address the gap between execution DAGs and artifact lineage DAGs.

---

## 3. Feature Stores: The Consistency Bridge

### The Training-Serving Skew Problem

Training-serving skew is the single most prevalent and hardest-to-detect failure mode in production ML. It occurs when the feature computation logic used during training produces subtly different values than the feature computation logic used during inference — even when both are "correct" implementations of the same specification.

A concrete example: during training, a "7-day rolling average purchase amount" feature is computed over a historical dataset using a Spark batch job. During serving, the same feature is computed in real-time using a Redis sorted set with an approximate windowing algorithm. The offline and online computations are semantically equivalent under uniform load but diverge during sparse periods when the online store has insufficient historical data to fill the window. The model was never trained on this sparse-window distribution, so its predictions are uncalibrated for exactly the users who are least active — often the highest-value edge cases in fraud detection or recommendation systems.

The feature store architecture directly addresses this by providing a **unified feature computation layer** that guarantees offline (batch training) and online (low-latency serving) feature retrieval produce identical values for identical entity keys and timestamps.

```mermaid
graph LR
    subgraph sub_offline_path__training ["Offline Path (Training)"]
        RD[("Raw Data\nWarehouse")] -->|"batch transform"| OF[("Offline Store\nParquet / Delta")]
        OF -->|"point-in-time\ncorrect join"| TV["Training Dataset\n(no future leakage)"]
    end

    subgraph sub_online_path__serving ["Online Path (Serving)"]
        ST[("Streaming Source\nKafka")] -->|"micro-batch\nor stream transform"| ON[("Online Store\nRedis / DynamoDB")]
        ON -->|"<5ms lookup"| FV["Feature Vector\nfor Prediction"]
    end

    subgraph sub_feature_store ["Feature Store"]
        FD["Feature Definitions\n(versioned Python SDK)"]
        FD -.->|"same logic"| OF
        FD -.->|"same logic"| ON
    end

    TV -->|"train model"| M["Model Artifact"]
    FV -->|"serve model"| M
```

The critical property enforced by the feature store is **point-in-time correctness**: when constructing training data, features are retrieved using the value they had *at the time of the label event*, not their current value. Without this, a training job that joins features to labels after the fact will inadvertently include features computed from data that postdates the label — a form of data leakage that inflates training metrics and produces models that fail catastrophically in production.

Feast implements this through its `get_historical_features()` API, which performs a time-travel join against the offline store. The underlying implementation uses a sorted merge join on entity key + timestamp, implemented in Apache Arrow or Spark depending on scale.

---

## 4. Pipeline Orchestration: Implementation Depth

### Kubeflow Pipelines v2 — Architecture and Mechanics

Kubeflow Pipelines v2 is the dominant orchestration platform for Kubernetes-native ML workflows. Its architecture separates three concerns that prior tools conflated:

```mermaid
graph TB
    subgraph sub_sdk_layer__python ["SDK Layer (Python)"]
        PC["Pipeline Definition\n@pipeline decorator"]
        CC["Component Definitions\n@component decorator"]
        AR2["Artifact Types\n(Dataset, Model, Metrics)"]
    end

    subgraph sub_compilation_layer ["Compilation Layer"]
        IR["Pipeline IR\n(protobuf / YAML)"]
    end

    subgraph sub_control_plane__kubernetes ["Control Plane (Kubernetes)"]
        API["KFP API Server\n(gRPC + REST)"]
        MLMD2[("ML Metadata Store\n(MySQL + MLMD)")]
        SC["Argo Workflows\nor Tekton\n(execution backend)"]
    end

    subgraph sub_data_plane ["Data Plane"]
        OBJ[("Object Storage\nMinIO / GCS / S3")]
    end

    PC --> CC
    CC --> IR
    AR2 --> IR
    IR -->|"submit"| API
    API -->|"persist pipeline spec"| MLMD2
    API -->|"instantiate workflow"| SC
    SC -->|"execute pods"| K8S["Kubernetes Pods"]
    K8S -->|"write artifacts"| OBJ
    K8S -->|"log metadata"| MLMD2
    MLMD2 -.->|"lineage queries"| API
```

The key architectural decision in KFP v2 is that artifacts are **typed, metadata-tracked objects stored in object storage**, not raw file paths. When a component outputs a `Dataset` artifact, the framework automatically:

1. Generates a unique URI in the configured object store (e.g., `gs://bucket/pipeline_id/run_id/component_id/artifact_name/`)
2. Records the artifact's URI, type, schema, and producing execution in the MLMD store
3. Passes only the artifact's metadata URI to downstream components — not the raw data

This means artifact lineage is a first-class database query, not a convention. You can ask "which runs produced models that were trained on this dataset version?" with a SQL query against MLMD.

### A Production-Grade KFP Component

```python
from kfp.v2 import dsl
from kfp.v2.dsl import component, Dataset, Model, Output, Input, Metrics
from typing import NamedTuple

@component(
    base_image="python:3.10-slim",
    packages_to_install=[
        "scikit-learn==1.3.2",
        "pandas==2.1.4",
        "great-expectations==0.18.8",
        "mlflow==2.9.2",
    ],
)
def train_and_validate_model(
    training_data: Input[Dataset],
    model_artifact: Output[Model],
    metrics_artifact: Output[Metrics],
    experiment_name: str,
    n_estimators: int = 200,
    max_depth: int = 6,
    min_samples_split: int = 20,
    drift_threshold: float = 0.05,
) -> NamedTuple("ValidationResult", [("passed", bool), ("ks_statistic", float)]):
    """
    Trains a gradient boosted classifier with integrated validation.
    Fails fast if training data distribution deviates from baseline.
    """
    import json
    import hashlib
    import pandas as pd
    import numpy as np
    from sklearn.ensemble import GradientBoostingClassifier
    from sklearn.model_selection import StratifiedKFold, cross_val_score
    from sklearn.metrics import roc_auc_score
    from scipy.stats import ks_2samp
    import joblib
    import mlflow
    import mlflow.sklearn
    from collections import namedtuple

    # --- Load and validate input data ---
    df = pd.read_parquet(training_data.path)

    if df.empty:
        raise ValueError(f"Training dataset at {training_data.path} is empty.")

    feature_cols = [c for c in df.columns if c not in {"label", "entity_id", "event_timestamp"}]
    X = df[feature_cols].values.astype(np.float32)
    y = df["label"].values.astype(np.int32)

    if len(np.unique(y)) < 2:
        raise ValueError(f"Training data contains only one class: {np.unique(y)}. Cannot train classifier.")

    # --- Distribution validation against stored baseline statistics ---
    baseline_stats_path = training_data.metadata.get("baseline_stats_path")
    ks_statistic = 0.0

    if baseline_stats_path:
        with open(baseline_stats_path) as f:
            baseline_stats = json.load(f)

        # Kolmogorov-Smirnov test: compare each feature's empirical CDF
        # against the baseline distribution. KS p-value < drift_threshold
        # indicates statistically significant distribution shift.
        ks_results = []
        for i, col in enumerate(feature_cols):
            if col in baseline_stats:
                baseline_samples = np.array(baseline_stats[col]["sample"])
                stat, p_value = ks_2samp(X[:, i], baseline_samples)
                ks_results.append((col, stat, p_value))

        failing_features = [(col, stat, p) for col, stat, p in ks_results if p < drift_threshold]
        ks_statistic = max(stat for _, stat, _ in ks_results) if ks_results else 0.0

        if failing_features:
            # Log the drift details before failing — the exception message alone
            # is insufficient for post-mortem analysis.
            drift_report = {
                col: {"ks_stat": float(stat), "p_value": float(p)}
                for col, stat, p in failing_features
            }
            metrics_artifact.log_metric("drift_detected", 1.0)
            metrics_artifact.log_metric("num_drifted_features", len(failing_features))
            raise RuntimeError(
                f"Data drift detected in {len(failing_features)} features. "
                f"KS test p-value < {drift_threshold}. Report: {json.dumps(drift_report, indent=2)}"
            )

    # --- Training with MLflow experiment tracking ---
    mlflow.set_experiment(experiment_name)

    with mlflow.start_run():
        mlflow.log_params({
            "n_estimators": n_estimators,
            "max_depth": max_depth,
            "min_samples_split": min_samples_split,
            "n_training_rows": len(df),
            "n_features": len(feature_cols),
            "training_data_hash": hashlib.sha256(
                pd.util.hash_pandas_object(df).values.tobytes()
            ).hexdigest(),
        })

        clf = GradientBoostingClassifier(
            n_estimators=n_estimators,
            max_depth=max_depth,
            min_samples_split=min_samples_split,
            subsample=0.8,
            learning_rate=0.05,
            random_state=42,
            n_iter_no_change=15,
            validation_fraction=0.1,
        )

        # Stratified k-fold CV to estimate generalization without holdout leakage
        cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
        cv_scores = cross_val_score(clf, X, y, cv=cv, scoring="roc_auc", n_jobs=-1)

        # Final fit on full training data for the production artifact
        clf.fit(X, y)

        auc_mean = float(cv_scores.mean())
        auc_std = float(cv_scores.std())

        mlflow.log_metrics({
            "cv_roc_auc_mean": auc_mean,
            "cv_roc_auc_std": auc_std,
            "train_roc_auc": roc_auc_score(y, clf.predict_proba(X)[:, 1]),
        })

        mlflow.sklearn.log_model(clf, artifact_path="model")
        run_id = mlflow.active_run().info.run_id

    # --- Persist model artifact with metadata for downstream components ---
    joblib.dump(clf, model_artifact.path)
    model_artifact.metadata["framework"] = "scikit-learn"
    model_artifact.metadata["framework_version"] = "1.3.2"
    model_artifact.metadata["feature_names"] = json.dumps(feature_cols)
    model_artifact.metadata["cv_roc_auc_mean"] = str(auc_mean)
    model_artifact.metadata["mlflow_run_id"] = run_id

    metrics_artifact.log_metric("cv_roc_auc_mean", auc_mean)
    metrics_artifact.log_metric("cv_roc_auc_std", auc_std)
    metrics_artifact.log_metric("ks_statistic", ks_statistic)
    metrics_artifact.log_metric("drift_detected", 0.0)

    ValidationResult = namedtuple("ValidationResult", ["passed", "ks_statistic"])
    return ValidationResult(passed=True, ks_statistic=ks_statistic)
```

### A/B Canary Pipeline with Automated Promotion Gate

```python
@dsl.pipeline(
    name="model-ab-promotion-pipeline",
    description="Trains challenger, compares against champion, promotes on statistical significance.",
)
def ab_promotion_pipeline(
    dataset_uri: str,
    champion_model_uri: str,
    experiment_name: str = "credit-risk-v2",
    significance_level: float = 0.05,
    minimum_auc_improvement: float = 0.005,
):
    """
    Two-stage pipeline:
    1. Train challenger model on latest data.
    2. Statistical comparison gate: Wilcoxon signed-rank test on CV fold AUCs.
       Promote challenger only if improvement is statistically significant
       AND exceeds the minimum absolute threshold.
    """
    ingest_op = ingest_dataset(dataset_uri=dataset_uri)
    ingest_op.set_retry(num_retries=3, backoff_duration="30s", backoff_factor=2.0)

    validate_op = validate_schema(dataset=ingest_op.outputs["dataset"])
    validate_op.after(ingest_op)

    train_op = train_and_validate_model(
        training_data=validate_op.outputs["validated_dataset"],
        experiment_name=experiment_name,
    )
    train_op.set_accelerator_type("NVIDIA_TESLA_T4")
    train_op.set_accelerator_limit(1)
    train_op.set_memory_limit("16G")
    train_op.set_cpu_limit("8")

    # Promotion gate: compare challenger against champion
    # using held-out evaluation data — not the training set.
    promote_op = compare_and_promote(
        champion_model_uri=champion_model_uri,
        challenger_model=train_op.outputs["model_artifact"],
        evaluation_data=validate_op.outputs["holdout_dataset"],
        significance_level=significance_level,
        minimum_improvement=minimum_auc_improvement,
    )
    promote_op.after(train_op)

    # Conditional deployment: only execute if promotion gate passed
    with dsl.Condition(promote_op.outputs["promoted"] == "true", name="promotion-approved"):
        deploy_op = deploy_to_triton(
            model_artifact=train_op.outputs["model_artifact"],
            deployment_config={"replicas": 3, "max_batch_size": 64, "instance_group": "GPU"},
        )
        deploy_op.after(promote_op)
```

---

## 5. Model Serving Architecture

### The Inference Server Design Space

Serving a trained model is not simply loading weights and calling `model.predict()`. Production inference systems must satisfy orthogonal requirements simultaneously: sub-10ms P99 latency, horizontal scalability, support for heterogeneous hardware (CPU, GPU, TPU), model versioning with zero-downtime rollout, and byte-accurate predictions identical to what the training framework produces.

The dominant inference serving frameworks each make different architectural tradeoffs:

| Framework | Primary Use Case | Batching | Hardware Abstraction | Protocol |
|---|---|---|---|---|
| NVIDIA Triton Inference Server | Multi-model, multi-framework GPU serving | Dynamic + static | CUDA, TensorRT, ONNX | gRPC + HTTP/REST |
| TorchServe | PyTorch models, flexible handlers | Adaptive | CPU + GPU | REST + gRPC |
| TensorFlow Serving | TensorFlow SavedModel | Microbatch | CPU + GPU | gRPC (TF Serving API) |
| vLLM | LLM autoregressive generation | PagedAttention + continuous batching | CUDA | OpenAI-compatible REST |
| Ray Serve | General Python + ML, complex DAGs | Flexible | Agnostic | HTTP |
| BentoML | Model packaging + serving, operator-friendly | Adaptive | Agnostic | REST + gRPC |

### NVIDIA Triton: Dynamic Batching Mechanics

Triton's dynamic batching scheduler is the most widely deployed mechanism for GPU inference latency/throughput optimization. The scheduler aggregates individual requests arriving within a configurable time window into a single batched tensor operation, amortizing the GPU kernel launch overhead across multiple requests.

The batching decision is governed by two parameters: `max_queue_delay_microseconds` (the maximum time the scheduler will hold a request waiting for a batch to fill) and `preferred_batch_size` (a list of batch sizes the scheduler prefers, in ascending order). The scheduler greedily fills batches: it waits up to `max_queue_delay_microseconds` for a batch of `preferred_batch_size[0]` to form; if the queue reaches `preferred_batch_size[1]` before the timeout, it dispatches immediately.

```mermaid
sequenceDiagram
    participant C1 as Client 1
    participant C2 as Client 2
    participant C3 as Client 3
    participant SQ as Scheduler Queue
    participant BS as Batch Scheduler
    participant GPU as GPU Execution Engine
    participant MR2 as Model Runtime

    C1->>SQ: request (t=0ms)
    C2->>SQ: request (t=1ms)
    Note over BS: preferred_batch_size=[4,8]<br/>max_queue_delay=5ms
    BS->>SQ: poll (t=2ms) — only 2 requests, wait
    C3->>SQ: request (t=4ms)
    BS->>SQ: poll (t=5ms) — timeout reached, dispatch batch=3
    BS->>GPU: forward(batch_tensor[3, feature_dim])
    GPU->>MR2: execute model kernel
    MR2-->>GPU: output_tensor[3, num_classes]
    GPU-->>BS: results[3]
    BS-->>C1: response (t=7ms)
    BS-->>C2: response (t=7ms)
    BS-->>C3: response (t=7ms)
```

### Triton Model Configuration

A production Triton model repository for a TensorRT-optimized model:

```text
model_repository/
├── credit_risk_v3/
│   ├── config.pbtxt
│   ├── 1/
│   │   └── model.plan          # TensorRT engine
│   └── 2/
│       └── model.plan          # newer version — both served simultaneously
└── credit_risk_ensemble/
    ├── config.pbtxt            # ensemble: preprocessing + model + postprocessing
    └── 1/
        └── <no weights — ensemble is pure config>
```

```protobuf
# credit_risk_v3/config.pbtxt
name: "credit_risk_v3"
platform: "tensorrt_plan"
max_batch_size: 128

input [
  {
    name: "features"
    data_type: TYPE_FP32
    dims: [ 47 ]   # feature vector dimensionality — must match training
  }
]

output [
  {
    name: "default_probability"
    data_type: TYPE_FP32
    dims: [ 1 ]
  }
]

dynamic_batching {
  preferred_batch_size: [ 16, 32, 64 ]
  max_queue_delay_microseconds: 5000  # 5ms — tune based on P99 SLA
  preserve_ordering: true             # critical for request correlation
}

instance_group [
  {
    count: 2          # 2 model instances per GPU
    kind: KIND_GPU
    gpus: [ 0, 1 ]   # pin to specific GPU device IDs
  }
]

version_policy {
  specific { versions: [ 1, 2 ] }  # serve both versions simultaneously for A/B
}

ensemble_scheduling {
  # not used here — see ensemble config below
}
```

### Model Serving with vLLM: PagedAttention

For large language models, the dominant serving bottleneck is **KV cache memory management**. The key-value cache stores intermediate attention computations for each token in a sequence; for a 70B parameter model with 80-layer attention and batch sizes relevant to production, the KV cache can require tens of gigabytes of GPU VRAM per concurrent request.

vLLM's **PagedAttention** mechanism borrows virtual memory paging from operating system design. KV cache is allocated in fixed-size "pages" (blocks of contiguous GPU memory) rather than as contiguous per-sequence allocations. A block manager maintains a page table mapping logical sequence positions to physical GPU memory blocks, allowing non-contiguous allocation and enabling **copy-on-write** for beam search and **memory sharing** across parallel sequences in the same request batch.

```mermaid
graph TB
    subgraph sub_physical_gpu_memory__80gb ["Physical GPU Memory (80GB)"]
        B1["Block 1\n(tokens 0-15)"]
        B2["Block 2\n(tokens 16-31)"]
        B3["Block 3\n(tokens 32-47)"]
        B4["Block 4\n(tokens 0-15)"]
        B5["Block 5\n(tokens 16-31)"]
        FREE["Free Blocks Pool"]
    end

    subgraph sub_logical_sequence_space ["Logical Sequence Space"]
        SEQ1["Sequence A\n(prompt: 48 tokens)"]
        SEQ2["Sequence B\n(prompt: 32 tokens)"]
    end

    subgraph sub_block_manager__page_table ["Block Manager (Page Table)"]
        PT1["Seq A: logical[0] → phys[1]\nSeq A: logical[1] → phys[2]\nSeq A: logical[2] → phys[3]"]
        PT2["Seq B: logical[0] → phys[4]\nSeq B: logical[1] → phys[5]"]
    end

    SEQ1 --> PT1
    SEQ2 --> PT2
    PT1 --> B1
    PT1 --> B2
    PT1 --> B3
    PT2 --> B4
    PT2 --> B5
```

This non-contiguous allocation eliminates the **memory fragmentation** that plagues naive KV cache implementations, where each sequence reserves a contiguous buffer sized for the maximum generation length — wasting memory proportional to `(max_len - actual_len)` per sequence.

**Continuous batching** completes the picture: rather than waiting for all sequences in a batch to finish generation before accepting new requests (static batching), vLLM's scheduler inserts new requests into the running batch as sequence slots become free. This keeps GPU utilization near 100% under load, as opposed to static batching's sawtooth utilization pattern.

```python
from vllm import LLM, SamplingParams
from vllm.engine.arg_utils import AsyncEngineArgs
from vllm.engine.async_llm_engine import AsyncLLMEngine
import asyncio
import uuid

# Production async serving engine configuration
engine_args = AsyncEngineArgs(
    model="meta-llama/Llama-2-70b-chat-hf",
    tokenizer="meta-llama/Llama-2-70b-chat-hf",
    tensor_parallel_size=4,         # split across 4 GPUs via Megatron-style column parallelism
    gpu_memory_utilization=0.90,    # reserve 10% for CUDA kernels and framework overhead
    max_num_batched_tokens=8192,    # maximum tokens across all concurrent sequences
    max_num_seqs=256,               # maximum concurrent sequences
    quantization="awq",             # 4-bit AWQ quantization: ~4x memory reduction
    dtype="float16",
    block_size=16,                  # PagedAttention block size (tokens per block)
    swap_space=4,                   # CPU swap space in GB for KV cache offloading
    enforce_eager=False,            # use CUDA graphs for static-shape optimization
)

engine = AsyncLLMEngine.from_engine_args(engine_args)

async def generate_with_streaming(
    prompt: str,
    max_tokens: int = 512,
    temperature: float = 0.7,
    top_p: float = 0.9,
) -> str:
    sampling_params = SamplingParams(
        temperature=temperature,
        top_p=top_p,
        max_tokens=max_tokens,
        stop=["</s>", "[INST]"],    # model-specific stop tokens
        skip_special_tokens=True,
    )

    request_id = str(uuid.uuid4())
    results_generator = engine.generate(prompt, sampling_params, request_id)

    full_output = ""
    async for request_output in results_generator:
        # Each iteration yields incremental tokens — stream to client
        if request_output.outputs:
            full_output = request_output.outputs[0].text

    return full_output
```

---

## 6. Distributed Training Architecture

### Data Parallelism vs. Model Parallelism

Scaling training beyond a single accelerator requires distributing computation. There are three primary strategies, each applicable at different model/dataset size regimes:

**Data parallelism** replicates the full model on each worker. Each worker processes a different shard of the mini-batch, computes gradients independently, and synchronizes gradients across all workers before the optimizer step. The communication pattern is an `AllReduce` collective — each worker sends and receives gradients of size proportional to the total parameter count. This scales well until the model no longer fits in a single GPU's memory.

**Tensor parallelism (intra-layer)** shards individual weight matrices across devices. For a linear layer `Y = XW`, the weight matrix `W` is split column-wise across N GPUs: each GPU holds `W[:, k/N:(k+1)/N]` and computes a partial output. An `AllGather` collective reassembles the full output tensor. This is the approach used in Megatron-LM and is the standard for transformer attention and MLP layers.

**Pipeline parallelism (inter-layer)** assigns different layers of the model to different devices. Device 0 computes layers 1-8, device 1 computes layers 9-16, and so on. Micro-batching is used to fill the pipeline: while device 1 processes micro-batch k, device 0 begins processing micro-batch k+1. The GPipe and PipeDream schedulers formalize this with different tradeoffs between memory and pipeline bubble overhead.

```mermaid
graph TB
    subgraph sub_data_parallel__ddp____4_gpus ["Data Parallel (DDP) — 4 GPUs"]
        direction LR
        DG0["GPU 0\nFull Model\nBatch shard 0"]
        DG1["GPU 1\nFull Model\nBatch shard 1"]
        DG2["GPU 2\nFull Model\nBatch shard 2"]
        DG3["GPU 3\nFull Model\nBatch shard 3"]
        DG0 <-->|"AllReduce\ngradients"| DG1
        DG1 <-->|"AllReduce\ngradients"| DG2
        DG2 <-->|"AllReduce\ngradients"| DG3
    end

    subgraph sub_tensor_parallel___4_gpus__single ["Tensor Parallel — 4 GPUs (single layer)"]
        direction LR
        TG0["GPU 0\nW[:, 0:k/4]"]
        TG1["GPU 1\nW[:, k/4:k/2]"]
        TG2["GPU 2\nW[:, k/2:3k/4]"]
        TG3["GPU 3\nW[:, 3k/4:k]"]
        TG0 <-->|"AllGather\npartial outputs"| TG1
        TG1 <-->|"AllGather\npartial outputs"| TG2
        TG2 <-->|"AllGather\npartial outputs"| TG3
    end

    subgraph sub_pipeline_parallel___4_gpus ["Pipeline Parallel — 4 GPUs"]
        direction LR
        PP0["GPU 0\nLayers 1-8\nStage 0"]
        PP1["GPU 1\nLayers 9-16\nStage 1"]
        PP2["GPU 2\nLayers 17-24\nStage 2"]
        PP3["GPU 3\nLayers 25-32\nStage 3"]
        PP0 -->|"activations\nmicrobatch k"| PP1
        PP1 -->|"activations\nmicrobatch k"| PP2
        PP2 -->|"activations\nmicrobatch k"| PP3
    end
```

### PyTorch FSDP: Fully Sharded Data Parallel

Fully Sharded Data Parallel (FSDP), introduced in PyTorch 1.11 and stabilized in 1.12, enables training models that exceed single-GPU memory by sharding parameters, gradients, and optimizer states across all data-parallel ranks. Each rank holds only `1/N` of the full model parameters. Before a forward or backward pass through a layer, an `AllGather` collective reassembles the full parameters on all ranks; after the backward pass, parameters are re-sharded (discarded on all but the owning rank) to free memory.

```python
import torch
import torch.distributed as dist
from torch.distributed.fsdp import (
    FullyShardedDataParallel as FSDP,
    MixedPrecision,
    BackwardPrefetch,
    ShardingStrategy,
    CPUOffload,
)
from torch.distributed.fsdp.wrap import (
    size_based_auto_wrap_policy,
    transformer_auto_wrap_policy,
)
from transformers import LlamaForCausalLM, LlamaConfig
import functools
import os

def setup_distributed():
    dist.init_process_group(backend="nccl")
    local_rank = int(os.environ["LOCAL_RANK"])
    torch.cuda.set_device(local_rank)
    return local_rank

def build_fsdp_model(local_rank: int) -> FSDP:
    # Mixed precision: forward/backward in bfloat16, optimizer state in float32.
    # bfloat16 has the same exponent range as float32 (avoids gradient underflow)
    # but only 7 mantissa bits (vs 23 for float32) — acceptable for training.
    mixed_precision_policy = MixedPrecision(
        param_dtype=torch.bfloat16,
        reduce_dtype=torch.bfloat16,   # gradient AllReduce in bfloat16
        buffer_dtype=torch.bfloat16,
    )

    # Auto-wrap policy: shard at the transformer block boundary.
    # Each LlamaDecoderLayer becomes an independent FSDP unit —
    # AllGather/parameter-shard happens at the block granularity.
    from transformers.models.llama.modeling_llama import LlamaDecoderLayer
    auto_wrap_policy = functools.partial(
        transformer_auto_wrap_policy,
        transformer_layer_cls={LlamaDecoderLayer},
    )

    config = LlamaConfig(
        hidden_size=4096,
        intermediate_size=11008,
        num_hidden_layers=32,
        num_attention_heads=32,
        max_position_embeddings=4096,
    )

    with torch.device("meta"):
        # Initialize on meta device — no memory allocated yet.
        # FSDP will materialize shards on the correct device during wrapping.
        model = LlamaForCausalLM(config)

    model = FSDP(
        model,
        auto_wrap_policy=auto_wrap_policy,
        mixed_precision=mixed_precision_policy,
        sharding_strategy=ShardingStrategy.FULL_SHARD,  # shard params + grads + optimizer
        cpu_offload=CPUOffload(offload_params=False),   # keep params on GPU; offload optimizer only
        backward_prefetch=BackwardPrefetch.BACKWARD_PRE, # overlap AllGather with backward compute
        device_id=local_rank,
        sync_module_states=True,  # broadcast rank-0 weights to all ranks after materialization
        use_orig_params=True,     # required for torch.compile compatibility
    )

    return model

def train_step(
    model: FSDP,
    optimizer: torch.optim.Optimizer,
    batch: dict,
    grad_accum_steps: int = 4,
) -> float:
    """
    Gradient accumulation: accumulate gradients over `grad_accum_steps` micro-batches
    before the optimizer step. This simulates a larger effective batch size without
    increasing peak memory — critical for large-model fine-tuning.
    """
    model.train()
    total_loss = 0.0

    for step in range(grad_accum_steps):
        micro_batch = {k: v[step::grad_accum_steps].cuda() for k, v in batch.items()}

        # Only synchronize gradients on the last accumulation step.
        # no_sync() context manager suppresses the AllReduce in intermediate steps,
        # reducing communication overhead by a factor of grad_accum_steps.
        ctx = model.no_sync() if step < grad_accum_steps - 1 else contextlib.nullcontext()
        with ctx:
            outputs = model(**micro_batch)
            loss = outputs.loss / grad_accum_steps
            loss.backward()
            total_loss += loss.item()

    # Gradient clipping: clip by global norm across all shards.
    # FSDP.clip_grad_norm_ handles the cross-shard norm computation correctly.
    model.clip_grad_norm_(max_norm=1.0)
    optimizer.step()
    optimizer.zero_grad(set_to_none=True)  # set_to_none=True frees gradient buffers immediately

    return total_loss * grad_accum_steps
```

---

## 7. Model Drift Detection and Monitoring

### Statistical Foundations

Model monitoring is fundamentally an application of **nonparametric hypothesis testing** applied continuously to streaming data. The null hypothesis in every drift test is: "the distribution of this feature (or model output) has not changed since training." The challenge is that this test must be run continuously at production scale, with low latency, and with a false-positive rate calibrated to avoid alert fatigue.

The major drift detection methods differ in what they measure and their statistical power:

**Kolmogorov-Smirnov (KS) test** compares the empirical cumulative distribution functions of two samples. The KS statistic `D = max|F₁(x) - F₂(x)|` is the maximum absolute difference between the two CDFs. It is distribution-free (makes no parametric assumptions), sensitive to differences in both location and shape, but has low power for detecting differences in the tails — which are often precisely where the most consequential distribution shifts occur in production.

**Population Stability Index (PSI)** is the information-theoretic measure most commonly used in financial credit modeling. `PSI = Σ (actual% - expected%) × ln(actual%/expected%)` over histogram bins. PSI < 0.1 indicates negligible shift; 0.1-0.25 indicates moderate shift requiring investigation; > 0.25 indicates significant shift requiring model retraining. PSI is a discretized approximation of the symmetric KL divergence and is sensitive to the binning strategy.

**Maximum Mean Discrepancy (MMD)** measures the distance between distributions in a reproducing kernel Hilbert space (RKHS). For two distributions P and Q, `MMD²(P,Q) = E[k(x,x')] - 2E[k(x,y)] + E[k(y,y')]` where k is a kernel function (typically RBF). MMD is particularly powerful for detecting multivariate distribution shifts that are invisible in marginal distributions — a critical capability when feature correlations shift.

### Concept Drift vs. Data Drift

The distinction is architecturally important for determining the correct response:

**Data drift** (covariate shift): the input distribution `P(X)` changes but the conditional `P(Y|X)` does not. The model's learned function is still correct; it is just being applied to inputs outside its training domain. Response: flag for review; may require retraining with new data, or simply expanding the training distribution.

**Concept drift**: the conditional `P(Y|X)` changes — the relationship between features and labels has fundamentally changed. The model's learned function is now incorrect even for inputs that look like training data. Response: immediate retraining is mandatory. This is the more dangerous and harder-to-detect form of drift, because it requires ground-truth labels (which arrive with a lag in production) to confirm.

```python
import numpy as np
import pandas as pd
from scipy.stats import ks_2samp, chi2_contingency
from scipy.spatial.distance import jensenshannon
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


@dataclass
class DriftReport:
    feature_name: str
    test_statistic: float
    p_value: float
    psi: float
    is_drifted: bool
    severity: str  # "none" | "warning" | "critical"


class ProductionDriftMonitor:
    """
    Multi-method drift monitor designed for production serving systems.
    Combines KS test (sensitivity to location/shape shifts) with PSI
    (industry-standard threshold semantics) for each monitored feature.
    """

    def __init__(
        self,
        reference_data: pd.DataFrame,
        feature_columns: List[str],
        categorical_columns: Optional[List[str]] = None,
        ks_p_value_threshold: float = 0.05,
        psi_warning_threshold: float = 0.1,
        psi_critical_threshold: float = 0.25,
        n_bins: int = 10,
    ):
        self.reference_data = reference_data
        self.feature_columns = feature_columns
        self.categorical_columns = set(categorical_columns or [])
        self.ks_p_value_threshold = ks_p_value_threshold
        self.psi_warning_threshold = psi_warning_threshold
        self.psi_critical_threshold = psi_critical_threshold
        self.n_bins = n_bins

        # Pre-compute reference histograms for PSI calculation.
        # Store bin edges from the reference distribution so that
        # production data is binned identically — PSI is only valid
        # when both distributions use the same bins.
        self._reference_bins: Dict[str, np.ndarray] = {}
        self._reference_hist: Dict[str, np.ndarray] = {}
        self._precompute_reference_stats()

    def _precompute_reference_stats(self):
        for col in self.feature_columns:
            if col in self.categorical_columns:
                continue
            ref_values = self.reference_data[col].dropna().values
            hist, bin_edges = np.histogram(ref_values, bins=self.n_bins)
            # Add small epsilon to avoid log(0) in PSI calculation
            self._reference_hist[col] = (hist + 1e-6) / (hist.sum() + 1e-6 * len(hist))
            self._reference_bins[col] = bin_edges

    def _compute_psi(self, col: str, production_values: np.ndarray) -> float:
        bin_edges = self._reference_bins[col]
        prod_hist, _ = np.histogram(production_values, bins=bin_edges)
        prod_hist_norm = (prod_hist + 1e-6) / (prod_hist.sum() + 1e-6 * len(prod_hist))
        ref_hist_norm = self._reference_hist[col]
        psi = np.sum(
            (prod_hist_norm - ref_hist_norm) * np.log(prod_hist_norm / ref_hist_norm)
        )
        return float(psi)

    def _severity(self, psi: float, p_value: float) -> str:
        if psi >= self.psi_critical_threshold or (p_value < self.ks_p_value_threshold and psi >= self.psi_warning_threshold):
            return "critical"
        if psi >= self.psi_warning_threshold:
            return "warning"
        return "none"

    def compute_drift_report(
        self, production_data: pd.DataFrame, min_samples: int = 100
    ) -> List[DriftReport]:
        reports = []

        for col in self.feature_columns:
            if col not in production_data.columns:
                logger.warning("Column %s missing from production data; skipping drift check.", col)
                continue

            prod_values = production_data[col].dropna().values
            ref_values = self.reference_data[col].dropna().values

            if len(prod_values) < min_samples:
                logger.info(
                    "Column %s has only %d production samples (< %d); drift estimate unreliable.",
                    col, len(prod_values), min_samples,
                )
                continue

            if col in self.categorical_columns:
                # For categorical features, use chi-squared test of independence
                # between reference and production value frequencies.
                ref_counts = pd.Series(ref_values).value_counts()
                prod_counts = pd.Series(prod_values).value_counts()
                all_cats = ref_counts.index.union(prod_counts.index)
                observed = np.array([
                    [ref_counts.get(c, 0) for c in all_cats],
                    [prod_counts.get(c, 0) for c in all_cats],
                ])
                if observed.min() == 0:
                    observed += 1  # Yates correction for sparse categories
                chi2, p_value, _, _ = chi2_contingency(observed)
                stat = float(chi2)
                # PSI analog for categorical: Jensen-Shannon divergence
                ref_p = observed[0] / observed[0].sum()
                prod_p = observed[1] / observed[1].sum()
                psi = float(jensenshannon(ref_p, prod_p))
            else:
                stat, p_value = ks_2samp(ref_values, prod_values)
                psi = self._compute_psi(col, prod_values)

            severity = self._severity(psi, p_value)
            reports.append(DriftReport(
                feature_name=col,
                test_statistic=float(stat),
                p_value=float(p_value),
                psi=psi,
                is_drifted=(severity != "none"),
                severity=severity,
            ))

        return reports

    def emit_prometheus_metrics(self, reports: List[DriftReport], registry=None):
        """
        Emit drift metrics in Prometheus format for integration with
        Grafana dashboards and AlertManager rules.
        """
        try:
            from prometheus_client import Gauge, CollectorRegistry, push_to_gateway
        except ImportError:
            logger.error("prometheus_client not installed; cannot emit metrics.")
            return

        reg = registry or CollectorRegistry()
        psi_gauge = Gauge(
            "ml_feature_psi",
            "Population Stability Index for each monitored feature",
            ["feature_name", "severity"],
            registry=reg,
        )
        drift_gauge = Gauge(
            "ml_feature_drift_detected",
            "Binary indicator: 1 if drift detected, 0 otherwise",
            ["feature_name"],
            registry=reg,
        )

        for report in reports:
            psi_gauge.labels(
                feature_name=report.feature_name,
                severity=report.severity,
            ).set(report.psi)
            drift_gauge.labels(feature_name=report.feature_name).set(
                1.0 if report.is_drifted else 0.0
            )
```

---

## 8. The Model Registry and Promotion Lifecycle

### State Machine for Model Lifecycle

A model registry is not a file server. It is a **state machine** that enforces the promotion lifecycle of model artifacts from experimentation to production. The canonical state transitions are:

```mermaid
flowchart TD
    START((" ")):::terminal
    REG["Registered"]
    STG["Staging"]
    PRD["Production"]
    ARC["Archived"]
    END((" ")):::terminal

    START -->|"artifact logged by training job"| REG
    REG -->|"automated validation gate passes\n(schema check, performance threshold, drift gate)"| STG
    STG -->|"manual approval OR\nautomated canary analysis passes"| PRD
    STG -->|"validation failure\n(rolled back, flagged for investigation)"| REG
    PRD -->|"new Production version promoted\n(previous version archived, not deleted)"| ARC
    PRD -->|"performance regression detected\n(automated rollback triggered)"| STG
    ARC -->|"retention policy enforcement\n(after N days or N versions)"| END

    classDef terminal fill:#111,stroke:#111,color:#111,width:12px,height:12px
    classDef state fill:#1e3a5f,stroke:#4a90d9,stroke-width:2px,color:#e8f0fe,rx:6,ry:6
    class REG,STG,PRD,ARC state
```

No model should ever transition from `Registered` directly to `Production`. The `Staging` state exists specifically to enforce that every production deployment was preceded by an automated validation run against a held-out evaluation set, with explicit human or automated approval. This is the enforcement mechanism for the "fail-closed validation gate" invariant established in Section 1.

### MLflow Model Registry: Production Integration

```python
import mlflow
from mlflow.tracking import MlflowClient
from mlflow.entities.model_registry import ModelVersion
import time
import logging
from typing import Optional

logger = logging.getLogger(__name__)

MLFLOW_TRACKING_URI = "postgresql://mlflow_user:${MLFLOW_DB_PASS}@mlflow-db.internal:5432/mlflow"
MODEL_NAME = "credit-risk-classifier"


def register_and_validate_model(
    run_id: str,
    model_artifact_path: str = "model",
    evaluation_auc: float = 0.0,
    baseline_auc: float = 0.0,
    min_auc_threshold: float = 0.80,
    min_improvement: float = 0.005,
) -> Optional[ModelVersion]:
    """
    Register a trained model and conditionally transition it to Staging.
    Does NOT transition to Production — that requires separate canary analysis.
    """
    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
    client = MlflowClient()

    # Register the model — this creates a new version in the registry
    # linked to the training run's artifact URI.
    model_uri = f"runs:/{run_id}/{model_artifact_path}"
    model_version = mlflow.register_model(model_uri=model_uri, name=MODEL_NAME)
    logger.info("Registered model version %s for run %s", model_version.version, run_id)

    # Validation gate: absolute performance threshold + relative improvement
    if evaluation_auc < min_auc_threshold:
        client.update_model_version(
            name=MODEL_NAME,
            version=model_version.version,
            description=(
                f"VALIDATION FAILED: AUC {evaluation_auc:.4f} < threshold {min_auc_threshold:.4f}. "
                f"Model will not be promoted."
            ),
        )
        logger.warning(
            "Model version %s rejected: AUC %.4f < threshold %.4f",
            model_version.version, evaluation_auc, min_auc_threshold,
        )
        return None

    if evaluation_auc < baseline_auc + min_improvement:
        logger.warning(
            "Model version %s rejected: AUC improvement %.4f < required %.4f",
            model_version.version, evaluation_auc - baseline_auc, min_improvement,
        )
        return None

    # Set tags for auditability — these are queryable in MLflow's search API
    client.set_model_version_tag(MODEL_NAME, model_version.version, "evaluation_auc", str(evaluation_auc))
    client.set_model_version_tag(MODEL_NAME, model_version.version, "baseline_auc", str(baseline_auc))
    client.set_model_version_tag(MODEL_NAME, model_version.version, "validated_by", "automated_pipeline")

    # Transition to Staging — not Production
    client.transition_model_version_stage(
        name=MODEL_NAME,
        version=model_version.version,
        stage="Staging",
        archive_existing_versions=False,  # keep current Staging version for rollback
    )
    logger.info("Model version %s promoted to Staging (AUC=%.4f)", model_version.version, evaluation_auc)

    return model_version


def promote_staging_to_production(
    version: str,
    approval_token: str,
    expected_approver: str,
) -> bool:
    """
    Final production promotion gate. Requires a valid approval token
    generated by the canary analysis system — not a human clicking a button.
    In practice, this is called by the canary analysis job after Argo Rollouts
    confirms the error rate delta is within acceptable bounds.
    """
    client = MlflowClient()
    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)

    # Verify the approval token is recorded as a tag on this model version.
    # This creates an auditable chain: the canary system sets the tag;
    # this function verifies it before promoting.
    mv = client.get_model_version(MODEL_NAME, version)
    recorded_token = mv.tags.get("canary_approval_token")
    recorded_approver = mv.tags.get("approved_by")

    if recorded_token != approval_token or recorded_approver != expected_approver:
        logger.error(
            "Invalid approval token for model version %s. Expected approver: %s, got: %s",
            version, expected_approver, recorded_approver,
        )
        return False

    client.transition_model_version_stage(
        name=MODEL_NAME,
        version=version,
        stage="Production",
        archive_existing_versions=True,  # archive previous Production version
    )
    logger.info("Model version %s promoted to Production.", version)
    return True
```

---

## 9. End-to-End Failure Mode Analysis

### Taxonomy of Production ML Failures

The following failure modes are drawn from post-mortem analyses across large-scale production ML systems. Each represents a distinct failure class with a specific root cause and architectural mitigation.

```mermaid
graph TB
    subgraph sub_data_layer_failures ["Data Layer Failures"]
        F1["Schema drift\n(upstream column type change)"]
        F2["Silent data loss\n(partial pipeline failure)"]
        F3["Training-serving skew\n(offline/online feature divergence)"]
        F4["Label leakage\n(future data in training features)"]
    end

    subgraph sub_training_failures ["Training Failures"]
        F5["Gradient explosion\n(loss goes to NaN after N steps)"]
        F6["GPU OOM mid-epoch\n(batch size too large for sequence length)"]
        F7["Checkpoint corruption\n(disk full during checkpoint write)"]
        F8["Nondeterminism\n(different results across hardware)"]
    end

    subgraph sub_serving_failures ["Serving Failures"]
        F9["Model version skew\n(preprocessing != training preprocessing)"]
        F10["Latency regression\n(dynamic batching timeout misconfig)"]
        F11["Silent prediction error\n(integer overflow in feature encoding)"]
        F12["Cold start spike\n(model not loaded at traffic onset)"]
    end

    subgraph sub_operational_failures ["Operational Failures"]
        F13["Concept drift\n(P(Y|X) changes without alert)"]
        F14["Feedback loop\n(model predictions affect future training data)"]
        F15["Retraining cascade\n(automated retraining on drifted data)"]
    end
```

**Training-serving skew (F3)** is the most prevalent silent failure. The root cause is almost always that feature computation code exists in two places — a batch job for training and an online service for serving — and the two implementations diverge over time. The architectural mitigation is the feature store described in Section 3: a single parameterized implementation that generates both offline and online features from the same code path.

**Concept drift triggering a retraining cascade (F13+F15)** is the most dangerous operational failure. The scenario: drift detection fires, automated retraining triggers, the new model trains on the drifted data distribution, the drift monitor compares the new model's output distribution to the old model's (not to the original training distribution), finds no drift (both models are now calibrated to the new distribution), promotes the new model, and the cycle continues. The mitigation is to maintain a **pinned reference distribution** — the statistical properties of the original healthy training data — against which all future models are compared, regardless of how many retraining cycles have elapsed.

**Feedback loops (F14)** occur when a deployed model's predictions influence user behavior, which then affects the next training dataset. A recommendation model trained on historical clicks will generate recommendations that drive future clicks, creating training data that reflects the model's past biases rather than user preferences. This is the **filter bubble problem** at the infrastructure level. The only robust mitigation is **counterfactual logging**: for a random sample of requests, serve a random baseline (or the previous model version) instead of the production model, and log these counterfactual exposures separately. Train the next model on data that includes counterfactual samples to maintain an unbiased view of the underlying distribution.

---

## 10. Observability: Metrics, Tracing, and Alerting

### The Three Signals of ML Observability

Classical service observability focuses on latency, error rate, and throughput. ML systems require three additional signal classes:

**Data quality signals**: schema validation pass rates, null rates per feature, out-of-range value counts, referential integrity failures between feature store and raw data sources. These are pre-model signals — they fire before the model runs.

**Model behavioral signals**: prediction distribution statistics (mean, variance, percentiles), confidence score distributions, class balance in multi-class outputs, top-k feature attribution shifts (from SHAP or LIME). These are post-model signals that characterize what the model is doing without requiring ground-truth labels.

**Outcome signals**: actual label outcomes joined back to prediction logs (with the appropriate time lag), AUC/precision/recall/F1 computed on rolling windows, calibration curves. These are the gold-standard signals but arrive with delay — anywhere from minutes (online systems with immediate feedback) to weeks (credit default models where the label is "did this loan default?").

### AlertManager Rules for ML Pipelines

```yaml
# prometheus/alerts/ml_pipeline.yml
groups:
  - name: ml_pipeline_alerts
    interval: 60s
    rules:
      # Critical: model is making predictions but drift is severe
      - alert: CriticalFeatureDriftDetected
        expr: |
          max by (model_name) (
            ml_feature_psi{severity="critical"}
          ) > 0.25
        for: 5m
        labels:
          severity: critical
          team: ml-platform
        annotations:
          summary: "Critical data drift in model {{ $labels.model_name }}"
          description: |
            PSI > 0.25 detected for {{ $labels.feature_name }} in model {{ $labels.model_name }}.
            This indicates the input distribution has shifted significantly from training.
            Automatic retraining has been triggered. Review deployment decision.
          runbook_url: "https://wiki.internal/ml-platform/runbooks/feature-drift"

      # Warning: prediction confidence distribution has shifted
      - alert: PredictionConfidenceShift
        expr: |
          abs(
            avg_over_time(ml_prediction_confidence_mean[1h])
            - avg_over_time(ml_prediction_confidence_mean[24h] offset 24h)
          ) > 0.1
        for: 15m
        labels:
          severity: warning
          team: ml-platform
        annotations:
          summary: "Prediction confidence distribution shifted for {{ $labels.model_name }}"

      # Critical: serving latency P99 exceeds SLA
      - alert: InferenceLatencySLABreach
        expr: |
          histogram_quantile(0.99,
            rate(triton_inference_request_duration_seconds_bucket[5m])
          ) > 0.05  # 50ms P99 SLA
        for: 2m
        labels:
          severity: critical
          team: ml-platform
        annotations:
          summary: "Inference P99 latency > 50ms for model {{ $labels.model }}"

      # Warning: pipeline stage has been running longer than expected
      - alert: TrainingJobStalledOrSlow
        expr: |
          time() - kfp_run_start_time_seconds{status="RUNNING"} > 7200  # 2 hours
        for: 10m
        labels:
          severity: warning
          team: ml-platform
        annotations:
          summary: "Training job {{ $labels.run_name }} has been running for > 2 hours"

      # Critical: model validation gate rejected a candidate
      - alert: ModelValidationGateFailed
        expr: increase(ml_model_validation_failures_total[1h]) > 0
        for: 0m
        labels:
          severity: warning
          team: ml-platform
        annotations:
          summary: "Model candidate rejected by validation gate"
          description: "A trained model failed automated validation. Manual review required."
```

### Structured Prediction Logging

Every prediction made in production must be logged in a structured format that enables post-hoc analysis, drift detection, and eventual label joining. The logging schema must balance completeness (capturing everything needed for debugging) against volume (prediction logs at high traffic are among the largest data streams in an ML system).

```python
import json
import time
import hashlib
from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional
import uuid


@dataclass
class PredictionLog:
    # Request identification
    request_id: str
    model_name: str
    model_version: str

    # Timing
    request_timestamp_ms: int           # Unix milliseconds — sortable, timezone-unambiguous
    inference_latency_ms: float

    # Input features — store a hash for privacy compliance,
    # full features only for sampled requests (1% by default).
    feature_hash: str                   # SHA-256 of serialized feature vector
    features_sampled: Optional[Dict[str, Any]]  # None for 99% of requests

    # Output
    prediction_label: Any              # top-1 prediction or regression output
    prediction_scores: List[float]     # full probability vector or top-k scores
    prediction_confidence: float        # max(scores) for classification

    # Metadata
    serving_host: str
    experiment_id: Optional[str]       # set for A/B experiment traffic
    is_counterfactual: bool            # True for random baseline exposures


def log_prediction(
    model_name: str,
    model_version: str,
    features: Dict[str, float],
    prediction_label: Any,
    prediction_scores: List[float],
    serving_host: str,
    sample_rate: float = 0.01,
    experiment_id: Optional[str] = None,
    counterfactual_rate: float = 0.001,
) -> PredictionLog:
    feature_bytes = json.dumps(features, sort_keys=True).encode()
    feature_hash = hashlib.sha256(feature_bytes).hexdigest()

    import random
    features_sampled = features if random.random() < sample_rate else None
    is_counterfactual = random.random() < counterfactual_rate

    return PredictionLog(
        request_id=str(uuid.uuid4()),
        model_name=model_name,
        model_version=model_version,
        request_timestamp_ms=int(time.time() * 1000),
        inference_latency_ms=0.0,   # caller fills this in after inference
        feature_hash=feature_hash,
        features_sampled=features_sampled,
        prediction_label=prediction_label,
        prediction_scores=prediction_scores,
        prediction_confidence=max(prediction_scores),
        serving_host=serving_host,
        experiment_id=experiment_id,
        is_counterfactual=is_counterfactual,
    )
```

---

## 11. Summary: Architectural Principles

The operational reliability of a production ML system rests on a small number of architectural principles that, when violated, produce failures that are difficult or impossible to diagnose after the fact:

**Artifact lineage is non-negotiable.** Every model in production must have a queryable provenance graph back to its training data. This is enforced structurally through the MLMD store in Kubeflow, the artifact lineage API in MLflow, or equivalent tooling — not through documentation or convention.

**The feature store is the single source of truth for feature computation.** Training-serving skew is eliminated by architectural constraint (a single code path for offline and online feature retrieval), not by code review discipline.

**Validation gates are fail-closed.** The default behavior of a promotion pipeline on ambiguous or missing results is to block, not to allow. Automated promotion to Production requires explicit, auditable approval artifacts — not the absence of failure signals.

**Drift detection requires a pinned reference distribution.** The reference against which production data is compared must be the original training distribution, preserved as an immutable artifact. Comparing to recent production data defeats the purpose: a gradually drifting system will appear stable under relative comparison.

**Counterfactual logging is required for feedback loop prevention.** Any system where model predictions influence future training data must include a mechanism for collecting unbiased observations — typically a random traffic fraction served with a baseline policy whose outcomes are logged and kept separate from the main training corpus.

These principles are not aspirational. They are the minimum viable architectural requirements for a system that can be operated, debugged, and improved over time without accumulating invisible technical debt in the form of model quality degradation.
