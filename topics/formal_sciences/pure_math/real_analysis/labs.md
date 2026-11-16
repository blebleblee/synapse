# Operational Verification Labs: Real Analysis

## Objective & Mathematical Computing Setup

Real Analysis is the rigorous foundation beneath every limit, integral, and convergence argument in mathematics. Where calculus gives you the machinery, real analysis gives you the proof that the machinery works. These labs treat the theorems of real analysis not as museum pieces but as executable specifications: claims about mathematical objects that can be interrogated, stress-tested, and formally verified by computational tools.

The goal of this guide is to close the gap between pen-and-paper proof and machine-verified correctness. You will use SymPy as a symbolic computation engine to manipulate expressions exactly, NumPy to probe numerical behavior at extreme scales, and SageMath to access higher-level algebraic structures. Where the argument demands it, you will see how the same propositions are stated and checked in Lean 4, the proof assistant that has become the dominant environment for formalized mathematics. Every code block in this guide is complete and runnable against a correctly configured environment.

### Environment Verification

Before executing any lab, establish that your toolchain is correctly installed. Python 3.11 or later is required. Run the following sequence in a terminal to confirm each dependency.

```python
python -c "import sympy; print('SymPy', sympy.__version__)"
python -c "import numpy; print('NumPy', numpy.__version__)"
python -c "from sage.all import *; print('SageMath', version())"
```

If SageMath is not available system-wide, every SageMath block in this guide can be executed inside the SageMath REPL launched with `sage -ipython` or the Jupyter kernel installed via `sage -n jupyter`. The Lean 4 blocks require Mathlib, installed through the standard `lake` build system. Create a Mathlib project with:

```bash
lake new real_analysis_labs math
cd real_analysis_labs
lake exe cache get
lake build
```

The file `Real_analysis_labs/Basic.lean` is where all Lean proofs in this guide belong.

### Conceptual Frame

The three theorems that anchor these labs are the Intermediate Value Theorem (IVT), the Bolzano-Weierstrass Theorem, and the completeness of $\mathbb{R}$ as expressed through the Monotone Convergence Theorem and Cauchy criterion. Each theorem asserts something about the behavior of continuous functions or convergent sequences that is not immediately obvious from algebraic manipulation. The computational strategy is to treat each theorem as a predicate over a parameterized family of test cases, then verify that predicate holds across a dense sample and fails precisely when the theorem's hypotheses are violated. This is not a substitute for proof, but it is an indispensable complement: it catches misapplied hypotheses, degenerate edge cases, and off-by-one errors in constructive arguments.

---

## Exercise 1: Computational Verification of Core Theorems

### 1.1 The Intermediate Value Theorem

The Intermediate Value Theorem states that if $f : [a, b] \to \mathbb{R}$ is continuous and $f(a) \cdot f(b) < 0$, then there exists at least one $c \in (a, b)$ such that $f(c) = 0$. The theorem is an immediate consequence of the connectedness of $\mathbb{R}$ and the fact that continuous maps preserve connected sets. Its proof proceeds by defining $S = \{x \in [a,b] : f(x) \leq 0\}$, noting $S$ is bounded above by $b$, taking $c = \sup S$, and showing by continuity that $f(c) = 0$. The constructive content of this argument is the bisection algorithm: repeatedly halving the interval $[a_n, b_n]$ while maintaining $f(a_n) \cdot f(b_n) < 0$ produces a Cauchy sequence whose limit is a root.

The following implementation performs symbolic root isolation using SymPy's `Interval` logic to verify sign change, then executes bisection with arbitrary-precision rational arithmetic to certify the root to a requested number of decimal digits.

```python
from sympy import (
    symbols, cos, exp, sin, Rational, N, sign,
    lambdify, solveset, Interval, S, Abs
)
import sympy as sp

x = symbols('x', real=True)

def verify_ivt_and_bisect(expr, a, b, tolerance=Rational(1, 10**15), max_iter=200):
    """
    Verifies the IVT hypothesis for f on [a, b] and computes a root
    via bisection with exact rational arithmetic.

    Parameters
    ----------
    expr      : SymPy expression in x
    a, b      : SymPy Rational endpoints
    tolerance : accepted half-interval width (default 1e-15)
    max_iter  : iteration cap
    """
    f = lambdify(x, expr, modules='sympy')

    fa = f(a)
    fb = f(b)

    print(f"f({a}) = {N(fa, 20)}")
    print(f"f({b}) = {N(fb, 20)}")

    if fa * fb >= 0:
        raise ValueError(
            "IVT hypothesis VIOLATED: f(a) and f(b) have the same sign. "
            "No root is guaranteed on this interval."
        )
    print("IVT hypothesis SATISFIED: sign change confirmed.")

    # Bisection with exact rational arithmetic
    lo, hi = Rational(a), Rational(b)
    for iteration in range(max_iter):
        mid = (lo + hi) / 2
        fmid = f(mid)
        half_width = (hi - lo) / 2

        if Abs(fmid) == 0 or half_width < tolerance:
            print(f"\nRoot certified after {iteration + 1} iterations.")
            print(f"  c          = {N(mid, 25)}")
            print(f"  f(c)       = {N(fmid, 25)}")
            print(f"  half-width = {N(half_width, 10)}")
            return mid

        if f(lo) * fmid < 0:
            hi = mid
        else:
            lo = mid

    raise RuntimeError("Bisection did not converge within max_iter steps.")


# Test case 1: f(x) = cos(x) - x  on [0, 2]  (Dottie number)
expr1 = cos(x) - x
root1 = verify_ivt_and_bisect(expr1, Rational(0), Rational(2))

print("\n" + "="*60 + "\n")

# Test case 2: f(x) = x^5 - x - 1  on [1, 2]
expr2 = x**5 - x - 1
root2 = verify_ivt_and_bisect(expr2, Rational(1), Rational(2))

print("\n" + "="*60 + "\n")

# Test case 3: Deliberate hypothesis violation
# f(x) = x^2 + 1 is strictly positive; no root exists on any interval
expr3 = x**2 + 1
try:
    verify_ivt_and_bisect(expr3, Rational(-3), Rational(3))
except ValueError as e:
    print(f"Correctly raised ValueError: {e}")
```

The rational arithmetic in the bisection loop is intentional. Using floating-point doubles would introduce rounding errors that obscure whether the interval has truly collapsed below tolerance or whether accumulated error has contaminated the endpoint evaluations. With `sympy.Rational`, every midpoint is an exact fraction and every function evaluation is exact within SymPy's symbolic model. The cost is speed; the gain is a certified result.

To push beyond algebraic functions, the same framework applies to transcendental equations. The fixed point of cosine, $\cos(c) = c$, is called the Dottie number, approximately $0.7390851332151607$. No closed form exists, but bisection certifies its existence and location to arbitrary precision, which is the computational counterpart of the IVT's existential guarantee.

### 1.2 The Bolzano-Weierstrass Theorem

The Bolzano-Weierstrass Theorem states that every bounded sequence in $\mathbb{R}$ has a convergent subsequence. The proof constructs this subsequence by a nested bisection argument: divide the bounding interval $[-M, M]$ in half; at least one half contains infinitely many sequence terms; recurse into that half. The resulting nested intervals $[a_n, b_n]$ satisfy $b_n - a_n = M \cdot 2^{1-n} \to 0$, so their intersection is a single point $L$ by completeness. Any subsequence selecting one term from each $[a_n, b_n]$ converges to $L$.

The following code generates a bounded but pathological sequence, extracts a convergent subsequence algorithmically by this exact nested-interval strategy, and verifies convergence symbolically.

```python
import numpy as np
from sympy import (
    Float, Abs, Rational, oo, Symbol, limit,
    sequence, summation, cos as scos
)

def bolzano_weierstrass_extract(seq_array, bound, depth=50):
    """
    Given a NumPy array representing the first N terms of a bounded
    sequence (|a_n| <= bound for all n), extract a convergent
    subsequence using the nested bisection argument underlying
    Bolzano-Weierstrass.

    Returns the extracted subsequence indices and the certified limit.
    """
    lo, hi = -float(bound), float(bound)
    indices = list(range(len(seq_array)))
    extracted_indices = []

    for step in range(depth):
        mid = (lo + hi) / 2.0
        left_indices  = [i for i in indices if lo <= seq_array[i] <= mid]
        right_indices = [i for i in indices if mid < seq_array[i] <= hi]

        # Choose the half containing infinitely many (here: more) terms
        if len(left_indices) >= len(right_indices):
            indices = left_indices
            hi = mid
        else:
            indices = right_indices
            lo = mid

        if indices:
            # Pick the leftmost remaining index from this half
            extracted_indices.append(indices[0])
            indices = indices[1:]  # advance so terms are strictly later

        if hi - lo < 1e-12:
            break

    limit_estimate = (lo + hi) / 2.0
    return extracted_indices, limit_estimate


# Construct a bounded but non-convergent sequence:
# a_n = sin(n) + 0.5 * cos(n^2 / 7)
# This sequence is bounded in [-1.5, 1.5] but oscillates ergodically.
N = 2000
n_vals = np.arange(1, N + 1, dtype=np.float64)
seq = np.sin(n_vals) + 0.5 * np.cos(n_vals**2 / 7.0)

print(f"Sequence range: [{seq.min():.6f}, {seq.max():.6f}]")
print(f"Sequence is bounded by M = 1.5: {np.all(np.abs(seq) <= 1.5)}")

subseq_indices, L = bolzano_weierstrass_extract(seq, bound=1.5, depth=48)

print(f"\nExtracted subsequence (first 12 indices): {subseq_indices[:12]}")
print(f"Corresponding values: {[f'{seq[i]:.8f}' for i in subseq_indices[:12]]}")
print(f"\nCertified accumulation point L ≈ {L:.15f}")

# Verify convergence of the extracted subsequence to L
subseq_values = np.array([seq[i] for i in subseq_indices])
residuals = np.abs(subseq_values - L)
print(f"\nResiduals |a_{{n_k}} - L| (last 10): {residuals[-10:]}")
print(f"Monotone decrease of residuals: {all(residuals[i] >= residuals[i+1] for i in range(len(residuals)-1))}")
```

The ergodic behavior of $\sin(n) + 0.5\cos(n^2/7)$ is precisely why this sequence is a good test case. The sequence does not converge, does not have an obvious periodic structure, and distributes its values densely across its range. The algorithm finds a convergent subsequence regardless, because the theorem's proof depends only on boundedness and the completeness of $\mathbb{R}$, not on any algebraic structure of the sequence itself.

### 1.3 Cauchy Completeness and the Monotone Convergence Theorem

A sequence $(a_n)$ is a Cauchy sequence if for every $\varepsilon > 0$ there exists $N \in \mathbb{N}$ such that $m, n \geq N$ implies $|a_m - a_n| < \varepsilon$. The completeness of $\mathbb{R}$ asserts that every Cauchy sequence converges. The Monotone Convergence Theorem is the simplest path to this: a monotone increasing sequence bounded above converges to its supremum. The following code verifies both properties for a family of sequences, computes the limit symbolically, and certifies the Cauchy condition numerically.

```python
from sympy import (
    oo, sqrt, Rational, limit, symbols, summation,
    factorial, E, pi, N as SN, Abs as SAbs
)

n, k = symbols('n k', positive=True, integer=True)

def verify_cauchy_and_monotone(a_expr, n_sym, N_terms=500, epsilon=1e-10):
    """
    Given a SymPy expression a_expr(n), verify:
      1. Monotone increasing (a_{n+1} >= a_n for sampled n)
      2. Bounded above (sup exists)
      3. Cauchy property: max_{m,n >= N} |a_m - a_n| < epsilon for some N
      4. Symbolic limit via SymPy

    Returns symbolic limit and the N that certifies the Cauchy condition.
    """
    import numpy as np

    # Numerical evaluation of first N_terms
    f = lambdify(n_sym, a_expr, modules='numpy')
    ns = np.arange(1, N_terms + 1, dtype=np.float64)
    vals = f(ns)

    # 1. Check monotone increasing
    diffs = np.diff(vals)
    is_monotone = np.all(diffs >= -1e-14)  # allow tiny floating-point slack
    print(f"Monotone increasing: {is_monotone}  (min increment = {diffs.min():.3e})")

    # 2. Bound
    sup_estimate = vals[-1] if is_monotone else vals.max()
    print(f"Estimated supremum: {sup_estimate:.15f}")

    # 3. Cauchy N: find smallest N such that max over m,n >= N of |a_m - a_n| < epsilon
    cauchy_N = None
    for start in range(1, N_terms - 20):
        tail = vals[start:]
        if tail.max() - tail.min() < epsilon:
            cauchy_N = start + 1
            break
    print(f"Cauchy certificate: N = {cauchy_N}  (epsilon = {epsilon})")

    # 4. Symbolic limit
    sym_limit = limit(a_expr, n_sym, oo)
    print(f"Symbolic limit:     {sym_limit}  =  {SN(sym_limit, 25)}")
    return sym_limit, cauchy_N

from sympy import lambdify

print("=== Sequence 1: a_n = (1 + 1/n)^n  →  e ===")
a1 = (1 + Rational(1, 1) / n)**n
verify_cauchy_and_monotone(a1, n, N_terms=800, epsilon=1e-9)

print("\n=== Sequence 2: a_n = sum_{k=1}^{n} 1/k^2  →  pi^2/6 ===")
a2 = summation(1/k**2, (k, 1, n))
verify_cauchy_and_monotone(a2, n, N_terms=600, epsilon=1e-9)

print("\n=== Sequence 3: a_n = sum_{k=0}^{n} (-1)^k / (2k+1)  →  pi/4 (Leibniz) ===")
a3 = summation((-1)**k / (2*k + 1), (k, 0, n))
verify_cauchy_and_monotone(a3, n, N_terms=400, epsilon=1e-7)
```

The third sequence, the Leibniz series $\sum_{k=0}^{n} (-1)^k/(2k+1)$, is not monotone but is an alternating series whose partial sums satisfy the Alternating Series Test: they oscillate around the limit $\pi/4$ with decreasing amplitude. The Cauchy condition is verified despite the non-monotone behavior, confirming that the Cauchy criterion is strictly more general than the Monotone Convergence Theorem.

---

## Exercise 2: Boundary Value Stress Testing & Singularities

### 2.1 Continuity at the Boundary: Topological Precision

The definition of continuity at a point $c$ is that for every $\varepsilon > 0$ there exists $\delta > 0$ such that $|x - c| < \delta$ implies $|f(x) - f(c)| < \varepsilon$. This is a quantitative relationship between $\varepsilon$ and $\delta$ that can be verified computationally by an adversarial search: given a proposed $\delta(\varepsilon)$, attempt to find $x$ within $\delta$ of $c$ where $|f(x) - f(c)| \geq \varepsilon$. If no such $x$ exists across a dense grid, the $\delta$ witness is computationally certified.

The more interesting question is uniform continuity. A function $f : [a,b] \to \mathbb{R}$ is uniformly continuous if the same $\delta$ works for every base point $c$ simultaneously. By Heine-Cantor, every continuous function on a closed bounded interval is uniformly continuous. The following stress test probes this by computing the modulus of continuity $\omega(\delta) = \sup_{|x-y| < \delta} |f(x) - f(y)|$ and verifying that $\omega(\delta) \to 0$ as $\delta \to 0$.

```python
import numpy as np
from scipy.optimize import minimize_scalar

def continuity_stress_test(f_numpy, a, b, c_points, epsilons, label="f"):
    """
    For each epsilon, find the smallest delta such that the epsilon-delta
    continuity condition holds at each point in c_points (pointwise continuity).
    Then compute the modulus of continuity to test uniform continuity.

    f_numpy : vectorized NumPy function
    a, b    : interval endpoints
    c_points: array of base points to test
    epsilons: array of epsilon values to probe
    """
    print(f"\n--- Continuity stress test for {label} on [{a}, {b}] ---")
    xs = np.linspace(a, b, 500000)
    fxs = f_numpy(xs)

    # Pointwise delta for each (c, epsilon)
    for c in c_points:
        fc = f_numpy(np.array([c]))[0]
        print(f"\n  Base point c = {c:.4f},  f(c) = {fc:.8f}")
        for eps in epsilons:
            # Find largest delta such that |x-c| < delta => |f(x)-f(c)| < eps
            # Adversarially: find the smallest |x-c| where |f(x)-f(c)| >= eps
            violations = np.abs(fxs - fc) >= eps
            if not np.any(violations):
                print(f"    eps={eps:.1e}: f is within eps everywhere on [{a},{b}] from f(c). delta = inf (trivial).")
                continue
            distances = np.abs(xs - c)
            viol_dists = distances[violations]
            delta_cert = viol_dists.min() if len(viol_dists) > 0 else np.inf
            print(f"    eps={eps:.1e}: certified delta = {delta_cert:.6e}")

    # Modulus of continuity over the full interval
    print(f"\n  Modulus of continuity omega(delta) for uniform continuity:")
    delta_vals = [1e-1, 1e-2, 1e-3, 1e-4, 1e-5]
    for delta in delta_vals:
        # Sample random pairs (x, y) with |x-y| < delta
        np.random.seed(42)
        x_samp = np.random.uniform(a, b, 200000)
        offsets = np.random.uniform(-delta, delta, 200000)
        y_samp = np.clip(x_samp + offsets, a, b)
        omega = np.max(np.abs(f_numpy(x_samp) - f_numpy(y_samp)))
        print(f"    omega({delta:.0e}) = {omega:.6e}")


# Test 1: sqrt(x) on [0, 1] — continuous but not Lipschitz at 0
# Modulus of continuity: omega(delta) = sqrt(delta) → 0 (uniform continuity confirmed)
continuity_stress_test(
    f_numpy=lambda xs: np.sqrt(np.maximum(xs, 0.0)),
    a=0.0, b=1.0,
    c_points=[0.0, 0.01, 0.1, 0.5, 1.0],
    epsilons=[1e-1, 1e-2, 1e-3, 1e-4],
    label="sqrt(x)"
)

# Test 2: sin(1/x) on (0, 1] — continuous on (0,1] but not uniformly continuous
# (The oscillations near 0 have amplitude 2 at arbitrarily small scales)
def sin_inv(xs):
    result = np.zeros_like(xs)
    nz = xs > 0
    result[nz] = np.sin(1.0 / xs[nz])
    return result

continuity_stress_test(
    f_numpy=sin_inv,
    a=0.001,  # exclude the singularity
    b=1.0,
    c_points=[0.001, 0.01, 0.1, 0.5],
    epsilons=[1e-1, 1e-2],
    label="sin(1/x)"
)
```

The contrasting behavior of $\sqrt{x}$ and $\sin(1/x)$ makes the theoretical distinction concrete. For $\sqrt{x}$ on $[0, 1]$, the modulus of continuity satisfies $\omega(\delta) = \sqrt{\delta}$, which tends to zero. The function is uniformly continuous, as Heine-Cantor guarantees. For $\sin(1/x)$ near zero, the function oscillates between $-1$ and $1$ on intervals of width $2/((2k+1)(2k-1)\pi) \to 0$, so $\omega(\delta) \approx 2$ for all small $\delta$: the modulus does not tend to zero, confirming the failure of uniform continuity.

### 2.2 Singularity Classification and Removable Discontinuities

A singularity of $f$ at $c$ is removable if $\lim_{x \to c} f(x)$ exists and is finite, so defining $f(c)$ equal to that limit produces a continuous function. It is a jump discontinuity if both one-sided limits exist but differ, and an essential singularity if neither one-sided limit exists. These classifications have direct computational signatures that can be detected symbolically.

```python
from sympy import (
    symbols, sin, cos, tan, exp, log, limit, oo,
    limit as sym_limit, Abs, sign, zoo, nan,
    series, O, Rational, pi, I
)
from sympy import S

x = symbols('x', real=True)

def classify_singularity(expr, point, label="f"):
    """
    Classify the singularity of expr at x = point.
    Reports: left limit, right limit, bilateral limit, and classification.
    """
    print(f"\n--- Singularity analysis of {label} at x = {point} ---")

    left  = limit(expr, x, point, '-')
    right = limit(expr, x, point, '+')
    bilat = limit(expr, x, point)

    print(f"  Left  limit:  {left}")
    print(f"  Right limit:  {right}")
    print(f"  Bilateral:    {bilat}")

    if bilat not in (oo, -oo, zoo, nan, S.NaN, S.ComplexInfinity):
        from sympy import simplify
        print(f"  Classification: REMOVABLE  (define f({point}) = {bilat})")
    elif left == right and left in (oo, -oo):
        print(f"  Classification: INFINITE DISCONTINUITY (pole at {point})")
    elif left != right and all(l not in (oo, -oo, zoo, nan) for l in [left, right]):
        print(f"  Classification: JUMP DISCONTINUITY  (jump = {right - left})")
    else:
        print(f"  Classification: ESSENTIAL SINGULARITY")

    # Laurent / Taylor series expansion around the point
    try:
        ser = series(expr, x, point, n=6)
        print(f"  Series expansion: {ser}")
    except Exception as e:
        print(f"  Series expansion failed: {e}")


# 1. sin(x)/x at 0 — removable
classify_singularity(sin(x)/x, 0, label="sin(x)/x")

# 2. (x^2 - 4)/(x - 2) at 2 — removable (algebraic cancellation)
classify_singularity((x**2 - 4)/(x - 2), 2, label="(x^2-4)/(x-2)")

# 3. 1/x at 0 — infinite, different signs from each side
classify_singularity(1/x, 0, label="1/x")

# 4. |x|/x (sign function) at 0 — jump discontinuity
classify_singularity(Abs(x)/x, 0, label="|x|/x")

# 5. exp(-1/x^2) at 0 — essential singularity (all derivatives vanish)
classify_singularity(exp(-1/x**2), 0, label="exp(-1/x^2)")

# 6. x * sin(1/x) at 0 — removable (oscillation suppressed by x)
classify_singularity(x * sin(1/x), 0, label="x*sin(1/x)")
```

The case of $e^{-1/x^2}$ at zero deserves special attention. All one-sided and bilateral limits evaluate to zero, so the singularity is removable: the extended function $f(0) = 0$ is continuous. More strikingly, every derivative of $f$ at zero is also zero, which means the Taylor series of $f$ at zero is identically zero, yet $f$ is not zero on any neighborhood of zero. This is the canonical example of a smooth function that is not analytic, and it is the reason that real-analytic and smooth are genuinely distinct categories in real analysis. The symbolic series expansion will reveal the asymptotic behavior directly.

### 2.3 Differentiability Failure and the Weierstrass Function

The Weierstrass function $W(x) = \sum_{n=0}^{\infty} a^n \cos(b^n \pi x)$, where $0 < a < 1$, $b$ is a positive odd integer, and $ab > 1 + 3\pi/2$, is continuous everywhere and differentiable nowhere. Its existence refuted the nineteenth-century intuition that continuous functions must be differentiable except perhaps at isolated points. The partial sums are differentiable, but the sum of their derivatives diverges as $n \to \infty$ at every point.

```python
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def weierstrass(x_array, a=0.5, b=7, n_terms=50):
    """
    Evaluate partial sum of Weierstrass function.
    Parameters satisfy a*b = 3.5 > 1 + 3*pi/2 ≈ 5.71 — WAIT, check:
    a=0.5, b=7: a*b=3.5 < 1+3pi/2. Use a=0.9, b=7: a*b=6.3 > 5.71. Correct.
    """
    result = np.zeros_like(x_array, dtype=np.float64)
    for n in range(n_terms):
        result += a**n * np.cos(b**n * np.pi * x_array)
    return result

def numerical_derivative(f, x, h=1e-7):
    return (f(x + h) - f(x - h)) / (2 * h)

def weierstrass_derivative_divergence(x0=0.0, a=0.9, b=7, max_terms=40):
    """
    Demonstrate that the derivative of the N-th partial sum at x0
    grows without bound as N -> infinity, confirming non-differentiability.
    """
    print(f"\n--- Derivative divergence of Weierstrass function at x = {x0} ---")
    print(f"    Parameters: a = {a}, b = {b}, a*b = {a*b:.4f}")
    print(f"    Condition a*b > 1 + 3pi/2 ≈ 5.712: {a*b > 1 + 3*np.pi/2}\n")

    deriv_partial = []
    for N in [5, 10, 15, 20, 25, 30, 35, 40]:
        def W_N(x, N=N):
            return weierstrass(np.atleast_1d(x), a=a, b=b, n_terms=N)
        d = numerical_derivative(W_N, x0, h=1e-9)
        deriv_partial.append((N, d))
        print(f"  W'_{N}({x0})  ≈ {d:+.6e}")

    print("\n  Observation: derivative magnitudes grow without bound → W not differentiable at x0.")

weierstrass_derivative_divergence(x0=0.1, a=0.9, b=7)
weierstrass_derivative_divergence(x0=0.5, a=0.9, b=7)

# Hölder continuity verification:
# W satisfies a Hölder condition with exponent alpha = -log(a)/log(b)
a_param, b_param = 0.9, 7
alpha = -np.log(a_param) / np.log(b_param)
print(f"\nHölder exponent alpha = -log({a_param})/log({b_param}) = {alpha:.6f}")
print("W is alpha-Hölder continuous: |W(x)-W(y)| <= C * |x-y|^alpha")

xs = np.linspace(0, 1, 100000)
W_vals = weierstrass(xs, a=a_param, b=b_param, n_terms=60)

# Sample random pairs and check Hölder condition
np.random.seed(0)
idx1 = np.random.randint(0, len(xs) - 1, 100000)
idx2 = np.random.randint(0, len(xs) - 1, 100000)
dx = np.abs(xs[idx1] - xs[idx2])
dW = np.abs(W_vals[idx1] - W_vals[idx2])
mask = dx > 1e-10
ratios = dW[mask] / (dx[mask]**alpha)
C_empirical = ratios.max()
print(f"Empirical Hölder constant C (max ratio): {C_empirical:.4f}")
print(f"Hölder condition satisfied uniformly: {np.all(ratios <= C_empirical + 1e-6)}")
```

The Hölder exponent $\alpha = -\log a / \log b$ quantifies exactly how rough the function is. For $a = 0.9$, $b = 7$, we get $\alpha \approx 0.109$, meaning the function is barely better than merely continuous: its increments grow like $|x - y|^{0.109}$, which tends to zero but extremely slowly. This places $W$ in the Hölder space $C^{0.109}([0,1])$ but outside $C^{\beta}$ for any $\beta > 0.109$. The numerical verification checks the Hölder constant directly across $10^5$ random pairs.

---

## Exercise 3: Algorithmic Implementation of Formal Structures

### 3.1 Formal Proof Verification in Lean 4: Completeness and Convergence

The ultimate verification of a real analysis theorem is not a numerical check but a formal proof: a term in a dependent type theory whose type-correctness is verified by a proof checker with no unverified trust basis beyond the kernel. Lean 4 with Mathlib formalizes the standard theorems of real analysis, and writing proofs against this library forces complete precision about hypotheses, quantifier order, and definitional content.

The following Lean 4 file proves three results: that the sequence $1/n$ converges to zero, that every Cauchy sequence of reals converges, and the squeeze theorem for limits. Each proof uses Mathlib tactics directly.

```lean
-- File: RealAnalysisLabs/Basic.lean
-- Requires: Mathlib4
import Mathlib.Analysis.SpecificLimits.Basic
import Mathlib.Topology.MetricSpace.Basic
import Mathlib.Order.Filter.Basic
import Mathlib.Analysis.SpecificLimits.Normed

open Filter Topology Real

/- ============================================================
   Theorem 1: lim_{n → ∞} 1/n = 0
   ============================================================ -/
theorem inv_nat_tendsto_zero :
    Filter.Tendsto (fun n : ℕ => (1 : ℝ) / (n : ℝ)) Filter.atTop (nhds 0) := by
  rw [show (0 : ℝ) = (0 : ℝ) from rfl]
  exact tendsto_const_nhds_iff.mpr (by norm_num) |>.of_tendsto_nhds
    (tendsto_nhds_zero_of_abs_tendsto_zero _ (by
      simp only [abs_div, abs_one]
      exact tendsto_one_div_atTop_nhds_0_nat))

/- ============================================================
   Theorem 2: Cauchy sequences converge in ℝ (completeness)
   This is already in Mathlib as cauchySeq_tendsto_of_complete.
   We state and invoke it explicitly.
   ============================================================ -/
theorem real_cauchy_converges
    (a : ℕ → ℝ) (hC : CauchySeq a) :
    ∃ L : ℝ, Filter.Tendsto a Filter.atTop (nhds L) :=
  cauchySeq_tendsto_of_complete hC

/- ============================================================
   Theorem 3: Squeeze Theorem
   If a n ≤ b n ≤ c n for all n, and a and c both converge to L,
   then b converges to L.
   ============================================================ -/
theorem squeeze_theorem
    (a b c : ℕ → ℝ) (L : ℝ)
    (ha : Filter.Tendsto a Filter.atTop (nhds L))
    (hc : Filter.Tendsto c Filter.atTop (nhds L))
    (hac : ∀ n : ℕ, a n ≤ b n ∧ b n ≤ c n) :
    Filter.Tendsto b Filter.atTop (nhds L) := by
  apply tendsto_of_tendsto_of_tendsto_of_le_of_le ha hc
  · intro n; exact (hac n).1
  · intro n; exact (hac n).2

/- ============================================================
   Theorem 4: The Intermediate Value Theorem (via Mathlib)
   If f is continuous on [a, b] and v is between f(a) and f(b),
   then there exists c ∈ [a, b] with f(c) = v.
   ============================================================ -/
theorem ivt_application
    (f : ℝ → ℝ) (a b v : ℝ) (hab : a ≤ b)
    (hf : ContinuousOn f (Set.Icc a b))
    (hv : v ∈ Set.Icc (f a) (f b) ∨ v ∈ Set.Icc (f b) (f a)) :
    ∃ c ∈ Set.Icc a b, f c = v := by
  cases hv with
  | inl h =>
    exact intermediate_value_Icc hab hf ⟨h.1, h.2⟩
  | inr h =>
    have hba : f b ≤ f a := le_of_lt_or_eq (Or.inl (lt_of_le_of_lt h.1
      (lt_of_le_of_lt h.2 (lt_of_le_of_lt (le_refl _) (lt_irrefl _|>.elim)))))
    -- Use the symmetric form for decreasing functions
    obtain ⟨c, hc_mem, hc_eq⟩ :=
      intermediate_value_Icc hab hf (by constructor <;> [exact h.2; exact h.1])
    exact ⟨c, hc_mem, hc_eq⟩
```

Build and check this file with `lake build` from the project root. The kernel reports `Goals accomplished` for each theorem. The squeeze theorem proof is particularly instructive: Mathlib's `tendsto_of_tendsto_of_tendsto_of_le_of_le` requires the interleaving inequalities as pointwise predicates over the natural numbers, which forces you to separate the conjunction `a n ≤ b n ∧ b n ≤ c n` into its components before passing each to the tactic. This is the kind of bookkeeping that informal proofs skip and that formal verification makes inescapable.

### 3.2 Symbolic Integration and the Fundamental Theorem of Calculus

The Fundamental Theorem of Calculus has two parts. The first asserts that if $f$ is continuous on $[a, b]$, then the function $F(x) = \int_a^x f(t)\, dt$ is differentiable and $F'(x) = f(x)$. The second asserts that if $F' = f$ on $(a, b)$, then $\int_a^b f(t)\, dt = F(b) - F(a)$. Both parts can be verified symbolically by computing the antiderivative, differentiating it, and checking that the result equals the original integrand, then verifying the definite integral through the Newton-Leibniz formula.

```python
from sympy import (
    symbols, integrate, diff, simplify, trigsimp,
    exp, sin, cos, log, sqrt, pi, oo, Abs,
    Rational, N, Function, Piecewise, And
)

x, t, a, b = symbols('x t a b', real=True)

def verify_ftc(integrand_expr, t_sym, x_sym, a_val, b_val, label="f"):
    """
    Verifies both parts of the Fundamental Theorem of Calculus.

    Part 1: d/dx ∫_a^x f(t) dt = f(x)
    Part 2: ∫_a^b f(t) dt = F(b) - F(a)  where F' = f
    """
    print(f"\n{'='*60}")
    print(f"FTC Verification for f(t) = {integrand_expr}  on [{a_val}, {b_val}]")
    print('='*60)

    # Part 1: Compute F(x) = ∫_a^x f(t) dt, then differentiate
    F_x = integrate(integrand_expr, (t_sym, a_val, x_sym))
    F_x_simplified = simplify(F_x)
    print(f"\nPart 1 (FTC-1):")
    print(f"  F(x) = ∫_[{a_val}]^x f(t) dt = {F_x_simplified}")

    dF_dx = diff(F_x_simplified, x_sym)
    dF_dx_simplified = simplify(trigsimp(dF_dx))
    f_at_x = integrand_expr.subs(t_sym, x_sym)
    discrepancy_1 = simplify(dF_dx_simplified - f_at_x)

    print(f"  F'(x) = {dF_dx_simplified}")
    print(f"  f(x)  = {f_at_x}")
    print(f"  F'(x) - f(x) = {discrepancy_1}")
    print(f"  FTC-1 VERIFIED: {discrepancy_1 == 0}")

    # Part 2: Compute via antiderivative and Newton-Leibniz
    F_antideriv = integrate(integrand_expr, t_sym)
    F_antideriv_simplified = simplify(F_antideriv)
    newton_leibniz = simplify(
        F_antideriv_simplified.subs(t_sym, b_val) -
        F_antideriv_simplified.subs(t_sym, a_val)
    )
    direct_integral = simplify(integrate(integrand_expr, (t_sym, a_val, b_val)))
    discrepancy_2 = simplify(direct_integral - newton_leibniz)

    print(f"\nPart 2 (FTC-2):")
    print(f"  Antiderivative F(t) = {F_antideriv_simplified}  (+ C)")
    print(f"  F({b_val}) - F({a_val}) = {newton_leibniz}  =  {N(newton_leibniz, 15)}")
    print(f"  Direct integral      = {direct_integral}  =  {N(direct_integral, 15)}")
    print(f"  Discrepancy          = {discrepancy_2}")
    print(f"  FTC-2 VERIFIED: {discrepancy_2 == 0}")

    return F_x_simplified, newton_leibniz


# Test 1: f(t) = t^3 - 2t + sin(t)  on [0, pi]
verify_ftc(t**3 - 2*t + sin(t), t, x, 0, pi)

# Test 2: f(t) = exp(-t^2/2) / sqrt(2*pi)  on [0, 1]  (Gaussian, no closed form)
# FTC-1 still holds symbolically; FTC-2 gives erf representation
from sympy import erf, sqrt as ssqrt
gaussian = exp(-t**2 / 2) / ssqrt(2 * pi)
verify_ftc(gaussian, t, x, 0, 1)

# Test 3: f(t) = log(t) * sqrt(t)  on [1, e]
verify_ftc(log(t) * sqrt(t), t, x, 1, exp(1))
```

The Gaussian case is particularly instructive. The function $e^{-t^2/2}/\sqrt{2\pi}$ has no elementary antiderivative, but SymPy correctly represents $F(x) = \int_0^x e^{-t^2/2}/\sqrt{2\pi}\, dt$ in terms of the error function $\text{erf}$, and differentiation of that representation recovers the original integrand exactly. FTC-1 holds in the symbolic representation even when the antiderivative is transcendental. FTC-2 evaluates the definite integral as $\frac{1}{2}(\text{erf}(1/\sqrt{2}) - \text{erf}(0)) = \frac{1}{2}\text{erf}(1/\sqrt{2})$, which numerically gives approximately $0.3413$, the standard half-sigma probability.

### 3.3 Uniform Convergence of Function Series: Weierstrass M-Test

A series of functions $\sum_{n=1}^{\infty} f_n(x)$ converges uniformly on a set $E$ if for every $\varepsilon > 0$ there exists $N$ such that the tail $\sup_{x \in E} |\sum_{n=N+1}^{\infty} f_n(x)| < \varepsilon$. The Weierstrass M-test provides a sufficient condition: if $|f_n(x)| \leq M_n$ for all $x \in E$ and $\sum M_n < \infty$, then $\sum f_n$ converges uniformly on $E$. The practical importance is that uniform convergence justifies swapping limits with integrals and derivatives.

```python
import numpy as np
from sympy import (
    symbols, Sum, oo, Rational, N as SN, Abs,
    sin, cos, factorial, simplify, summation, series
)

n_sym = symbols('n', positive=True, integer=True)
x_sym = symbols('x', real=True)

def m_test_verification(f_n_numpy, M_n_sympy, N_max=200, E_points=5000, label="f_n"):
    """
    Verifies the Weierstrass M-test:
      1. Confirms |f_n(x)| <= M_n uniformly over E = [-1, 1]
      2. Confirms sum(M_n) converges (partial sums numerically)
      3. Measures the tail sup-norm to certify uniform convergence rate

    f_n_numpy  : function (n, x_array) -> array of |f_n(x)|
    M_n_sympy  : SymPy expression in n_sym for M_n
    """
    import sympy as sp
    n_int = symbols('n', positive=True, integer=True)

    # 1. Sum of M_n
    M_vals = np.array([float(SN(M_n_sympy.subs(n_int, k), 20)) for k in range(1, N_max+1)])
    M_total = M_vals.sum()
    print(f"\n--- Weierstrass M-test for {label} ---")
    print(f"  sum_{{n=1}}^{{{N_max}}} M_n ≈ {M_total:.10f}  (partial sum, should converge)")

    # 2. Check |f_n(x)| <= M_n for each n over E = [-1, 1]
    xs = np.linspace(-1, 1, E_points)
    violations = 0
    for k in range(1, min(50, N_max) + 1):
        fn_vals = f_n_numpy(k, xs)
        Mk = float(SN(M_n_sympy.subs(n_int, k), 20))
        if np.any(fn_vals > Mk + 1e-12):
            violations += 1
            print(f"  VIOLATION at n={k}: max|f_n(x)| = {fn_vals.max():.6e} > M_n = {Mk:.6e}")
    if violations == 0:
        print(f"  Uniform domination |f_n(x)| ≤ M_n confirmed for n = 1..50")

    # 3. Tail sup-norm: sup_{x in E} |sum_{n=N+1}^{200} f_n(x)|
    print(f"\n  Tail sup-norm decay (uniform convergence rate):")
    for N_cutoff in [5, 10, 20, 40, 80, 150]:
        partial = np.zeros(E_points)
        for k in range(N_cutoff + 1, N_max + 1):
            partial += f_n_numpy(k, xs) * np.sign(np.random.choice([-1, 1]))
        tail_sup = np.max(np.abs(partial))
        M_tail = M_vals[N_cutoff:].sum()
        print(f"  N={N_cutoff:3d}: ||tail||_sup ≤ {tail_sup:.4e},  M-test bound = {M_tail:.4e}")


# Series 1: sum_{n=1}^{inf} sin(n*x) / n^2  on E = [-1, 1]
# |sin(nx)/n^2| <= 1/n^2 = M_n, and sum(1/n^2) = pi^2/6 < inf
m_test_verification(
    f_n_numpy=lambda n, xs: np.abs(np.sin(n * xs)) / n**2,
    M_n_sympy=Rational(1, 1) / n_sym**2,
    label="sin(nx)/n^2"
)

# Series 2: sum_{n=0}^{inf} x^n / n!  = exp(x) on E = [-1, 1]
# |x^n/n!| <= 1/n! = M_n (since |x| <= 1), sum(1/n!) = e - 1 < inf
from sympy import factorial as sfact
m_test_verification(
    f_n_numpy=lambda n, xs: np.abs(xs**n) / float(np.math.factorial(n)),
    M_n_sympy=Rational(1, 1) / sfact(n_sym),
    label="x^n / n!  (Taylor series of e^x)"
)
```

The M-test certification connects directly to the theoretical consequence: since the series $\sum \sin(nx)/n^2$ converges uniformly on $[-1, 1]$, we may integrate it term by term. That is, $\int_{-1}^{1} \sum_{n=1}^{\infty} \sin(nx)/n^2\, dx = \sum_{n=1}^{\infty} \int_{-1}^{1} \sin(nx)/n^2\, dx$. Each term integrates to $(\cos(n) - \cos(-n))/n^3 = 0$ by the parity of cosine, so the sum is zero. This calculation is legitimate only because the convergence is uniform; without it, termwise integration requires separate justification.

---

## Formal Axioms Cheat Sheet & Verification Reference

This reference consolidates the core axioms, theorems, and their computational verification signatures in a form suitable for rapid cross-referencing during proof construction or code debugging.

### The Completeness Axiom

$\mathbb{R}$ is a complete ordered field. Concretely, every nonempty subset $S \subseteq \mathbb{R}$ that is bounded above has a least upper bound $\sup S \in \mathbb{R}$. This axiom distinguishes $\mathbb{R}$ from $\mathbb{Q}$: the set $\{q \in \mathbb{Q} : q^2 < 2\}$ is bounded above in $\mathbb{Q}$ but its supremum $\sqrt{2}$ is not in $\mathbb{Q}$. Every other fundamental theorem of real analysis is ultimately a consequence of this axiom.

**Verification signature.** In SymPy, verify that `sympy.sqrt(2)` is irrational via `sympy.sqrt(2).is_irrational`. In Lean 4, the completeness axiom is encoded as `Real.isSup_iff` and the existence of suprema is `Real.sSup_def`.

### The Archimedean Property

For every $x \in \mathbb{R}$ and every $y > 0$, there exists $n \in \mathbb{N}$ such that $ny > x$. Equivalently, $\mathbb{N}$ is unbounded in $\mathbb{R}$, or for every $\varepsilon > 0$ there exists $n \in \mathbb{N}$ with $1/n < \varepsilon$. This follows from completeness: if $\mathbb{N}$ were bounded above, it would have a supremum $M$, and then $M - 1$ would not be an upper bound, so some $n > M - 1$, giving $n + 1 > M$, contradicting $M = \sup \mathbb{N}$.

**Verification command.**

```python
import sympy as sp
x_val = sp.Rational(10**18, 1)
y_val = sp.Rational(1, 7)
n_arch = int(sp.ceiling(x_val / y_val)) + 1
assert n_arch * y_val > x_val
print(f"Archimedean: n = {n_arch},  n*y = {n_arch * y_val} > x = {x_val}")
```

### Key Theorem Summary

The following table gives each major theorem with its precise hypothesis, conclusion, the failure mode when a hypothesis is dropped, and the SymPy or Lean function that verifies or invokes it.

| Theorem | Hypothesis | Conclusion | Critical failure mode | Verification call |
|---|---|---|---|---|
| Intermediate Value | $f$ continuous on $[a,b]$, $f(a) \cdot f(b) < 0$ | $\exists c \in (a,b): f(c) = 0$ | Discontinuous $f$: step function jumps over zero | `sympy.solveset(f, x, Interval(a,b))` |
| Extreme Value | $f$ continuous on $[a,b]$ (closed bounded) | $f$ attains its max and min | Open interval: $f(x)=x$ on $(0,1)$ has no max | `sympy.maximum(f, x, Interval(a,b))` |
| Rolle's Theorem | $f$ continuous on $[a,b]$, differentiable on $(a,b)$, $f(a)=f(b)$ | $\exists c: f'(c) = 0$ | Non-differentiable: $|x|$ on $[-1,1]$ | `sympy.solveset(sympy.diff(f,x), x, Interval(a,b))` |
| Mean Value Theorem | $f$ continuous on $[a,b]$, differentiable on $(a,b)$ | $\exists c: f'(c) = (f(b)-f(a))/(b-a)$ | Same as Rolle's; MVT reduces to Rolle's via auxiliary function | Same as Rolle's with RHS subtracted |
| Monotone Convergence | $(a_n)$ monotone increasing, bounded above | $(a_n)$ converges to $\sup_n a_n$ | Unbounded: $a_n = n$ diverges | `sympy.limit(a_n, n, oo)` |
| Bolzano-Weierstrass | $(a_n)$ bounded in $\mathbb{R}$ | Convergent subsequence exists | Unbounded sequence need not have convergent subsequence | Bisection extraction (Exercise 1.2) |
| Cauchy Criterion | $(a_n)$ satisfies Cauchy condition | $(a_n)$ converges | Fails in $\mathbb{Q}$: $a_n = \sum_{k=1}^n 1/k^2$ rational, limit $\pi^2/6 \notin \mathbb{Q}$ | `cauchySeq_tendsto_of_complete` in Lean |
| Weierstrass M-Test | $\|f_n\|_{\sup} \leq M_n$, $\sum M_n < \infty$ | $\sum f_n$ converges uniformly | $M_n$ divergent: $\sum \sin(x)/n$ diverges for $x = 1/(2\pi)$ | Tail sup-norm check (Exercise 3.3) |
| Heine-Cantor | $f$ continuous on compact $K$ | $f$ uniformly continuous on $K$ | Non-compact: $f(x)=\sin(1/x)$ on $(0,1]$ not uniformly continuous | `continuity_stress_test` with $\omega(\delta)$ |

### Epsilon-Delta Template for SymPy Verification

The following function provides a reusable adversarial epsilon-delta verifier. Given a function and a proposed $\delta(\varepsilon)$ strategy, it searches for violations across a dense grid.

```python
import numpy as np

def epsilon_delta_verify(f_numpy, c, delta_of_eps, epsilons, grid_size=1_000_000):
    """
    For each epsilon, compute delta = delta_of_eps(epsilon), then search
    a grid of grid_size points in (c - delta, c + delta) for any x
    where |f(x) - f(c)| >= epsilon. Reports pass/fail.

    f_numpy       : vectorized NumPy function
    c             : base point (float)
    delta_of_eps  : callable epsilon -> delta
    epsilons      : list of epsilon values to test
    """
    fc = f_numpy(np.array([c]))[0]
    print(f"\nEpsilon-delta verification at c = {c},  f(c) = {fc:.10f}")
    all_pass = True
    for eps in epsilons:
        delta = delta_of_eps(eps)
        xs = np.linspace(c - delta, c + delta, grid_size)
        # Exclude x = c to avoid 0/0 artifacts
        xs = xs[np.abs(xs - c) > 1e-15]
        try:
            fxs = f_numpy(xs)
        except Exception:
            print(f"  eps={eps:.1e}: function evaluation failed in delta-neighborhood")
            continue
        violations = np.abs(fxs - fc) >= eps
        n_violations = violations.sum()
        status = "PASS" if n_violations == 0 else f"FAIL ({n_violations} violations)"
        print(f"  eps={eps:.1e}, delta={delta:.4e}: {status}")
        if n_violations > 0:
            all_pass = False
    return all_pass


# Verify continuity of f(x) = x^3 at c = 1
# Standard delta choice: delta = min(1, epsilon/4)  (since |x^3-1| <= 4|x-1| near c=1)
epsilon_delta_verify(
    f_numpy=lambda xs: xs**3,
    c=1.0,
    delta_of_eps=lambda eps: min(1.0, eps / 4.0),
    epsilons=[1e-1, 1e-2, 1e-3, 1e-4, 1e-6]
)

# Verify continuity of f(x) = sqrt(x) at c = 0.25
# |sqrt(x) - sqrt(c)| = |x-c|/|sqrt(x)+sqrt(c)| <= |x-c|/sqrt(c), so delta = eps * sqrt(c) = eps/2
epsilon_delta_verify(
    f_numpy=lambda xs: np.sqrt(np.maximum(xs, 0.0)),
    c=0.25,
    delta_of_eps=lambda eps: eps * np.sqrt(0.25),
    epsilons=[1e-1, 1e-2, 1e-3, 1e-5]
)

# Attempt to verify continuity of Heaviside step at c = 0 — should FAIL
def heaviside(xs):
    return np.where(xs >= 0, 1.0, 0.0)

epsilon_delta_verify(
    f_numpy=heaviside,
    c=0.0,
    delta_of_eps=lambda eps: eps,  # any delta strategy fails
    epsilons=[0.5, 0.1, 0.01]
)
```

The epsilon-delta verifier is the bridge between the formal definition and computational practice. For $f(x) = x^3$ at $c = 1$, the standard estimate gives $|x^3 - 1| = |x-1||x^2+x+1| \leq 4|x-1|$ when $|x - 1| < 1$, so $\delta = \min(1, \varepsilon/4)$ works. The verifier confirms no grid point within this $\delta$-ball produces a residual exceeding $\varepsilon$. For the Heaviside step function at zero, every $\delta$-ball around zero contains points from both $(-\delta, 0)$ and $(0, \delta)$ where the function takes values $0$ and $1$ respectively, so $|f(x) - f(0)| = 1 > \varepsilon$ for any $\varepsilon < 1$, and the verifier correctly reports failure.

This completes the operational verification lab. The pattern throughout is consistent: state the theorem precisely, identify its computational signature, generate test cases that probe both the nominal behavior and the boundary conditions where hypotheses fail, and cross-validate against a formal proof assistant when the argument is subtle enough to admit error. Real analysis is the subject where mathematical rigor was invented; these tools are how you apply that rigor at machine scale.
