# Operational Verification Labs: 04 Model Evaluation And Cross Validation

## Objective & Environment Setup

This lab aims to provide hands-on experience with model evaluation and cross-validation techniques in the context of machine learning. Through this lab, you will implement a complete evaluation pipeline, perform hyperparameter tuning, and conduct stress testing and edge case analysis. To set up the environment, ensure you have a Python 3.11+ installation with the following packages:

- PyTorch
- Scikit-learn
- NumPy
- Matplotlib

You can install these packages using pip:

```bash
pip install torch scikit-learn numpy matplotlib
```

## Exercise 1: Hands-On Implementation & Pipeline Execution

In this exercise, we will implement a simple machine learning pipeline using a synthetic dataset. We will train a logistic regression model, evaluate it using cross-validation, and report the accuracy.

```python
import numpy as np
import matplotlib.pyplot as plt
from sklearn.datasets import make_classification
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, confusion_matrix, classification_report

# Generate synthetic dataset
X, y = make_classification(n_samples=1000, n_features=20, n_informative=2, n_redundant=10, random_state=42)

# Split the dataset into training and testing sets
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Initialize the logistic regression model
model = LogisticRegression(max_iter=1000)

# Train the model
model.fit(X_train, y_train)

# Predict on the test set
y_pred = model.predict(X_test)

# Evaluate the model
accuracy = accuracy_score(y_test, y_pred)
conf_matrix = confusion_matrix(y_test, y_pred)
class_report = classification_report(y_test, y_pred)

print(f"Accuracy: {accuracy}")
print("Confusion Matrix:")
print(conf_matrix)
print("Classification Report:")
print(class_report)

# Perform cross-validation
cv_scores = cross_val_score(model, X, y, cv=5)
print(f"Cross-Validation Scores: {cv_scores}")
print(f"Mean CV Score: {np.mean(cv_scores)}")
```

## Exercise 2: Hyperparameter Tuning & Empirical Benchmarking

In this exercise, we will perform hyperparameter tuning using grid search and evaluate the model's performance in terms of accuracy and latency.

```python
from sklearn.model_selection import GridSearchCV
import time

# Define the parameter grid
param_grid = {
    'C': [0.1, 1, 10, 100],
    'solver': ['liblinear', 'saga']
}

# Initialize the grid search
grid_search = GridSearchCV(LogisticRegression(max_iter=1000), param_grid, cv=5, scoring='accuracy')

# Record the start time
start_time = time.time()

# Fit the grid search
grid_search.fit(X, y)

# Record the end time
end_time = time.time()

# Calculate the elapsed time
elapsed_time = end_time - start_time

# Print the best parameters and the best score
print(f"Best Parameters: {grid_search.best_params_}")
print(f"Best Cross-Validation Score: {grid_search.best_score_}")
print(f"Elapsed Time: {elapsed_time} seconds")

# Evaluate the best model on the test set
best_model = grid_search.best_estimator_
y_pred_best = best_model.predict(X_test)
accuracy_best = accuracy_score(y_test, y_pred_best)
print(f"Test Set Accuracy with Best Model: {accuracy_best}")
```

## Exercise 3: Stress Testing, Edge Cases & Failure Mitigation

In this exercise, we will test the model under various stress conditions and edge cases, and implement guardrails to handle potential failures.

```python
# Test with a single sample
single_sample = X_test[0].reshape(1, -1)
single_pred = best_model.predict(single_sample)
print(f"Prediction for Single Sample: {single_pred}")

# Test with an empty dataset
try:
    empty_pred = best_model.predict(np.array([]).reshape(0, X.shape[1]))
except ValueError as e:
    print(f"Error with Empty Dataset: {e}")

# Test with a dataset with missing values
X_test_missing = X_test.copy()
X_test_missing[0, 0] = np.nan
try:
    missing_pred = best_model.predict(X_test_missing)
except ValueError as e:
    print(f"Error with Missing Values: {e}")

# Implement guardrails for edge cases
def safe_predict(model, X):
    if X.shape[0] == 0:
        raise ValueError("Input dataset is empty.")
    if np.isnan(X).any():
        raise ValueError("Input dataset contains NaN values.")
    return model.predict(X)

# Test the safe_predict function
try:
    safe_pred = safe_predict(best_model, X_test_missing)
except ValueError as e:
    print(f"Guardrail Triggered: {e}")

# Test with a dataset with incorrect shape
X_test_wrong_shape = X_test[:, :-1]
try:
    wrong_shape_pred = safe_predict(best_model, X_test_wrong_shape)
except ValueError as e:
    print(f"Guardrail Triggered: {e}")
```

## Verification Checklist & Quick Reference Cheat Sheet

| Method/Parameter | Description |
|------------------|-------------|
| `make_classification` | Generates a synthetic dataset for classification. |
| `train_test_split` | Splits the dataset into training and testing sets. |
| `LogisticRegression` | Initializes a logistic regression model. |
| `fit` | Trains the model on the training data. |
| `predict` | Predicts the labels for the input data. |
| `accuracy_score` | Computes the accuracy of the model. |
| `confusion_matrix` | Computes the confusion matrix for the model. |
| `classification_report` | Generates a detailed classification report. |
| `cross_val_score` | Performs cross-validation and returns the scores. |
| `GridSearchCV` | Initializes a grid search for hyperparameter tuning. |
| `best_params_` | Retrieves the best parameters found by grid search. |
| `best_score_` | Retrieves the best cross-validation score. |
| `safe_predict` | A function to safely predict labels with guardrails. |

This lab provides a comprehensive hands-on experience with model evaluation and cross-validation, including hyperparameter tuning and stress testing. By following the exercises, you will gain practical skills in evaluating machine learning models and handling edge cases.
