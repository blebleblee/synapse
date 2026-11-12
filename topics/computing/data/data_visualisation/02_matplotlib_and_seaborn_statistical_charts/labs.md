# Operational Verification Labs: 02 Matplotlib And Seaborn Statistical Charts

## Objective & Environment Setup

The objective of this lab is to provide hands-on experience with creating and customizing statistical charts using Matplotlib and Seaborn in Python. This lab assumes a Python 3.11+ environment with the following packages installed:

- NumPy
- Pandas
- Matplotlib
- Seaborn
- Scikit-learn

You can set up the environment using the following commands:

```bash
# Create a virtual environment
python3.11 -m venv matplotlib-seaborn-lab

# Activate the virtual environment
source matplotlib-seaborn-lab/bin/activate

# Install required packages
pip install numpy pandas matplotlib seaborn scikit-learn
```

## Exercise 1: Hands-On Implementation & Pipeline Execution

In this exercise, we will create a pipeline to generate statistical charts using Matplotlib and Seaborn. We will use a synthetic dataset generated with NumPy and Pandas to demonstrate the creation of histograms, box plots, and pair plots.

### Complete, Runnable Python Script

```python
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Set the aesthetic style of the plots
sns.set(style="whitegrid")

# Generate synthetic data
np.random.seed(42)
data = {
    'Feature1': np.random.normal(0, 1, 1000),
    'Feature2': np.random.normal(5, 2, 1000),
    'Category': np.random.choice(['A', 'B', 'C'], 1000)
}
df = pd.DataFrame(data)

# Exercise 1.1: Histogram of Feature1
plt.figure(figsize=(10, 6))
sns.histplot(df['Feature1'], bins=30, kde=True)
plt.title('Histogram of Feature1 with KDE')
plt.xlabel('Feature1')
plt.ylabel('Frequency')
plt.show()

# Exercise 1.2: Box Plot of Feature2 by Category
plt.figure(figsize=(10, 6))
sns.boxplot(x='Category', y='Feature2', data=df)
plt.title('Box Plot of Feature2 by Category')
plt.xlabel('Category')
plt.ylabel('Feature2')
plt.show()

# Exercise 1.3: Pair Plot of Features
sns.pairplot(df, hue='Category', diag_kind='kde')
plt.suptitle('Pair Plot of Features', y=1.02)
plt.show()
```

### Explanation

1. **Data Generation**: We generate a synthetic dataset with two features (`Feature1` and `Feature2`) and a categorical variable (`Category`).
2. **Histogram with KDE**: We create a histogram of `Feature1` with a Kernel Density Estimate (KDE) overlay to visualize the distribution.
3. **Box Plot**: We create a box plot of `Feature2` grouped by the `Category` variable to compare the distributions across categories.
4. **Pair Plot**: We create a pair plot to visualize pairwise relationships in the dataset, coloring the points by the `Category` variable.

## Exercise 2: Hyperparameter Tuning & Empirical Benchmarking

In this exercise, we will explore the impact of different hyperparameters on the appearance of the charts. We will measure the time taken to generate each chart and compare the results.

### Real Benchmarking Code

```python
import time

# Exercise 2.1: Benchmark Histogram with KDE
start_time = time.time()
plt.figure(figsize=(10, 6))
sns.histplot(df['Feature1'], bins=30, kde=True)
plt.title('Histogram of Feature1 with KDE')
plt.xlabel('Feature1')
plt.ylabel('Frequency')
plt.show()
hist_kde_time = time.time() - start_time
print(f"Time taken for Histogram with KDE: {hist_kde_time:.4f} seconds")

# Exercise 2.2: Benchmark Box Plot
start_time = time.time()
plt.figure(figsize=(10, 6))
sns.boxplot(x='Category', y='Feature2', data=df)
plt.title('Box Plot of Feature2 by Category')
plt.xlabel('Category')
plt.ylabel('Feature2')
plt.show()
box_plot_time = time.time() - start_time
print(f"Time taken for Box Plot: {box_plot_time:.4f} seconds")

# Exercise 2.3: Benchmark Pair Plot
start_time = time.time()
sns.pairplot(df, hue='Category', diag_kind='kde')
plt.suptitle('Pair Plot of Features', y=1.02)
plt.show()
pair_plot_time = time.time() - start_time
print(f"Time taken for Pair Plot: {pair_plot_time:.4f} seconds")
```

### Explanation

1. **Benchmarking Histogram with KDE**: We measure the time taken to generate a histogram with a KDE overlay.
2. **Benchmarking Box Plot**: We measure the time taken to generate a box plot.
3. **Benchmarking Pair Plot**: We measure the time taken to generate a pair plot.

## Exercise 3: Stress Testing, Edge Cases & Failure Mitigation

In this exercise, we will test the robustness of the charts under various edge cases, such as missing data and extreme values.

### Reproducing Failure Modes, Testing Edge Cases, and Implementing Guardrails

```python
# Exercise 3.1: Introduce Missing Data
df_with_missing = df.copy()
df_with_missing.loc[::10, 'Feature1'] = np.nan
df_with_missing.loc[::15, 'Feature2'] = np.nan

# Exercise 3.2: Histogram with Missing Data
plt.figure(figsize=(10, 6))
sns.histplot(df_with_missing['Feature1'].dropna(), bins=30, kde=True)
plt.title('Histogram of Feature1 with Missing Data')
plt.xlabel('Feature1')
plt.ylabel('Frequency')
plt.show()

# Exercise 3.3: Box Plot with Missing Data
plt.figure(figsize=(10, 6))
sns.boxplot(x='Category', y='Feature2', data=df_with_missing)
plt.title('Box Plot of Feature2 with Missing Data')
plt.xlabel('Category')
plt.ylabel('Feature2')
plt.show()

# Exercise 3.4: Pair Plot with Missing Data
sns.pairplot(df_with_missing, hue='Category', diag_kind='kde')
plt.suptitle('Pair Plot of Features with Missing Data', y=1.02)
plt.show()
```

### Explanation

1. **Introduce Missing Data**: We introduce missing values in the dataset to simulate real-world scenarios.
2. **Histogram with Missing Data**: We generate a histogram of `Feature1` after dropping missing values.
3. **Box Plot with Missing Data**: We generate a box plot of `Feature2` grouped by the `Category` variable, handling missing values.
4. **Pair Plot with Missing Data**: We generate a pair plot of the dataset with missing values.

## Verification Checklist & Quick Reference Cheat Sheet

### Essential Python Methods and Parameters

| Method/Parameter | Description |
|------------------|-------------|
| `sns.set(style="whitegrid")` | Sets the aesthetic style of the plots. |
| `sns.histplot()` | Creates a histogram with optional KDE overlay. |
| `sns.boxplot()` | Creates a box plot to compare distributions across categories. |
| `sns.pairplot()` | Creates a pair plot to visualize pairwise relationships. |
| `plt.figure(figsize=(10, 6))` | Sets the figure size for the plot. |
| `plt.title()` | Sets the title of the plot. |
| `plt.xlabel()` | Sets the x-axis label of the plot. |
| `plt.ylabel()` | Sets the y-axis label of the plot. |
| `plt.show()` | Displays the plot. |
| `time.time()` | Returns the current time in seconds since the epoch. |

### Verification Flags

- **Histogram with KDE**: Verify the presence of the KDE overlay and the distribution of `Feature1`.
- **Box Plot**: Verify the box plot for each category and the distribution of `Feature2`.
- **Pair Plot**: Verify the pairwise relationships and the distribution of each feature.
- **Benchmarking**: Verify the time taken to generate each chart.
- **Missing Data Handling**: Verify the handling of missing data in each chart.

This lab provides a comprehensive hands-on experience with creating and customizing statistical charts using Matplotlib and Seaborn, ensuring that you can apply these techniques in real-world data visualization tasks.
