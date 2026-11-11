# Operational Verification Labs: 01 Variational Autoencoders (VAEs)

## Objective & Environment Setup

The objective of this lab is to provide hands-on experience with Variational Autoencoders (VAEs), a fundamental generative model in AI. By the end of this lab, you will have implemented a VAE, tuned its hyperparameters, and performed stress testing to ensure robustness. This lab assumes a Python 3.11+ environment with the following packages installed:

- PyTorch
- NumPy
- Scikit-learn
- Matplotlib

You can set up your environment using the following commands:

```bash
pip install torch numpy scikit-learn matplotlib
```

## Exercise 1: Hands-On Implementation & Pipeline Execution

In this exercise, we will implement a simple VAE using PyTorch. The VAE will be trained on the MNIST dataset, a standard dataset for handwritten digit recognition.

### Step-by-Step Implementation

1. **Import Libraries**

    ```python
    import torch
    import torch.nn as nn
    import torch.optim as optim
    import torch.nn.functional as F
    from torchvision import datasets, transforms
    from torch.utils.data import DataLoader
    import matplotlib.pyplot as plt
    ```

2. **Define the VAE Model**

    ```python
    class VAE(nn.Module):
        def __init__(self, input_dim=784, hidden_dim=400, latent_dim=20):
            super(VAE, self).__init__()
            self.fc1 = nn.Linear(input_dim, hidden_dim)
            self.fc21 = nn.Linear(hidden_dim, latent_dim)
            self.fc22 = nn.Linear(hidden_dim, latent_dim)
            self.fc3 = nn.Linear(latent_dim, hidden_dim)
            self.fc4 = nn.Linear(hidden_dim, input_dim)

        def encode(self, x):
            h1 = F.relu(self.fc1(x))
            return self.fc21(h1), self.fc22(h1)

        def reparameterize(self, mu, logvar):
            std = torch.exp(0.5 * logvar)
            eps = torch.randn_like(std)
            return mu + eps * std

        def decode(self, z):
            h3 = F.relu(self.fc3(z))
            return torch.sigmoid(self.fc4(h3))

        def forward(self, x):
            mu, logvar = self.encode(x.view(-1, 784))
            z = self.reparameterize(mu, logvar)
            return self.decode(z), mu, logvar
    ```

3. **Define the Loss Function**

    ```python
    def loss_function(recon_x, x, mu, logvar):
        BCE = F.binary_cross_entropy(recon_x, x.view(-1, 784), reduction='sum')
        KLD = -0.5 * torch.sum(1 + logvar - mu.pow(2) - logvar.exp())
        return BCE + KLD
    ```

4. **Load and Preprocess the Data**

    ```python
    transform = transforms.Compose([transforms.ToTensor()])
    train_dataset = datasets.MNIST('./data', train=True, download=True, transform=transform)
    train_loader = DataLoader(train_dataset, batch_size=128, shuffle=True)
    ```

5. **Train the Model**

    ```python
    def train(model, train_loader, optimizer, epoch):
        model.train()
        train_loss = 0
        for batch_idx, (data, _) in enumerate(train_loader):
            optimizer.zero_grad()
            recon_batch, mu, logvar = model(data)
            loss = loss_function(recon_batch, data, mu, logvar)
            loss.backward()
            train_loss += loss.item()
            optimizer.step()
            if batch_idx % 100 == 0:
                print(f'Train Epoch: {epoch} [{batch_idx * len(data)}/{len(train_loader.dataset)}] Loss: {loss.item() / len(data):.6f}')
        print(f'====> Epoch: {epoch} Average loss: {train_loss / len(train_loader.dataset):.4f}')
    ```

6. **Visualize the Results**

    ```python
    def test(model, test_loader):
        model.eval()
        with torch.no_grad():
            for i, (data, _) in enumerate(test_loader):
                recon_batch, mu, logvar = model(data)
                if i == 0:
                    n = min(data.size(0), 8)
                    comparison = torch.cat([data[:n], recon_batch.view(128, 1, 28, 28)[:n]])
                    save_image(comparison.cpu(), 'results/reconstruction_' + str(epoch) + '.png', nrow=n)
                break

    def save_image(tensor, filename, nrow=8, padding=2, normalize=False, range=None, scale_each=False, pad_value=0):
        from PIL import Image
        grid = torchvision.utils.make_grid(tensor, nrow=nrow, padding=padding, pad_value=pad_value,
                                          normalize=normalize, range=range, scale_each=scale_each)
        ndarr = grid.mul(255).add_(0.5).clamp_(0, 255).permute(1, 2, 0).to('cpu', torch.uint8).numpy()
        im = Image.fromarray(ndarr)
        im.save(filename)
    ```

7. **Run the Training Loop**

    ```python
    model = VAE()
    optimizer = optim.Adam(model.parameters(), lr=1e-3)

    for epoch in range(1, 11):
        train(model, train_loader, optimizer, epoch)
    ```

## Exercise 2: Hyperparameter Tuning & Empirical Benchmarking

In this exercise, we will perform hyperparameter tuning and benchmark the VAE model based on reconstruction loss and convergence speed.

### Hyperparameter Tuning

We will experiment with different hidden dimensions and learning rates.

```python
import itertools

# Define hyperparameters to tune
hidden_dims = [200, 400, 600]
learning_rates = [1e-3, 5e-4, 1e-4]

# Perform grid search
best_loss = float('inf')
best_params = None

for hidden_dim, lr in itertools.product(hidden_dims, learning_rates):
    model = VAE(hidden_dim=hidden_dim)
    optimizer = optim.Adam(model.parameters(), lr=lr)
    for epoch in range(1, 6):
        train_loss = train(model, train_loader, optimizer, epoch)
        if train_loss < best_loss:
            best_loss = train_loss
            best_params = (hidden_dim, lr)

print(f'Best hyperparameters: hidden_dim={best_params[0]}, lr={best_params[1]}')
```

### Benchmarking

We will measure the convergence speed by plotting the loss over epochs.

```python
import matplotlib.pyplot as plt

def plot_loss(losses, title='Training Loss'):
    plt.figure(figsize=(10, 5))
    plt.plot(losses, label='Loss')
    plt.title(title)
    plt.xlabel('Epoch')
    plt.ylabel('Loss')
    plt.legend()
    plt.show()

# Run training with best parameters and collect losses
model = VAE(hidden_dim=best_params[0])
optimizer = optim.Adam(model.parameters(), lr=best_params[1])

losses = []
for epoch in range(1, 11):
    train_loss = train(model, train_loader, optimizer, epoch)
    losses.append(train_loss)

plot_loss(losses)
```

## Exercise 3: Stress Testing, Edge Cases & Failure Mitigation

In this exercise, we will test the VAE model under various edge cases and implement guardrails to handle potential failures.

### Stress Testing

We will test the model with noisy data and missing data.

```python
import numpy as np

# Add noise to the data
def add_noise(data, noise_factor=0.1):
    noise = torch.randn_like(data) * noise_factor
    noisy_data = data + noise
    noisy_data = torch.clamp(noisy_data, 0., 1.)
    return noisy_data

# Test with noisy data
noisy_data = add_noise(train_loader.dataset.data.float() / 255.0)
noisy_loader = DataLoader(noisy_data, batch_size=128, shuffle=True)

# Train with noisy data
model = VAE(hidden_dim=best_params[0])
optimizer = optim.Adam(model.parameters(), lr=best_params[1])

for epoch in range(1, 6):
    train(model, noisy_loader, optimizer, epoch)
```

### Edge Cases

We will test the model with edge cases such as all-zero images.

```python
# Create all-zero images
zero_data = torch.zeros_like(train_loader.dataset.data.float() / 255.0)
zero_loader = DataLoader(zero_data, batch_size=128, shuffle=True)

# Train with zero data
model = VAE(hidden_dim=best_params[0])
optimizer = optim.Adam(model.parameters(), lr=best_params[1])

for epoch in range(1, 6):
    train(model, zero_loader, optimizer, epoch)
```

### Failure Mitigation

We will implement guardrails to handle potential failures such as NaN values in the loss.

```python
def train_with_guardrails(model, train_loader, optimizer, epoch):
    model.train()
    train_loss = 0
    for batch_idx, (data, _) in enumerate(train_loader):
        optimizer.zero_grad()
        recon_batch, mu, logvar = model(data)
        loss = loss_function(recon_batch, data, mu, logvar)
        if torch.isnan(loss):
            print(f'NaN loss detected at epoch {epoch}, batch {batch_idx}. Skipping this batch.')
            continue
        loss.backward()
        train_loss += loss.item()
        optimizer.step()
        if batch_idx % 100 == 0:
            print(f'Train Epoch: {epoch} [{batch_idx * len(data)}/{len(train_loader.dataset)}] Loss: {loss.item() / len(data):.6f}')
    print(f'====> Epoch: {epoch} Average loss: {train_loss / len(train_loader.dataset):.4f}')

# Run training with guardrails
model = VAE(hidden_dim=best_params[0])
optimizer = optim.Adam(model.parameters(), lr=best_params[1])

for epoch in range(1, 11):
    train_with_guardrails(model, train_loader, optimizer, epoch)
```

## Verification Checklist & Quick Reference Cheat Sheet

### Essential Python Methods and Parameters

- **Model Definition:**
  - `VAE(input_dim, hidden_dim, latent_dim)`
  - `encode(x)`
  - `reparameterize(mu, logvar)`
  - `decode(z)`
  - `forward(x)`

- **Loss Function:**
  - `loss_function(recon_x, x, mu, logvar)`

- **Training:**
  - `train(model, train_loader, optimizer, epoch)`
  - `train_with_guardrails(model, train_loader, optimizer, epoch)`

- **Testing and Visualization:**
  - `test(model, test_loader)`
  - `save_image(tensor, filename, nrow, padding, normalize, range, scale_each, pad_value)`

- **Hyperparameter Tuning:**
  - `itertools.product(hidden_dims, learning_rates)`

- **Benchmarking:**
  - `plot_loss(losses, title)`

- **Stress Testing:**
  - `add_noise(data, noise_factor)`

### Verification Flags

- **NaN Loss Detection:**
  - `torch.isnan(loss)`

This lab provides a comprehensive hands-on experience with Variational Autoencoders, covering implementation, hyperparameter tuning, benchmarking, and stress testing. By following the steps outlined in this guide, you will gain a deep understanding of VAEs and their practical applications in generative AI.
