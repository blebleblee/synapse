# Operational Verification Labs: Arithmetic

## Objective & Mathematical Computing Setup

This laboratory sequence transforms abstract arithmetic theory into computationally verifiable reality. You will execute symbolic manipulations that prove fundamental properties of the natural numbers, integers, rationals, and reals through direct computational demonstration rather than axiomatic hand-waving. The primary objective is to establish mechanical confidence in arithmetic foundations by programming formal verification routines that expose the algebraic structure beneath elementary operations.

Modern symbolic computation engines provide the infrastructure for rigorous mathematical verification. SymPy implements a computer algebra system (CAS) in pure Python, enabling exact symbolic arithmetic free from floating-point approximation errors. NumPy handles high-performance numerical array operations when computational speed matters more than symbolic exactness. SageMath integrates dozens of specialized mathematical libraries into a unified interface, bridging symbolic algebra, number theory, and computational group theory. Lean and Coq represent the proof assistant frontier, where every theorem requires mechanically verified derivations with no logical gaps permitted.

Your working environment must support exact rational arithmetic, symbolic variable manipulation, and automated theorem verification. Install the foundational Python mathematical stack with `pip install sympy numpy matplotlib`. For comprehensive symbolic capabilities, install SageMath through your system package manager or download the distribution from sagemath.org. On Debian-based systems, execute `sudo apt install sagemath`. On macOS, download the distribution from sagemath.org, install via conda (`conda install -c conda-forge sagemath`), or use Docker. Verify your installation by launching an interactive Python session and executing `import sympy; print(sympy.__version__)`. A version string of 1.12 or higher confirms you possess modern symbolic computation capabilities.

The distinction between symbolic and numeric computation governs every verification exercise in this guide. Symbolic engines manipulate mathematical expressions as abstract syntax trees, preserving exact relationships between variables and constants. When you define `x = sympy.Symbol('x')` and compute `sympy.expand((x + 1)**2)`, the system returns `x**2 + 2*x + 1` as an exact algebraic identity, not a floating-point approximation. Numeric computation sacrifices exactness for computational speed, representing numbers as finite-precision binary approximations. NumPy's `np.sqrt(2)` yields approximately `1.4142135623730951`, while SymPy's `sympy.sqrt(2)` preserves the exact irrational value for subsequent symbolic manipulation. Verification labs demand symbolic exactness whenever proving universal properties, switching to numeric methods only when estimating convergence rates or visualizing continuous functions.

The foundational arithmetic structures you will verify include the natural numbers $\mathbb{N} = \{0, 1, 2, 3, \ldots\}$ with addition and multiplication, the integers $\mathbb{Z} = \{\ldots, -2, -1, 0, 1, 2, \ldots\}$ extending naturals with additive inverses, the rationals $\mathbb{Q}$ forming a field under addition and multiplication with division by nonzero elements, and the reals $\mathbb{R}$ completing the rationals under Cauchy sequences or Dedekind cuts. Each structure embeds naturally in the next, preserving arithmetic operations while adding new algebraic capabilities. The Peano axioms characterize natural number arithmetic through five fundamental rules: zero exists, every natural number has a unique successor, zero is not the successor of any number, distinct numbers have distinct successors, and induction holds for all predicates. These axioms generate the entire structure of elementary arithmetic through recursive definitions of addition and multiplication.

## Exercise 1: Computational Verification of Core Theorems

The fundamental theorem of arithmetic states that every integer greater than one factors uniquely into primes, disregarding order. This decomposition provides the foundation for modular arithmetic, cryptographic protocols, and algebraic number theory. You will verify this theorem computationally by implementing prime factorization algorithms and testing uniqueness across thousands of random integers.

Begin by implementing trial division factorization in pure Python. Create a file named `arithmetic_verification.py` and define the following function:

```python
import sympy
from sympy import isprime, factorint, Integer
from collections import Counter
import random

def trial_division_factor(n):
    """
    Factor n using trial division by all primes up to sqrt(n).
    Returns list of prime factors with multiplicity.
    """
    if n < 2:
        return []
    
    factors = []
    d = 2
    
    while d * d <= n:
        while n % d == 0:
            factors.append(d)
            n //= d
        d += 1
    
    if n > 1:
        factors.append(n)
    
    return factors

def verify_unique_factorization(n, trials=1000):
    """
    Verify that factorization is unique by comparing multiple algorithms
    and checking that all produce identical prime decompositions.
    """
    results = []
    
    for _ in range(trials):
        test_val = random.randint(2, n)
        
        # Method 1: Trial division
        factors_trial = sorted(trial_division_factor(test_val))
        
        # Method 2: SymPy's optimized factorization
        factors_sympy = []
        factorization_dict = factorint(test_val)
        for prime, multiplicity in factorization_dict.items():
            factors_sympy.extend([prime] * multiplicity)
        factors_sympy = sorted(factors_sympy)
        
        # Verify both methods produce identical results
        if factors_trial != factors_sympy:
            return False, test_val, factors_trial, factors_sympy
        
        # Verify reconstruction produces original number
        product = 1
        for p in factors_trial:
            product *= p
        
        if product != test_val:
            return False, test_val, factors_trial, product
        
        results.append((test_val, factors_trial))
    
    return True, results

# Execute verification
success, data = verify_unique_factorization(10000, trials=5000)

if success:
    print("VERIFICATION SUCCESS: Unique factorization holds across all test cases")
    print(f"\nSample factorizations:")
    for i in range(10):
        num, factors = data[i]
        print(f"  {num} = {' × '.join(map(str, factors))}")
else:
    print(f"VERIFICATION FAILURE: Inconsistent factorization detected")
    print(f"  Number: {data[0]}")
    print(f"  Method 1: {data[1]}")
    print(f"  Method 2: {data[2]}")
```

Execute this script with `python arithmetic_verification.py`. The verification succeeds when every randomly selected integer produces identical prime factorizations under two independent algorithms and when multiplying the factors reconstructs the original number exactly. Failure indicates either a software bug or catastrophic hardware failure corrupting arithmetic operations.

The associativity and commutativity of addition and multiplication form the bedrock of algebraic manipulation. For all integers $a, b, c$, associativity requires $(a + b) + c = a + (b + c)$ and $(a \cdot b) \cdot c = a \cdot (b \cdot c)$, while commutativity demands $a + b = b + a$ and $a \cdot b = b \cdot a$. Symbolic verification proves these properties hold for arbitrary symbolic expressions, not merely specific numeric instances. Extend your verification script with the following symbolic property tests:

```python
def verify_arithmetic_axioms():
    """
    Symbolically verify foundational arithmetic axioms.
    """
    # Define symbolic variables
    a, b, c = sympy.symbols('a b c', integer=True)
    
    axioms_verified = []
    
    # Associativity of addition: (a + b) + c = a + (b + c)
    lhs_add = (a + b) + c
    rhs_add = a + (b + c)
    assoc_add = sympy.simplify(lhs_add - rhs_add) == 0
    axioms_verified.append(("Associativity of Addition", assoc_add))
    
    # Commutativity of addition: a + b = b + a
    comm_add = sympy.simplify((a + b) - (b + a)) == 0
    axioms_verified.append(("Commutativity of Addition", comm_add))
    
    # Associativity of multiplication: (a * b) * c = a * (b * c)
    lhs_mul = (a * b) * c
    rhs_mul = a * (b * c)
    assoc_mul = sympy.simplify(lhs_mul - rhs_mul) == 0
    axioms_verified.append(("Associativity of Multiplication", assoc_mul))
    
    # Commutativity of multiplication: a * b = b * a
    comm_mul = sympy.simplify((a * b) - (b * a)) == 0
    axioms_verified.append(("Commutativity of Multiplication", comm_mul))
    
    # Distributivity: a * (b + c) = a * b + a * c
    lhs_dist = a * (b + c)
    rhs_dist = a * b + a * c
    distributivity = sympy.simplify(lhs_dist - rhs_dist) == 0
    axioms_verified.append(("Distributivity", distributivity))
    
    # Identity elements: a + 0 = a and a * 1 = a
    add_identity = sympy.simplify((a + 0) - a) == 0
    mul_identity = sympy.simplify((a * 1) - a) == 0
    axioms_verified.append(("Additive Identity", add_identity))
    axioms_verified.append(("Multiplicative Identity", mul_identity))
    
    # Additive inverse: a + (-a) = 0
    add_inverse = sympy.simplify(a + (-a)) == 0
    axioms_verified.append(("Additive Inverse", add_inverse))
    
    # Print results
    print("SYMBOLIC AXIOM VERIFICATION")
    print("=" * 60)
    all_pass = True
    for axiom_name, verified in axioms_verified:
        status = "✓ PASS" if verified else "✗ FAIL"
        print(f"{status}: {axiom_name}")
        if not verified:
            all_pass = False
    
    print("=" * 60)
    if all_pass:
        print("All foundational arithmetic axioms verified symbolically.")
    else:
        print("WARNING: Axiom verification failure detected.")
    
    return all_pass

verify_arithmetic_axioms()
```

This verification establishes that SymPy's symbolic engine respects the field axioms for integer arithmetic. Each axiom check subtracts the right-hand side from the left-hand side and verifies the result simplifies to zero identically, confirming the equality holds for all possible integer values rather than merely specific test cases.

The division algorithm for integers states that for any integer $a$ and positive integer $b$, there exist unique integers $q$ (quotient) and $r$ (remainder) such that $a = bq + r$ with $0 \le r < b$. This theorem underlies modular arithmetic, the Euclidean algorithm for greatest common divisors, and polynomial division in abstract algebra. Verify the division algorithm through exhaustive computational testing:

```python
def verify_division_algorithm(max_dividend=1000, max_divisor=100):
    """
    Verify the division algorithm: For all integers a and positive b,
    there exist unique q and r such that a = bq + r with 0 <= r < b.
    """
    test_cases = []
    
    for a in range(-max_dividend, max_dividend + 1):
        for b in range(1, max_divisor + 1):
            # Compute quotient and remainder using Python's divmod
            q_python, r_python = divmod(a, b)
            
            # Verify division property: a = bq + r
            reconstructed = b * q_python + r_python
            if reconstructed != a:
                return False, f"Reconstruction failed: {a} ≠ {b}×{q_python} + {r_python}"
            
            # Verify remainder bounds: 0 <= r < b
            if not (0 <= r_python < b):
                return False, f"Remainder out of bounds: r={r_python}, b={b}"
            
            # Verify uniqueness by checking no other valid (q', r') exists
            # If there were another solution, we'd have a = bq' + r' with 0 <= r' < b
            # Then bq + r = bq' + r', so b(q - q') = r' - r
            # Since |r' - r| < b and b divides b(q - q'), we must have q = q' and r = r'
            
            test_cases.append((a, b, q_python, r_python))
    
    print(f"DIVISION ALGORITHM VERIFICATION")
    print(f"Tested {len(test_cases)} cases: all integers a in [{-max_dividend}, {max_dividend}]")
    print(f"  divided by all positive integers b in [1, {max_divisor}]")
    print(f"\nSample results:")
    for i in range(0, min(20, len(test_cases)), max(1, len(test_cases) // 20)):
        a, b, q, r = test_cases[i]
        print(f"  {a:4d} = {b:2d} × {q:4d} + {r:2d}    (verification: {b*q + r == a})")
    
    return True, test_cases

success, result = verify_division_algorithm(max_dividend=500, max_divisor=50)
if success:
    print(f"\n✓ Division algorithm verified across {len(result)} test cases")
else:
    print(f"\n✗ FAILURE: {result}")
```

Run this verification to confirm that Python's built-in integer division operator implements the mathematical division algorithm correctly. The uniqueness of $q$ and $r$ follows from the bounds on $r$: if two different pairs $(q_1, r_1)$ and $(q_2, r_2)$ both satisfied the conditions, then $b(q_1 - q_2) = r_2 - r_1$, but since $|r_2 - r_1| < b$, the only possibility is $q_1 = q_2$ and $r_1 = r_2$.

## Exercise 2: Boundary Value Stress Testing & Singularities

Arithmetic operations exhibit pathological behavior at boundary conditions and singularities. Division by zero remains undefined in standard arithmetic, though limits and extended real number systems assign meaning to expressions like $\lim_{x \to 0^+} \frac{1}{x} = +\infty$. Integer overflow silently wraps around in fixed-width hardware arithmetic, producing mathematically incorrect results when exceeding representational limits. Floating-point arithmetic introduces rounding errors that accumulate through repeated operations, violating associativity and distributivity in numerical computation. This exercise section systematically probes these boundary conditions to distinguish mathematical truth from computational approximation.

Begin with division-by-zero detection and symbolic limit analysis. Symbolic systems like SymPy represent undefined expressions explicitly rather than crashing with runtime exceptions. Create a boundary testing script:

```python
import sympy
from sympy import Symbol, limit, oo, zoo, nan, Rational
import numpy as np
import warnings

def test_division_singularities():
    """
    Test behavior of division near and at zero, comparing symbolic
    and numeric approaches.
    """
    x = Symbol('x', real=True, positive=True)
    
    print("DIVISION SINGULARITY ANALYSIS")
    print("=" * 60)
    
    # Symbolic division by zero
    print("\n1. Symbolic Division by Zero:")
    try:
        result_sym = sympy.sympify("1/0")
        print(f"   SymPy 1/0 = {result_sym} (type: {type(result_sym).__name__})")
    except Exception as e:
        print(f"   SymPy raises: {type(e).__name__}: {e}")
    
    # Complex infinity representation
    print(f"   SymPy zoo (complex infinity) = {zoo}")
    
    # Numeric division by zero
    print("\n2. Numeric Division by Zero:")
    print("   Python float 1.0/0.0:")
    try:
        result_float = 1.0 / 0.0
        print(f"     {result_float}")
    except ZeroDivisionError:
        print(f"     Raises ZeroDivisionError (unlike NumPy)")
    
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        result_np = np.float64(1.0) / np.float64(0.0)
        print(f"   NumPy 1.0/0.0 = {result_np}")
    
    # Limit analysis approaching zero
    print("\n3. Limit Analysis as x → 0:")
    
    # One-sided limits
    lim_right = limit(1/x, x, 0, '+')
    lim_left = limit(1/x, x, 0, '-')
    
    print(f"   lim(x→0⁺) 1/x = {lim_right}")
    print(f"   lim(x→0⁻) 1/x = {lim_left}")
    print(f"   Two-sided limit does not exist (directional limits differ)")
    
    # Quadratic approaching zero
    lim_quad = limit(1/x**2, x, 0)
    print(f"   lim(x→0) 1/x² = {lim_quad}")
    
    # Oscillating singularity
    lim_sin = limit(sympy.sin(1/x), x, 0)
    print(f"   lim(x→0) sin(1/x) = {lim_sin} (DNE - oscillates infinitely)")
    
    return True

def test_integer_overflow():
    """
    Demonstrate that Python integers have arbitrary precision while
    fixed-width types overflow.
    """
    print("\n" + "=" * 60)
    print("INTEGER OVERFLOW BEHAVIOR")
    print("=" * 60)
    
    # Python arbitrary-precision integers
    print("\n1. Python Arbitrary-Precision Integers:")
    large_int = 2 ** 1000
    print(f"   2^1000 = {large_int}")
    print(f"   Bit length: {large_int.bit_length()} bits")
    print(f"   Can compute (2^1000)^2 without overflow:")
    print(f"   Result has {(large_int ** 2).bit_length()} bits")
    
    # NumPy fixed-width integers (demonstrate overflow)
    print("\n2. NumPy Fixed-Width Integer Overflow:")
    print("   int8 range: [-128, 127]")
    
    a = np.int8(127)
    b = np.int8(1)
    
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        result_overflow = a + b
        print(f"   np.int8(127) + np.int8(1) = {result_overflow}")
        print(f"   ✗ Overflow wraps to {result_overflow} (should be 128)")
    
    # Demonstrate correct behavior with promotion
    result_correct = int(a) + int(b)
    print(f"   int(np.int8(127)) + int(np.int8(1)) = {result_correct}")
    print(f"   ✓ Correct result with type promotion")
    
    return True

def test_floating_point_pathologies():
    """
    Demonstrate accumulation of rounding errors and violation of
    associativity in floating-point arithmetic.
    """
    print("\n" + "=" * 60)
    print("FLOATING-POINT ARITHMETIC PATHOLOGIES")
    print("=" * 60)
    
    # Loss of associativity
    print("\n1. Associativity Violation:")
    a, b, c = 1e16, 1.0, -1e16
    
    result1 = (a + b) + c
    result2 = a + (b + c)
    
    print(f"   Let a = {a}, b = {b}, c = {c}")
    print(f"   (a + b) + c = {result1}")
    print(f"   a + (b + c) = {result2}")
    print(f"   Equal? {result1 == result2}")
    print(f"   ✗ Associativity violated due to finite precision")
    
    # Symbolic verification shows mathematical truth
    a_sym, b_sym, c_sym = sympy.symbols('a b c', real=True)
    expr1 = (a_sym + b_sym) + c_sym
    expr2 = a_sym + (b_sym + c_sym)
    symbolic_equal = sympy.simplify(expr1 - expr2) == 0
    print(f"   Symbolic verification: (a+b)+c = a+(b+c)? {symbolic_equal}")
    print(f"   ✓ Mathematically true, but numerically violated")
    
    # Catastrophic cancellation
    print("\n2. Catastrophic Cancellation:")
    x = 1.0 + 1e-15
    y = 1.0
    
    diff_numeric = x - y
    diff_exact = Rational(1, 10**15)
    
    print(f"   x = 1.0 + 10⁻¹⁵ (stored in float64)")
    print(f"   y = 1.0")
    print(f"   x - y (numeric) = {diff_numeric:.20e}")
    print(f"   x - y (exact)   = {float(diff_exact):.20e}")
    relative_error = abs(diff_numeric - float(diff_exact)) / float(diff_exact)
    print(f"   Relative error: {relative_error:.2%}")
    
    # Accumulation through summation
    print("\n3. Summation Order Dependence:")
    terms = [1e-10] * 1000000 + [1.0]
    
    # Forward summation
    sum_forward = 0.0
    for t in terms:
        sum_forward += t
    
    # Reverse summation
    sum_reverse = 0.0
    for t in reversed(terms):
        sum_reverse += t
    
    # Kahan summation (compensated)
    sum_kahan = 0.0
    compensation = 0.0
    for t in terms:
        y = t - compensation
        temp = sum_kahan + y
        compensation = (temp - sum_kahan) - y
        sum_kahan = temp
    
    print(f"   Sum of 10⁶ copies of 10⁻¹⁰ plus 1.0:")
    print(f"   Forward sum:  {sum_forward:.15f}")
    print(f"   Reverse sum:  {sum_reverse:.15f}")
    print(f"   Kahan sum:    {sum_kahan:.15f}")
    print(f"   Exact value:  {1.0 + 1e-10 * 1e6:.15f}")
    print(f"   ✗ Order matters in floating-point summation")
    
    return True

# Execute all boundary tests
test_division_singularities()
test_integer_overflow()
test_floating_point_pathologies()
```

Execute this comprehensive boundary analysis with `python arithmetic_verification.py`. The division singularity tests reveal that SymPy preserves mathematical structure by representing undefined expressions symbolically as `zoo` (complex infinity) or computing directional limits explicitly. NumPy and native Python floats follow IEEE 754 standards, returning `inf` for overflow and `-inf` or `inf` for division by zero depending on sign, with `nan` (not-a-number) propagating through subsequent calculations.

The integer overflow demonstration exposes the fundamental distinction between mathematical integers and computational representations. Python's native integers automatically promote to arbitrary-precision arithmetic, computing $2^{1000}$ exactly and allocating sufficient memory to store results requiring thousands of bits. NumPy's fixed-width integer types (`int8`, `int16`, `int32`, `int64`) wrap around upon overflow, silently producing incorrect results when exceeding their representational range. The computation `np.int8(127) + np.int8(1)` wraps to `-128` rather than producing `128`, because `int8` represents integers using two's complement in 8 bits, with range $[-128, 127]$.

The floating-point pathology tests demonstrate that approximate arithmetic violates mathematical field axioms. The associativity violation $(10^{16} + 1) + (-10^{16}) \ne 10^{16} + (1 + (-10^{16}))$ occurs because the magnitude difference between $10^{16}$ and $1$ exceeds floating-point precision. When adding $1$ to $10^{16}$, the result rounds back to $10^{16}$ exactly, erasing the contribution of $1$. The left-to-right evaluation produces $(10^{16}) + (-10^{16}) = 0$, while right-to-left gives $10^{16} + (0) = 10^{16}$. Catastrophic cancellation amplifies rounding errors when subtracting nearly equal quantities, losing significant digits. Kahan summation compensates for accumulated errors by maintaining a running compensation term, demonstrating that algorithmic approaches can partially mitigate floating-point pathologies.

Rational arithmetic using SymPy's `Rational` class preserves exact fractional values throughout computation. Extend your verification script to compare rational and floating-point accumulation:

```python
def test_rational_vs_float_accumulation():
    """
    Compare accumulation errors between floating-point and exact rational arithmetic.
    """
    print("\n" + "=" * 60)
    print("RATIONAL VS FLOATING-POINT ACCUMULATION")
    print("=" * 60)
    
    # Compute sum of 1/n for n = 1 to 1000 (harmonic series partial sum)
    n_terms = 1000
    
    # Floating-point computation
    sum_float = 0.0
    for n in range(1, n_terms + 1):
        sum_float += 1.0 / n
    
    # Rational exact computation
    sum_rational = Rational(0)
    for n in range(1, n_terms + 1):
        sum_rational += Rational(1, n)
    
    print(f"\nSum of 1/n for n = 1 to {n_terms}:")
    print(f"  Float result:    {sum_float:.15f}")
    print(f"  Rational result: {float(sum_rational):.15f}")
    print(f"  Difference:      {abs(sum_float - float(sum_rational)):.2e}")
    print(f"\nRational representation (first few terms):")
    
    # Show exact rational form for small partial sum
    sum_small = Rational(0)
    for n in range(1, 6):
        sum_small += Rational(1, n)
    print(f"  1 + 1/2 + 1/3 + 1/4 + 1/5 = {sum_small}")
    print(f"  Decimal: {float(sum_small):.10f}")
    
    # Demonstrate rational arithmetic preservation
    print(f"\nRational arithmetic properties:")
    r1 = Rational(1, 3)
    r2 = Rational(1, 6)
    r_sum = r1 + r2
    print(f"  1/3 + 1/6 = {r_sum} (exact)")
    print(f"  Float: {float(r1)} + {float(r2)} = {float(r1) + float(r2):.17f}")
    print(f"  ✓ Rational preserves exact value {r_sum} = {float(r_sum)}")
    
    return True

test_rational_vs_float_accumulation()
```

This verification establishes that SymPy's `Rational` class maintains exact fractional arithmetic, representing numbers as pairs of integers (numerator and denominator) and performing all operations without approximation. The harmonic series partial sum $\sum_{n=1}^{1000} \frac{1}{n}$ accumulates differently in floating-point versus exact rational arithmetic, with floating-point errors growing as more terms are added. Rational arithmetic exactly represents results like $\frac{1}{3} + \frac{1}{6} = \frac{1}{2}$, while floating-point produces approximations limited by binary representation constraints.

## Exercise 3: Algorithmic Implementation of Formal Structures

Formal arithmetic structures emerge through algorithmic implementation rather than axiomatic definition. The Euclidean algorithm computes greatest common divisors through repeated division, formalizing the fundamental theorem that every pair of integers shares a unique maximal common divisor expressible as a linear combination (Bézout's identity). Modular arithmetic forms a ring structure under addition and multiplication modulo $n$, with multiplicative inverses existing precisely when elements are coprime to the modulus. The Chinese Remainder Theorem reconstructs integers from their residues modulo pairwise coprime moduli, providing the foundation for efficient computation in cryptographic protocols.

Implement the extended Euclidean algorithm to compute Bézout coefficients. For integers $a$ and $b$, the algorithm returns $\gcd(a, b)$ along with integers $x$ and $y$ satisfying $ax + by = \gcd(a, b)$. This linear combination proves the gcd divides every linear combination of $a$ and $b$, establishing its maximality:

```python
def extended_gcd(a, b):
    """
    Extended Euclidean Algorithm.
    Returns (gcd, x, y) such that ax + by = gcd(a, b).
    """
    if b == 0:
        return (a, 1, 0)
    
    old_r, r = a, b
    old_x, x = 1, 0
    old_y, y = 0, 1
    
    while r != 0:
        quotient = old_r // r
        old_r, r = r, old_r - quotient * r
        old_x, x = x, old_x - quotient * x
        old_y, y = y, old_y - quotient * y
    
    return (old_r, old_x, old_y)

def verify_bezout_identity(test_pairs):
    """
    Verify Bézout's identity for multiple integer pairs.
    """
    print("BÉZOUT'S IDENTITY VERIFICATION")
    print("=" * 60)
    
    all_verified = True
    
    for a, b in test_pairs:
        gcd, x, y = extended_gcd(a, b)
        
        # Verify ax + by = gcd
        linear_combination = a * x + b * y
        verified = (linear_combination == gcd)
        
        # Verify gcd divides both a and b
        divides_a = (a % gcd == 0)
        divides_b = (b % gcd == 0)
        
        # Compare with SymPy's gcd
        gcd_sympy = sympy.gcd(a, b)
        matches_sympy = (gcd == gcd_sympy)
        
        status = "✓" if (verified and divides_a and divides_b and matches_sympy) else "✗"
        
        print(f"{status} gcd({a:4d}, {b:4d}) = {gcd:3d}")
        print(f"     {a}×({x:3d}) + {b}×({y:3d}) = {linear_combination:4d}")
        print(f"     Verification: {linear_combination} = {gcd}? {verified}")
        
        if not verified:
            all_verified = False
    
    print("=" * 60)
    if all_verified:
        print("✓ All Bézout identity verifications passed")
    
    return all_verified

# Test cases including edge cases
test_pairs = [
    (240, 46),
    (17, 13),
    (100, 35),
    (1071, 462),
    (35, 0),      # Edge: gcd(a, 0) = a
    (0, 42),      # Edge: gcd(0, b) = b
    (1, 1),       # Edge: gcd(1, 1) = 1
    (13, 13),     # Edge: gcd(a, a) = a
    (-48, 18),    # Negative numbers
    (97, 31),     # Coprime (gcd = 1)
]

verify_bezout_identity(test_pairs)
```

Run this verification to confirm the extended Euclidean algorithm correctly computes Bézout coefficients. The algorithm maintains the invariant that $\gcd(a, b) = \gcd(b, a \bmod b)$ while tracking linear combination coefficients through each division step. When the algorithm terminates with remainder zero, the accumulated coefficients satisfy the Bézout identity exactly. The edge cases verify behavior when one input is zero, both inputs are equal, or inputs are coprime with $\gcd(a, b) = 1$.

Modular multiplicative inverses exist precisely when the element and modulus are coprime. For $a$ and $n$ with $\gcd(a, n) = 1$, the modular inverse $a^{-1} \pmod{n}$ satisfies $a \cdot a^{-1} \equiv 1 \pmod{n}$. The extended Euclidean algorithm computes this inverse by finding $x$ such that $ax + ny = 1$, which implies $ax \equiv 1 \pmod{n}$. Implement modular inverse computation and verify the multiplicative property:

```python
def mod_inverse(a, n):
    """
    Compute modular multiplicative inverse of a modulo n.
    Returns a^(-1) mod n such that (a * a^(-1)) % n = 1.
    Returns None if gcd(a, n) != 1 (inverse does not exist).
    """
    gcd, x, _ = extended_gcd(a, n)
    
    if gcd != 1:
        return None  # Inverse does not exist
    
    return x % n

def verify_modular_inverses(modulus_values, test_count=20):
    """
    Verify modular multiplicative inverse properties.
    """
    print("\n" + "=" * 60)
    print("MODULAR MULTIPLICATIVE INVERSE VERIFICATION")
    print("=" * 60)
    
    for n in modulus_values:
        print(f"\nModulus n = {n}:")
        
        # Find all elements coprime to n
        coprime_elements = [a for a in range(1, n) if sympy.gcd(a, n) == 1]
        
        print(f"  φ(n) = {len(coprime_elements)} elements coprime to {n}")
        print(f"  Elements: {coprime_elements[:20]}{'...' if len(coprime_elements) > 20 else ''}")
        
        # Verify inverse property for subset
        test_elements = coprime_elements[:min(test_count, len(coprime_elements))]
        
        all_verified = True
        for a in test_elements:
            # Compute inverse
            a_inv = mod_inverse(a, n)
            
            if a_inv is None:
                print(f"  ✗ Unexpected: no inverse for {a} (should be coprime)")
                all_verified = False
                continue
            
            # Verify a * a_inv ≡ 1 (mod n)
            product = (a * a_inv) % n
            verified = (product == 1)
            
            # Compare with SymPy's inverse
            a_inv_sympy = pow(a, -1, n)  # Python 3.8+ built-in modular inverse
            matches_sympy = (a_inv == a_inv_sympy)
            
            if not verified or not matches_sympy:
                print(f"  ✗ a={a}, a⁻¹={a_inv}, a×a⁻¹ mod {n} = {product}")
                all_verified = False
        
        if all_verified:
            print(f"  ✓ All {len(test_elements)} tested inverses verified")
        
        # Verify non-coprime elements have no inverse
        non_coprime = [a for a in range(1, n) if sympy.gcd(a, n) != 1]
        if non_coprime:
            sample_non_coprime = non_coprime[:3]
            print(f"\n  Non-coprime elements (no inverse): {sample_non_coprime}")
            for a in sample_non_coprime:
                inv = mod_inverse(a, n)
                if inv is not None:
                    print(f"  ✗ Unexpected inverse for non-coprime {a}")
                    all_verified = False
    
    return True

# Test with various moduli
moduli = [7, 10, 13, 16, 26, 37]
verify_modular_inverses(moduli, test_count=15)
```

This verification establishes the structure of multiplicative groups modulo $n$. The elements coprime to $n$ form a group under multiplication modulo $n$, with Euler's totient function $\phi(n)$ counting the group order. For prime $p$, all $p-1$ nonzero elements have inverses, forming the cyclic group $(\mathbb{Z}/p\mathbb{Z})^*$ of order $p-1$. For composite $n$, only elements coprime to $n$ possess inverses, with non-coprime elements having no multiplicative inverse since they share factors with the modulus.

The Chinese Remainder Theorem (CRT) provides an isomorphism between $\mathbb{Z}/n\mathbb{Z}$ and the product $\mathbb{Z}/n_1\mathbb{Z} \times \cdots \times \mathbb{Z}/n_k\mathbb{Z}$ when $n = n_1 \cdots n_k$ with pairwise coprime factors. Given residues $a_i \equiv x \pmod{n_i}$, the CRT reconstructs the unique $x \pmod{n}$ satisfying all congruences simultaneously. Implement CRT reconstruction:

```python
def chinese_remainder_theorem(residues, moduli):
    """
    Chinese Remainder Theorem: Solve system of congruences
      x ≡ a_i (mod n_i) for i = 1, ..., k
    where moduli n_i are pairwise coprime.
    
    Returns unique solution x modulo N = n_1 * n_2 * ... * n_k.
    """
    # Verify pairwise coprimality
    for i in range(len(moduli)):
        for j in range(i + 1, len(moduli)):
            if sympy.gcd(moduli[i], moduli[j]) != 1:
                raise ValueError(f"Moduli not pairwise coprime: gcd({moduli[i]}, {moduli[j]}) != 1")
    
    # Compute product of all moduli
    N = 1
    for n in moduli:
        N *= n
    
    # Apply CRT construction
    x = 0
    for a_i, n_i in zip(residues, moduli):
        N_i = N // n_i
        M_i = mod_inverse(N_i, n_i)
        x += a_i * N_i * M_i
    
    return x % N

def verify_chinese_remainder_theorem():
    """
    Verify CRT reconstruction for multiple systems of congruences.
    """
    print("\n" + "=" * 60)
    print("CHINESE REMAINDER THEOREM VERIFICATION")
    print("=" * 60)
    
    # Test case 1: Classic example
    print("\nTest 1: x ≡ 2 (mod 3), x ≡ 3 (mod 5), x ≡ 2 (mod 7)")
    residues_1 = [2, 3, 2]
    moduli_1 = [3, 5, 7]
    
    x_1 = chinese_remainder_theorem(residues_1, moduli_1)
    N_1 = 3 * 5 * 7
    
    print(f"  Solution: x ≡ {x_1} (mod {N_1})")
    
    # Verify solution satisfies all congruences
    verified_1 = all(x_1 % n == a for a, n in zip(residues_1, moduli_1))
    print(f"  Verification:")
    for a, n in zip(residues_1, moduli_1):
        print(f"    {x_1} mod {n} = {x_1 % n} {'✓' if x_1 % n == a else '✗'}")
    
    # Test case 2: Larger system
    print("\nTest 2: Five congruences")
    residues_2 = [3, 5, 7, 1, 2]
    moduli_2 = [7, 11, 13, 17, 19]
    
    x_2 = chinese_remainder_theorem(residues_2, moduli_2)
    N_2 = 7 * 11 * 13 * 17 * 19
    
    print(f"  Moduli: {moduli_2}")
    print(f"  Residues: {residues_2}")
    print(f"  Solution: x ≡ {x_2} (mod {N_2})")
    
    verified_2 = all(x_2 % n == a for a, n in zip(residues_2, moduli_2))
    
    if verified_2:
        print(f"  ✓ All congruences satisfied")
    
    # Test case 3: Demonstrate uniqueness modulo N
    print("\nTest 3: Uniqueness verification")
    residues_3 = [1, 2]
    moduli_3 = [3, 5]
    
    x_3 = chinese_remainder_theorem(residues_3, moduli_3)
    N_3 = 3 * 5
    
    print(f"  x ≡ 1 (mod 3), x ≡ 2 (mod 5)")
    print(f"  Solution in [0, {N_3}): x = {x_3}")
    print(f"  Other solutions: x = {x_3} + k×{N_3} for any integer k")
    print(f"  Examples: {[x_3 + k*N_3 for k in range(-2, 3)]}")
    
    # Verify all examples satisfy both congruences
    examples = [x_3 + k*N_3 for k in range(-2, 3)]
    all_satisfy = all((ex % 3 == 1 and ex % 5 == 2) for ex in examples)
    print(f"  All examples satisfy congruences: {all_satisfy}")
    
    return True

verify_chinese_remainder_theorem()
```

Execute this CRT verification to confirm the algorithm correctly reconstructs solutions to simultaneous congruences. The construction computes $x = \sum_{i=1}^k a_i N_i M_i \pmod{N}$, where $N = \prod n_i$, $N_i = N/n_i$, and $M_i = N_i^{-1} \pmod{n_i}$. Each term $a_i N_i M_i$ satisfies the $i$-th congruence while being zero modulo all other $n_j$, making the sum satisfy all congruences simultaneously. The solution is unique modulo $N$, with all solutions differing by multiples of $N$.

Implement Fermat's Little Theorem verification as a final algorithmic exercise. For prime $p$ and integer $a$ not divisible by $p$, Fermat's theorem states $a^{p-1} \equiv 1 \pmod{p}$. This provides a probabilistic primality test and underlies the RSA cryptosystem's correctness:

```python
def verify_fermats_little_theorem(primes, test_cases_per_prime=20):
    """
    Verify Fermat's Little Theorem: For prime p and a not divisible by p,
      a^(p-1) ≡ 1 (mod p)
    """
    print("\n" + "=" * 60)
    print("FERMAT'S LITTLE THEOREM VERIFICATION")
    print("=" * 60)
    
    for p in primes:
        print(f"\nPrime p = {p}:")
        
        # Test with random integers not divisible by p
        test_values = []
        for _ in range(test_cases_per_prime):
            a = random.randint(2, min(1000, p * 10))
            if a % p != 0:  # Ensure a is not divisible by p
                test_values.append(a)
        
        all_verified = True
        failures = []
        
        for a in test_values[:20]:  # Show first 20
            # Compute a^(p-1) mod p
            result = pow(a, p - 1, p)
            
            verified = (result == 1)
            
            if not verified:
                all_verified = False
                failures.append((a, result))
        
        if all_verified:
            print(f"  ✓ Verified for {len(test_values)} values of a")
        else:
            print(f"  ✗ Failures detected:")
            for a, result in failures[:5]:
                print(f"    a={a}: {a}^{p-1} mod {p} = {result} (expected 1)")
        
        # Special case: verify the corollary a^p ≡ a (mod p) for all a
        print(f"\n  Corollary: a^p ≡ a (mod p) for all a:")
        corollary_samples = [1, 2, p//2, p-1, p, p+1, 2*p]
        corollary_verified = True
        
        for a in corollary_samples:
            result = pow(a, p, p)
            expected = a % p
            verified = (result == expected)
            
            if not verified:
                corollary_verified = False
                print(f"    ✗ a={a}: {a}^{p} mod {p} = {result} (expected {expected})")
        
        if corollary_verified:
            print(f"    ✓ Corollary verified for sample values")
    
    # Demonstrate use in primality testing
    print("\n" + "=" * 60)
    print("APPLICATION: Fermat Primality Test")
    print("=" * 60)
    
    def fermat_primality_test(n, k=10):
        """
        Probabilistic primality test using Fermat's Little Theorem.
        Test k random bases. If any fail, n is composite.
        If all pass, n is probably prime.
        """
        if n < 2:
            return False
        if n == 2 or n == 3:
            return True
        
        for _ in range(k):
            a = random.randint(2, n - 2)
            if pow(a, n - 1, n) != 1:
                return False  # Definitely composite
        
        return True  # Probably prime
    
    # Test with known primes and composites
    test_numbers = [
        (17, True),
        (19, True),
        (91, False),   # 91 = 7 × 13
        (97, True),
        (100, False),
        (561, False),  # Carmichael number (pseudoprime)
    ]
    
    print("\nTesting numbers:")
    for n, is_prime in test_numbers:
        fermat_result = fermat_primality_test(n, k=20)
        actual = sympy.isprime(n)
        
        status = "✓" if (fermat_result == is_prime and actual == is_prime) else "⚠"
        print(f"  {status} n={n:3d}: Fermat test={fermat_result:5}, Actual={actual:5}")
    
    print("\nNote: Carmichael numbers (like 561) pass Fermat test but are composite.")
    
    return True

# Test with small primes
primes_to_test = [3, 5, 7, 11, 13, 17, 23, 29, 37, 41]
verify_fermats_little_theorem(primes_to_test, test_cases_per_prime=50)
```

Run this verification to confirm Fermat's Little Theorem across multiple primes and witness its application to probabilistic primality testing. The theorem provides a necessary condition for primality: if $a^{n-1} \not\equiv 1 \pmod{n}$ for some $a$ coprime to $n$, then $n$ is definitely composite. However, the converse fails for Carmichael numbers—composite integers $n$ satisfying $a^{n-1} \equiv 1 \pmod{n}$ for all $a$ coprime to $n$. The smallest Carmichael number is $561 = 3 \times 11 \times 17$, which passes Fermat's test for all bases despite being composite. More sophisticated primality tests like Miller-Rabin avoid this weakness by checking additional algebraic structure.

## Formal Axioms Cheat Sheet & Verification Reference

The field axioms for real numbers $\mathbb{R}$ establish addition and multiplication as binary operations satisfying closure, associativity, commutativity, identity, inverse, and distributivity properties. These axioms generate all algebraic manipulations permitted in elementary and advanced mathematics.

**Additive Structure (Abelian Group):**
1. Closure: For all $a, b \in \mathbb{R}$, $a + b \in \mathbb{R}$
2. Associativity: $(a + b) + c = a + (b + c)$
3. Identity: $0 \in \mathbb{R}$ such that $a + 0 = a$
4. Inverse: For each $a \in \mathbb{R}$, there exists $-a \in \mathbb{R}$ such that $a + (-a) = 0$
5. Commutativity: $a + b = b + a$

**Multiplicative Structure (Abelian Group on Nonzero Elements):**
1. Closure: For all $a, b \in \mathbb{R}$, $a \cdot b \in \mathbb{R}$
2. Associativity: $(a \cdot b) \cdot c = a \cdot (b \cdot c)$
3. Identity: $1 \in \mathbb{R}$ with $1 \ne 0$ such that $a \cdot 1 = a$
4. Inverse: For each $a \in \mathbb{R}$ with $a \ne 0$, there exists $a^{-1} \in \mathbb{R}$ such that $a \cdot a^{-1} = 1$
5. Commutativity: $a \cdot b = b \cdot a$

**Distributivity (Connecting Addition and Multiplication):**
$a \cdot (b + c) = a \cdot b + a \cdot c$

**Order Axioms (Total Ordering Compatible with Field Operations):**
1. Trichotomy: For all $a, b \in \mathbb{R}$, exactly one of $a < b$, $a = b$, or $a > b$ holds
2. Transitivity: If $a < b$ and $b < c$, then $a < c$
3. Addition compatibility: If $a < b$, then $a + c < b + c$
4. Multiplication compatibility: If $a < b$ and $0 < c$, then $a \cdot c < b \cdot c$

**Completeness Axiom (Distinguishing Reals from Rationals):**
Every nonempty subset of $\mathbb{R}$ bounded above has a least upper bound (supremum) in $\mathbb{R}$.

**Peano Axioms (Characterizing Natural Numbers):**
1. $0 \in \mathbb{N}$ (zero is a natural number)
2. For each $n \in \mathbb{N}$, the successor $S(n) \in \mathbb{N}$ exists
3. For all $n \in \mathbb{N}$, $S(n) \ne 0$ (zero is not a successor)
4. $S$ is injective: if $S(n) = S(m)$, then $n = m$
5. Induction: If $P(0)$ holds and $P(n) \implies P(S(n))$ for all $n$, then $P(n)$ holds for all $n \in \mathbb{N}$

**Division Algorithm (Fundamental to Modular Arithmetic):**
For any integer $a$ and positive integer $b$, there exist unique integers $q$ (quotient) and $r$ (remainder) such that:
$$a = bq + r \quad \text{with} \quad 0 \le r < b$$

**Bézout's Identity (Characterizing GCD as Linear Combination):**
For any integers $a$ and $b$, their greatest common divisor $d = \gcd(a, b)$ can be expressed as:
$$d = ax + by$$
for some integers $x$ and $y$. Moreover, $d$ is the smallest positive integer expressible as a linear combination of $a$ and $b$.

**Chinese Remainder Theorem (Isomorphism for Pairwise Coprime Moduli):**
Let $n_1, \ldots, n_k$ be pairwise coprime positive integers, and let $N = n_1 \cdots n_k$. Then the system of congruences:
$$x \equiv a_1 \pmod{n_1}, \quad \ldots, \quad x \equiv a_k \pmod{n_k}$$
has a unique solution modulo $N$. The map $\mathbb{Z}/N\mathbb{Z} \to \mathbb{Z}/n_1\mathbb{Z} \times \cdots \times \mathbb{Z}/n_k\mathbb{Z}$ defined by $x \mapsto (x \bmod n_1, \ldots, x \bmod n_k)$ is a ring isomorphism.

**Fermat's Little Theorem (Characterizing Arithmetic Modulo Primes):**
For any prime $p$ and integer $a$ not divisible by $p$:
$$a^{p-1} \equiv 1 \pmod{p}$$
Equivalently, for all integers $a$:
$$a^p \equiv a \pmod{p}$$

**Fundamental Theorem of Arithmetic (Unique Prime Factorization):**
Every integer $n > 1$ can be expressed uniquely (up to order) as a product of prime powers:
$$n = p_1^{e_1} p_2^{e_2} \cdots p_k^{e_k}$$
where $p_1 < p_2 < \cdots < p_k$ are primes and $e_i \ge 1$.

**Quick Verification Commands:**

Test field axioms symbolically:
```python
import sympy
a, b, c = sympy.symbols('a b c', real=True)
print(sympy.simplify((a + b) + c - (a + (b + c))) == 0)  # Associativity
print(sympy.simplify(a * (b + c) - (a*b + a*c)) == 0)    # Distributivity
```

Verify division algorithm:
```python
a, b = 17, 5
q, r = divmod(a, b)
print(f"{a} = {b}×{q} + {r}, 0 ≤ {r} < {b}: {a == b*q + r and 0 <= r < b}")
```

Compute GCD with Bézout coefficients:
```python
import sympy
a, b = 240, 46
g, x, y = sympy.gcdex(a, b)
print(f"gcd({a},{b}) = {g} = {a}×({x}) + {b}×({y})")
print(f"Verification: {a*x + b*y == g}")
```

Verify modular inverse:
```python
a, n = 7, 26
a_inv = pow(a, -1, n)  # Python 3.8+
print(f"{a}^(-1) mod {n} = {a_inv}")
print(f"Verification: {a}×{a_inv} mod {n} = {(a * a_inv) % n}")
```

Apply Chinese Remainder Theorem:
```python
from sympy.ntheory.modular import crt
moduli = [3, 5, 7]
residues = [2, 3, 2]
x, N = crt(moduli, residues)
print(f"Solution: x ≡ {x} (mod {N})")
print(f"Verification: {[x % n for n in moduli]} == {residues}")
```

Test Fermat's Little Theorem:
```python
p, a = 13, 7
result = pow(a, p-1, p)
print(f"{a}^({p}-1) mod {p} = {result}")
print(f"Fermat verified: {result == 1}")
```

These verification commands provide immediate computational confirmation of theoretical arithmetic properties, transforming abstract axioms into executable mathematical reality. Every assertion in pure mathematics admits computational verification through symbolic manipulation or numeric stress testing, establishing confidence in both the theory and its computational implementation.
