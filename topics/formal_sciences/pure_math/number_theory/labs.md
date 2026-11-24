# Operational Verification Labs: Number Theory

## Objective & Mathematical Computing Setup

Number theory stands as one of the oldest and most elegant branches of pure mathematics, yet its computational verification demands precision tooling that bridges abstract algebraic reasoning with symbolic execution. These operational laboratories transform classical theorems—divisibility properties, congruence arithmetic, primality structure, multiplicative functions, and Diophantine equations—into verified computational artifacts. The practitioner working through these exercises will not merely assert that Fermat's Little Theorem holds or that the Euclidean algorithm terminates; instead, you will construct formal proofs mechanized through computer algebra systems and proof assistants, stress-test boundary cases that expose the structural limits of number-theoretic functions, and implement algorithms whose correctness follows directly from first principles.

The computational environment for rigorous number theory verification requires Python 3.11 or later as the foundational runtime, augmented by SymPy for symbolic manipulation of integers, polynomials, and algebraic number fields. SymPy provides a pure-Python implementation of divisibility predicates, primality testing via Miller-Rabin and deterministic methods, modular arithmetic rings, and continued fraction expansions. For deeper symbolic computation involving algebraic number theory and elliptic curves, SageMath delivers a comprehensive mathematical software system built atop Python, integrating PARI/GP for high-performance number-theoretic routines, Maxima for symbolic integration, and GAP for computational group theory. When formal proof verification becomes essential—particularly for foundational results like Bézout's identity or the Chinese Remainder Theorem—Lean 4 and Coq offer interactive theorem provers with substantial mathematical libraries (Mathlib for Lean, Mathematical Components for Coq) that permit machine-checked derivations.

Begin by establishing your computational workspace. Install SymPy and NumPy through the Python package manager: execute `pip install sympy numpy` in your terminal, ensuring that your Python interpreter resolves to version 3.11 or higher. Verify the installation by running `python -c 'import sympy; print(sympy.__version__)'`, which should report version 1.12 or later. For SageMath, the recommended approach involves either downloading the precompiled binary distribution from sagemath.org or using a containerized environment via Docker with the official `sagemath/sagemath` image. Launch SageMath in interactive mode by invoking `sage` from your terminal, which drops you into an IPython-enhanced REPL with all mathematical libraries preloaded. If you pursue formal proof verification, install Lean 4 through `elan` (the Lean version manager) with `curl https://raw.githubusercontent.com/leanprover/elan/master/elan-init.sh -sSf | sh`, then initialize a Lean project with `lake new number_theory math` and add the Mathlib dependency to your `lakefile.lean`.

The philosophical approach throughout these laboratories prioritizes constructive verification over passive observation. Each exercise presents a number-theoretic statement—a divisibility criterion, a multiplicative function identity, an algorithmic procedure—and challenges you to verify its correctness through three complementary modalities. First, symbolic computation produces concrete numerical evidence across parameter ranges, testing the statement against hundreds or thousands of instantiations to detect counterexamples or confirm patterns. Second, algorithmic implementation translates the mathematical structure into executable code whose correctness you analyze through invariant checking, complexity bounds, and edge-case handling. Third, formal proof construction encodes the theorem in a proof assistant, forcing you to supply every inference step explicitly and mechanically verify that your reasoning contains no logical gaps.

Throughout these exercises, maintain a disciplined computational notebook—either Jupyter for Python-centric work or a Lean project directory for formal proofs. Document every verification step, recording not just the final result but the intermediate symbolic simplifications, the parameter ranges tested, and the reasoning that justifies algorithmic correctness. Number theory's beauty lies in its accessibility to elementary reasoning combined with its depth of structural insight; the computational verification process amplifies both dimensions, making abstract arguments tangible while exposing subtle edge cases that pure reasoning might overlook.

## Exercise 1: Computational Verification of Core Theorems

The foundational architecture of elementary number theory rests on divisibility, the Euclidean algorithm, and congruence arithmetic. These structures admit both symbolic verification and algorithmic implementation, making them ideal starting points for rigorous computational exploration. You will verify Bézout's identity through extended Euclidean computation, confirm the structural properties of the greatest common divisor as a lattice meet operation, explore Fermat's Little Theorem and Euler's generalization across modular arithmetic rings, and implement Wilson's Theorem with explicit prime boundary testing.

**Bézout's Identity and the Extended Euclidean Algorithm**

Bézout's identity asserts that for any integers $a$ and $b$, there exist integers $x$ and $y$ such that $\gcd(a, b) = ax + by$. This identity is not merely an existence statement; the extended Euclidean algorithm provides a constructive procedure for computing the coefficients $x$ and $y$ through backward substitution along the Euclidean division sequence. Begin by implementing the extended Euclidean algorithm in pure Python, ensuring that your implementation handles all edge cases including zero inputs, negative integers, and coprime pairs.

```python
import sympy as sp
from sympy import gcd, igcd, gcdex

def extended_euclidean(a, b):
    """
    Compute gcd(a, b) and Bézout coefficients x, y such that ax + by = gcd(a, b).
    Returns (g, x, y) where g = gcd(a, b).
    """
    if b == 0:
        return (abs(a), 1 if a >= 0 else -1, 0)
    
    old_r, r = a, b
    old_s, s = 1, 0
    old_t, t = 0, 1
    
    while r != 0:
        quotient = old_r // r
        old_r, r = r, old_r - quotient * r
        old_s, s = s, old_s - quotient * s
        old_t, t = t, old_t - quotient * t
    
    # Normalize so gcd is positive
    if old_r < 0:
        return (-old_r, -old_s, -old_t)
    return (old_r, old_s, old_t)

# Verification against SymPy's built-in implementation
test_pairs = [
    (252, 105),
    (1071, 462),
    (17, 13),
    (1234567890, 9876543210),
    (-48, 18),
    (0, 15),
    (13, 0)
]

print("Bézout Identity Verification:")
print("=" * 80)
for a, b in test_pairs:
    g, x, y = extended_euclidean(a, b)
    x_sympy, y_sympy, g_sympy = sp.gcdex(a, b)
    
    # Verify identity holds
    identity_check = a * x + b * y
    assert identity_check == g, f"Identity failed: {a}*{x} + {b}*{y} = {identity_check}, expected {g}"
    
    # Verify agreement with SymPy
    assert g == g_sympy, f"GCD mismatch: computed {g}, SymPy gives {g_sympy}"
    
    print(f"gcd({a:15}, {b:15}) = {g:10} = {a:15}*({x:8}) + {b:15}*({y:8})")
    print(f"  Verification: {a}*({x}) + {b}*({y}) = {identity_check} ✓")
```

Execute this verification suite and observe how the algorithm handles the boundary cases. When $b = 0$, the gcd is $|a|$ with coefficients $x = \pm 1$ and $y = 0$. For negative inputs, the algorithm maintains the invariant that the gcd remains positive while adjusting the sign of coefficients. The pair $(1234567890, 9876543210)$ tests the algorithm's performance on large integers, where SymPy's optimized backend demonstrates computational efficiency.

**Fermat's Little Theorem and Euler's Totient Function**

Fermat's Little Theorem states that if $p$ is prime and $a$ is not divisible by $p$, then $a^{p-1} \equiv 1 \pmod{p}$. Euler generalized this to arbitrary moduli: for any integer $a$ coprime to $n$, we have $a^{\phi(n)} \equiv 1 \pmod{n}$, where $\phi(n)$ denotes Euler's totient function counting integers in $\{1, 2, \ldots, n\}$ coprime to $n$. Verify these theorems computationally across a spectrum of moduli, testing both the prime case and composite moduli with nontrivial factorizations.

```python
from sympy import isprime, totient, primefactors, factorint, gcd
from sympy.ntheory.modular import crt
import random

def verify_fermat_little_theorem(p, sample_size=100):
    """
    Verify Fermat's Little Theorem for prime p across random bases a.
    Tests that a^(p-1) ≡ 1 (mod p) for all a coprime to p.
    """
    if not isprime(p):
        raise ValueError(f"{p} is not prime")
    
    failures = []
    for _ in range(sample_size):
        a = random.randint(2, p - 1)
        residue = pow(a, p - 1, p)
        if residue != 1:
            failures.append((a, residue))
    
    return len(failures) == 0, failures

def verify_euler_theorem(n, sample_size=100):
    """
    Verify Euler's Theorem for modulus n across random bases a coprime to n.
    Tests that a^φ(n) ≡ 1 (mod n).
    """
    phi_n = totient(n)
    failures = []
    
    for _ in range(sample_size):
        a = random.randint(2, n - 1)
        if gcd(a, n) != 1:
            continue  # Skip if not coprime
        
        residue = pow(a, phi_n, n)
        if residue != 1:
            failures.append((a, residue))
    
    return len(failures) == 0, failures

# Verification suite
print("\nFermat's Little Theorem Verification:")
print("=" * 80)
primes_to_test = [5, 7, 13, 97, 1009, 10007]
for p in primes_to_test:
    success, failures = verify_fermat_little_theorem(p, sample_size=200)
    status = "✓ PASS" if success else f"✗ FAIL ({len(failures)} counterexamples)"
    print(f"p = {p:6}: a^(p-1) ≡ 1 (mod p) for all tested a... {status}")

print("\nEuler's Theorem Verification:")
print("=" * 80)
moduli_to_test = [
    (15, factorint(15)),
    (28, factorint(28)),
    (100, factorint(100)),
    (1001, factorint(1001)),
    (2048, factorint(2048))
]
for n, factorization in moduli_to_test:
    phi_n = totient(n)
    success, failures = verify_euler_theorem(n, sample_size=200)
    status = "✓ PASS" if success else f"✗ FAIL ({len(failures)} counterexamples)"
    print(f"n = {n:6} = {factorization}, φ(n) = {phi_n:6}: a^φ(n) ≡ 1 (mod n)... {status}")
```

This computational verification samples the space of bases systematically, confirming that no counterexamples exist within the tested range. The modulus $n = 2048 = 2^{11}$ demonstrates Euler's theorem on a pure prime-power, where $\phi(2^{11}) = 2^{10} = 1024$. For $n = 1001 = 7 \times 11 \times 13$, the totient function applies multiplicatively: $\phi(1001) = \phi(7)\phi(11)\phi(13) = 6 \times 10 \times 12 = 720$.

**Wilson's Theorem and Factorial Congruences**

Wilson's Theorem provides a primality characterization through factorials: an integer $p > 1$ is prime if and only if $(p-1)! \equiv -1 \pmod{p}$. This theorem offers no practical primality test due to the computational expense of factorial computation, but it provides deep structural insight into the multiplicative group modulo a prime. Verify Wilson's Theorem by computing $(p-1)! \bmod p$ for both primes and composites, observing the sharp distinction between the two cases.

```python
from sympy import factorial, Mod
from math import factorial as math_factorial

def verify_wilson_theorem(n):
    """
    Verify Wilson's Theorem: (n-1)! ≡ -1 (mod n) if and only if n is prime.
    Returns (is_prime, factorial_residue).
    """
    if n <= 1:
        return (False, None)
    
    # Compute (n-1)! mod n
    fact_residue = 1
    for k in range(2, n):
        fact_residue = (fact_residue * k) % n
    
    expected = (n - 1) % n  # This is -1 mod n
    is_prime_predicted = (fact_residue == expected)
    
    return (is_prime_predicted, fact_residue)

print("\nWilson's Theorem Verification:")
print("=" * 80)
print(f"{'n':>4} {'Prime?':>8} {'(n-1)! mod n':>15} {'Expected':>10} {'Status':>8}")
print("-" * 80)

test_values = list(range(2, 20)) + [23, 24, 25, 29, 30, 31, 32, 97, 100]
for n in test_values:
    is_prime_actual = isprime(n)
    is_prime_wilson, fact_residue = verify_wilson_theorem(n)
    expected = (n - 1) if is_prime_actual else "varies"
    
    status = "✓" if is_prime_wilson == is_prime_actual else "✗"
    prime_str = "PRIME" if is_prime_actual else "composite"
    
    print(f"{n:4} {prime_str:>8} {fact_residue:15} {str(expected):>10} {status:>8}")
```

Observe the computational output carefully. For primes like $p = 7$, we compute $6! = 720 \equiv 6 \equiv -1 \pmod{7}$. For composite $n = 6$, we have $5! = 120 \equiv 0 \pmod{6}$, failing Wilson's condition spectacularly. The composite case often yields zero residue when $n$ contains repeated prime factors or when $(n-1)!$ contains all prime factors of $n$ with sufficient multiplicity.

**Formal Proof in Lean: Bézout's Identity**

Transitioning from computational verification to formal proof, construct a mechanized proof of Bézout's identity in Lean 4 using Mathlib's number theory library. This exercise demonstrates how computational intuition guides formal reasoning while the proof assistant enforces absolute rigor.

```lean
import Mathlib.Data.Nat.GCD.Basic
import Mathlib.Algebra.EuclideanDomain.Basic

theorem bezout_identity (a b : ℤ) : ∃ x y : ℤ, a * x + b * y = Int.gcd a b := by
  -- Mathlib provides gcdA and gcdB such that a * gcdA a b + b * gcdB a b = gcd a b
  use Int.gcdA a b, Int.gcdB a b
  exact Int.gcd_eq_gcd_ab a b

-- Verification for concrete instances
example : ∃ x y : ℤ, 252 * x + 105 * y = Int.gcd 252 105 := by
  use Int.gcdA 252 105, Int.gcdB 252 105
  exact Int.gcd_eq_gcd_ab 252 105

#eval Int.gcd 252 105        -- Output: 21
#eval Int.gcdA 252 105       -- Output: x coefficient
#eval Int.gcdB 252 105       -- Output: y coefficient
#eval 252 * (Int.gcdA 252 105) + 105 * (Int.gcdB 252 105)  -- Verify identity
```

In this Lean formalization, the `Int.gcd_eq_gcd_ab` theorem from Mathlib encapsulates the extended Euclidean algorithm's correctness, asserting that the functions `gcdA` and `gcdB` yield the Bézout coefficients. The `norm_num` tactic handles numerical simplification, while the proof structure remains constructive: we explicitly provide the witness terms rather than merely asserting existence.

## Exercise 2: Boundary Value Stress Testing & Singularities

Number-theoretic functions exhibit rich structural behavior at boundary values, singularities, and limiting cases. The Möbius function $\mu(n)$ and the Liouville function $\lambda(n)$ demonstrate multiplicativity with exceptional cases at prime powers. The divisor function $\sigma_k(n)$ and Euler's totient $\phi(n)$ reveal asymptotic growth patterns and sharp fluctuations. Primality testing algorithms encounter pseudoprimes—composite numbers that satisfy prime-like congruences—exposing the probabilistic nature of certain primality certificates. This exercise battery stress-tests these structures at computational boundaries, exploring edge cases where naive implementations fail and formal verification becomes essential.

**Möbius Inversion and Multiplicative Function Identities**

The Möbius function $\mu(n)$ is defined as $\mu(1) = 1$, $\mu(n) = 0$ if $n$ has a squared prime factor, and $\mu(n) = (-1)^k$ if $n$ is a product of $k$ distinct primes. The Möbius inversion formula provides a fundamental transformation between arithmetic functions: if $g(n) = \sum_{d \mid n} f(d)$, then $f(n) = \sum_{d \mid n} \mu(d) g(n/d)$. Verify this inversion formula computationally for various arithmetic functions, testing the boundary case where $f$ or $g$ vanish, and examining the behavior at prime powers.

```python
from sympy import mobius, divisors, primefactors, divisor_count, divisor_sigma, totient

def mobius_inversion_forward(f, n):
    """
    Compute g(n) = Σ_{d|n} f(d) from arithmetic function f.
    """
    return sum(f(d) for d in divisors(n, generator=False))

def mobius_inversion_backward(g, n):
    """
    Recover f(n) = Σ_{d|n} μ(d) g(n/d) from g using Möbius inversion.
    """
    return sum(mobius(d) * g(n // d) for d in divisors(n, generator=False))

# Test arithmetic functions
def constant_one(n):
    return 1

def identity_function(n):
    return n

def totient_function(n):
    return totient(n)

print("Möbius Inversion Verification:")
print("=" * 80)

# Test 1: f(n) = 1, g(n) = d(n) = number of divisors
print("\nTest 1: f(n) = 1 → g(n) = d(n) (divisor count)")
test_range = range(1, 21)
for n in test_range:
    g_computed = mobius_inversion_forward(constant_one, n)
    g_expected = divisor_count(n)
    f_recovered = mobius_inversion_backward(lambda m: divisor_count(m), n)
    
    status_g = "✓" if g_computed == g_expected else "✗"
    status_f = "✓" if f_recovered == constant_one(n) else "✗"
    
    print(f"n={n:3}: g(n)={g_computed:3} (expected {g_expected:3}) {status_g}, "
          f"f recovered = {f_recovered:3} (expected 1) {status_f}")

# Test 2: f(n) = n, g(n) = σ_1(n) = sum of divisors
print("\nTest 2: f(n) = n → g(n) = σ₁(n) (sum of divisors)")
for n in test_range:
    g_computed = mobius_inversion_forward(identity_function, n)
    g_expected = divisor_sigma(n, 1)
    f_recovered = mobius_inversion_backward(lambda m: divisor_sigma(m, 1), n)
    
    status_g = "✓" if g_computed == g_expected else "✗"
    status_f = "✓" if f_recovered == identity_function(n) else "✗"
    
    print(f"n={n:3}: g(n)={g_computed:4} (expected {g_expected:4}) {status_g}, "
          f"f recovered = {f_recovered:4} (expected {n:3}) {status_f}")

# Test 3: f(n) = φ(n), g(n) = n
print("\nTest 3: f(n) = φ(n) → g(n) = n (identity)")
for n in test_range:
    g_computed = mobius_inversion_forward(totient_function, n)
    g_expected = n
    f_recovered = mobius_inversion_backward(identity_function, n)
    
    status_g = "✓" if g_computed == g_expected else "✗"
    status_f = "✓" if abs(f_recovered - totient(n)) < 1e-10 else "✗"
    
    print(f"n={n:3}: g(n)={g_computed:4} (expected {g_expected:4}) {status_g}, "
          f"φ(n) recovered = {f_recovered:4} (expected {totient(n):4}) {status_f}")
```

This verification suite confirms that Möbius inversion correctly transforms between arithmetic function pairs. The identity $\sum_{d \mid n} \phi(d) = n$ emerges naturally from the inversion formula, reflecting the fact that partitioning $\{1, 2, \ldots, n\}$ by $\gcd(k, n)$ yields $\phi(d)$ elements with $\gcd(k, n) = d$ for each divisor $d$ of $n$. The computational boundary case $n = 1$ requires careful handling: $\mu(1) = 1$, and the summation collapses to a single term.

**Pseudoprimes and the Limits of Fermat's Test**

While Fermat's Little Theorem provides a necessary condition for primality, it is not sufficient: composite numbers satisfying $a^{n-1} \equiv 1 \pmod{n}$ for certain bases $a$ are called pseudoprimes to base $a$. Carmichael numbers are composite integers that are pseudoprimes to all bases coprime to them, fooling the Fermat test completely. Identify Carmichael numbers computationally and verify their pseudoprime properties, exposing the limitations of Fermat-based primality testing.

```python
def is_fermat_pseudoprime(n, base):
    """
    Check if n is a pseudoprime to the given base:
    n is composite and base^(n-1) ≡ 1 (mod n).
    """
    if isprime(n):
        return False  # By definition, pseudoprimes are composite
    if gcd(base, n) != 1:
        return False  # Base must be coprime to n
    return pow(base, n - 1, n) == 1

def is_carmichael_number(n):
    """
    Check if n is a Carmichael number: composite and pseudoprime to all bases coprime to n.
    Equivalently, by Korselt's criterion: n is squarefree and for all primes p|n, (p-1)|(n-1).
    """
    if isprime(n) or n < 2:
        return False
    
    factorization = factorint(n)
    
    # Check squarefree
    if any(exp > 1 for exp in factorization.values()):
        return False
    
    # Check Korselt's criterion
    for p in factorization.keys():
        if (n - 1) % (p - 1) != 0:
            return False
    
    return True

# Find first Carmichael numbers
print("\nCarmichael Number Detection:")
print("=" * 80)
carmichael_numbers = []
for n in range(2, 100000):
    if is_carmichael_number(n):
        carmichael_numbers.append(n)
        if len(carmichael_numbers) >= 7:
            break

for cn in carmichael_numbers:
    factors = factorint(cn)
    print(f"\nCarmichael number: {cn} = {factors}")
    
    # Verify it's pseudoprime to several bases
    test_bases = [2, 3, 5, 7, 11, 13]
    for base in test_bases:
        if gcd(base, cn) == 1:
            is_pseudo = is_fermat_pseudoprime(cn, base)
            residue = pow(base, cn - 1, cn)
            print(f"  Base {base:2}: {base}^{cn-1} ≡ {residue} (mod {cn}), pseudoprime: {is_pseudo}")

# Verify Korselt's criterion explicitly for 561 = 3 × 11 × 17
print("\n" + "=" * 80)
print("Detailed Korselt's Criterion Verification for 561:")
n = 561
factors = [3, 11, 17]
print(f"n = {n} = {' × '.join(map(str, factors))}")
print(f"n - 1 = {n - 1} = {factorint(n - 1)}")
for p in factors:
    quotient, remainder = divmod(n - 1, p - 1)
    print(f"  (n-1) / (p-1) = {n-1} / {p-1} = {quotient} remainder {remainder} {'✓' if remainder == 0 else '✗'}")
```

The smallest Carmichael number is $561 = 3 \times 11 \times 17$, which satisfies Korselt's criterion: $560 = n - 1$ is divisible by $p - 1 = 2$, $p - 1 = 10$, and $p - 1 = 16$ for each prime factor. This verification exposes the computational boundary where Fermat's test fails: a composite number can satisfy the Fermat congruence for all bases, necessitating stronger primality tests like Miller-Rabin or deterministic methods based on the generalized Riemann hypothesis.

**Asymptotic Behavior of Arithmetic Functions**

The asymptotic growth of arithmetic functions reveals deep connections between number theory and analysis. The average order of the divisor function $\tau(n)$ is $\log n$, while the sum-of-divisors function $\sigma(n)$ grows like $\frac{\pi^2}{6} n \log \log n$. Euler's totient function satisfies $\sum_{n \leq x} \phi(n) \sim \frac{3}{\pi^2} x^2$. Compute these functions over large ranges and compare empirical growth to theoretical predictions, stress-testing the asymptotic estimates.

```python
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
from sympy import divisor_count, totient, divisor_sigma, factorint

def compute_asymptotic_statistics(max_n):
    """
    Compute arithmetic function values and asymptotic comparisons.
    """
    n_values = np.arange(1, max_n + 1)
    
    # Compute functions
    tau_values = np.array([divisor_count(n) for n in n_values])
    phi_values = np.array([totient(n) for n in n_values])
    sigma_values = np.array([divisor_sigma(n, 1) for n in n_values])
    
    # Asymptotic predictions
    log_n = np.log(n_values)
    log_log_n = np.log(np.maximum(log_n, 1))  # Avoid log(log(1))
    
    tau_asymptotic = log_n
    sigma_asymptotic = (np.pi**2 / 6) * n_values * log_log_n
    
    # Cumulative totient
    phi_cumulative = np.cumsum(phi_values)
    phi_cumulative_asymptotic = (3 / np.pi**2) * n_values**2
    
    return {
        'n': n_values,
        'tau': tau_values,
        'tau_asymptotic': tau_asymptotic,
        'phi_cumulative': phi_cumulative,
        'phi_cumulative_asymptotic': phi_cumulative_asymptotic,
        'sigma': sigma_values,
        'sigma_asymptotic': sigma_asymptotic
    }

print("\nAsymptotic Behavior Analysis:")
print("=" * 80)

# Compute for moderate range
max_n = 1000
stats = compute_asymptotic_statistics(max_n)

# Sample points for comparison
sample_points = [10, 50, 100, 200, 500, 1000]
print(f"\n{'n':>6} {'τ(n)':>8} {'log(n)':>10} {'Ratio':>8} | "
      f"{'Σφ(k)':>12} {'3n²/π²':>12} {'Ratio':>8}")
print("-" * 80)

for n_idx in [i - 1 for i in sample_points]:
    n = stats['n'][n_idx]
    tau_actual = np.mean(stats['tau'][:n_idx+1])  # Average τ up to n
    tau_pred = np.mean(stats['tau_asymptotic'][:n_idx+1])
    
    phi_cum_actual = stats['phi_cumulative'][n_idx]
    phi_cum_pred = stats['phi_cumulative_asymptotic'][n_idx]
    
    tau_ratio = tau_actual / tau_pred if tau_pred > 0 else 0
    phi_ratio = phi_cum_actual / phi_cum_pred if phi_cum_pred > 0 else 0
    
    print(f"{n:6} {tau_actual:8.3f} {tau_pred:10.3f} {tau_ratio:8.4f} | "
          f"{phi_cum_actual:12.0f} {phi_cum_pred:12.0f} {phi_ratio:8.4f}")

# Test highly composite numbers (numbers with many divisors)
print("\nHighly Composite Number Analysis:")
print("=" * 80)
highly_composite = []
record_divisor_count = 0
for n in range(1, 10001):
    tau_n = divisor_count(n)
    if tau_n > record_divisor_count:
        highly_composite.append((n, tau_n, factorint(n)))
        record_divisor_count = tau_n

print(f"{'n':>6} {'τ(n)':>6} {'Factorization':>40}")
print("-" * 60)
for n, tau_n, factors in highly_composite[:15]:
    factor_str = ' × '.join([f"{p}^{e}" if e > 1 else str(p) for p, e in factors.items()])
    print(f"{n:6} {tau_n:6} {factor_str:>40}")
```

This analysis reveals that highly composite numbers—those with more divisors than any smaller number—follow a predictable structure: they are products of small primes with decreasing exponents, such as $5040 = 2^4 \times 3^2 \times 5 \times 7$, which has $\tau(5040) = 60$ divisors. The asymptotic ratio between empirical totient sums and the prediction $\frac{3}{\pi^2} n^2$ approaches unity as $n$ grows, validating the probabilistic heuristic that a random integer near $n$ is coprime to a fixed modulus with probability approximately $\frac{6}{\pi^2} \approx 0.608$.

## Exercise 3: Algorithmic Implementation of Formal Structures

The transition from theorem to algorithm demands careful attention to computational complexity, correctness invariants, and edge-case handling. This laboratory section implements core number-theoretic algorithms with full rigor: the Miller-Rabin primality test with explicit error-bound analysis, the Tonelli-Shanks algorithm for modular square roots, the continued fraction expansion of quadratic irrationals with periodic structure verification, and the Lenstra elliptic curve factorization method. Each implementation includes formal specification, invariant assertions, and complexity analysis grounded in number-theoretic structure.

**Miller-Rabin Primality Test with Probabilistic Guarantees**

The Miller-Rabin test improves upon Fermat's test by examining the structure of $n - 1 = 2^s d$ with $d$ odd, and testing whether $a^d \equiv 1 \pmod{n}$ or $a^{2^r d} \equiv -1 \pmod{n}$ for some $0 \leq r < s$. A composite number passing this test for a random base is called a strong pseudoprime. The error probability for a single iteration is at most $1/4$, yielding exponentially decreasing failure probability with repeated trials.

```python
import random

def miller_rabin_decomposition(n):
    """
    Write n - 1 = 2^s * d with d odd.
    Returns (s, d).
    """
    assert n > 2 and n % 2 == 1, "n must be odd and greater than 2"
    
    s = 0
    d = n - 1
    while d % 2 == 0:
        s += 1
        d //= 2
    
    assert 2**s * d == n - 1, "Decomposition invariant failed"
    assert d % 2 == 1, "d must be odd"
    
    return s, d

def miller_rabin_witness(n, a):
    """
    Test if a is a Miller-Rabin witness for the compositeness of n.
    Returns True if a proves n is composite, False if n might be prime.
    """
    if n == 2:
        return False
    if n % 2 == 0 or n < 2:
        return True
    
    s, d = miller_rabin_decomposition(n)
    
    # Compute a^d mod n
    x = pow(a, d, n)
    
    if x == 1 or x == n - 1:
        return False  # n might be prime
    
    # Square x repeatedly s-1 times
    for _ in range(s - 1):
        x = pow(x, 2, n)
        if x == n - 1:
            return False  # n might be prime
    
    return True  # a is a witness: n is definitely composite

def miller_rabin_test(n, k=20):
    """
    Miller-Rabin primality test with k iterations.
    Returns (probably_prime, witnesses_found).
    Error probability ≤ 4^(-k).
    """
    if n == 2 or n == 3:
        return True, []
    if n < 2 or n % 2 == 0:
        return False, []
    
    # Test deterministic witnesses for small n
    if n < 2047:
        witnesses_to_test = [2]
    elif n < 1373653:
        witnesses_to_test = [2, 3]
    elif n < 9080191:
        witnesses_to_test = [31, 73]
    elif n < 25326001:
        witnesses_to_test = [2, 3, 5]
    else:
        # Use random witnesses for large n
        witnesses_to_test = [random.randint(2, n - 2) for _ in range(k)]
    
    witnesses = []
    for a in witnesses_to_test:
        if miller_rabin_witness(n, a):
            witnesses.append(a)
            return False, witnesses  # Definitely composite
    
    return True, witnesses  # Probably prime

# Verification suite
print("\nMiller-Rabin Primality Test Verification:")
print("=" * 80)

# Test known primes
large_primes = [1009, 1013, 1019, 10007, 100003, 1000003, 15485863]
print("\nTesting known primes:")
for p in large_primes:
    is_prime, witnesses = miller_rabin_test(p, k=20)
    sympy_check = isprime(p)
    status = "✓" if is_prime and sympy_check else "✗"
    print(f"n = {p:10}: Miller-Rabin: {is_prime:5}, SymPy: {sympy_check:5} {status}")

# Test known composites including Carmichael numbers
composites = [561, 1105, 1729, 2465, 2821, 6601, 8911]
print("\nTesting Carmichael numbers and composites:")
for n in composites:
    is_prime, witnesses = miller_rabin_test(n, k=20)
    sympy_check = isprime(n)
    status = "✓" if not is_prime and not sympy_check else "✗"
    witness_str = f"witnesses: {witnesses[:3]}" if witnesses else "no witnesses (error!)"
    print(f"n = {n:6}: Miller-Rabin: {is_prime:5}, SymPy: {sympy_check:5} {status}, {witness_str}")

# Test error probability empirically
print("\nEmpirical Error Probability Test:")
print("=" * 80)
known_composite = 561  # Carmichael number
iterations_range = [1, 2, 5, 10, 20]
trials_per_k = 1000

for k in iterations_range:
    false_prime_count = 0
    for _ in range(trials_per_k):
        is_prime, _ = miller_rabin_test(known_composite, k=k)
        if is_prime:
            false_prime_count += 1
    
    empirical_error = false_prime_count / trials_per_k
    theoretical_bound = 4**(-k)
    
    print(f"k = {k:2} iterations: empirical error = {empirical_error:.6f}, "
          f"theoretical bound = {theoretical_bound:.6f}")
```

The Miller-Rabin implementation demonstrates deterministic witness sets for small ranges (based on work by Pomerance, Selfridge, and Wagstaff) and transitions to probabilistic testing for large inputs. The Carmichael number $561$ fools Fermat's test for all bases but is quickly exposed by Miller-Rabin: base $a = 2$ serves as a witness since $2^{35} \equiv 263 \not\equiv \pm 1 \pmod{561}$.

**Tonelli-Shanks Algorithm for Modular Square Roots**

Given a quadratic residue $a$ modulo an odd prime $p$, the Tonelli-Shanks algorithm computes $x$ such that $x^2 \equiv a \pmod{p}$. The algorithm exploits the structure of $p - 1 = 2^s q$ with $q$ odd, using a quadratic non-residue to construct successive approximations through multiplicative corrections in the subgroup of order $2^s$.

```python
def tonelli_shanks(a, p):
    """
    Compute a square root of a modulo prime p using the Tonelli-Shanks algorithm.
    Returns r such that r^2 ≡ a (mod p), or None if a is not a quadratic residue.
    Precondition: p is an odd prime.
    """
    assert isprime(p) and p > 2, "p must be an odd prime"
    
    a = a % p
    
    # Check if a is a quadratic residue using Euler's criterion
    if pow(a, (p - 1) // 2, p) != 1:
        return None  # Not a quadratic residue
    
    # Special case: p ≡ 3 (mod 4)
    if p % 4 == 3:
        r = pow(a, (p + 1) // 4, p)
        assert pow(r, 2, p) == a % p
        return r
    
    # General case: write p - 1 = 2^s * q with q odd
    s = 0
    q = p - 1
    while q % 2 == 0:
        s += 1
        q //= 2
    
    # Find a quadratic non-residue z
    z = 2
    while pow(z, (p - 1) // 2, p) != p - 1:
        z += 1
    
    # Initialize variables
    m = s
    c = pow(z, q, p)
    t = pow(a, q, p)
    r = pow(a, (q + 1) // 2, p)
    
    while t != 1:
        # Find the least i such that t^(2^i) ≡ 1 (mod p)
        i = 1
        temp = pow(t, 2, p)
        while temp != 1:
            temp = pow(temp, 2, p)
            i += 1
        
        # Update values
        b = pow(c, 1 << (m - i - 1), p)  # b = c^(2^(m-i-1))
        m = i
        c = pow(b, 2, p)
        t = (t * c) % p
        r = (r * b) % p
    
    assert pow(r, 2, p) == a % p, "Algorithm invariant violated"
    return r

# Verification suite
print("\nTonelli-Shanks Square Root Algorithm:")
print("=" * 80)

test_cases = [
    (10, 13),   # 10 is a QR mod 13
    (5, 41),    # 5 is a QR mod 41
    (2, 7),     # 2 is a QR mod 7
    (2, 11),    # 2 is NOT a QR mod 11
    (85, 101),  # 85 is a QR mod 101
    (56, 101),  # 56 is a QR mod 101
]

print(f"{'a':>4} {'p':>5} {'x':>8} {'x² mod p':>10} {'Status':>10}")
print("-" * 50)

for a, p in test_cases:
    x = tonelli_shanks(a, p)
    
    if x is None:
        legendre = pow(a, (p - 1) // 2, p)
        status = "✓ Non-QR" if legendre == p - 1 else "✗ Error"
        print(f"{a:4} {p:5} {'None':>8} {'N/A':>10} {status:>10}")
    else:
        verification = pow(x, 2, p)
        status = "✓" if verification == a % p else "✗"
        print(f"{a:4} {p:5} {x:8} {verification:10} {status:>10}")

# Test against SymPy implementation
print("\nComparison with SymPy sqrt_mod:")
print("=" * 80)
from sympy.ntheory.residue_ntheory import sqrt_mod

large_test_cases = [
    (123456, 1000003),
    (7890, 100003),
    (42, 15485863),
]

for a, p in large_test_cases:
    x_tonelli = tonelli_shanks(a, p)
    x_sympy = sqrt_mod(a, p)
    
    if x_tonelli is None and x_sympy is None:
        print(f"a = {a:8}, p = {p:8}: Both report non-QR ✓")
    elif x_tonelli is None or x_sympy is None:
        print(f"a = {a:8}, p = {p:8}: Mismatch in QR status ✗")
    else:
        # Both solutions are valid (either x or p-x is a square root)
        match = (x_tonelli == x_sympy) or (x_tonelli == p - x_sympy)
        verification_tonelli = pow(x_tonelli, 2, p) == a % p
        verification_sympy = pow(x_sympy, 2, p) == a % p
        
        status = "✓" if match and verification_tonelli and verification_sympy else "✗"
        print(f"a = {a:8}, p = {p:8}: Tonelli = {x_tonelli:10}, SymPy = {x_sympy:10} {status}")
```

The Tonelli-Shanks algorithm runs in expected time $O((\log p)^2 \cdot s)$, where $s$ is the 2-adic valuation of $p - 1$. For primes $p \equiv 3 \pmod{4}$, the algorithm reduces to a single modular exponentiation, as $(a^{(p+1)/4})^2 \equiv a^{(p+1)/2} \equiv a \cdot a^{(p-1)/2} \equiv a \pmod{p}$ by Euler's criterion.

**Continued Fractions and Quadratic Irrational Periodicity**

Every quadratic irrational $\alpha = \frac{P + \sqrt{D}}{Q}$ with $D$ nonsquare admits a periodic continued fraction expansion. The period begins when a convergent $(P_i, Q_i)$ repeats, revealing algebraic structure through the expansion's palindromic partial quotients. Implement continued fraction expansion with period detection, verifying Lagrange's theorem that periodicity characterizes quadratic irrationals.

```python
from sympy import sqrt, continued_fraction_periodic, nsimplify

def continued_fraction_quadratic(P, D, Q, max_iterations=1000):
    """
    Compute continued fraction expansion of (P + √D) / Q.
    Returns (partial_quotients, period_start, period_length).
    """
    assert D > 0 and int(sqrt(D))**2 != D, "D must be a positive non-square"
    
    partial_quotients = []
    seen_states = {}
    
    P_i, Q_i = P, Q
    iteration = 0
    
    while iteration < max_iterations:
        # Compute partial quotient a_i = floor((P_i + √D) / Q_i)
        sqrt_D_approx = float(sqrt(D))
        a_i = int((P_i + sqrt_D_approx) / Q_i)
        partial_quotients.append(a_i)
        
        # Check for period
        state = (P_i, Q_i)
        if state in seen_states:
            period_start = seen_states[state]
            period_length = iteration - period_start
            return partial_quotients, period_start, period_length
        
        seen_states[state] = iteration
        
        # Update P and Q
        P_next = a_i * Q_i - P_i
        Q_next = (D - P_next**2) // Q_i
        
        P_i, Q_i = P_next, Q_next
        iteration += 1
    
    return partial_quotients, -1, -1  # No period found

# Verify continued fraction expansion
print("\nContinued Fraction Expansion of Quadratic Irrationals:")
print("=" * 80)

quadratic_irrationals = [
    (0, 2, 1, "√2"),
    (0, 3, 1, "√3"),
    (0, 5, 1, "√5"),
    (1, 5, 2, "(1 + √5)/2 (golden ratio)"),
    (0, 7, 1, "√7"),
    (0, 13, 1, "√13"),
]

for P, D, Q, description in quadratic_irrationals:
    cf, period_start, period_length = continued_fraction_quadratic(P, D, Q, max_iterations=100)
    
    # Extract the periodic part
    if period_length > 0:
        pre_period = cf[:period_start]
        period = cf[period_start:period_start + period_length]
        
        print(f"\n{description}:")
        print(f"  Expansion: [{', '.join(map(str, pre_period[:5]))}; "
              f"periodic: ({', '.join(map(str, period))})]")
        print(f"  Period starts at index {period_start}, length {period_length}")
        
        # Verify using SymPy
        if P == 0 and Q == 1:
            sympy_cf = continued_fraction_periodic(0, 1, sqrt(D))
            sympy_period = list(sympy_cf[1])  # Skip the initial part
            
            match = tuple(period) == tuple(sympy_period)
            status = "✓" if match else "✗"
            print(f"  SymPy verification: {status}")

# Compute convergents and verify approximation quality
print("\nConvergent Approximations to √2:")
print("=" * 80)

def compute_convergents(partial_quotients, num_convergents):
    """
    Compute the first num_convergents convergents p_n/q_n from partial quotients.
    """
    if not partial_quotients:
        return []
    
    convergents = []
    p_prev, p_curr = 0, 1
    q_prev, q_curr = 1, 0
    
    for i, a in enumerate(partial_quotients[:num_convergents]):
        p_next = a * p_curr + p_prev
        q_next = a * q_curr + q_prev
        
        convergents.append((p_next, q_next))
        
        p_prev, p_curr = p_curr, p_next
        q_prev, q_curr = q_curr, q_next
    
    return convergents

cf_sqrt2, _, _ = continued_fraction_quadratic(0, 2, 1, max_iterations=50)
convergents_sqrt2 = compute_convergents(cf_sqrt2, 10)

sqrt_2_value = float(sqrt(2))
print(f"{'n':>3} {'p_n':>8} {'q_n':>8} {'p_n/q_n':>18} {'|p_n/q_n - √2|':>20} {'p_n² - 2q_n²':>15}")
print("-" * 90)

for i, (p, q) in enumerate(convergents_sqrt2):
    ratio = p / q
    error = abs(ratio - sqrt_2_value)
    pell_value = p**2 - 2 * q**2
    
    print(f"{i:3} {p:8} {q:8} {ratio:18.15f} {error:20.15e} {pell_value:15}")
```

The continued fraction expansion of $\sqrt{2} = [1; \overline{2}]$ has period one, yielding convergents that solve the Pell equation $p^2 - 2q^2 = \pm 1$ alternately. The golden ratio $\phi = \frac{1 + \sqrt{5}}{2} = [1; \overline{1}]$ exhibits the slowest convergence among all real numbers, a consequence of its continued fraction containing only ones, achieving the worst-case approximation quality in Hurwitz's theorem.

## Formal Axioms Cheat Sheet & Verification Reference

This reference codifies the foundational axioms, theorems, and algorithmic invariants verified throughout these laboratories, providing both mathematical statements and their computational signatures for rapid verification lookup.

**Fundamental Theorems**

**Division Algorithm:** For integers $a$ and $b$ with $b > 0$, there exist unique integers $q$ and $r$ such that $a = bq + r$ with $0 \leq r < b$. Computational verification: `divmod(a, b)` returns `(q, r)` satisfying the constraints.

**Bézout's Identity:** For integers $a$ and $b$, there exist integers $x$ and $y$ such that $\gcd(a, b) = ax + by$. The extended Euclidean algorithm computes these coefficients constructively. Verification: `sympy.gcdex(a, b)` returns `(g, x, y)` with `a*x + b*y == g`.

**Fundamental Theorem of Arithmetic:** Every integer $n > 1$ admits a unique prime factorization $n = p_1^{e_1} p_2^{e_2} \cdots p_k^{e_k}$ with primes $p_1 < p_2 < \cdots < p_k$ and positive exponents $e_i$. Verification: `sympy.factorint(n)` returns the factorization dictionary.

**Fermat's Little Theorem:** If $p$ is prime and $\gcd(a, p) = 1$, then $a^{p-1} \equiv 1 \pmod{p}$. Verification: `pow(a, p-1, p) == 1` for all coprime bases $a$.

**Euler's Theorem:** For integers $a$ and $n$ with $\gcd(a, n) = 1$, we have $a^{\phi(n)} \equiv 1 \pmod{n}$, where $\phi(n) = |\{k : 1 \leq k \leq n, \gcd(k, n) = 1\}|$. Verification: `pow(a, sympy.totient(n), n) == 1`.

**Chinese Remainder Theorem:** Given pairwise coprime moduli $m_1, m_2, \ldots, m_k$ and arbitrary residues $a_1, a_2, \ldots, a_k$, there exists a unique $x \pmod{m_1 m_2 \cdots m_k}$ satisfying $x \equiv a_i \pmod{m_i}$ for all $i$. Verification: `sympy.ntheory.modular.crt([m_1, m_2, ...], [a_1, a_2, ...])` computes $x$.

**Wilson's Theorem:** An integer $p > 1$ is prime if and only if $(p-1)! \equiv -1 \pmod{p}$. Verification: compute `math.factorial(p-1) % p` and compare to `p-1`.

**Quadratic Reciprocity:** For distinct odd primes $p$ and $q$, the Legendre symbols satisfy $\left(\frac{p}{q}\right) \left(\frac{q}{p}\right) = (-1)^{(p-1)(q-1)/4}$. Verification: `sympy.legendre_symbol(p, q) * sympy.legendre_symbol(q, p) == (-1)**((p-1)*(q-1)//4)`.

**Multiplicative Function Identities**

**Möbius Inversion:** If $g(n) = \sum_{d \mid n} f(d)$, then $f(n) = \sum_{d \mid n} \mu(d) g(n/d)$. Verification demonstrated through the identity $\sum_{d \mid n} \phi(d) = n$, where $\phi$ is Euler's totient function.

**Divisor Sum Formula:** For $n = p_1^{e_1} \cdots p_k^{e_k}$, the sum of divisors is $\sigma_k(n) = \prod_{i=1}^k \frac{p_i^{(e_i+1)k} - 1}{p_i^k - 1}$. Verification: `sympy.divisor_sigma(n, k)` implements this formula.

**Totient Product Formula:** For $n = p_1^{e_1} \cdots p_k^{e_k}$, Euler's totient is $\phi(n) = n \prod_{p \mid n} \left(1 - \frac{1}{p}\right) = \prod_{i=1}^k p_i^{e_i-1}(p_i - 1)$. Verification: `sympy.totient(n)`.

**Primality Testing Invariants**

**Korselt's Criterion (Carmichael Numbers):** A composite integer $n$ is a Carmichael number if and only if $n$ is squarefree and for every prime divisor $p$ of $n$, we have $(p-1) \mid (n-1)$. Implementation: check `all((n-1) % (p-1) == 0 for p in sympy.primefactors(n))`.

**Miller-Rabin Witness Criterion:** For odd $n = 2^s d + 1$ with $d$ odd, an integer $a$ with $1 < a < n$ is a Miller-Rabin witness for the compositeness of $n$ if $a^d \not\equiv 1 \pmod{n}$ and $a^{2^r d} \not\equiv -1 \pmod{n}$ for all $0 \leq r < s$. Implementation handles deterministic witness sets for small $n$ and random witnesses for probabilistic testing.

**Computational Complexity Bounds**

**Extended Euclidean Algorithm:** $O(\log \min(a, b))$ divisions, each requiring $O((\log \max(a, b))^2)$ bit operations. Total: $O((\log \max(a, b))^3)$ bit complexity.

**Modular Exponentiation (Binary Method):** Computing $a^e \bmod n$ requires $O(\log e)$ squarings and multiplications, each taking $O((\log n)^2)$ bit operations. Total: $O((\log e)(\log n)^2)$.

**Miller-Rabin Test:** Each iteration requires $O(\log n)$ modular squarings, yielding $O((\log n)^3)$ bit complexity per witness. With $k$ witnesses, total complexity is $O(k (\log n)^3)$ with error probability at most $4^{-k}$.

**Tonelli-Shanks Algorithm:** Expected $O((\log p)^2 \cdot s)$ complexity, where $s$ is the 2-adic valuation of $p - 1$. Worst case when $s$ is large (e.g., $p = 2^{1000} + 1$).

**SymPy Quick Reference**

```python
import sympy as sp
from sympy import gcd, gcdex, lcm, isprime, factorint, totient, divisors
from sympy import mobius, divisor_count, divisor_sigma, primefactors
from sympy import legendre_symbol, jacobi_symbol, sqrt_mod
from sympy.ntheory.modular import crt, solve_congruence
from sympy.ntheory.continued_fraction import continued_fraction_periodic

# Core number-theoretic functions
g = sp.gcd(48, 18)                    # 6
g, x, y = sp.gcdex(48, 18)            # (6, -1, 3) with 48*(-1) + 18*3 = 6
factors = sp.factorint(360)           # {2: 3, 3: 2, 5: 1}
is_prime = sp.isprime(97)             # True
phi = sp.totient(100)                 # 40
divs = sp.divisors(12)                # [1, 2, 3, 4, 6, 12]
sigma = sp.divisor_sigma(12, 1)       # 28 (sum of divisors)
mu = sp.mobius(30)                    # -1
leg = sp.legendre_symbol(10, 13)      # 1 (10 is a QR mod 13)
x = sp.sqrt_mod(10, 13)               # 6 (since 6² ≡ 10 mod 13)
solution = sp.ntheory.modular.crt([3, 5, 7], [2, 3, 2])  # Solve x ≡ 2 (mod 3), x ≡ 3 (mod 5), x ≡ 2 (mod 7)
```

This cheat sheet encapsulates the verified theorems and computational procedures explored throughout these laboratories, serving as a rapid reference for mathematical verification workflows in both symbolic computation and formal proof assistant environments.
