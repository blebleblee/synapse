Operational Verification Labs: 01 Supervised Vs Unsupervised Learning
===========================================================

### Objective & Environment Setup

This lab guides hands-on AI engineers and practitioners through the implementation and verification of supervised and unsupervised learning techniques. To complete this lab, ensure you have a Python 3.11+ environment set up with the following packages installed:

* PyTorch
* HuggingFace
* NumPy
* Scikit-learn
* Ollama
* Polars

Additionally, configure your API settings as required for the specific tasks.

### Exercise 1: Hands-On Implementation & Pipeline Execution

Implement a basic supervised learning model using PyTorch for classification. This example uses the MNIST dataset for demonstration purposes.

```python
import torch
import torch.nn as nn
import torchvision
import torchvision.transforms as transforms

# Define the neural network model
class Net(nn.Module):
    def __init__(self):
        super(Net, self).__init__()
        self.fc1 = nn.Linear(784, 128)
        self.fc2 = nn.Linear(128, 10)

    def forward(self, x):
        x = torch.relu(self.fc1(x))
        x = self.fc2(x)
        return x

# Initialize the model, loss function, and optimizer
model = Net()
criterion = nn.CrossEntropyLoss()
optimizer = torch.optim.Adam(model.parameters(), lr=0.001)

# Load the MNIST dataset
transform = transforms.Compose([transforms.ToTensor()])
trainset = torchvision.datasets.MNIST(root='./data', train=True, download=True, transform=transform)
trainloader = torch.utils.data.DataLoader(trainset, batch_size=64, shuffle=True)

# Train the model
for epoch in range(10):
    running_loss = 0.0
    for i, data in enumerate(trainloader, 0):
        inputs, labels = data
        optimizer.zero_grad()
        outputs = model(inputs.view(-1, 784))
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()
        running_loss += loss.item()
    print('Epoch %d, Loss: %.3f' % (epoch+1, running_loss/(i+1)))

# Evaluate the model
model.eval()
correct = 0
total = 0
with torch.no_grad():
    for data in trainloader:
        inputs, labels = data
        outputs = model(inputs.view(-1, 784))
        _, predicted = torch.max(outputs, 1)
        total += labels.size(0)
        correct += (predicted == labels).sum().item()

accuracy = correct/total
print('Accuracy: %.2f' % accuracy)
```

### Exercise 2: Hyperparameter Tuning & Empirical Benchmarking

Measure the accuracy and latency of the model using the Hugging Face Transformers library. This example uses the `transformers` library to load the pre-trained model and evaluate its performance.

```python
from transformers import AutoModelForSequenceClassification, AutoTokenizer

# Load the pre-trained model and tokenizer
model_name = "distilbert-base-uncased"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSequenceClassification.from_pretrained(model_name)

# Define the evaluation function
def evaluate(model, tokenizer, text):
    inputs = tokenizer.encode_plus(text, 
                                    add_special_tokens=True, 
                                    max_length=512, 
                                    return_attention_mask=True, 
                                    return_tensors='pt')
    outputs = model(**inputs)
    return torch.argmax(outputs.logits)

# Evaluate the model on a sample text
text = "This is a sample text for evaluation."
accuracy = evaluate(model, tokenizer, text)
print('Accuracy: %.2f' % accuracy)
```

### Exercise 3: Stress Testing, Edge Cases & Failure Mitigation

Reproduce failure modes and test edge cases by intentionally introducing errors into the model or dataset. Implement guardrails or error handling to mitigate these failures.

```python
# Introduce an error into the model
model.fc1.weight.data.fill_(0)

# Test the model on a sample text
text = "This is a sample text for evaluation."
try:
    accuracy = evaluate(model, tokenizer, text)
    print('Accuracy: %.2f' % accuracy)
except Exception as e:
    print('Error: %s' % str(e))
```

### Verification Checklist & Quick Reference Cheat Sheet

| Python Method | Parameters | Verification Flags |
| --- | --- | --- |
| `torch.nn.Linear` | `in_features`, `out_features`, `bias` | `requires_grad=True` |
| `torch.nn.ReLU` |  |  |
| `torch.optim.Adam` | `lr`, `betas`, `eps` | `amsgrad=True` |
| `torch.utils.data.DataLoader` | `batch_size`, `shuffle`, `drop_last` | `num_workers=4` |
| `transformers.AutoModelForSequenceClassification` | `model_name` | `use_cache=True` |
| `transformers.AutoTokenizer` | `model_name` | `cache_dir='./cache'` |

Note: This is a basic example and may require modifications to suit your specific use case. Ensure to test and verify the code thoroughly before deployment.
