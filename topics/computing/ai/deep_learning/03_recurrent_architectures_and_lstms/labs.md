# Operational Verification Labs: 03 Recurrent Architectures And LSTMs

## Objective & Environment Setup
The objective of this lab is to gain hands-on experience with implementing, tuning, and verifying Long Short-Term Memory (LSTM) networks, a type of recurrent neural network (RNN) widely used in sequence prediction problems. We will use a Python 3.11+ environment with the following packages installed:

- PyTorch
- HuggingFace Transformers
- NumPy
- Scikit-learn
- Matplotlib

Ensure your environment is set up with these packages. You can install them using pip:

```bash
pip install torch transformers numpy scikit-learn matplotlib
```

## Exercise 1: Hands-On Implementation & Pipeline Execution
In this exercise, we will implement an LSTM network to predict the next value in a time series. We will use the popular sine wave dataset for this purpose. The LSTM will be trained to predict the next value in the sequence given a fixed number of previous values.

### Step-by-Step Implementation

1. **Import Libraries**

```python
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
import matplotlib.pyplot as plt
from sklearn.preprocessing import MinMaxScaler
```

2. **Generate Sine Wave Data**

```python
def generate_sine_wave_data(seq_length, num_samples):
    x = np.linspace(0, 100, num_samples)
    y = np.sin(x)
    data = []
    for i in range(len(y) - seq_length):
        data.append(y[i:i + seq_length])
    data = np.array(data)
    return data

seq_length = 50
num_samples = 1000
data = generate_sine_wave_data(seq_length, num_samples)
```

3. **Normalize Data**

```python
scaler = MinMaxScaler(feature_range=(-1, 1))
data = scaler.fit_transform(data)
```

4. **Split Data into Training and Testing Sets**

```python
train_size = int(len(data) * 0.8)
train_data = data[:train_size]
test_data = data[train_size:]
```

5. **Create DataLoader**

```python
def create_data_loader(data, seq_length, batch_size):
    x = []
    y = []
    for i in range(len(data) - seq_length):
        x.append(data[i:i + seq_length, :-1])
        y.append(data[i + seq_length - 1, -1])
    x = np.array(x)
    y = np.array(y)
    x = torch.tensor(x, dtype=torch.float32)
    y = torch.tensor(y, dtype=torch.float32)
    dataset = torch.utils.data.TensorDataset(x, y)
    data_loader = torch.utils.data.DataLoader(dataset, batch_size=batch_size, shuffle=True)
    return data_loader

batch_size = 32
train_loader = create_data_loader(train_data, seq_length, batch_size)
test_loader = create_data_loader(test_data, seq_length, batch_size)
```

6. **Define LSTM Model**

```python
class LSTMModel(nn.Module):
    def __init__(self, input_size, hidden_size, num_layers, output_size):
        super(LSTMModel, self).__init__()
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        self.lstm = nn.LSTM(input_size, hidden_size, num_layers, batch_first=True)
        self.fc = nn.Linear(hidden_size, output_size)

    def forward(self, x):
        h0 = torch.zeros(self.num_layers, x.size(0), self.hidden_size).to(x.device)
        c0 = torch.zeros(self.num_layers, x.size(0), self.hidden_size).to(x.device)
        out, _ = self.lstm(x, (h0, c0))
        out = self.fc(out[:, -1, :])
        return out

input_size = 1
hidden_size = 50
num_layers = 2
output_size = 1
model = LSTMModel(input_size, hidden_size, num_layers, output_size)
```

7. **Define Loss Function and Optimizer**

```python
criterion = nn.MSELoss()
optimizer = optim.Adam(model.parameters(), lr=0.001)
```

8. **Train the Model**

```python
num_epochs = 100
for epoch in range(num_epochs):
    for inputs, labels in train_loader:
        optimizer.zero_grad()
        outputs = model(inputs)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()
    if (epoch+1) % 10 == 0:
        print(f'Epoch [{epoch+1}/{num_epochs}], Loss: {loss.item():.4f}')
```

9. **Evaluate the Model**

```python
model.eval()
with torch.no_grad():
    predictions = []
    for inputs, labels in test_loader:
        outputs = model(inputs)
        predictions.extend(outputs.numpy())
    predictions = np.array(predictions)
    predictions = scaler.inverse_transform(np.concatenate((test_data[-len(predictions):, :-1], predictions.reshape(-1, 1)), axis=1))[:, -1]
    true_values = scaler.inverse_transform(test_data[-len(predictions):])[:, -1]
    plt.figure(figsize=(12, 6))
    plt.plot(true_values, label='True Values')
    plt.plot(predictions, label='Predictions')
    plt.legend()
    plt.show()
```

## Exercise 2: Hyperparameter Tuning & Empirical Benchmarking
In this exercise, we will perform hyperparameter tuning and benchmark the LSTM model based on accuracy and convergence curves.

### Hyperparameter Tuning

1. **Define Hyperparameters**

```python
hyperparameters = {
    'hidden_size': [50, 100, 200],
    'num_layers': [1, 2, 3],
    'learning_rate': [0.001, 0.0001, 0.00001]
}
```

2. **Grid Search**

```python
best_loss = float('inf')
best_params = None

for hs in hyperparameters['hidden_size']:
    for nl in hyperparameters['num_layers']:
        for lr in hyperparameters['learning_rate']:
            model = LSTMModel(input_size, hs, nl, output_size)
            criterion = nn.MSELoss()
            optimizer = optim.Adam(model.parameters(), lr=lr)
            for epoch in range(num_epochs):
                for inputs, labels in train_loader:
                    optimizer.zero_grad()
                    outputs = model(inputs)
                    loss = criterion(outputs, labels)
                    loss.backward()
                    optimizer.step()
            if loss.item() < best_loss:
                best_loss = loss.item()
                best_params = {'hidden_size': hs, 'num_layers': nl, 'learning_rate': lr}
            print(f'Hidden Size: {hs}, Num Layers: {nl}, Learning Rate: {lr}, Loss: {loss.item():.4f}')

print(f'Best Parameters: {best_params}')
```

### Benchmarking

1. **Convergence Curves**

```python
import matplotlib.pyplot as plt

hidden_size = best_params['hidden_size']
num_layers = best_params['num_layers']
learning_rate = best_params['learning_rate']

model = LSTMModel(input_size, hidden_size, num_layers, output_size)
criterion = nn.MSELoss()
optimizer = optim.Adam(model.parameters(), lr=learning_rate)

losses = []
for epoch in range(num_epochs):
    for inputs, labels in train_loader:
        optimizer.zero_grad()
        outputs = model(inputs)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()
    losses.append(loss.item())
    if (epoch+1) % 10 == 0:
        print(f'Epoch [{epoch+1}/{num_epochs}], Loss: {loss.item():.4f}')

plt.figure(figsize=(12, 6))
plt.plot(losses, label='Training Loss')
plt.legend()
plt.show()
```

## Exercise 3: Stress Testing, Edge Cases & Failure Mitigation
In this exercise, we will test the LSTM model under various stress conditions and edge cases to ensure robustness and reliability.

### Stress Testing

1. **Large Input Sequences**

```python
large_seq_length = 100
large_data = generate_sine_wave_data(large_seq_length, num_samples)
large_data = scaler.fit_transform(large_data)
large_train_data = large_data[:train_size]
large_test_data = large_data[train_size:]
large_train_loader = create_data_loader(large_train_data, large_seq_length, batch_size)
large_test_loader = create_data_loader(large_test_data, large_seq_length, batch_size)

model = LSTMModel(input_size, hidden_size, num_layers, output_size)
criterion = nn.MSELoss()
optimizer = optim.Adam(model.parameters(), lr=learning_rate)

for epoch in range(num_epochs):
    for inputs, labels in large_train_loader:
        optimizer.zero_grad()
        outputs = model(inputs)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()
    if (epoch+1) % 10 == 0:
        print(f'Epoch [{epoch+1}/{num_epochs}], Loss: {loss.item():.4f}')
```

### Edge Cases

1. **Single Data Point**

```python
single_data = generate_sine_wave_data(1, num_samples)
single_data = scaler.fit_transform(single_data)
single_train_data = single_data[:train_size]
single_test_data = single_data[train_size:]
single_train_loader = create_data_loader(single_train_data, 1, batch_size)
single_test_loader = create_data_loader(single_test_data, 1, batch_size)

model = LSTMModel(input_size, hidden_size, num_layers, output_size)
criterion = nn.MSELoss()
optimizer = optim.Adam(model.parameters(), lr=learning_rate)

for epoch in range(num_epochs):
    for inputs, labels in single_train_loader:
        optimizer.zero_grad()
        outputs = model(inputs)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()
    if (epoch+1) % 10 == 0:
        print(f'Epoch [{epoch+1}/{num_epochs}], Loss: {loss.item():.4f}')
```

### Failure Mitigation

1. **Guardrails and Error Handling**

```python
try:
    model = LSTMModel(input_size, hidden_size, num_layers, output_size)
    criterion = nn.MSELoss()
    optimizer = optim.Adam(model.parameters(), lr=learning_rate)
    for epoch in range(num_epochs):
        for inputs, labels in train_loader:
            optimizer.zero_grad()
            outputs = model(inputs)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()
        if (epoch+1) % 10 == 0:
            print(f'Epoch [{epoch+1}/{num_epochs}], Loss: {loss.item():.4f}')
except Exception as e:
    print(f'An error occurred: {e}')
```

## Verification Checklist & Quick Reference Cheat Sheet

| Method/Parameter | Description |
|------------------|-------------|
| `generate_sine_wave_data` | Generates a sine wave dataset for training and testing. |
| `MinMaxScaler` | Normalizes the dataset to a specified range. |
| `create_data_loader` | Creates a DataLoader for batching and shuffling the dataset. |
| `LSTMModel` | Defines the LSTM architecture with specified input, hidden, and output sizes. |
| `nn.MSELoss` | Mean Squared Error loss function for regression tasks. |
| `optim.Adam` | Adam optimizer for training the model. |
| `model.eval()` | Sets the model to evaluation mode. |
| `torch.no_grad()` | Disables gradient calculation for inference. |
| `scaler.inverse_transform` | Inverse transforms the normalized data to its original scale. |
| `plt.plot` | Plots the training and testing data for visualization. |

This lab provides a comprehensive hands-on experience with implementing, tuning, and verifying LSTM networks. By following the steps and exercises, you will gain a deeper understanding of recurrent architectures and their applications in sequence prediction problems.
