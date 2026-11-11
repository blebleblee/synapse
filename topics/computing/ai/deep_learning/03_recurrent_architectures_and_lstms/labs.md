# Operational Verification Labs: 03 Recurrent Architectures And LSTMs

## Objective & Environment Setup

The objective of this lab is to gain hands-on experience with Recurrent Neural Networks (RNNs) and Long Short-Term Memory (LSTM) networks. We will implement an LSTM model to predict time series data, perform hyperparameter tuning, and conduct stress testing to ensure robustness. This lab assumes a Python 3.11+ environment with the following packages installed:

- PyTorch
- HuggingFace Transformers
- NumPy
- Scikit-learn
- Matplotlib

You can set up the environment using the following command:

```bash
pip install torch transformers numpy scikit-learn matplotlib
```

## Exercise 1: Hands-On Implementation & Pipeline Execution

In this exercise, we will implement an LSTM model to predict the sine wave function. This will serve as a simple yet effective demonstration of how LSTMs can capture temporal dependencies in sequential data.

### Step-by-Step Implementation

1. **Import Required Libraries**

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

4. **Create Train and Test Sets**

```python
train_size = int(len(data) * 0.8)
train_data = data[:train_size]
test_data = data[train_size:]
```

5. **Prepare Data for LSTM**

```python
def create_inout_sequences(input_data, tw):
    inout_seq = []
    L = len(input_data)
    for i in range(L - tw):
        train_seq = input_data[i:i + tw]
        train_label = input_data[i + tw:i + tw + 1]
        inout_seq.append((train_seq, train_label))
    return inout_seq

train_inout_seq = create_inout_sequences(train_data, seq_length)
test_inout_seq = create_inout_sequences(test_data, seq_length)
```

6. **Define LSTM Model**

```python
class LSTM(nn.Module):
    def __init__(self, input_size=1, hidden_layer_size=100, output_size=1):
        super().__init__()
        self.hidden_layer_size = hidden_layer_size

        self.lstm = nn.LSTM(input_size, hidden_layer_size)

        self.linear = nn.Linear(hidden_layer_size, output_size)

        self.hidden_cell = (torch.zeros(1, 1, self.hidden_layer_size),
                            torch.zeros(1, 1, self.hidden_layer_size))

    def forward(self, input_seq):
        lstm_out, self.hidden_cell = self.lstm(input_seq.view(len(input_seq), 1, -1), self.hidden_cell)
        predictions = self.linear(lstm_out.view(len(input_seq), -1))
        return predictions[-1]

model = LSTM()
loss_function = nn.MSELoss()
optimizer = optim.Adam(model.parameters(), lr=0.001)
```

7. **Train the Model**

```python
epochs = 150

for i in range(epochs):
    for seq, labels in train_inout_seq:
        optimizer.zero_grad()
        model.hidden_cell = (torch.zeros(1, 1, model.hidden_layer_size),
                            torch.zeros(1, 1, model.hidden_layer_size))

        y_pred = model(seq)

        single_loss = loss_function(y_pred, labels)
        single_loss.backward()
        optimizer.step()

    if i % 25 == 1:
        print(f'Epoch {i} loss: {single_loss.item()}')
```

8. **Test the Model**

```python
fut_pred = 15
test_inputs = train_data[-seq_length:].tolist()

model.eval()

for i in range(fut_pred):
    seq = torch.FloatTensor(test_inputs[-seq_length:])
    with torch.no_grad():
        model.hidden_cell = (torch.zeros(1, 1, model.hidden_layer_size),
                            torch.zeros(1, 1, model.hidden_layer_size))
        test_inputs.append(model(seq).item())

actual_predictions = scaler.inverse_transform(np.array(test_inputs[seq_length:]).reshape(-1, 1))
x = np.arange(0, len(actual_predictions), 1)

plt.title('Model Prediction')
plt.scatter(x, actual_predictions)
plt.grid(True)
plt.show()
```

## Exercise 2: Hyperparameter Tuning & Empirical Benchmarking

In this exercise, we will perform hyperparameter tuning to optimize the LSTM model's performance. We will measure accuracy, latency, and convergence curves.

### Step-by-Step Tuning and Benchmarking

1. **Define Hyperparameters**

```python
hidden_layer_sizes = [50, 100, 150]
learning_rates = [0.001, 0.01, 0.1]
epochs = 150
```

2. **Benchmarking Function**

```python
def benchmark_lstm(hidden_layer_size, learning_rate):
    model = LSTM(hidden_layer_size=hidden_layer_size)
    loss_function = nn.MSELoss()
    optimizer = optim.Adam(model.parameters(), lr=learning_rate)

    losses = []
    for i in range(epochs):
        for seq, labels in train_inout_seq:
            optimizer.zero_grad()
            model.hidden_cell = (torch.zeros(1, 1, model.hidden_layer_size),
                                torch.zeros(1, 1, model.hidden_layer_size))

            y_pred = model(seq)

            single_loss = loss_function(y_pred, labels)
            single_loss.backward()
            optimizer.step()

        losses.append(single_loss.item())

    return losses
```

3. **Run Benchmarks**

```python
results = {}
for hidden_layer_size in hidden_layer_sizes:
    for learning_rate in learning_rates:
        print(f'Running benchmark for hidden_layer_size={hidden_layer_size}, learning_rate={learning_rate}')
        losses = benchmark_lstm(hidden_layer_size, learning_rate)
        results[(hidden_layer_size, learning_rate)] = losses
```

4. **Plot Convergence Curves**

```python
for (hidden_layer_size, learning_rate), losses in results.items():
    plt.plot(losses, label=f'hidden_layer_size={hidden_layer_size}, learning_rate={learning_rate}')

plt.title('Convergence Curves')
plt.xlabel('Epochs')
plt.ylabel('Loss')
plt.legend()
plt.grid(True)
plt.show()
```

## Exercise 3: Stress Testing, Edge Cases & Failure Mitigation

In this exercise, we will stress test the LSTM model by introducing edge cases and implementing guardrails to handle potential failures.

### Step-by-Step Stress Testing

1. **Introduce Edge Cases**

```python
def create_edge_case_sequences(input_data, tw):
    inout_seq = []
    L = len(input_data)
    for i in range(L - tw):
        train_seq = input_data[i:i + tw]
        train_label = input_data[i + tw:i + tw + 1]
        inout_seq.append((train_seq, train_label))
    # Introduce an edge case with a NaN value
    inout_seq.append((np.array([np.nan] * tw), np.array([0])))
    return inout_seq

edge_case_inout_seq = create_edge_case_sequences(train_data, seq_length)
```

2. **Handle Edge Cases**

```python
def safe_forward(model, input_seq):
    if np.isnan(input_seq).any():
        print("NaN detected in input sequence. Returning default value.")
        return torch.tensor([0.0])
    return model(input_seq)

model.eval()

for seq, labels in edge_case_inout_seq:
    seq = torch.FloatTensor(seq)
    with torch.no_grad():
        model.hidden_cell = (torch.zeros(1, 1, model.hidden_layer_size),
                            torch.zeros(1, 1, model.hidden_layer_size))
        prediction = safe_forward(model, seq)
        print(f'Prediction: {prediction.item()}')
```

## Verification Checklist & Quick Reference Cheat Sheet

### Essential Python Methods and Parameters

| Method/Parameter          | Description                                                                 |
|---------------------------|-----------------------------------------------------------------------------|
| `generate_sine_wave_data` | Generates sine wave data for training and testing.                          |
| `MinMaxScaler`            | Scales features to a given range.                                           |
| `create_inout_sequences`  | Creates input-output sequences for LSTM training.                           |
| `LSTM`                    | Defines the LSTM model architecture.                                        |
| `nn.MSELoss`              | Mean squared error loss function.                                           |
| `optim.Adam`              | Adam optimizer for training the model.                                      |
| `benchmark_lstm`          | Benchmarks the LSTM model with different hyperparameters.                   |
| `safe_forward`            | Safely handles edge cases by checking for NaN values in input sequences.    |

### Verification Flags

- **Loss Function**: `nn.MSELoss` is used to measure the mean squared error between predictions and actual values.
- **Optimizer**: `optim.Adam` is used for efficient gradient descent.
- **Epochs**: Number of iterations over the entire training dataset.
- **Hidden Layer Size**: Number of neurons in the LSTM hidden layer.
- **Learning Rate**: Step size for the optimizer during training.

By completing this lab, you will have a solid understanding of implementing, tuning, and testing LSTM models for time series prediction. This hands-on experience will equip you with the skills to apply LSTM architectures to various real-world problems.
