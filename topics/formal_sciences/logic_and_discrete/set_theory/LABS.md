# Hands-On Operational Lab: Set Theory
## Objective & Lab Prerequisites

### Objective
This lab aims to provide a comprehensive understanding of set theory through practical, hands-on exercises. You will explore basic set operations, build a production scenario using Python, and perform fault injection and debugging to diagnose failures.

### Prerequisites
- Basic knowledge of Python programming.
- Familiarity with terminal commands.
- Python installed on your system (preferably Python 3.8 or later).

## Exercise 1: Exploration, Diagnostics & System State Inspection

### Task
Implement basic set operations in Python and inspect the system state to understand how sets behave.

### Steps
1. Open your terminal.
2. Create a new Python script named `set_operations.py`:
   ```bash
   touch set_operations.py
   ```
3. Open `set_operations.py` in your preferred text editor and add the following code:
   ```python
   # Define two sets
   set_a = {1, 2, 3, 4}
   set_b = {3, 4, 5, 6}

   # Union of sets
   union_set = set_a.union(set_b)
   print("Union of set_a and set_b:", union_set)

   # Intersection of sets
   intersection_set = set_a.intersection(set_b)
   print("Intersection of set_a and set_b:", intersection_set)

   # Difference of sets
   difference_set = set_a.difference(set_b)
   print("Difference of set_a and set_b:", difference_set)

   # Symmetric difference of sets
   symmetric_difference_set = set_a.symmetric_difference(set_b)
   print("Symmetric difference of set_a and set_b:", symmetric_difference_set)
   ```
4. Run the script:
   ```bash
   python set_operations.py
   ```
5. Inspect the output:
   ```
   Union of set_a and set_b: {1, 2, 3, 4, 5, 6}
   Intersection of set_a and set_b: {3, 4}
   Difference of set_a and set_b: {1, 2}
   Symmetric difference of set_a and set_b: {1, 2, 5, 6}
   ```

## Exercise 2: Building, Configuring & Deploying a Production Scenario

### Task
Build a more complex scenario involving set operations and deploy it as a Python module.

### Steps
1. Create a new directory for your project:
   ```bash
   mkdir set_theory_project
   cd set_theory_project
   ```
2. Create a new Python file named `set_operations_module.py`:
   ```bash
   touch set_operations_module.py
   ```
3. Open `set_operations_module.py` and add the following code:
   ```python
   def union(set_a, set_b):
       return set_a.union(set_b)

   def intersection(set_a, set_b):
       return set_a.intersection(set_b)

   def difference(set_a, set_b):
       return set_a.difference(set_b)

   def symmetric_difference(set_a, set_b):
       return set_a.symmetric_difference(set_b)
   ```
4. Create a new Python script named `main.py`:
   ```bash
   touch main.py
   ```
5. Open `main.py` and add the following code:
   ```python
   from set_operations_module import union, intersection, difference, symmetric_difference

   # Define two sets
   set_a = {1, 2, 3, 4}
   set_b = {3, 4, 5, 6}

   # Perform set operations
   print("Union of set_a and set_b:", union(set_a, set_b))
   print("Intersection of set_a and set_b:", intersection(set_a, set_b))
   print("Difference of set_a and set_b:", difference(set_a, set_b))
   print("Symmetric difference of set_a and set_b:", symmetric_difference(set_a, set_b))
   ```
6. Run the script:
   ```bash
   python main.py
   ```
7. Inspect the output:
   ```
   Union of set_a and set_b: {1, 2, 3, 4, 5, 6}
   Intersection of set_a and set_b: {3, 4}
   Difference of set_a and set_b: {1, 2}
   Symmetric difference of set_a and set_b: {1, 2, 5, 6}
   ```

## Exercise 3: Fault Injection, Failure Analysis & Debugging

### Task
Introduce a fault in the code and debug it to understand the failure.

### Steps
1. Modify `set_operations_module.py` to introduce a fault:
   ```python
   def union(set_a, set_b):
       return set_a.union(set_b)

   def intersection(set_a, set_b):
       return set_a.intersection(set_b)

   def difference(set_a, set_b):
       return set_a.difference(set_b)

   def symmetric_difference(set_a, set_b):
       return set_a.symmetric_difference(set_b) + 1  # Fault: Adding 1 to a set
   ```
2. Run the script again:
   ```bash
   python main.py
   ```
3. Inspect the output and observe the error:
   ```
   Traceback (most recent call last):
     File "main.py", line 10, in <module>
       print("Symmetric difference of set_a and set_b:", symmetric_difference(set_a, set_b))
     File "/path/to/set_theory_project/set_operations_module.py", line 12, in symmetric_difference
       return set_a.symmetric_difference(set_b) + 1
   TypeError: unsupported operand type(s) for +: 'set' and 'int'
   ```
4. Debug the fault by removing the `+ 1` in `set_operations_module.py`:
   ```python
   def symmetric_difference(set_a, set_b):
       return set_a.symmetric_difference(set_b)
   ```
5. Run the script again to verify the fix:
   ```bash
   python main.py
   ```
6. Inspect the output:
   ```
   Union of set_a and set_b: {1, 2, 3, 4, 5, 6}
   Intersection of set_a and set_b: {3, 4}
   Difference of set_a and set_b: {1, 2}
   Symmetric difference of set_a and set_b: {1, 2, 5, 6}
   ```

## Challenge Lab: Independent Advanced Scenarios

### Task
Create a more advanced scenario involving set operations, such as set comprehensions, power sets, or Cartesian products.

### Steps
1. Create a new Python script named `advanced_set_operations.py`:
   ```bash
   touch advanced_set_operations.py
   ```
2. Open `advanced_set_operations.py` and add the following code:
   ```python
   from itertools import product

   # Define a set
   set_a = {1, 2, 3}

   # Set comprehension to create a new set
   set_b = {x * 2 for x in set_a}
   print("Set comprehension result:", set_b)

   # Power set using a function
   def power_set(s):
       return [set(p) for p in product([0, 1], repeat=len(s))]

   power_set_a = power_set(set_a)
   print("Power set of set_a:", power_set_a)

   # Cartesian product of two sets
   set_c = {4, 5}
   cartesian_product = set(product(set_a, set_c))
   print("Cartesian product of set_a and set_c:", cartesian_product)
   ```
3. Run the script:
   ```bash
   python advanced_set_operations.py
   ```
4. Inspect the output:
   ```
   Set comprehension result: {2, 4, 6}
   Power set of set_a: [set(), {1}, {2}, {1, 2}, {3}, {1, 3}, {2, 3}, {1, 2, 3}]
   Cartesian product of set_a and set_c: {(1, 4), (1, 5), (2, 4), (2, 5), (3, 4), (3, 5)}
   ```

### Self-Guided Lab Scenarios
1. **Scenario 1:** Implement a function to find the complement of a set with respect to a universal set.
2. **Scenario 2:** Create a function to find the symmetric difference of more than two sets.
3. **Scenario 3:** Implement a function to find the Cartesian product of more than two sets.

Feel free to explore and extend these scenarios to deepen your understanding of set theory.
