# Beginner Hands-On Lab: Abstract Algebra 02 Normal Subgroups And Isomorphisms

## Objective & Prerequisites
The objective of this lab is to introduce you to the concepts of normal subgroups and isomorphisms in abstract algebra. We will set up a computational environment to perform basic algebraic operations and verify these concepts through hands-on experimentation. 

### Prerequisites:
- Basic knowledge of abstract algebra, including groups and subgroups.
- Familiarity with Python programming.
- Installation of the SymPy library for symbolic mathematics in Python.

## Exercise 1: Environment Setup & Sanity Check (Exact commands to verify tools)

1. **Install Python**: Ensure Python is installed on your system. You can download it from [python.org](https://www.python.org/downloads/).
2. **Install SymPy**: Open your terminal or command prompt and run the following command to install SymPy:
   ```bash
   pip install sympy
   ```
3. **Verify Installation**: Run the following command to verify that SymPy is installed correctly:
   ```bash
   python -c "import sympy; print(sympy.__version__)"
   ```
   You should see the version number of SymPy printed in the terminal.

## Exercise 2: Your First Working Experiment (Step-by-step guided instructions with expected outputs)

In this exercise, we will define a group and a subgroup, and check if the subgroup is normal.

1. **Open a Python Script**: Create a new Python file named `normal_subgroup_check.py`.
2. **Import SymPy**: Add the following line at the top of your script to import SymPy:
   ```python
   import sympy as sp
   from sympy.combinatorics.named_groups import SymmetricGroup
   from sympy.combinatorics.perm_groups import PermutationGroup
   from sympy.combinatorics.permutations import Permutation
   ```
3. **Define a Group and a Subgroup**: Add the following code to define the symmetric group \( S_3 \) and a subgroup \( H \):
   ```python
   # Define the symmetric group S_3
   S3 = SymmetricGroup(3)

   # Define a subgroup H of S_3
   H = PermutationGroup([Permutation([0, 1, 2]), Permutation([0, 2, 1])])
   ```
4. **Check if the Subgroup is Normal**: Add the following code to check if \( H \) is a normal subgroup of \( S_3 \):
   ```python
   # Check if H is a normal subgroup of S3
   is_normal = H.is_normal(S3)
   print(f"Is H a normal subgroup of S3? {is_normal}")
   ```
5. **Run the Script**: Save the file and run it using the following command in your terminal:
   ```bash
   python normal_subgroup_check.py
   ```
   **Expected Output**:
   ```
   Is H a normal subgroup of S3? False
   ```

## Exercise 3: Inspecting Basic State (Reading logs or simple outputs)

In this exercise, we will inspect the elements of the group and the subgroup to understand why \( H \) is not a normal subgroup of \( S_3 \).

1. **Print Elements of the Group and Subgroup**: Add the following code to print the elements of \( S_3 \) and \( H \):
   ```python
   # Print elements of S3
   print("Elements of S3:")
   for element in S3.generate():
       print(element)

   # Print elements of H
   print("\nElements of H:")
   for element in H.generate():
       print(element)
   ```
2. **Run the Script**: Save the file and run it again using the following command in your terminal:
   ```bash
   python normal_subgroup_check.py
   ```
   **Expected Output**:
   ```
   Is H a normal subgroup of S3? False
   Elements of S3:
   Permutation(2)
   Permutation(0, 1, 2)
   Permutation(0, 2, 1)
   Permutation(1, 2)
   Permutation(0, 1)
   Permutation(0, 2)

   Elements of H:
   Permutation(2)
   Permutation(0, 2, 1)
   ```

## Challenge Exercise (Simple self-test for beginners)

Define another subgroup \( K \) of \( S_3 \) and check if it is a normal subgroup. Use the following code snippet as a guide:

1. **Define Subgroup \( K \)**:
   ```python
   # Define a subgroup K of S3
   K = PermutationGroup([Permutation([0, 1, 2]), Permutation([1, 2, 0]), Permutation([2, 0, 1])])
   ```
2. **Check if \( K \) is Normal**:
   ```python
   # Check if K is a normal subgroup of S3
   is_normal_K = K.is_normal(S3)
   print(f"Is K a normal subgroup of S3? {is_normal_K}")
   ```
3. **Run the Script**: Save the file and run it using the following command in your terminal:
   ```bash
   python normal_subgroup_check.py
   ```
   **Expected Output**:
   ```
   Is H a normal subgroup of S3? False
   Elements of S3:
   Permutation(2)
   Permutation(0, 1, 2)
   Permutation(0, 2, 1)
   Permutation(1, 2)
   Permutation(0, 1)
   Permutation(0, 2)

   Elements of H:
   Permutation(2)
   Permutation(0, 2, 1)

   Is K a normal subgroup of S3? True
   ```
