# Operational Verification Labs: Graph Theory

## Objective & Mathematical Computing Setup

These labs treat graph theory as a living computational science rather than a static body of definitions. The goal is to verify graph-theoretic theorems through direct symbolic execution and formal proof, so that every abstract claim becomes something you can run, challenge, and break. By the end, you will have implemented structural invariants from scratch, stress-tested classical theorems at their degenerate boundaries, and encoded formal proofs in a proof assistant, gaining the dual fluency that separates a practitioner from a student.

The mathematical objects we work with are precise. A graph $G = (V, E)$ consists of a finite vertex set $V$ and an edge set $E \subseteq \binom{V}{2}$, where $\binom{V}{2}$ denotes the set of all 2-element subsets of $V$. The degree of a vertex $v \in V$ is $\deg(v) = |\{u \in V : \{u,v\} \in E\}|$. The degree sequence of $G$ is the non-increasing list of all vertex degrees. A graph is connected if every pair of distinct vertices is joined by a path. A tree is a connected acyclic graph. A planar graph is one admitting an embedding in the plane $\mathbb{R}^2$ without edge crossings. These definitions are not backdrop; they are the objects you will interrogate computationally.

Your environment requires Python 3.11 or later with SymPy, NumPy, and NetworkX. SageMath provides higher-level algebraic graph invariants and is used in Exercise 3. Lean 4 (with Mathlib) handles formal proof obligations. Verify the core stack before proceeding.

```text
pip install sympy numpy networkx
python -c "import sympy; print('SymPy', sympy.__version__)"
python -c "import networkx as nx; print('NetworkX', nx.__version__)"
python -c "import numpy as np; print('NumPy', np.__version__)"
```

For SageMath, the recommended path is the official Docker image, which ships a self-contained environment with no dependency conflicts:

```bash
docker pull sagemath/sagemath:latest
docker run -it sagemath/sagemath:latest sage
```

For Lean 4 with Mathlib, initialize a project using the Lake build system:

```bash
curl -sSf https://raw.githubusercontent.com/leanprover/elan/master/elan-init.sh | sh
lake new graph_proofs math
cd graph_proofs
lake exe cache get
```

With the environment confirmed, the lab work begins.

---

## Exercise 1: Computational Verification of Core Theorems

### 1.1 The Handshaking Lemma

The Handshaking Lemma is the foundational parity constraint of graph theory, and it is both simple to state and surprisingly powerful to verify computationally across adversarial inputs. The theorem asserts that for any graph $G = (V, E)$,

$$\sum_{v \in V} \deg(v) = 2|E|$$

The proof follows immediately from the observation that each edge $\{u, v\}$ contributes exactly 1 to $\deg(u)$ and exactly 1 to $\deg(v)$, so the sum over all vertices counts each edge exactly twice. As an immediate corollary, the number of vertices of odd degree is always even. These two facts together govern the existence of Eulerian circuits, the structure of bipartite graphs, and the feasibility of degree sequence realizations.

The following program builds a symbolic representation of an arbitrary graph over a parameterized edge set, computes both sides of the identity using SymPy's summation machinery, and asserts their equality. It then runs a Monte Carlo sweep over 10,000 random graphs of varying order and size, reporting any failure.

```python
import sympy as sp
import networkx as nx
import random
import itertools

def handshaking_symbolic():
    """
    Verify the Handshaking Lemma symbolically using SymPy.
    We build the degree sequence as a SymPy expression and confirm
    that summing it equals twice the edge count.
    """
    # Construct a specific graph with symbolic edge indicators
    # Use a 6-vertex graph encoded as an adjacency list
    edges = [(0,1), (0,2), (1,2), (1,3), (3,4), (4,5), (2,5)]
    n = 6
    degrees = [0] * n
    for u, v in edges:
        degrees[u] += 1
        degrees[v] += 1

    lhs = sum(degrees)
    rhs = 2 * len(edges)

    lhs_sym = sp.Integer(lhs)
    rhs_sym = sp.Integer(rhs)

    diff = sp.simplify(lhs_sym - rhs_sym)
    assert diff == 0, f"Handshaking failed: LHS={lhs}, RHS={rhs}"
    print(f"Symbolic check passed: sum of degrees = {lhs}, 2|E| = {rhs}, difference = {diff}")

    # Verify the odd-degree corollary
    odd_degree_count = sum(1 for d in degrees if d % 2 != 0)
    assert odd_degree_count % 2 == 0, f"Odd degree count {odd_degree_count} is not even"
    print(f"Odd-degree vertex count: {odd_degree_count} (must be even) — verified")

def handshaking_monte_carlo(trials=10000):
    """
    Stress test across 10,000 random graphs. For each, assert the lemma holds.
    """
    failures = 0
    for _ in range(trials):
        n = random.randint(2, 20)
        # Build a random simple graph by sampling edges from all possible pairs
        all_possible = list(itertools.combinations(range(n), 2))
        k = random.randint(0, len(all_possible))
        edges = random.sample(all_possible, k)

        degrees = [0] * n
        for u, v in edges:
            degrees[u] += 1
            degrees[v] += 1

        if sum(degrees) != 2 * len(edges):
            failures += 1

    print(f"Monte Carlo: {trials} trials, {failures} failures (expected 0)")

handshaking_symbolic()
handshaking_monte_carlo(trials=10000)
```

### 1.2 Euler's Formula for Planar Graphs

For any connected planar graph embedded in the sphere $S^2$ (or equivalently the plane $\mathbb{R}^2$ with one unbounded face), Euler's formula states

$$V - E + F = 2$$

where $V = |V|$, $E = |E|$, and $F$ is the number of faces (regions, including the unbounded outer face). The proof proceeds by induction on $E$. For the base case, a tree on $n$ vertices has $n - 1$ edges and exactly 1 face (the outer face), giving $n - (n-1) + 1 = 2$. For the inductive step, if $G$ has a cycle, remove any edge $e$ on that cycle; this merges two faces into one, so $E$ decreases by 1 and $F$ decreases by 1, leaving $V - E + F$ unchanged. If $G$ has no cycle, it is a tree and we apply the base case. This yields two critical inequalities: for any simple connected planar graph with $V \geq 3$, we have $E \leq 3V - 6$, and if the graph is additionally triangle-free (girth at least 4), then $E \leq 2V - 4$. These inequalities are what make $K_5$ and $K_{3,3}$ non-planar, as we now verify.

```python
import sympy as sp
import networkx as nx
import itertools

def euler_formula_check(G_nx, embedding=None):
    """
    Given a NetworkX planar graph and its combinatorial embedding,
    compute V, E, F and verify V - E + F = 2.
    Returns (V, E, F, Euler_characteristic).
    """
    assert nx.is_connected(G_nx), "Graph must be connected for Euler's formula"
    is_planar, planar_embedding = nx.check_planarity(G_nx)
    assert is_planar, "Graph is not planar"

    V = G_nx.number_of_nodes()
    E = G_nx.number_of_edges()

    # Count faces using the planar embedding's half-edge traversal
    # NetworkX's PlanarEmbedding provides traverse_face()
    visited_half_edges = set()
    F = 0
    for v in planar_embedding.nodes():
        for w in planar_embedding.neighbors_cw_order(v):
            if (v, w) not in visited_half_edges:
                face = planar_embedding.traverse_face(v, w)
                face_edges = [(face[i], face[(i+1) % len(face)]) for i in range(len(face))]
                for he in face_edges:
                    visited_half_edges.add(he)
                F += 1

    chi = V - E + F
    return V, E, F, chi

def verify_euler_on_examples():
    # Cube graph: V=8, E=12, expected F=6
    cube = nx.cubical_graph()
    V, E, F, chi = euler_formula_check(cube)
    print(f"Cube graph: V={V}, E={E}, F={F}, chi=V-E+F={chi} (expected 2)")
    assert chi == 2

    # Petersen-free test: dodecahedron
    dodec = nx.dodecahedral_graph()
    V, E, F, chi = euler_formula_check(dodec)
    print(f"Dodecahedron: V={V}, E={E}, F={F}, chi=V-E+F={chi} (expected 2)")
    assert chi == 2

    # Wheel graph W_6: V=7, E=12
    wheel = nx.wheel_graph(7)
    V, E, F, chi = euler_formula_check(wheel)
    print(f"Wheel W_6: V={V}, E={E}, F={F}, chi=V-E+F={chi} (expected 2)")
    assert chi == 2

def verify_nonplanarity_inequality():
    """
    Use E <= 3V - 6 to confirm K5 and K_{3,3} are non-planar before
    calling the full planarity check, demonstrating the inequality as a filter.
    """
    K5 = nx.complete_graph(5)
    V_K5, E_K5 = K5.number_of_nodes(), K5.number_of_edges()
    bound_K5 = 3 * V_K5 - 6
    print(f"K5: V={V_K5}, E={E_K5}, 3V-6={bound_K5}. E > 3V-6: {E_K5 > bound_K5}")
    assert E_K5 > bound_K5, "K5 should violate planarity inequality"

    K33 = nx.complete_bipartite_graph(3, 3)
    V_K33, E_K33 = K33.number_of_nodes(), K33.number_of_edges()
    # K_{3,3} is triangle-free, so apply the tighter bound E <= 2V - 4
    bound_K33_tight = 2 * V_K33 - 4
    print(f"K_{{3,3}}: V={V_K33}, E={E_K33}, 2V-4={bound_K33_tight}. E > 2V-4: {E_K33 > bound_K33_tight}")
    assert E_K33 > bound_K33_tight, "K_{3,3} should violate triangle-free planarity inequality"

    # Confirm with full planarity test
    assert not nx.is_planar(K5), "K5 planarity check should return False"
    assert not nx.is_planar(K33), "K_{3,3} planarity check should return False"
    print("Non-planarity of K5 and K_{3,3} confirmed by both inequality and algorithm.")

verify_euler_on_examples()
verify_nonplanarity_inequality()
```

### 1.3 Verification of the Erdős–Gallai Theorem

The Erdős–Gallai theorem characterizes precisely which non-increasing integer sequences $(d_1, d_2, \ldots, d_n)$ are realizable as degree sequences of simple graphs. The sequence is graphical if and only if its sum is even and for each $k \in \{1, 2, \ldots, n\}$,

$$\sum_{i=1}^{k} d_i \leq k(k-1) + \sum_{i=k+1}^{n} \min(d_i, k)$$

The left side counts the maximum number of edges that could be incident to the $k$ highest-degree vertices among themselves and toward the rest. The right side counts the theoretical maximum: $k(k-1)$ edges among the $k$ vertices themselves, plus at most $\min(d_i, k)$ edges from each remaining vertex into the top $k$. The theorem asserts that these necessary conditions are also jointly sufficient, a non-trivial claim whose proof proceeds by constructing a realization via the Erdős–Gallai construction (or equivalently, the Hakimi algorithm).

```python
import sympy as sp
import networkx as nx

def erdos_gallai_check(sequence):
    """
    Verify whether a non-increasing integer sequence is graphical
    using the Erdos-Gallai conditions. Returns True if graphical.
    """
    d = sorted(sequence, reverse=True)
    n = len(d)

    # Condition 1: sum must be even
    if sum(d) % 2 != 0:
        return False, "Sum of degrees is odd"

    # Condition 2: all degrees non-negative and at most n-1
    if any(di < 0 for di in d) or any(di >= n for di in d):
        return False, "Degree out of valid range [0, n-1]"

    # Condition 3: Erdos-Gallai inequalities for each k
    for k in range(1, n + 1):
        lhs = sum(d[:k])
        rhs = k * (k - 1) + sum(min(d[i], k) for i in range(k, n))
        if lhs > rhs:
            return False, f"Erdos-Gallai violated at k={k}: LHS={lhs} > RHS={rhs}"

    return True, "Sequence is graphical"

def hakimi_realize(sequence):
    """
    Realize a graphical sequence as an explicit graph using the Hakimi algorithm.
    At each step, take the vertex with the highest degree d_max, connect it to
    the next d_max vertices in sorted order, decrement their degrees, and repeat.
    """
    n = len(sequence)
    # Track (degree, vertex_id)
    indexed = [(sequence[i], i) for i in range(n)]
    edges = []

    while True:
        indexed.sort(key=lambda x: -x[0])
        # Remove zero-degree vertices for termination check
        if all(d == 0 for d, _ in indexed):
            break
        d_max, v = indexed[0]
        if d_max == 0:
            break
        if d_max > len(indexed) - 1:
            raise ValueError(f"Degree {d_max} exceeds remaining vertices {len(indexed)-1}")
        for j in range(1, d_max + 1):
            dj, u = indexed[j]
            edges.append((v, u))
            indexed[j] = (dj - 1, u)
        indexed[0] = (0, v)

    G = nx.Graph()
    G.add_nodes_from(range(n))
    G.add_edges_from(edges)
    return G

def verify_erdos_gallai():
    test_cases = [
        ([3, 3, 2, 2, 2],     True,  "Pentagon + extra"),
        ([4, 3, 3, 2, 2],     True,  "K4 minus one edge + pendant"),
        ([3, 3, 3, 3],        True,  "Complete graph K4"),
        ([5, 3, 3, 3, 2],     False, "Sum is odd"),
        ([4, 4, 4, 4, 4],     False, "Sum is odd again"),
        ([3, 3, 3, 3, 3, 3],  True,  "K_{3,3} degree sequence"),
        ([1, 1, 1, 1, 1],     False, "Sum is odd (5 ones)"),
        ([2, 2, 2, 2],        True,  "4-cycle"),
        ([3, 3, 3, 3, 2, 2],  True,  "Valid complex sequence"),
        ([5, 5, 5, 0, 0, 0],  False, "EG violated at k=3"),
    ]

    for seq, expected_graphical, label in test_cases:
        is_graphical, reason = erdos_gallai_check(seq)
        status = "PASS" if (is_graphical == expected_graphical) else "FAIL"
        print(f"[{status}] {label}: {seq} -> graphical={is_graphical} ({reason})")

        if is_graphical:
            G = hakimi_realize(list(seq))
            realized_degrees = sorted([d for _, d in G.degree()], reverse=True)
            realized_degrees_trimmed = realized_degrees[:len(seq)]
            # Pad with zeros if needed
            while len(realized_degrees_trimmed) < len(seq):
                realized_degrees_trimmed.append(0)
            assert realized_degrees_trimmed == sorted(seq, reverse=True), \
                f"Hakimi realization degree mismatch: got {realized_degrees_trimmed}"
            print(f"       Hakimi realization verified: degree sequence matches.")

verify_erdos_gallai()
```

---

## Exercise 2: Boundary Value Stress Testing & Singularities

Graph theorems frequently carry implicit assumptions that collapse at degenerate boundaries: the empty graph, the complete graph, trees, graphs with isolated vertices, or graphs with self-loops in a simple-graph framework. This exercise systematically probes those boundaries to understand not just where theorems hold, but where and how they degrade.

### 2.1 Chromatic Polynomial at Degenerate Inputs

The chromatic polynomial $P(G, k)$ of a graph $G$ is the unique polynomial in $k$ such that $P(G, k)$ counts the number of proper $k$-colorings of $G$ for every non-negative integer $k$. It is defined recursively via the deletion-contraction identity

$$P(G, k) = P(G - e, k) - P(G / e, k)$$

where $G - e$ is $G$ with edge $e$ deleted and $G / e$ is $G$ with $e$ contracted (the two endpoints merged). The base cases are $P(K_1, k) = k$ for a single vertex and $P(\bar{K}_n, k) = k^n$ for the empty graph on $n$ vertices (no edges). The chromatic polynomial has remarkable algebraic properties: its evaluation at $k = 0$ is always 0, its evaluation at $k = 1$ is 0 for any graph with at least one edge, its leading term is $k^{|V|}$, and $(-1)^{|V|} P(G, -1)$ equals the number of acyclic orientations of $G$ (a theorem due to Stanley).

The degenerate stress tests worth running are: the null graph (no vertices), the edgeless graph, the complete graph $K_n$, trees, cycles, and graphs containing self-loops (which have chromatic polynomial identically 0 for all $k \geq 1$).

```python
import sympy as sp
import networkx as nx
from itertools import combinations

def chromatic_polynomial_deletion_contraction(G, k_sym):
    """
    Compute the chromatic polynomial of graph G using deletion-contraction.
    G is a NetworkX graph. k_sym is a SymPy symbol.
    Returns a SymPy polynomial expression in k_sym.
    """
    # Base case: no edges
    if G.number_of_edges() == 0:
        n = G.number_of_nodes()
        return k_sym ** n

    # Base case: complete graph Kn
    n = G.number_of_nodes()
    if G.number_of_edges() == n * (n - 1) // 2:
        result = sp.Integer(1)
        for i in range(n):
            result *= (k_sym - i)
        return sp.expand(result)

    # Pick an arbitrary edge for deletion-contraction
    u, v = next(iter(G.edges()))

    # G - e: delete edge (u, v)
    G_minus = G.copy()
    G_minus.remove_edge(u, v)

    # G / e: contract edge (u, v) — merge v into u, redirect all v's edges to u
    G_contract = G.copy()
    G_contract.remove_edge(u, v)
    for neighbor in list(G_contract.neighbors(v)):
        if neighbor != u:
            G_contract.add_edge(u, neighbor)
    G_contract.remove_node(v)
    # Relabel to maintain integer node labels
    mapping = {node: i for i, node in enumerate(G_contract.nodes())}
    G_contract = nx.relabel_nodes(G_contract, mapping)

    P_minus = chromatic_polynomial_deletion_contraction(G_minus, k_sym)
    P_contract = chromatic_polynomial_deletion_contraction(G_contract, k_sym)

    return sp.expand(P_minus - P_contract)

def stress_test_chromatic_polynomial():
    k = sp.Symbol('k')

    print("=== Chromatic Polynomial Boundary Stress Tests ===\n")

    # Test 1: Empty graph (no vertices)
    G_empty = nx.Graph()
    P_empty = chromatic_polynomial_deletion_contraction(G_empty, k)
    print(f"Empty graph (0 vertices): P(G,k) = {P_empty}")
    assert P_empty == 1, "P(empty graph, k) should be 1 (empty product)"
    # NetworkX returns k^0 = 1

    # Test 2: Single vertex
    G_single = nx.Graph()
    G_single.add_node(0)
    P_single = chromatic_polynomial_deletion_contraction(G_single, k)
    print(f"Single vertex K1: P(G,k) = {P_single}")
    assert sp.simplify(P_single - k) == 0

    # Test 3: Edgeless graph on 4 vertices (independent set)
    G_edgeless = nx.Graph()
    G_edgeless.add_nodes_from(range(4))
    P_edgeless = chromatic_polynomial_deletion_contraction(G_edgeless, k)
    print(f"Edgeless graph on 4 vertices: P(G,k) = {P_edgeless}")
    assert sp.simplify(P_edgeless - k**4) == 0

    # Test 4: Complete graph K4 — expected k(k-1)(k-2)(k-3)
    G_K4 = nx.complete_graph(4)
    P_K4 = chromatic_polynomial_deletion_contraction(G_K4, k)
    P_K4_expected = sp.expand(k * (k-1) * (k-2) * (k-3))
    print(f"K4: P(G,k) = {P_K4}")
    assert sp.simplify(P_K4 - P_K4_expected) == 0, f"K4 mismatch: got {P_K4}"

    # Test 5: Path graph P4 (4 vertices, 3 edges in a line)
    G_P4 = nx.path_graph(4)
    P_P4 = chromatic_polynomial_deletion_contraction(G_P4, k)
    # Path Pn has chromatic polynomial k(k-1)^{n-1}
    P_P4_expected = sp.expand(k * (k-1)**3)
    print(f"Path P4: P(G,k) = {P_P4}, expected = {P_P4_expected}")
    assert sp.simplify(P_P4 - P_P4_expected) == 0

    # Test 6: Cycle C5 — expected (k-1)^5 + (k-1)
    G_C5 = nx.cycle_graph(5)
    P_C5 = chromatic_polynomial_deletion_contraction(G_C5, k)
    P_C5_expected = sp.expand((k-1)**5 + (k-1))
    print(f"Cycle C5: P(G,k) = {P_C5}, expected = {P_C5_expected}")
    assert sp.simplify(P_C5 - P_C5_expected) == 0

    # Test 7: Evaluate at k=0 (must be 0 for all non-empty graphs)
    for G, name in [(G_K4, "K4"), (G_P4, "P4"), (G_C5, "C5")]:
        P = chromatic_polynomial_deletion_contraction(G, k)
        val_at_0 = P.subs(k, 0)
        assert val_at_0 == 0, f"P({name}, 0) = {val_at_0}, expected 0"
    print("P(G, 0) = 0 for K4, P4, C5 — verified")

    # Test 8: Stanley's acyclic orientation theorem: (-1)^|V| * P(G, -1) = #acyclic orientations
    # For a tree Tn on n vertices, there are 2^{n-1} acyclic orientations
    G_tree = nx.path_graph(5)  # This is a path tree on 5 vertices
    n_tree = G_tree.number_of_nodes()
    P_tree = chromatic_polynomial_deletion_contraction(G_tree, k)
    stanley_value = ((-1)**n_tree) * P_tree.subs(k, -1)
    expected_acyclic = 2 ** (n_tree - 1)
    print(f"Stanley's theorem on P5 (path/tree): (-1)^5 * P(G,-1) = {stanley_value}, "
          f"expected 2^{{n-1}} = {expected_acyclic}")
    assert stanley_value == expected_acyclic

stress_test_chromatic_polynomial()
```

### 2.2 Spectral Graph Theory: Eigenvalue Degeneracies and Singular Cases

The adjacency matrix $A$ of a graph $G$ on $n$ vertices is the $n \times n$ symmetric matrix with $A_{ij} = 1$ if $\{i,j\} \in E$ and $A_{ij} = 0$ otherwise. Because $A$ is real symmetric, its eigenvalues $\lambda_1 \geq \lambda_2 \geq \cdots \geq \lambda_n$ are real and form the spectrum of $G$. The normalized Laplacian is $\mathcal{L} = D^{-1/2} A D^{-1/2}$ where $D$ is the diagonal degree matrix, and the combinatorial Laplacian is $L = D - A$. The Laplacian $L$ is positive semidefinite; its smallest eigenvalue is always 0 (with eigenvector the all-ones vector $\mathbf{1}$), and by the Matrix-Tree Theorem, the product of all nonzero Laplacian eigenvalues divided by $n$ equals the number of spanning trees:

$$\tau(G) = \frac{1}{n} \prod_{i=1}^{n-1} \mu_i$$

where $\mu_1 \leq \mu_2 \leq \cdots \leq \mu_{n-1}$ are the $n-1$ nonzero eigenvalues of $L$. Degenerate cases arise when the graph is disconnected (the zero eigenvalue has multiplicity equal to the number of connected components, making $\tau = 0$), when the graph is a tree (exactly $n-1$ eigenvalues are nonzero and $\tau = 1$), and when the graph is complete ($\tau(K_n) = n^{n-2}$ by Cayley's formula).

```python
import numpy as np
import sympy as sp
import networkx as nx
from fractions import Fraction

def laplacian_matrix(G):
    """Return the combinatorial Laplacian L = D - A as a NumPy array."""
    n = G.number_of_nodes()
    nodes = sorted(G.nodes())
    node_idx = {v: i for i, v in enumerate(nodes)}
    A = np.zeros((n, n), dtype=float)
    for u, v in G.edges():
        i, j = node_idx[u], node_idx[v]
        A[i][j] = 1.0
        A[j][i] = 1.0
    D = np.diag(A.sum(axis=1))
    return D - A

def spanning_tree_count_kirchhoff(G):
    """
    Compute tau(G) using Kirchhoff's Matrix-Tree Theorem:
    tau(G) = (1/n) * product of nonzero Laplacian eigenvalues.
    Use SymPy for exact integer arithmetic via the Laplacian cofactor.
    """
    n = G.number_of_nodes()
    if n == 0:
        return 0
    nodes = sorted(G.nodes())
    node_idx = {v: i for i, v in enumerate(nodes)}

    # Build Laplacian with SymPy rational arithmetic for exactness
    L = sp.zeros(n, n)
    for u, v in G.edges():
        i, j = node_idx[u], node_idx[v]
        L[i, j] -= 1
        L[j, i] -= 1
        L[i, i] += 1
        L[j, j] += 1

    # tau(G) = any cofactor of L = det of (n-1)x(n-1) submatrix
    # obtained by deleting row 0 and column 0
    L_reduced = L.minor_submatrix(0, 0)
    return int(L_reduced.det())

def stress_test_matrix_tree():
    print("=== Matrix-Tree Theorem Boundary Stress Tests ===\n")

    # Test 1: Tree on 5 vertices — exactly 1 spanning tree
    G_tree = nx.path_graph(5)
    tau = spanning_tree_count_kirchhoff(G_tree)
    print(f"Path tree P5: tau = {tau} (expected 1)")
    assert tau == 1

    # Test 2: Cycle C5 — exactly 5 spanning trees
    G_C5 = nx.cycle_graph(5)
    tau = spanning_tree_count_kirchhoff(G_C5)
    print(f"Cycle C5: tau = {tau} (expected 5)")
    assert tau == 5

    # Test 3: Complete graph K4 — tau(K4) = 4^(4-2) = 16 by Cayley
    G_K4 = nx.complete_graph(4)
    tau = spanning_tree_count_kirchhoff(G_K4)
    cayley = 4 ** (4 - 2)
    print(f"Complete K4: tau = {tau} (expected Cayley {cayley})")
    assert tau == cayley

    # Test 4: Complete graph K5 — tau(K5) = 5^3 = 125
    G_K5 = nx.complete_graph(5)
    tau = spanning_tree_count_kirchhoff(G_K5)
    cayley_K5 = 5 ** 3
    print(f"Complete K5: tau = {tau} (expected {cayley_K5})")
    assert tau == cayley_K5

    # Test 5: Disconnected graph — tau = 0 (no spanning tree exists)
    G_disc = nx.Graph()
    G_disc.add_nodes_from([0, 1, 2, 3])
    G_disc.add_edge(0, 1)
    # nodes 2 and 3 are isolated
    tau = spanning_tree_count_kirchhoff(G_disc)
    print(f"Disconnected graph: tau = {tau} (expected 0)")
    assert tau == 0

    # Test 6: Single edge K2 — tau = 1
    G_K2 = nx.complete_graph(2)
    tau = spanning_tree_count_kirchhoff(G_K2)
    print(f"Complete K2 (single edge): tau = {tau} (expected 1)")
    assert tau == 1

    # Test 7: Petersen graph — tau should equal 2000
    G_petersen = nx.petersen_graph()
    tau = spanning_tree_count_kirchhoff(G_petersen)
    print(f"Petersen graph: tau = {tau} (expected 2000)")
    assert tau == 2000

    # Test 8: Verify spectral formula numerically against cofactor formula for K6
    G_K6 = nx.complete_graph(6)
    n = G_K6.number_of_nodes()
    L_np = laplacian_matrix(G_K6)
    eigenvalues = np.linalg.eigvalsh(L_np)
    nonzero_eigs = eigenvalues[eigenvalues > 1e-10]
    tau_spectral = round(np.prod(nonzero_eigs) / n)
    tau_exact = spanning_tree_count_kirchhoff(G_K6)
    cayley_K6 = 6 ** 4
    print(f"K6: tau_exact={tau_exact}, tau_spectral={tau_spectral}, Cayley={cayley_K6}")
    assert tau_exact == cayley_K6
    assert abs(tau_spectral - cayley_K6) < 1, f"Spectral approximation error: {tau_spectral}"

stress_test_matrix_tree()
```

### 2.3 Menger's Theorem and Max-Flow Min-Cut at Boundary Configurations

Menger's theorem is the fundamental vertex-connectivity result: for any two non-adjacent vertices $s$ and $t$ in a graph $G$, the maximum number of internally vertex-disjoint $s$-$t$ paths equals the minimum number of vertices whose removal disconnects $s$ from $t$. The edge version replaces vertex-disjoint with edge-disjoint and vertex cuts with edge cuts (bonds). The edge version is exactly the max-flow min-cut theorem when all edge capacities are 1. Degenerate cases include $s$ and $t$ being adjacent (the minimum cut is then at most $\deg(s)$, and one must be careful about whether the shared edge is included in the cut), complete graphs (where vertex connectivity equals $n-1$), and disconnected graphs (where the minimum cut is 0).

```python
import networkx as nx

def menger_vertex_disjoint_paths(G, s, t):
    """
    Compute the maximum number of internally vertex-disjoint s-t paths
    using NetworkX's node connectivity, which implements Menger's theorem
    via unit-capacity node-splitting max-flow.
    """
    return nx.node_connectivity(G, s, t)

def menger_edge_disjoint_paths(G, s, t):
    """
    Compute the maximum number of edge-disjoint s-t paths
    using unit-capacity max-flow (Ford-Fulkerson).
    """
    return nx.edge_connectivity(G, s, t)

def verify_menger_theorem():
    print("=== Menger's Theorem Boundary Stress Tests ===\n")

    # Test 1: Path graph P6 — only 1 vertex-disjoint path between ends
    G = nx.path_graph(6)
    vdp = menger_vertex_disjoint_paths(G, 0, 5)
    print(f"Path P6, s=0, t=5: vertex-disjoint paths = {vdp} (expected 1)")
    assert vdp == 1

    # Test 2: Grid graph 3x3 — corner-to-corner connectivity
    G_grid = nx.grid_2d_graph(3, 3)
    s_grid, t_grid = (0, 0), (2, 2)
    vdp_grid = menger_vertex_disjoint_paths(G_grid, s_grid, t_grid)
    edp_grid = menger_edge_disjoint_paths(G_grid, s_grid, t_grid)
    print(f"Grid 3x3, corner-to-corner: vertex-disjoint={vdp_grid}, edge-disjoint={edp_grid}")
    assert edp_grid >= vdp_grid  # edge-disjoint >= vertex-disjoint always

    # Test 3: Complete graph K6 — every pair has n-1 = 5 vertex-disjoint paths
    G_K6 = nx.complete_graph(6)
    for s, t in [(0,1), (0,5), (2,4)]:
        vdp = menger_vertex_disjoint_paths(G_K6, s, t)
        assert vdp == 5, f"K6 ({s},{t}): expected 5, got {vdp}"
    print(f"K6: all tested pairs have 5 vertex-disjoint paths — verified")

    # Test 4: Graph with a cut vertex (bridge/articulation point) — bottle-neck
    # Build a graph that is two triangles sharing a single vertex (articulation point at 2)
    G_bowtie = nx.Graph()
    G_bowtie.add_edges_from([(0,1),(1,2),(2,0)])   # first triangle
    G_bowtie.add_edges_from([(2,3),(3,4),(4,2)])   # second triangle
    # Path from 0 to 4 must pass through vertex 2
    vdp_bowtie = menger_vertex_disjoint_paths(G_bowtie, 0, 4)
    print(f"Bowtie (two triangles at vertex 2), s=0, t=4: vertex-disjoint paths = {vdp_bowtie} (expected 1)")
    assert vdp_bowtie == 1

    # Test 5: Petersen graph — 3-connected, so every non-adjacent pair has >=3 vertex-disjoint paths
    G_petersen = nx.petersen_graph()
    global_connectivity = nx.node_connectivity(G_petersen)
    print(f"Petersen graph global vertex connectivity: {global_connectivity} (expected 3)")
    assert global_connectivity == 3

    # Test 6: Disconnected graph — Menger count is 0
    G_disc = nx.Graph()
    G_disc.add_nodes_from([0,1,2,3])
    G_disc.add_edge(0,1)
    G_disc.add_edge(2,3)
    vdp_disc = menger_vertex_disjoint_paths(G_disc, 0, 3)
    print(f"Disconnected graph, s=0, t=3: vertex-disjoint paths = {vdp_disc} (expected 0)")
    assert vdp_disc == 0

verify_menger_theorem()
```

---

## Exercise 3: Algorithmic Implementation of Formal Structures

### 3.1 Graph Isomorphism via Canonical Labeling

Two graphs $G = (V, E)$ and $H = (V', E')$ are isomorphic, written $G \cong H$, if there exists a bijection $\phi: V \to V'$ such that $\{u,v\} \in E$ if and only if $\{\phi(u), \phi(v)\} \in E'$. Graph isomorphism occupies a unique complexity-theoretic position: it is in NP, not known to be NP-complete, and not known to be in P (Babai's 2015 quasipolynomial-time algorithm being the state of the art). For moderate graph sizes, canonical labeling via certificate strings provides a practical isomorphism test: compute a canonical form $\text{can}(G)$ such that $G \cong H$ if and only if $\text{can}(G) = \text{can}(H)$. NetworkX delegates to the `pynauty` backend or uses the Weisfeiler-Leman refinement for approximate certificates. For exact isomorphism checking, we use SageMath's `canonical_label()` which calls nauty/Traces.

```python
import networkx as nx
import numpy as np
from collections import defaultdict

def weisfeiler_leman_canonical_hash(G, iterations=10):
    """
    Compute a canonical hash for G using the 1-dimensional Weisfeiler-Leman
    (color refinement) algorithm. If two graphs produce different hashes,
    they are non-isomorphic. Equal hashes are necessary but not sufficient.

    Returns a sorted tuple of final color counts (the color histogram),
    which serves as a graph certificate under WL.
    """
    nodes = sorted(G.nodes())
    # Initialize color as degree
    color = {v: G.degree(v) for v in nodes}

    for _ in range(iterations):
        new_color = {}
        for v in nodes:
            neighbor_colors = sorted(color[u] for u in G.neighbors(v))
            # Hash the (current_color, sorted_neighbor_colors) tuple
            new_color[v] = hash((color[v], tuple(neighbor_colors)))
        # Normalize: relabel colors as integers by rank
        sorted_colors = sorted(set(new_color.values()))
        rank = {c: i for i, c in enumerate(sorted_colors)}
        color = {v: rank[new_color[v]] for v in nodes}

    # The certificate is the sorted sequence of final color labels
    histogram = sorted(color.values())
    return tuple(histogram)

def verify_graph_isomorphism():
    print("=== Graph Isomorphism via WL Canonical Hashing ===\n")

    # Test 1: Two labelings of the same 4-cycle — must hash identically
    C4_a = nx.cycle_graph(4)
    C4_b = nx.Graph()
    C4_b.add_edges_from([(0,2),(2,1),(1,3),(3,0)])  # Same 4-cycle, different edge order
    h_a = weisfeiler_leman_canonical_hash(C4_a)
    h_b = weisfeiler_leman_canonical_hash(C4_b)
    print(f"C4 variant A hash: {h_a}")
    print(f"C4 variant B hash: {h_b}")
    print(f"Hashes equal (should be True): {h_a == h_b}")
    # Confirm with NetworkX isomorphism
    assert nx.is_isomorphic(C4_a, C4_b)

    # Test 2: C4 vs K4 — must hash differently
    K4 = nx.complete_graph(4)
    h_K4 = weisfeiler_leman_canonical_hash(K4)
    print(f"\nC4 hash:  {h_a}")
    print(f"K4 hash:  {h_K4}")
    print(f"Hashes differ (should be True): {h_a != h_K4}")
    assert not nx.is_isomorphic(C4_a, K4)

    # Test 3: Two non-isomorphic cubic graphs on 6 vertices
    # K_{3,3} (bipartite, girth 4) vs prism graph (K3 x K2, girth 3)
    K33 = nx.complete_bipartite_graph(3, 3)
    prism = nx.circular_ladder_graph(3)
    h_K33 = weisfeiler_leman_canonical_hash(K33)
    h_prism = weisfeiler_leman_canonical_hash(prism)
    is_iso_nx = nx.is_isomorphic(K33, prism)
    print(f"\nK_{{3,3}} hash: {h_K33}")
    print(f"Prism hash:   {h_prism}")
    print(f"NetworkX isomorphic: {is_iso_nx} (expected False)")
    assert not is_iso_nx

    # Test 4: Petersen graph vs Kneser(5,2) — they ARE the same graph
    # Petersen graph = Kneser(5,2), so relabeled versions must be isomorphic
    petersen_1 = nx.petersen_graph()
    petersen_2 = nx.petersen_graph()
    # Relabel petersen_2 with a permutation
    import random
    perm = list(range(10))
    random.seed(42)
    random.shuffle(perm)
    mapping = {i: perm[i] for i in range(10)}
    petersen_2_relabeled = nx.relabel_nodes(petersen_2, mapping)
    h_p1 = weisfeiler_leman_canonical_hash(petersen_1)
    h_p2 = weisfeiler_leman_canonical_hash(petersen_2_relabeled)
    is_iso = nx.is_isomorphic(petersen_1, petersen_2_relabeled)
    print(f"\nPetersen vs relabeled Petersen: hashes equal={h_p1 == h_p2}, isomorphic={is_iso}")
    assert is_iso

verify_graph_isomorphism()
```

### 3.2 Formal Proof Verification in Lean 4: The Handshaking Lemma

The following Lean 4 code encodes a formal proof of the Handshaking Lemma for finite simple graphs using Mathlib's `SimpleGraph` API. The proof strategy follows the combinatorial argument: define a sum over directed edge incidences, then show that each undirected edge contributes exactly 2 to the sum. Save this file as `GraphProofs/Handshaking.lean` inside the Lake project initialized during setup.

```lean
-- GraphProofs/Handshaking.lean
-- Formal verification of the Handshaking Lemma using Lean 4 + Mathlib

import Mathlib.Combinatorics.SimpleGraph.Degree
import Mathlib.Algebra.BigOperators.Basic
import Mathlib.Data.Finset.Basic

open BigOperators SimpleGraph

/-!
## The Handshaking Lemma

For a finite simple graph `G` on vertex type `V`, the sum of all vertex
degrees equals twice the number of edges:

  ∑ v : V, G.degree v = 2 * G.edgeFinset.card

We prove this by showing that the sum of degrees counts each edge exactly
twice — once from each endpoint — which follows from the bijection between
the dart set (directed incidences) and pairs (edge, endpoint).
-/

variable {V : Type*} [Fintype V] [DecidableEq V]
         (G : SimpleGraph V) [DecidableRel G.Adj]

/-- The sum of all vertex degrees in a finite simple graph equals twice
    the number of edges. -/
theorem handshaking_lemma :
    ∑ v : V, G.degree v = 2 * G.edgeFinset.card := by
  -- Rewrite degree sum in terms of dart finset cardinality.
  -- G.dartFinset consists of ordered pairs (v, w) with v~w.
  -- Each undirected edge {u,v} contributes exactly 2 darts: (u,v) and (v,u).
  rw [← G.sum_degrees_eq_twice_card_edges]
```

The critical lemma `SimpleGraph.sum_degrees_eq_twice_card_edges` is proven in Mathlib by establishing a two-to-one correspondence between darts (directed incidences) and edges. Each dart is a pair $(v, w)$ with $v \sim w$, and the map sending a dart to its underlying undirected edge is exactly 2-to-1. The formal statement in Mathlib is:

```lean
-- From Mathlib.Combinatorics.SimpleGraph.Degree:
-- theorem SimpleGraph.sum_degrees_eq_twice_card_edges
--   {V : Type u_1} [Fintype V] [DecidableEq V]
--   (G : SimpleGraph V) [DecidableRel G.Adj] :
--   ∑ v, G.degree v = 2 * G.edgeFinset.card
```

To extend this to a constructive verification of Euler's formula, the following Lean sketch uses Mathlib's `Finset` infrastructure. The full Euler formula proof for planar graphs requires considerably more Mathlib infrastructure around planar embeddings (which is still being actively developed in Mathlib4), but the combinatorial core — that for a connected planar graph the Euler characteristic is 2 — can be verified for specific finite instances using `decide`:

```lean
-- EulerVerify.lean: Instance-level decision procedure for small planar graphs
import Mathlib.Combinatorics.SimpleGraph.Basic
import Mathlib.Data.Fin.Basic

-- Define the cube graph on 8 vertices as a concrete SimpleGraph (Fin 8)
def cubeAdj : Fin 8 → Fin 8 → Prop
  | 0, 1 | 1, 0 => True
  | 0, 2 | 2, 0 => True
  | 0, 4 | 4, 0 => True
  | 1, 3 | 3, 1 => True
  | 1, 5 | 5, 1 => True
  | 2, 3 | 3, 2 => True
  | 2, 6 | 6, 2 => True
  | 3, 7 | 7, 3 => True
  | 4, 5 | 5, 4 => True
  | 4, 6 | 6, 4 => True
  | 5, 7 | 7, 5 => True
  | 6, 7 | 7, 6 => True
  | _, _ => False

instance : DecidableEq (Fin 8) := inferInstance

def cubeGraph : SimpleGraph (Fin 8) where
  Adj := cubeAdj
  symm := by intro a b h; simp [cubeAdj] at *; exact h
  loopless := by intro a; simp [cubeAdj]; fin_cases a <;> decide

-- Verify vertex count, edge count via #eval
#eval cubeGraph.edgeFinset.card   -- should output 12
-- V=8, E=12, F=6 => chi = 8 - 12 + 6 = 2 ✓
```

Build and type-check the project with:

```text
lake build
lean --run GraphProofs/Handshaking.lean
```

### 3.3 Algebraic Graph Theory via SageMath: Characteristic Polynomials and Automorphism Groups

The characteristic polynomial of a graph $G$ is $\chi_G(\lambda) = \det(\lambda I - A)$ where $A$ is the adjacency matrix. It encodes the spectrum and is a weaker invariant than the chromatic polynomial: two non-isomorphic graphs can share the same spectrum (they are called cospectral or isospectral). The automorphism group $\text{Aut}(G)$ is the group of all vertex permutations preserving adjacency; it is a subgroup of the symmetric group $S_{|V|}$ and directly measures the symmetry of $G$. For the Petersen graph, $|\text{Aut}(G)| = 120 = |S_5|$, reflecting its exceptional symmetry as the Kneser graph $K(5,2)$.

The following SageMath session computes these invariants exactly, using Sage's built-in graph automorphism computation (via the Traces algorithm) and symbolic polynomial arithmetic.

```python
# sage_graph_invariants.sage
# Run with: sage sage_graph_invariants.sage

from sage.all import (
    graphs, matrix, ZZ, QQ, PolynomialRing, var,
    factor, Graph, SymmetricGroup, Set
)

def characteristic_polynomial_adjacency(G_sage):
    """
    Compute the characteristic polynomial det(lambda*I - A)
    of the adjacency matrix of a Sage graph, over QQ[lambda].
    """
    A = G_sage.adjacency_matrix(sparse=False).change_ring(QQ)
    n = A.nrows()
    R = PolynomialRing(QQ, 'lam')
    lam = R.gen()
    I_n = matrix.identity(QQ, n)
    M = lam * I_n - A
    return M.det()

def analyze_graph(G_sage, name):
    print(f"\n{'='*60}")
    print(f"Graph: {name}")
    print(f"  Vertices: {G_sage.order()}, Edges: {G_sage.size()}")

    # Characteristic polynomial
    chi = characteristic_polynomial_adjacency(G_sage)
    chi_factored = factor(chi)
    print(f"  Characteristic polynomial: {chi}")
    print(f"  Factored: {chi_factored}")

    # Spectrum (eigenvalues with multiplicities)
    spectrum = G_sage.spectrum()
    print(f"  Spectrum: {spectrum}")

    # Automorphism group order
    aut_group = G_sage.automorphism_group()
    print(f"  |Aut(G)|: {aut_group.order()}")

    # Chromatic polynomial
    chrom_poly = G_sage.chromatic_polynomial()
    print(f"  Chromatic polynomial: {chrom_poly}")

    # Number of spanning trees (Kirchhoff)
    # Sage's spanning_trees_count uses the Matrix-Tree theorem internally
    tau = G_sage.spanning_trees_count()
    print(f"  Spanning tree count tau: {tau}")

    return chi

# Petersen graph
P = graphs.PetersenGraph()
chi_petersen = analyze_graph(P, "Petersen Graph")

# Complete graph K5
K5 = graphs.CompleteGraph(5)
chi_K5 = analyze_graph(K5, "K5")

# Cycle C6
C6 = graphs.CycleGraph(6)
chi_C6 = analyze_graph(C6, "C6")

# Cubical graph
Cube = graphs.CubeGraph(3)  # 3-cube = Q3
analyze_graph(Cube, "3-Cube Q3")

# Demonstrate cospectral graphs: two non-isomorphic graphs with same spectrum
# The Saltire graph and another 5-vertex graph are cospectral
# Classic example: K_{1,4} and C4 + K1 (disjoint union)
K14 = graphs.StarGraph(4)   # K_{1,4}: star with 4 leaves
# C4 disjoint union isolated vertex
C4_plus_K1 = graphs.CycleGraph(4).disjoint_union(graphs.CompleteGraph(1))

chi_K14 = characteristic_polynomial_adjacency(K14)
chi_C4K1 = characteristic_polynomial_adjacency(C4_plus_K1)

print(f"\n{'='*60}")
print("Cospectral pair demonstration:")
print(f"  K_{{1,4}} char poly: {chi_K14}")
print(f"  C4+K1 char poly:   {chi_C4K1}")
print(f"  Polynomials equal: {chi_K14 == chi_C4K1}")
print(f"  Graphs isomorphic: {K14.is_isomorphic(C4_plus_K1)}")

# Verify the cospectrality formally: same spectrum, different structure
spectrum_K14 = K14.spectrum()
spectrum_C4K1 = C4_plus_K1.spectrum()
print(f"  K_{{1,4}} spectrum: {sorted(spectrum_K14)}")
print(f"  C4+K1 spectrum:   {sorted(spectrum_C4K1)}")
```

---

## Formal Axioms Cheat Sheet & Verification Reference

This reference consolidates the core definitions, theorems, and their computational verification signatures into a single practitioner lookup table. Each entry states the theorem in full mathematical precision, identifies the degenerate boundary cases the theorem must survive, and specifies the exact function call or proof strategy used in the exercises above.

**Handshaking Lemma.** For any graph $G = (V, E)$, $\sum_{v \in V} \deg(v) = 2|E|$. The number of odd-degree vertices is always even. Degeneracy: holds trivially for the empty graph ($0 = 0$) and for edgeless graphs. Formally verified in Lean 4 via `SimpleGraph.sum_degrees_eq_twice_card_edges`. Computationally checked via `handshaking_monte_carlo(10000)`.

**Erdős–Gallai Theorem.** A non-increasing sequence $(d_1, \ldots, d_n)$ of non-negative integers is graphical if and only if $\sum_{i=1}^n d_i$ is even and for all $k \in \{1, \ldots, n\}$,

$$\sum_{i=1}^{k} d_i \leq k(k-1) + \sum_{i=k+1}^{n} \min(d_i, k)$$

Boundary: a sequence of all zeros is graphical (the empty graph). A sequence failing only parity is not graphical. Realization via the Hakimi greedy algorithm runs in $O(n \log n)$ per step. Verified by `verify_erdos_gallai()` with ten test cases including two failure modes.

**Euler's Formula.** For any connected planar graph embedded in $S^2$, $V - E + F = 2$. Equivalent formulation: Euler characteristic $\chi(S^2) = 2$. For $V \geq 3$: $E \leq 3V - 6$; for triangle-free graphs: $E \leq 2V - 4$. These inequalities certify the non-planarity of $K_5$ ($V=5$, $E=10 > 9 = 3 \cdot 5 - 6$) and $K_{3,3}$ ($V=6$, $E=9 > 8 = 2 \cdot 6 - 4$). Verified by `verify_euler_on_examples()` and `verify_nonplanarity_inequality()`.

**Chromatic Polynomial.** $P(G, k)$ counts proper $k$-colorings. It satisfies $P(G, k) = P(G-e, k) - P(G/e, k)$ (deletion-contraction). Boundary evaluations: $P(G, 0) = 0$ for all non-empty graphs; $P(G, 1) = 0$ if $G$ has any edge; $P(K_n, k) = k(k-1)\cdots(k-n+1)$; $P(\bar{K}_n, k) = k^n$; $P(T, k) = k(k-1)^{n-1}$ for any tree $T$ on $n$ vertices; $P(C_n, k) = (k-1)^n + (-1)^n(k-1)$. Stanley's acyclic orientation theorem: $(-1)^{|V|} P(G, -1) = $ number of acyclic orientations of $G$.

**Matrix-Tree Theorem (Kirchhoff).** The number of spanning trees of a connected graph $G$ on $n$ vertices is

$$\tau(G) = \frac{1}{n} \prod_{i=1}^{n-1} \mu_i = \det(L^*)$$

where $\mu_1 \leq \cdots \leq \mu_{n-1}$ are the nonzero eigenvalues of the combinatorial Laplacian $L = D - A$, and $L^*$ is any $(n-1) \times (n-1)$ cofactor of $L$. Cayley's formula: $\tau(K_n) = n^{n-2}$. Boundary: $\tau(G) = 0$ iff $G$ is disconnected; $\tau(T) = 1$ for any tree; $\tau(C_n) = n$.

**Menger's Theorem.** For any two non-adjacent vertices $s, t$ in graph $G$, the maximum number of internally vertex-disjoint $s$-$t$ paths equals the minimum size of a vertex cut separating $s$ from $t$. The edge version: maximum edge-disjoint paths equals minimum edge cut (bond). The global vertex connectivity $\kappa(G)$ is the minimum over all non-adjacent pairs; $\kappa(K_n) = n-1$; $\kappa(G) \leq \delta(G)$ where $\delta(G)$ is the minimum degree. The Petersen graph achieves $\kappa = 3 = \delta$.

**Weisfeiler–Leman Invariant.** The 1-WL color refinement algorithm produces a polynomial-time computable graph invariant. Two graphs with different WL histograms are non-isomorphic. The converse fails: there exist non-isomorphic graphs (e.g., the Shrikhande graph and $K_{4,4}$ minus a perfect matching) that WL cannot distinguish. For trees and planar graphs of bounded genus, 2-WL and 3-WL respectively provide complete isomorphism invariants.

**Automorphism Group.** $\text{Aut}(G) \leq S_{|V|}$ is the group of adjacency-preserving permutations. $|\text{Aut}(K_n)| = n!$; $|\text{Aut}(C_n)| = 2n$; $|\text{Aut}(\text{Petersen})| = 120$. Computing $\text{Aut}(G)$ is equivalent to solving graph isomorphism; both are in the complexity class GI. In SageMath: `G.automorphism_group().order()`.

The following table consolidates the key verification function signatures from across all three exercises for rapid reference.

| Theorem | Python Entry Point | Expected Output | Failure Mode |
|---|---|---|---|
| Handshaking Lemma | `handshaking_symbolic()` | `difference = 0` | Sum parity mismatch |
| Handshaking Monte Carlo | `handshaking_monte_carlo(10000)` | `0 failures` | Random edge construction error |
| Erdős–Gallai | `verify_erdos_gallai()` | All `[PASS]` | EG inequality violated at some $k$ |
| Euler's Formula | `verify_euler_on_examples()` | `chi=2` for all graphs | Incorrect face count |
| Non-planarity filter | `verify_nonplanarity_inequality()` | `E > 3V-6` for $K_5$ | Inequality direction reversed |
| Chromatic polynomial | `stress_test_chromatic_polynomial()` | All assertions pass | Base case error in recursion |
| Matrix-Tree Theorem | `stress_test_matrix_tree()` | Exact integer counts | Singular Laplacian handling |
| Menger's Theorem | `verify_menger_theorem()` | All assertions pass | Cut vertex miscounted |
| WL Isomorphism | `verify_graph_isomorphism()` | Correct iso/non-iso | Collision in hash function |
| Sage Invariants | `sage sage_graph_invariants.sage` | Spectrum + poly output | Ring arithmetic error |
| Lean Handshaking | `lake build` | No type errors | Missing Mathlib import |
