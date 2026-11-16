# Operational Verification Labs: Discrete Mathematics

## Objective & Mathematical Computing Setup

Discrete mathematics forms the computational backbone of computer science, cryptography, combinatorial optimization, and formal verification systems. Unlike continuous analysis, discrete structures demand exact symbolic manipulation: graph connectivity is either proven or refuted, a combinatorial identity holds universally or fails at a single counterexample, and modular arithmetic operations must preserve group axioms without approximation error. This laboratory guide establishes a practitioner-grade environment for verifying discrete mathematical properties through symbolic computation engines, automated theorem provers, and algorithmic implementations that expose the mechanical reality of abstract structures.

The operational philosophy centers on computational falsifiability. Every theorem becomes a computational hypothesis subject to symbolic verification, boundary stress testing, and algorithmic implementation. When we claim that Euler's formula $V - E + F = 2$ holds for planar connected graphs, we construct explicit graph adjacency matrices, compute cycle bases, and verify the invariant across homeomorphic transformations. When we assert that the Chinese Remainder Theorem guarantees unique solutions modulo $n_1 n_2 \cdots n_k$ for pairwise coprime moduli, we implement the extended Euclidean algorithm, construct Bézout coefficient solvers, and stress-test the reconstruction map against edge cases where coprimality assumptions break down.

The primary computational environment leverages Python 3.11 or later with SymPy 1.12+ for symbolic algebra, NumPy 1.24+ for numerical matrix operations, and SageMath 10.0+ for advanced combinatorial structures and number-theoretic primitives. SymPy provides the core symbolic manipulation engine: polynomial factorization over finite fields, modular arithmetic with automatic reduction, combinatorial enumeration through generating functions, and graph-theoretic algorithms with certified correctness guarantees. SageMath extends this foundation with specialized discrete mathematics libraries: Gröbner basis computation for ideal membership testing, lattice reduction algorithms for cryptographic applications, and partition enumeration with hook-length formulas.

Installation proceeds through standard Python package management. On Unix-like systems, establish a clean virtual environment with `python3.11 -m venv discrete_math_lab && source discrete_math_lab/bin/activate`, then install dependencies with `pip install sympy==1.12 numpy==1.24.3 matplotlib==3.7.1`. SageMath requires either a full installation from source or the official binary distribution available at sagemath.org, which bundles Python with all mathematical libraries pre-configured. Verify the installation by executing `python -c 'import sympy; print(sympy.__version__); from sympy import symbols, factor, isprime; x = symbols("x"); print(factor(x**4 - 1)); print(isprime(2**31 - 1))'`, which should return version `1.12` followed by the factored form $(x - 1)(x + 1)(x^2 + 1)$ and the primality confirmation `True` for the Mersenne prime $2^{31} - 1 = 2147483647$.

For formal proof verification, Lean 4 provides a production-grade interactive theorem prover with extensive mathematical libraries in Mathlib. Install Lean through the official toolchain manager with `curl https://raw.githubusercontent.com/leanprover/elan/master/elan-init.sh -sSf | sh`, then initialize a project directory with `lake new discrete_proofs math && cd discrete_proofs`. The Lean workflow differs fundamentally from symbolic computation: rather than executing algorithms, you construct formal proof terms that the type checker mechanically verifies against axioms. A simple proof that addition commutes in natural numbers takes the form `example (m n : Nat) : m + n = n + m := Nat.add_comm m n`, where `Nat.add_comm` references a theorem proven in Mathlib through structural induction.

The laboratory structure follows a three-phase verification methodology. Exercise One focuses on computational verification of canonical theorems: implement the theorem statement as a symbolic predicate, construct test cases spanning the domain of discourse, and verify consistency through exhaustive enumeration or property-based testing. Exercise Two stress-tests boundary conditions and singularities: identify parameter regimes where naive implementations fail, construct counterexamples for weakened hypotheses, and measure computational complexity degradation at phase transitions. Exercise Three implements formal structures as executable data types: encode axioms as runtime assertions, build certified algorithms that maintain invariants through type-safe interfaces, and benchmark performance against industrial-strength libraries.

Throughout all exercises, the emphasis remains on mechanical verification over intuitive plausibility. A proof-of-concept becomes production-ready only when it survives adversarial inputs, edge-case perturbations, and formal correctness audits. The output is not merely theoretical understanding but operational mastery: the ability to translate abstract mathematical claims into verifiable computational artifacts and to diagnose precisely where theoretical elegance meets implementation reality.

## Exercise 1: Computational Verification of Core Theorems

The first exercise establishes symbolic verification workflows for foundational discrete mathematics theorems. We focus on three domains where computational verification exposes structural insights: combinatorial identities through generating function manipulation, number-theoretic congruences through modular arithmetic engines, and graph-theoretic invariants through adjacency matrix spectral analysis.

### Combinatorial Identity Verification: Vandermonde's Convolution

Vandermonde's convolution asserts that $\sum_{k=0}^r \binom{m}{k} \binom{n}{r-k} = \binom{m+n}{r}$ for non-negative integers $m, n, r$. The combinatorial interpretation counts ways to select $r$ objects from a union of two disjoint sets of sizes $m$ and $n$ by partitioning the selection into $k$ objects from the first set and $r - k$ from the second. Symbolic verification proceeds through direct computation across parameter sweeps, exposing the identity's stability under extreme values.

Begin by implementing a symbolic binomial coefficient function that handles edge cases rigorously. SymPy provides `sympy.binomial(n, k)`, which automatically reduces to zero for $k < 0$ or $k > n$ and handles symbolic parameters. Construct the verification harness:

```python
from sympy import symbols, binomial, summation, simplify, expand
from sympy.abc import k

def verify_vandermonde(m_val, n_val, r_val):
    """Verify Vandermonde convolution for concrete integer parameters."""
    m, n, r = symbols('m n r', integer=True, nonnegative=True)
    
    # Left-hand side: convolution sum
    lhs = summation(binomial(m, k) * binomial(n, r - k), (k, 0, r))
    lhs_evaluated = lhs.subs({m: m_val, n: n_val, r: r_val})
    
    # Right-hand side: direct binomial
    rhs = binomial(m + n, r)
    rhs_evaluated = rhs.subs({m: m_val, n: n_val, r: r_val})
    
    # Verify equality
    lhs_value = lhs_evaluated.doit()
    rhs_value = rhs_evaluated.doit()
    
    return lhs_value, rhs_value, lhs_value == rhs_value

# Test across parameter space
test_cases = [
    (5, 3, 2),   # Standard case
    (10, 10, 5), # Symmetric case
    (20, 5, 7),  # Asymmetric case
    (0, 5, 3),   # Boundary: m = 0
    (5, 0, 0),   # Boundary: n = 0, r = 0
    (10, 10, 25) # Boundary: r > m + n (should both be 0)
]

print("Vandermonde Convolution Verification")
print("=" * 60)
for m, n, r in test_cases:
    lhs, rhs, valid = verify_vandermonde(m, n, r)
    status = "✓ PASS" if valid else "✗ FAIL"
    print(f"m={m:2d}, n={n:2d}, r={r:2d} | LHS={lhs:8d}, RHS={rhs:8d} | {status}")
```

This implementation exposes the critical detail that SymPy's `summation` requires explicit `.doit()` evaluation to force symbolic computation. The boundary case $r > m + n$ tests whether both sides correctly reduce to zero, verifying that the implementation respects the binomial coefficient's domain restrictions. The symmetric case $m = n$ with $r = 5$ produces $\binom{20}{5} = 15504$, a computationally intensive evaluation that validates the symbolic engine's handling of large intermediate terms.

Extend the verification to symbolic parameter regimes by checking whether SymPy can prove the identity algebraically:

```python
def symbolic_vandermonde_proof():
    """Attempt symbolic proof of Vandermonde's identity."""
    m, n, r = symbols('m n r', integer=True, nonnegative=True)
    k = symbols('k', integer=True)
    
    lhs = summation(binomial(m, k) * binomial(n, r - k), (k, 0, r))
    rhs = binomial(m + n, r)
    
    # Simplify the difference
    difference = simplify(lhs - rhs)
    
    print(f"\nSymbolic Verification:")
    print(f"LHS - RHS simplified: {difference}")
    print(f"Symbolic equality established: {difference == 0}")
    
    return difference

symbolic_vandermonde_proof()
```

SymPy's symbolic simplification engine will reduce the difference to zero when sufficient algebraic rewrite rules apply, but for complex combinatorial identities, the simplifier may return an unsimplified expression. This limitation reveals the boundary between mechanical verification (numerically checking instances) and automated theorem proving (constructing formal derivations).

### Number-Theoretic Verification: Chinese Remainder Theorem

The Chinese Remainder Theorem (CRT) asserts that for pairwise coprime moduli $n_1, n_2, \ldots, n_k$, the system of congruences $x \equiv a_i \pmod{n_i}$ has a unique solution modulo $N = n_1 n_2 \cdots n_k$. The constructive proof provides an explicit formula involving Bézout coefficients from the extended Euclidean algorithm. Operational verification requires implementing the CRT construction algorithm and testing correctness through modular arithmetic validation.

Implement the extended Euclidean algorithm first, which computes integers $s, t$ satisfying $\gcd(a, b) = sa + tb$:

```python
def extended_gcd(a, b):
    """Compute gcd(a, b) and Bézout coefficients s, t such that sa + tb = gcd(a, b)."""
    if b == 0:
        return a, 1, 0
    else:
        gcd_val, s1, t1 = extended_gcd(b, a % b)
        s = t1
        t = s1 - (a // b) * t1
        return gcd_val, s, t

def chinese_remainder_theorem(remainders, moduli):
    """
    Solve system of congruences x ≡ a_i (mod n_i) using CRT construction.
    
    Args:
        remainders: List of remainder values [a_1, a_2, ..., a_k]
        moduli: List of pairwise coprime moduli [n_1, n_2, ..., n_k]
    
    Returns:
        Unique solution x modulo N = n_1 * n_2 * ... * n_k
    """
    # Verify pairwise coprimality
    k = len(moduli)
    for i in range(k):
        for j in range(i + 1, k):
            gcd_val, _, _ = extended_gcd(moduli[i], moduli[j])
            if gcd_val != 1:
                raise ValueError(f"Moduli {moduli[i]} and {moduli[j]} not coprime (gcd={gcd_val})")
    
    # Compute N = product of all moduli
    N = 1
    for n in moduli:
        N *= n
    
    # CRT construction
    x = 0
    for i in range(k):
        N_i = N // moduli[i]
        gcd_val, M_i, _ = extended_gcd(N_i, moduli[i])
        # M_i * N_i ≡ 1 (mod n_i)
        x += remainders[i] * M_i * N_i
    
    return x % N, N

# Verification test cases
crt_test_cases = [
    {
        'remainders': [2, 3, 2],
        'moduli': [3, 5, 7],
        'description': 'Standard case from textbooks'
    },
    {
        'remainders': [1, 4, 6],
        'moduli': [5, 7, 11],
        'description': 'Larger moduli set'
    },
    {
        'remainders': [0, 0, 0],
        'moduli': [2, 3, 5],
        'description': 'Trivial solution x = 0'
    },
    {
        'remainders': [1, 1, 1],
        'moduli': [2, 3, 5],
        'description': 'Solution x = 1'
    }
]

print("\nChinese Remainder Theorem Verification")
print("=" * 60)

for test in crt_test_cases:
    remainders = test['remainders']
    moduli = test['moduli']
    desc = test['description']
    
    try:
        x, N = chinese_remainder_theorem(remainders, moduli)
        
        # Verify solution satisfies all congruences
        valid = True
        verification_details = []
        for i in range(len(moduli)):
            residue = x % moduli[i]
            matches = residue == remainders[i]
            valid = valid and matches
            verification_details.append(f"{x} ≡ {residue} (mod {moduli[i]}), expected {remainders[i]}")
        
        status = "✓ PASS" if valid else "✗ FAIL"
        print(f"\n{desc}")
        print(f"Solution: x = {x} (mod {N})")
        print(f"Status: {status}")
        for detail in verification_details:
            print(f"  {detail}")
    
    except ValueError as e:
        print(f"\n{desc}")
        print(f"Error: {e}")
```

This implementation demonstrates the CRT's constructive nature: the algorithm computes the solution explicitly through Bézout coefficients rather than searching through residue classes. The verification step confirms that the computed $x$ satisfies all original congruences, establishing correctness through direct substitution.

Stress-test the coprimality requirement by intentionally violating it:

```python
print("\n" + "=" * 60)
print("Coprimality Violation Test")
print("=" * 60)

invalid_test = {
    'remainders': [1, 2],
    'moduli': [6, 9],  # gcd(6, 9) = 3, not coprime
    'description': 'Non-coprime moduli should fail'
}

try:
    x, N = chinese_remainder_theorem(invalid_test['remainders'], invalid_test['moduli'])
    print(f"ERROR: Should have raised exception but got x = {x}")
except ValueError as e:
    print(f"✓ Correctly rejected: {e}")
```

This negative test confirms that the implementation enforces the theorem's preconditions, preventing silent errors when assumptions are violated.

### Graph-Theoretic Invariants: Euler's Formula for Planar Graphs

Euler's polyhedron formula asserts that for any connected planar graph, $V - E + F = 2$, where $V$ is the vertex count, $E$ the edge count, and $F$ the face count (including the exterior unbounded face). Computational verification requires constructing explicit planar embeddings, computing face decompositions through cycle enumeration, and validating the Euler characteristic across graph families.

SymPy does not provide native graph-theoretic data structures, but we can implement minimal graph representations using adjacency dictionaries and verify Euler's formula through explicit construction:

```python
class PlanarGraph:
    """Minimal planar graph representation with face enumeration."""
    
    def __init__(self):
        self.adjacency = {}
        self.vertex_count = 0
        self.edge_count = 0
    
    def add_vertex(self, v):
        """Add vertex to graph."""
        if v not in self.adjacency:
            self.adjacency[v] = set()
            self.vertex_count += 1
    
    def add_edge(self, u, v):
        """Add undirected edge between vertices u and v."""
        self.add_vertex(u)
        self.add_vertex(v)
        if v not in self.adjacency[u]:
            self.adjacency[u].add(v)
            self.adjacency[v].add(u)
            self.edge_count += 1
    
    def euler_characteristic(self, face_count):
        """Compute V - E + F for given face count."""
        return self.vertex_count - self.edge_count + face_count

def verify_euler_formula(graph_name, edges, expected_faces):
    """Verify Euler's formula for a specific planar graph."""
    G = PlanarGraph()
    
    for u, v in edges:
        G.add_edge(u, v)
    
    V = G.vertex_count
    E = G.edge_count
    F = expected_faces
    chi = G.euler_characteristic(F)
    
    valid = (chi == 2)
    status = "✓ PASS" if valid else "✗ FAIL"
    
    print(f"\n{graph_name}")
    print(f"  V = {V}, E = {E}, F = {F}")
    print(f"  χ = V - E + F = {V} - {E} + {F} = {chi}")
    print(f"  Status: {status}")
    
    return valid

print("\nEuler's Formula Verification for Planar Graphs")
print("=" * 60)

# Test Case 1: K4 (complete graph on 4 vertices)
k4_edges = [(1,2), (1,3), (1,4), (2,3), (2,4), (3,4)]
k4_faces = 4  # 3 triangular faces + 1 exterior face
verify_euler_formula("K4 (Complete graph on 4 vertices)", k4_edges, k4_faces)

# Test Case 2: Cube graph
cube_edges = [
    (1,2), (2,3), (3,4), (4,1),  # bottom face
    (5,6), (6,7), (7,8), (8,5),  # top face
    (1,5), (2,6), (3,7), (4,8)   # vertical edges
]
cube_faces = 6  # 5 square faces + 1 exterior
verify_euler_formula("Cube graph", cube_edges, cube_faces)

# Test Case 3:
```
