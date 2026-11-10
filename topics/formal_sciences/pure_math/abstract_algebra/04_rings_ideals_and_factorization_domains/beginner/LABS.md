# Beginner Hands-On Lab: Abstract Algebra 04 Rings Ideals And Factorization Domains

## Objective & Prerequisites
The objective of this lab is to set up your environment for working with abstract algebra concepts such as rings, ideals, and factorization domains. We will use Python with the SymPy library, which is a powerful tool for symbolic mathematics. Ensure you have Python installed on your system. This lab assumes you have basic knowledge of Python and are familiar with command-line operations.

## Exercise 1: Environment Setup & Sanity Check (Exact commands to verify tools)
1. **Install Python**: If Python is not installed, download and install it from [python.org](https://www.python.org/downloads/).
2. **Install SymPy**: Open your terminal or command prompt and run the following command to install SymPy:
   ```bash
   pip install sympy
   ```
3. **Verify Installation**: Run the following command to verify that SymPy is installed correctly:
   ```bash
   python -c "import sympy; print(sympy.__version__)"
   ```
   You should see the version number of SymPy printed to the console.

## Exercise 2: Your First Working Experiment (Step-by-step guided instructions with expected outputs)
1. **Create a Python Script**: Open your favorite text editor or IDE and create a new file named `rings_ideals.py`.
2. **Write the Script**: Copy and paste the following code into `rings_ideals.py`:
   ```python
   from sympy import symbols, Eq, solve, ZZ, Poly, gcd

   # Define a polynomial ring over the integers
   x = symbols('x')
   R = ZZ[x]

   # Define two polynomials
   f = Poly(x**2 - 3*x + 2, x, domain='ZZ')
   g = Poly(x - 1, x, domain='ZZ')

   # Compute the greatest common divisor (gcd) of f and g
   gcd_fg = gcd(f, g)

   # Print the gcd
   print(f"The gcd of {f} and {g} is {gcd_fg}")
   ```
3. **Run the Script**: Save the file and run it using the following command in your terminal or command prompt:
   ```bash
   python rings_ideals.py
   ```
4. **Expected Output**:
   ```
   The gcd of Poly(x**2 - 3*x + 2, x, domain='ZZ') and Poly(x - 1, x, domain='ZZ') is Poly(x - 1, x, domain='ZZ')
   ```

## Exercise 3: Inspecting Basic State (Reading logs or simple outputs)
1. **Inspect the Output**: The output from Exercise 2 should confirm that the greatest common divisor of the polynomials \(x^2 - 3x + 2\) and \(x - 1\) is \(x - 1\). This demonstrates the basic functionality of SymPy in handling polynomial rings and computing gcds.

## Challenge Exercise (Simple self-test for beginners)
1. **Modify the Script**: Change the polynomials \(f\) and \(g\) in `rings_ideals.py` to \(f = x^3 - 2x^2 - x + 2\) and \(g = x - 2\).
2. **Run the Modified Script**: Execute the script again and observe the output.
3. **Expected Output**:
   ```
   The gcd of Poly(x**3 - 2*x**2 - x + 2, x, domain='ZZ') and Poly(x - 2, x, domain='ZZ') is Poly(x - 2, x, domain='ZZ')
   ```

This challenge exercise tests your ability to modify and run a script, and to interpret the output in the context of polynomial rings and gcds.
