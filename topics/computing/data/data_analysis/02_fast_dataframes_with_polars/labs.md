# Operational Verification Labs: 02 Fast Dataframes With Polars

## Objective & Environment Setup

This lab guides you through hands-on implementation, pipeline execution, hyperparameter tuning, and stress testing of Polars, a high-performance, in-memory data processing library for Python. To begin, ensure you have Python 3.11+ installed on your system. Install the required packages using pip:

```bash
pip install polars pandas numpy pytorch huggingface transformers
```

Configure your Polars environment by setting the following environment variables:

```python
import os

os.environ['POLARS_JIT'] = 'true'  # Enable just-in-time compilation
os.environ['POLARS_NUM_THREADS'] = '8'  # Set number of threads for parallel processing
```

## Exercise 1: Hands-On Implementation & Pipeline Execution

Implement a basic data processing pipeline using Polars. This example loads a sample dataset, performs filtering and aggregation, and outputs the result to a Pandas DataFrame.

```python
import polars as pl
import pandas as pd

# Load sample dataset
df = pl.read_csv('https://raw.githubusercontent.com/polars-py/polars/main/docs/data/iris.csv')

# Filter rows where sepal length is greater than 5
filtered_df = df.filter(pl.col('sepal_length') > 5)

# Group by species and calculate mean sepal width
aggregated_df = filtered_df.groupby('species').agg(pl.mean('sepal_width'))

# Convert Polars DataFrame to Pandas DataFrame
pandas_df = aggregated_df.to_pandas()

print(pandas_df)
```

## Exercise 2: Hyperparameter Tuning & Empirical Benchmarking

Measure the performance of Polars under different hyperparameter settings. This example tunes the number of threads and the JIT compilation threshold.

```python
import time
import numpy as np

# Define hyperparameter search space
num_threads = [4, 8, 16]
jit_threshold = [0.5, 0.7, 0.9]

# Define benchmark function
def benchmark(num_threads, jit_threshold):
    pl.set_options(threads=num_threads, jit_threshold=jit_threshold)
    df = pl.read_csv('https://raw.githubusercontent.com/polars-py/polars/main/docs/data/iris.csv')
    filtered_df = df.filter(pl.col('sepal_length') > 5)
    aggregated_df = filtered_df.groupby('species').agg(pl.mean('sepal_width'))
    return aggregated_df.compute()

# Perform hyperparameter tuning
best_num_threads = None
best_jit_threshold = None
best_time = float('inf')

for num_thread in num_threads:
    for jit_thres in jit_threshold:
        start_time = time.time()
        aggregated_df = benchmark(num_thread, jit_thres)
        end_time = time.time()
        elapsed_time = end_time - start_time
        if elapsed_time < best_time:
            best_num_threads = num_thread
            best_jit_threshold = jit_thres
            best_time = elapsed_time

print(f'Best hyperparameters: num_threads={best_num_threads}, jit_threshold={best_jit_threshold}')
```

## Exercise 3: Stress Testing, Edge Cases & Failure Mitigation

Reproduce failure modes and test edge cases to ensure robustness. This example simulates a memory overflow by loading a large dataset.

```python
import polars as pl

# Simulate memory overflow by loading a large dataset
large_df = pl.read_csv('https://raw.githubusercontent.com/polars-py/polars/main/docs/data/large_dataset.csv')

# Attempt to perform aggregation on the large dataset
try:
    aggregated_df = large_df.groupby('species').agg(pl.mean('sepal_width'))
except MemoryError as e:
    print(f'Memory error caught: {e}')
```

## Verification Checklist & Quick Reference Cheat Sheet

| Python Method | Parameters | Verification Flags |
| --- | --- | --- |
| `pl.read_csv` | `path`, `header`, `infer_schema` | `infer_schema=True` |
| `pl.filter` | `condition` | `condition=pl.col('sepal_length') > 5` |
| `pl.groupby` | `by` | `by=['species']` |
| `pl.agg` | `aggr` | `aggr=[pl.mean('sepal_width')]` |
| `pl.compute` |  |  |
| `pl.set_options` | `threads`, `jit_threshold` | `threads=8`, `jit_threshold=0.7` |

Note: This is a basic guide and you should adapt it to your specific use case and requirements. Additionally, you may need to modify the code to fit your specific environment and dataset.
