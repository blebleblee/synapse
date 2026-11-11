# Operational Verification Labs: 04 Hypothesis Testing And Statistical Significance

## Objective & Environment Setup

### Objective
The objective of this lab is to provide hands-on experience with hypothesis testing and statistical significance in the context of data analysis and machine learning. This lab will guide you through implementing hypothesis tests, tuning hyperparameters, benchmarking models, and handling edge cases. By the end of this lab, you will have a solid understanding of how to apply statistical methods to verify the significance of your results in a practical setting.

### Environment Setup
Ensure you have a Python 3.11+ environment with the following packages installed:
- NumPy
- Scikit-learn
- Matplotlib
- Seaborn
- Pandas

You can install these packages using pip:

```bash
pip install numpy scikit-learn matplotlib seaborn pandas
```

## Exercise 1: Hands-On Implementation & Pipeline Execution

### Hypothesis Testing Scenario
Suppose you are working with a dataset of customer satisfaction scores before and after a service improvement initiative. You want to determine if the service improvement has had a statistically significant impact on customer satisfaction.

### Implementation
We will perform a paired t-test to compare the means of the satisfaction scores before and after the service improvement.

```python
import numpy as np
import pandas as pd
from scipy import stats
import matplotlib.pyplot as plt
import seaborn as sns

# Generate synthetic data
np.random.seed(42)
before_scores = np.random.normal(loc=70, scale=10, size=100)
after_scores = np.random.normal(loc=75, scale=10, size=100)

# Create a DataFrame
data = pd.DataFrame({
    'Before': before_scores,
    'After': after_scores
})

# Perform paired t-test
t_stat, p_value = stats.ttest_rel(data['Before'], data['After'])

# Print results
print(f"Paired t-test results:\nT-statistic: {t_stat}\nP-value: {p_value}")

# Plotting the data
plt.figure(figsize=(12, 6))
sns.boxplot(data=data)
plt.title('Boxplot of Customer Satisfaction Scores Before and After Service Improvement')
plt.xlabel('Time Period')
plt.ylabel('Satisfaction Score')
plt.show()
```

### Explanation
- **Data Generation**: We generate synthetic data for customer satisfaction scores before and after the service improvement.
- **Paired t-test**: We use `stats.ttest_rel` to perform a paired t-test, which compares the means of two related samples.
- **Visualization**: We use Seaborn to create a boxplot to visualize the distribution of satisfaction scores before and after the service improvement.

## Exercise 2: Hyperparameter Tuning & Empirical Benchmarking

### Benchmarking Scenario
We will benchmark the performance of different machine learning models on a synthetic dataset to determine which model performs best in terms of accuracy and convergence.

### Implementation
We will train and evaluate a few different models using Scikit-learn and measure their accuracy.

```python
from sklearn.model_selection import train_test_split
from sklearn.datasets import make_classification
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC
from sklearn.metrics import accuracy_score

# Generate synthetic dataset
X, y = make_classification(n_samples=1000, n_features=20, n_informative=15, n_redundant=5, random_state=42)

# Split the dataset
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Define models
models = {
    'Logistic Regression': LogisticRegression(max_iter=1000),
    'Random Forest': RandomForestClassifier(n_estimators=100, random_state=42),
    'Support Vector Machine': SVC(kernel='linear', random_state=42)
}

# Train and evaluate models
results = {}
for name, model in models.items():
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    results[name] = accuracy

# Print results
print("Model Accuracies:")
for name, accuracy in results.items():
    print(f"{name}: {accuracy:.4f}")

# Plotting the results
plt.figure(figsize=(10, 6))
sns.barplot(x=list(results.keys()), y=list(results.values()))
plt.title('Model Accuracies')
plt.xlabel('Model')
plt.ylabel('Accuracy')
plt.ylim(0, 1)
plt.show()
```

### Explanation
- **Data Generation**: We generate a synthetic classification dataset using `make_classification`.
- **Model Training**: We define three different models (Logistic Regression, Random Forest, and Support Vector Machine) and train them on the training dataset.
- **Model Evaluation**: We evaluate each model on the test dataset and measure their accuracy.
- **Visualization**: We use Seaborn to create a barplot to visualize the accuracy of each model.

## Exercise 3: Stress Testing, Edge Cases & Failure Mitigation

### Stress Testing Scenario
We will test the robustness of our models by introducing noise to the dataset and evaluating their performance under these conditions.

### Implementation
We will add noise to the dataset and re-evaluate the models.

```python
# Add noise to the dataset
noisy_X = X + np.random.normal(loc=0, scale=5, size=X.shape)

# Split the noisy dataset
noisy_X_train, noisy_X_test, y_train, y_test = train_test_split(noisy_X, y, test_size=0.2, random_state=42)

# Re-train and evaluate models on noisy data
noisy_results = {}
for name, model in models.items():
    model.fit(noisy_X_train, y_train)
    y_pred = model.predict(noisy_X_test)
    accuracy = accuracy_score(y_test, y_pred)
    noisy_results[name] = accuracy

# Print results
print("Model Accuracies on Noisy Data:")
for name, accuracy in noisy_results.items():
    print(f"{name}: {accuracy:.4f}")

# Plotting the results
plt.figure(figsize=(10, 6))
sns.barplot(x=list(noisy_results.keys()), y=list(noisy_results.values()))
plt.title('Model Accuracies on Noisy Data')
plt.xlabel('Model')
plt.ylabel('Accuracy')
plt.ylim(0, 1)
plt.show()
```

### Explanation
- **Noise Addition**: We add Gaussian noise to the dataset to simulate real-world noise.
- **Model Re-training**: We re-train the models on the noisy dataset.
- **Model Re-evaluation**: We evaluate the models on the noisy test dataset and measure their accuracy.
- **Visualization**: We use Seaborn to create a barplot to visualize the accuracy of each model on the noisy data.

## Verification Checklist & Quick Reference Cheat Sheet

### Essential Python Methods & Parameters
- **Data Generation**:
  - `np.random.normal(loc=mean, scale=std, size=n)`: Generate normal distributed random numbers.
  - `make_classification(n_samples=n, n_features=n, n_informative=n, n_redundant=n, random_state=seed)`: Generate a synthetic classification dataset.

- **Model Training & Evaluation**:
  - `train_test_split(X, y, test_size=frac, random_state=seed)`: Split the dataset into training and test sets.
  - `LogisticRegression(max_iter=n)`: Logistic Regression model.
  - `RandomForestClassifier(n_estimators=n, random_state=seed)`: Random Forest model.
  - `SVC(kernel=kernel, random_state=seed)`: Support Vector Machine model.
  - `model.fit(X_train, y_train)`: Train the model.
  - `model.predict(X_test)`: Predict the labels for the test set.
  - `accuracy_score(y_true, y_pred)`: Calculate the accuracy of the model.

- **Visualization**:
  - `sns.boxplot(data=data)`: Create a boxplot.
  - `sns.barplot(x=x, y=y)`: Create a barplot.

### Verification Flags
- **Hypothesis Testing**:
  - `stats.ttest_rel(a, b)`: Perform a paired t-test.
- **Model Evaluation**:
  - `accuracy_score(y_true, y_pred)`: Calculate the accuracy of the model.

By following this lab guide, you will gain practical experience with hypothesis testing, model benchmarking, and stress testing in a data analysis context. This will enable you to make more informed decisions about the significance and robustness of your models in real-world applications.
