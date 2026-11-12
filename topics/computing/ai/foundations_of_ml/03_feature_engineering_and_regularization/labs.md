# Operational Verification Labs: 03 Feature Engineering And Regularization

## Objective & Environment Setup

This lab aims to provide hands-on experience with feature engineering and regularization techniques in the context of machine learning. Through this lab, you will implement these techniques using Python, leveraging libraries such as NumPy, Scikit-learn, and PyTorch. To set up your environment, ensure you have Python 3.11+ installed, and install the necessary packages with the following command:

```bash
pip install numpy scikit-learn torch
```

## Exercise 1: Hands-On Implementation & Pipeline Execution

In this exercise, you will implement a feature engineering pipeline and apply regularization techniques to a synthetic dataset. The pipeline will include feature scaling, polynomial feature generation, and the application of L2 regularization using Ridge regression.

### Complete, Runnable Python Script

```python
import numpy as np
from sklearn.datasets import make_regression
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, PolynomialFeatures
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_squared_error

# Generate synthetic dataset
X, y = make_regression(n_samples=1000, n_features=10, noise=0.1, random_state=42)

# Split dataset into training and testing sets
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Feature scaling
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# Polynomial feature generation
poly = PolynomialFeatures(degree=2, include_bias=False)
X_train_poly = poly.fit_transform(X_train_scaled)
X_test_poly = poly.transform(X_test_scaled)

# Apply L2 regularization (Ridge regression)
ridge = Ridge(alpha=1.0)
ridge.fit(X_train_poly, y_train)

# Predict and evaluate
y_pred = ridge.predict(X_test_poly)
mse = mean_squared_error(y_test, y_pred)

print(f"Mean Squared Error: {mse}")
```

## Exercise 2: Hyperparameter Tuning & Empirical Benchmarking

In this exercise, you will perform hyperparameter tuning for the Ridge regression model and benchmark its performance in terms of mean squared error (MSE) and computational time.

### Real Benchmarking Code

```python
import time
from sklearn.model_selection import GridSearchCV

# Define hyperparameter grid
param_grid = {'alpha': [0.1, 1.0, 10.0, 100.0]}

# Initialize Ridge regression model
ridge = Ridge()

# Set up grid search with cross-validation
grid_search = GridSearchCV(ridge, param_grid, cv=5, scoring='neg_mean_squared_error', n_jobs=-1)

# Measure time taken for grid search
start_time = time.time()
grid_search.fit(X_train_poly, y_train)
end_time = time.time()

# Print best parameters and corresponding MSE
print(f"Best parameters: {grid_search.best_params_}")
print(f"Best cross-validation MSE: {-grid_search.best_score_}")
print(f"Time taken for grid search: {end_time - start_time} seconds")

# Evaluate on test set
best_ridge = grid_search.best_estimator_
y_pred = best_ridge.predict(X_test_poly)
mse = mean_squared_error(y_test, y_pred)

print(f"Test set MSE: {mse}")
```

## Exercise 3: Stress Testing, Edge Cases & Failure Mitigation

In this exercise, you will test the robustness of your feature engineering and regularization pipeline by introducing edge cases and implementing guardrails to handle potential failures.

### Reproducing Failure Modes, Testing Edge Cases, and Implementing Guardrails

```python
import warnings

# Introduce edge case: zero variance feature
X_train_poly_with_zero_variance = np.hstack((X_train_poly, np.zeros((X_train_poly.shape[0], 1))))
X_test_poly_with_zero_variance = np.hstack((X_test_poly, np.zeros((X_test_poly.shape[0], 1))))

# Suppress warnings for zero variance features
with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    ridge.fit(X_train_poly_with_zero_variance, y_train)

# Predict and evaluate
y_pred = ridge.predict(X_test_poly_with_zero_variance)
mse = mean_squared_error(y_test, y_pred)

print(f"Mean Squared Error with zero variance feature: {mse}")

# Implement guardrail: check for zero variance features
def check_zero_variance_features(X):
    zero_variance_features = np.all(X == X[0, :], axis=0)
    if np.any(zero_variance_features):
        raise ValueError("Dataset contains zero variance features.")
    return X

# Apply guardrail
try:
    X_train_poly_clean = check_zero_variance_features(X_train_poly_with_zero_variance)
    X_test_poly_clean = check_zero_variance_features(X_test_poly_with_zero_variance)
except ValueError as e:
    print(e)

# Re-fit model without zero variance features
ridge.fit(X_train_poly_clean, y_train)
y_pred = ridge.predict(X_test_poly_clean)
mse = mean_squared_error(y_test, y_pred)

print(f"Mean Squared Error after removing zero variance features: {mse}")
```

## Verification Checklist & Quick Reference Cheat Sheet

| Method/Parameter                         | Description                                                                 |
|------------------------------------------|-----------------------------------------------------------------------------|
| `make_regression`                        | Generates a random regression problem.                                      |
| `train_test_split`                       | Splits arrays or matrices into random train and test subsets.             |
| `StandardScaler`                         | Standardizes features by removing the mean and scaling to unit variance.    |
| `PolynomialFeatures`                     | Generates polynomial and interaction features.                              |
| `Ridge`                                  | Linear least squares with L2 regularization.                                |
| `mean_squared_error`                     | Mean squared error regression loss.                                         |
| `GridSearchCV`                           | Exhaustive search over specified parameter values for an estimator.         |
| `np.hstack`                              | Stacks arrays in sequence horizontally (column wise).                     |
| `warnings.catch_warnings`                | Context manager for filtering warnings.                                     |
| `check_zero_variance_features`           | Custom function to check for zero variance features in the dataset.         |

This lab provides a comprehensive hands-on experience with feature engineering and regularization, equipping you with the skills to build robust and efficient machine learning pipelines.
