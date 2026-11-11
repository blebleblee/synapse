# Operational Verification Labs: 01 Multilayer Perceptrons And Backprop

## Objective & Environment Setup

### Objective
The objective of this lab is to gain hands-on experience with implementing, tuning, and verifying a multilayer perceptron (MLP) using backpropagation. This lab will cover the core concepts of neural network architecture, training, and evaluation, providing a comprehensive understanding of how MLPs operate and how they can be optimized.

### Environment Setup
Ensure you have a Python 3.11+ environment set up with the following packages installed:
- PyTorch
- NumPy
- Scikit-learn
- Matplotlib

You can install these packages using pip:

```bash
pip install torch numpy scikit-learn matplotlib
```

## Exercise 1: Hands-On Implementation & Pipeline Execution

In this exercise, we will implement a simple multilayer perceptron using PyTorch. The MLP will consist of an input layer, one hidden layer, and an output layer. We will use the backpropagation algorithm to train the model on a synthetic dataset.

### Step-by-Step Implementation

1. **Import Required Libraries**

    ```python
    import torch
    import torch.nn as nn
    import torch.optim as optim
    import numpy as np
    import matplotlib.pyplot as plt
    from sklearn.datasets import make_classification
    from sklearn.model_selection import train_test_split
    from sklearn.preprocessing import StandardScaler
    ```

2. **Generate Synthetic Dataset**

    ```python
    # Generate a synthetic binary classification dataset
    X, y = make_classification(n_samples=1000, n_features=20, n_informative=15, n_redundant=5, random_state=42)

    # Split the dataset into training and testing sets
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # Standardize the features
    scaler = StandardScaler()
    X_train = scaler.fit_transform(X_train)
    X_test = scaler.transform(X_test)

    # Convert to PyTorch tensors
    X_train_tensor = torch.tensor(X_train, dtype=torch.float32)
    y_train_tensor = torch.tensor(y_train, dtype=torch.float32).view(-1, 1)
    X_test_tensor = torch.tensor(X_test, dtype=torch.float32)
    y_test_tensor = torch.tensor(y_test, dtype=torch.float32).view(-1, 1)
    ```

3. **Define the Multilayer Perceptron Model**

    ```python
    class MLP(nn.Module):
        def __init__(self, input_size, hidden_size, output_size):
            super(MLP, self).__init__()
            self.fc1 = nn.Linear(input_size, hidden_size)
            self.relu = nn.ReLU()
            self.fc2 = nn.Linear(hidden_size, output_size)
            self.sigmoid = nn.Sigmoid()

        def forward(self, x):
            out = self.fc1(x)
            out = self.relu(out)
            out = self.fc2(out)
            out = self.sigmoid(out)
            return out
    ```

4. **Initialize the Model, Loss Function, and Optimizer**

    ```python
    # Hyperparameters
    input_size = X_train.shape[1]
    hidden_size = 10
    output_size = 1
    learning_rate = 0.01
    num_epochs = 100

    # Initialize the model
    model = MLP(input_size, hidden_size, output_size)

    # Define the loss function and optimizer
    criterion = nn.BCELoss()
    optimizer = optim.SGD(model.parameters(), lr=learning_rate)
    ```

5. **Train the Model**

    ```python
    # Training loop
    for epoch in range(num_epochs):
        # Forward pass
        outputs = model(X_train_tensor)
        loss = criterion(outputs, y_train_tensor)

        # Backward pass and optimization
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

        if (epoch+1) % 10 == 0:
            print(f'Epoch [{epoch+1}/{num_epochs}], Loss: {loss.item():.4f}')
    ```

6. **Evaluate the Model**

    ```python
    # Evaluate the model on the test set
    with torch.no_grad():
        test_outputs = model(X_test_tensor)
        predicted = (test_outputs > 0.5).float()
        accuracy = (predicted.eq(y_test_tensor).sum() / float(y_test_tensor.shape[0])).item()
        print(f'Test Accuracy: {accuracy:.4f}')
    ```

7. **Visualize Training Loss**

    ```python
    # Plot the training loss
    plt.plot(range(1, num_epochs+1, 10), [loss.item() for epoch in range(0, num_epochs, 10)])
    plt.xlabel('Epoch')
    plt.ylabel('Loss')
    plt.title('Training Loss')
    plt.show()
    ```

## Exercise 2: Hyperparameter Tuning & Empirical Benchmarking

In this exercise, we will perform hyperparameter tuning to optimize the MLP model. We will measure the accuracy and training time for different hyperparameter settings.

### Step-by-Step Hyperparameter Tuning

1. **Define Hyperparameter Grid**

    ```python
    import time

    # Define hyperparameter grid
    hidden_sizes = [5, 10, 20]
    learning_rates = [0.001, 0.01, 0.1]
    num_epochs = 100
    ```

2. **Perform Hyperparameter Tuning**

    ```python
    best_accuracy = 0.0
    best_params = {}

    for hidden_size in hidden_sizes:
        for learning_rate in learning_rates:
            # Initialize the model
            model = MLP(input_size, hidden_size, output_size)

            # Define the loss function and optimizer
            criterion = nn.BCELoss()
            optimizer = optim.SGD(model.parameters(), lr=learning_rate)

            # Training loop
            start_time = time.time()
            for epoch in range(num_epochs):
                # Forward pass
                outputs = model(X_train_tensor)
                loss = criterion(outputs, y_train_tensor)

                # Backward pass and optimization
                optimizer.zero_grad()
                loss.backward()
                optimizer.step()

            # Evaluate the model on the test set
            with torch.no_grad():
                test_outputs = model(X_test_tensor)
                predicted = (test_outputs > 0.5).float()
                accuracy = (predicted.eq(y_test_tensor).sum() / float(y_test_tensor.shape[0])).item()

            end_time = time.time()
            training_time = end_time - start_time

            # Print results
            print(f'Hidden Size: {hidden_size}, Learning Rate: {learning_rate}, Accuracy: {accuracy:.4f}, Training Time: {training_time:.2f}s')

            # Update best parameters
            if accuracy > best_accuracy:
                best_accuracy = accuracy
                best_params = {'hidden_size': hidden_size, 'learning_rate': learning_rate}
    ```

3. **Print Best Parameters**

    ```python
    print(f'Best Parameters: {best_params}, Best Accuracy: {best_accuracy:.4f}')
    ```

## Exercise 3: Stress Testing, Edge Cases & Failure Mitigation

In this exercise, we will test the MLP model under various stress conditions and edge cases to ensure robustness and reliability.

### Step-by-Step Stress Testing

1. **Test with Noisy Data**

    ```python
    # Add noise to the test data
    noisy_X_test = X_test + np.random.normal(0, 0.1, X_test.shape)

    # Standardize the noisy test data
    noisy_X_test = scaler.transform(noisy_X_test)

    # Convert to PyTorch tensors
    noisy_X_test_tensor = torch.tensor(noisy_X_test, dtype=torch.float32)

    # Evaluate the model on the noisy test set
    with torch.no_grad():
        noisy_test_outputs = model(noisy_X_test_tensor)
        noisy_predicted = (noisy_test_outputs > 0.5).float()
        noisy_accuracy = (noisy_predicted.eq(y_test_tensor).sum() / float(y_test_tensor.shape[0])).item()
        print(f'Noisy Test Accuracy: {noisy_accuracy:.4f}')
    ```

2. **Test with Out-of-Distribution Data**

    ```python
    # Generate out-of-distribution data
    ood_X, _ = make_classification(n_samples=100, n_features=20, n_informative=15, n_redundant=5, random_state=43)

    # Standardize the out-of-distribution data
    ood_X = scaler.transform(ood_X)

    # Convert to PyTorch tensors
    ood_X_tensor = torch.tensor(ood_X, dtype=torch.float32)

    # Evaluate the model on the out-of-distribution test set
    with torch.no_grad():
        ood_test_outputs = model(ood_X_tensor)
        ood_predicted = (ood_test_outputs > 0.5).float()
        ood_accuracy = (ood_predicted.eq(torch.zeros_like(ood_predicted)).sum() / float(ood_X_tensor.shape[0])).item()
        print(f'Out-of-Distribution Test Accuracy: {ood_accuracy:.4f}')
    ```

3. **Implement Guardrails or Error Handling**

    ```python
    # Implement guardrails for input data
    def validate_input_data(X):
        if not isinstance(X, np.ndarray):
            raise ValueError("Input data must be a NumPy array.")
        if X.shape[1] != input_size:
            raise ValueError(f"Input data must have {input_size} features.")
        return X

    # Example usage
    try:
        noisy_X_test = validate_input_data(noisy_X_test)
        noisy_X_test_tensor = torch.tensor(noisy_X_test, dtype=torch.float32)
    except ValueError as e:
        print(f'Error: {e}')
    ```

## Verification Checklist & Quick Reference Cheat Sheet

### Essential Python Methods and Parameters

| Method/Parameter | Description |
|------------------|-------------|
| `make_classification` | Generates a synthetic binary classification dataset. |
| `train_test_split` | Splits the dataset into training and testing sets. |
| `StandardScaler` | Standardizes features by removing the mean and scaling to unit variance. |
| `torch.tensor` | Converts a NumPy array to a PyTorch tensor. |
| `nn.Linear` | Applies a linear transformation to the input. |
| `nn.ReLU` | Applies the rectified linear unit function. |
| `nn.Sigmoid` | Applies the sigmoid function. |
| `nn.BCELoss` | Binary cross-entropy loss function. |
| `optim.SGD` | Stochastic gradient descent optimizer. |
| `model.forward` | Defines the forward pass of the model. |
| `loss.backward` | Computes the gradient of the loss with respect to the model parameters. |
| `optimizer.step` | Updates the model parameters based on the computed gradients. |
| `torch.no_grad` | Disables gradient calculation to reduce memory consumption during inference. |
| `plt.plot` | Plots the training loss over epochs. |

### Verification Flags

| Flag | Description |
|------|-------------|
| `--hidden_size` | Specifies the size of the hidden layer. |
| `--learning_rate` | Specifies the learning rate for the optimizer. |
| `--num_epochs` | Specifies the number of training epochs. |

This lab provides a comprehensive hands-on experience with implementing, tuning, and verifying a multilayer perceptron using backpropagation. By following the steps outlined in this guide, you will gain a deeper understanding of the underlying mechanics of neural networks and how they can be optimized for performance and robustness.
