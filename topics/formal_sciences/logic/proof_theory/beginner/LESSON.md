# Beginner Technical Lesson: Proof Theory
## 1. Core Mechanics & Basic Principles

Proof theory is a branch of mathematical logic that deals with the study of the structure and properties of mathematical proofs. It provides a framework for understanding how mathematical truths are established and how they can be used to derive new truths. At its core, proof theory is concerned with the mechanics of how we construct and evaluate mathematical proofs.

### Key Concepts:

* **Formal System**: A formal system is a set of rules and axioms that govern the construction of mathematical proofs. It provides a framework for ensuring that proofs are valid and sound.
* **Axioms**: Axioms are self-evident truths that serve as the foundation for a formal system. They are the starting point for constructing proofs.
* **Inference Rules**: Inference rules are the rules that govern how we derive new truths from existing axioms and previously proven statements.
* **Proof**: A proof is a sequence of statements that demonstrates the validity of a mathematical statement.

## 2. Step-by-Step Component Breakdown

To understand how proof theory works, let's break down the components involved in constructing a proof:

### 1. **Axioms**:

* Axioms are the foundation of a formal system.
* They are self-evident truths that require no proof.
* Examples of axioms include:
	+ Peano's axioms for arithmetic (e.g., 0 is a number, the successor of a number is a number)
	+ Zermelo-Fraenkel axioms for set theory (e.g., the empty set exists, the power set of a set exists)

### 2. **Inference Rules**:

* Inference rules govern how we derive new truths from existing axioms and previously proven statements.
* Examples of inference rules include:
	+ Modus Ponens (if A implies B, and A is true, then B is true)
	+ Universal Instantiation (if A is true for all x, then A is true for some x)

### 3. **Proof**:

* A proof is a sequence of statements that demonstrates the validity of a mathematical statement.
* A proof consists of a series of steps, each of which applies an inference rule to the previous statements.

## 3. First Working Implementation

Here is a simple example of a formal system in Python:
```python
# Formal System Example

# Axioms
axioms = {
    '0': '0 is a number',
    'succ': 'the successor of a number is a number'
}

# Inference Rules
inference_rules = {
    'modus_ponens': lambda A, B: f'if {A} implies {B}, and {A} is true, then {B} is true',
    'universal_instantiation': lambda A: f'if {A} is true for all x, then {A} is true for some x'
}

# Proof
proof = {
    'step1': '0 is a number (axiom)',
    'step2': 'the successor of 0 is a number (inference rule: modus ponens)',
    'step3': 'the successor of 0 is a number (axiom)'
}

print(proof)
```
This example demonstrates a simple formal system with two axioms and two inference rules. The proof consists of three steps, each of which applies an inference rule to the previous statements.

## 4. What Can Go Wrong

Here are some common mistakes to watch out for when working with proof theory:

* **Invalid Inference**: Make sure that the inference rules are applied correctly and that the conclusions follow logically from the premises.
* **Incomplete Proof**: Ensure that the proof is complete and that all steps are justified by the axioms and inference rules.
* **Circular Reasoning**: Avoid circular reasoning, where the conclusion is used as a premise.

## 5. Key Takeaways & Review Checklist

Here are the key takeaways from this lesson:

* **Formal System**: A formal system is a set of rules and axioms that govern the construction of mathematical proofs.
* **Axioms**: Axioms are self-evident truths that serve as the foundation for a formal system.
* **Inference Rules**: Inference rules govern how we derive new truths from existing axioms and previously proven statements.
* **Proof**: A proof is a sequence of statements that demonstrates the validity of a mathematical statement.

Review checklist:

* Do you understand the basic mechanics of proof theory?
* Can you identify the key components of a formal system (axioms, inference rules, and proof)?
* Can you apply inference rules to derive new truths from existing axioms and previously proven statements?
* Can you identify common mistakes in proof theory (invalid inference, incomplete proof, and circular reasoning)?
