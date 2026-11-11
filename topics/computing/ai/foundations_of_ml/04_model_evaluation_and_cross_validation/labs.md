# Operational Verification Labs: 04 Model Evaluation And Cross Validation

## Objective & Environment Setup

### Objective
The primary objective of this lab is to provide hands-on experience with model evaluation and cross-validation techniques in the context of machine learning. This lab will guide you through implementing evaluation pipelines, hyperparameter tuning, and stress testing using real, executable Python scripts. By the end of this lab, you will have a comprehensive understanding of how to evaluate and validate machine learning models effectively.

### Environment Setup
Ensure you have a Python 3.11+ environment set up with the following packages:
- `scikit-learn`
- `numpy`
- `pandas`
- `matplotlib`
- `seaborn`
- `torch` (optional, for deep learning models)
- `huggingface` (optional, for pre-trained models)

You can install these packages using pip:

```bash
pip install scikit-learn numpy pandas matplotlib seaborn torch transformers
```

## Exercise 1: Hands-On Implementation & Pipeline Execution

In this exercise, we will implement a simple machine learning pipeline using a synthetic dataset. We will train a logistic regression model and evaluate its performance using cross-validation.

### Complete, Runnable Python Script

```python
import numpy as np
import pandas as pd
from sklearn.datasets import make_classification
from sklearn.model_selection import train_test_split, cross_val_score, KFold
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import matplotlib.pyplot as plt
import seaborn as sns

# Generate synthetic dataset
X, y = make_classification(n_samples=1000, n_features=20, n_informative=2, n_redundant=10, random_state=42)

# Split the dataset into training and testing sets
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Initialize the logistic regression model
model = LogisticRegression(max_iter=200)

# Train the model
model.fit(X_train, y_train)

# Predict on the test set
y_pred = model.predict(X_test)

# Evaluate the model
accuracy = accuracy_score(y_test, y_pred)
print(f"Accuracy: {accuracy:.2f}")

# Print classification report
print("Classification Report:")
print(classification_report(y_test, y_pred))

# Print confusion matrix
conf_matrix = confusion_matrix(y_test, y_pred)
sns.heatmap(conf_matrix, annot=True, fmt='d', cmap='Blues')
plt.xlabel('Predicted')
plt.ylabel('Actual')
plt.title('Confusion Matrix')
plt.show()

# Cross-validation
kf = KFold(n_splits=5, shuffle=True, random_state=42)
cv_scores = cross_val_score(model, X, y, cv=kf, scoring='accuracy')

print(f"Cross-Validation Scores: {cv_scores}")
print(f"Mean CV Accuracy: {cv_scores.mean():.2f} ± {cv_scores.std():.2f}")
```

## Exercise 2: Hyperparameter Tuning & Empirical Benchmarking

In this exercise, we will perform hyperparameter tuning using grid search and benchmark the model's performance in terms of accuracy and latency.

### Real Benchmarking Code

```python
from sklearn.model_selection import GridSearchCV
import time

# Define hyperparameter grid
param_grid = {
    'C': [0.1, 1, 10, 100],
    'solver': ['liblinear', 'saga']
}

# Initialize GridSearchCV
grid_search = GridSearchCV(LogisticRegression(max_iter=200), param_grid, cv=5, scoring='accuracy', n_jobs=-1)

# Start timing
start_time = time.time()

# Fit GridSearchCV
grid_search.fit(X_train, y_train)

# End timing
end_time = time.time()

# Print best parameters and best score
print(f"Best Parameters: {grid_search.best_params_}")
print(f"Best Cross-Validation Accuracy: {grid_search.best_score_:.2f}")

# Evaluate the best model on the test set
best_model = grid_search.best_estimator_
y_pred_best = best_model.predict(X_test)
accuracy_best = accuracy_score(y_test, y_pred_best)
print(f"Test Accuracy with Best Model: {accuracy_best:.2f}")

# Print execution time
print(f"Execution Time: {end_time - start_time:.2f} seconds")
```

## Exercise 3: Stress Testing, Edge Cases & Failure Mitigation

In this exercise, we will test the model on edge cases and implement guardrails to handle potential failures.

### Reproducing Failure Modes, Testing Edge Cases, and Implementing Guardrails

```python
# Test with a single sample
single_sample = X_test[0].reshape(1, -1)
single_pred = best_model.predict(single_sample)
print(f"Prediction for single sample: {single_pred[0]}")

# Test with an invalid sample (e.g., missing features)
invalid_sample = np.array([[1, 2, 3]])
try:
    invalid_pred = best_model.predict(invalid_sample)
except ValueError as e:
    print(f"Error with invalid sample: {e}")

# Implement guardrails for invalid input
def safe_predict(model, sample):
    if sample.shape[1] != X_train.shape[1]:
        raise ValueError(f"Sample must have {X_train.shape[1]} features, got {sample.shape[1]}")
    return model.predict(sample)

# Test safe_predict with valid and invalid samples
try:
    valid_pred = safe_predict(best_model, single_sample)
    print(f"Safe prediction for valid sample: {valid_pred[0]}")
except ValueError as e:
    print(f"Error with valid sample: {e}")

try:
    invalid_pred = safe_predict(best_model, invalid_sample)
except ValueError as e:
    print(f"Error with invalid sample: {e}")
```

## Verification Checklist & Quick Reference Cheat Sheet

### Essential Python Methods, Parameters, and Verification Flags

| Method/Parameter | Description |
|------------------|-------------|
| `make_classification` | Generates a synthetic dataset for classification. |
| `train_test_split` | Splits the dataset into training and testing sets. |
| `LogisticRegression` | Logistic regression model. |
| `fit` | Trains the model on the training data. |
| `predict` | Predicts the labels for the given samples. |
| `accuracy_score` | Computes the accuracy of the model. |
| `classification_report` | Generates a detailed classification report. |
| `confusion_matrix` | Computes the confusion matrix. |
| `KFold` | K-Folds cross-validator. |
| `cross_val_score` | Evaluates a score by cross-validation. |
| `GridSearchCV` | Exhaustive search over specified parameter values for an estimator. |
| `time.time` | Returns the current time in seconds since the Epoch. |
| `reshape` | Reshapes the array to the given shape. |

This lab provides a comprehensive guide to model evaluation and cross-validation, ensuring that you can effectively evaluate and validate machine learning models in practice.
