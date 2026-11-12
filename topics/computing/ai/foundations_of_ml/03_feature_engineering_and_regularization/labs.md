# Operational Verification Labs: 03 Feature Engineering And Regularization

## Objective & Environment Setup

The objective of this lab is to gain hands-on experience with feature engineering and regularization techniques in machine learning. We will implement a complete pipeline that includes data preprocessing, feature engineering, model training, hyperparameter tuning, and evaluation. The lab will use a real dataset and will be executed in a Python 3.11+ environment. The required packages are PyTorch, NumPy, Scikit-learn, and Pandas. Ensure that these packages are installed in your environment.

To set up the environment, you can use the following commands:

```bash
pip install numpy pandas scikit-learn torch
```

## Exercise 1: Hands-On Implementation & Pipeline Execution

In this exercise, we will implement a feature engineering pipeline and train a regularized linear regression model using Scikit-learn. We will use the Boston Housing dataset for this purpose. The dataset will be preprocessed, features will be engineered, and a regularized linear regression model will be trained.

Here is the complete, runnable Python script:

```python
import numpy as np
import pandas as pd
from sklearn.datasets import load_boston
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, PolynomialFeatures
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_squared_error

# Load the Boston Housing dataset
boston = load_boston()
X, y = boston.data, boston.target

# Split the dataset into training and testing sets
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Standardize the features
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# Engineer polynomial features
poly = PolynomialFeatures(degree=2, include_bias=False)
X_train_poly = poly.fit_transform(X_train_scaled)
X_test_poly = poly.transform(X_test_scaled)

# Train a regularized linear regression model (Ridge regression)
ridge = Ridge(alpha=1.0)
ridge.fit(X_train_poly, y_train)

# Make predictions
y_train_pred = ridge.predict(X_train_poly)
y_test_pred = ridge.predict(X_test_poly)

# Evaluate the model
train_mse = mean_squared_error(y_train, y_train_pred)
test_mse = mean_squared_error(y_test, y_test_pred)

print(f"Training MSE: {train_mse}")
print(f"Testing MSE: {test_mse}")
```

## Exercise 2: Hyperparameter Tuning & Empirical Benchmarking

In this exercise, we will perform hyperparameter tuning for the Ridge regression model using grid search. We will also benchmark the model's performance in terms of accuracy and latency.

Here is the complete, runnable Python script:

```python
import numpy as np
import pandas as pd
from sklearn.datasets import load_boston
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.preprocessing import StandardScaler, PolynomialFeatures
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_squared_error
import time

# Load the Boston Housing dataset
boston = load_boston()
X, y = boston.data, boston.target

# Split the dataset into training and testing sets
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Standardize the features
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# Engineer polynomial features
poly = PolynomialFeatures(degree=2, include_bias=False)
X_train_poly = poly.fit_transform(X_train_scaled)
X_test_poly = poly.transform(X_test_scaled)

# Define the model and hyperparameter grid
ridge = Ridge()
param_grid = {'alpha': [0.1, 1.0, 10.0, 100.0]}

# Perform grid search with cross-validation
grid_search = GridSearchCV(ridge, param_grid, cv=5, scoring='neg_mean_squared_error')
grid_search.fit(X_train_poly, y_train)

# Get the best model
best_ridge = grid_search.best_estimator_

# Measure training time
start_time = time.time()
best_ridge.fit(X_train_poly, y_train)
training_time = time.time() - start_time

# Make predictions
y_train_pred = best_ridge.predict(X_train_poly)
y_test_pred = best_ridge.predict(X_test_poly)

# Evaluate the model
train_mse = mean_squared_error(y_train, y_train_pred)
test_mse = mean_squared_error(y_test, y_test_pred)

print(f"Best alpha: {best_ridge.alpha}")
print(f"Training MSE: {train_mse}")
print(f"Testing MSE: {test_mse}")
print(f"Training time: {training_time} seconds")
```

## Exercise 3: Stress Testing, Edge Cases & Failure Mitigation

In this exercise, we will test the model's performance on edge cases and implement guardrails to handle potential failures. We will also handle cases where the dataset might be missing values or contain outliers.

Here is the complete, runnable Python script:

```python
import numpy as np
import pandas as pd
from sklearn.datasets import load_boston
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, PolynomialFeatures
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_squared_error
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline

# Load the Boston Housing dataset
boston = load_boston()
X, y = boston.data, boston.target

# Introduce some missing values for stress testing
X[::10, 0] = np.nan

# Split the dataset into training and testing sets
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Create a pipeline with imputation, scaling, polynomial features, and ridge regression
pipeline = Pipeline([
    ('imputer', SimpleImputer(strategy='mean')),
    ('scaler', StandardScaler()),
    ('poly', PolynomialFeatures(degree=2, include_bias=False)),
    ('ridge', Ridge(alpha=1.0))
])

# Train the model
pipeline.fit(X_train, y_train)

# Make predictions
y_train_pred = pipeline.predict(X_train)
y_test_pred = pipeline.predict(X_test)

# Evaluate the model
train_mse = mean_squared_error(y_train, y_train_pred)
test_mse = mean_squared_error(y_test, y_test_pred)

print(f"Training MSE: {train_mse}")
print(f"Testing MSE: {test_mse}")
```

## Verification Checklist & Quick Reference Cheat Sheet

| Method/Parameter | Description |
|------------------|-------------|
| `StandardScaler` | Standardizes features by removing the mean and scaling to unit variance. |
| `PolynomialFeatures` | Generates polynomial and interaction features. |
| `Ridge` | Linear least squares with L2 regularization. |
| `GridSearchCV` | Exhaustive search over specified parameter values for an estimator. |
| `SimpleImputer` | Imputation transformer for completing missing values. |
| `Pipeline` | Sequentially apply a list of transforms and a final estimator. |
| `mean_squared_error` | Mean squared error regression loss. |
| `train_test_split` | Splits arrays or matrices into random train and test subsets. |

This lab provides a comprehensive hands-on experience with feature engineering and regularization techniques, ensuring that you can apply these concepts in real-world machine learning projects.
