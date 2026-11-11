# Operational Verification Labs: 01 Exploratory Data Analysis And Pandas

## Objective & Environment Setup

### Objective
The primary objective of this lab is to provide hands-on experience with exploratory data analysis (EDA) using the Pandas library in Python. This lab will guide you through loading, cleaning, transforming, and visualizing data to derive meaningful insights. By the end of this lab, you will have a solid understanding of how to perform EDA using Pandas and be able to apply these skills to real-world datasets.

### Environment Setup
Ensure you have a Python 3.11+ environment set up. You will need to install the following packages:

```bash
pip install pandas numpy matplotlib seaborn scikit-learn
```

These packages will provide the necessary tools for data manipulation, numerical operations, data visualization, and machine learning.

## Exercise 1: Hands-On Implementation & Pipeline Execution

### Loading and Inspecting Data
We will use the popular Titanic dataset for this exercise. The dataset contains information about the passengers on the Titanic, including their survival status, class, age, fare, and more.

#### Step-by-Step Implementation

1. **Import Libraries**

   ```python
   import pandas as pd
   import numpy as np
   import matplotlib.pyplot as plt
   import seaborn as sns
   ```

2. **Load the Dataset**

   ```python
   # Load the Titanic dataset from a CSV file
   url = 'https://raw.githubusercontent.com/datasciencedojo/datasets/master/titanic.csv'
   titanic_data = pd.read_csv(url)
   ```

3. **Inspect the Data**

   ```python
   # Display the first few rows of the dataset
   print(titanic_data.head())

   # Get a summary of the dataset
   print(titanic_data.info())

   # Get basic statistics of the dataset
   print(titanic_data.describe())
   ```

4. **Data Cleaning**

   ```python
   # Check for missing values
   print(titanic_data.isnull().sum())

   # Fill missing values in the 'Age' column with the median age
   titanic_data['Age'].fillna(titanic_data['Age'].median(), inplace=True)

   # Drop rows with missing values in the 'Embarked' column
   titanic_data.dropna(subset=['Embarked'], inplace=True)
   ```

5. **Data Transformation**

   ```python
   # Convert 'Sex' column to numerical values
   titanic_data['Sex'] = titanic_data['Sex'].map({'male': 0, 'female': 1})

   # Convert 'Embarked' column to numerical values
   titanic_data['Embarked'] = titanic_data['Embarked'].map({'S': 0, 'C': 1, 'Q': 2})
   ```

6. **Data Visualization**

   ```python
   # Plot the distribution of ages
   plt.figure(figsize=(10, 6))
   sns.histplot(titanic_data['Age'], bins=30, kde=True)
   plt.title('Age Distribution')
   plt.xlabel('Age')
   plt.ylabel('Frequency')
   plt.show()

   # Plot the survival rate by class
   plt.figure(figsize=(10, 6))
   sns.barplot(x='Pclass', y='Survived', data=titanic_data)
   plt.title('Survival Rate by Class')
   plt.xlabel('Passenger Class')
   plt.ylabel('Survival Rate')
   plt.show()
   ```

## Exercise 2: Hyperparameter Tuning & Empirical Benchmarking

### Benchmarking Data Transformation and Visualization

In this exercise, we will benchmark the time taken to perform data transformations and visualizations. This will help us understand the performance implications of different operations.

1. **Benchmark Data Transformation**

   ```python
   import time

   # Measure the time taken to fill missing values in the 'Age' column
   start_time = time.time()
   titanic_data['Age'].fillna(titanic_data['Age'].median(), inplace=True)
   end_time = time.time()
   print(f"Time taken to fill missing values in 'Age': {end_time - start_time} seconds")

   # Measure the time taken to convert 'Sex' column to numerical values
   start_time = time.time()
   titanic_data['Sex'] = titanic_data['Sex'].map({'male': 0, 'female': 1})
   end_time = time.time()
   print(f"Time taken to convert 'Sex' column: {end_time - start_time} seconds")
   ```

2. **Benchmark Data Visualization**

   ```python
   # Measure the time taken to plot the age distribution
   start_time = time.time()
   plt.figure(figsize=(10, 6))
   sns.histplot(titanic_data['Age'], bins=30, kde=True)
   plt.title('Age Distribution')
   plt.xlabel('Age')
   plt.ylabel('Frequency')
   plt.show()
   end_time = time.time()
   print(f"Time taken to plot age distribution: {end_time - start_time} seconds")

   # Measure the time taken to plot the survival rate by class
   start_time = time.time()
   plt.figure(figsize=(10, 6))
   sns.barplot(x='Pclass', y='Survived', data=titanic_data)
   plt.title('Survival Rate by Class')
   plt.xlabel('Passenger Class')
   plt.ylabel('Survival Rate')
   plt.show()
   end_time = time.time()
   print(f"Time taken to plot survival rate by class: {end_time - start_time} seconds")
   ```

## Exercise 3: Stress Testing, Edge Cases & Failure Mitigation

### Testing Edge Cases and Implementing Guardrails

In this exercise, we will test the robustness of our data pipeline by introducing edge cases and implementing guardrails to handle potential failures.

1. **Testing Edge Cases**

   ```python
   # Test with a dataset containing missing values in critical columns
   edge_case_data = titanic_data.copy()
   edge_case_data['Age'] = np.nan
   edge_case_data['Embarked'] = np.nan

   # Attempt to fill missing values in the 'Age' column
   try:
       edge_case_data['Age'].fillna(edge_case_data['Age'].median(), inplace=True)
   except Exception as e:
       print(f"Error filling missing values in 'Age': {e}")

   # Attempt to drop rows with missing values in the 'Embarked' column
   try:
       edge_case_data.dropna(subset=['Embarked'], inplace=True)
   except Exception as e:
       print(f"Error dropping rows with missing values in 'Embarked': {e}")
   ```

2. **Implementing Guardrails**

   ```python
   # Implement guardrails to handle missing values in critical columns
   def clean_data(data):
       if data['Age'].isnull().sum() > 0:
           data['Age'].fillna(data['Age'].median(), inplace=True)
       if data['Embarked'].isnull().sum() > 0:
           data['Embarked'].dropna(subset=['Embarked'], inplace=True)
       return data

   # Clean the edge case data
   cleaned_data = clean_data(edge_case_data)
   print(cleaned_data.head())
   ```

## Verification Checklist & Quick Reference Cheat Sheet

### Essential Python Methods and Parameters

| Method/Parameter | Description |
|------------------|-------------|
| `pd.read_csv()`  | Reads a CSV file into a DataFrame. |
| `DataFrame.head()` | Returns the first n rows of the DataFrame. |
| `DataFrame.info()` | Provides a concise summary of the DataFrame. |
| `DataFrame.describe()` | Generates descriptive statistics for the DataFrame. |
| `DataFrame.isnull().sum()` | Returns the number of missing values in each column. |
| `DataFrame.fillna()` | Fills missing values in the DataFrame. |
| `DataFrame.dropna()` | Drops rows with missing values in the specified column. |
| `DataFrame.map()` | Maps values of Series according to an input dictionary or function. |
| `sns.histplot()` | Plots a histogram with a kernel density estimate. |
| `sns.barplot()` | Plots a bar plot. |
| `time.time()` | Returns the current time in seconds since the Epoch. |

### Verification Flags

- **Data Loading**: Ensure the dataset is loaded correctly by checking the first few rows and the summary.
- **Data Cleaning**: Verify that missing values are handled appropriately by checking the number of missing values before and after cleaning.
- **Data Transformation**: Confirm that categorical variables are correctly transformed into numerical values.
- **Data Visualization**: Validate that plots are generated correctly and provide meaningful insights.

By following this lab guide, you will gain practical experience with exploratory data analysis using Pandas. This will equip you with the skills to perform similar analyses on other datasets and contribute effectively to data-driven projects.
