# Hands-On Operational Lab: Combinatorics

## Objective & Prerequisites

This lab provides hands-on experience with combinatorial calculations using Python. The objective is to develop intuition for combinatorial structures and to practice debugging common errors in combinatorial algorithms.

**Prerequisites**:
- Basic knowledge of Python programming (version 3.6+)
- Understanding of set theory and basic combinatorial concepts (subsets, permutations)
- Familiarity with mathematical notation for combinations and permutations

---

## Exercise 1: Exploration & System State Inspection

In this exercise, we explore the number of subsets for a small set and verify the result using direct computation.

**Step 1**: Create the script `combinatorics_lab.py` with the following content:

```python
import itertools

def count_subsets(n):
    return 2 ** n

def generate_subsets(n):
    s = set(range(n))
    subsets = []
    for r in range(0, n+1):
        for subset in itertools.combinations(s, r):
            subsets.append(subset)
    return subsets

def count_permutations(n, k):
    if k < 0 or k > n:
        return 0
    result = 1
    for i in range(0, k+1):
        result *= (n - i)
    return result

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python3 combinatorics_lab.py [command] [args]")
        print("Commands: count, subsets, permutations")
        sys.exit(1)

    command = sys.argv[1]
    if command == "count":
        n = int(sys.argv[2])
        print(f"Number of subsets for n={n}: {count_subsets(n)}")
    elif command == "subsets":
        n = int(sys.argv[2])
        subsets = generate_subsets(n)
        print(f"Number of subsets for n={n}: {len(subsets)}")
        if n <= 2:
            print("Subsets:")
            for subset in subsets:
                print(subset)
    elif command == "permutations":
        n = int(sys.argv[2])
        k = int(sys.argv[3])
        print(f"Permutations of {n} things taken {k} at a time: {count_permutations(n, k)}")
    else:
        print(f"Unknown command: {command}")
```

**Step 2**: Run the command to count the number of subsets for a set of size 3:

```bash
python3 combinatorics_lab.py count 3
```

**Expected Output**:
```
Number of subsets for n=3: 8
```

**Why this works**: The number of subsets of a set with $n$ elements is $2^n$. For $n=3$, we have $2^3 = 8$ subsets. This matches the combinatorial identity $\sum_{k=0}^{n} \binom{n}{k} = 2^n$.

---

## Exercise 2: Building & Deploying / Modeling Scenario

In this exercise, we model the generation of all subsets and permutations for small sets.

**Step 1**: Generate all subsets for a set of size 3:

```bash
python3 combinatorics_lab.py subsets 3
```

**Expected Output**:
```
Number of subsets for n=3: 8
Subsets:
()
(0,)
(1,)
(2,)
(0, 1)
(0, 2)
(1, 2)
(0, 1, 2)
```

**Why this works**: The script generates all $2^3 = 8$ subsets of $\{0,1,2\}$ using `itertools.combinations`. This matches the combinatorial definition where each subset corresponds to a unique binary choice for each element.

**Step 2**: Compute permutations of 3 things taken 2 at a time:

```bash
python3 combinatorics_lab.py permutations 3 2
```

**Expected Output**:
```
Permutations of 3 things taken 2 at a time: 6
```

**Why this works**: The number of permutations $P(n,k) = n \times (n-1) \times \cdots \times (n-k+1)$ for $n=3$, $k=2$ is $3 \times 2 = 6$. This follows the definition of permutations where order matters.

---

## Exercise 3: Fault Injection, Failure Analysis & Debugging

In this exercise, we introduce a bug in the permutation function and analyze the failure.

**Step 1**: Run the command to compute permutations of 3 things taken 3 at a time (this will fail):

```bash
python3 combinatorics_lab.py permutations 3 3
```

**Expected Output**:
```
Permutations of 3 things taken 3 at a time: 0
```

**Failure Analysis**:  
The bug in the permutation function is the loop `for i in range(0, k+1)`. This runs $k+1$ times instead of $k$ times. For $n=3$, $k=3$:
- $i=0$: $3 \times 1 = 3$
- $i=1$: $3 \times 2 = 6$
- $i=2$: $6 \times 1 = 6$
- $i=3$: $6 \times 0 = 0$ (the bug causes the final term to be zero)

**Why this fails**: The permutation formula $P(n,k) = n \times (n-1) \times \cdots \times (n-k+1)$ requires exactly $k$ terms. The bug adds an extra term $(n-k)$ which becomes zero when $k=n$.

**Step 2**: Fix the bug by changing the loop to `for i in range(0, k)`:

```python
# In combinatorics_lab.py, change:
#   for i in range(0, k+1):
# to
for i in range(0, k):
```

**Step 3**: Re-run the command with the fixed script:

```bash
python3 combinatorics_lab.py permutations 3 3
```

**Expected Output**:
```
Permutations of 3 things taken 3 at a time: 6
```

**Why the fix works**: The loop now runs exactly $k$ times (from $i=0$ to $i=k-1$), producing $n \times (n-1) \times \cdots \times (n-k+1)$. For $n=3$, $k=3$: $3 \times 2 \times 1 = 6$.

---

## Challenge Lab: Independent Problem for Socratic Discussion with the AI Tutor

**Problem**:  
How many ways are there to choose a committee of 3 members from a group of 10 people, and then choose a chairperson from the committee?

**Socratic Discussion Questions**:
1. What is the total number of ways to choose the committee?
2. Why is the chairperson selection not independent of the committee selection?
3. Write the formula for the total number of ways using combinatorial notation.
4. How does this relate to the permutation formula $P(n,k)$?

**Expected Solution**:  
The total number of ways is $\binom{10}{3} \times 3 = 120 \times 3 = 360$.  
This follows from the multiplication principle:  
- First, choose 3 people from 10: $\binom{10}{3} = \frac{10!}{3!7!} = 120$  
- Then, choose 1 chair from the 3: $3$ ways  
- Total: $120 \times 3 = 360$

**Why this is important**:  
This problem demonstrates the difference between combinations (where order doesn't matter) and permutations (where order matters). The solution requires recognizing that after selecting the committee, we have a *permutation* of the committee (choosing one chair from three).

**AI Tutor Guidance**:  
Ask the AI tutor to derive the formula step-by-step using:
- The definition of combinations $\binom{n}{k}$
- The multiplication principle
- The relationship between combinations and permutations ($P(n,k) = k \times \binom{n}{k}$)

**Further Challenge**:  
What if we wanted to choose a committee of 3 with a chairperson and a secretary (distinct roles)? How would the count change?

> 💡 **Key Insight**: Combinatorics problems often require identifying whether order matters and applying the multiplication principle correctly. The AI tutor can help you formalize the reasoning using set theory and combinatorial identities.

---

This lab provides a rigorous, hands-on approach to combinatorial reasoning with clear failure analysis and debugging. The exercises build intuition while maintaining formal correctness through step-by-step verification.
