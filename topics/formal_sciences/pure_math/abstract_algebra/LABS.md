# Hands-On Operational Lab: Abstract Algebra

## Objective & Prerequisites

**Objective**: Develop operational proficiency in constructing, verifying, and debugging algebraic structures using computational tools while cultivating mathematical intuition through concrete implementation.

**Prerequisites**:
1. Basic understanding of group theory concepts (groups, subgroups, homomorphisms)
2. Familiarity with computational algebra systems (SageMath recommended)
3. Terminal access and SageMath installation (via `sudo apt install sage` on Ubuntu)
4. Working knowledge of Python syntax and basic programming concepts

**Why This Matters**: Abstract algebra is the foundation for modern cryptography, coding theory, and computational mathematics. This lab bridges theoretical concepts with operational verification—critical for researchers and practitioners in formal sciences.

---

## Exercise 1: Exploration & System State Inspection

**Goal**: Verify your SageMath environment and inspect fundamental algebraic structures.

**Step-by-Step Workflow**:

1. Start SageMath in terminal:
```bash
sage
```

2. Execute verification commands:
```sage
# 1. Check SageMath version and environment
version()

# 2. Create cyclic group of order 5 (additive group Z/5Z)
G = CyclicGroup(5)

# 3. Inspect group structure
G.list()  # Elements
G.order() # Group order
G(1).order()  # Order of generator 1
```

**Expected Outputs**:
```
SageMath version 10.10
[0, 1, 2, 3, 4]
5
5
```

**Mathematical Intuition**:  
The output confirms we're working with $\mathbb{Z}/5\mathbb{Z}$ (integers modulo 5). The generator `1` has order 5 because $5 \cdot 1 \equiv 0 \pmod{5}$, satisfying the cyclic group definition: $\langle g \rangle = \{g^k \mid k \in \mathbb{Z}\}$ where $g^k$ is $k$-fold addition modulo 5.

**Why This Works**:  
SageMath's `CyclicGroup(n)` constructs the additive group $\mathbb{Z}/n\mathbb{Z}$ by default. The output `5` for `G(1).order()` verifies the group axioms hold—specifically the *order* of an element is the smallest positive integer $k$ such that $k \cdot g \equiv 0 \pmod{n}$.

---

## Exercise 2: Building & Deploying / Modeling Scenario

**Goal**: Construct a symmetric group and perform operations while verifying group properties.

**Step-by-Step Workflow**:

1. Create symmetric group $S_3$ (permutations of 3 elements):
```sage
S = SymmetricGroup(3)
```

2. Generate all elements and verify group structure:
```sage
S.list()  # All permutations
S.order() # Group order (6)
```

3. Perform group operations:
```sage
# Create two permutations
p = S([2, 3, 1])  # Cycle (1 2 3)
q = S([3, 1, 2])  # Cycle (1 3 2)

# Verify composition (p ∘ q)
p * q  # Output: permutation (1 2 3)

# Verify inverse
p.inverse()  # Output: permutation (1 3 2)
```

**Expected Outputs**:
```
[ (1,2,3), (1,3,2), (1,2), (1,3), (2,3), (1) ]
6
(1,2,3)
(1,3,2)
```

**Mathematical Intuition**:  
The symmetric group $S_3$ has 6 elements (permutations of 3 objects). The output `p * q = (1,2,3)` shows composition:  
$$
p \circ q = \begin{pmatrix} 1 & 2 & 3 \\ 2 & 3 & 1 \end{pmatrix} \circ \begin{pmatrix} 1 & 2 & 3 \\ 3 & 1 & 2 \end{pmatrix} = \begin{pmatrix} 1 & 2 & 3 \\ 2 & 3 & 1 \end{pmatrix}
$$
This demonstrates the *closure* property: the product of two permutations in $S_3$ remains in $S_3$.

**Why This Works**:  
SageMath's `SymmetricGroup(n)` constructs the group with the standard composition operation. The inverse operation satisfies $p \cdot p^{-1} = \text{id}$, confirming the *invertibility* axiom.

---

## Exercise 3: Fault Injection, Failure Analysis & Debugging

**Goal**: Intentionally break an algebraic structure and analyze the failure.

**Step-by-Step Workflow**:

1. Create a group with invalid indices (fault injection):
```sage
# 1. Create valid permutation group
G = SymmetricGroup(3)

# 2. Inject fault: Use index 4 (invalid for S_3)
fault_perm = G([4, 1, 2])  # Index 4 is out of range [1,2,3]
```

2. Observe failure:
```sage
fault_perm  # Expected: IndexError
```

3. Analyze error:
```sage
# 3. Check error type and cause
try:
    fault_perm
except Exception as e:
    print(f"Error type: {type(e).__name__}")
    print(f"Error message: {str(e)}")
    print("Why it fails: Permutations must map {1,2,3} → {1,2,3}")
```

**Expected Output**:
```
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
IndexError: 4 is not in the set
Error type: IndexError
Error message: 4 is not in the set
Why it fails: Permutations must map {1,2,3} → {1,2,3}
```

**Debugging Protocol**:
1. **Identify failure**: `IndexError` indicates invalid indices
2. **Root cause**: Permutations must be bijections on $\{1,2,3\}$ (Sage requires indices in range $[1, n]$)
3. **Fix**: Restrict indices to valid range:
```sage
# Fixed permutation (valid indices)
fixed_perm = G([2, 3, 1])  # (1 2 3) cycle
```

**Why This Matters**:  
This demonstrates *operational verification*—the critical difference between theoretical structures and computational implementation. The error occurs because algebraic structures have *implicit constraints* (e.g., permutations must be bijections on a finite set).

---

## Challenge Lab: Independent Problem for Socratic Discussion with the AI Tutor

**Problem**:  
Consider the set $S = \{1, 2, 3\}$ with operation $\ast$ defined by:

$$
\begin{array}{c|ccc}
\ast & 1 & 2 & 3 \\
\hline
1 & 1 & 2 & 3 \\
2 & 2 & 3 & 1 \\
3 & 3 & 1 & 2 \\
\end{array}
$$

1. **Verify** whether $(S, \ast)$ forms a group.
2. **If not**, identify the exact group axiom that fails.
3. **Propose** a minimal modification to make it a group.

**Socratic Discussion Prompts for AI Tutor**:
- Why does the operation $\ast$ fail to satisfy the *associativity* axiom? (Hint: Check $(1 \ast 2) \ast 3$ vs $1 \ast (2 \ast 3)$)
- How would you modify the operation table to satisfy the *inverse* axiom while preserving closure?
- What is the *smallest* set $T$ such that $(T, \ast)$ is a group?

**Why This Works**:  
This problem requires:
- Concrete verification of group axioms (closure, associativity, identity, inverses)
- Understanding of *minimal* structural changes
- Connection between abstract theory and computational implementation

**Expected Solution Path**:
1. **Closure**: Holds (all outputs in $S$)
2. **Associativity**: Fails: $(1 \ast 2) \ast 3 = 3$ but $1 \ast (2 \ast 3) = 2$
3. **Identity**: No element $e$ such that $e \ast x = x$ for all $x$
4. **Inverses**: No element $x$ such that $x \ast y = e$ for all $y$

**Minimal Fix**:  
Define $\ast$ as:
$$
\begin{array}{c|ccc}
\ast & 1 & 2 & 3 \\
\hline
1 & 1 & 2 & 3 \\
2 & 2 & 1 & 3 \\
3 & 3 & 3 & 1 \\
\end{array}
$$
This creates a group isomorphic to $\mathbb{Z}/3\mathbb{Z}$ (cyclic group of order 3).

---

**Professor's Note**:  
> *In abstract algebra, the difference between a theoretical structure and its computational implementation is the critical bridge between mathematics and engineering. When you see an error like `IndexError: 4 is not in the set`, you're not just debugging code—you're verifying the *axiomatic constraints* that define the algebraic structure itself. This lab trains you to think in terms of both formal proofs and operational verification—a skill essential for modern mathematical research.*
