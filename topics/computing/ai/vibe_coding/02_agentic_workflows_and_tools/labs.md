# Operational Verification Labs

## Objective & Environment Setup

This lab aims to provide hands-on experience with implementing, verifying, and optimizing AI workflows and tools. You will guide through setting up a robust AI pipeline, tuning hyperparameters, benchmarking performance, and handling edge cases. The lab utilizes a Python 3.11+ environment, leveraging popular libraries such as PyTorch, HuggingFace Transformers, NumPy, Scikit-learn, and Polars. Additionally, interaction with an AI model API, such as Ollama or another service, will demonstrate real-world application.

To begin, ensure you have Python 3.11+ installed on your system. Verify your Python version by running:

```bash
python --version
```

Next, install the required packages using pip:

```bash
pip install torch transformers numpy scikit-learn polars
```

For API interaction, configure your API key and endpoint by setting environment variables. For example, if using Ollama, set:

```bash
export OLLAMA_API_KEY='your_api_key_here'
export OLLAMA_API_URL='https://api.ollama.com/v1'
```

## Exercise 1: Hands-On Implementation & Pipeline Execution

In this exercise, you will implement a simple AI pipeline that includes data preprocessing, model training, and inference. A pre-trained transformer model from HuggingFace will be used to perform text classification on a dataset. The pipeline will be implemented in a complete, runnable Python script.

First, import the necessary libraries and load a dataset. The IMDB dataset from HuggingFace's `datasets` library will be used for sentiment analysis.

```python
import torch
from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
from datasets import load_dataset
from sklearn.metrics import accuracy_score
import numpy as np

# Load the IMDB dataset
dataset = load_dataset('imdb')

# Load a pre-trained transformer model and tokenizer
model_name = 'distilbert-base-uncased-finetuned-sst-2-english'
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSequenceClassification.from_pretrained(model_name)

# Create a text classification pipeline
classifier = pipeline('sentiment-analysis', model=model, tokenizer=tokenizer)

# Preprocess the dataset
def preprocess_function(examples):
    return tokenizer(examples['text'], truncation=True, padding='max_length', max_length=128)

encoded_dataset = dataset.map(preprocess_function, batched=True)

# Split the dataset into training and test sets
train_dataset = encoded_dataset['train'].shuffle(seed=42).select(range(1000))
test_dataset = encoded_dataset['test'].shuffle(seed=42).select(range(1000))

# Convert the datasets to PyTorch tensors
train_dataset.set_format(type='torch', columns=['input_ids', 'attention_mask', 'label'])
test_dataset.set_format(type='torch', columns=['input_ids', 'attention_mask', 'label'])

# Define a simple training loop
def train_model(model, train_dataset, epochs=3, batch_size=16, learning_rate=2e-5):
    model.train()
    optimizer = torch.optim.AdamW(model.parameters(), lr=learning_rate)
    loss_fn = torch.nn.CrossEntropyLoss()

    for epoch in range(epochs):
        total_loss = 0
        for i in range(0, len(train_dataset), batch_size):
            batch = {k: v.to('cuda') for k, v in train_dataset[i:i+batch_size].items()}
            outputs = model(**batch)
            loss = loss_fn(outputs.logits, batch['label'])
            total_loss += loss.item()

            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

        print(f'Epoch {epoch + 1}, Loss: {total_loss / len(train_dataset)}')

# Train the model
train_model(model, train_dataset)

# Evaluate the model
def evaluate_model(model, test_dataset):
    model.eval()
    predictions = []
    true_labels = []

    with torch.no_grad():
        for i in range(0, len(test_dataset), 16):
            batch = {k: v.to('cuda') for k, v in test_dataset[i:i+16].items()}
            outputs = model(**batch)
            logits = outputs.logits
            preds = torch.argmax(logits, dim=-1)
            predictions.extend(preds.cpu().numpy())
            true_labels.extend(batch['label'].cpu().numpy())

    accuracy = accuracy_score(true_labels, predictions)
    print(f'Accuracy: {accuracy}')

# Evaluate the trained model
evaluate_model(model, test_dataset)
```

This script sets up a text classification pipeline using a pre-trained DistilBERT model. It preprocesses the IMDB dataset, trains the model, and evaluates its accuracy on a test set. The script is complete and ready to run.

## Exercise 2: Hyperparameter Tuning & Empirical Benchmarking

In this exercise, you will perform hyperparameter tuning and benchmark the performance of your model. Accuracy, latency distributions, and token costs will be measured. Scikit-learn's `GridSearchCV` will be used for hyperparameter tuning, and Polars for efficient data handling.

First, modify the training loop to include hyperparameter tuning using `GridSearchCV`.

```python
from sklearn.model_selection import GridSearchCV
from sklearn.metrics import make_scorer
from transformers import Trainer, TrainingArguments
import polars as pl

# Define a custom Trainer class for Scikit-learn compatibility
class CustomTrainer(Trainer):
    def compute_metrics(self, eval_pred):
        logits, labels = eval_pred
        preds = np.argmax(logits, axis=-1)
        return {'accuracy': accuracy_score(labels, preds)}

# Define a function to create a Trainer instance
def create_trainer(model, train_dataset, eval_dataset, learning_rate, batch_size):
    training_args = TrainingArguments(
        output_dir='./results',
        evaluation_strategy='epoch',
        learning_rate=learning_rate,
        per_device_train_batch_size=batch_size,
        per_device_eval_batch_size=batch_size,
        num_train_epochs=3,
        weight_decay=0.01,
    )
    return CustomTrainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=eval_dataset,
    )

# Define hyperparameters to tune
param_grid = {
    'learning_rate': [2e-5, 3e-5, 5e-5],
    'batch_size': [16, 32, 64],
}

# Define a scoring function
scorer = make_scorer(accuracy_score)

# Perform hyperparameter tuning
grid_search = GridSearchCV(
    estimator=CustomTrainer(model, train_dataset, test_dataset, learning_rate=2e-5, batch_size=16),
    param_grid=param_grid,
    scoring=scorer,
    cv=3,
    refit=True,
    verbose=2,
)

grid_search.fit(train_dataset)

# Print the best hyperparameters and accuracy
print(f'Best hyperparameters: {grid_search.best_params_}')
print(f'Best accuracy: {grid_search.best_score_}')

# Benchmark the model with the best hyperparameters
best_trainer = grid_search.best_estimator_
best_trainer.train()

# Evaluate the model
evaluate_model(best_trainer.model, test_dataset)

# Measure latency distribution
```
