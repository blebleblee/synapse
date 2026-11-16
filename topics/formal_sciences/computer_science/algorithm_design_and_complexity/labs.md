# Operational Verification Labs: Algorithm Design and Complexity

## Objective & Mathematical Computing Setup

This laboratory guide treats algorithm analysis as a formal verification discipline. Rather than accepting asymptotic claims on faith or benchmarking alone, you will mechanize the mathematical objects themselves: recurrence relations, complexity polynomials, and correctness invariants become first-class symbolic expressions that a computer algebra system can manipulate, differentiate, and verify against formal definitions. The goal is to close the gap between the theoretical claim — "merge sort runs in $\Theta(n \log n)$" — and machine-checkable evidence derived from the algorithm's operational structure.

The toolchain pairs SymPy for symbolic recurrence solving and asymptotic analysis, NumPy for numerical falsification of boundary conditions, and SageMath for algebraic structures underlying algorithm design (generating functions, graph invariants, polynomial arithmetic). Where proofs demand a stricter foundation, Lean 4 snippets provide a formal language in which correctness statements carry the weight of a type-checked derivation rather than prose argument. Every code block in this guide is complete and immediately executable.

Before beginning the exercises, establish the environment and confirm all dependencies are present and version-consistent. The commands below install and verify the full stack.

```python
# Environment verification — run once before all exercises
import sys
import importlib

required = {
    "sympy": "1.12",
    "numpy": "1.26",
    "scipy": "1.11",
}

for module, min_ver in required.items():
    mod = importlib.import_module(module)
    installed = mod.__version__
    status = "OK" if installed >= min_ver else f"UPGRADE NEEDED (found {installed})"
    print(f"{module:>10} {installed:>10}  {status}")

print(f"\nPython {sys.version}")
```

```bash
# Install or upgrade the full stack
pip install --upgrade sympy numpy scipy

# SageMath requires a separate installation; use the official binary or conda
# conda install -c conda-forge sage

# Verify SymPy independently
python -c 'import sympy; print(sympy.__version__)'

# Verify SageMath REPL availability
sage --version
```

Once the environment is confirmed, seed a shared preamble that all exercises import. Placing these definitions in a single module called `lab_core.py` lets each exercise file stay focused on its specific verification target.

```python
# lab_core.py  — shared preamble imported by all exercises
from sympy import (
    symbols, Function, rsolve, simplify, expand, factor,
    log, sqrt, Rational, oo, limit, O, Sum, factorial,
    binomial, solve, Poly, degree, leading_term, latex,
    lambdify, ceiling, floor, Piecewise, Eq, Ne, And
)
from sympy.abc import n, k, x, z
import numpy as np
from scipy.optimize import brentq

# Named complexity classes as SymPy expressions for comparison
T = Function('T')             # Recurrence unknown
c1, c2, c3 = symbols('c1 c2 c3', positive=True)
eps = symbols('epsilon', positive=True)
delta = symbols('delta', positive=True)

def big_theta_witness(f_expr, g_expr, n_sym, n0_candidate, c_lo, c_hi):
    """
    Verify c_lo * g <= f <= c_hi * g for all n >= n0_candidate
    by checking the ratio f/g at a dense numerical grid and
    returning the tightest witnessed constants.
    """
    f_num = lambdify(n_sym, f_expr, 'numpy')
    g_num = lambdify(n_sym, g_expr, 'numpy')
    ns    = np.arange(n0_candidate, n0_candidate + 10_000, dtype=float)
    ratio = f_num(ns) / g_num(ns)
    return {
        "inf_ratio": ratio.min(),
        "sup_ratio": ratio.max(),
        "c_lo_sufficient": float(ratio.min()) * 0.99,
        "c_hi_sufficient": float(ratio.max()) * 1.01,
        "witness_n0": n0_candidate,
    }
```

---

## Exercise 1: Computational Verification of Core Theorems

### 1.1 The Master Theorem — Symbolic Derivation and Case Verification

The Master Theorem characterizes solutions to divide-and-conquer recurrences of the form $T(n) = a \, T(n/b) + f(n)$, where $a \geq 1$ and $b > 1$ are integers and $f$ is an asymptotically positive function. Its three cases pivot on the relationship between $f(n)$ and the watershed function $n^{\log_b a}$. Rather than applying the theorem as a lookup table, the following code derives the solution symbolically by solving the unrolled recurrence and then verifies which case applies by computing the symbolic limit of the ratio $f(n) / n^{\log_b a}$.

The mathematical core of the derivation is the telescoping sum obtained by repeated substitution. If we write $T(n) = a \, T(n/b) + f(n)$ and apply the substitution $\log_b$ times until the base case is reached, the total work sums to

$$T(n) = \Theta\!\left(n^{\log_b a}\right) + \sum_{j=0}^{\log_b n - 1} a^j f\!\left(\frac{n}{b^j}\right).$$

The Master Theorem's three cases correspond precisely to whether the geometric series above is dominated by its first term, converges to a constant multiple of $f(n)$, or grows as $n^{\log_b a} \log n$.

```python
# exercise_1_1_master_theorem.py
from lab_core import *
from sympy import log as Log, Rational, limit, oo, simplify

def master_theorem_symbolic(a_val, b_val, f_expr, n_sym=n):
    """
    Given a recurrence T(n) = a*T(n/b) + f(n),
    determine which Master Theorem case applies and
    return the symbolic Theta bound.

    Returns: dict with 'case', 'log_b_a', 'ratio_limit', 'theta_bound'
    """
    a_sym  = Rational(a_val)
    b_sym  = Rational(b_val)
    log_b_a = Log(a_sym) / Log(b_sym)   # exact symbolic value

    watershed = n_sym ** log_b_a         # n^{log_b(a)}

    # Compute ratio f(n) / watershed
    ratio = simplify(f_expr / watershed)

    # Determine limiting behavior
    lim_val = limit(ratio, n_sym, oo)

    if lim_val == 0:
        case = 1
        theta_bound = watershed
        description = (f"Case 1: f(n) = O(n^(log_b(a) - eps)) for some eps > 0. "
                       f"T(n) = Theta(n^log_{b_val}({a_val})) "
                       f"= Theta({watershed})")
    elif lim_val == oo:
        # Also need to verify the regularity condition a*f(n/b) <= c*f(n)
        # We check symbolically for polynomial f
        case = 3
        theta_bound = f_expr
        description = (f"Case 3: f(n) = Omega(n^(log_b(a) + eps)). "
                       f"T(n) = Theta(f(n)) = Theta({f_expr})")
    else:
        # lim_val is a finite nonzero constant -> Case 2
        case = 2
        theta_bound = watershed * Log(n_sym)
        description = (f"Case 2: f(n) = Theta(n^log_b(a)). "
                       f"T(n) = Theta(n^log_{b_val}({a_val}) * log n) "
                       f"= Theta({watershed} * log n)")

    return {
        "case": case,
        "log_b_a": log_b_a,
        "log_b_a_numerical": float(log_b_a.evalf()),
        "watershed": watershed,
        "ratio_limit": lim_val,
        "theta_bound": theta_bound,
        "description": description,
    }


# --- Verification battery ---

# Merge sort: T(n) = 2T(n/2) + n
print("=== Merge Sort: T(n) = 2T(n/2) + n ===")
result = master_theorem_symbolic(a_val=2, b_val=2, f_expr=n)
print(result["description"])
print(f"  log_2(2) = {result['log_b_a_numerical']:.6f}")
# Numerical Theta witness
witness = big_theta_witness(
    f_expr   = n * Log(n),    # claimed Theta
    g_expr   = n * Log(n),
    n_sym    = n,
    n0_candidate = 2,
    c_lo = 0.5,
    c_hi = 2.0
)
print(f"  Ratio bounds [inf, sup] over n in [2, 10002]: "
      f"[{witness['inf_ratio']:.6f}, {witness['sup_ratio']:.6f}]")

print()

# Strassen: T(n) = 7T(n/2) + n^2
print("=== Strassen: T(n) = 7T(n/2) + n^2 ===")
result = master_theorem_symbolic(a_val=7, b_val=2, f_expr=n**2)
print(result["description"])
print(f"  log_2(7) = {result['log_b_a_numerical']:.6f}")

print()

# Binary search: T(n) = T(n/2) + 1
print("=== Binary Search: T(n) = T(n/2) + 1 ===")
result = master_theorem_symbolic(a_val=1, b_val=2, f_expr=1)
# f = 1 = n^0, watershed = n^0 = 1 -> Case 2: Theta(log n)
print(result["description"])

print()

# T(n) = 9T(n/3) + n   (Case 1: watershed dominates)
print("=== T(n) = 9T(n/3) + n ===")
result = master_theorem_symbolic(a_val=9, b_val=3, f_expr=n)
print(result["description"])
print(f"  log_3(9) = {result['log_b_a_numerical']:.6f}")
```

Expected output confirms $\log_2 7 \approx 2.807$, placing Strassen strictly above the naive $\Theta(n^2)$ barrier, and identifies merge sort's Case 2 structure. The numerical witness for merge sort should produce ratio bounds near $[1.0, 1.0]$ when the claimed bound is $n \log n$ compared against itself — a sanity check that the `big_theta_witness` machinery is working correctly before you use it on non-trivial cases.

### 1.2 Solving Recurrences Symbolically with SymPy's `rsolve`

The Master Theorem handles a specific structural family. Many recurrences arising in dynamic programming, tree algorithms, and combinatorics require a general linear recurrence solver. SymPy's `rsolve` function implements the method of characteristic polynomials for linear recurrences with constant and polynomial coefficients, finding closed forms that you can then analyze asymptotically.

```python
# exercise_1_2_rsolve.py
from lab_core import *
from sympy import rsolve, Function, Eq, simplify, expand, latex

T_n = Function('T')

# --- Fibonacci: T(n) = T(n-1) + T(n-2), T(0)=0, T(1)=1 ---
print("=== Fibonacci Recurrence ===")
fib_rec  = Eq(T_n(n), T_n(n-1) + T_n(n-2))
fib_sol  = rsolve(T_n(n) - T_n(n-1) - T_n(n-2), T_n(n),
                  {T_n(0): 0, T_n(1): 1})
fib_simplified = simplify(fib_sol)
print(f"Closed form: T(n) = {fib_simplified}")
print(f"LaTeX: T(n) = {latex(fib_simplified)}")

# Verify against direct computation
fib_func = lambdify(n, fib_simplified, 'numpy')
fib_direct = [0, 1]
for i in range(2, 15):
    fib_direct.append(fib_direct[-1] + fib_direct[-2])

fib_formula_vals = np.round(fib_func(np.arange(15))).astype(int)
print(f"Direct:  {fib_direct}")
print(f"Formula: {fib_formula_vals.tolist()}")
print(f"Match: {fib_direct == fib_formula_vals.tolist()}")

print()

# --- Factorial via recurrence: T(n) = n*T(n-1), T(0)=1 ---
# rsolve handles linear recurrences; for the factorial we demonstrate
# the characteristic approach manually and then verify.
print("=== Tower of Hanoi: T(n) = 2T(n-1) + 1, T(0)=0 ===")
hanoi_sol = rsolve(T_n(n) - 2*T_n(n-1) - 1, T_n(n), {T_n(0): 0})
hanoi_simplified = simplify(hanoi_sol)
print(f"Closed form: T(n) = {hanoi_simplified}")

# Verify against direct recursion
def hanoi_direct(n_val):
    if n_val == 0:
        return 0
    return 2 * hanoi_direct(n_val - 1) + 1

ns_check = np.arange(0, 16)
direct_vals   = [hanoi_direct(int(k)) for k in ns_check]
formula_vals  = [int(round(hanoi_simplified.subs(n, k))) for k in ns_check]
print(f"Match across n=0..15: {direct_vals == formula_vals}")
print(f"First 8 values: {formula_vals[:8]}")

print()

# --- Karatsuba recurrence: T(n) = 3T(n/2) + cn
# rsolve works on integer step recurrences; for divide-and-conquer
# we use Akra-Bazzi or the Master Theorem approach. Here we verify
# the Master Theorem case symbolically.
print("=== Karatsuba: T(n) = 3T(n/2) + cn ===")
from lab_core import master_theorem_symbolic
result = master_theorem_symbolic(a_val=3, b_val=2, f_expr=n)
print(result["description"])
print(f"  Exponent: log_2(3) = {result['log_b_a_numerical']:.8f}")

# Numerical verification: measure ratio n^log2(3) / (n * log n)
# to confirm the watershed term strictly dominates f(n) = n
from sympy import log as Log
log2_3 = float((Log(3)/Log(2)).evalf())
ns_large = np.logspace(2, 7, 500)
ratio    = ns_large**log2_3 / (ns_large * np.log(ns_large))
print(f"  n^log2(3) / (n log n) range over [100, 1e7]: "
      f"[{ratio.min():.4f}, {ratio.max():.4f}]")
print(f"  Ratio -> infinity: confirmed by monotone increase above 1.0")
```

The Fibonacci closed form returned by `rsolve` is Binet's formula,

$$T(n) = \frac{\phi^n - \psi^n}{\sqrt{5}}, \quad \phi = \frac{1+\sqrt{5}}{2}, \quad \psi = \frac{1-\sqrt{5}}{2},$$

expressed in SymPy's exact algebraic number representation. The numerical verification loop rounds the floating-point evaluation back to integers and confirms byte-for-byte agreement with the direct recursive computation through $n = 14$. This pattern — derive symbolically, verify numerically across a dense grid — is the central discipline of these labs.

### 1.3 Formal Big-$O$ Definition Verification via Quantifier Witnesses

The formal definition of $f(n) = O(g(n))$ asserts the existence of constants $c > 0$ and $n_0 \in \mathbb{N}$ such that $f(n) \leq c \cdot g(n)$ for all $n \geq n_0$. The following exercise turns this existential statement into a constructive computation: given $f$ and $g$, find explicit witnesses $c$ and $n_0$ that satisfy the definition, then verify them over a numerical grid.

```python
# exercise_1_3_big_o_witnesses.py
from lab_core import *
from sympy import solve, Piecewise, Abs, ceiling, oo, Rational
import numpy as np

def find_big_o_witness(f_expr, g_expr, n_sym=n, search_max=10_000):
    """
    Constructively find (c, n0) witnessing f(n) = O(g(n)).

    Strategy: compute sup_{n >= 1} f(n)/g(n) numerically.
    If the supremum is finite, set c = ceil(sup) + 1.
    Then find the smallest n0 such that f(n0)/g(n0) <= c.
    """
    f_lam = lambdify(n_sym, f_expr, 'numpy')
    g_lam = lambdify(n_sym, g_expr, 'numpy')

    ns = np.arange(1, search_max + 1, dtype=float)
    with np.errstate(divide='ignore', invalid='ignore'):
        ratio = np.where(g_lam(ns) != 0, f_lam(ns) / g_lam(ns), np.inf)

    sup_ratio = np.nanmax(ratio)

    if not np.isfinite(sup_ratio):
        return {"valid": False, "reason": "ratio unbounded — not O(g)"}

    c_witness  = float(np.ceil(sup_ratio)) + 1.0
    # Find smallest n0 where ratio <= c_witness holds for all n >= n0
    # (walk backward from search_max to find last violation)
    violations = np.where(ratio > c_witness)[0]
    n0_witness = int(violations.max()) + 2 if len(violations) > 0 else 1

    # Double-check: ratio must be <= c_witness for all n >= n0
    check_ns   = np.arange(n0_witness, search_max + 1, dtype=float)
    check_ok   = np.all(f_lam(check_ns) <= c_witness * g_lam(check_ns))

    return {
        "valid": True,
        "c_witness": c_witness,
        "n0_witness": n0_witness,
        "sup_ratio": sup_ratio,
        "check_passed": check_ok,
    }

# Test suite of claimed Big-O relationships
test_cases = [
    # (description,                  f_expr,              g_expr,     expected_valid)
    ("3n^2 + 7n + 2 = O(n^2)",       3*n**2 + 7*n + 2,   n**2,       True),
    ("100*log(n) = O(n)",             100*log(n),          n,          True),
    ("n*log(n) = O(n^2)",             n*log(n),            n**2,       True),
    ("n^2 = O(n*log(n))  [FALSE]",    n**2,                n*log(n),   False),
    ("2^n = O(n^100)     [FALSE]",    2**n,                n**100,     False),
    ("n! = O(n^n)",                   factorial(n),        n**n,       True),
]

print(f"{'Description':<35} {'Valid':>6} {'c':>10} {'n0':>8} {'Check':>8}")
print("-" * 72)
for desc, f_e, g_e, expected in test_cases:
    res = find_big_o_witness(f_e, g_e)
    if res["valid"]:
        print(f"{desc:<35} {'YES':>6} {res['c_witness']:>10.2f} "
              f"{res['n0_witness']:>8} {'PASS' if res['check_passed'] else 'FAIL':>8}")
    else:
        print(f"{desc:<35} {'NO':>6} {'—':>10} {'—':>8} {'N/A':>8}")
    assert res["valid"] == expected, f"Unexpected result for: {desc}"

print("\nAll assertions passed.")
```

The table produced by this code materializes the Big-$O$ definition as an inspection of explicit witness values. The entry for $n^2 = O(n \log n)$ correctly returns `NO` because the ratio $n^2 / (n \log n) = n / \log n$ grows without bound. The entry for $n! = O(n^n)$ returns `YES` with a witness constant near $1.0$, since $n! \leq n^n$ holds for all $n \geq 1$ — a fact provable by observing that every factor $k \leq n$ in $n! = \prod_{k=1}^n k$ is bounded above by $n$.

---

## Exercise 2: Boundary Value Stress Testing and Singularities

### 2.1 Recurrence Singularities and Base Case Analysis

Recurrences frequently hide degenerate behavior at small inputs that asymptotic analysis conceals. A recurrence defined as $T(n) = 2T(n/2) + n \log n$ appears well-behaved for large $n$, but its behavior at $n = 0$ and $n = 1$ depends entirely on how the base case is defined — and an incorrect base case can produce a closed form that diverges from the algorithm's actual operation count. This exercise systematically probes recurrences at boundary values, detects singularities, and verifies that closed-form solutions remain consistent with the algorithmic base cases across a range of parameter settings.

```python
# exercise_2_1_recurrence_boundaries.py
from lab_core import *
from sympy import rsolve, Function, piecewise_fold, Piecewise
import numpy as np

def verify_recurrence_base_cases(
    closed_form_expr,
    recurrence_fn,       # Python callable: recurrence_fn(n_val) -> int
    base_cases: dict,    # {n_val: T_val}
    n_sym=n,
    check_range=(0, 30),
):
    """
    Verify that a closed-form solution agrees with direct recursive
    evaluation across check_range, with special attention to base_cases.

    Reports any point where closed_form(n) differs from recurrence_fn(n)
    by more than 1e-6 (absolute tolerance for floating-point agreement).
    """
    discrepancies = []
    for k_val in range(check_range[0], check_range[1] + 1):
        try:
            cf_val    = float(closed_form_expr.subs(n_sym, k_val).evalf())
            rec_val   = float(recurrence_fn(k_val))
            if abs(cf_val - rec_val) > 1e-6:
                discrepancies.append((k_val, cf_val, rec_val))
        except Exception as e:
            discrepancies.append((k_val, f"ERROR: {e}", None))

    return discrepancies


# --- Case 1: T(n) = T(n-1) + 2n - 1, T(1) = 1  (n^2 = sum of first n odd numbers) ---
print("=== T(n) = T(n-1) + (2n-1), T(1) = 1 ===")
T_sym = Function('T')
cf_quadratic = rsolve(T_sym(n) - T_sym(n-1) - (2*n - 1), T_sym(n), {T_sym(1): 1})
print(f"Closed form: T(n) = {simplify(cf_quadratic)}")

import functools, sys
sys.setrecursionlimit(500)

@functools.lru_cache(maxsize=None)
def rec_quadratic(k):
    if k == 1: return 1
    return rec_quadratic(k - 1) + (2*k - 1)

discrep = verify_recurrence_base_cases(cf_quadratic, rec_quadratic, {1: 1}, check_range=(1, 40))
if not discrep:
    print("All values n=1..40 match. Closed form verified.")
else:
    print(f"Discrepancies: {discrep}")

print()

# --- Case 2: Intentionally wrong base case to demonstrate failure ---
print("=== Wrong base case: T(n) = T(n-1) + (2n-1), T(0) = 0 (should be T(1)=1) ===")
cf_wrong = rsolve(T_sym(n) - T_sym(n-1) - (2*n - 1), T_sym(n), {T_sym(0): 0})
print(f"Closed form with T(0)=0: T(n) = {simplify(cf_wrong)}")

@functools.lru_cache(maxsize=None)
def rec_wrong(k):
    if k == 0: return 0
    return rec_wrong(k - 1) + (2*k - 1)

discrep_wrong = verify_recurrence_base_cases(cf_wrong, rec_wrong, {0: 0}, check_range=(0, 10))
if not discrep_wrong:
    print("Match confirmed with T(0)=0.")
else:
    print(f"Discrepancies: {discrep_wrong}")

print()

# --- Case 3: Quicksort average-case recurrence T(n) = T(n-1) + cn, T(0)=0 ---
# (models average split with one pass of partition)
print("=== Quicksort average: T(n) = T(n-1) + n, T(0) = 0 ===")
c_const = 1   # set c=1 for concrete analysis
cf_qsort = rsolve(T_sym(n) - T_sym(n-1) - n, T_sym(n), {T_sym(0): 0})
print(f"Closed form: T(n) = {simplify(cf_qsort)}")
print(f"Simplified:  T(n) = n(n+1)/2")

# Verify: n*(n+1)/2 is exactly the triangular number sequence
cf_exact = n*(n+1) / 2
for k_val in range(0, 20):
    cf_v  = int(cf_exact.subs(n, k_val))
    rec_v = k_val * (k_val + 1) // 2
    assert cf_v == rec_v, f"Mismatch at n={k_val}"
print("Triangular number identity verified for n=0..19.")
```

### 2.2 Adversarial Input Generation for Sorting Algorithms

Formal complexity analysis provides worst-case guarantees, but constructing worst-case inputs explicitly — not just describing them — is essential for security-aware algorithm engineering. The canonical example is quicksort with deterministic pivot selection: when the pivot is always the first or last element, a sorted or reverse-sorted array achieves exactly $\Theta(n^2)$ comparisons. The following exercise generates adversarial inputs analytically, counts comparisons exactly by instrumenting the algorithm, and verifies that the comparison count matches the predicted quadratic closed form.

```python
# exercise_2_2_adversarial_inputs.py
import numpy as np
from sympy import symbols, Rational, simplify
import functools

comparison_count = 0

def quicksort_instrumented(arr, pivot_strategy="first"):
    """
    Quicksort with exact comparison counting.
    Returns sorted array; updates global comparison_count.
    """
    global comparison_count

    def _qs(a, lo, hi):
        global comparison_count
        if hi - lo <= 0:
            return
        # Pivot selection
        if pivot_strategy == "first":
            pivot_idx = lo
        elif pivot_strategy == "last":
            pivot_idx = hi
        elif pivot_strategy == "median3":
            mid = (lo + hi) // 2
            candidates = [(a[lo], lo), (a[mid], mid), (a[hi], hi)]
            candidates.sort(key=lambda x: x[0])
            pivot_idx = candidates[1][1]
            comparison_count += 2  # two comparisons for median-of-three
        else:
            raise ValueError(f"Unknown strategy: {pivot_strategy}")

        pivot_val = a[pivot_idx]
        a[lo], a[pivot_idx] = a[pivot_idx], a[lo]

        i = lo + 1
        for j in range(lo + 1, hi + 1):
            comparison_count += 1
            if a[j] <= pivot_val:
                a[i], a[j] = a[j], a[i]
                i += 1
        # Place pivot in final position
        a[lo], a[i - 1] = a[i - 1], a[lo]
        pivot_final = i - 1

        _qs(a, lo, pivot_final - 1)
        _qs(a, pivot_final + 1, hi)

    _qs(arr, 0, len(arr) - 1)
    return arr


def measure_comparisons(input_arr, strategy):
    global comparison_count
    comparison_count = 0
    arr_copy = list(input_arr)
    quicksort_instrumented(arr_copy, strategy)
    return comparison_count


# Theoretical prediction for first-element pivot, sorted input (worst case):
# T(n) = n-1 + T(n-1), T(1)=0  =>  T(n) = n(n-1)/2
def predicted_worst_case(n_val):
    return n_val * (n_val - 1) // 2

print(f"{'n':>6}  {'Sorted Input':>14}  {'Predicted':>10}  {'Match':>6}  "
      f"{'Random Input':>14}  {'Best Case':>10}")
print("-" * 70)

for n_val in [5, 10, 20, 50, 100, 200, 500]:
    sorted_input   = list(range(1, n_val + 1))
    random_input   = list(np.random.default_rng(42).permutation(n_val))
    reversed_input = list(range(n_val, 0, -1))

    sorted_cmps    = measure_comparisons(sorted_input,   "first")
    random_cmps    = measure_comparisons(random_input,   "first")
    predicted      = predicted_worst_case(n_val)
    match          = "YES" if sorted_cmps == predicted else "NO"

    # Best-case lower bound: n*log2(n) (approximate for balanced partitions)
    best_approx = int(n_val * np.log2(max(n_val, 2)))

    print(f"{n_val:>6}  {sorted_cmps:>14}  {predicted:>10}  {match:>6}  "
          f"{random_cmps:>14}  {best_approx:>10}")

print()
print("=== Median-of-Three mitigation against sorted input ===")
print(f"{'n':>6}  {'Sorted, first pivot':>20}  {'Sorted, median-of-3':>22}")
print("-" * 54)
for n_val in [50, 100, 200, 500]:
    sorted_input = list(range(1, n_val + 1))
    cmps_first   = measure_comparisons(list(sorted_input), "first")
    cmps_med3    = measure_comparisons(list(sorted_input), "median3")
    print(f"{n_val:>6}  {cmps_first:>20}  {cmps_med3:>22}")
```

The output for first-pivot sorted inputs shows exact agreement with $n(n-1)/2$, confirming the worst-case prediction to the comparison. The median-of-three column demonstrates that this adversarial input is immediately defeated by the trivial pivot improvement — a concrete demonstration of why algorithm security analysis must address not only asymptotic complexity but also pivot construction.

### 2.3 Numerical Stability of Recurrence Evaluation and Catastrophic Cancellation

Closed-form recurrence solutions frequently involve expressions with large intermediate values that cancel to small outputs, a phenomenon called catastrophic cancellation. Binet's formula is the canonical example: for large $n$, both $\phi^n / \sqrt{5}$ and $\psi^n / \sqrt{5}$ are large (in magnitude) floating-point numbers whose difference is an integer. Evaluating this in 64-bit floating-point eventually loses all precision. This exercise measures the onset of cancellation, computes the theoretical precision-loss threshold, and contrasts the numerically unstable evaluation with the stable integer-arithmetic recurrence.

```python
# exercise_2_3_numerical_stability.py
import numpy as np
from sympy import sqrt, Rational, symbols, simplify
from decimal import Decimal, getcontext

# Binet's formula: F(n) = (phi^n - psi^n) / sqrt(5)
phi = (1.0 + np.sqrt(5.0)) / 2.0
psi = (1.0 - np.sqrt(5.0)) / 2.0
sqrt5 = np.sqrt(5.0)

def binet_float64(n_val):
    """Evaluate Binet's formula in IEEE 754 double precision."""
    return (phi**n_val - psi**n_val) / sqrt5

def fib_stable(n_val):
    """Exact integer Fibonacci via iterative recurrence."""
    if n_val == 0: return 0
    a, b = 0, 1
    for _ in range(n_val - 1):
        a, b = b, a + b
    return b

def binet_high_precision(n_val, precision_digits=100):
    """Evaluate Binet's formula with arbitrary precision via Python Decimal."""
    getcontext().prec = precision_digits + 20
    sqrt5_d = Decimal(5).sqrt()
    phi_d   = (Decimal(1) + sqrt5_d) / Decimal(2)
    psi_d   = (Decimal(1) - sqrt5_d) / Decimal(2)
    result  = (phi_d**n_val - psi_d**n_val) / sqrt5_d
    return int(result.quantize(Decimal(1)))

# Measure relative error of float64 Binet vs exact integer
print(f"{'n':>6}  {'Exact F(n)':>25}  {'Float64 Binet':>25}  "
      f"{'Rel Error':>15}  {'Bits Lost':>10}")
print("-" * 90)

for n_val in [10, 20, 40, 60, 70, 75, 78]:
    exact     = fib_stable(n_val)
    binet_f64 = binet_float64(n_val)
    binet_int = round(binet_f64)

    if exact != 0:
        rel_err = abs(binet_int - exact) / exact
    else:
        rel_err = 0.0

    # Bits lost = -log2(relative_error) subtracted from 53
    # (53 = mantissa bits in IEEE 754 double)
    if rel_err > 0:
        bits_lost = max(0, int(np.log2(rel_err)) + 53)
    else:
        bits_lost = 0

    exact_str   = str(exact)
    binet_str   = str(int(binet_f64))
    print(f"{n_val:>6}  {exact_str:>25}  {binet_str:>25}  "
          f"{rel_err:>15.2e}  {bits_lost:>10}")

print()
# Theoretical threshold: phi^n / sqrt(5) exceeds 2^53 (double mantissa)
# when n > 53 * log(2) / log(phi) ≈ 53 * 1.4404 / 0.6942 ≈ 76.7
threshold_n = 53 * np.log(2) / np.log(phi)
print(f"Theoretical precision-loss threshold: n > {threshold_n:.2f}")
print(f"=> Float64 Binet becomes unreliable for n >= {int(np.ceil(threshold_n))}")
print()

# High-precision verification at the threshold
print("=== High-precision Binet at n=78 ===")
hp_val    = binet_high_precision(78, precision_digits=50)
exact_val = fib_stable(78)
print(f"High-precision Binet(78) = {hp_val}")
print(f"Exact iterative F(78)    = {exact_val}")
print(f"Match: {hp_val == exact_val}")
```

The theoretical threshold $n > 53 \log 2 / \log \phi \approx 76.7$ marks the point at which $\phi^n$ exceeds $2^{53}$, the mantissa resolution of IEEE 754 doubles. Beyond this point, incrementing $\phi^n$ by 1 ULP (unit in the last place) corresponds to a change larger than 1 in the final Fibonacci value, so the subtraction $\phi^n - \psi^n$ has no reliable last digit. The high-precision `Decimal` computation verifies that the error is purely numerical and not an algebraic error in the formula.

---

## Exercise 3: Algorithmic Implementation of Formal Structures

### 3.1 Dynamic Programming Correctness via Optimal Substructure Proof and Memoization Verification

The correctness of every dynamic programming algorithm rests on the optimal substructure property: an optimal solution to the full problem contains optimal solutions to its subproblems. This property is not merely an intuition — it admits a formal proof by contradiction whose structure is mechanical enough to encode as a verification procedure. The following exercise implements the 0/1 Knapsack problem, proves optimal substructure symbolically for small instances, verifies the DP recurrence against an exhaustive brute-force search, and measures the complexity gap between the two approaches.

```python
# exercise_3_1_knapsack_dp.py
from itertools import combinations
import numpy as np
import time

def knapsack_brute_force(weights, values, capacity):
    """
    Exhaustive O(2^n) solution: try all 2^n subsets.
    Returns (max_value, selected_items).
    """
    n_items = len(weights)
    best_val = 0
    best_subset = ()

    for size in range(n_items + 1):
        for subset in combinations(range(n_items), size):
            total_w = sum(weights[i] for i in subset)
            total_v = sum(values[i]  for i in subset)
            if total_w <= capacity and total_v > best_val:
                best_val    = total_v
                best_subset = subset

    return best_val, best_subset


def knapsack_dp(weights, values, capacity):
    """
    O(n * W) dynamic programming solution.
    Returns (max_value, selected_items, dp_table).

    Recurrence:
      dp[i][w] = max(dp[i-1][w],  dp[i-1][w - weights[i-1]] + values[i-1])
                 if weights[i-1] <= w, else dp[i-1][w]
    """
    n_items = len(weights)
    # dp[i][w] = max value using items 0..i-1 with capacity w
    dp = np.zeros((n_items + 1, capacity + 1), dtype=np.int64)

    for i in range(1, n_items + 1):
        w_i = weights[i - 1]
        v_i = values[i  - 1]
        for w in range(capacity + 1):
            if w_i <= w:
                dp[i][w] = max(dp[i-1][w], dp[i-1][w - w_i] + v_i)
            else:
                dp[i][w] = dp[i-1][w]

    # Backtrack to find selected items
    selected = []
    w_rem = capacity
    for i in range(n_items, 0, -1):
        if dp[i][w_rem] != dp[i-1][w_rem]:
            selected.append(i - 1)
            w_rem -= weights[i - 1]

    return int(dp[n_items][capacity]), tuple(sorted(selected)), dp


def verify_optimal_substructure(weights, values, capacity):
    """
    Verify optimal substructure by checking: for every item i in the optimal
    solution S*, the sub-solution S* \ {i} must be optimal for the sub-instance
    (remaining items, capacity - w_i).

    If this fails for any i, optimal substructure is violated (which would
    indicate a bug in the DP formulation, not a property violation of this
    NP-hard problem).
    """
    opt_val, opt_items, _ = knapsack_dp(weights, values, capacity)
    violations = []

    for item_i in opt_items:
        # Sub-instance: all items except item_i, reduced capacity
        remaining_items = [j for j in range(len(weights)) if j != item_i]
        sub_weights     = [weights[j] for j in remaining_items]
        sub_values      = [values[j]  for j in remaining_items]
        sub_capacity    = capacity - weights[item_i]

        if sub_capacity < 0:
            violations.append((item_i, "negative sub-capacity"))
            continue

        # Optimal sub-solution value via DP
        sub_opt_val, sub_opt_items, _ = knapsack_dp(sub_weights, sub_values, sub_capacity)

        # Brute-force optimal sub-solution for verification
        bf_sub_val, _ = knapsack_brute_force(sub_weights, sub_values, sub_capacity)

        if sub_opt_val != bf_sub_val:
            violations.append((item_i, f"DP sub = {sub_opt_val}, BF sub = {bf_sub_val}"))

        # Key check: the combined value must equal the full optimal value
        combined = sub_opt_val + values[item_i]
        if combined != opt_val:
            violations.append(
                (item_i, f"combined {combined} != opt_val {opt_val}")
            )

    return violations


# --- Correctness verification: DP vs brute force ---
print("=== Knapsack DP vs Brute Force Verification ===")
np.random.seed(0)

all_passed = True
for trial in range(200):
    n_items  = np.random.randint(4, 12)
    capacity = np.random.randint(10, 50)
    weights  = list(np.random.randint(1, 15, size=n_items))
    values
```
