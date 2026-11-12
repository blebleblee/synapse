# Operational Verification Labs: 04 Model Evaluation And Cross Validation

## Objective & Environment Setup

The objective of this lab is to provide hands-on experience with model evaluation and cross-validation techniques in the context of machine learning. This lab will guide you through implementing, tuning, and verifying a machine learning model using real, executable Python scripts. The environment setup requires Python 3.11+ and the following packages:

- PyTorch
- Scikit-learn
- NumPy
- Matplotlib

You can install these packages using pip:

```bash
pip install torch scikit-learn numpy matplotlib
```

## Exercise 1: Hands-On Implementation & Pipeline Execution

In this exercise, we will implement a simple machine learning pipeline using PyTorch and Scikit-learn. We will train a logistic regression model on the Iris dataset and evaluate its performance using cross-validation.

### Step-by-Step Implementation

1. **Import Libraries**

   ```python
   import torch
   import torch.nn as nn
   import torch.optim as optim
   from sklearn.datasets import load_iris
   from sklearn.model_selection import train_test_split, cross_val_score
   from sklearn.preprocessing import StandardScaler
   import numpy as np
   import matplotlib.pyplot as plt
   ```

2. **Load and Preprocess Data**

   ```python
   # Load the Iris dataset
   iris = load_iris()
   X, y = iris.data, iris.target

   # Standardize the features
   scaler = StandardScaler()
   X_scaled = scaler.fit_transform(X)

   # Convert to PyTorch tensors
   X_tensor = torch.tensor(X_scaled, dtype=torch.float32)
   y_tensor = torch.tensor(y, dtype=torch.long)
   ```

3. **Define the Logistic Regression Model**

   ```python
   class LogisticRegressionModel(nn.Module):
       def __init__(self, input_dim, output_dim):
           super(LogisticRegressionModel, self).__init__()
           self.linear = nn.Linear(input_dim, output_dim)

       def forward(self, x):
           return self.linear(x)
   ```

4. **Train the Model**

   ```python
   # Hyperparameters
   input_dim = X_tensor.shape[1]
   output_dim = len(np.unique(y))
   learning_rate = 0.01
   num_epochs = 100

   # Initialize the model, loss function, and optimizer
   model = LogisticRegressionModel(input_dim, output_dim)
   criterion = nn.CrossEntropyLoss()
   optimizer = optim.SGD(model.parameters(), lr=learning_rate)

   # Training loop
   for epoch in range(num_epochs):
       # Forward pass
       outputs = model(X_tensor)
       loss = criterion(outputs, y_tensor)

       # Backward pass and optimization
       optimizer.zero_grad()
       loss.backward()
       optimizer.step()

       if (epoch+1) % 10 == 0:
           print(f'Epoch [{epoch+1}/{num_epochs}], Loss: {loss.item():.4f}')
   ```

5. **Evaluate the Model with Cross-Validation**

   ```python
   # Convert PyTorch model to a function for Scikit-learn compatibility
   def torch_model_predict(X):
       with torch.no_grad():
           X_tensor = torch.tensor(X, dtype=torch.float32)
           outputs = model(X_tensor)
           _, predicted = torch.max(outputs.data, 1)
           return predicted.numpy()

   # Perform cross-validation
   cv_scores = cross_val_score(torch_model_predict, X_scaled, y, cv=5)
   print(f'Cross-Validation Scores: {cv_scores}')
   print(f'Mean CV Score: {np.mean(cv_scores):.4f}')
   ```

## Exercise 2: Hyperparameter Tuning & Empirical Benchmarking

In this exercise, we will perform hyperparameter tuning using grid search and benchmark the model's accuracy and convergence.

### Step-by-Step Implementation

1. **Define Hyperparameter Grid**

   ```python
   from sklearn.model_selection import GridSearchCV

   # Define a function to create and train the model
   def create_model(learning_rate=0.01, num_epochs=100):
       model = LogisticRegressionModel(input_dim, output_dim)
       criterion = nn.CrossEntropyLoss()
       optimizer = optim.SGD(model.parameters(), lr=learning_rate)

       for epoch in range(num_epochs):
           outputs = model(X_tensor)
           loss = criterion(outputs, y_tensor)
           optimizer.zero_grad()
           loss.backward()
           optimizer.step()

       return torch_model_predict

   # Define the parameter grid
   param_grid = {
       'learning_rate': [0.001, 0.01, 0.1],
       'num_epochs': [50, 100, 200]
   }
   ```

2. **Perform Grid Search**

   ```python
   # Create a GridSearchCV object
   grid_search = GridSearchCV(estimator=create_model, param_grid=param_grid, cv=5, scoring='accuracy')

   # Fit the grid search to the data
   grid_search.fit(X_scaled, y)

   # Print the best parameters and best score
   print(f'Best Parameters: {grid_search.best_params_}')
   print(f'Best Score: {grid_search.best_score_:.4f}')
   ```

3. **Benchmark the Model**

   ```python
   import time

   # Measure training time
   start_time = time.time()
   best_model = grid_search.best_estimator_
   best_model(X_scaled)
   end_time = time.time()
   training_time = end_time - start_time
   print(f'Training Time: {training_time:.4f} seconds')
   ```

## Exercise 3: Stress Testing, Edge Cases & Failure Mitigation

In this exercise, we will test the model's robustness by simulating edge cases and implementing guardrails.

### Step-by-Step Implementation

1. **Simulate Edge Cases**

   ```python
   # Simulate edge cases by introducing outliers
   X_outliers = np.vstack((X_scaled, np.array([[100, 100, 100, 100]])))
   y_outliers = np.append(y, 0)

   # Evaluate the model on the outlier data
   outlier_scores = cross_val_score(torch_model_predict, X_outliers, y_outliers, cv=5)
   print(f'Outlier Cross-Validation Scores: {outlier_scores}')
   print(f'Mean Outlier CV Score: {np.mean(outlier_scores):.4f}')
   ```

2. **Implement Guardrails**

   ```python
   # Implement a guardrail to handle outliers
   def safe_predict(X):
       try:
           return torch_model_predict(X)
       except Exception as e:
           print(f'Error during prediction: {e}')
           return np.array([0] * X.shape[0])

   # Test the guardrail with outlier data
   safe_predictions = safe_predict(X_outliers)
   print(f'Safe Predictions: {safe_predictions}')
   ```

## Verification Checklist & Quick Reference Cheat Sheet

| Method/Parameter | Description |
|------------------|-------------|
| `cross_val_score` | Perform cross-validation and return the scores for each fold. |
| `GridSearchCV` | Perform an exhaustive search over specified parameter values for an estimator. |
| `StandardScaler` | Standardize features by removing the mean and scaling to unit variance. |
| `torch.no_grad()` | Disable gradient calculation to reduce memory consumption and speed up computations. |
| `torch.max` | Return the maximum value of each row of the input tensor in the given dimension. |
| `time.time()` | Return the current time in seconds since the Epoch. |

This lab provides a comprehensive hands-on experience with model evaluation and cross-validation, including hyperparameter tuning, benchmarking, and robustness testing. By following the steps outlined in this guide, you will gain practical skills in evaluating and verifying machine learning models.
