# Operational Verification Labs: 03 Sql Analytics And Window Functions

## Objective & Environment Setup

### Objective
The objective of this lab is to gain hands-on experience with SQL analytics and window functions. We will implement a pipeline that processes and analyzes data using SQL queries, focusing on window functions to perform complex calculations over a set of table rows. The lab will cover data processing, hyperparameter tuning, stress testing, and failure mitigation.

### Environment Setup
Ensure you have a Python 3.11+ environment set up. You will need the following packages:

- `pandas` for data manipulation.
- `sqlalchemy` for SQL database interaction.
- `sqlite3` for an in-memory SQLite database.
- `numpy` for numerical operations.
- `matplotlib` for plotting results.

You can install these packages using pip:

```bash
pip install pandas sqlalchemy numpy matplotlib
```

## Exercise 1: Hands-On Implementation & Pipeline Execution

### Implementation Overview
In this exercise, we will create a pipeline that processes a dataset using SQL queries with window functions. We will use an in-memory SQLite database for simplicity.

### Complete, Runnable Python Script

```python
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sqlalchemy import create_engine, text

# Create an in-memory SQLite database
engine = create_engine('sqlite:///:memory:')

# Sample data creation
data = {
    'department': ['Sales', 'Sales', 'Sales', 'Marketing', 'Marketing', 'Marketing', 'Engineering', 'Engineering', 'Engineering'],
    'employee': ['Alice', 'Bob', 'Charlie', 'David', 'Eve', 'Frank', 'Grace', 'Hannah', 'Ian'],
    'salary': [50000, 54000, 52000, 48000, 49000, 51000, 60000, 62000, 61000]
}

# Create a DataFrame
df = pd.DataFrame(data)

# Load data into the SQLite database
df.to_sql('employees', con=engine, index=False, if_exists='replace')

# Define a SQL query with window functions
query = text("""
SELECT 
    department,
    employee,
    salary,
    AVG(salary) OVER (PARTITION BY department) AS avg_salary,
    MAX(salary) OVER (PARTITION BY department) AS max_salary,
    ROW_NUMBER() OVER (PARTITION BY department ORDER BY salary DESC) AS salary_rank
FROM 
    employees
ORDER BY 
    department, salary_rank
""")

# Execute the query and fetch results
with engine.connect() as connection:
    result = connection.execute(query)
    result_df = pd.DataFrame(result.fetchall(), columns=result.keys())

# Display the results
print("SQL Query Results with Window Functions:")
print(result_df)

# Plotting the results
plt.figure(figsize=(12, 6))
for dept, group in result_df.groupby('department'):
    plt.plot(group['salary_rank'], group['salary'], marker='o', label=dept)

plt.title('Employee Salaries by Department')
plt.xlabel('Salary Rank')
plt.ylabel('Salary')
plt.legend()
plt.grid(True)
plt.show()
```

## Exercise 2: Hyperparameter Tuning & Empirical Benchmarking

### Benchmarking Overview
In this exercise, we will benchmark the performance of our SQL queries with different window functions and configurations. We will measure the execution time and analyze the results.

### Real Benchmarking Code

```python
import timeit

# Define a function to execute the query
def execute_query():
    with engine.connect() as connection:
        connection.execute(query)

# Measure the execution time
execution_time = timeit.timeit(execute_query, number=100)
print(f"Average execution time over 100 runs: {execution_time / 100:.6f} seconds")

# Additional benchmarking for different window functions
queries = {
    'avg_salary': text("""
        SELECT 
            department,
            employee,
            salary,
            AVG(salary) OVER (PARTITION BY department) AS avg_salary
        FROM 
            employees
    """),
    'max_salary': text("""
        SELECT 
            department,
            employee,
            salary,
            MAX(salary) OVER (PARTITION BY department) AS max_salary
        FROM 
            employees
    """),
    'salary_rank': text("""
        SELECT 
            department,
            employee,
            salary,
            ROW_NUMBER() OVER (PARTITION BY department ORDER BY salary DESC) AS salary_rank
        FROM 
            employees
    """)
}

# Benchmark each query
for name, q in queries.items():
    execution_time = timeit.timeit(lambda: engine.execute(q), number=100)
    print(f"Average execution time for {name} over 100 runs: {execution_time / 100:.6f} seconds")
```

## Exercise 3: Stress Testing, Edge Cases & Failure Mitigation

### Stress Testing Overview
In this exercise, we will test the robustness of our SQL queries under stress conditions and handle edge cases.

### Reproducing Failure Modes

```python
# Introduce a failure mode: missing data
data_with_missing = data.copy()
data_with_missing['salary'][1] = None  # Set Bob's salary to None

# Create a DataFrame with missing data
df_missing = pd.DataFrame(data_with_missing)

# Load data into the SQLite database
df_missing.to_sql('employees_missing', con=engine, index=False, if_exists='replace')

# Define a query to handle missing data
query_missing = text("""
SELECT 
    department,
    employee,
    salary,
    AVG(salary) OVER (PARTITION BY department) AS avg_salary,
    MAX(salary) OVER (PARTITION BY department) AS max_salary,
    ROW_NUMBER() OVER (PARTITION BY department ORDER BY salary DESC) AS salary_rank
FROM 
    employees_missing
ORDER BY 
    department, salary_rank
""")

# Execute the query and fetch results
with engine.connect() as connection:
    result_missing = connection.execute(query_missing)
    result_df_missing = pd.DataFrame(result_missing.fetchall(), columns=result_missing.keys())

# Display the results
print("SQL Query Results with Missing Data:")
print(result_df_missing)
```

### Testing Edge Cases

```python
# Edge case: single department
data_single_dept = {
    'department': ['Sales', 'Sales', 'Sales'],
    'employee': ['Alice', 'Bob', 'Charlie'],
    'salary': [50000, 54000, 52000]
}

# Create a DataFrame with a single department
df_single_dept = pd.DataFrame(data_single_dept)

# Load data into the SQLite database
df_single_dept.to_sql('employees_single_dept', con=engine, index=False, if_exists='replace')

# Define a query for a single department
query_single_dept = text("""
SELECT 
    department,
    employee,
    salary,
    AVG(salary) OVER (PARTITION BY department) AS avg_salary,
    MAX(salary) OVER (PARTITION BY department) AS max_salary,
    ROW_NUMBER() OVER (PARTITION BY department ORDER BY salary DESC) AS salary_rank
FROM 
    employees_single_dept
ORDER BY 
    department, salary_rank
""")

# Execute the query and fetch results
with engine.connect() as connection:
    result_single_dept = connection.execute(query_single_dept)
    result_df_single_dept = pd.DataFrame(result_single_dept.fetchall(), columns=result_single_dept.keys())

# Display the results
print("SQL Query Results for Single Department:")
print(result_df_single_dept)
```

### Implementing Guardrails or Error Handling

```python
# Implement error handling for missing data
def safe_execute_query(query, table_name):
    try:
        with engine.connect() as connection:
            result = connection.execute(query)
            result_df = pd.DataFrame(result.fetchall(), columns=result.keys())
        return result_df
    except Exception as e:
        print(f"Error executing query on {table_name}: {e}")
        return None

# Execute the query with error handling
result_df_safe = safe_execute_query(query_missing, 'employees_missing')
if result_df_safe is not None:
    print("SQL Query Results with Safe Execution:")
    print(result_df_safe)
```

## Verification Checklist & Quick Reference Cheat Sheet

### Essential Python Methods and Parameters

| Method/Parameter | Description |
|------------------|-------------|
| `pd.DataFrame`   | Create a DataFrame from a dictionary. |
| `to_sql`         | Load DataFrame into a SQL database table. |
| `create_engine`  | Create a SQLAlchemy engine for database connection. |
| `text`           | Create a SQL text query. |
| `execute`        | Execute a SQL query. |
| `fetchall`       | Fetch all rows from the query result. |
| `timeit.timeit`  | Measure the execution time of a function. |
| `plt.plot`       | Plot data using matplotlib. |
| `plt.title`      | Set the title of the plot. |
| `plt.xlabel`     | Set the x-axis label of the plot. |
| `plt.ylabel`     | Set the y-axis label of the plot. |
| `plt.legend`     | Add a legend to the plot. |
| `plt.grid`       | Add a grid to the plot. |
| `plt.show`       | Display the plot. |

### Verification Flags

| Flag/Parameter | Description |
|----------------|-------------|
| `if_exists='replace'` | Replace the table if it already exists. |
| `number=100`   | Number of times to execute the function for benchmarking. |

This lab provides a comprehensive hands-on experience with SQL analytics and window functions, covering implementation, benchmarking, stress testing, and error handling.
