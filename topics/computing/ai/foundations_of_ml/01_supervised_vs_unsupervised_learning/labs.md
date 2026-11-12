# Operational Verification Labs: 01 Supervised Vs Unsupervised Learning

## Objective & Environment Setup

The objective of this lab is to provide hands-on experience with both supervised and unsupervised learning techniques. We will implement and evaluate these techniques using Python, leveraging popular libraries such as Scikit-learn, NumPy, and HuggingFace. The lab assumes a Python 3.11+ environment with the following packages installed:

- Scikit-learn
- NumPy
- HuggingFace Transformers
- Matplotlib

To set up the environment, execute the following commands in your terminal:

```bash
pip install scikit-learn numpy transformers matplotlib
```

## Exercise 1: Hands-On Implementation & Pipeline Execution

In this exercise, we will implement both a supervised learning model (Logistic Regression) and an unsupervised learning model (K-Means Clustering) using Scikit-learn. We will use the Iris dataset for supervised learning and the MNIST dataset for unsupervised learning.

### Supervised Learning: Logistic Regression on Iris Dataset

The Iris dataset is a classic dataset for classification tasks. It contains 150 samples from three species of Iris flowers (Iris setosa, Iris versicolor, and Iris virginica), with four features each.

```python
import numpy as np
from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report

# Load the Iris dataset
iris = load_iris()
X, y = iris.data, iris.target

# Split the dataset into training and testing sets
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Initialize and train the Logistic Regression model
model = LogisticRegression(max_iter=200)
model.fit(X_train, y_train)

# Make predictions on the test set
y_pred = model.predict(X_test)

# Evaluate the model
accuracy = accuracy_score(y_test, y_pred)
report = classification_report(y_test, y_pred)

print(f"Accuracy: {accuracy}")
print("Classification Report:")
print(report)
```

### Unsupervised Learning: K-Means Clustering on MNIST Dataset

The MNIST dataset is a well-known dataset for handwritten digit recognition. We will use a subset of the dataset to perform K-Means clustering.

```python
from sklearn.datasets import fetch_openml
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
import matplotlib.pyplot as plt

# Load the MNIST dataset
mnist = fetch_openml('mnist_784', version=1)
X, y = mnist["data"], mnist["target"]

# Use only a subset of the dataset for clustering
X_subset = X[:1000]
y_subset = y[:1000]

# Reduce dimensionality for visualization
pca = PCA(n_components=2)
X_reduced = pca.fit_transform(X_subset)

# Initialize and train the K-Means model
kmeans = KMeans(n_clusters=10, random_state=42)
kmeans.fit(X_reduced)

# Plot the clusters
plt.figure(figsize=(8, 6))
plt.scatter(X_reduced[:, 0], X_reduced[:, 1], c=kmeans.labels_, cmap='viridis', marker='o', edgecolor='k', s=50)
plt.title("K-Means Clustering on MNIST Dataset")
plt.xlabel("PCA Component 1")
plt.ylabel("PCA Component 2")
plt.colorbar(label="Cluster Label")
plt.show()
```

## Exercise 2: Hyperparameter Tuning & Empirical Benchmarking

In this exercise, we will perform hyperparameter tuning for the Logistic Regression model and evaluate its performance using accuracy and convergence curves.

### Hyperparameter Tuning for Logistic Regression

We will use GridSearchCV to find the best hyperparameters for the Logistic Regression model.

```python
from sklearn.model_selection import GridSearchCV

# Define the parameter grid
param_grid = {
    'C': [0.1, 1, 10, 100],
    'solver': ['liblinear', 'saga']
}

# Initialize GridSearchCV
grid_search = GridSearchCV(LogisticRegression(max_iter=200), param_grid, cv=5, scoring='accuracy')

# Fit GridSearchCV
grid_search.fit(X_train, y_train)

# Print the best parameters and best score
print(f"Best Parameters: {grid_search.best_params_}")
print(f"Best Cross-Validation Accuracy: {grid_search.best_score_}")

# Evaluate the best model on the test set
best_model = grid_search.best_estimator_
y_pred_best = best_model.predict(X_test)
accuracy_best = accuracy_score(y_test, y_pred_best)
report_best = classification_report(y_test, y_pred_best)

print(f"Test Set Accuracy with Best Model: {accuracy_best}")
print("Test Set Classification Report with Best Model:")
print(report_best)
```

### Convergence Curves for Logistic Regression

We will plot the convergence curves for different values of the regularization parameter `C`.

```python
import matplotlib.pyplot as plt

# Define a range of C values
C_values = np.logspace(-4, 4, 10)

# Initialize lists to store the training and validation accuracies
train_accuracies = []
val_accuracies = []

# Train and evaluate the model for each C value
for C in C_values:
    model = LogisticRegression(C=C, max_iter=200)
    model.fit(X_train, y_train)
    train_accuracies.append(model.score(X_train, y_train))
    val_accuracies.append(model.score(X_test, y_test))

# Plot the convergence curves
plt.figure(figsize=(10, 6))
plt.plot(C_values, train_accuracies, label='Training Accuracy', marker='o')
plt.plot(C_values, val_accuracies, label='Validation Accuracy', marker='o')
plt.xscale('log')
plt.xlabel('C')
plt.ylabel('Accuracy')
plt.title('Convergence Curves for Logistic Regression')
plt.legend()
plt.grid(True)
plt.show()
```

## Exercise 3: Stress Testing, Edge Cases & Failure Mitigation

In this exercise, we will test the robustness of our models by introducing edge cases and implementing guardrails or error handling.

### Stress Testing Logistic Regression

We will test the Logistic Regression model with a noisy dataset and evaluate its performance.

```python
from sklearn.utils import resample

# Introduce noise to the dataset
X_noisy, y_noisy = resample(X, y, random_state=42)
X_noisy += np.random.normal(0, 1, X_noisy.shape)

# Split the noisy dataset into training and testing sets
X_train_noisy, X_test_noisy, y_train_noisy, y_test_noisy = train_test_split(X_noisy, y_noisy, test_size=0.2, random_state=42)

# Train the Logistic Regression model on the noisy dataset
model_noisy = LogisticRegression(max_iter=200)
model_noisy.fit(X_train_noisy, y_train_noisy)

# Make predictions on the test set
y_pred_noisy = model_noisy.predict(X_test_noisy)

# Evaluate the model
accuracy_noisy = accuracy_score(y_test_noisy, y_pred_noisy)
report_noisy = classification_report(y_test_noisy, y_pred_noisy)

print(f"Noisy Dataset Accuracy: {accuracy_noisy}")
print("Noisy Dataset Classification Report:")
print(report_noisy)
```

### Edge Cases for K-Means Clustering

We will test the K-Means clustering model with edge cases such as an empty dataset and a dataset with a single point.

```python
# Test with an empty dataset
try:
    kmeans_empty = KMeans(n_clusters=10, random_state=42)
    kmeans_empty.fit(np.array([]).reshape(0, 2))
except ValueError as e:
    print(f"Error with empty dataset: {e}")

# Test with a dataset with a single point
X_single = np.array([[0, 0]])
kmeans_single = KMeans(n_clusters=1, random_state=42)
kmeans_single.fit(X_single)

# Print the cluster center
print(f"Cluster Center for Single Point: {kmeans_single.cluster_centers_}")
```

## Verification Checklist & Quick Reference Cheat Sheet

| Method/Parameter | Description | Usage |
|------------------|-------------|-------|
| `train_test_split` | Splits the dataset into training and testing sets | `train_test_split(X, y, test_size=0.2, random_state=42)` |
| `LogisticRegression` | Implements logistic regression for classification | `LogisticRegression(max_iter=200)` |
| `accuracy_score` | Computes the accuracy of the model | `accuracy_score(y_true, y_pred)` |
| `classification_report` | Generates a detailed classification report | `classification_report(y_true, y_pred)` |
| `GridSearchCV` | Performs hyperparameter tuning using cross-validation | `GridSearchCV(estimator, param_grid, cv=5, scoring='accuracy')` |
| `KMeans` | Implements K-Means clustering | `KMeans(n_clusters=10, random_state=42)` |
| `PCA` | Performs principal component analysis for dimensionality reduction | `PCA(n_components=2)` |
| `resample` | Resamples the dataset with replacement | `resample(X, y, random_state=42)` |

This lab provides a comprehensive hands-on experience with both supervised and unsupervised learning techniques, including model implementation, hyperparameter tuning, and robustness testing.
