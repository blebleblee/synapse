# Beginner Hands-On Lab: Proof Theory
## Objective & Prerequisites

In this lab, you will set up a basic proof theory environment and execute your first commands. To begin, ensure you have the following tools installed:

* LaTeX (for typesetting mathematical formulas)
* A proof assistant (e.g., Coq, Isabelle, or Lean) installed on your system
* A basic understanding of formal logic and mathematical notation

## Exercise 1: Environment Setup & Sanity Check

1. Open a terminal or command prompt and navigate to your working directory.
2. Install the necessary packages for your chosen proof assistant. For example, with Coq:
```bash
opam switch 4.13.0
opam install coq
```
3. Verify that your proof assistant is installed and functional by running a simple command. For Coq:
```bash
coqtop
```
You should see the Coq interactive toplevel. Type `Check 1 + 1` and press Enter. The output should be `= 2`.

## Exercise 2: Your First Working Experiment

1. Open your proof assistant's interactive environment (e.g., Coq's `coqtop`).
2. Define a simple proposition using the `Prop` type. For example, in Coq:
```coq
Definition my_prop : Prop := True.
```
3. Use the `Proof` command to start a new proof. For example, in Coq:
```coq
Proof.
```
4. State the goal of your proof. For example, in Coq:
```coq
Goal my_prop.
```
5. Use the `exact` tactic to prove the goal. For example, in Coq:
```coq
exact my_prop.
```
6. Save your proof as a file (e.g., `my_proof.v`).

## Exercise 3: Inspecting Basic State

1. Open the log file for your proof assistant (e.g., `coq.log`).
2. Look for the section where your proof was saved. You should see the `my_proof.v` file listed.
3. Open the `my_proof.v` file in a text editor. You should see the proof written in your chosen proof assistant's notation.

## Challenge Exercise

1. Modify the `my_prop` definition to use a different proposition (e.g., `False`).
2. Attempt to prove the modified proposition using the `exact` tactic.
3. What happens when you try to prove a false proposition?
