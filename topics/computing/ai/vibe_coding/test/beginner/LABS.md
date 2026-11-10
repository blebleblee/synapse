# Beginner Hands-On Lab: Test
## Objective & Prerequisites
### Objective
The objective of this lab is to verify that your computing environment is properly set up and to execute your first commands. This will help you get familiar with the basic tools and commands you will be using throughout your learning journey.

### Prerequisites
- A computer with an internet connection.
- Access to a terminal or command prompt (Command Prompt on Windows, Terminal on macOS/Linux).
- Basic understanding of using a terminal or command prompt.

## Exercise 1: Environment Setup & Sanity Check (Exact commands to verify tools)
In this exercise, we will verify that you have the necessary tools installed on your system. We will check for the presence of `git`, `python`, and `pip`.

### Step-by-Step Instructions
1. **Open your terminal or command prompt.**
2. **Check if `git` is installed:**
   ```bash
   git --version
   ```
   **Expected Output:** A version number, e.g., `git version 2.31.1`.

3. **Check if `python` is installed:**
   ```bash
   python --version
   ```
   **Expected Output:** A version number, e.g., `Python 3.9.7`.

   If `python` is not found, try:
   ```bash
   python3 --version
   ```
   **Expected Output:** A version number, e.g., `Python 3.9.7`.

4. **Check if `pip` is installed:**
   ```bash
   pip --version
   ```
   **Expected Output:** A version number, e.g., `pip 21.2.4 from /usr/local/lib/python3.9/site-packages/pip (python 3.9)`.

   If `pip` is not found, try:
   ```bash
   pip3 --version
   ```
   **Expected Output:** A version number, e.g., `pip 21.2.4 from /usr/local/lib/python3.9/site-packages/pip (python 3.9)`.

## Exercise 2: Your First Working Experiment (Step-by-step guided instructions with expected outputs)
In this exercise, we will write a simple Python script and run it to ensure everything is working correctly.

### Step-by-Step Instructions
1. **Create a new directory for your project:**
   ```bash
   mkdir ai_vibe_coding_lab
   cd ai_vibe_coding_lab
   ```

2. **Create a new Python file named `hello.py`:**
   ```bash
   touch hello.py
   ```
   or, if you are using Windows Command Prompt:
   ```cmd
   type nul > hello.py
   ```

3. **Open `hello.py` in a text editor and add the following code:**
   ```python
   print("Hello, AI Vibe Coding!")
   ```

4. **Save the file and return to your terminal or command prompt.**

5. **Run the Python script:**
   ```bash
   python hello.py
   ```
   or, if you are using Python 3 specifically:
   ```bash
   python3 hello.py
   ```

   **Expected Output:**
   ```
   Hello, AI Vibe Coding!
   ```

## Exercise 3: Inspecting Basic State (Reading logs or simple outputs)
In this exercise, we will inspect the output of the Python script to ensure it ran correctly.

### Step-by-Step Instructions
1. **Check the output of the `hello.py` script again:**
   ```bash
   python hello.py
   ```
   or, if you are using Python 3 specifically:
   ```bash
   python3 hello.py
   ```

2. **Verify that the output matches the expected output:**
   ```
   Hello, AI Vibe Coding!
   ```

## Challenge Exercise (Simple self-test for beginners)
In this challenge exercise, you will modify the `hello.py` script to print a different message.

### Step-by-Step Instructions
1. **Open `hello.py` in a text editor and modify the code to print a different message, e.g., "Welcome to the AI Vibe Coding Lab!".**

2. **Save the file and return to your terminal or command prompt.**

3. **Run the modified Python script:**
   ```bash
   python hello.py
   ```
   or, if you are using Python 3 specifically:
   ```bash
   python3 hello.py
   ```

   **Expected Output:**
   ```
   Welcome to the AI Vibe Coding Lab!
   ```

Congratulations! You have completed the Beginner Hands-On Lab: Test. You have verified your environment, written your first Python script, and inspected the output.
