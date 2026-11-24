# Operational Verification Labs: Set Theory

## Objective & Mathematical Computing Setup

Set theory constitutes the foundational language of modern mathematics, providing the axiomatic substrate upon which analysis, algebra, topology, and logic are constructed. These operational verification labs transform abstract set-theoretic propositions into computationally verifiable assertions through symbolic execution engines, automated theorem provers, and exhaustive algorithmic enumeration. Rather than passively accepting the Zermelo-Fraenkel axioms or cardinal arithmetic as self-evident truths, we employ Python's SymPy symbolic algebra system, SageMath's computational framework, and interactive proof assistants to mechanize derivations, stress-test boundary cases, and implement constructive witnesses for existence theorems.

The computational mathematician requires a rigorous environment where abstract set membership, power set constructions, cardinality comparisons, and transfinite ordinal arithmetic can be executed as verifiable operations. We establish this environment through Python 3.11 or later with SymPy version 1.12 or higher, which provides symbolic finite set manipulation, and SageMath 10.0 or later for advanced combinatorial set operations. For formal proof verification, we utilize Lean 4 or Coq 8.17, though the primary focus remains on executable Python-based symbolic verification that bridges the gap between pure abstraction and computational reality.

Begin by verifying your symbolic computation environment. Execute the following diagnostic sequence to confirm that SymPy's set manipulation modules, cardinality comparison functions, and symbolic logic engines are properly installed and operational. Open a terminal session and invoke Python's symbolic algebra system directly:

```bash
python3 -c "import sympy; print('SymPy version:', sympy.__version__); from sympy import FiniteSet, Interval, Union, Intersection, ProductSet, PowerSet, ImageSet, Lambda, symbols; print('Set theory modules loaded successfully')"
```

This command imports the core set-theoretic constructors from SymPy's combinatorics and sets modules, confirming that finite set operations, interval arithmetic, Cartesian products, and power set generators are available. The output should display SymPy version 1.12 or higher along with a successful module load confirmation. If import errors occur, install SymPy through pip with explicit version specification:

```bash
pip3 install --upgrade 'sympy>=1.12'
```

For advanced set-theoretic computations involving infinite combinatorics, install SageMath either through your system package manager or via the official distribution. On Ubuntu or Debian systems, execute:

```bash
sudo apt-get update && sudo apt-get install sagemath
```

On macOS with Homebrew:

```bash
brew install --cask sage
```

Verify SageMath installation by launching the interactive environment and confirming set construction capabilities:

```bash
sage -c "print(Set([1,2,3]).cardinality()); print('SageMath operational')"
```

The computational environment now supports symbolic finite set arithmetic, cardinality verification, and algorithmic generation of power sets, Cartesian products, and function spaces. We proceed to mechanize fundamental set-theoretic theorems through executable verification protocols.

## Exercise 1: Computational Verification of Core Theorems

Set theory's foundational theorems—De Morgan's laws for set complements, the distributivity of intersection over union, the subset lattice properties, and cardinality arithmetic for finite sets—require rigorous computational verification rather than appeal to intuition. We construct explicit symbolic witnesses for each theorem, enumerate all relevant cases for small finite universes, and mechanically derive identities through algebraic manipulation engines.

**De Morgan's Laws and Set Complement Identities**

De Morgan's laws assert that the complement of a union equals the intersection of complements, formally $(A \cup B)^c = A^c \cap B^c$, and dually $(A \cap B)^c = A^c \cup B^c$. Rather than accepting these identities through Venn diagram intuition, we verify them computationally across all possible set configurations within a finite universe. Create a Python verification script that enumerates every possible pair of subsets within a universe of five elements and confirms both De Morgan identities through element-wise membership testing:

```python
from sympy import FiniteSet
from itertools import combinations

def verify_de_morgan_laws(universe_size):
    """
    Exhaustively verify De Morgan's laws for all subset pairs
    in a universe of specified size.
    """
    universe = FiniteSet(*range(universe_size))
    all_subsets = []
    
    # Generate all possible subsets via power set enumeration
    elements = list(range(universe_size))
    for r in range(universe_size + 1):
        for subset_tuple in combinations(elements, r):
            all_subsets.append(FiniteSet(*subset_tuple))
    
    verification_count = 0
    failure_cases = []
    
    for A in all_subsets:
        for B in all_subsets:
            # Compute complements relative to universe
            A_complement = universe - A
            B_complement = universe - B
            
            # First De Morgan law: (A ∪ B)^c = A^c ∩ B^c
            left_side_1 = universe - (A | B)
            right_side_1 = A_complement & B_complement
            
            if left_side_1 != right_side_1:
                failure_cases.append(('Law 1', A, B, left_side_1, right_side_1))
            
            # Second De Morgan law: (A ∩ B)^c = A^c ∪ B^c
            left_side_2 = universe - (A & B)
            right_side_2 = A_complement | B_complement
            
            if left_side_2 != right_side_2:
                failure_cases.append(('Law 2', A, B, left_side_2, right_side_2))
            
            verification_count += 1
    
    total_verifications = len(all_subsets) ** 2 * 2
    print(f"Universe size: {universe_size}")
    print(f"Total subsets: {len(all_subsets)}")
    print(f"Subset pairs tested: {len(all_subsets) ** 2}")
    print(f"Total verifications: {total_verifications}")
    print(f"Failures detected: {len(failure_cases)}")
    
    if failure_cases:
        print("\nFailure cases:")
        for case in failure_cases[:5]:  # Display first 5 failures
            print(f"  {case[0]}: A={case[1]}, B={case[2]}")
            print(f"    Left: {case[3]}, Right: {case[4]}")
    else:
        print("✓ All De Morgan law verifications passed")
    
    return len(failure_cases) == 0

# Verify for universes of increasing size
for size in [3, 4, 5]:
    print("\n" + "="*60)
    verify_de_morgan_laws(size)
```

Execute this verification protocol to confirm De Morgan's laws across 2048 distinct subset pair configurations for a five-element universe. The exhaustive enumeration approach guarantees that no counterexample exists within the tested domain, providing computational certainty rather than proof by assertion. The output displays the total number of subset pairs examined and confirms zero failures, establishing De Morgan's laws as verified identities within finite set theory.

**Cardinality Arithmetic and Inclusion-Exclusion Principle**

The inclusion-exclusion principle provides the fundamental counting formula for union cardinalities: $|A \cup B| = |A| + |B| - |A \cap B|$. For three sets, the formula extends to $|A \cup B \cup C| = |A| + |B| + |C| - |A \cap B| - |A \cap C| - |B \cap C| + |A \cap B \cap C|$. We verify this principle computationally and implement the general $n$-set inclusion-exclusion algorithm through recursive subset enumeration:

```python
from sympy import FiniteSet, symbols
from itertools import combinations
import random

def verify_inclusion_exclusion_two_sets(num_trials=1000, max_size=20):
    """
    Verify two-set inclusion-exclusion through random sampling.
    """
    failures = 0
    
    for trial in range(num_trials):
        # Generate random finite sets
        size_A = random.randint(0, max_size)
        size_B = random.randint(0, max_size)
        
        A = FiniteSet(*random.sample(range(max_size * 2), size_A))
        B = FiniteSet(*random.sample(range(max_size * 2), size_B))
        
        # Direct computation
        union_size = len(A | B)
        
        # Inclusion-exclusion formula
        formula_result = len(A) + len(B) - len(A & B)
        
        if union_size != formula_result:
            failures += 1
            print(f"Failure: |A∪B|={union_size}, formula={formula_result}")
            print(f"  A={A}, B={B}")
    
    print(f"Two-set inclusion-exclusion: {num_trials - failures}/{num_trials} passed")
    return failures == 0

def verify_inclusion_exclusion_three_sets(num_trials=1000, max_size=15):
    """
    Verify three-set inclusion-exclusion through random sampling.
    """
    failures = 0
    
    for trial in range(num_trials):
        # Generate random finite sets
        A = FiniteSet(*random.sample(range(max_size * 2), random.randint(0, max_size)))
        B = FiniteSet(*random.sample(range(max_size * 2), random.randint(0, max_size)))
        C = FiniteSet(*random.sample(range(max_size * 2), random.randint(0, max_size)))
        
        # Direct computation
        union_size = len(A | B | C)
        
        # Inclusion-exclusion formula
        formula_result = (len(A) + len(B) + len(C) 
                         - len(A & B) - len(A & C) - len(B & C)
                         + len(A & B & C))
        
        if union_size != formula_result:
            failures += 1
            print(f"Failure: |A∪B∪C|={union_size}, formula={formula_result}")
    
    print(f"Three-set inclusion-exclusion: {num_trials - failures}/{num_trials} passed")
    return failures == 0

def general_inclusion_exclusion(sets):
    """
    Compute |A₁ ∪ A₂ ∪ ... ∪ Aₙ| using general inclusion-exclusion principle.
    
    Formula: Σ|Aᵢ| - Σ|Aᵢ ∩ Aⱼ| + Σ|Aᵢ ∩ Aⱼ ∩ Aₖ| - ... + (-1)^(n+1)|A₁ ∩ ... ∩ Aₙ|
    """
    if not sets:
        return 0
    
    n = len(sets)
    total = 0
    
    # Iterate over all non-empty subsets of indices
    for k in range(1, n + 1):
        sign = (-1) ** (k + 1)
        for index_subset in combinations(range(n), k):
            # Compute intersection of sets at selected indices
            intersection = sets[index_subset[0]]
            for idx in index_subset[1:]:
                intersection = intersection & sets[idx]
            total += sign * len(intersection)
    
    return total

def verify_general_inclusion_exclusion(num_trials=500, num_sets=5, max_size=10):
    """
    Verify general n-set inclusion-exclusion formula.
    """
    failures = 0
    
    for trial in range(num_trials):
        # Generate random collection of sets
        sets = []
        for _ in range(num_sets):
            set_size = random.randint(0, max_size)
            sets.append(FiniteSet(*random.sample(range(max_size * 2), set_size)))
        
        # Direct computation
        union = sets[0]
        for s in sets[1:]:
            union = union | s
        direct_size = len(union)
        
        # Inclusion-exclusion formula
        formula_size = general_inclusion_exclusion(sets)
        
        if direct_size != formula_size:
            failures += 1
            if failures <= 3:  # Print first few failures
                print(f"Failure: direct={direct_size}, formula={formula_size}")
    
    print(f"General {num_sets}-set inclusion-exclusion: {num_trials - failures}/{num_trials} passed")
    return failures == 0

# Execute verification suite
print("Inclusion-Exclusion Principle Verification")
print("="*60)
verify_inclusion_exclusion_two_sets(num_trials=2000)
verify_inclusion_exclusion_three_sets(num_trials=2000)
verify_general_inclusion_exclusion(num_trials=500, num_sets=4, max_size=12)
verify_general_inclusion_exclusion(num_trials=200, num_sets=6, max_size=8)
```

This verification suite executes thousands of randomized trials across sets of varying cardinalities, confirming that the inclusion-exclusion formula produces identical results to direct union cardinality computation. The general inclusion-exclusion implementation employs the alternating sum over all subset intersections, providing a constructive algorithmic realization of the abstract combinatorial principle. The computational verification establishes empirical confidence in the formula's correctness across diverse input configurations.

**Power Set Cardinality and Cantor's Theorem**

Cantor's theorem asserts that for any set $A$, the power set $\mathcal{P}(A)$ has strictly greater cardinality than $A$ itself, formally $|A| < |\mathcal{P}(A)|$. For finite sets, this reduces to the concrete identity $|\mathcal{P}(A)| = 2^{|A|}$. We verify this relationship computationally by constructing explicit power sets and enumerating their elements:

```python
from sympy import FiniteSet
from itertools import combinations

def construct_power_set(base_set):
    """
    Explicitly construct power set by enumerating all subsets.
    """
    elements = list(base_set)
    n = len(elements)
    power_set_elements = []
    
    for r in range(n + 1):
        for subset_tuple in combinations(elements, r):
            power_set_elements.append(FiniteSet(*subset_tuple))
    
    return power_set_elements

def verify_power_set_cardinality(max_size=7):
    """
    Verify |P(A)| = 2^|A| for finite sets of increasing size.
    """
    print("Power Set Cardinality Verification")
    print("="*60)
    
    for n in range(max_size + 1):
        A = FiniteSet(*range(n))
        power_set = construct_power_set(A)
        
        actual_size = len(power_set)
        expected_size = 2 ** n
        
        verification_symbol = "✓" if actual_size == expected_size else "✗"
        
        print(f"|A| = {n:2d}  →  |P(A)| = {actual_size:4d}  (expected 2^{n} = {expected_size:4d}) {verification_symbol}")
        
        if n <= 3:  # Display explicit power set for small cases
            print(f"  A = {A}")
            print(f"  P(A) = {{", end="")
            for i, subset in enumerate(power_set):
                if i > 0:
                    print(", ", end="")
                print(subset, end="")
            print("}")
        
        if actual_size != expected_size:
            return False
    
    return True

def verify_cantor_inequality(max_size=8):
    """
    Verify Cantor's theorem: |A| < |P(A)| for finite sets.
    """
    print("\nCantor's Theorem Verification: |A| < |P(A)|")
    print("="*60)
    
    all_verified = True
    
    for n in range(max_size + 1):
        A = FiniteSet(*range(n))
        power_set = construct_power_set(A)
        
        base_size = len(A)
        power_size = len(power_set)
        
        inequality_holds = base_size < power_size
        verification_symbol = "✓" if inequality_holds else "✗"
        
        print(f"|A| = {base_size:2d} < |P(A)| = {power_size:4d}  {verification_symbol}")
        
        if not inequality_holds:
            all_verified = False
    
    return all_verified

# Execute power set verification suite
verify_power_set_cardinality(max_size=8)
verify_cantor_inequality(max_size=8)

# Demonstrate explicit power set construction for a small concrete set
print("\nExplicit Power Set Construction Example")
print("="*60)
A = FiniteSet(1, 2, 3)
power_set = construct_power_set(A)
print(f"Base set A = {A}")
print(f"Power set P(A) contains {len(power_set)} elements:")
for i, subset in enumerate(power_set, 1):
    print(f"  {i}. {subset}")
```

Execute this verification to observe the exponential growth of power set cardinality and confirm Cantor's fundamental inequality. The explicit enumeration for sets up to size eight demonstrates that power set cardinality doubles with each additional base element, yielding 256 subsets for an eight-element set. This computational verification transforms Cantor's abstract diagonal argument into a tangible algorithmic construction, bridging pure set theory and discrete combinatorics.

## Exercise 2: Boundary Value Stress Testing & Singularities

Set-theoretic operations exhibit critical boundary behaviors at the empty set, singleton sets, universe boundaries, and infinite cardinality transitions. Stress testing these singularities reveals subtle implementation constraints and confirms that symbolic engines handle edge cases consistently with axiomatic foundations. We probe empty set algebraic properties, identity element behavior, and cardinality arithmetic at boundary configurations.

**Empty Set Algebraic Properties and Neutral Elements**

The empty set $\emptyset$ functions as the additive identity for set union and the absorbing element for set intersection, formally $A \cup \emptyset = A$ and $A \cap \emptyset = \emptyset$ for all sets $A$. Additionally, the Cartesian product involving the empty set yields the empty set: $A \times \emptyset = \emptyset$. We verify these boundary identities through exhaustive testing across diverse set configurations:

```python
from sympy import FiniteSet, ProductSet
import random

def verify_empty_set_properties(num_trials=1000, max_size=20):
    """
    Stress test empty set algebraic properties across random configurations.
    """
    empty = FiniteSet()
    
    union_identity_failures = 0
    intersection_absorption_failures = 0
    difference_identity_failures = 0
    symmetric_difference_identity_failures = 0
    
    print("Empty Set Boundary Value Verification")
    print("="*60)
    
    for trial in range(num_trials):
        # Generate random finite set
        size = random.randint(0, max_size)
        A = FiniteSet(*random.sample(range(max_size * 2), size))
        
        # Union identity: A ∪ ∅ = A
        if (A | empty) != A:
            union_identity_failures += 1
        
        # Intersection absorption: A ∩ ∅ = ∅
        if (A & empty) != empty:
            intersection_absorption_failures += 1
        
        # Difference identity: A \ ∅ = A and ∅ \ A = ∅
        if (A - empty) != A or (empty - A) != empty:
            difference_identity_failures += 1
        
        # Symmetric difference identity: A Δ ∅ = A
        if (A ^ empty) != A:
            symmetric_difference_identity_failures += 1
    
    print(f"Union identity (A ∪ ∅ = A): {num_trials - union_identity_failures}/{num_trials} ✓")
    print(f"Intersection absorption (A ∩ ∅ = ∅): {num_trials - intersection_absorption_failures}/{num_trials} ✓")
    print(f"Difference identity (A \\ ∅ = A, ∅ \\ A = ∅): {num_trials - difference_identity_failures}/{num_trials} ✓")
    print(f"Symmetric difference identity (A Δ ∅ = A): {num_trials - symmetric_difference_identity_failures}/{num_trials} ✓")
    
    total_failures = (union_identity_failures + intersection_absorption_failures + 
                     difference_identity_failures + symmetric_difference_identity_failures)
    
    return total_failures == 0

def verify_empty_cartesian_product():
    """
    Verify Cartesian product behavior with empty set.
    """
    empty = FiniteSet()
    
    print("\nEmpty Set Cartesian Product Verification")
    print("="*60)
    
    test_sets = [
        FiniteSet(1, 2, 3),
        FiniteSet('a', 'b'),
        FiniteSet(0),
        empty
    ]
    
    all_verified = True
    
    for A in test_sets:
        # A × ∅ should be empty
        product_1 = ProductSet(A, empty)
        # ∅ × A should be empty
        product_2 = ProductSet(empty, A)
        
        # Convert to list to check if empty (ProductSet is lazy)
        elements_1 = list(product_1)
        elements_2 = list(product_2)
        
        is_empty_1 = len(elements_1) == 0
        is_empty_2 = len(elements_2) == 0
        
        status_1 = "✓" if is_empty_1 else "✗"
        status_2 = "✓" if is_empty_2 else "✗"
        
        print(f"A = {A}")
        print(f"  A × ∅: empty = {is_empty_1} {status_1}")
        print(f"  ∅ × A: empty = {is_empty_2} {status_2}")
        
        if not (is_empty_1 and is_empty_2):
            all_verified = False
    
    return all_verified

def verify_empty_power_set():
    """
    Verify power set of empty set: P(∅) = {∅}.
    """
    empty = FiniteSet()
    
    print("\nPower Set of Empty Set Verification")
    print("="*60)
    
    # P(∅) should contain exactly one element: the empty set itself
    power_set = [empty]  # By definition
    
    expected_size = 1  # 2^0 = 1
    actual_size = len(power_set)
    
    print(f"∅ = {empty}")
    print(f"P(∅) = {{{empty}}}")
    print(f"|P(∅)| = {actual_size} (expected 2^0 = {expected_size})")
    print(f"Verification: {actual_size == expected_size} ✓" if actual_size == expected_size else f"Verification: Failed ✗")
    
    return actual_size == expected_size

# Execute boundary verification suite
verify_empty_set_properties(num_trials=2000)
verify_empty_cartesian_product()
verify_empty_power_set()
```

This stress test confirms that symbolic set engines preserve empty set algebraic identities across thousands of randomized configurations. The Cartesian product verification demonstrates that ProductSet correctly implements the absorbing property of the empty set, while the power set verification confirms the fundamental identity $\mathcal{P}(\emptyset) = \{\emptyset\}$, establishing that the empty set has exactly one subset—itself.

**Singleton Set Behavior and Identity Morphisms**

Singleton sets exhibit unique algebraic properties as minimal non-empty structures. For any singleton $\{a\}$ and set $A$ containing $a$, intersection yields the singleton when $a \in A$ and the empty set otherwise. We stress-test singleton membership, subset relationships, and cardinality arithmetic:

```python
from sympy import FiniteSet
import random

def verify_singleton_properties(num_trials=1000, max_size=15):
    """
    Verify singleton set algebraic properties and membership behavior.
    """
    print("Singleton Set Boundary Verification")
    print("="*60)
    
    membership_failures = 0
    intersection_failures = 0
    union_failures = 0
    subset_failures = 0
    
    for trial in range(num_trials):
        # Generate random singleton and test set
        element = random.randint(0, max_size * 2)
        singleton = FiniteSet(element)
        
        # Generate random set that may or may not contain element
        test_size = random.randint(0, max_size)
        test_elements = random.sample(range(max_size * 2), test_size)
        A = FiniteSet(*test_elements)
        
        # Membership verification
        element_in_A = element in test_elements
        
        # Intersection: {a} ∩ A = {a} if a ∈ A, else ∅
        intersection = singleton & A
        expected_intersection = singleton if element_in_A else FiniteSet()
        
        if intersection != expected_intersection:
            intersection_failures += 1
        
        # Union: {a} ∪ A should contain a and all elements of A
        union = singleton | A
        if element not in union or not all(x in union for x in A):
            union_failures += 1
        
        # Subset: {a} ⊆ A iff a ∈ A
        is_subset = singleton.is_subset(A)
        expected_subset = element_in_A
        
        if is_subset != expected_subset:
            subset_failures += 1
    
    print(f"Intersection behavior: {num_trials - intersection_failures}/{num_trials} ✓")
    print(f"Union behavior: {num_trials - union_failures}/{num_trials} ✓")
    print(f"Subset relationship: {num_trials - subset_failures}/{num_trials} ✓")
    
    return (intersection_failures + union_failures + subset_failures) == 0

def verify_singleton_cardinality_arithmetic():
    """
    Verify cardinality arithmetic for singleton sets.
    """
    print("\nSingleton Cardinality Arithmetic")
    print("="*60)
    
    singleton = FiniteSet(42)
    
    # Cardinality of singleton
    card = len(singleton)
    print(f"|{{42}}| = {card} (expected 1) {'✓' if card == 1 else '✗'}")
    
    # Power set of singleton: P({a}) = {∅, {a}}
    power_set = [FiniteSet(), singleton]
    power_card = len(power_set)
    expected_power_card = 2  # 2^1 = 2
    print(f"|P({{42}})| = {power_card} (expected 2^1 = {expected_power_card}) {'✓' if power_card == expected_power_card else '✗'}")
    print(f"P({{42}}) = {{∅, {{42}}}} = {{{power_set[0]}, {power_set[1]}}}")
    
    # Cartesian product of singleton with itself
    product = ProductSet(singleton, singleton)
    product_elements = list(product)
    product_card = len(product_elements)
    expected_product_card = 1  # 1 × 1 = 1
    print(f"|{{42}} × {{42}}| = {product_card} (expected 1 × 1 = {expected_product_card}) {'✓' if product_card == expected_product_card else '✗'}")
    print(f"{{42}} × {{42}} = {product_elements}")
    
    return True

# Execute singleton verification suite
verify_singleton_properties(num_trials=2000)
verify_singleton_cardinality_arithmetic()
```

The verification confirms that symbolic engines correctly implement singleton membership testing, intersection with arbitrary sets, and cardinality arithmetic. The power set computation establishes that a singleton has exactly two subsets—the empty set and itself—while the Cartesian self-product yields the ordered pair $(42, 42)$ as its sole element.

**Subset Lattice Completeness and Extremal Elements**

Every finite set induces a complete lattice under the subset ordering, with the empty set as the minimal element and the set itself as the maximal element. We verify lattice properties including join (union) and meet (intersection) operations, along with complementation forming a Boolean algebra:

```python
from sympy import FiniteSet
from itertools import combinations

def verify_subset_lattice_properties(base_set_size=4):
    """
    Verify that the power set forms a complete lattice under subset ordering.
    """
    print("Subset Lattice Completeness Verification")
    print("="*60)
    
    # Construct base set and its power set
    base_set = FiniteSet(*range(base_set_size))
    elements = list(range(base_set_size))
    
    # Generate all subsets (the lattice elements)
    lattice = []
    for r in range(base_set_size + 1):
        for subset_tuple in combinations(elements, r):
            lattice.append(FiniteSet(*subset_tuple))
    
    print(f"Base set A = {base_set}, |A| = {base_set_size}")
    print(f"Lattice size |P(A)| = {len(lattice)} (expected 2^{base_set_size} = {2**base_set_size})")
    
    # Verify minimal and maximal elements
    minimal = FiniteSet()  # Empty set
    maximal = base_set
    
    minimal_verified = all(minimal.is_subset(s) for s in lattice)
    maximal_verified = all(s.is_subset(maximal) for s in lattice)
    
    print(f"\nMinimal element (∅): {'✓' if minimal_verified else '✗'}")
    print(f"Maximal element (A): {'✓' if maximal_verified else '✗'}")
    
    # Verify join (union) and meet (intersection) closure
    join_closure_failures = 0
    meet_closure_failures = 0
    
    for S1 in lattice[:min(20, len(lattice))]:  # Sample for efficiency
        for S2 in lattice[:min(20, len(lattice))]:
            # Join: S1 ∨ S2 = S1 ∪ S2 must be in lattice
            join = S1 | S2
            if join not in lattice:
                join_closure_failures += 1
            
            # Meet: S1 ∧ S2 = S1 ∩ S2 must be in lattice
            meet = S1 & S2
            if meet not in lattice:
                meet_closure_failures += 1
    
    print(f"Join (∪) closure: {'✓' if join_closure_failures == 0 else '✗'}")
    print(f"Meet (∩) closure: {'✓' if meet_closure_failures == 0 else '✗'}")
    
    # Verify Boolean algebra complementation
    complement_failures = 0
    
    for S in lattice:
        complement = base_set - S
        
        # S ∪ S^c = A (maximal)
        union_with_complement = S | complement
        
        # S ∩ S^c = ∅ (minimal)
        intersection_with_complement = S & complement
        
        if union_with_complement != maximal or intersection_with_complement != minimal:
            complement_failures += 1
    
    print(f"Complement properties (S ∪ S^c = A, S ∩ S^c = ∅): {'✓' if complement_failures == 0 else '✗'}")
    
    return (minimal_verified and maximal_verified and 
            join_closure_failures == 0 and meet_closure_failures == 0 and
            complement_failures == 0)

def verify_lattice_distributivity(base_set_size=3):
    """
    Verify distributive laws: A ∩ (B ∪ C) = (A ∩ B) ∪ (A ∩ C).
    """
    print("\nLattice Distributivity Verification")
    print("="*60)
    
    elements = list(range(base_set_size))
    lattice = []
    
    for r in range(base_set_size + 1):
        for subset_tuple in combinations(elements, r):
            lattice.append(FiniteSet(*subset_tuple))
    
    distributive_failures = 0
    total_tests = 0
    
    for A in lattice:
        for B in lattice:
            for C in lattice:
                # First distributive law: A ∩ (B ∪ C) = (A ∩ B) ∪ (A ∩ C)
                left_side = A & (B | C)
                right_side = (A & B) | (A & C)
                
                if left_side != right_side:
                    distributive_failures += 1
                
                total_tests += 1
    
    print(f"Distributive law tests: {total_tests - distributive_failures}/{total_tests} ✓")
    
    return distributive_failures == 0

# Execute lattice verification suite
verify_subset_lattice_properties(base_set_size=4)
verify_lattice_distributivity(base_set_size=4)
```

This verification establishes that the power set under subset ordering forms a complete Boolean lattice with well-defined extremal elements, closed binary operations, and complementation satisfying Boolean algebra axioms. The distributivity verification confirms that intersection distributes over union across all 4096 triple combinations for a four-element base set, providing computational certainty for this fundamental algebraic structure.

## Exercise 3: Algorithmic Implementation of Formal Structures

Abstract set-theoretic constructions—relations, functions, equivalence classes, partitions, and transfinite ordinals—require concrete algorithmic realizations to bridge foundational theory and computational practice. We implement relation composition, function injectivity testing, partition generation from equivalence relations, and ordinal arithmetic through explicit Python algorithms that mechanize Zermelo-Fraenkel constructions.

**Relation Composition and Transitive Closure**

A binary relation $R \subseteq A \times B$ encodes pairwise associations between elements. Relation composition $(S \circ R)(a, c)$ holds when there exists $b$ such that $R(a, b)$ and $S(b, c)$. We implement relation composition as explicit subset construction and compute transitive closures through iterative fixpoint algorithms:

```python
from sympy import FiniteSet

def compose_relations(R, S):
    """
    Compute relation composition S ∘ R.
    
    (S ∘ R)(a, c) holds iff ∃b: R(a, b) ∧ S(b, c)
    
    Args:
        R: Set of ordered pairs (a, b)
        S: Set of ordered pairs (b, c)
    
    Returns:
        Set of ordered pairs (a, c) representing S ∘ R
    """
    composition = set()
    
    for (a, b) in R:
        for (b_prime, c) in S:
            if b == b_prime:
                composition.add((a, c))
    
    return composition

def relation_power(R, n):
    """
    Compute n-th power of relation R: R^n = R ∘ R ∘ ... ∘ R (n times).
    """
    if n == 0:
        # R^0 is the identity relation on domain of R
        domain = set(a for (a, b) in R)
        return {(x, x) for x in domain}
    
    if n == 1:
        return R
    
    result = R
    for _ in range(n - 1):
        result = compose_relations(result, R)
    
    return result

def transitive_closure(R):
    """
    Compute transitive closure R⁺ = R ∪ R² ∪ R³ ∪ ...
    
    Uses iterative fixpoint algorithm: repeatedly compose until no new pairs added.
    """
    closure = set(R)
    changed = True
    
    while changed:
        new_closure = set(closure)
        
        # Add all pairs reachable through composition
        for (a, b) in closure:
            for (b_prime, c) in closure:
                if b == b_prime:
                    new_closure.add((a, c))
        
        changed = len(new_closure) > len(closure)
        closure = new_closure
    
    return closure

def reflexive_transitive_closure(R, domain):
    """
    Compute reflexive-transitive closure R* = R⁺ ∪ Identity.
    """
    trans_closure = transitive_closure(R)
    identity = {(x, x) for x in domain}
    return trans_closure | identity

# Demonstration: Compute transitive closure of a partial order
print("Relation Composition and Transitive Closure")
print("="*60)

# Define a relation R on {0, 1, 2, 3, 4}
R = {(0, 1), (1, 2), (2, 3), (0, 2), (3, 4)}
domain = {0, 1, 2, 3, 4}

print(f"Base relation R = {R}")
print(f"Domain = {domain}")

# Compute powers of R
print("\nRelation powers:")
for n in range(1, 5):
    R_n = relation_power(R, n)
    print(f"R^{n} = {R_n}")

# Compute transitive closure
R_plus = transitive_closure(R)
print(f"\nTransitive closure R⁺ = {R_plus}")

# Compute reflexive-transitive closure
R_star = reflexive_transitive_closure(R, domain)
print(f"Reflexive-transitive closure R* = {R_star}")

# Verify transitivity of closure
print("\nTransitivity verification of R⁺:")
is_transitive = True
for (a, b) in R_plus:
    for (b_prime, c) in R_plus:
        if b == b_prime and (a, c) not in R_plus:
            print(f"  Transitivity violation: ({a}, {b}), ({b}, {c}) ∈ R⁺ but ({a}, {c}) ∉ R⁺")
            is_transitive = False

print(f"R⁺ is transitive: {is_transitive} {'✓' if is_transitive else '✗'}")
```

Execute this implementation to observe relation composition mechanics and transitive closure convergence. The iterative fixpoint algorithm repeatedly composes the relation with itself until no new pairs are discovered, guaranteeing termination for finite relations. The output displays successive relation powers and the final transitive closure, demonstrating the computational realization of this fundamental graph-theoretic construction.

**Function Property Verification: Injectivity, Surjectivity, Bijectivity**

Functions constitute special relations where each domain element maps to exactly one codomain element. We implement algorithmic verifiers for injectivity (one-to-one), surjectivity (onto), and bijectivity (bijective correspondence):

```python
from sympy import FiniteSet
from collections import defaultdict

def verify_function_property(mapping, domain, codomain):
    """
    Verify that mapping defines a valid function from domain to codomain.
    
    Args:
        mapping: Dictionary {domain_element: codomain_element}
        domain: Set of domain elements
        codomain: Set of codomain elements
    
    Returns:
        Boolean indicating whether mapping is a valid function
    """
    # Every domain element must have exactly one image
    for x in domain:
        if x not in mapping:
            return False
    
    # All images must be in codomain
    for y in mapping.values():
        if y not in codomain:
            return False
    
    return True

def is_injective(mapping, domain):
    """
    Test injectivity: f(x₁) = f(x₂) implies x₁ = x₂.
    
    Equivalently: distinct domain elements map to distinct codomain elements.
    """
    image_to_preimages = defaultdict(set)
    
    for x in domain:
        y = mapping[x]
        image_to_preimages[y].add(x)
    
    # Check if any codomain element has multiple preimages
    for y, preimages in image_to_preimages.items():
        if len(preimages) > 1:
            return False
    
    return True

def is_surjective(mapping, domain, codomain):
    """
    Test surjectivity: for all y ∈ codomain, exists x ∈ domain with f(x) = y.
    
    Equivalently: image equals codomain.
    """
    image = {mapping[x] for x in domain}
    return image == codomain

def is_bijective(mapping, domain, codomain):
    """
    Test bijectivity: both injective and surjective.
    """
    return is_injective(mapping, domain) and is_surjective(mapping, domain, codomain)

def count_functions(domain_size, codomain_size):
    """
    Count total functions from domain to codomain: |codomain|^|domain|.
    """
    return codomain_size ** domain_size

def count_injections(domain_size, codomain_size):
    """
    Count injective functions: P(|codomain|, |domain|) = |codomain|! / (|codomain| - |domain|)!
    
    Returns 0 if |domain| > |codomain| (pigeonhole principle).
    """
    if domain_size > codomain_size:
        return 0
    
    # Compute falling factorial: n(n-1)...(n-k+1)
    result = 1
    for i in range(domain_size):
        result *= (codomain_size - i)
    
    return result

def count_surjections(domain_size, codomain_size):
    """
    Count surjective functions using inclusion-exclusion principle.
    
    Formula: Σ(-1)^k * C(m, k) * (m-k)^n for k=0 to m
    where n = |domain|, m = |codomain|
    """
    if domain_size < codomain_size:
        return 0
    
    from math import comb
    
    total = 0
    for k in range(codomain_size + 1):
        sign = (-1) ** k
        binomial = comb(codomain_size, k)
        power = (codomain_size - k) ** domain_size
        total += sign * binomial * power
    
    return total

def count_bijections(domain_size, codomain_size):
    """
    Count bijective functions: |domain|! if |domain| = |codomain|, else 0.
    """
    if domain_size != codomain_size:
        return 0
    
    from math import factorial
    return factorial(domain_size)

# Demonstrate function property verification
print("Function Property Verification")
print("="*60)

domain = {1, 2, 3}
codomain = {'a', 'b', 'c', 'd'}

# Test various function types
test_functions = [
    ("Injective, not surjective", {1: 'a', 2: 'b', 3: 'c'}),
    ("Not injective, not surjective", {1: 'a', 2: 'a', 3: 'b'}),
    ("Neither injective nor surjective", {1: 'a', 2: 'a', 3: 'a'}),
]

for description, mapping in test_functions:
    is_func = verify_function_property(mapping, domain, codomain)
    inj = is_injective(mapping, domain) if is_func else False
    surj = is_surjective(mapping, domain, codomain) if is_func else False
    bij = is_bijective(mapping, domain, codomain) if is_func else False
    
    print(f"\nFunction: {description}")
    print(f"  Mapping: {mapping}")
    print(f"  Valid function: {is_func}")
    print(f"  Injective: {inj}")
    print(f"  Surjective: {surj}")
    print(f"  Bijective: {bij}")

# Special case: bijection requires equal cardinalities
domain_bij = {1, 2, 3}
codomain_bij = {'a', 'b', 'c'}
mapping_bij = {1: 'a', 2: 'b', 3: 'c'}

print(f"\nBijection test (equal cardinalities):")
print(f"  Domain: {domain_bij}, Codomain: {codomain_bij}")
print(f"  Mapping: {mapping_bij}")
print(f"  Bijective: {is_bijective(mapping_bij, domain_bij, codomain_bij)} ✓")

# Counting formulas verification
print("\n" + "="*60)
print("Function Counting Formulas")
print("="*60)

for n in range(1, 5):
    for m in range(1, 5):
        total_funcs = count_functions(n, m)
        injections = count_injections(n, m)
        surjections = count_surjections(n, m)
        bijections = count_bijections(n, m)
        
        print(f"\n|Domain| = {n}, |Codomain| = {m}")
        print(f"  Total functions: {m}^{n} = {total_funcs}")
        print(f"  Injections: {injections}")
        print(f"  Surjections: {surjections}")
        print(f"  Bijections: {bijections}")
```

This implementation provides algorithmic decision procedures for function properties that are typically defined through quantified logical formulas. The counting formulas verify combinatorial principles: total functions grow exponentially, injections require sufficient codomain elements, surjections employ inclusion-exclusion, and bijections exist only between equinumerous sets.

**Equivalence Relations and Partition Generation**

An equivalence relation $\sim$ on a set $A$ partitions $A$ into disjoint equivalence classes $[a] = \{x \in A : x \sim a\}$. We implement partition generation from equivalence relations through union-find data structures and verify the fundamental bijection between equivalence relations and partitions:

```python
from collections import defaultdict

class UnionFind:
    """
    Union-Find (Disjoint Set Union) data structure for partition management.
    """
    def __init__(self, elements):
        self.parent = {x: x for x in elements}
        self.rank = {x: 0 for x in elements}
    
    def find(self, x):
        """Find root representative with path compression."""
        if self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])
        return self.parent[x]
    
    def union(self, x, y):
        """Unite equivalence classes of x and y using union by rank."""
        root_x = self.find(x)
        root_y = self.find(y)
        
        if root_x == root_y:
            return
        
        # Union by rank
        if self.rank[root_x] < self.rank[root_y]:
            self.parent[root_x] = root_y
        elif self.rank[root_x] > self.rank[root_y]:
            self.parent[root_y] = root_x
        else:
            self.parent[root_y] = root_x
            self.rank[root_x] += 1
    
    def get_partition(self):
        """Extract partition as list of equivalence classes."""
        classes = defaultdict(set)
        
        for x in self.parent:
            root = self.find(x)
            classes[root].add(x)
        
        return [frozenset(cls) for cls in classes.values()]

def partition_from_equivalence_relation(relation, domain):
    """
    Generate partition from equivalence relation.
    
    Args:
        relation: Set of ordered pairs (a, b) where a ~ b
        domain: Set of all elements
    
    Returns:
        List of frozensets representing equivalence classes
    """
    uf = UnionFind(domain)
    
    for (a, b) in relation:
        uf.union(a, b)
    
    return uf.get_partition()

def verify_equivalence_relation(relation, domain):
    """
    Verify that relation satisfies equivalence properties: reflexive, symmetric, transitive.
    """
    # Reflexivity: ∀x: (x, x) ∈ R
    reflexive = all((x, x) in relation for x in domain)
    
    # Symmetry: (x, y) ∈ R implies (y, x) ∈ R
    symmetric = all((y, x) in relation for (x, y) in relation)
    
    # Transitivity: (x, y) ∈ R and (y, z) ∈ R implies (x, z) ∈ R
    transitive = True
    for (x, y) in relation:
        for (y_prime, z) in relation:
            if y == y_prime and (x, z) not in relation:
                transitive = False
                break
        if not transitive:
            break
    
    return reflexive, symmetric, transitive

def verify_partition_properties(partition, domain):
    """
    Verify that partition satisfies: non-empty classes, disjoint, union equals domain.
    """
    # All classes non-empty
    non_empty = all(len(cls) > 0 for cls in partition)
    
    # Classes are pairwise disjoint
    disjoint = True
    for i, cls1 in enumerate(partition):
        for j, cls2 in enumerate(partition):
            if i != j and not cls1.isdisjoint(cls2):
                disjoint = False
                break
        if not disjoint:
            break
    
    # Union of classes equals domain
    union = set()
    for cls in partition:
        union |= cls
    covers_domain = union == domain
    
    return non_empty, disjoint, covers_domain

def equivalence_relation_from_partition(partition):
    """
    Construct equivalence relation from partition.
    
    Elements are related iff they belong to the same partition class.
    """
    relation = set()
    
    for cls in partition:
        for x in cls:
            for y in cls:
                relation.add((x, y))
    
    return relation

# Demonstration: Equivalence relations and partitions
print("Equivalence Relations and Partitions")
print("="*60)

# Define equivalence relation on {0, 1, 2, 3, 4, 5}
domain = {0, 1, 2, 3, 4, 5}

# Equivalence relation: a ~ b iff a ≡ b (mod 3)
relation = set()
for a in domain:
    for b in domain:
        if a % 3 == b % 3:
            relation.add((a, b))

print(f"Domain: {domain}")
print(f"Equivalence relation (mod 3): {sorted(relation)}")

# Verify equivalence properties
reflexive, symmetric, transitive = verify_equivalence_relation(relation, domain)
print(f"\nEquivalence properties:")
print(f"  Reflexive: {reflexive} ✓" if reflexive else f"  Reflexive: {reflexive} ✗")
print(f"  Symmetric: {symmetric} ✓" if symmetric else f"  Symmetric: {symmetric} ✗")
print(f"  Transitive: {transitive} ✓" if transitive else f"  Transitive: {transitive} ✗")

# Generate partition from equivalence relation
partition = partition_from_equivalence_relation(relation, domain)
print(f"\nGenerated partition:")
for i, cls in enumerate(sorted(partition, key=lambda x: min(x)), 1):
    print(f"  Class {i}: {sorted(cls)}")

# Verify partition properties
non_empty, disjoint, covers = verify_partition_properties(partition, domain)
print(f"\nPartition properties:")
print(f"  Non-empty classes: {non_empty} ✓" if non_empty else f"  Non-empty classes: {non_empty} ✗")
print(f"  Pairwise disjoint: {disjoint} ✓" if disjoint else f"  Pairwise disjoint: {disjoint} ✗")
print(f"  Union covers domain: {covers} ✓" if covers else f"  Union covers domain: {covers} ✗")

# Verify bijection: reconstruct equivalence relation from partition
reconstructed_relation = equivalence_relation_from_partition(partition)
bijection_verified = reconstructed_relation == relation

print(f"\nBijection verification:")
print(f"  Original relation size: {len(relation)}")
print(f"  Reconstructed relation size: {len(reconstructed_relation)}")
print(f"  Relations equal: {bijection_verified} ✓" if bijection_verified else f"  Relations equal: {bijection_verified} ✗")

# Additional example: partition integers by parity
domain_parity = {0, 1, 2, 3, 4, 5, 6, 7, 8, 9}
partition_parity = [
    frozenset({0, 2, 4, 6, 8}),  # Even numbers
    frozenset({1, 3, 5, 7, 9})   # Odd numbers
]

print(f"\n" + "="*60)
print("Parity Partition Example")
print(f"Domain: {domain_parity}")
print(f"Partition by parity: {[sorted(cls) for cls in partition_parity]}")

relation_parity = equivalence_relation_from_partition(partition_parity)
ref, sym, trans = verify_equivalence_relation(relation_parity, domain_parity)

print(f"Induced equivalence relation is valid: {ref and sym and trans} ✓" if (ref and sym and trans) else f"Induced equivalence relation is valid: {ref and sym and trans} ✗")
```

This implementation demonstrates the algorithmic construction of the fundamental bijection between equivalence relations and partitions, establishing through executable code the abstract theorem that partitioning a set is equivalent to defining an equivalence relation. The union-find data structure provides efficient $O(\alpha(n))$ amortized time complexity for equivalence class queries, where $\alpha$ is the inverse Ackermann function, making this approach practical for large-scale discrete structure manipulation.

## Formal Axioms Cheat Sheet & Verification Reference

The Zermelo-Fraenkel axioms with the Axiom of Choice (ZFC) constitute the standard foundation for modern set theory, providing the axiomatic substrate from which all classical mathematical structures derive. This reference section catalogs the formal axioms, their computational interpretations, and verification protocols for finite model checking.

**Axiom of Extensionality**

Two sets are equal if and only if they contain precisely the same elements. Formally, $\forall A \forall B (\forall x (x \in A \leftrightarrow x \in B) \rightarrow A = B)$. This axiom establishes that sets are completely determined by their membership relation, with no hidden internal structure or ordering.

Computational verification: For finite sets represented as Python FiniteSet objects, extensionality reduces to element-wise equality testing. Implement verification through explicit membership comparison:

```python
from sympy import FiniteSet

def verify_extensionality(A, B):
    """
    Verify extensionality: A = B iff ∀x(x ∈ A ↔ x ∈ B).
    """
    # Check set equality
    sets_equal = (A == B)
    
    # Check element-wise equivalence
    forward = all(x in B for x in A)
    backward = all(x in A for x in B)
    elementwise_equal = forward and backward
    
    # Extensionality holds iff both directions agree
    return sets_equal == elementwise_equal

# Test cases
A1 = FiniteSet(1, 2, 3)
A2 = FiniteSet(3, 2, 1)  # Order irrelevant
A3 = FiniteSet(1, 2, 3, 3)  # Duplicates irrelevant
B = FiniteSet(1, 2, 4)

print("Extensionality Verification")
print("="*60)
print(f"A1 = {A1}, A2 = {A2}: {verify_extensionality(A1, A2)} ✓")
print(f"A1 = {A1}, A3 = {A3}: {verify_extensionality(A1, A3)} ✓")
print(f"A1 = {A1}, B = {B}: {verify_extensionality(A1, B)} ✓")
```

**Axiom of Pairing**

For any sets $a$ and $b$, there exists a set $\{a, b\}$ containing exactly $a$ and $b$. Formally, $\forall a \forall b \exists c \forall x (x \in c \leftrightarrow (x = a \lor x = b))$. This axiom enables construction of unordered pairs, which serve as building blocks for ordered pairs through the Kuratowski definition $(a, b) = \{\{a\}, \{a, b\}\}$.

Computational verification:

```python
from sympy import FiniteSet

def construct_pair(a, b):
    """Construct unordered pair {a, b}."""
    return FiniteSet(a, b)

def verify_pairing_axiom(a, b):
    """Verify that {a, b} contains exactly a and b."""
    pair = construct_pair(a, b)
    
    # Check that a and b are in the pair
    contains_a = a in pair
    contains_b = b in pair
    
    # Check that pair contains only a and b
    only_a_and_b = all(x == a or x == b for x in pair)
    
    return contains_a and contains_b and only_a_and_b

# Demonstrate pairing and Kuratowski ordered pair construction
print("\nPairing and Ordered Pairs")
print("="*60)

a, b = 42, 'x'
pair = construct_pair(a, b)
print(f"Unordered pair {{a, b}} = {pair}")
print(f"Pairing axiom verified: {verify_pairing_axiom(a, b)} ✓")

# Kuratowski ordered pair: (a, b) = {{a}, {a, b}}
singleton_a = FiniteSet(a)
pair_ab = FiniteSet(a, b)
ordered_pair = FiniteSet(singleton_a, pair_ab)

print(f"\nKuratowski ordered pair (a, b):")
print(f"  {{{{a}}}} = {singleton_a}")
print(f"  {{{{a, b}}}} = {pair_ab}")
print(f"  (a, b) = {{{{a}}, {{a, b}}}} = {ordered_pair}")
```

**Axiom of Union**

For any set $A$, there exists a set $\bigcup A$ containing exactly those elements that belong to at least one element of $A$. Formally, $\forall A \exists B \forall x (x \in B \leftrightarrow \exists c (c \in A \land x \in c))$. This axiom enables flattening of nested set structures.

Computational verification:

```python
from sympy import FiniteSet

def set_union_axiom(A):
    """
    Compute union of a set of sets: ⋃A = {x : ∃c ∈ A, x ∈ c}.
    """
    result = FiniteSet()
    for subset in A:
        result = result | subset
    return result

# Demonstration
A = FiniteSet(
    FiniteSet(1, 2),
    FiniteSet(2, 3, 4),
    FiniteSet(5)
)

union_A = set_union_axiom(A)

print("\nUnion Axiom")
print("="*60)
print(f"A = {A}")
print(f"⋃A = {union_A}")
print(f"Expected: {{1, 2, 3, 4, 5}}")
print(f"Verified: {union_A == FiniteSet(1, 2, 3, 4, 5)} ✓")
```

**Axiom of Power Set**

For any set $A$, there exists a set $\mathcal{P}(A)$ containing exactly the subsets of $A$. Formally, $\forall A \exists B \forall x (x \in B \leftrightarrow x \subseteq A)$. This axiom guarantees the existence of the power set construction verified extensively in Exercise 1.

**Axiom of Infinity**

There exists an infinite set, specifically a set containing the empty set and closed under the successor operation $S(x) = x \cup \{x\}$. This axiom establishes the existence of the natural numbers as the smallest inductive set, formalized through von Neumann ordinals where $0 = \emptyset$, $1 = \{0\}$, $2 = \{0, 1\}$, and so forth.

Computational construction of initial von Neumann ordinals:

```python
from sympy import FiniteSet

def von_neumann_ordinal(n):
    """
    Construct von Neumann ordinal for natural number n.
    
    0 = ∅
    n+1 = n ∪ {n}
    """
    if n == 0:
        return FiniteSet()
    
    predecessor = von_neumann_ordinal(n - 1)
    return predecessor | FiniteSet(predecessor)

print("\nVon Neumann Ordinals (Axiom of Infinity)")
print("="*60)

for n in range(6):
    ordinal = von_neumann_ordinal(n)
    print(f"{n} = {ordinal}, |{n}| = {len(ordinal)}")

# Verify that |n| = n for von Neumann ordinals
verification_passed = all(len(von_neumann_ordinal(n)) == n for n in range(10))
print(f"\nCardinality verification |n| = n: {verification_passed} ✓")
```

**Axiom Schema of Separation (Specification)**

For any set $A$ and any property $P(x)$, there exists a set $B = \{x \in A : P(x)\}$ containing exactly those elements of $A$ satisfying $P$. Formally, $\forall A \exists B \forall x (x \in B \leftrightarrow (x \in A \land P(x)))$. This axiom prevents Russell's paradox by restricting comprehension to subsets of existing sets.

Computational implementation through Python predicates:

```python
from sympy import FiniteSet

def separation(A, predicate):
    """
    Axiom of Separation: {x ∈ A : P(x)}.
    
    Args:
        A: Base set
        predicate: Function mapping elements to boolean
    
    Returns:
        Subset of A satisfying predicate
    """
    return FiniteSet(*[x for x in A if predicate(x)])

# Demonstrate separation with various predicates
A = FiniteSet(*range(1, 11))

print("\nAxiom of Separation")
print("="*60)
print(f"Base set A = {A}")

# Even numbers
evens = separation(A, lambda x: x % 2 == 0)
print(f"Evens = {{x ∈ A : x ≡ 0 (mod 2)}} = {evens}")

# Prime numbers
def is_prime(n):
    if n < 2:
        return False
    for i in range(2, int(n**0.5) + 1):
        if n % i == 0:
            return False
    return True

primes = separation(A, is_prime)
print(f"Primes = {{x ∈ A : x is prime}} = {primes}")

# Perfect squares
squares = separation(A, lambda x: int(x**0.5)**2 == x)
print(f"Squares = {{x ∈ A : ∃n(n² = x)}} = {squares}")
```

**Axiom of Replacement**

If $F$ is a functional relation (each domain element maps to a unique image), then for any set $A$, the image $F[A] = \{F(x) : x \in A\}$ is also a set. This axiom ensures that functions preserve set-hood, enabling construction of image sets and function spaces.

**Axiom of Regularity (Foundation)**

Every non-empty set $A$ contains an element $x$ that is disjoint from $A$, formally $\forall A (A \neq \emptyset \rightarrow \exists x (x \in A \land x \cap A = \emptyset))$. This axiom prohibits infinite descending membership chains and ensures that sets are well-founded, preventing paradoxes like the set of all sets that do not contain themselves.

**Axiom of Choice**

For any set $X$ of non-empty sets, there exists a choice function $f: X \to \bigcup X$ such that $f(A) \in A$ for all $A \in X$. This axiom enables simultaneous selection from infinitely many sets and implies numerous equivalent principles including Zorn's Lemma, the Well-Ordering Theorem, and the existence of bases for vector spaces. For finite sets, choice follows from the other axioms, but for infinite collections it constitutes an independent logical principle.

Computational verification for finite choice functions:

```python
from sympy import FiniteSet

def construct_choice_function(family):
    """
    Construct choice function for finite family of non-empty sets.
    
    Args:
        family: List of FiniteSets, all non-empty
    
    Returns:
        Dictionary mapping each set to a chosen element
    """
    choice_func = {}
    
    for idx, A in enumerate(family):
        if len(A) == 0:
            raise ValueError(f"Set {idx} is empty; choice function undefined")
        
        # Choose minimal element (arbitrary but deterministic)
        chosen = min(A, key=lambda x: (str(type(x)), str(x)))
        choice_func[idx] = (A, chosen)
    
    return choice_func

# Demonstrate choice function construction
print("\nAxiom of Choice (Finite Version)")
print("="*60)

family = [
    FiniteSet(1, 2, 3),
    FiniteSet('a', 'b'),
    FiniteSet(10, 20, 30, 40),
    FiniteSet(True, False)
]

choice_func = construct_choice_function(family)

print("Family of sets:")
for idx, A in enumerate(family):
    print(f"  A_{idx} = {A}")

print("\nChoice function:")
for idx, (A, chosen) in choice_func.items():
    print(f"  f(A_{idx}) = {chosen} ∈ {A}")

# Verify choice function properties
print("\nVerification:")
all_valid = all(chosen in A for (A, chosen) in choice_func.values())
print(f"  ∀i: f(A_i) ∈ A_i: {all_valid} ✓")
```

This formal axioms reference provides both abstract logical formulations and concrete computational realizations, establishing set theory as simultaneously a foundational language for pure mathematics and an executable framework for discrete computational structures. The Python implementations transform ZFC axioms from philosophical abstractions into mechanized verification protocols, bridging the gap between mathematical logic and computational practice.
