# Beginner Hands-On Lab: Mathematical Logic
## Objective & Prerequisites
### Objective
In this lab, you will set up a basic environment for mathematical logic and execute your first commands.

### Prerequisites
- Familiarity with basic mathematical concepts
- Access to a LaTeX environment (e.g., Overleaf, TeX Live)
- Basic understanding of formal logic notation

## Exercise 1: Environment Setup & Sanity Check

### Step 1: Install LaTeX
If you haven't already, install a LaTeX environment on your system. For this example, we'll use Overleaf.

### Step 2: Create a New Project
- Go to Overleaf and create a new project.
- Name your project (e.g., "Mathematical Logic Lab").

### Step 3: Verify LaTeX Installation
- Open your project in Overleaf.
- In the editor, type the following command to verify LaTeX installation:
```latex
\documentclass{article}
\begin{document}
\section{Hello World}
Hello World!
\end{document}
```
- Click the "Compile" button to see if LaTeX compiles without errors.

## Exercise 2: Your First Working Experiment

### Step 1: Basic Propositional Logic
- In your Overleaf project, create a new section for propositional logic.
- Type the following code to define a basic proposition:
```latex
\documentclass{article}
\begin{document}
\section{Propositional Logic}
Let $p$ be the proposition "It is raining."
\end{document}
```
- Compile the document to see the result.

### Step 2: Logical Operators
- Introduce logical operators (e.g., $\neg$, $\wedge$, $\vee$) using LaTeX notation.
- Type the following code to demonstrate the conjunction of two propositions:
```latex
\documentclass{article}
\begin{document}
\section{Logical Operators}
Let $p$ and $q$ be the propositions "It is raining" and "The grass is wet," respectively.
Then, $p \wedge q$ is the proposition "It is raining and the grass is wet."
\end{document}
```
- Compile the document to see the result.

## Exercise 3: Inspecting Basic State

### Step 1: Reading Logs
- In Overleaf, click on the "Logs" tab to view the compilation logs.
- Look for any errors or warnings that might indicate issues with your LaTeX installation or code.

### Step 2: Simple Outputs
- Observe the output of your code in the "Preview" tab.
- Verify that the logical operators and propositions are displayed correctly.

## Challenge Exercise
### Task
- Define a proposition $p \vee q$ using LaTeX notation.
- Use the `\documentclass` command to create a new document class called "Logic".
- Include a section with the title "Propositional Logic" and the proposition $p \vee q$.

### Hint
- Use the `\newcommand` command to define a new command for the proposition.
- Use the `\section` command to create a new section with the title "Propositional Logic".

### Expected Output
- A new document class called "Logic" with a section titled "Propositional Logic" containing the proposition $p \vee q$.

### Tip
- Don't forget to compile your document after making changes to see the output.
