# Operational Verification Labs: 04 Dashboard Storytelling And Tableau

## Objective & Environment Setup

### Objective
The objective of this lab is to build a comprehensive data visualization dashboard using Tableau. We will focus on storytelling through data, ensuring that the dashboard not only presents data accurately but also communicates insights effectively. The lab will involve data extraction, transformation, loading (ETL) processes, and the creation of interactive visualizations.

### Environment Setup
Ensure you have the following environment setup:
- **Python 3.11+**: This is the base environment for running our scripts.
- **Required Python Packages**: Install the following packages using pip:
  ```bash
  pip install pandas numpy scikit-learn requests
  ```
- **Tableau Desktop**: Download and install Tableau Desktop from the official Tableau website.
- **API Configuration**: For this lab, we will use a sample API to fetch data. Ensure you have access to an API key if required.

## Exercise 1: Hands-On Implementation & Pipeline Execution

### Data Extraction and Transformation

We will start by extracting data from a sample API and transforming it into a format suitable for visualization. For this example, we will use a public API that provides sample sales data.

#### Complete, Runnable Python Script

```python
import requests
import pandas as pd
import numpy as np

# Sample API endpoint
API_URL = "https://api.sampleapis.com/coffee/hot"

# Fetch data from the API
response = requests.get(API_URL)
data = response.json()

# Convert JSON data to a DataFrame
df = pd.DataFrame(data)

# Data transformation: Adding a new column for price category
def categorize_price(price):
    if price < 5:
        return 'Low'
    elif price < 10:
        return 'Medium'
    else:
        return 'High'

df['PriceCategory'] = df['price'].apply(categorize_price)

# Save the transformed data to a CSV file
df.to_csv('transformed_sales_data.csv', index=False)

print("Data extraction and transformation complete. CSV file saved.")
```

### Data Loading into Tableau

1. **Open Tableau Desktop**.
2. **Connect to Data**: Click on `Connect` and select `Text File` to load the `transformed_sales_data.csv` file.
3. **Data Source Setup**: Ensure the data is correctly loaded and the schema is as expected.
4. **Create Calculated Fields**: Create a calculated field for `PriceCategory` if not already done in the script.
5. **Build Visualizations**: Create various visualizations such as bar charts, line graphs, and pie charts to represent the data.

## Exercise 2: Hyperparameter Tuning & Empirical Benchmarking

In this exercise, we will benchmark the performance of our data pipeline by measuring the time taken for data extraction and transformation.

#### Real Benchmarking Code

```python
import time

# Start timing
start_time = time.time()

# Fetch data from the API
response = requests.get(API_URL)
data = response.json()

# Convert JSON data to a DataFrame
df = pd.DataFrame(data)

# Data transformation: Adding a new column for price category
df['PriceCategory'] = df['price'].apply(categorize_price)

# Save the transformed data to a CSV file
df.to_csv('transformed_sales_data.csv', index=False)

# End timing
end_time = time.time()

# Calculate and print the elapsed time
elapsed_time = end_time - start_time
print(f"Data extraction and transformation took {elapsed_time:.2f} seconds.")
```

## Exercise 3: Stress Testing, Edge Cases & Failure Mitigation

### Reproducing Failure Modes

To ensure robustness, we will test our pipeline under different scenarios, such as network failures or invalid data formats.

#### Stress Testing Code

```python
import requests
import pandas as pd
import time

def fetch_data_with_retries(api_url, retries=3, backoff_factor=0.3):
    for attempt in range(retries):
        try:
            response = requests.get(api_url)
            response.raise_for_status()  # Raises an HTTPError for bad responses
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            time.sleep(backoff_factor * (2 ** attempt))
    raise Exception("All retries failed")

# Fetch data with retries
data = fetch_data_with_retries(API_URL)

# Convert JSON data to a DataFrame
df = pd.DataFrame(data)

# Data transformation: Adding a new column for price category
df['PriceCategory'] = df['price'].apply(categorize_price)

# Save the transformed data to a CSV file
df.to_csv('transformed_sales_data.csv', index=False)

print("Data extraction and transformation complete with retries. CSV file saved.")
```

### Testing Edge Cases

We will test the pipeline with edge cases such as empty data responses or missing fields.

#### Edge Case Testing Code

```python
def transform_data(data):
    if not data:
        print("No data received.")
        return pd.DataFrame()
    
    df = pd.DataFrame(data)
    
    # Check for missing fields
    if 'price' not in df.columns:
        print("Missing 'price' field in data.")
        return df
    
    # Data transformation: Adding a new column for price category
    df['PriceCategory'] = df['price'].apply(categorize_price)
    
    return df

# Fetch data with retries
data = fetch_data_with_retries(API_URL)

# Transform data
df = transform_data(data)

# Save the transformed data to a CSV file
df.to_csv('transformed_sales_data.csv', index=False)

print("Data extraction and transformation complete with edge case handling. CSV file saved.")
```

### Implementing Guardrails or Error Handling

We will implement guardrails to ensure the pipeline handles errors gracefully.

#### Error Handling Code

```python
def safe_transform_data(data):
    try:
        df = pd.DataFrame(data)
        
        # Check for missing fields
        if 'price' not in df.columns:
            raise ValueError("Missing 'price' field in data.")
        
        # Data transformation: Adding a new column for price category
        df['PriceCategory'] = df['price'].apply(categorize_price)
        
        return df
    except Exception as e:
        print(f"Error during data transformation: {e}")
        return pd.DataFrame()

# Fetch data with retries
data = fetch_data_with_retries(API_URL)

# Transform data safely
df = safe_transform_data(data)

# Save the transformed data to a CSV file
df.to_csv('transformed_sales_data.csv', index=False)

print("Data extraction and transformation complete with error handling. CSV file saved.")
```

## Verification Checklist & Quick Reference Cheat Sheet

### Essential Python Methods and Parameters

| Method/Parameter | Description |
|------------------|-------------|
| `requests.get()` | Fetches data from a specified URL. |
| `response.json()` | Converts the JSON response to a Python dictionary. |
| `pd.DataFrame()` | Creates a DataFrame from a dictionary or list of dictionaries. |
| `df.to_csv()` | Saves the DataFrame to a CSV file. |
| `time.time()` | Returns the current time in seconds since the epoch. |
| `time.sleep()` | Suspends execution for a given number of seconds. |
| `try-except` | Used for exception handling in Python. |

### Verification Flags

| Flag | Description |
|------|-------------|
| `-v` | Verbose mode for detailed output. |
| `-t` | Test mode for running specific tests. |
| `-r` | Retry mode for handling network failures. |

This lab provides a comprehensive guide to building a data visualization dashboard using Tableau, focusing on data extraction, transformation, and visualization. By following the steps and using the provided code snippets, you will be able to create an interactive and insightful dashboard.
