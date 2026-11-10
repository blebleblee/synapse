# Hands-On Operational Lab: Logic
## Objective & Lab Prerequisites

### Objective
This lab aims to provide a comprehensive understanding of logic and its applications in formal sciences. You will explore logical operations, build a simple logical system, inject faults, and debug issues. By the end of this lab, you will have hands-on experience with logical reasoning, system diagnostics, and fault analysis.

### Prerequisites
- Basic understanding of logic and formal reasoning.
- Familiarity with terminal commands and scripting.
- Python installed on your system (version 3.6 or higher).
- LaTeX installed for generating reports (optional).

## Exercise 1: Exploration, Diagnostics & System State Inspection

### Task 1: Install Required Libraries
First, install the `sympy` library, which will be used for symbolic mathematics and logic operations.

```bash
pip install sympy
```

**Expected Output:**
```
Collecting sympy
  Downloading sympy-1.10.1-py3-none-any.whl (6.5 MB)
     |████████████████████████████████| 6.5 MB 1.2 MB/s 
Installing collected packages: sympy
Successfully installed sympy-1.10.1
```

### Task 2: Write a Simple Logic Script
Create a Python script named `logic_exploration.py` to explore basic logical operations.

```python
# logic_exploration.py
from sympy import symbols, And, Or, Not, Implies, satisfiable

# Define symbols
p, q = symbols('p q')

# Define logical expressions
expr1 = And(p, q)
expr2 = Or(p, q)
expr3 = Not(p)
expr4 = Implies(p, q)

# Print truth tables
print("Truth table for And(p, q):")
print(satisfiable(expr1, all_models=True))

print("\nTruth table for Or(p, q):")
print(satisfiable(expr2, all_models=True))

print("\nTruth table for Not(p):")
print(satisfiable(expr3, all_models=True))

print("\nTruth table for Implies(p, q):")
print(satisfiable(expr4, all_models=True))
```

### Task 3: Run the Script
Execute the script in the terminal.

```bash
python logic_exploration.py
```

**Expected Output:**
```
Truth table for And(p, q):
[{p: True, q: True}]

Truth table for Or(p, q):
[{p: False, q: True}, {p: True, q: False}, {p: True, q: True}]

Truth table for Not(p):
[{p: False}]

Truth table for Implies(p, q):
[{p: False, q: False}, {p: False, q: True}, {p: True, q: True}]
```

### Task 4: Inspect System State
Check the installed Python version and list installed packages to ensure the environment is correctly set up.

```bash
python --version
pip list
```

**Expected Output:**
```
Python 3.9.7
Package    Version
---------- -------
pip        21.2.4
setuptools 58.0.4
sympy      1.10.1
```

## Exercise 2: Building, Configuring & Deploying a Production Scenario

### Task 1: Define a Complex Logical System
Create a Python script named `complex_logic_system.py` to define a more complex logical system.

```python
# complex_logic_system.py
from sympy import symbols, And, Or, Not, Implies, satisfiable

# Define symbols
p, q, r = symbols('p q r')

# Define logical expressions
expr1 = And(p, q, r)
expr2 = Or(p, q, r)
expr3 = Not(p)
expr4 = Implies(p, q)
expr5 = Implies(q, r)

# Print truth tables
print("Truth table for And(p, q, r):")
print(satisfiable(expr1, all_models=True))

print("\nTruth table for Or(p, q, r):")
print(satisfiable(expr2, all_models=True))

print("\nTruth table for Not(p):")
print(satisfiable(expr3, all_models=True))

print("\nTruth table for Implies(p, q):")
print(satisfiable(expr4, all_models=True))

print("\nTruth table for Implies(q, r):")
print(satisfiable(expr5, all_models=True))
```

### Task 2: Run the Script
Execute the script in the terminal.

```bash
python complex_logic_system.py
```

**Expected Output:**
```
Truth table for And(p, q, r):
[{p: True, q: True, r: True}]

Truth table for Or(p, q, r):
[{p: False, q: False, r: True}, {p: False, q: True, r: False}, {p: False, q: True, r: True}, {p: False, q: False, r: False}, {p: True, q: False, r: False}, {p: True, q: False, r: True}, {p: True, q: True, r: False}, {p: True, q: True, r: True}]

Truth table for Not(p):
[{p: False}]

Truth table for Implies(p, q):
[{p: False, q: False}, {p: False, q: True}, {p: True, q: True}]

Truth table for Implies(q, r):
[{q: False, r: False}, {q: False, r: True}, {q: True, r: True}]
```

### Task 3: Deploy the System
Deploy the system by creating a simple web interface using Flask to display the truth tables.

```bash
pip install flask
```

**Expected Output:**
```
Collecting flask
  Downloading Flask-2.0.1-py3-none-any.whl (94 kB)
     |████████████████████████████████| 94 kB 1.3 MB/s 
Collecting itsdangerous>=2.0.1
  Downloading itsdangerous-2.0.1-py3-none-any.whl (18 kB)
Collecting click>=7.1.2
  Downloading click-8.0.1-py3-none-any.whl (97 kB)
     |████████████████████████████████| 97 kB 1.4 MB/s 
Collecting Jinja2>=3.0.1
  Downloading Jinja2-3.0.1-py3-none-any.whl (133 kB)
     |████████████████████████████████| 133 kB 1.4 MB/s 
Collecting Werkzeug>=2.0.1
  Downloading Werkzeug-2.0.1-py3-none-any.whl (289 kB)
     |████████████████████████████████| 289 kB 1.4 MB/s 
Collecting MarkupSafe>=2.0
  Downloading MarkupSafe-2.0.1-cp39-cp39-manylinux2010_x86_64.whl (18 kB)
Installing collected packages: MarkupSafe, Jinja2, itsdangerous, click, Werkzeug, flask
Successfully installed Jinja2-3.0.1 MarkupSafe-2.0.1 Werkzeug-2.0.1 click-8.0.1 flask-2.0.1 itsdangerous-2.0.1
```

Create a Flask application named `app.py`.

```python
# app.py
from flask import Flask, render_template_string
from sympy import symbols, And, Or, Not, Implies, satisfiable

app = Flask(__name__)

@app.route('/')
def index():
    p, q, r = symbols('p q r')
    expr1 = And(p, q, r)
    expr2 = Or(p, q, r)
    expr3 = Not(p)
    expr4 = Implies(p, q)
    expr5 = Implies(q, r)
    
    truth_tables = {
        "And(p, q, r)": list(satisfiable(expr1, all_models=True)),
        "Or(p, q, r)": list(satisfiable(expr2, all_models=True)),
        "Not(p)": list(satisfiable(expr3, all_models=True)),
        "Implies(p, q)": list(satisfiable(expr4, all_models=True)),
        "Implies(q, r)": list(satisfiable(expr5, all_models=True))
    }
    
    html = "<h1>Truth Tables</h1>"
    for expr, table in truth_tables.items():
        html += f"<h2>{expr}</h2><ul>"
        for model in table:
            html += f"<li>{model}</li>"
        html += "</ul>"
    
    return render_template_string(html)

if __name__ == '__main__':
    app.run(debug=True)
```

Run the Flask application.

```bash
python app.py
```

**Expected Output:**
```
 * Serving Flask app "app" (lazy loading)
 * Environment: production
   WARNING: This is a development server. Do not use it in a production deployment.
   Use a production WSGI server instead.
 * Debug mode: on
 * Running on http://127.0.0.1:5000/ (Press CTRL+C to quit)
 * Restarting with stat
 * Debugger is active!
 * Debugger PIN: 123-456-789
```

Visit `http://127.0.0.1:5000/` in your web browser to see the truth tables.

## Exercise 3: Fault Injection, Failure Analysis & Debugging

### Task 1: Introduce a Fault
Introduce a fault in the `complex_logic_system.py` script by changing the logical expression `expr1` to `And(p, q, Not(r))`.

```python
# complex_logic_system.py
from sympy import symbols, And, Or, Not, Implies, satisfiable

# Define symbols
p, q, r = symbols('p q r')

# Define logical expressions
expr1 = And(p, q, Not(r))  # Fault introduced here
expr2 = Or(p, q, r)
expr3 = Not(p)
expr4 = Implies(p, q)
expr5 = Implies(q, r)

# Print truth tables
print("Truth table for And(p, q, Not(r)):")
print(satisfiable(expr1, all_models=True))

print("\nTruth table for Or(p, q, r):")
print(satisfiable(expr2, all_models=True))

print("\nTruth table for Not(p):")
print(satisfiable(expr3, all_models=True))

print("\nTruth table for Implies(p, q):")
print(satisfiable(expr4, all_models=True))

print("\nTruth table for Implies(q, r):")
print(satisfiable(expr5, all_models=True))
```

### Task 2: Run the Faulty Script
Execute the faulty script in the terminal.

```bash
python complex_logic_system.py
```

**Expected Output:**
```
Truth table for And(p, q, Not(r)):
[{p: True, q: True, r: False}]

Truth table for Or(p, q, r):
[{p: False, q: False, r: True}, {p: False, q: True, r: False}, {p: False, q: True, r: True}, {p: False, q: False, r: False}, {p: True, q: False, r: False}, {p: True, q: False, r: True}, {p: True, q: True, r: False}, {p: True, q: True, r: True}]

Truth table for Not(p):
[{p: False}]

Truth table for Implies(p, q):
[{p: False, q: False}, {p: False, q: True}, {p: True, q: True}]

Truth table for Implies(q, r):
[{q: False, r: False}, {q: False, r: True}, {q: True, r: True}]
```

### Task 3: Diagnose the Fault
Identify the fault by comparing the expected output with the actual output. The fault is in the expression `And(p, q, Not(r))`, which should be `And(p, q, r)`.

### Task 4: Fix the Fault
Revert the change in `complex_logic_system.py` to fix the fault.

```python
# complex_logic_system.py
from sympy import symbols, And, Or, Not, Implies, satisfiable

# Define symbols
p, q, r = symbols('p q r')

# Define logical expressions
expr1 = And(p, q, r)  # Fault fixed here
expr2 = Or(p, q, r)
expr3 = Not(p)
expr4 = Implies(p, q)
expr5 = Implies(q, r)

# Print truth tables
print("Truth table for And(p, q, r):")
print(satisfiable(expr1, all_models=True))

print("\nTruth table for Or(p, q, r):")
print(satisfiable(expr2, all_models=True))

print("\nTruth table for Not(p):")
print(satisfiable(expr3, all_models=True))

print("\nTruth table for Implies(p, q):")
print(satisfiable(expr4, all_models=True))

print("\nTruth table for Implies(q, r):")
print(satisfiable(expr5, all_models=True))
```

### Task 5: Re-run the Fixed Script
Execute the fixed script in the terminal.

```bash
python complex_logic_system.py
```

**Expected Output:**
```
Truth table for And(p, q, r):
[{p: True, q: True, r: True}]

Truth table for Or(p, q, r):
[{p: False, q: False, r: True}, {p: False, q: True, r: False}, {p: False, q: True, r: True}, {p: False, q: False, r: False}, {p: True, q: False, r: False}, {p: True, q: False, r: True}, {p: True, q: True, r: False}, {p: True, q: True, r: True}]

Truth table for Not(p):
[{p: False}]

Truth table for Implies(p, q):
[{p: False, q: False}, {p: False, q: True}, {p: True, q: True}]

Truth table for Implies(q, r):
[{q: False, r: False}, {q: False, r: True}, {q: True, r: True}]
```

## Challenge Lab: Independent Advanced Scenarios

### Task 1: Create a Logical Puzzle
Create a logical puzzle using the `sympy` library. For example, solve the puzzle: "If it is raining, then the streets are wet. If the streets are wet, then the cars are slippery. If the cars are slippery, then the accidents occur. If it is not raining, then the streets are not wet. Is it possible for accidents to occur without rain?"

```python
# logical_puzzle.py
from sympy import symbols, And, Or, Not, Implies, satisfiable

# Define symbols
rain, wet, slippery, accident = symbols('rain wet slippery accident')

# Define logical expressions
expr1 = Implies(rain, wet)
expr2 = Implies(wet, slippery)
expr3 = Implies(slippery, accident)
expr4 = Implies(Not(rain), Not(wet))

# Combine all expressions
combined_expr = And(expr1, expr2, expr3, expr4)

# Check if accidents can occur without rain
result = satisfiable(And(combined_expr, accident, Not(rain)), all_models=True)

# Print result
if list(result):
    print("It is possible for accidents to occur without rain.")
else:
    print("It is not possible for accidents to occur without rain.")
```

### Task 2: Run the Puzzle Script
Execute the puzzle script in the terminal.

```bash
python logical_puzzle.py
```

**Expected Output:**
```
It is not possible for accidents to occur without rain.
```

### Task 3: Document the Solution
Document the solution in a LaTeX report.

```latex
\documentclass{article}
\usepackage{amsmath}

\begin{document}

\title{Logical Puzzle Solution}
\author{Your Name}
\date{\today}
\maketitle

\section{Problem Statement}
Solve the puzzle: "If it is raining, then the streets are wet. If the streets are wet, then the cars are slippery. If the cars are slippery, then the accidents occur. If it is not raining, then the streets are not wet. Is it possible for accidents to occur without rain?"

\section{Logical Expressions}
\begin{align*}
\text{expr1} &= \text{Implies}(rain, wet) \\
\text{expr2} &= \text{Implies}(wet, slippery) \\
\text{expr3} &= \text{Implies}(slippery, accident) \\
\text{expr4} &= \text{Implies}(\neg rain, \neg wet)
\end{align*}

\section{Solution}
\begin{align*}
\text{combined\_expr} &= \text{And}(\text{expr1}, \text{expr2}, \text{expr3}, \text{expr4}) \\
\text{result} &= \text{satisfiable}(\text{And}(\text{combined\_expr}, accident, \neg rain), \text{all\_models=True})
\end{align*}

\textbf{Conclusion:} It is not possible for accidents to occur without rain.

\end{document}
```

Compile the LaTeX document using `pdflatex`.

```bash
pdflatex logical_puzzle.tex
```

**Expected Output:**
A PDF file named `logical_puzzle.pdf` will be generated.

## Conclusion
This lab provided hands-on experience with logic, system diagnostics, and fault analysis. You explored logical operations, built a simple logical system, injected faults, and debugged issues. By completing this lab, you have gained a deeper understanding of logic and its applications in formal sciences.
