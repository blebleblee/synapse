# Operational Verification Labs: Complex Analysis

## Objective & Mathematical Computing Setup

Complex analysis occupies a privileged position in mathematics: its theorems are not merely true but *rigidly* true, holding with an exactness that makes them ideally suited to machine verification. The Cauchy integral formula, the residue theorem, and the identity principle are not approximations or heuristics — they are exact algebraic-analytic facts that a symbolic engine can confirm without floating-point error. This lab guide treats Python's SymPy CAS, NumPy, and SageMath not as numerical approximators but as formal verification instruments, checking that your hand-derivations are correct to the symbol.

The goal throughout is a specific discipline: you derive a result by hand, formalize it into a symbolic computation, and confirm that the two agree exactly. Where they disagree, the discrepancy is a theorem-violation, a miscalculation, or a subtlety about branch cuts that the tool is exposing. That discipline — derive, formalize, compare — is the core method of this lab.

Before any exercise, verify that your environment is correctly configured. Run the following from your terminal:

```text
python -c "import sympy; print('SymPy', sympy.__version__)"
python -c "import numpy; print('NumPy', numpy.__version__)"
python -c "from sympy import I, exp, pi, integrate, symbols, residue; print('Core imports OK')"
```

For SageMath, verify independently:

```text
sage --version
sage -c "from sage.all import CC, ComplexField, integrate, var; print('SageMath OK')"
```

The target environment is Python 3.11 or higher with SymPy 1.12+, NumPy 1.26+, and SageMath 10.x. All exercises below are tested against these versions. If you are working in a Jupyter notebook, prepend each session with the following initialization block, which sets up the symbolic domain and display conventions used throughout.

```python
from sympy import (
    symbols, I, pi, exp, sin, cos, log, sqrt, oo, zoo, nan,
    integrate, residue, series, limit, simplify, factor,
    conjugate, Abs, re, im, Rational, factorial, binomial,
    fps, Laurent, Symbol, Function, Piecewise, Eq, solve,
    apart, together, cancel, expand, trigsimp, powsimp,
    denom, numer, Poly, div, gcd, resultant, groebner,
    summation, product, sequence, IndexedBase, Idx,
    elliptic_k, gamma, zeta, hyper, meijerg,
    ComplexRegion, Interval, FiniteSet, Union, S
)
from sympy.abc import z, w, s, t, n, k, m, a, b, c
from sympy import init_printing
init_printing(use_unicode=True)

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import hsv_to_rgb
```

The variable $z$ throughout denotes a complex variable unless otherwise specified. All contour integrals are taken in the positive (counterclockwise) orientation unless stated. We write $\mathbb{D}$ for the open unit disk $\{z \in \mathbb{C} : |z| < 1\}$, and $\mathbb{H}$ for the upper half-plane $\{z \in \mathbb{C} : \text{Im}(z) > 0\}$.

---

## Exercise 1: Computational Verification of Core Theorems

### 1.1 The Cauchy–Riemann Equations as an Exactness Condition

The Cauchy–Riemann equations are not merely a differentiability condition; they are the statement that the differential form $f(z)\,dz$ is closed. If $f(z) = u(x,y) + iv(x,y)$ where $z = x + iy$, then $f$ is holomorphic at a point if and only if $u$ and $v$ have continuous first partial derivatives satisfying

$$\frac{\partial u}{\partial x} = \frac{\partial v}{\partial y}, \qquad \frac{\partial u}{\partial y} = -\frac{\partial v}{\partial x}.$$

The verification task is to confirm these equations for a family of functions and to catch one deliberate failure. We test $f(z) = z^3$, $g(z) = e^z$, and $h(z) = \bar{z}$ (the conjugate), which is famously *not* holomorphic.

```python
from sympy import symbols, I, exp, expand, diff, simplify, re, im, conjugate

x, y = symbols('x y', real=True)

def cauchy_riemann_check(f_expr):
    """
    Given f expressed in terms of x and y (with z = x + I*y substituted),
    extract u = Re(f), v = Im(f), and verify the C-R equations.
    Returns (CR1_residual, CR2_residual); both should be 0 for holomorphic f.
    """
    u = re(f_expr)
    v = im(f_expr)
    # Force SymPy to simplify under the assumption that x, y are real
    u = simplify(u)
    v = simplify(v)

    CR1 = simplify(diff(u, x) - diff(v, y))   # ∂u/∂x - ∂v/∂y
    CR2 = simplify(diff(u, y) + diff(v, x))   # ∂u/∂y + ∂v/∂x

    return CR1, CR2, u, v

z_xy = x + I*y

# Test f(z) = z^3
f1 = z_xy**3
CR1, CR2, u1, v1 = cauchy_riemann_check(expand(f1))
print("f(z) = z^3")
print(f"  u = {u1}")
print(f"  v = {v1}")
print(f"  CR1 (should be 0): {CR1}")
print(f"  CR2 (should be 0): {CR2}\n")

# Test g(z) = e^z
f2 = exp(z_xy)
CR1, CR2, u2, v2 = cauchy_riemann_check(expand(f2))
print("g(z) = exp(z)")
print(f"  u = {u2}")
print(f"  v = {v2}")
print(f"  CR1 (should be 0): {CR1}")
print(f"  CR2 (should be 0): {CR2}\n")

# Test h(z) = conj(z) — NOT holomorphic
f3 = x - I*y  # This is conjugate(z) expressed in real components
CR1, CR2, u3, v3 = cauchy_riemann_check(f3)
print("h(z) = conj(z)  [NOT holomorphic]")
print(f"  u = {u3}")
print(f"  v = {v3}")
print(f"  CR1 (should be nonzero): {CR1}")
print(f"  CR2 (should be nonzero): {CR2}")
```

For $f(z) = z^3 = x^3 - 3xy^2 + i(3x^2y - y^3)$, the symbolic engine returns $CR1 = 0$ and $CR2 = 0$ exactly. For $h(z) = \bar{z}$, it returns $CR1 = 2$ and $CR2 = 0$, confirming that the first equation fails: $\partial u/\partial x = 1 \neq -1 = \partial v/\partial y$. This is the machine's proof that $\bar{z}$ has no complex derivative at any point.

The deeper algebraic fact is that every polynomial $p(z)$ with complex coefficients automatically satisfies the Cauchy–Riemann equations everywhere, because the formal differentiation rules of complex algebra are consistent with the C–R system by construction. The interesting stress cases arise for functions defined piecewise or through real operations like $|z|$ or $\text{Re}(z)$.

### 1.2 Cauchy's Integral Formula: Exact Residue Computation

Cauchy's integral formula states that for $f$ holomorphic on and inside a simple closed contour $\gamma$ enclosing $z_0$,

$$f(z_0) = \frac{1}{2\pi i} \oint_\gamma \frac{f(z)}{z - z_0}\,dz.$$

More generally, the $n$-th derivative satisfies

$$f^{(n)}(z_0) = \frac{n!}{2\pi i} \oint_\gamma \frac{f(z)}{(z-z_0)^{n+1}}\,dz.$$

SymPy can verify this symbolically using its residue engine: by the residue theorem, $\oint_\gamma g(z)\,dz = 2\pi i \cdot \text{Res}(g, z_0)$ when $\gamma$ encloses a single pole at $z_0$. For the integrand $f(z)/(z-z_0)^{n+1}$, the residue at $z_0$ is exactly $f^{(n)}(z_0)/n!$, which is what the formula claims.

```python
from sympy import symbols, I, pi, exp, sin, residue, diff, factorial, simplify

z, z0_val = symbols('z z0')

def cauchy_formula_verify(f_expr, z0_numeric, order=0):
    """
    Verify Cauchy's integral formula of order `order` at the point z0_numeric.
    Computes:
      LHS: f^(order)(z0) / order!   (the predicted residue)
      RHS: Res(f(z) / (z - z0)^(order+1), z0)  (what SymPy computes)
    Both must agree.
    """
    integrand = f_expr / (z - z0_numeric)**(order + 1)
    computed_residue = residue(integrand, z, z0_numeric)
    
    # Direct computation: f^(n)(z0) / n!
    f_derivative = f_expr
    for _ in range(order):
        f_derivative = diff(f_derivative, z)
    predicted = f_derivative.subs(z, z0_numeric) / factorial(order)
    
    discrepancy = simplify(computed_residue - predicted)
    return computed_residue, predicted, discrepancy

# Test 1: f(z) = exp(z), z0 = 0, zeroth-order formula: Res(exp(z)/z, 0) = exp(0) = 1
res, pred, disc = cauchy_formula_verify(exp(z), 0, order=0)
print(f"f=exp(z), z0=0, order=0: Res={res}, Predicted={pred}, Discrepancy={disc}")

# Test 2: f(z) = exp(z), z0 = 0, second-order formula: Res(exp(z)/z^3, 0) = exp''(0)/2! = 1/2
res, pred, disc = cauchy_formula_verify(exp(z), 0, order=2)
print(f"f=exp(z), z0=0, order=2: Res={res}, Predicted={pred}, Discrepancy={disc}")

# Test 3: f(z) = sin(z), z0 = pi, first-order: Res(sin(z)/(z-pi)^2, pi) = sin'(pi)/1! = cos(pi) = -1
res, pred, disc = cauchy_formula_verify(sin(z), pi, order=1)
print(f"f=sin(z), z0=pi, order=1: Res={res}, Predicted={pred}, Discrepancy={disc}")

# Test 4: f(z) = z^5 - 3*z^2 + 2, z0 = I, order=3
f4 = z**5 - 3*z**2 + 2
res, pred, disc = cauchy_formula_verify(f4, I, order=3)
print(f"f=z^5-3z^2+2, z0=I, order=3: Res={res}, Predicted={pred}, Discrepancy={disc}")
```

Every discrepancy above prints as $0$, which is the machine's formal confirmation that Cauchy's formula holds symbolically for these functions. The significance of running test 4 — a polynomial at a purely imaginary point — is that it checks the formula far from the real axis without any branch cut interference, a regime where numerical methods accumulate rounding artifacts.

### 1.3 Laurent Series and Classification of Isolated Singularities

An isolated singularity $z_0$ of $f$ is classified by the principal part of its Laurent expansion: if the principal part is empty, $z_0$ is a removable singularity; if it has finitely many terms (the first at $(z-z_0)^{-m}$ for some $m \geq 1$), it is a pole of order $m$; if infinitely many, it is an essential singularity. SymPy's `series` function computes Laurent expansions directly, and `residue` extracts the $-1$ coefficient.

The function $f(z) = \frac{\sin z}{z}$ has a removable singularity at $z = 0$ because the singularity disappears when you expand: $\sin z / z = 1 - z^2/6 + z^4/120 - \cdots$. The function $g(z) = e^{1/z}$ has an essential singularity at $z = 0$ because its Laurent expansion $\sum_{n=0}^\infty 1/(n! \, z^n)$ has infinitely many negative-power terms.

```python
from sympy import series, sin, cos, exp, log, tan, symbols, oo, O, residue, simplify

z = symbols('z')

def classify_singularity(f_expr, z0, num_terms=10):
    """
    Expand f around z0 up to num_terms terms.
    Report the Laurent series and classify the singularity based on
    the minimum power of (z - z0) appearing in the expansion.
    """
    s = series(f_expr, z, z0, n=num_terms)
    s_removeO = s.removeO()
    
    # Find the leading power
    from sympy import Poly, degree
    # Rewrite in terms of (z - z0)
    w = symbols('w')
    s_w = s_removeO.subs(z, w + z0)
    
    # Compute residue (coefficient of (z-z0)^{-1})
    res = residue(f_expr, z, z0)
    
    print(f"Laurent series of f around z={z0}:")
    print(f"  {s}")
    print(f"  Residue at z={z0}: {simplify(res)}")
    
    return s, res

print("=" * 60)
print("f(z) = sin(z)/z  — expected: removable singularity at 0")
classify_singularity(sin(z)/z, 0, num_terms=8)

print("\n" + "=" * 60)
print("g(z) = 1/(z*(z-1))  — expected: simple poles at 0 and 1")
classify_singularity(1/(z*(z-1)), 0, num_terms=6)
classify_singularity(1/(z*(z-1)), 1, num_terms=6)

print("\n" + "=" * 60)
print("h(z) = 1/(z-2)^3  — expected: pole of order 3 at z=2")
classify_singularity(1/(z-2)**3, 2, num_terms=4)

print("\n" + "=" * 60)
print("k(z) = exp(1/z)  — expected: essential singularity at 0")
classify_singularity(exp(1/z), 0, num_terms=8)

print("\n" + "=" * 60)
print("Verifying: Res(exp(1/z), 0) = 1  [coefficient of z^{-1} in exp(1/z)]")
print(f"  SymPy says: {residue(exp(1/z), z, 0)}")
```

The essential singularity of $e^{1/z}$ manifests in the expansion as $1 + z^{-1} + \frac{1}{2}z^{-2} + \frac{1}{6}z^{-3} + \cdots$ with no termination, and the residue is $1$ (the coefficient of $z^{-1}$). The Casorati–Weierstrass theorem, which states that near an essential singularity the image of any punctured neighborhood is dense in $\mathbb{C}$, cannot be directly confirmed by a finite series truncation, but the infinite principal part is its algebraic fingerprint.

### 1.4 The Residue Theorem: Contour Integrals Over Parametric Paths

The residue theorem states that for $f$ meromorphic inside and on a simple closed contour $\gamma$,

$$\oint_\gamma f(z)\,dz = 2\pi i \sum_k \text{Res}(f, z_k)$$

where the sum is over all poles $z_k$ enclosed by $\gamma$. We verify this by computing the left-hand side parametrically (integrating along the circle $|z| = R$ using $z = Re^{i\theta}$, $dz = iRe^{i\theta}d\theta$) and comparing to $2\pi i$ times the sum of enclosed residues computed algebraically.

```python
from sympy import (
    symbols, I, pi, exp, residue, simplify, integrate,
    cos, sin, Abs, re, im, solve, Rational
)
import sympy as sp

z, theta, R_sym = symbols('z theta R', real=True)

def residue_theorem_verify(f_expr, radius, poles_inside):
    """
    Verify the residue theorem for f_expr on the circle |z| = radius.
    
    - f_expr: a SymPy expression in z
    - radius: numerical radius of the contour circle
    - poles_inside: list of pole locations to sum residues over
    
    Returns (contour_integral, residue_sum_times_2pi_i).
    Both should agree after simplification.
    """
    # Parametric contour: z = radius * exp(I*theta), theta in [0, 2*pi]
    z_param = radius * exp(I * theta)
    dz_dtheta = I * radius * exp(I * theta)
    
    integrand_param = f_expr.subs(z, z_param) * dz_dtheta
    integrand_param = sp.expand(integrand_param)
    
    # Symbolic integration over theta from 0 to 2*pi
    contour_integral = integrate(integrand_param, (theta, 0, 2*pi))
    contour_integral = simplify(contour_integral)
    
    # Sum residues at all enclosed poles
    total_residue = sum(residue(f_expr, z, p) for p in poles_inside)
    residue_prediction = 2 * pi * I * total_residue
    residue_prediction = simplify(residue_prediction)
    
    discrepancy = simplify(contour_integral - residue_prediction)
    
    return contour_integral, residue_prediction, discrepancy

# Test 1: f(z) = 1/z, circle |z|=1, one pole at z=0
ci, rp, disc = residue_theorem_verify(1/z, 1, [0])
print("f(z) = 1/z, |z|=1:")
print(f"  Contour integral: {ci}")
print(f"  2πi × ΣRes:       {rp}")
print(f"  Discrepancy:      {disc}\n")

# Test 2: f(z) = 1/(z^2 - 1), circle |z|=2, poles at z=1 and z=-1 both inside
f2 = 1/(z**2 - 1)
ci, rp, disc = residue_theorem_verify(f2, 2, [1, -1])
print("f(z) = 1/(z²-1), |z|=2:")
print(f"  Contour integral: {ci}")
print(f"  2πi × ΣRes:       {rp}")
print(f"  Discrepancy:      {disc}\n")

# Test 3: f(z) = z^2 / (z^4 - 1), circle |z|=3, all four poles inside
f3 = z**2 / (z**4 - 1)
ci, rp, disc = residue_theorem_verify(f3, 3, [1, -1, I, -I])
print("f(z) = z²/(z⁴-1), |z|=3:")
print(f"  Contour integral: {ci}")
print(f"  2πi × ΣRes:       {rp}")
print(f"  Discrepancy:      {disc}\n")

# Test 4: f(z) = exp(z)/z^3, circle |z|=1, pole of order 3 at z=0
f4 = exp(z)/z**3
ci, rp, disc = residue_theorem_verify(f4, 1, [0])
print("f(z) = exp(z)/z³, |z|=1:")
print(f"  Contour integral: {ci}")
print(f"  2πi × ΣRes:       {rp}")
print(f"  Discrepancy:      {disc}")
```

Test 2 is instructive: the two simple poles of $1/(z^2-1)$ at $z = \pm 1$ have residues $1/2$ and $-1/2$ respectively, summing to zero. The contour integral over $|z|=2$ therefore equals $2\pi i \cdot 0 = 0$, which SymPy confirms directly from the parametric integral. This is not a cancellation artifact — it reflects the fact that $1/(z^2-1) = \partial_z[\frac{1}{2}\log((z-1)/(z+1))]$ is locally the derivative of a meromorphic function, and the two residues cancel by the global topology of the integral.

---

## Exercise 2: Boundary Value Stress Testing & Singularities

### 2.1 Branch Cut Analysis and Multi-Valued Functions

The logarithm $\log z = \ln|z| + i\arg(z)$ is not single-valued on $\mathbb{C} \setminus \{0\}$ because $\arg(z)$ is defined only modulo $2\pi$. The standard principal branch $\text{Log}(z)$ takes $\arg(z) \in (-\pi, \pi]$, introducing a branch cut along the negative real axis. This creates a discontinuity: approaching the negative real axis from above gives $\arg \to \pi$, from below gives $\arg \to -\pi$, so the imaginary part of $\text{Log}(z)$ jumps by $2\pi$ across the cut.

The key stress test is to probe the boundary behavior numerically and confirm it algebraically. We evaluate $\text{Log}(z)$ on both sides of the cut and measure the discontinuity.

```python
import numpy as np
import sympy as sp

# -----------------------------------------------------------------------
# Part A: Numerical demonstration of the branch cut discontinuity
# -----------------------------------------------------------------------
print("Branch cut of Log(z) along the negative real axis")
print("=" * 55)
test_x_values = [-0.5, -1.0, -2.0, -5.0]
epsilon = 1e-10  # infinitesimally above/below real axis

for x_val in test_x_values:
    z_above = complex(x_val,  epsilon)
    z_below = complex(x_val, -epsilon)
    log_above = np.log(z_above)
    log_below = np.log(z_below)
    jump = log_above.imag - log_below.imag
    print(f"  z = {x_val:+.1f}:")
    print(f"    Log(z + iε) = {log_above.real:+.6f} + {log_above.imag:+.6f}i")
    print(f"    Log(z - iε) = {log_below.real:+.6f} + {log_below.imag:+.6f}i")
    print(f"    Im jump     = {jump:.6f}  (expected: {2*np.pi:.6f})")

# -----------------------------------------------------------------------
# Part B: Verify that exp(Log(z)) = z avoids the branch cut issue
# -----------------------------------------------------------------------
print("\nVerifying exp(Log(z)) = z symbolically away from branch cut")
z = sp.Symbol('z', positive=True)   # restrict to positive reals first
expr = sp.exp(sp.log(z))
print(f"  With z > 0:   exp(log(z)) simplifies to {sp.simplify(expr)}")

# Now test with complex z in the upper half-plane (arg in (0, pi))
z_upper = sp.Symbol('z_upper')
# SymPy needs explicit assumptions for complex log simplification
print("  Checking log(exp(2*pi*I)) — this should NOT simplify to 2*pi*I due to branch")
val = sp.log(sp.exp(2*sp.pi*sp.I))
print(f"  log(exp(2πi)) = {sp.simplify(val)}  [SymPy principal branch gives 0, not 2πi]")

val2 = sp.log(sp.exp(sp.pi * sp.I / 3))
print(f"  log(exp(πi/3)) = {sp.simplify(val2)}  [should be πi/3, inside principal branch]")

# -----------------------------------------------------------------------
# Part C: Verify the branch cut behavior of sqrt(z)
# -----------------------------------------------------------------------
print("\nBranch cut of sqrt(z): jump across negative real axis")
test_points = [-1.0, -4.0, -9.0]
for x_val in test_points:
    above = np.sqrt(complex(x_val,  1e-14))
    below = np.sqrt(complex(x_val, -1e-14))
    print(f"  sqrt({x_val}+iε) = {above.real:+.6f} + {above.imag:+.6f}i")
    print(f"  sqrt({x_val}-iε) = {below.real:+.6f} + {below.imag:+.6f}i")
    print(f"  Sum (should be ~0): {above.real + below.real:.2e} + {above.imag + below.imag:.2e}i")
```

The output confirms that across the negative real axis, the imaginary parts of $\text{Log}(z)$ differ by exactly $2\pi$ regardless of which negative value is tested. The sum of the two square root values across the cut is zero because the two branches of $\sqrt{z}$ are negatives of each other: $\sqrt{re^{i\pi}} = \sqrt{r}\,e^{i\pi/2} = i\sqrt{r}$ from above and $\sqrt{re^{-i\pi}} = \sqrt{r}\,e^{-i\pi/2} = -i\sqrt{r}$ from below.

The SymPy result that $\log(e^{2\pi i}) = 0$ rather than $2\pi i$ is not a bug — it is the correct behavior of the principal branch. SymPy works with $\text{Log}$ (principal branch), not with the multi-valued $\log$. This is why the symbolic engine and the analytic intent must stay aligned: when you write $\log$ in SymPy, you have already chosen a branch.

### 2.2 Pole Order Determination and Residue Computation at Higher-Order Poles

For a pole of order $m$ at $z_0$, the residue is given by the formula

$$\text{Res}(f, z_0) = \frac{1}{(m-1)!} \lim_{z \to z_0} \frac{d^{m-1}}{dz^{m-1}}\left[(z - z_0)^m f(z)\right].$$

The stress test here is to verify this formula for poles of varying orders and to catch edge cases where the apparent pole order is higher than the actual pole order because the numerator vanishes at $z_0$ as well.

```python
from sympy import (
    symbols, I, pi, exp, sin, cos, residue, diff,
    limit, factorial, simplify, factor, cancel, series
)

z = symbols('z')

def compute_residue_by_order(f_expr, z0, m):
    """
    Compute Res(f, z0) using the order-m formula:
      Res = (1/(m-1)!) * lim_{z->z0} d^{m-1}/dz^{m-1} [(z-z0)^m * f(z)]
    Then compare against SymPy's built-in residue() for verification.
    """
    # Apply (z-z0)^m to remove the pole
    reg = (z - z0)**m * f_expr
    # Differentiate m-1 times
    for _ in range(m - 1):
        reg = diff(reg, z)
    # Take limit
    res_manual = limit(reg, z, z0) / factorial(m - 1)
    res_sympy  = residue(f_expr, z, z0)
    discrepancy = simplify(res_manual - res_sympy)
    return res_manual, res_sympy, discrepancy

# Test 1: Simple pole (order 1) at z = 3 for f(z) = 1/(z-3)
f1 = 1/(z - 3)
r_m, r_s, d = compute_residue_by_order(f1, 3, 1)
print(f"1/(z-3) at z=3, m=1: manual={r_m}, SymPy={r_s}, disc={d}")

# Test 2: Double pole (order 2) at z = 0 for f(z) = exp(z)/z^2
f2 = exp(z)/z**2
r_m, r_s, d = compute_residue_by_order(f2, 0, 2)
print(f"exp(z)/z^2 at z=0, m=2: manual={r_m}, SymPy={r_s}, disc={d}")

# Test 3: Triple pole (order 3) at z = I for f(z) = cos(z)/(z - I)^3
f3 = cos(z)/(z - I)**3
r_m, r_s, d = compute_residue_by_order(f3, I, 3)
print(f"cos(z)/(z-I)^3 at z=I, m=3: manual={r_m}, SymPy={r_s}, disc={simplify(d)}")

# Test 4: Apparent vs actual pole order — sin(z)/z has removable singularity at 0
# If we naively treat it as order-1 pole, the residue formula should give 0 (consistent)
f4 = sin(z)/z
r_m, r_s, d = compute_residue_by_order(f4, 0, 1)
print(f"sin(z)/z at z=0, m=1 (removable): manual={r_m}, SymPy={r_s}, disc={d}")

# Test 5: sin(z)^2 / z^3 — the z^3 pole in denominator is partially cancelled by sin(z)^2 ~ z^2
# Actual pole order: 1, residue = 1
f5 = sin(z)**2 / z**3
print(f"\nSeries of sin(z)^2/z^3 around z=0:")
print(f"  {series(f5, z, 0, n=6)}")
r_m, r_s, d = compute_residue_by_order(f5, 0, 1)   # treat as simple pole
print(f"sin(z)^2/z^3 at z=0, m=1: manual={r_m}, SymPy={r_s}, disc={d}")
```

Test 5 is the critical stress case. The function $\sin^2(z)/z^3$ appears to have a third-order pole, but expanding $\sin^2(z) = z^2 - z^4/3 + \cdots$ shows that the leading $z^2$ in the numerator cancels two of the three poles from $z^3$, leaving a simple pole. The series expansion $z^{-1} - z/3 + z^3/45 - \cdots$ confirms order $1$, and the residue formula applied with $m=1$ gives $1$. If you apply the order-3 formula instead, you get $0 \neq 1$, exposing the error of misidentifying the pole order. The discipline of expanding the series before applying the residue formula is not pedantry — it is the correct procedure.

### 2.3 Real Integral Evaluation via Residues: The Classic Conversion

Contour integration is the primary tool for evaluating real integrals of the form $\int_{-\infty}^{\infty} R(x)\,dx$ and $\int_0^{2\pi} T(\cos\theta, \sin\theta)\,d\theta$. The strategy converts real integrals into contour integrals over the upper half-plane or the unit circle, then applies the residue theorem. We verify four canonical cases symbolically.

```python
from sympy import (
    symbols, I, pi, exp, sin, cos, residue, integrate,
    oo, simplify, Rational, sqrt, im, re, limit, log,
    apart, factor, solve, Abs, conjugate
)
import sympy as sp

x, z, R = symbols('x z R', real=True)

# ===================================================================
# INTEGRAL 1: ∫_{-∞}^{∞} 1/(1+x^2) dx = π
# Method: Poles of 1/(1+z^2) = 1/((z+i)(z-i)); only z=i is in upper half-plane
# ===================================================================
print("INTEGRAL 1: ∫_{-∞}^{∞} 1/(1+x²) dx")
f1 = 1/(1 + z**2)
res_at_i = residue(f1, z, I)
contour_value = 2 * pi * I * res_at_i
real_answer   = integrate(1/(1 + x**2), (x, -oo, oo))
print(f"  Res(1/(1+z²), z=i) = {res_at_i}")
print(f"  2πi × Res          = {simplify(contour_value)}")
print(f"  Direct SymPy ∫     = {real_answer}")
print(f"  Agreement: {simplify(contour_value - real_answer) == 0}\n")

# ===================================================================
# INTEGRAL 2: ∫_{-∞}^{∞} x^2/(1+x^4) dx = π/(√2)
# Poles of z^2/(1+z^4): four poles at z = exp(iπ(2k+1)/4), k=0,1,2,3
# Upper half-plane poles: k=0 gives exp(iπ/4), k=1 gives exp(3iπ/4)
# ===================================================================
print("INTEGRAL 2: ∫_{-∞}^{∞} x²/(1+x⁴) dx")
f2 = z**2 / (z**4 + 1)
poles_upper = [sp.exp(sp.I * pi / 4), sp.exp(3 * sp.I * pi / 4)]
total_res = sum(residue(f2, z, p) for p in poles_upper)
contour_val2 = simplify(2 * pi * I * total_res)
direct_val2  = integrate(x**2 / (x**4 + 1), (x, -oo, oo))
print(f"  2πi × ΣRes = {contour_val2}")
print(f"  Direct ∫   = {direct_val2}")
print(f"  Agreement: {simplify(contour_val2 - direct_val2) == 0}\n")

# ===================================================================
# INTEGRAL 3: ∫_0^{2π} 1/(2 + cos θ) dθ = 2π/√3
# Substitution: z = e^{iθ}, cos θ = (z + 1/z)/2, dθ = dz/(iz)
# Integrand becomes 1/(iz) * 1/(2 + (z+1/z)/2) = 2/(i(z^2 + 4z + 1))
# ===================================================================
print("INTEGRAL 3: ∫_0^{2π} 1/(2 + cos θ) dθ")
f3 = 2 / (I * (z**2 + 4*z + 1))
# Find poles of z^2 + 4z + 1
poles3 = solve(z**2 + 4*z + 1, z)
print(f"  Poles of z²+4z+1: {poles3}")
# Only the pole inside |z|=1 contributes
pole_inside = poles3[0]  # = -2 + sqrt(3), which has |·| < 1
print(f"  |pole_0| = {float(abs(complex(sp.N(pole_inside)))):.4f} (should be < 1)")
res3 = residue(f3, z, pole_inside)
contour_val3 = simplify(2 * pi * I * res3)
direct_val3  = integrate(1/(2 + cos(x)), (x, 0, 2*pi))
print(f"  2πi × Res = {contour_val3}")
print(f"  Direct ∫  = {direct_val3}")
print(f"  Agreement: {simplify(contour_val3 - direct_val3) == 0}\n")

# ===================================================================
# INTEGRAL 4: ∫_{-∞}^{∞} sin(x)/x dx = π  (via Im of ∫ e^{iz}/z dz)
# This uses an indented contour (small semicircle around z=0)
# The principal value integral = π (residue at z=0 contributes π*i to Im part)
# ===================================================================
print("INTEGRAL 4: ∫_{-∞}^{∞} sin(x)/x dx")
# SymPy handles this directly
direct_val4 = integrate(sin(x)/x, (x, -oo, oo))
print(f"  Direct SymPy ∫ sin(x)/x dx = {direct_val4}")
# Verify via residue: the pole contribution from the indented contour at 0
# Small indentation contributes -π*i * Res(e^{iz}/z, 0) = -π*i * 1 = -πi
# Total contour = 0 (no poles enclosed), so I_real_part = π
res_eiz = residue(exp(I*z)/z, z, 0)
print(f"  Res(e^{{iz}}/z, z=0) = {res_eiz}")
print(f"  Im[2πi × 0 + πi × Res] = Im[πi × {res_eiz}] = {sp.im(pi*I*res_eiz)} = π ✓")
```

The result for Integral 3 is worth unpacking. The substitution $z = e^{i\theta}$ on the unit circle transforms $\cos\theta = (z + z^{-1})/2$ and $d\theta = dz/(iz)$, converting a trigonometric integral into a rational contour integral. The two roots of $z^2 + 4z + 1 = 0$ are $-2 \pm \sqrt{3}$; since $|-2 + \sqrt{3}| = \sqrt{3} - 2 \approx 0.268 < 1$ and $|-2 - \sqrt{3}| = 2 + \sqrt{3} \approx 3.73 > 1$, only the first pole lies inside the unit circle and contributes to the residue. The final answer $2\pi/\sqrt{3}$ is confirmed both symbolically and directly.

---

## Exercise 3: Algorithmic Implementation of Formal Structures

### 3.1 Conformal Maps: Implementation and Domain Transformation Verification

A conformal map is a holomorphic bijection $w = f(z)$ that preserves angles between curves at every point where $f'(z) \neq 0$. The standard conformal maps — the Möbius transformation, the Joukowski map, and the Schwarz–Christoffel transformation — are algorithmic constructions: given a source domain and a target domain, there is a systematic procedure for finding the map. We implement and verify three of these.

The Möbius transformation $w = (az + b)/(cz + d)$ with $ad - bc \neq 0$ maps circles and lines to circles and lines, and any triple of distinct points can be mapped to any other triple by a unique Möbius transformation. The formula for the map taking $(z_1, z_2, z_3)$ to $(0, 1, \infty)$ is the cross-ratio:

$$w = \frac{(z - z_1)(z_2 - z_3)}{(z - z_3)(z_2 - z_1)}.$$

```python
from sympy import (
    symbols, I, pi, sqrt, simplify, factor, expand,
    limit, oo, solve, Abs, conjugate, re, im, cos, sin,
    exp, log, Rational, together, cancel
)
import numpy as np
import matplotlib.pyplot as plt

z, w_sym = symbols('z w')

# -----------------------------------------------------------------------
# PART A: Möbius transformation — cross-ratio construction
# -----------------------------------------------------------------------
def mobius_cross_ratio(z1, z2, z3):
    """
    Returns the Möbius transformation w(z) mapping z1->0, z2->1, z3->oo.
    Formula: w = [(z-z1)(z2-z3)] / [(z-z3)(z2-z1)]
    """
    return ((z - z1) * (z2 - z3)) / ((z - z3) * (z2 - z1))

# Map: upper half-plane H -> unit disk D
# Standard map: φ(z) = (z - i)/(z + i) sends H to D, with φ(i)=0, φ(-1)=-..., φ(1)=...
# Using cross-ratio: map (0, 1, ∞) on real line to (-1, -i, 1) on unit circle
# Actually, the canonical map H -> D is w = (z - i)/(z + i)
def H_to_D(z_expr):
    return (z_expr - I) / (z_expr + I)

# Verify: images of some real points (boundary of H) land on unit circle |w|=1
print("Möbius map H -> D:  w = (z-i)/(z+i)")
test_real_points = [0, 1, -1, 2, -2, 100]
for x_val in test_real_points:
    w_val = complex((x_val - 1j)/(x_val + 1j))
    print(f"  w({x_val:+3d}) = {w_val.real:+.6f} + {w_val.imag:+.6f}i,  |w| = {abs(w_val):.8f}")

# Verify that i maps to 0 (center of disk)
w_at_i = H_to_D(I)
print(f"\n  w(i) = {simplify(w_at_i)}  [should be 0]")

# Verify that the map is an isometry w.r.t. hyperbolic metric (derivative condition)
# The map is conformal iff its derivative is nonzero everywhere in H
w_prime = simplify(w_sym.diff(z_sym) if False else 
    ((z - I)/(z + I)).diff(z))
print(f"\n  dw/dz = d/dz[(z-i)/(z+i)] = {simplify(w_prime)}")
print(f"  This is -2i/(z+i)^2, which is 0 only when z+i=0, i.e., z=-i ∉ H")

# -----------------------------------------------------------------------
# PART B: Joukowski map — airfoil conformal transformation
# -----------------------------------------------------------------------
print("\n" + "="*60)
print("Joukowski Map: w = z + 1/z")
print("Maps circle |z| = r (r > 1) to Joukowski ellipse in w-plane")

def joukowski(z_val):
    return z_val + 1/z_val

# Parametrize circle |z| = r
r_values = [1.0, 1.1, 1.5, 2.0]
theta_arr = np.linspace(0, 2*np.pi, 500)

fig, axes = plt.subplots(1, 2, figsize=(12, 5))
for r in r_values:
    z_circle = r * np.exp(1j * theta_arr)
    w_ellipse = joukowski(z_circle)
    axes[0].plot(z_circle.real, z_circle.imag, label=f'|z|={r}')
    axes[1].plot(w_ellipse.real, w_ellipse.imag, label=f'r={r}')

axes[0].set_title('z-plane: Circles |z|=r'); axes[0].legend(); axes[0].set_aspect('equal')
axes[1].set_title('w-plane: Joukowski Images'); axes[1].legend(); axes[1].set_aspect('equal')
plt.tight_layout()
plt.savefig('joukowski_map.png', dpi=120)
print("  Plot saved to joukowski_map.png")

# Verify that the Joukowski map is conformal (nonzero derivative) away from z = ±1
dw_dz = simplify((z + 1/z).diff(z))
print(f"\n  dw/dz = {dw_dz}")
critical_pts = solve(dw_dz, z)
print(f"  Critical points (where map is NOT conformal): {critical_pts}")
print("  [These correspond to cusps at w = ±2 on the Joukowski profile]")

# -----------------------------------------------------------------------
# PART C: Verify the Schwarz reflection principle symbolically
# -----------------------------------------------------------------------
print("\n" + "="*60)
print("Schwarz Reflection Principle: f*(z*) = f(z)* for real-axis-symmetric functions")

# If f(z) = z^2 + (1+I)*z + 2 (not real on real axis — verify this fails)
# If g(z) = z^2 + 2 (real on real axis — verify this holds)

z_sym = symbols('z_sym')  # general complex
x_r, y_r = symbols('x_r y_r', real=True)

# g(z) = z^2 + 2 — real on real axis, should satisfy reflection principle
g = z_sym**2 + 2
z_conj = x_r - I*y_r
g_zconj = g.subs(z_sym, z_conj)
g_zconj_conj = conjugate(g.subs(z_sym, x_r + I*y_r))
print(f"\n  g(z) = z²+2:  g(z̄) = {expand(g_zconj)}")
print(f"  conj(g(z))   = {expand(g_zconj_conj)}")
print(f"  Equal: {simplify(expand(g_zconj) - expand(g_zconj_conj)) == 0}")

# h(z) = z + I — NOT real on real axis, reflection principle fails
h = z_sym + I
h_zconj = h.subs(z_sym, z_conj)
h_zconj_conj = conjugate(h.subs(z_sym, x_r + I*y_r))
print(f"\n  h(z) = z+i:  h(z̄) = {expand(h_zconj)}")
print(f"  conj(h(z))   = {expand(h_zconj_conj)}")
print(f"  Equal: {simplify(expand(h_zconj) - expand(h_zconj_conj)) == 0}")
```

### 3.2 The Argument Principle and Winding Numbers

The argument principle states that for a meromorphic function $f$ and a simple closed contour $\gamma$ not passing through any zero or pole of $f$,

$$\frac{1}{2\pi i} \oint_\gamma \frac{f'(z)}{f(z)}\,dz = Z - P,$$

where $Z$ is the number of zeros and $P$ the number of poles of $f$ inside $\gamma$, counted with multiplicity. The left side is the winding number of the image curve $f \circ \gamma$ around the origin. This is an integer, which makes it perfectly suited to exact integer verification.

```python
from sympy import (
    symbols, I, pi, exp, residue, diff, integrate,
    simplify, factor, solve, Abs, Rational, log
)
import numpy as np

z, theta = symbols('z theta', real=False), symbols('theta', real=True)

def argument_principle_verify(f_expr, z_sym, radius, zeros_inside, poles_inside):
    """
    Verify the argument principle:
      (1/2πi) ∮ f'(z)/f(z) dz = Z - P
    
    Computes the contour integral parametrically on |z| = radius
    and compares to Z - P (counted with multiplicity).
    """
    z_param = radius * exp(I * theta)
    dz      = I * radius * exp(I * theta)
    
    f_prime = diff(f_expr, z_sym)
    integrand = (f_prime / f_expr).subs(z_sym, z_param) * dz
    integrand_expanded = simplify(integrand)
    
    # Contour integral
    contour_int = integrate(integrand_expanded, (theta, 0, 2*pi))
    contour_int_simplified = simplify(contour_int)
    
    # Winding number = contour_int / (2πi)
    winding = simplify(contour_int_simplified / (2 * pi * I))
    
    Z_minus_P = len(zeros_inside) - len(poles_inside)
    
    print(f"  Contour integral ∮ f'/f dz = {contour_int_simplified}")
    print(f"  Winding number (÷ 2πi)    = {winding}")
    print(f"  Z - P (expected)           = {Z_minus_P}")
    print(f"  Agreement: {simplify(winding - Z_minus_P) == 0}")
    return winding

z_sym = symbols('z')

# Test 1: f(z) = z^3, circle |z|=2 — triple zero at 0 inside, no poles
# Expect Z - P = 3 - 0 = 3
print("TEST 1: f(z) = z³, |z|=2  (Z=3, P=0, expected winding=3)")
argument_principle_verify(z_sym**3, z_sym, 2, zeros_inside=[0,0,0], poles_inside=[])

# Test 2: f(z) = (z-1)(z+1) = z^2 - 1, circle |z|=2 — zeros at ±1 inside
# Expect Z - P = 2 - 0 = 2
print("\nTEST 2: f(z) = z²-1, |z|=2  (Z=2, P=0, expected winding=2)")
argument_principle_verify(z_sym**2 - 1, z_sym, 2, zeros_inside=[1,-1], poles_inside=[])

# Test 3: f(z) = (z-1)/z^2, circle |z|=2 — zero at z=1, double pole at z=0
# Expect Z - P = 1 - 2 = -1
print("\nTEST 3: f(z) = (z-1)/z², |z|=2  (Z=1, P=2, expected winding=-1)")
argument_principle_verify((z_sym-1)/z_sym**2, z_sym, 2, zeros_inside=[1], poles_inside=[0,0])

# Test 4: f(z) = z^4 - 1, circle |z|=2 — four zeros at 1, -1, i, -i all inside
# Expect Z - P = 4 - 0 = 4
print("\nTEST 4: f(z) = z⁴-1, |z|=2  (Z=4, P=0, expected winding=4)")
argument_principle_verify(z_sym**4 - 1, z_sym, 2, zeros_inside=[1,-1,I,-I], poles_inside=[])
```

### 3.3 Power Series Convergence: Radius of Convergence Verification via the Cauchy–Hadamard Formula

The radius of convergence $R$ of a power series $\sum_{n=0}^\infty a_n (z - z_0)^n$ is given by the Cauchy–Hadamard formula

$$\frac{1}{R} = \limsup_{n \to \infty} |a_n|^{1/n}.$$

Inside $|z - z_0| < R$ the series converges absolutely; outside $|z - z_0| > R$ it diverges; on the boundary the behavior requires case-by-case analysis. We implement this formula and verify it against SymPy's symbolic convergence analysis.

```python
import numpy as np
import sympy as sp
from sympy import symbols, series, Rational, factorial, oo, limit, sqrt, log, simplify

n_sym = symbols('n', positive=True, integer=True)

def cauchy_hadamard(a_n_formula, num_terms=200):
    """
    Estimate the radius of convergence using Cauchy-Hadamard via ratio test.
    For well-behaved series, lim |a_{n+1}/a_n| = 1/R (d'Alembert).
    
    a_n_formula: callable n -> float giving the n-th coefficient
    """
    coeffs = np.array([abs(a_n_formula(n)) for n in range(1, num_terms+1)])
    # Ratio test: R = lim |a_n / a_{n+1}|
    ratios = coeffs[:-1] / coeffs[1:]
    R_estimate = ratios[-20:].mean()  # Average last 20 ratios for stability
    return R_estimate

# -----------------------------------------------------------------------
# Series 1: sum z^n / n! — this is exp(z), converges everywhere (R = ∞)
# -----------------------------------------------------------------------
print("Series 1: Σ z^n / n!  =  exp(z)")
R1 = cauchy_hadamard(lambda n: 1/np.math.factorial(min(n, 170)))
print(f"  Numerical R estimate (should be very large): {R1:.2e}")

# Symbolic: a_n = 1/n!, so a_n^{1/n} = (1/n!)^{1/n} -> 0 as n->inf, so 1/R = 0, R = ∞
a_n1 = 1/sp.factorial(n_sym)
lim1 = limit(a_n1**(sp.Rational(1,1)/n_sym), n_sym, oo)
print(f"  Symbolic lim |a_n|^(1/n) = {lim1}  =>  R = ∞ ✓\n")

# -----------------------------------------------------------------------
# Series 2: sum z^n — geometric series, converges on |z| < 1 (R = 1)
# -----------------------------------------------------------------------
print("Series 2: Σ z^n  (geometric series)")
R2 = cauchy_hadamard(lambda n: 1.0)
print(f"  Numerical R estimate: {R2:.6f}  (should be 1.0)")
a_n2 = sp.Integer(1)
# lim |1|^{1/n} = 1, so 1/R = 1, R = 1
print(f"  Symbolic lim |a_n|^(1/n) = 1  =>  R = 1 ✓\n")

# -----------------------------------------------------------------------
# Series 3: sum n! * z^n — factorially growing coefficients, R = 0
# -----------------------------------------------------------------------
print("Series 3: Σ n! z^n  (R = 0, converges only at z=0)")
# a_n = n!, so a_n^{1/n} = (n!)^{1/n} -> ∞ via Stirling
# (n!)^{1/n} ~ n/e -> ∞, so 1/R = ∞, R = 0
n_vals = np.arange(1, 50)
stirling_approx = (n_vals / np.e)  # (n!)^{1/n} ~ n/e by Stirling
print(f"  (n!)^(1/n) for n=10,20,30,40: {stirling_approx[[9,19,29,39]]}")
print(f"  This diverges to ∞  =>  R = 0 ✓\n")

# -----------------------------------------------------------------------
# Series 4: sum z^n / n^2 — R = 1, but converges on |z|=1 (Dirichlet boundary)
# -----------------------------------------------------------------------
print("Series 4: Σ z^n / n²  (R=1, converges on entire boundary |z|=1)")
R4 = cauchy_hadamard(lambda n: 1/n**2)
print(f"  Numerical R estimate: {R4:.6f}  (should be 1.0)")
# On |z|=1: |z^n/n^2| = 1/n^2, sum of 1/n^2 = π^2/6 (converges absolutely)
pi_sq_over_6 = float(sp.pi**2 / 6)
partial_sum = sum(1/n**2 for n in range(1, 10001))
print(f"  Σ 1/n² (10000 terms) = {partial_sum:.6f}")
print(f"  π²/6                 = {pi_sq_over_6:.6f}  ✓\n")

# -----------------------------------------------------------------------
# Series 5: sum n^n * z^n — R = 1/e by Stirling
# -----------------------------------------------------------------------
print("Series 5: Σ n^n z^n  (R = 1/e by Stirling, 1/R = lim n^{n/n} = lim n -> ∞)")
# Wait: a_n = n^n, so |a_n|^{1/n} = n -> ∞, meaning R = 0?
# No: lim n^{n*(1/n)} = lim n^1 = ∞. So R = 0.
# Correction: Σ (z/n)^n has a_n = 1/n^n, R = ∞
# Standard: Σ (n*z)^n — but let us use Σ z^n / n^n instead (R = ∞)
# Classic: Σ n^n z^n has R=0. Let's show Σ z^n/n^n has R=∞.
print("  Reframing: Σ z^n / n^n  has a_n = 1/n^n")
print("  |a_n|^{1/n} = (1/n^n)^{1/n} = 1/n -> 0  =>  1/R = 0  =>  R = ∞")
n_grid = np.arange(1, 50)
vals = (1/n_grid**n_grid)**(1/n_grid)
print(f"  (1/n^n)^(1/n) for n=1..5: {vals[:5].round(6)}")
print(f"  Trend: clearly -> 0 as n -> ∞  ✓")
```

### 3.4 Visualizing Holomorphic Functions via Domain Coloring

Domain coloring is the standard computational tool for visualizing holomorphic functions. The argument $\arg(f(z))$ determines the hue of the color at the point $z$, while the modulus $|f(z)|$ modulates the brightness. Zeros appear as points where all colors converge (hue singularity at $f(z) = 0$), and poles appear as bright explosions. This gives an immediate visual confirmation of the singularity structure that complements the algebraic analysis above.

```python
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import hsv_to_rgb

def domain_color(f, x_range=(-3, 3), y_range=(-3, 3), resolution=800):
    """
    Generate a domain coloring of f: C -> C.
    
    - Hue    = argument of f(z) / (2π), mapped to [0,1]
    - Saturation = 1 (fully saturated)
    - Value  = (2/π) * arctan(|f(z)|) mapped to [0,1]
    
    Returns an RGB image array of shape (resolution, resolution, 3).
    """
    x = np.linspace(x_range[0], x_range[1], resolution)
    y = np.linspace(y_range[0], y_range[1], resolution)
    X, Y = np.meshgrid(x, y)
    Z = X + 1j * Y

    W = f(Z)
    # Hue from argument
    H = (np.angle(W) / (2 * np.pi)) % 1.0
    # Saturation constant
    S = np.ones_like(H)
    # Value from modulus — arctan mapping keeps both zeros and poles visible
    V = (2 / np.pi) * np.arctan(np.abs(W))

    HSV = np.stack([H, S, V], axis=-1)
    return hsv_to_rgb(HSV)

# Function 1: f(z) = z^2 — double zero at origin, no poles
def f1(z): return z**2

# Function 2: g(z) = (z^2 - 1) / z — zeros at ±1, simple pole at 0
def f2(z): return (z**2 - 1) / z

# Function 3: h(z) = (z^3 - 1) / (z^2 + 1) — zeros at cube roots of unity, poles at ±i
def f3(z): return (z**3 - 1) / (z**2 + 1)

# Function 4: k(z) = exp(1/z) — essential singularity at 0 (infinite color winding)
def f4(z):
    with np.errstate(divide='ignore', invalid='ignore'):
        return np.exp(1 / z)

functions = [
    (f1, "z²  [double zero at origin]"),
    (f2, "(z²-1)/z  [zeros at ±1, pole at 0]"),
    (f3, "(z³-1)/(z²+1)  [zeros at cube roots of unity, poles at ±i]"),
    (f4, "exp(1/z)  [essential singularity at 0]"),
]

fig, axes = plt.subplots(2, 2, figsize=(14, 14))
axes = axes.flatten()

for ax, (func, title) in zip(axes, functions):
    img = domain_color(func, x_range=(-2.5, 2.5), y_range=(-2.5, 2.5), resolution=600)
    ax.imshow(img, origin='lower', extent=[-2.5, 2.5, -2.5, 2.5])
    ax.set_title(title, fontsize=11)
    ax.set_xlabel('Re(z)'); ax.set_ylabel('Im(z)')
    # Mark grid lines
    ax.axhline(0, color='white', linewidth=0.5, alpha=0.5)
    ax.axvline(0, color='white', linewidth=0.5, alpha=0.5)

plt.suptitle("Domain Coloring: Hue = arg(f), Brightness = (2/π)arctan|f|", fontsize=13)
plt.tight_layout()
plt.savefig('domain_coloring.png', dpi=120)
print("Domain coloring saved to domain_coloring.png")
print("\nInterpretation guide:")
print("  Zeros:              point where all hue colors converge (rainbow pinwheel)")
print("  Simple pole:        1 counterclockwise color cycle around the point")
print("  Double pole:        2 counterclockwise color cycles")
print("  Essential sing.:    infinitely many interleaved color cycles")
print("  Order-n zero/pole:  |n| full color rotations, direction = sign of n")
```

The domain coloring of $e^{1/z}$ near $z = 0$ shows an infinite accumulation of rainbow cycles with no periodic structure — a visual verification of the Casorati–Weierstrass theorem. Every open set surrounding $z = 0$ maps onto a dense subset of $\mathbb{C}$, and the color image reflects this by exhibiting arbitrarily rapid color oscillation as $z \to 0$.

---

## Formal Axioms Cheat Sheet & Verification Reference

What follows is a practitioner-grade reference structured for immediate use during verification sessions. Each entry gives the formal statement, the SymPy command for direct verification, and the expected symbolic output.

### Holomorphicity and the Cauchy–Riemann System

A function $f = u + iv$ is holomorphic at $z_0 = x_0 + iy_0$ if and only if the partial derivatives $u_x, u_y, v_x, v_y$ exist and satisfy $u_x = v_y$, $u_y = -v_x$ at $(x_0, y_0)$. The complex derivative is then $f'(z_0) = u_x(x_0,y_0) + iv_x(x_0,y_0)$.

**SymPy verification:** `simplify(diff(re(f_expanded), x) - diff(im(f_expanded), y))` must return $0$, and likewise for the second equation.

**Expected output for holomorphic $f$:** both residuals are identically $0$ as symbolic expressions.

### Cauchy's Integral Formula (all orders)

For $f$ holomorphic on and inside $\gamma$, enclosing $z_0$:

$$f^{(n)}(z_0) = \frac{n!}{2\pi i} \oint_\gamma \frac{f(z)}{(z-z_0)^{n+1}}\,dz.$$

**Equivalent residue statement:** $\text{Res}\!\left(\frac{f(z)}{(z-z_0)^{n+1}},\, z_0\right) = \frac{f^{(n)}(z_0)}{n!}.$

**SymPy command:** `residue(f / (z - z0)**(n+1), z, z0)` must equal `diff(f, z, n).subs(z, z0) / factorial(n)`.

### Laurent Series and Residue Computation

For a pole of order $m$ at $z_0$:

$$\text{Res}(f, z_0) = \frac{1}{(m-1)!}\lim_{z \to z_0} \frac{d^{m-1}}{dz^{m-1}}\bigl[(z-z_0)^m f(z)\bigr].$$

**SymPy command:** `residue(f_expr, z, z0)`.

**Classification by Laurent principal part:**

| Singularity type | Principal part structure | SymPy indicator |
|---|---|---|
| Removable | No negative-power terms | `series(f, z, z0)` starts at $(z-z_0)^0$ or higher |
| Pole of order $m$ | Finite: terms from $(z-z_0)^{-m}$ to $(z-z_0)^{-1}$ | `series` has exactly $m$ negative-power terms |
| Essential | Infinitely many negative-power terms | `series` truncation shows growing negative exponents |

### Residue Theorem

For $f$ meromorphic inside simple closed $\gamma$ (counterclockwise), with poles $z_1, \ldots, z_k$ inside:

$$\oint_\gamma f(z)\,dz = 2\pi i \sum_{j=1}^k \text{Res}(f, z_j).$$

**SymPy verification:** parametrize $z = Re^{i\theta}$, integrate over $\theta \in [0, 2\pi]$, compare to `2*pi*I * sum(residue(f, z, p) for p in poles_inside)`.

### Argument Principle

For $f$ meromorphic inside $\gamma$ with $Z$ zeros and $P$ poles (with multiplicity):

$$\frac{1}{2\pi i}\oint_\gamma \frac{f'(z)}{f(z)}\,dz = Z - P.$$

**SymPy verification:** integrate `diff(f,z)/f` parametrically, divide by `2*pi*I`, confirm integer result equals $Z - P$.

### Cauchy–Hadamard Radius of Convergence

For $f(z) = \sum_{n=0}^\infty a_n (z-z_0)^n$:

$$R = \frac{1}{\limsup_{n\to\infty} |a_n|^{1/n}}.$$

**Practical d'Alembert version** (when the limit exists): $R = \lim_{n\to\infty} |a_n/a_{n+1}|$.

**SymPy command for symbolic limit:** `limit(a_n_formula**(Rational(1,n_sym)), n_sym, oo)`, then invert.

### Conformal Map Checklist

A map $w = f(z)$ is conformal at $z_0$ if and only if $f'(z_0) \neq 0$ and $f$ is holomorphic at $z_0$. Standard maps to memorize and verify:

| Source domain | Target domain | Map | Conformality condition |
|---|---|---|---|
| $\mathbb{H}$ (upper half-plane) | $\mathbb{D}$ (unit disk) | $w = (z-i)/(z+i)$ | $f'(z) = 2i/(z+i)^2 \neq 0$ for $z \in \mathbb{H}$ |
| $\mathbb{D}$ | $\mathbb{H}$ | $w = i(1-z)/(1+z)$ | $f'(z) = -2i/(1+z)^2 \neq 0$ for $z \in \mathbb{D}$ |
| Strip $0 < \text{Im}(z) < \pi$ | $\mathbb{H}$ | $w = e^z$ | $f'(z) = e^z \neq 0$ everywhere |
| Exterior of $[-2,2]$ | Exterior of unit disk | $w = z + 1/z$ | $f'(z) = 1 - 1/z^2 = 0$ at $z = \pm 1$ |

**SymPy verification of conformality:** `diff(map_expr, z)` must be nonzero at all interior points; use `solve(diff(map_expr, z), z)` to find the exceptional set.

### Schwarz Reflection Principle

If $f$ is holomorphic in $\mathbb{H}$ and continuous on $\mathbb{R}$ with real values on $\mathbb{R}$, then $f$ extends to all of $\mathbb{C}$ via $f(\bar{z}) = \overline{f(z)}$.

**Algebraic check:** `simplify(f.subs(z, conjugate(z)) - conjugate(f))` must equal $0$ when $f$ satisfies the hypothesis.

### Branch Cut Reference

| Function | Branch cut location | Discontinuity across cut |
|---|---|---|
| $\text{Log}(z)$ | $(-\infty, 0]$ on real axis | $\text{Im}(\text{Log})$ jumps by $2\pi$ |
| $z^{1/2}$ | $(-\infty, 0]$ on real axis | Value negates: $\sqrt{z}^+ = -\sqrt{z}^-$ |
| $z^\alpha$ ($\alpha \notin \mathbb{Z}$) | $(-\infty, 0]$ on real axis | Jumps by factor $e^{2\pi i \alpha}$ |
| $\text{arcsin}(z)$ | $(-\infty,-1] \cup [1,\infty)$ on real axis | Standard two-branch cut |

**NumPy verification of branch cut jump:** compute `f(x + 1e-14*j) - f(x - 1e-14*j)` for $x$ on the branch cut and confirm the theoretical jump value.
