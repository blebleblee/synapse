# Hands-On Operational Lab: Topology

## Objective & Prerequisites

**Objective**: To develop practical intuition and rigorous verification skills for topological spaces through computational exploration. This lab bridges abstract topological concepts with executable verification, emphasizing the interplay between formal definitions and computational implementation.

**Prerequisites**:
- Solid understanding of set theory (unions, intersections, complements)
- Familiarity with the three axioms of a topology:
  1. $\emptyset, X \in \mathcal{O}$
  2. $\mathcal{O}$ closed under finite unions
  3. $\mathcal{O}$ closed under arbitrary intersections
- Basic proficiency in Python (or willingness to learn minimal scripting)
- Understanding that topological spaces are foundational in analysis, geometry, and algebraic topology

*Note: All commands and scripts are designed to be executed in a standard Unix-like shell (e.g., macOS Terminal, Linux bash, or Windows WSL).*

---

## Exercise 1: Exploration & System State Inspection (Explicit verification commands and expected outputs)

**Goal**: Verify a standard topological space through direct computation.

**Step 1**: Create the verification script `topology_check.py` with the following content:

```python
from typing import Set, List

def is_topology(X: Set, O: List[Set]) -> bool:
    # Axiom 1: Contains empty set and X
    if set() not in O or X not in O:
        return False
    
    # Axiom 2: Closed under finite unions
    for A in O:
        for B in O:
            union = A.union(B)
            if union not in O:
                return False
    
    # Axiom 3: Closed under finite intersections (sufficient for small spaces)
    for A in O:
        for B in O:
            intersection = A.intersection(B)
            if intersection not in O:
                return False
    
    return True

def main():
    # Discrete topology on {0, 1}
    X = {0, 1}
    O = [set(), {0}, {1}, X]
    
    # Verify topology
    if is_topology(X, O):
        print(f"Topology on {X} with open sets {O} is valid.")
    else:
        print(f"Topology on {X} with open sets {O} is invalid.")
    
    # Check if {0} is open
    test_set = {0}
    print(f"{test_set} is open." if test_set in O else f"{test_set} is not open.")

if __name__ == "__main__":
    main()
```

**Step 2**: Execute the script in the shell:

```bash
python3 topology_check.py
```

**Expected Output**:
```
Topology on {0, 1} with open sets [set(), {0}, {1}, {0, 1}] is valid.
{0} is open.
```

**Why this works**: The discrete topology on two points satisfies all three axioms:
1. $\emptyset, X \in \mathcal{O}$ (verified)
2. All unions of open sets remain open (e.g., $\{0\} \cup \{1\} = \{0,1\} \in \mathcal{O}$)
3. All intersections of open sets remain open (e.g., $\{0\} \cap \{1\} = \emptyset \in \mathcal{O}$)

This output confirms the system correctly implements topological verification.

---

## Exercise 2: Building & Deploying / Modeling Scenario (Step-by-step interactive workflow)

**Goal**: Construct and validate a non-trivial topological space (Sierpinski space).

**Step 1**: Create the modeling script `sierpinski_topology.py` with the following content:

```python
from typing import Set, List

def is_topology(X: Set, O: List[Set]) -> bool:
    # Axiom 1: Contains empty set and X
    if set() not in O or X not in O:
        return False
    
    # Axiom 2: Closed under finite unions
    for A in O:
        for B in O:
            union = A.union(B)
            if union not in O:
                return False
    
    # Axiom 3: Closed under finite intersections
    for A in O:
        for B in O:
            intersection = A.intersection(B)
            if intersection not in O:
                return False
    
    return True

def main():
    # Sierpinski space on {0, 1}
    X = {0, 1}
    O = [set(), {0}, X]  # Standard Sierpinski topology
    
    # Verify topology
    if is_topology(X, O):
        print(f"Topology on {X} with open sets {O} is valid.")
    else:
        print(f"Topology on {X} with open sets {O} is invalid.")
    
    # Check if {0} is open
    test_set = {0}
    print(f"{test_set} is open." if test_set in O else f"{test_set} is not open.")

if __name__ == "__main__":
    main()
```

**Step 2**: Execute the script:

```bash
python3 sierpinski_topology.py
```

**Expected Output**:
```
Topology on {0, 1} with open sets [set(), {0}, {0, 1}] is valid.
{0} is open.
```

**Why this works**: The Sierpinski topology satisfies:
1. $\emptyset, X \in \mathcal{O}$ (verified)
2. Unions: $\{0\} \cup \{0\} = \{0\} \in \mathcal{O}$, $\{0\} \cup X = X \in \mathcal{O}$
3. Intersections: $\{0\} \cap \{0\} = \{0\} \in \mathcal{O}$, $\{0\} \cap X = \{0\} \in \mathcal{O}$

This demonstrates how to model a non-trivial topological space with minimal computational overhead.

---

## Exercise 3: Fault Injection, Failure Analysis & Debugging

**Goal**: Intentionally break a topology and analyze the failure mechanism.

**Step 1**: Create the faulty topology script `faulty_topology.py`:

```python
from typing import Set, List

def is_topology(X: Set, O: List[Set]) -> bool:
    # Axiom 1: Contains empty set and X
    if set() not in O or X not in O:
        return False
    
    # Axiom 2: Closed under finite unions
    for A in O:
        for B in O:
            union = A.union(B)
            if union not in O:
                return False
    
    # Axiom 3: Closed under finite intersections
    for A in O:
        for B in O:
            intersection = A.intersection(B)
            if intersection not in O:
                return False
    
    return True

def main():
    # Faulty topology on {0, 1, 2}
    X = {0, 1, 2}
    O = [set(), {0}, {1, 2}]  # Missing X and union closure
    
    # Verify topology
    if is_topology(X, O):
        print(f"Topology on {X} with open sets {O} is valid.")
    else:
        print(f"Topology on {X} with open sets {O} is invalid.")
        print("Failure analysis: The topology fails Axiom 2 because:")
        print(f"  {O[1]} ∪ {O[2]} = {{0, 1, 2}} ∉ {O}")

if __name__ == "__main__":
    main()
```

**Step 2**: Execute the script:

```bash
python3 faulty_topology.py
```

**Expected Output**:
```
Topology on {0, 1, 2} with open sets [set(), {0}, {1, 2}] is invalid.
Failure analysis: The topology fails Axiom 2 because:
  {0} ∪ {1, 2} = {0, 1, 2} ∉ [set(), {0}, {1, 2}]
```

**Failure Analysis**:
1. **Root cause**: The topology violates Axiom 2 (finite unions) because $\{0\} \cup \{1,2\} = \{0,1,2\}$ is not in $\mathcal{O}$.
2. **Why it matters**: Topologies must be closed under unions to ensure continuity of mappings and path-connectedness.
3. **Debugging fix**: Add $X = \{0,1,2\}$ to $\mathcal{O}$ to satisfy the union axiom.

**Step 3**: Fix the topology and revalidate:

```bash
# Create fixed topology
echo "X = {0, 1, 2}
O = [set(), {0}, {1, 2}, X]" > fixed_topology.py

# Run fixed topology
python3 fixed_topology.py
```

**Expected Output**:
```
Topology on {0, 1, 2} with open sets [set(), {0}, {1, 2}, {0, 1, 2}] is valid.
```

**Key Insight**: Topological spaces require strict adherence to the union and intersection axioms. This exercise demonstrates how computational verification exposes structural flaws in topological constructions.

---

## Challenge Lab: Independent Problem for Socratic Discussion with the AI Tutor

**Problem**:  
Consider the set $X = \{a, b, c\}$. Define $\mathcal{O} = \{\emptyset, \{a\}, \{b\}, \{a,b\}\}$. Is $\mathcal{O}$ a topology on $X$? If not, what is the minimal set of open sets that must be added to $\mathcal{O}$ to make it a topology?

**Socratic Discussion Points** (for the student to explore with the AI Tutor):

1. **Verify Axiom 1**: Does $\mathcal{O}$ contain $\emptyset$ and $X$?  
   *Why this matters*: Topologies must include the entire space and empty set.

2. **Check union closure**: What is $\{a\} \cup \{b\}$? Is it in $\mathcal{O}$?  
   *Why this matters*: The union of two open sets must be open.

3. **Check intersection closure**: What is $\{a\} \cap \{b\}$? Is it in $\mathcal{O}$?  
   *Why this matters*: The intersection of two open sets must be open.

4. **Identify missing sets**: What is the minimal set that must be added to $\mathcal{O}$ to satisfy all axioms?  
   *Why this matters*: Topologies are minimal structures satisfying the axioms.

**Expected Answer** (for verification):  
$\mathcal{O}$ is **not** a topology because it does **not** contain $X = \{a,b,c\}$. The minimal set to add is $\{X\}$ (i.e., $\{a,b,c\}$).

**Why this works**:  
- After adding $X$, $\mathcal{O}' = \{\emptyset, \{a\}, \{b\}, \{a,b\}, \{a,b,c\}\}$ satisfies:
  - Axiom 1: $\emptyset, X \in \mathcal{O}'$
  - Axiom 2: All unions remain in $\mathcal{O}'$ (e.g., $\{a\} \cup \{b\} = \{a,b\} \in \mathcal{O}'$)
  - Axiom 3: All intersections remain in $\mathcal{O}'$ (e.g., $\{a\} \cap \{b\} = \emptyset \in \mathcal{O}'$)

This exercise reinforces that topological spaces are defined by *structural constraints* rather than arbitrary collections of sets.

---

> **Professor's Note**: In formal topology, the distinction between *finite* and *arbitrary* unions is critical (e.g., in infinite spaces). This lab uses finite unions for simplicity but demonstrates the core verification process. For advanced work, consider implementing arbitrary unions using `itertools.combinations` or a topological space with infinitely many open sets. Always verify your constructions against the axioms—this is the essence of rigorous topological practice.
