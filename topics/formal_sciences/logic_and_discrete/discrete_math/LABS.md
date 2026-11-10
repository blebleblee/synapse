# Hands-On Operational Lab: Discrete Math

## Objective & Prerequisites

**Objective**: Develop hands-on proficiency in discrete mathematics through systematic modeling, verification, and fault analysis of core structures. This lab focuses on *operational* application of discrete concepts rather than theoretical abstraction.

**Prerequisites**:
- Basic familiarity with Python programming (version 3.7+)
- Understanding of core discrete concepts: sets, functions, graphs, combinatorics
- Terminal environment (Linux/macOS/WSL) with Python installed
- Minimum 10 minutes of dedicated practice time

> 💡 *Why this works*: This lab bridges abstract theory with executable systems by using Python as the operational medium. Discrete math becomes tangible through concrete modeling rather than symbolic manipulation.

---

## Exercise 1: Exploration & System State Inspection

**Goal**: Verify foundational discrete structures through explicit system state inspection.

**Step 1: Generate natural numbers sequence**  
Run this command to inspect the first 10 natural numbers:

```bash
python3 -c "print('Natural numbers (1-10): ', end='') for i in range(1, 11): print(i, end=' ')"
```

**Expected Output**:  
`Natural numbers (1-10): 1 2 3 4 5 6 7 8 9 10`

**Why this works**: The `range(1, 11)` generates integers from 1 to 10 (exclusive upper bound), demonstrating the *well-defined* nature of natural number sequences.

**Step 2: Generate prime numbers sequence**  
Run this command to inspect the first 10 primes:

```bash
python3 -c "print('First 10 primes: ', end='') for n in range(2, 100): if all(n % i != 0 for i in range(2, int(n**0.5)+1)): print(n, end=' ')"
```

**Expected Output**:  
`First 10 primes: 2 3 5 7 11 13 17 19 23 29`

**Why this works**: The nested loop implements *trial division* – a fundamental discrete math technique for primality testing. The output matches the known sequence of prime numbers.

**Verification Check**:  
Confirm the output matches the *first 10 primes* (2, 3, 5, 7, 11, 13, 17, 19, 23, 29) using the definition: *a prime number is a natural number greater than 1 that has no positive divisors other than 1 and itself*.

> ✅ **Key Insight**: System state inspection reveals how discrete structures (natural numbers, primes) are *explicitly constructed* through deterministic algorithms – the foundation of computational discrete math.

---

## Exercise 2: Building & Deploying / Modeling Scenario

**Goal**: Model a graph and perform breadth-first search (BFS) to demonstrate discrete structure traversal.

**Step 1: Create graph model**  
Generate `graph_bfs.py` with this content:

```python
from collections import deque

def bfs(graph, start):
    visited = set()
    queue = deque([start])
    visited.add(start)
    while queue:
        current = queue.popleft()
        print(f"Visiting node: {current}")
        for neighbor in graph[current]:
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append(neighbor)
    return visited

# Define graph: {node: [neighbors]}
graph = {
    'A': ['B', 'C'],
    'B': ['A', 'D'],
    'C': ['A', 'E'],
    'D': ['B'],
    'E': ['C']
}

print("BFS starting from A:")
bfs(graph, 'A')
```

**Step 2: Deploy the model**  
Run the model:

```bash
python3 graph_bfs.py
```

**Expected Output**:  
```
BFS starting from A:
Visiting node: A
Visiting node: B
Visiting node: C
Visiting node: D
Visiting node: E
```

**Why this works**:  
1. The graph is a *well-defined* discrete structure (nodes and edges)
2. BFS follows the *discrete* property of *level-by-level exploration* (no cycles)
3. The output sequence (`A → B → C → D → E`) demonstrates *topological order* – a key discrete concept in graph theory

**System State Verification**:  
Confirm the visited set contains exactly 5 nodes (`{'A', 'B', 'C', 'D', 'E'}`) using:
```bash
python3 graph_bfs.py | grep "Visiting node"
```

> 🔍 **Critical Insight**: This model shows how discrete structures (graphs) are *operationally traversed* using deterministic state transitions – the essence of discrete computation.

---

## Exercise 3: Fault Injection, Failure Analysis & Debugging

**Goal**: Introduce a fault in the BFS model and analyze the failure mechanism.

**Step 1: Inject fault**  
Modify `graph_bfs.py` to remove the `visited` check (causing infinite loops):

```python
# BEFORE (working code)
# if neighbor not in visited:

# AFTER (faulty code)
if True:  # Removed visited check
```

**Step 2: Run faulty model**  
Execute the modified script:

```bash
python3 graph_bfs.py
```

**Expected Output (failure)**:  
```
BFS starting from A:
Visiting node: A
Visiting node: B
Visiting node: B
Visiting node: B
...
```
*(Infinite loop of "B" nodes)*

**Step 3: Failure analysis**  
Identify the root cause:
```bash
python3 graph_bfs.py | grep "Visiting node" | head -n 5
```
**Output**:  
`Visiting node: A`  
`Visiting node: B`  
`Visiting node: B`  
`Visiting node: B`  
`Visiting node: B`

**Why this fails**:  
The `visited` set is *not maintained*, so node `B` is repeatedly added to the queue. This violates the *discrete state transition* property – the system enters an *infinite state* (no termination).

**Step 4: Debugging fix**  
Restore the `visited` check to fix the model:
```python
if neighbor not in visited:  # Restored check
```

**Why this works**: The `visited` set enforces *discrete state boundaries* – each node is processed exactly once, preventing infinite loops.

> ⚠️ **Critical Lesson**: Discrete systems *require* state constraints to avoid pathological behavior. The `visited` set is a *fundamental discrete invariant* that maintains system integrity.

---

## Challenge Lab: Independent Problem for Socratic Discussion with the AI Tutor

**Problem**:  
*Consider the set $S = \{a, b, c\}$. How many subsets of size 2 exist in $S$? Prove your answer using combinatorial reasoning.*

**Socratic Discussion Prompts** (for your AI Tutor):

1. What is the total number of subsets of $S$?  
   *(Hint: $2^{|S|}$)*

2. How do we count subsets of size 2?  
   *(Hint: $\binom{n}{k}$)*

3. Write a Python program that computes $\binom{3}{2}$ and verify the output.  
   *(Hint: `from math import comb`)*

4. Why does this problem demonstrate the *operational* nature of discrete math?  
   *(Hint: What happens when we remove the state constraint?)*

**Expected Answer**:  
There are $\binom{3}{2} = 3$ subsets: $\{a,b\}$, $\{a,c\}$, $\{b,c\}$.

**Python Verification**:
```python
from math import comb
print(comb(3, 2))  # Output: 3
```

**Why this works**:  
This problem demonstrates *combinatorial generation* – a core discrete operation where we explicitly construct subsets (discrete structures) and count them (discrete operation). The solution is *operationally verifiable* through direct computation.

> 💡 **Professor's Insight**: In real-world systems, this is analogous to *state space exploration* – without the combinatorial constraint (the `visited` set), we'd get infinite states (like the BFS failure). Discrete math provides the *operational boundaries* that make computation feasible.

---

**Final Note**: This lab transforms abstract discrete concepts into *executable systems*. By focusing on explicit state inspection, fault injection, and operational verification, you develop the intuition that discrete math is not just theory – it's the foundation of *real-world computation*. 

> ✅ **Lab Completion Check**: You have successfully modeled discrete structures, verified system states, injected faults, and debugged failures – the complete operational cycle of discrete mathematics.
