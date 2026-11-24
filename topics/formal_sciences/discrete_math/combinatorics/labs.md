# Operational Verification Labs: Combinatorics

## Objective & Mathematical Computing Setup

Combinatorics sits at the intersection of counting, structure, and optimization. While classical combinatorial results appear straightforward—permutations, combinations, recurrence relations—their computational verification demands precision in symbolic manipulation, algorithmic implementation, and formal reasoning about discrete structures. This laboratory sequence transforms abstract combinatorial theorems into executable verification protocols, stress-testing boundary conditions where naive implementations fail and symbolic computation engines reveal hidden algebraic structure.

The operational environment requires Python 3.11 or later with SymPy for symbolic computation, NumPy for numerical array operations, and SageMath for advanced combinatorial structures including posets, integer partitions, and generating function manipulations. Proof assistant integration through Lean 4 provides formal verification of non-trivial combinatorial identities that resist purely computational approaches. Each exercise targets a specific verification modality: computational theorem checking through exhaustive enumeration and symbolic algebra, boundary stress testing where integer overflow and combinatorial explosion expose implementation weaknesses, and algorithmic implementation of formal structures like graph automorphisms and lattice orderings.

Install the core verification stack by executing `pip install sympy numpy matplotlib scipy` in a clean Python virtual environment. For SageMath integration, download the complete distribution from sagemath.org or run the Docker container `docker pull sagemath/sagemath` and launch with `docker run -it sagemath/sagemath`. Verify installation integrity by running `python -c 'import sympy; print(sympy.__version__)'` which should return version 1.12 or later, and `sage --version` for SageMath 10.0+. The Lean 4 proof assistant requires separate installation via `curl https://raw.githubusercontent.com/leanprover/elan/master/elan-init.sh -sSf | sh` followed by `lake new CombinatoricsVerification` to initialize a project workspace.

Combinatorial verification differs fundamentally from numerical analysis. Floating-point arithmetic introduces rounding errors that corrupt exact counting results; combinatorial objects demand exact integer arithmetic and symbolic representation. A binomial coefficient $\binom{50}{25}$ equals exactly $126410606437752$ without approximation. Generating functions encode infinite sequences as formal power series, enabling algebraic manipulation of recurrence relations through differentiation and substitution. The exponential generating function for derangements $D_n$ (permutations with no fixed points) is $\frac{e^{-x}}{1-x} = \sum_{n=0}^\infty D_n \frac{x^n}{n!}$, from which we extract $D_n = n! \sum_{k=0}^n \frac{(-1)^k}{k!}$ through coefficient extraction and series inversion.

The verification philosophy prioritizes constructive proof over existential claims. When proving the existence of a combinatorial object—a Hamiltonian cycle in a graph, a Latin square of order $n$, a block design with prescribed parameters—we provide an explicit construction algorithm or a symbolic existence proof verifiable by automated theorem provers. Boundary testing targets the transition regions where combinatorial formulas break: negative arguments to binomial coefficients, empty structures, and asymptotic regimes where Stirling approximations dominate exact formulas. Each exercise concludes with formal verification checkpoints, executable Python functions or Lean lemmas that encode mathematical invariants as machine-checkable propositions.

## Exercise 1: Computational Verification of Core Theorems

The Binomial Theorem asserts that $(x+y)^n = \sum_{k=0}^n \binom{n}{k} x^k y^{n-k}$ for non-negative integers $n$. This identity unifies Pascal's triangle, polynomial expansion, and probability mass functions. Computational verification proceeds through three strategies: direct polynomial expansion and coefficient comparison, symbolic differentiation to isolate specific terms, and recursive construction via Pascal's recurrence $\binom{n}{k} = \binom{n-1}{k-1} + \binom{n-1}{k}$. Begin by implementing exact binomial coefficient calculation avoiding integer overflow through iterative multiplication and division.

```python
import sympy as sp
from sympy import symbols, expand, binomial, summation, factorial, simplify
from sympy import Function, Integer, Rational, latex
import numpy as np
from functools import lru_cache

def binomial_coefficient_safe(n, k):
    """Compute binomial coefficient using SymPy's exact arithmetic."""
    if k < 0 or k > n:
        return 0
    if k == 0 or k == n:
        return 1
    # Use SymPy's built-in which handles large integers exactly
    return int(binomial(n, k))

def verify_binomial_theorem(n_test, x_val=2, y_val=3):
    """
    Verify (x+y)^n equals sum of binomial expansion terms.
    Returns tuple: (direct_expansion, binomial_sum, match_status)
    """
    x, y, k = symbols('x y k', integer=True, nonnegative=True)
    n = Integer(n_test)
    
    # Left side: direct expansion
    direct = (x + y)**n
    direct_expanded = expand(direct)
    
    # Right side: binomial sum
    binomial_sum = summation(binomial(n, k) * x**k * y**(n-k), (k, 0, n))
    binomial_expanded = expand(binomial_sum)
    
    # Symbolic verification
    difference = simplify(direct_expanded - binomial_expanded)
    symbolic_match = difference == 0
    
    # Numerical verification at specific point
    direct_numeric = (x_val + y_val)**n_test
    binomial_numeric = sum(binomial_coefficient_safe(n_test, i) * (x_val**i) * (y_val**(n_test-i)) 
                           for i in range(n_test + 1))
    numeric_match = direct_numeric == binomial_numeric
    
    return direct_expanded, binomial_expanded, symbolic_match and numeric_match

# Execute verification battery
test_cases = [0, 1, 2, 5, 10, 20]
print("=== Binomial Theorem Verification ===")
for n in test_cases:
    left, right, status = verify_binomial_theorem(n)
    print(f"n={n}: {'VERIFIED' if status else 'FAILED'}")
    if n <= 5:  # Print details for small cases
        print(f"  Symbolic: {left} = {right}")
```

The Vandermonde convolution identity states that $\binom{m+n}{r} = \sum_{k=0}^r \binom{m}{k}\binom{n}{r-k}$, interpreted combinatorially as selecting $r$ objects from two disjoint sets of sizes $m$ and $n$ by partitioning the selection. Verify this through symbolic summation and manipulation. The identity extends to multinomial coefficients and forms the foundation for hypergeometric function identities.

```python
def verify_vandermonde_identity(m_val, n_val, r_val):
    """
    Verify Vandermonde's convolution: C(m+n,r) = sum_{k=0}^r C(m,k)*C(n,r-k)
    """
    m, n, r, k = symbols('m n r k', integer=True, nonnegative=True)
    
    # Left side: direct binomial coefficient
    left_side = binomial(m_val + n_val, r_val)
    
    # Right side: convolution sum
    right_side = summation(binomial(m_val, k) * binomial(n_val, r_val - k), 
                           (k, 0, r_val))
    
    # Simplify and compare
    left_value = int(left_side)
    right_value = int(right_side)
    
    return left_value, right_value, left_value == right_value

# Test Vandermonde identity
print("\n=== Vandermonde Convolution Verification ===")
test_vandermonde = [(3, 4, 2), (5, 5, 5), (10, 8, 6), (20, 15, 10)]
for m, n, r in test_vandermonde:
    left, right, status = verify_vandermonde_identity(m, n, r)
    print(f"C({m}+{n},{r}): Left={left}, Right={right}, {'VERIFIED' if status else 'FAILED'}")
```

The Inclusion-Exclusion Principle computes the cardinality of a union of sets through alternating sums over intersections: $|A_1 \cup \cdots \cup A_n| = \sum_{i} |A_i| - \sum_{i<j} |A_i \cap A_j| + \sum_{i<j<k} |A_i \cap A_j \cap A_k| - \cdots + (-1)^{n+1}|A_1 \cap \cdots \cap A_n|$. Verify this computationally by constructing explicit finite sets and computing unions directly versus applying the inclusion-exclusion formula. Extend to counting derangements: the number of permutations of $n$ elements with no fixed points is $D_n = n! \sum_{k=0}^n \frac{(-1)^k}{k!}$.

```python
from itertools import combinations, permutations

def inclusion_exclusion_formula(sets):
    """
    Compute |A1 ∪ A2 ∪ ... ∪ An| using inclusion-exclusion principle.
    sets: list of Python sets
    """
    n = len(sets)
    total = 0
    
    for k in range(1, n + 1):
        # Sum over all k-way intersections
        sign = (-1)**(k + 1)
        for subset_indices in combinations(range(n), k):
            # Compute intersection of sets in this subset
            intersection = sets[subset_indices[0]].copy()
            for idx in subset_indices[1:]:
                intersection &= sets[idx]
            total += sign * len(intersection)
    
    return total

def verify_inclusion_exclusion():
    """Test inclusion-exclusion against direct union computation."""
    # Define test sets
    A1 = {1, 2, 3, 4, 5}
    A2 = {3, 4, 5, 6, 7}
    A3 = {5, 6, 7, 8, 9}
    A4 = {1, 5, 9, 10}
    
    sets = [A1, A2, A3, A4]
    
    # Direct union
    direct_union = set()
    for s in sets:
        direct_union |= s
    
    # Inclusion-exclusion formula
    ie_result = inclusion_exclusion_formula(sets)
    
    print(f"\n=== Inclusion-Exclusion Verification ===")
    print(f"Direct union cardinality: {len(direct_union)}")
    print(f"Inclusion-exclusion result: {ie_result}")
    print(f"Status: {'VERIFIED' if len(direct_union) == ie_result else 'FAILED'}")
    
    return len(direct_union) == ie_result

verify_inclusion_exclusion()

def derangements_formula(n):
    """Compute D_n using inclusion-exclusion: D_n = n! * sum_{k=0}^n (-1)^k / k!"""
    result = factorial(n) * sum(Rational((-1)**k, factorial(k)) for k in range(n + 1))
    return int(result)

def count_derangements_direct(n):
    """Count derangements by explicit enumeration (slow for n > 8)."""
    if n > 9:
        return None  # Too slow for direct enumeration
    count = 0
    for perm in permutations(range(n)):
        if all(perm[i] != i for i in range(n)):
            count += 1
    return count

print("\n=== Derangement Formula Verification ===")
for n in range(10):
    formula_result = derangements_formula(n)
    direct_result = count_derangements_direct(n)
    status = 'VERIFIED' if formula_result == direct_result else 'FAILED'
    print(f"D_{n}: Formula={formula_result}, Direct={direct_result}, {status}")
```

The Stirling numbers of the second kind $S(n,k)$ count partitions of $n$ distinguishable objects into $k$ non-empty unlabeled subsets. They satisfy the recurrence $S(n,k) = k \cdot S(n-1,k) + S(n-1,k-1)$ with boundary conditions $S(0,0)=1$ and $S(n,0)=0$ for $n>0$. The explicit formula via inclusion-exclusion is $S(n,k) = \frac{1}{k!} \sum_{j=0}^k (-1)^{k-j} \binom{k}{j} j^n$. Verify consistency between recursive and explicit formulas, then compute Bell numbers $B_n = \sum_{k=0}^n S(n,k)$, the total number of partitions of an $n$-element set.

```python
@lru_cache(maxsize=None)
def stirling_second_recursive(n, k):
    """Stirling number S(n,k) via recurrence relation."""
    if n == 0 and k == 0:
        return 1
    if n == 0 or k == 0:
        return 0
    if k > n:
        return 0
    return k * stirling_second_recursive(n - 1, k) + stirling_second_recursive(n - 1, k - 1)

def stirling_second_explicit(n, k):
    """Stirling number S(n,k) via inclusion-exclusion formula."""
    if k > n or k == 0:
        return 0 if n > 0 else (1 if n == 0 else 0)
    
    total = sum((-1)**(k - j) * binomial(k, j) * (j**n) for j in range(k + 1))
    return int(total / factorial(k))

def bell_number(n):
    """Bell number B_n = sum of Stirling numbers S(n,k) for k=0..n."""
    return sum(stirling_second_recursive(n, k) for k in range(n + 1))

print("\n=== Stirling Numbers (Second Kind) Verification ===")
for n in range(8):
    print(f"n={n}:")
    for k in range(n + 1):
        recursive_val = stirling_second_recursive(n, k)
        explicit_val = stirling_second_explicit(n, k)
        status = 'VERIFIED' if recursive_val == explicit_val else 'FAILED'
        print(f"  S({n},{k}): Recursive={recursive_val}, Explicit={explicit_val}, {status}")

print("\n=== Bell Numbers ===")
for n in range(10):
    bn = bell_number(n)
    print(f"B_{n} = {bn}")
```

Catalan numbers $C_n = \frac{1}{n+1}\binom{2n}{n}$ enumerate diverse combinatorial structures: binary trees with $n$ internal nodes, Dyck paths of length $2n$, triangulations of convex $(n+2)$-gons, and balanced parenthesis sequences of length $2n$. Verify the closed form against the recurrence $C_n = \sum_{i=0}^{n-1} C_i C_{n-1-i}$ with $C_0=1$, and against direct enumeration of balanced parenthesis sequences using a stack-based validator.

```python
@lru_cache(maxsize=None)
def catalan_recursive(n):
    """Catalan number via recurrence: C_n = sum_{i=0}^{n-1} C_i * C_{n-1-i}."""
    if n == 0:
        return 1
    return sum(catalan_recursive(i) * catalan_recursive(n - 1 - i) for i in range(n))

def catalan_closed_form(n):
    """Catalan number via closed form: C_n = (1/(n+1)) * C(2n, n)."""
    return int(binomial(2 * n, n) / (n + 1))

def is_balanced_parentheses(seq):
    """Check if a sequence of parentheses is balanced."""
    depth = 0
    for char in seq:
        if char == '(':
            depth += 1
        else:  # char == ')'
            depth -= 1
            if depth < 0:
                return False
    return depth == 0

def count_balanced_parentheses(n):
    """Count balanced parenthesis sequences of length 2n by enumeration."""
    if n > 7:
        return None  # Exponential explosion
    from itertools import product
    count = 0
    for seq in product('()', repeat=2*n):
        if seq.count('(') == n and is_balanced_parentheses(seq):
            count += 1
    return count

print("\n=== Catalan Numbers Verification ===")
for n in range(10):
    recursive_val = catalan_recursive(n)
    closed_val = catalan_closed_form(n)
    direct_val = count_balanced_parentheses(n) if n <= 7 else None
    
    print(f"C_{n}: Recursive={recursive_val}, Closed={closed_val}", end='')
    if direct_val is not None:
        status = 'VERIFIED' if recursive_val == closed_val == direct_val else 'FAILED'
        print(f", Direct={direct_val}, {status}")
    else:
        status = 'VERIFIED' if recursive_val == closed_val else 'FAILED'
        print(f", {status}")
```

## Exercise 2: Boundary Value Stress Testing & Singularities

Combinatorial formulas exhibit pathological behavior at boundary conditions where mathematical definitions extend beyond natural domains. The binomial coefficient $\binom{n}{k}$ admits multiple extensions: the polynomial definition $\binom{x}{k} = \frac{x(x-1)\cdots(x-k+1)}{k!}$ extends to real and complex $x$, producing negative values when $x$ is a negative integer not satisfying $x < k$. The gamma function extension $\binom{x}{k} = \frac{\Gamma(x+1)}{\Gamma(k+1)\Gamma(x-k+1)}$ introduces poles when arguments are non-positive integers. Test these extensions systematically.

```python
from scipy.special import comb as scipy_comb
from sympy import gamma, I, oo

def binomial_extended_polynomial(x, k):
    """
    Extended binomial coefficient via polynomial definition.
    Works for real/complex x and non-negative integer k.
    """
    if k < 0:
        return 0
    result = 1
    for i in range(k):
        result *= (x - i)
    result /= factorial(k)
    return result

def binomial_extended_gamma(x, k):
    """
    Extended binomial coefficient via gamma function.
    Returns SymPy expression to handle symbolic singularities.
    """
    return gamma(x + 1) / (gamma(k + 1) * gamma(x - k + 1))

print("\n=== Binomial Coefficient Boundary Testing ===")

# Test negative n with positive k
test_negative = [(-1, 2), (-2, 3), (-5, 2), (-10, 5)]
print("\nNegative n, positive k (polynomial extension):")
for n, k in test_negative:
    poly_val = binomial_extended_polynomial(n, k)
    print(f"  C({n},{k}) = {poly_val}")

# Test fractional arguments
test_fractional = [(0.5, 2), (1.5, 3), (2.5, 2), (3.5, 5)]
print("\nFractional n (polynomial extension):")
for n, k in test_fractional:
    poly_val = binomial_extended_polynomial(n, k)
    print(f"  C({n},{k}) = {poly_val:.6f}")

# Test k > n boundary
test_exceeding = [(3, 5), (2, 10), (5, 6)]
print("\nk > n (should be zero):")
for n, k in test_exceeding:
    standard_val = binomial_coefficient_safe(n, k)
    print(f"  C({n},{k}) = {standard_val}")

# Test large arguments approaching overflow
test_large = [(100, 50), (200, 100), (500, 250), (1000, 500)]
print("\nLarge arguments (exact arithmetic):")
for n, k in test_large:
    exact_val = binomial_coefficient_safe(n, k)
    print(f"  C({n},{k}) = {exact_val}")
    print(f"    Magnitude: 10^{len(str(exact_val)) - 1} ({len(str(exact_val))} digits)")
```

Generating functions serve as formal power series $F(x) = \sum_{n=0}^\infty a_n x^n$ encoding infinite sequences, manipulated algebraically without concern for convergence. The ordinary generating function for Fibonacci numbers $F(x) = \frac{x}{1-x-x^2}$ yields the closed form $F_n = \frac{\phi^n - \psi^n}{\sqrt{5}}$ where $\phi = \frac{1+\sqrt{5}}{2}$ and $\psi = \frac{1-\sqrt{5}}{2}$ through partial fraction decomposition and series expansion. Verify consistency between recursive definition, generating function extraction, and closed form across boundary cases including $F_0=0$, $F_1=1$, and large $n$ where floating-point errors accumulate in the closed form but exact arithmetic preserves correctness.

```python
from sympy import sqrt, symbols, apart, series, summation, floor

@lru_cache(maxsize=None)
def fibonacci_recursive(n):
    """Fibonacci via recurrence: F_0=0, F_1=1, F_n = F_{n-1} + F_{n-2}."""
    if n == 0:
        return 0
    if n == 1:
        return 1
    return fibonacci_recursive(n - 1) + fibonacci_recursive(n - 2)

def fibonacci_closed_form(n):
    """Fibonacci via Binet's formula using SymPy exact arithmetic."""
    phi = (1 + sqrt(5)) / 2
    psi = (1 - sqrt(5)) / 2
    result = (phi**n - psi**n) / sqrt(5)
    return int(result)

def fibonacci_generating_function(n, num_terms=50):
    """
    Extract F_n from generating function F(x) = x / (1 - x - x^2).
    Uses series expansion to specified number of terms.
    """
    x = symbols('x')
    gf = x / (1 - x - x**2)
    
    # Expand as Taylor series around x=0
    series_expansion = series(gf, x, 0, n + 2).removeO()
    
    # Extract coefficient of x^n
    coeff = series_expansion.coeff(x, n)
    return int(coeff) if coeff is not None else 0

print("\n=== Fibonacci Number Verification (Multiple Methods) ===")
test_fibonacci = [0, 1, 2, 5, 10, 15, 20, 30, 40, 50]
for n in test_fibonacci:
    recursive_val = fibonacci_recursive(n)
    closed_val = fibonacci_closed_form(n)
    gf_val = fibonacci_generating_function(n)
    
    match = (recursive_val == closed_val == gf_val)
    status = 'VERIFIED' if match else 'FAILED'
    
    print(f"F_{n}: Recursive={recursive_val}, Closed={closed_val}, GF={gf_val}, {status}")
```

Partition functions exhibit rich asymptotic behavior and generating function structure. The partition function $p(n)$ counts the number of ways to write $n$ as a sum of positive integers without regard to order. The generating function is the infinite product $\sum_{n=0}^\infty p(n)x^n = \prod_{k=1}^\infty \frac{1}{1-x^k}$. Euler's pentagonal number theorem provides a recurrence via pentagonal numbers $g_k = \frac{k(3k-1)}{2}$: $p(n) = p(n-1) + p(n-2) - p(n-5) - p(n-7) + p(n-12) + \cdots$ with alternating signs and pentagonal number offsets. Hardy-Ramanujan asymptotic formula states $p(n) \sim \frac{1}{4n\sqrt{3}} \exp\left(\pi\sqrt{\frac{2n}{3}}\right)$ as $n \to \infty$. Verify the recurrence against direct enumeration for small $n$ and test asymptotic approximation accuracy.

```python
from sympy import exp, pi, N

@lru_cache(maxsize=None)
def partition_function_recurrence(n):
    """
    Partition function p(n) via Euler's pentagonal number theorem.
    p(n) = sum over k≠0 of (-1)^(k+1) * p(n - k(3k-1)/2)
    """
    if n < 0:
        return 0
    if n == 0:
        return 1
    
    result = 0
    k = 1
    while True:
        # Pentagonal numbers: g_k = k(3k-1)/2 and g_{-k} = k(3k+1)/2
        pentagonal_pos = k * (3 * k - 1) // 2
        pentagonal_neg = k * (3 * k + 1) // 2
        
        # Apply both pentagonal offsets with alternating sign
        if pentagonal_pos <= n:
            sign_factor = (-1) ** (k + 1)
            result += sign_factor * partition_function_recurrence(n - pentagonal_pos)
        if pentagonal_neg <= n:
            sign_factor = (-1) ** (k + 1)
            result += sign_factor * partition_function_recurrence(n - pentagonal_neg)
        
        if pentagonal_pos > n:
            return result
        k += 1

def partition_asymptotic(n):
    """Hardy-Ramanujan asymptotic formula for p(n)."""
    if n == 0:
        return 1
    exponent = pi * sqrt(Rational(2 * n, 3))
    coefficient = 1 / (4 * n * sqrt(3))
    approximation = coefficient * exp(exponent)
    return float(N(approximation))

print("\n=== Partition Function Verification ===")
test_partitions = list(range(21)) + [25, 30, 40, 50, 100]
for n in test_partitions:
    exact = partition_function_recurrence(n)
    asymptotic = partition_asymptotic(n)
    relative_error = abs(exact - asymptotic) / exact if exact > 0 else 0
    
    print(f"p({n}): Exact={exact}, Asymptotic≈{asymptotic:.2f}, Error={relative_error:.4%}")
```

Graph enumeration problems test combinatorial explosion boundaries. The number of labeled graphs on $n$ vertices is $2^{\binom{n}{2}}$, growing super-exponentially. Cayley's formula states that the number of labeled trees on $n$ vertices is $n^{n-2}$. Verify Cayley's formula through the Prüfer sequence bijection: each labeled tree corresponds uniquely to a sequence of $n-2$ integers from $\{1,\ldots,n\}$. Implement encoding and decoding algorithms, verify the bijection preserves count, and test boundary cases including $n=1$ (one tree: the single vertex) and $n=2$ (one tree: a single edge).

```python
def prufer_encode(tree_edges, n):
    """
    Encode a labeled tree as a Prüfer sequence.
    tree_edges: list of tuples (u, v) representing edges
    n: number of vertices (labeled 0 to n-1)
    Returns: Prüfer sequence of length n-2
    """
    if n <= 2:
        return []
    
    # Build adjacency list
    adj = [set() for _ in range(n)]
    for u, v in tree_edges:
        adj[u].add(v)
        adj[v].add(u)
    
    sequence = []
    for _ in range(n - 2):
        # Find smallest leaf (degree 1 vertex)
        leaf = min(i for i in range(n) if len(adj[i]) == 1)
        # Find its unique neighbor
        neighbor = next(iter(adj[leaf]))
        sequence.append(neighbor)
        # Remove leaf
        adj[leaf].remove(neighbor)
        adj[neighbor].remove(leaf)
    
    return sequence

def prufer_decode(sequence):
    """
    Decode a Prüfer sequence to a labeled tree.
    sequence: list of integers (Prüfer sequence of length n-2)
    Returns: list of edges (u, v)
    """
    n = len(sequence) + 2
    if n <= 2:
        return [(0, 1)] if n == 2 else []
    
    # Degree of each vertex is 1 + count in sequence
    degree = [1] * n
    for node in sequence:
        degree[node] += 1
    
    edges = []
    for node in sequence:
        # Find smallest leaf
        leaf = min(i for i in range(n) if degree[i] == 1)
        edges.append((leaf, node))
        degree[leaf] -= 1
        degree[node] -= 1
    
    # Connect last two vertices with degree 1
    remaining = [i for i in range(n) if degree[i] == 1]
    edges.append(tuple(remaining))
    
    return edges

def cayley_formula(n):
    """Number of labeled trees on n vertices: n^(n-2)."""
    if n <= 0:
        return 0
    if n == 1:
        return 1
    return n**(n - 2)

print("\n=== Cayley's Formula Verification via Prüfer Sequences ===")

# Verify small cases
for n in range(1, 8):
    expected = cayley_formula(n)
    print(f"n={n}: Expected labeled trees = {expected}")
    
    if n <= 2:
        # Boundary cases
        if n == 1:
            print(f"  (Single vertex)")
        else:
            print(f"  (Single edge between 2 vertices)")
        continue
    
    # For n > 2, verify by counting distinct Prüfer sequences
    from itertools import product
    prufer_sequences = list(product(range(n), repeat=n - 2))
    count = len(prufer_sequences)
    
    print(f"  Prüfer sequences: {count}, {'VERIFIED' if count == expected else 'FAILED'}")
    
    # Test encode-decode round trip for a specific tree
    if n == 4:
        test_tree = [(0, 1), (1, 2), (1, 3)]  # Star graph with center 1
        encoded = prufer_encode(test_tree, n)
        decoded = prufer_decode(encoded)
        print(f"  Encode-decode test: Original={test_tree}, Encoded={encoded}, Decoded={decoded}")
```

## Exercise 3: Algorithmic Implementation of Formal Structures

Permutation group computations require efficient representation and manipulation of symmetric group elements. The symmetric group $S_n$ contains $n!$ permutations of $\{1,\ldots,n\}$, with composition as the group operation. Implement permutations in cycle notation, which uniquely factors each permutation into disjoint cycles. The sign of a permutation equals $(-1)^{n-c}$ where $c$ is the number of cycles. Verify group axioms: closure under composition, associativity, identity existence, and inverse existence. Compute the order of permutation $\sigma$ as the least common multiple of its cycle lengths.

```python
from math import gcd
from functools import reduce

class Permutation:
    """Permutation represented in cycle notation."""
    
    def __init__(self, cycles, n=None):
        """
        Initialize permutation from cycle notation.
        cycles: list of tuples, each representing a cycle
        n: size of symmetric group (inferred if not provided)
        """
        self.cycles = [tuple(c) for c in cycles if len(c) > 1]  # Ignore 1-cycles
        if n is None:
            self.n = max(max(c) for c in self.cycles) if self.cycles else 1
        else:
            self.n = n
        
        # Build mapping dictionary
        self.mapping = {i: i for i in range(1, self.n + 1)}
        for cycle in self.cycles:
            for i in range(len(cycle)):
                self.mapping[cycle[i]] = cycle[(i + 1) % len(cycle)]
    
    def __call__(self, x):
        """Apply permutation to element x."""
        return self.mapping.get(x, x)
    
    def __mul__(self, other):
        """Compose permutations: (self * other)(x) = self(other(x))."""
        # Compute composition by tracking where each element goes
        new_mapping = {i: self(other(i)) for i in range(1, self.n + 1)}
        
        # Convert back to cycle notation
        visited = set()
        cycles = []
        for start in range(1, self.n + 1):
            if start in visited:
                continue
            cycle = []
            current = start
            while current not in visited:
                visited.add(current)
                cycle.append(current)
                current = new_mapping[current]
            if len(cycle) > 1:
                cycles.append(tuple(cycle))
        
        return Permutation(cycles, self.n)
    
    def inverse(self):
        """Compute inverse permutation."""
        inv_cycles = [tuple(reversed(c)) for c in self.cycles]
        return Permutation(inv_cycles, self.n)
    
    def order(self):
        """Order of permutation: LCM of cycle lengths."""
        if not self.cycles:
            return 1
        
        def lcm(a, b):
            return abs(a * b) // gcd(a, b)
        
        cycle_lengths = [len(c) for c in self.cycles]
        return reduce(lcm, cycle_lengths)
    
    def sign(self):
        """Sign (parity) of permutation: (-1)^(n - number_of_cycles)."""
        num_cycles = len(self.cycles)
        # Count fixed points (1-cycles)
        fixed_points = sum(1 for i in range(1, self.n + 1) 
                          if self.mapping[i] == i)
        total_cycles = num_cycles + fixed_points
        return (-1) ** (self.n - total_cycles)
    
    def __repr__(self):
        if not self.cycles:
            return "id"
        return "".join(str(c) for c in self.cycles)

# Test permutation group axioms
print("\n=== Permutation Group Verification ===")

# Define test permutations in S_5
sigma = Permutation([(1, 2, 3), (4, 5)], n=5)  # (1 2 3)(4 5)
tau = Permutation([(1, 4), (2, 5, 3)], n=5)    # (1 4)(2 5 3)
rho = Permutation([(1, 3, 5, 2, 4)], n=5)      # (1 3 5 2 4)
identity = Permutation([], n=5)                 # identity

print(f"σ = {sigma}, order = {sigma.order()}, sign = {sigma.sign()}")
print(f"τ = {tau}, order = {tau.order()}, sign = {tau.sign()}")
print(f"ρ = {rho}, order = {rho.order()}, sign = {rho.sign()}")

# Test closure
sigma_tau = sigma * tau
print(f"\nClosure: σ∘τ = {sigma_tau}, order = {sigma_tau.order()}")

# Test associativity: (σ∘τ)∘ρ = σ∘(τ∘ρ)
left_assoc = (sigma * tau) * rho
right_assoc = sigma * (tau * rho)
assoc_test = all(left_assoc(i) == right_assoc(i) for i in range(1, 6))
print(f"Associativity: (σ∘τ)∘ρ = σ∘(τ∘ρ): {'VERIFIED' if assoc_test else 'FAILED'}")

# Test identity
identity_test_left = all((identity * sigma)(i) == sigma(i) for i in range(1, 6))
identity_test_right = all((sigma * identity)(i) == sigma(i) for i in range(1, 6))
print(f"Identity: id∘σ = σ∘id = σ: {'VERIFIED' if identity_test_left and identity_test_right else 'FAILED'}")

# Test inverse
sigma_inv = sigma.inverse()
left_inv = sigma_inv * sigma
right_inv = sigma * sigma_inv
inv_test = all(left_inv(i) == i and right_inv(i) == i for i in range(1, 6))
print(f"Inverse: σ⁻¹∘σ = σ∘σ⁻¹ = id: {'VERIFIED' if inv_test else 'FAILED'}")

# Verify order computation: σ^order = id
sigma_power = identity
for _ in range(sigma.order()):
    sigma_power = sigma_power * sigma
order_test = all(sigma_power(i) == i for i in range(1, 6))
print(f"Order verification: σ^{sigma.order()} = id: {'VERIFIED' if order_test else 'FAILED'}")
```

Partially ordered sets (posets) encode order relations satisfying reflexivity, antisymmetry, and transitivity. The divisibility relation on positive integers forms a poset where $a \preceq b$ if $a$ divides $b$. Implement a poset class with Hasse diagram computation, which removes transitive edges and self-loops to visualize the minimal covering relation. Verify lattice properties: existence of meets (greatest lower bounds) and joins (least upper bounds) for all pairs. The divisor lattice on $\{1,2,3,6\}$ has meet equal to $\gcd$ and join equal to $\text{lcm}$.

```python
class Poset:
    """Partially ordered set with covering relation computation."""
    
    def __init__(self, elements, relation):
        """
        Initialize poset.
        elements: list of elements
        relation: function (a, b) -> bool indicating if a ≤ b
        """
        self.elements = sorted(elements)
        self.relation = relation
        
        # Compute covering relation (Hasse diagram edges)
        self.covers = []
        for a in self.elements:
            for b in self.elements:
                if a == b:
                    continue
                if self.relation(a, b):
                    # Check if a covers b (no element strictly between)
                    is_cover = True
                    for c in self.elements:
                        if c == a or c == b:
                            continue
                        if self.relation(a, c) and self.relation(c, b):
                            is_cover = False
                            break
                    if is_cover:
                        self.covers.append((a, b))
    
    def is_comparable(self, a, b):
        """Check if a and b are comparable."""
        return self.relation(a, b) or self.relation(b, a)
    
    def meet(self, a, b):
        """Compute meet (greatest lower bound) of a and b."""
        lower_bounds = [x for x in self.elements 
                       if self.relation(x, a) and self.relation(x, b)]
        if not lower_bounds:
            return None
        # Find greatest among lower bounds
        for x in reversed(lower_bounds):
            if all(self.relation(y, x) for y in lower_bounds):
                return x
        return None
    
    def join(self, a, b):
        """Compute join (least upper bound) of a and b."""
        upper_bounds = [x for x in self.elements 
                       if self.relation(a, x) and self.relation(b, x)]
        if not upper_bounds:
            return None
        # Find least among upper bounds
        for x in upper_bounds:
            if all(self.relation(x, y) for y in upper_bounds):
                return x
        return None
    
    def is_lattice(self):
        """Check if poset is a lattice (all pairs have meet and join)."""
        for a in self.elements:
            for b in self.elements:
                if self.meet(a, b) is None or self.join(a, b) is None:
                    return False
        return True

# Divisibility poset
def divides(a, b):
    """Check if a divides b."""
    return b % a == 0

divisor_elements = [1, 2, 3, 6]
divisor_poset = Poset(divisor_elements, divides)

print("\n=== Divisibility Poset on {1, 2, 3, 6} ===")
print(f"Elements: {divisor_poset.elements}")
print(f"Covering relations (Hasse diagram): {divisor_poset.covers}")
print(f"Is lattice: {divisor_poset.is_lattice()}")

# Verify lattice properties: meet = gcd, join = lcm
print("\nLattice operations verification:")
for a in divisor_elements:
    for b in divisor_elements:
        meet_val = divisor_poset.meet(a, b)
        join_val = divisor_poset.join(a, b)
        expected_meet = gcd(a, b)
        expected_join = abs(a * b) // gcd(a, b)  # lcm formula
        
        meet_match = meet_val == expected_meet
        join_match = join_val == expected_join
        
        print(f"  {a} ∧ {b} = {meet_val} (gcd={expected_meet}), "
              f"{a} ∨ {b} = {join_val} (lcm={expected_join}), "
              f"{'VERIFIED' if meet_match and join_match else 'FAILED'}")

# Power set lattice with subset relation
def subset_relation(a, b):
    """Check if set a is subset of set b."""
    return a.issubset(b)

base_set = {1, 2, 3}
power_set = [frozenset(s) for s in [set(), {1}, {2}, {3}, {1,2}, {1,3}, {2,3}, {1,2,3}]]
subset_poset = Poset(power_set, subset_relation)

print(f"\n=== Power Set Lattice on {{1, 2, 3}} ===")
print(f"Number of elements: {len(subset_poset.elements)}")
print(f"Is lattice: {subset_poset.is_lattice()}")

# Verify meet = intersection, join = union
test_pairs = [(frozenset({1}), frozenset({2})), 
              (frozenset({1, 2}), frozenset({2, 3}))]
print("\nLattice operations verification:")
for a, b in test_pairs:
    meet_val = subset_poset.meet(a, b)
    join_val = subset_poset.join(a, b)
    expected_meet = a.intersection(b)
    expected_join = a.union(b)
    
    print(f"  {set(a)} ∧ {set(b)} = {set(meet_val)} (expected {set(expected_meet)}), "
          f"{set(a)} ∨ {set(b)} = {set(join_val)} (expected {set(expected_join)})")
```

Graph automorphism groups capture symmetries of discrete structures. An automorphism of graph $G=(V,E)$ is a bijection $\phi: V \to V$ preserving adjacency: $(u,v) \in E$ if and only if $(\phi(u),\phi(v)) \in E$. The automorphism group $\text{Aut}(G)$ under composition forms a subgroup of $S_n$ where $n=|V|$. Compute automorphism groups by exhaustive search for small graphs and verify group closure. The complete graph $K_n$ has $\text{Aut}(K_n) \cong S_n$, the path graph $P_n$ has automorphism group of order $2$ (identity and reflection), and the cycle graph $C_n$ has dihedral group $D_n$ of order $2n$.

```python
from itertools import permutations as iter_permutations

class Graph:
    """Simple undirected graph."""
    
    def __init__(self, n, edges):
        """
        Initialize graph.
        n: number of vertices (labeled 0 to n-1)
        edges: list of tuples (u, v)
        """
        self.n = n
        self.edges = set()
        for u, v in edges:
            self.edges.add((min(u, v), max(u, v)))  # Normalize edge representation
    
    def has_edge(self, u, v):
        """Check if edge (u,v) exists."""
        return (min(u, v), max(u, v)) in self.edges
    
    def apply_permutation(self, perm):
        """Apply permutation to vertices, return new edge set."""
        new_edges = set()
        for u, v in self.edges:
            new_u, new_v = perm[u], perm[v]
            new_edges.add((min(new_u, new_v), max(new_u, new_v)))
        return new_edges
    
    def is_automorphism(self, perm):
        """Check if permutation is an automorphism."""
        new_edges = self.apply_permutation(perm)
        return new_edges == self.edges
    
    def automorphism_group(self):
        """Compute automorphism group by exhaustive search."""
        autos = []
        for perm_tuple in iter_permutations(range(self.n)):
            perm_dict = {i: perm_tuple[i] for i in range(self.n)}
            if self.is_automorphism(perm_dict):
                autos.append(perm_tuple)
        return autos

# Complete graph K_4
k4 = Graph(4, [(i, j) for i in range(4) for j in range(i+1, 4)])
k4_autos = k4.automorphism_group()
print("\n=== Graph Automorphism Groups ===")
print(f"K_4 (Complete graph on 4 vertices):")
print(f"  |Aut(K_4)| = {len(k4_autos)} (expected {factorial(4)} for S_4)")
print(f"  Verification: {'VERIFIED' if len(k4_autos) == 24 else 'FAILED'}")

# Path graph P_4: 0-1-2-3
p4 = Graph(4, [(0, 1), (1, 2), (2, 3)])
p4_autos = p4.automorphism_group()
print(f"\nP_4 (Path graph on 4 vertices):")
print(f"  |Aut(P_4)| = {len(p4_autos)} (expected 2: identity and reflection)")
print(f"  Automorphisms: {p4_autos}")
print(f"  Verification: {'VERIFIED' if len(p4_autos) == 2 else 'FAILED'}")

# Cycle graph C_5: 0-1-2-3-4-0
c5 = Graph(5, [(0, 1), (1, 2), (2, 3), (3, 4), (4, 0)])
c5_autos = c5.automorphism_group()
print(f"\nC_5 (Cycle graph on 5 vertices):")
print(f"  |Aut(C_5)| = {len(c5_autos)} (expected 10 for dihedral group D_5)")
print(f"  Verification: {'VERIFIED' if len(c5_autos) == 10 else 'FAILED'}")

# Star graph: central vertex 0 connected to 1,2,3
star = Graph(4, [(0, 1), (0, 2), (0, 3)])
star_autos = star.automorphism_group()
print(f"\nStar graph (1 central vertex, 3 leaves):")
print(f"  |Aut(Star)| = {len(star_autos)} (expected 6 for S_3 acting on leaves)")
print(f"  Verification: {'VERIFIED' if len(star_autos) == 6 else 'FAILED'}")
```

Ramsey theory investigates conditions guaranteeing monochromatic structures in colored combinatorial objects. The Ramsey number $R(s,t)$ is the minimum $n$ such that any red-blue edge coloring of $K_n$ contains either a red $K_s$ or blue $K_t$. Classical results include $R(3,3)=6$ and $R(4,4)=18$. Verify $R(3,3)=6$ by exhaustive enumeration: demonstrate that $K_5$ admits a coloring avoiding monochromatic triangles, but every coloring of $K_6$ contains a monochromatic triangle. Implement triangle detection and coloring enumeration.

```python
def has_monochromatic_triangle(n, coloring):
    """
    Check if edge coloring contains a monochromatic triangle.
    coloring: dict mapping edge (i,j) to color 0 or 1
    """
    for i in range(n):
        for j in range(i+1, n):
            for k in range(j+1, n):
                # Check triangle (i,j,k)
                e1 = coloring.get((i, j), coloring.get((j, i)))
                e2 = coloring.get((j, k), coloring.get((k, j)))
                e3 = coloring.get((i, k), coloring.get((k, i)))
                
                if e1 == e2 == e3:
                    return True, (i, j, k), e1
    return False, None, None

def count_ramsey_colorings(n):
    """
    Count colorings of K_n without monochromatic triangles.
    Returns count and example coloring if exists.
    """
    edges = [(i, j) for i in range(n) for j in range(i+1, n)]
    num_edges = len(edges)
    
    count_valid = 0
    example_coloring = None
    
    # Enumerate all 2^num_edges colorings
    for coloring_bits in range(2**num_edges):
        coloring = {}
        for idx, (i, j) in enumerate(edges):
            color = (coloring_bits >> idx) & 1
            coloring[(i, j)] = color
        
        has_mono, triangle, color = has_monochromatic_triangle(n, coloring)
        if not has_mono:
            count_valid += 1
            if example_coloring is None:
                example_coloring = coloring
    
    return count_valid, example_coloring

print("\n=== Ramsey Number R(3,3) Verification ===")

# Verify K_5 admits triangle-free coloring
print("K_5 (5 vertices):")
count_k5, example_k5 = count_ramsey_colorings(5)
print(f"  Colorings without monochromatic triangles: {count_k5}")
if count_k5 > 0:
    print(f"  Example exists: VERIFIED")
    print(f"  Sample coloring: {example_k5}")
else:
    print(f"  No valid coloring: FAILED")

# Verify K_6 has no triangle-free coloring (this proves R(3,3) ≤ 6)
print("\nK_6 (6 vertices):")
count_k6, example_k6 = count_ramsey_colorings(6)
print(f"  Colorings without monochromatic triangles: {count_k6}")
if count_k6 == 0:
    print(f"  Every coloring has monochromatic triangle: VERIFIED")
    print(f"  Therefore R(3,3) = 6: VERIFIED")
else:
    print(f"  Found {count_k6} valid colorings: FAILED")
```

## Formal Axioms Cheat Sheet & Verification Reference

### Binomial Coefficient Identities

The binomial coefficient $\binom{n}{k} = \frac{n!}{k!(n-k)!}$ satisfies Pascal's recurrence $\binom{n}{k} = \binom{n-1}{k-1} + \binom{n-1}{k}$ with boundary conditions $\binom{n}{0} = \binom{n}{n} = 1$ and $\binom{n}{k} = 0$ for $k < 0$ or $k > n$. The binomial theorem states $(x+y)^n = \sum_{k=0}^n \binom{n}{k} x^k y^{n-k}$. Vandermonde's convolution gives $\binom{m+n}{r} = \sum_{k=0}^r \binom{m}{k}\binom{n}{r-k}$, verified by comparing direct computation with summation. The polynomial extension $\binom{x}{k} = \frac{x(x-1)\cdots(x-k+1)}{k!}$ allows real arguments, producing negative binomial coefficients when $x < 0$. The reflection formula $\binom{n}{k} = \binom{n}{n-k}$ expresses symmetry.

Verification protocol: Implement exact integer arithmetic using SymPy's `binomial` function. Test Pascal's recurrence for $0 \le k \le n \le 50$. Verify binomial theorem symbolically by expanding $(x+y)^n$ and comparing coefficients term-by-term. For Vandermonde convolution, enumerate $(m,n,r)$ triples with $m,n \le 20$ and verify equality between left and right sides. Test polynomial extension with negative and fractional arguments, confirming consistency with series definitions.

### Stirling Numbers and Bell Numbers

Stirling numbers of the second kind $S(n,k)$ count set partitions of $n$ elements into $k$ non-empty blocks. The recurrence $S(n,k) = k \cdot S(n-1,k) + S(n-1,k-1)$ follows from distinguishing whether element $n$ forms a singleton block or joins an existing block. The explicit formula $S(n,k) = \frac{1}{k!} \sum_{j=0}^k (-1)^{k-j} \binom{k}{j} j^n$ derives from inclusion-exclusion on surjective functions. Bell numbers $B_n = \sum_{k=0}^n S(n,k)$ count total partitions.

Verification protocol: Compute $S(n,k)$ for $0 \le k \le n \le 15$ using both recurrence and explicit formula. Verify equality for all $(n,k)$ pairs. Compare Bell numbers against direct summation of Stirling numbers. Test boundary cases: $S(0,0)=1$, $S(n,0)=0$ for $n>0$, $S(n,1)=1$, $S(n,n)=1$. The identity $\sum_{k=0}^n S(n,k)x^k$ generates restricted growth strings; verify by coefficient extraction from generating function $(e^x - 1)^k / k!$ using SymPy series expansion.

### Catalan Numbers

Catalan numbers $C_n = \frac{1}{n+1}\binom{2n}{n}$ enumerate binary trees, Dyck paths, triangulations, and balanced parentheses. The recurrence $C_n = \sum_{i=0}^{n-1} C_i C_{n-1-i}$ arises from decomposing trees by root's left subtree size. The generating function $C(x) = \frac{1 - \sqrt{1-4x}}{2x}$ satisfies $C(x) = 1 + xC(x)^2$, solved via quadratic formula.

Verification protocol: Compute $C_n$ for $0 \le n \le 20$ using closed form, recurrence, and generating function coefficient extraction. Verify all three methods agree. Enumerate balanced parentheses sequences of length $2n$ for $n \le 7$ using recursive generation with stack depth validation. Count sequences and compare to $C_n$. Test asymptotic approximation $C_n \sim \frac{4^n}{n^{3/2}\sqrt{\pi}}$ for $n \ge 10$, computing relative error. Verify special case $C_0=1$ (empty tree).

### Inclusion-Exclusion Principle

For finite sets $A_1, \ldots, A_n$, the cardinality of their union is $|A_1 \cup \cdots \cup A_n| = \sum_{k=1}^n (-1)^{k+1} \sum_{|S|=k} |\bigcap_{i \in S} A_i|$ where the inner sum ranges over all $k$-element subsets $S \subseteq \{1,\ldots,n\}$. Derangements $D_n$ satisfy $D_n = n! \sum_{k=0}^n \frac{(-1)^k}{k!}$, derived by inclusion-exclusion on fixed-point sets.

Verification protocol: Construct random finite sets $A_1, \ldots, A_n$ with controlled overlap. Compute union cardinality directly via set operations and via inclusion-exclusion formula. Verify equality for $n \le 6$. Enumerate derangements of $\{1,\ldots,n\}$ by explicit permutation generation with fixed-point checking for $n \le 9$. Compare count to formula $D_n$. Test asymptotic limit $\lim_{n\to\infty} D_n/n! = e^{-1}$ by computing ratio for $n=10,20,50,100$. Verify recurrence $D_n = (n-1)(D_{n-1} + D_{n-2})$ for $n \ge 2$.

### Generating Functions

The ordinary generating function $F(x) = \sum_{n=0}^\infty a_n x^n$ encodes sequence $(a_n)$ as formal power series. Exponential generating functions $E(x) = \sum_{n=0}^\infty a_n \frac{x^n}{n!}$ suit labeled structures. Fibonacci generating function $\frac{x}{1-x-x^2}$ yields closed form via partial fractions: $\frac{x}{1-x-x^2} = \frac{1}{\sqrt{5}}\left(\frac{1}{1-\phi x} - \frac{1}{1-\psi x}\right)$ where $\phi = \frac{1+\sqrt{5}}{2}$, $\psi = \frac{1-\sqrt{5}}{2}$. Coefficient extraction gives $F_n = \frac{\phi^n - \psi^n}{\sqrt{5}}$.

Verification protocol: Compute Fibonacci numbers $F_n$ for $0 \le n \le 100$ using recurrence, closed form (exact arithmetic with SymPy), and generating function series expansion (via `series` to $n+5$ terms). Verify all methods agree exactly. Test partition generating function $\prod_{k=1}^\infty \frac{1}{1-x^k}$ by expanding to degree $n=50$ and extracting coefficients. Compare to partition function $p(n)$ computed via Euler's pentagonal recurrence. Verify exponential generating function for derangements: $\frac{e^{-x}}{1-x} = \sum_{n=0}^\infty D_n \frac{x^n}{n!}$ by coefficient extraction and comparison to direct formula.

### Permutation Group Computations

Permutations of $\{1,\ldots,n\}$ form symmetric group $S_n$ of order $n!$. Cycle notation uniquely represents permutations: $(1\ 3\ 5)(2\ 4)$ maps $1 \mapsto 3 \mapsto 5 \mapsto 1$ and $2 \mapsto 4 \mapsto 2$. Composition $(1\ 2)(2\ 3) = (1\ 2\ 3)$ applies right-to-left. Order of permutation equals $\text{lcm}$ of cycle lengths. Sign equals $(-1)^{n-c}$ where $c$ counts cycles. Alternating group $A_n \subset S_n$ contains even permutations, satisfying $|A_n| = n!/2$ for $n \ge 2$.

Verification protocol: Implement permutation class with cycle notation storage, composition operation, inverse computation, and order calculation. Generate random permutations in $S_n$ for $n \le 10$. Verify group axioms: associativity by triple composition, identity preservation, inverse correctness via composition yielding identity. Test $\sigma^{\text{ord}(\sigma)} = e$ for sample permutations. Compute sign via cycle structure and verify alternating pattern under composition. Enumerate $A_5$ and confirm $|A_5|=60$ with no normal subgroups except trivial and $A_5$ itself, proving simplicity.

### Posets and Lattices

Partially ordered set $(P, \preceq)$ satisfies reflexivity ($a \preceq a$), antisymmetry ($a \preceq b$ and $b \preceq a$ implies $a=b$), and transitivity. Hasse diagram omits reflexive and transitive edges, showing only covering relations $a \prec b$ where no $c$ satisfies $a \prec c \prec b$. Lattice requires every pair $(a,b)$ has meet $a \wedge b = \inf\{a,b\}$ and join $a \vee b = \sup\{a,b\}$. Divisibility poset on positive integers has $a \preceq b$ iff $a | b$; meet is $\gcd$, join is $\text{lcm}$. Power set $(\mathcal{P}(S), \subseteq)$ has meet as intersection, join as union.

Verification protocol: Implement poset class storing elements and relation predicate. Compute covering relation by eliminating transitive edges: for each pair $(a,b)$ with $a \prec b$, check no intermediate $c$ exists. Test lattice property by computing meet and join for all pairs in divisor poset on $\{1,2,\ldots,30\}$. Verify $a \wedge b = \gcd(a,b)$ and $a \vee b = \text{lcm}(a,b)$ exactly. Enumerate power set $\mathcal{P}(\{1,2,3\})$ and verify subset lattice operations: meet as intersection, join as union. Check distributivity: $a \wedge (b \vee c) = (a \wedge b) \vee (a \wedge c)$.

### Graph Automorphisms

Graph automorphism $\phi: V \to V$ preserves adjacency: $(u,v) \in E \iff (\phi(u),\phi(v)) \in E$. Automorphism group $\text{Aut}(G)$ forms subgroup of $S_n$. Complete graph $K_n$ has $\text{Aut}(K_n) \cong S_n$ since all vertex permutations preserve full connectivity. Cycle $C_n$ has $\text{Aut}(C_n) \cong D_n$ (dihedral group) of order $2n$: $n$ rotations and $n$ reflections. Path $P_n$ has $|\text{Aut}(P_n)|=2$ (identity and end-swap). Orbit-stabilizer theorem gives $|G| = |\text{Orb}(v)| \cdot |\text{Stab}(v)|$ for vertex orbits under $G = \text{Aut}(G)$.

Verification protocol: Implement graph class with edge set representation. Enumerate all $n!$ permutations of vertices for graphs with $n \le 8$. Test each permutation for automorphism property by checking edge preservation. Count valid automorphisms and verify against theoretical values: $|S_4|=24$ for $K_4$, $10$ for $C_5$, $2$ for $P_n$. Compute vertex orbits by grouping vertices under automorphism action. Verify orbit-stabilizer: for each vertex, compute stabilizer subgroup and confirm $|G| = |\text{orbit}| \cdot |\text{stabilizer}|$. Test graph isomorphism via automorphism computation: graphs $G_1$, $G_2$ isomorphic iff $\text{Aut}(G_1 \sqcup G_2)$ mixes vertices between components.

### Ramsey Theory

Ramsey number $R(s,t)$ is minimal $n$ such that any red-blue coloring of $K_n$ contains red $K_s$ or blue $K_t$. Known values: $R(3,3)=6$, $R(3,4)=9$, $R(4,4)=18$. Upper bound: $R(s,t) \le \binom{s+t-2}{s-1}$ via probabilistic argument. Ramsey's theorem guarantees $R(s,t)$ exists and is finite for all $s,t \ge 2$.

Verification protocol: Enumerate all $2^{\binom{n}{2}}$ edge colorings of $K_n$ for $n \le 6$. For each coloring, search for monochromatic cliques of size $s=t=3$ by enumerating all triples and checking edge colors. Verify $K_5$ admits triangle-free colorings (exhibiting specific example), but $K_6$ admits none, proving $R(3,3)=6$. Implement clique detection algorithm: for target clique size $k$, enumerate all $k$-subsets of vertices and check if induced subgraph is monochromatic complete. Test $R(3,4)$ by extending search to $K_9$, verifying no coloring avoids red triangle and blue $K_4$ simultaneously.
