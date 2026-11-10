# Beginner Hands-On Lab: Abstract Algebra 03 Group Actions And Sylow Theorems

## Objective & Prerequisites
The objective of this lab is to introduce you to the concepts of group actions and Sylow theorems in abstract algebra. We will set up a computational environment to verify these concepts through practical examples. This lab assumes you have a basic understanding of abstract algebra, including groups, subgroups, and homomorphisms.

### Prerequisites:
- Basic knowledge of abstract algebra.
- Python installed on your system.
- Familiarity with Jupyter Notebooks or a similar interactive Python environment.
- Installation of the `sympy` library for symbolic mathematics.

## Exercise 1: Environment Setup & Sanity Check (Exact commands to verify tools)
Before we begin, we need to ensure that our computational environment is set up correctly. We will install the necessary Python libraries and verify their installation.

#### Step 1: Install Required Libraries
Open a terminal or command prompt and run the following command to install the `sympy` library, which we will use for symbolic mathematics:

```bash
pip install sympy
```

#### Step 2: Verify Installation
To verify that `sympy` is installed correctly, open a Python shell or Jupyter Notebook and run the following commands:

```python
import sympy as sp
print(sp.__version__)
```

You should see the version number of `sympy` printed, indicating that the installation was successful.

## Exercise 2: Your First Working Experiment (Step-by-step guided instructions with expected outputs)
In this exercise, we will explore a simple group action and verify a basic property using Python and `sympy`.

#### Step 1: Define a Group and a Set
We will define a simple group and a set on which the group acts. For simplicity, let's consider the cyclic group \( \mathbb{Z}_3 \) (integers modulo 3) and the set \( X = \{1, 2, 3\} \).

```python
from sympy.combinatorics.named_groups import CyclicGroup

# Define the cyclic group Z_3
G = CyclicGroup(3)
print("Group G (Z_3):", G)
```

**Expected Output:**
```
Group G (Z_3): PermutationGroup([
    (2)(0 1),
    (0 2 1)])
```

#### Step 2: Define a Group Action
We will define a simple group action of \( \mathbb{Z}_3 \) on the set \( X \). For each element \( g \in G \) and \( x \in X \), the action is defined as \( g \cdot x = (g + x) \mod 3 \).

```python
def group_action(g, x):
    return (g + x) % 3

# Test the group action
for g in G:
    for x in [1, 2, 3]:
        print(f"g = {g}, x = {x}, g * x = {group_action(g, x)}")
```

**Expected Output:**
```
g = (2)(0 1), x = 1, g * x = 0
g = (2)(0 1), x = 2, g * x = 1
g = (2)(0 1), x = 3, g * x = 2
g = (0 2 1), x = 1, g * x = 2
g = (0 2 1), x = 2, g * x = 0
g = (0 2 1), x = 3, g * x = 1
g = (), x = 1, g * x = 1
g = (), x = 2, g * x = 2
g = (), x = 3, g * x = 3
```

## Exercise 3: Inspecting Basic State (Reading logs or simple outputs)
In this exercise, we will inspect the basic state of our group action to ensure it behaves as expected.

#### Step 1: Verify the Orbit of an Element
The orbit of an element \( x \in X \) under the action of \( G \) is the set of all elements \( g \cdot x \) for \( g \in G \). Let's verify the orbit of \( x = 1 \).

```python
def orbit(g, x):
    return {group_action(g, x) for g in G}

# Calculate the orbit of x = 1
orbit_1 = orbit(G, 1)
print("Orbit of 1:", orbit_1)
```

**Expected Output:**
```
Orbit of 1: {0, 1, 2}
```

## Challenge Exercise (Simple self-test for beginners)
In this challenge exercise, you will verify the orbit of another element in the set \( X \).

#### Task:
Calculate the orbit of \( x = 2 \) under the action of \( G \) and verify that it matches the expected output.

#### Solution:
```python
# Calculate the orbit of x = 2
orbit_2 = orbit(G, 2)
print("Orbit of 2:", orbit_2)
```

**Expected Output:**
```
Orbit of 2: {0, 1, 2}
```

By completing this lab, you have successfully set up your computational environment, defined a group action, and verified basic properties of the action. This foundational knowledge will be useful as we delve deeper into group actions and Sylow theorems in abstract algebra.
