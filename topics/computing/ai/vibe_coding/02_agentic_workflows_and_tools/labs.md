# Operational Verification Labs

## Objective & Environment Setup

This lab aims to provide hands-on experience with agentic workflows and tools in the domain of AI and machine learning. Through this lab, you will gain practical knowledge in implementing, tuning, and verifying a machine learning pipeline using Python 3.11+. We will utilize popular libraries such as PyTorch, HuggingFace, NumPy, Scikit-learn, and Polars. Additionally, we will demonstrate real-world application integration by interacting with an API, such as Ollama.

To set up your environment, ensure that Python 3.11+ is installed. Verify your Python version by running:

```bash
python --version
```

Next, install the required packages using pip:

```bash
pip install torch transformers numpy scikit-learn polars
```

For API interaction, configure your API key. For Ollama, set your API key as an environment variable:

```bash
export OLLAMA_API_KEY='your_api_key_here'
```

## Exercise 1: Hands-On Implementation & Pipeline Execution

In this exercise, we will implement a machine learning pipeline that includes data preprocessing, model training, and evaluation. We will use a simple text classification task with the HuggingFace Transformers library and a dataset from Scikit-learn.

The following Python script implements the core prompt/model/algorithm for this topic:

```python
import numpy as np
import torch
from torch.utils.data import DataLoader, Dataset
from transformers import BertTokenizer, BertForSequenceClassification, Trainer, TrainingArguments
from sklearn.datasets import fetch_20newsgroups
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score

# Load dataset
newsgroups = fetch_20newsgroups(subset='all', remove=('headers', 'footers', 'quotes'))
texts = newsgroups.data
labels = newsgroups.target

# Encode labels
label_encoder = LabelEncoder()
encoded_labels = label_encoder.fit_transform(labels)

# Split dataset
train_texts, test_texts, train_labels, test_labels = train_test_split(texts, encoded_labels, test_size=0.2, random_state=42)

# Tokenizer
tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')

# Custom Dataset
class TextDataset(Dataset):
    def __init__(self, texts, labels, tokenizer, max_length=512):
        self.texts = texts
        self.labels = labels
        self.tokenizer = tokenizer
        self.max_length = max_length

    def __len__(self):
        return len(self.texts)

    def __getitem__(self, idx):
        text = self.texts[idx]
        label = self.labels[idx]
        encoding = self.tokenizer.encode_plus(
            text,
            add_special_tokens=True,
            max_length=self.max_length,
            return_token_type_ids=False,
            padding='max_length',
            return_attention_mask=True,
            return_tensors='pt',
        )
        return {
            'text': text,
            'input_ids': encoding['input_ids'].flatten(),
            'attention_mask': encoding['attention_mask'].flatten(),
            'labels': torch.tensor(label, dtype=torch.long)
        }

# Create datasets
train_dataset = TextDataset(train_texts, train_labels, tokenizer)
test_dataset = TextDataset(test_texts, test_labels, tokenizer)

# DataLoader
train_loader = DataLoader(train_dataset, batch_size=8, shuffle=True)
test_loader = DataLoader(test_dataset, batch_size=8, shuffle=False)

# Model
model = BertForSequenceClassification.from_pretrained('bert-base-uncased', num_labels=len(label_encoder.classes_))

# Training arguments
training_args = TrainingArguments(
    output_dir='./results',
    num_train_epochs=3,
    per_device_train_batch_size=8,
    per_device_eval_batch_size=8,
    warmup_steps=500,
    weight_decay=0.01,
    logging_dir='./logs',
    logging_steps=10,
    evaluation_strategy="epoch"
)

# Trainer
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=train_dataset,
    eval_dataset=test_dataset,
    compute_metrics=lambda p: {'accuracy': accuracy_score(p.label_ids, np.argmax(p.predictions, axis=1))}
)

# Train
trainer.train()

# Evaluate
results = trainer.evaluate()
print(results)
```

This script performs the following steps:
- Loads the 20 Newsgroups dataset and encodes the labels.
- Splits the dataset into training and test sets.
- Initializes a BERT tokenizer and defines a custom dataset class.
- Creates DataLoader instances for training and testing.
- Loads a pre-trained BERT model for sequence classification.
- Sets up training arguments and initializes a Trainer instance.
- Trains the model and evaluates its performance.

## Exercise 2: Hyperparameter Tuning & Empirical Benchmarking

In this exercise, we will perform hyperparameter tuning and empirical benchmarking to measure the accuracy, latency distributions, and convergence curves of our model. We will use the `optuna` library for hyperparameter tuning and the `time` module for latency measurement.

First, install the `optuna` library:

```bash
pip install optuna
```

The following Python script performs hyperparameter tuning and benchmarking:

```python
import optuna
import time
from transformers import BertForSequenceClassification, Trainer, TrainingArguments
from sklearn.metrics import accuracy_score

# Objective function for Optuna
def objective(trial):
    # Hyperparameters to tune
    learning_rate = trial.suggest_loguniform('learning_rate', 1e-5, 5e-5)
    num_train_epochs = trial.suggest_int('num_train_epochs', 2, 4)
    per_device_train_batch_size = trial.suggest_categorical('per_device_train_batch_size', [8, 16])
    warmup_steps = trial.suggest_int('warmup_steps', 0, 500)
    weight_decay = trial.suggest_loguniform('weight_decay', 1e-5, 1e-2)

    # Model
    model = BertForSequenceClassification.from_pretrained('bert-base-uncased', num_labels=len(label_encoder.classes_))

    # Training arguments
    training_args = TrainingArguments(
        output_dir='./results',
        num_train_epochs=num_train_epochs,
        per_device_train_batch_size=per_device_train_batch_size,
        per_device_eval_batch_size=per_device_train_batch_size,
        warmup_steps=warmup_steps,
        weight_decay=weight_decay,
        logging_dir='./logs',
        logging_steps=10,
        evaluation_strategy="epoch"
    )

    # Trainer
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=test_dataset,
        compute_metrics=lambda p: {'accuracy': accuracy_score(p.label_ids, np.argmax(p.predictions, axis=1))}
    )

    # Train
    start_time = time.time()
    trainer.train()
    end_time = time.time()

    # Evaluate
    results = trainer.evaluate()
    accuracy = results['eval_accuracy']
    latency = end_time - start_time

    # Log hyperparameters and metrics
    trial.set_user_attr('accuracy', accuracy)
    trial.set_user_attr('latency', latency)
    return accuracy
```

This script defines an objective function for Optuna to tune hyperparameters such as learning rate, number of training epochs, batch size, warmup steps, and weight decay. It measures the model's accuracy and training latency, logging these metrics for each trial.
