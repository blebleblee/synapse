# Operational Verification Labs: Differential Equations

## Objective & Mathematical Computing Setup

This laboratory guide treats differential equations not as a collection of tricks for producing closed-form solutions, but as a domain where symbolic computation and formal proof can be used to verify mathematical properties with the same rigor expected in pure analysis. The practitioner goal is twofold: first, to run symbolic computation pipelines in SymPy and SageMath that confirm existence, uniqueness, and structural properties of solutions; second, to build intuition for the moments when computational answers must be validated against formal mathematical reasoning rather than accepted at face value.

The mathematical substrate of this guide is the standard theory of ordinary differential equations over $\mathbb{R}$ and $\mathbb{C}$, anchored in the Picard-Lindelöf existence and uniqueness theorem, Sturm-Liouville theory for boundary value problems, and the Frobenius method for regular singular points. Every computation you execute here is a test of a specific mathematical claim: that a computed solution satisfies an equation identically, that a Wronskian is nonzero on a given interval, that a series expansion is consistent to a given order. The code is not decoration—it is the proof artifact.

Before any exercise, verify your environment satisfies the following requirements. Python 3.11 or later is required; SymPy 1.12+ provides the symbolic ODE solver, Wronskian computation, and series expansion machinery you will use throughout. SageMath 10.x supplies desolve for independent cross-verification. NumPy handles all numerical sanity checks.

```text
python -c "import sympy; print(sympy.__version__)"
python -c "import numpy; print(numpy.__version__)"
sage --version
```

If SageMath is not available as a command-line tool, the exercises designate SageMath blocks explicitly; SymPy covers all core verification steps independently. Install dependencies with:

```text
pip install sympy numpy scipy
```

The working environment for all exercises is a plain Python 3.11 script or an interactive IPython session. No Jupyter is required, though any notebook environment runs these scripts without modification.

---

## Exercise 1: Computational Verification of Core Theorems

### 1.1 The Picard-Lindelöf Theorem and Verification of Existence and Uniqueness

The Picard-Lindelöf theorem states that for the initial value problem

$$\frac{dy}{dx} = f(x, y), \quad y(x_0) = y_0,$$

if $f$ is continuous on a rectangle $R = \{(x, y) : |x - x_0| \le a,\; |y - y_0| \le b\}$ and Lipschitz continuous in $y$ on $R$—meaning there exists $L > 0$ such that $|f(x, y_1) - f(x, y_2)| \le L|y_1 - y_2|$ for all $(x, y_1), (x, y_2) \in R$—then there exists $h > 0$ and a unique solution $y : (x_0 - h, x_0 + h) \to \mathbb{R}$ satisfying the IVP. The Lipschitz constant can be bounded above by $L = \sup_{(x,y) \in R} |\partial f / \partial y|$, so verifying the Lipschitz condition reduces to checking that this partial derivative is bounded on $R$.

The following script computes the Lipschitz constant symbolically, confirms that the partial derivative is bounded on the stated rectangle, solves the IVP symbolically, and then verifies the solution satisfies both the ODE and the initial condition by reducing the residual to zero.

```python
import sympy as sp

x, y, C1 = sp.symbols('x y C1', real=True)

# IVP: dy/dx = x*y - x, y(0) = 2
# This is linear: dy/dx = x(y - 1)
f = x * y - x

# Step 1: Verify Lipschitz condition via partial derivative in y
df_dy = sp.diff(f, y)
print("∂f/∂y =", df_dy)
# ∂f/∂y = x. On rectangle |x| ≤ a, |y - 2| ≤ b, the Lipschitz constant is L = a.
# For a = 1, L = 1. The theorem guarantees existence and uniqueness.

a_val = 1
L = a_val
print(f"Lipschitz constant on |x| ≤ {a_val}: L = {L}")

# Step 2: Solve the IVP symbolically
y_func = sp.Function('y')
ode = sp.Eq(y_func(x).diff(x), x * y_func(x) - x)
general_solution = sp.dsolve(ode, y_func(x))
print("\nGeneral solution:", general_solution)

# Apply initial condition y(0) = 2
C1_val = sp.solve(general_solution.rhs.subs(x, 0) - 2, C1)[0]
particular_solution = general_solution.rhs.subs(C1, C1_val)
print("Particular solution:", particular_solution)

# Step 3: Verify the solution satisfies the ODE identically
# Compute dy/dx and compare to f(x, y(x))
y_expr = particular_solution
dy_dx = sp.diff(y_expr, x)
rhs_substituted = f.subs(y, y_expr)

residual = sp.simplify(dy_dx - rhs_substituted)
print("\nODE residual (must be 0):", residual)

# Step 4: Verify initial condition
ic_check = sp.simplify(y_expr.subs(x, 0) - 2)
print("IC residual (must be 0):", ic_check)
```

The residual on the ODE being identically zero is the computational analogue of the proof step where you substitute the candidate solution into the equation and confirm equality in $C^1$. The symbolic simplification confirms this algebraically, not numerically. Run this script: both residuals must print as $0$.

### 1.2 Wronskian and Linear Independence Verification

For a linear second-order ODE

$$y'' + P(x) y' + Q(x) y = 0,$$

a pair of solutions $y_1, y_2$ forms a fundamental set if and only if their Wronskian

$$W(y_1, y_2)(x) = \begin{vmatrix} y_1 & y_2 \\ y_1' & y_2' \end{vmatrix} = y_1 y_2' - y_2 y_1'$$

is nonzero on the interval of interest. Abel's identity gives $W(x) = W(x_0) \exp\!\left(-\int_{x_0}^x P(t)\,dt\right)$, which means the Wronskian is either identically zero or nowhere zero on any interval where $P$ is continuous. The following script verifies this for the Euler equation $x^2 y'' - 2xy' + 2y = 0$, whose solutions are $y_1 = x$ and $y_2 = x^2$.

```python
import sympy as sp

x = sp.Symbol('x', positive=True)

# Euler equation: x^2 y'' - 2x y' + 2y = 0
# Rewrite as y'' - (2/x) y' + (2/x^2) y = 0 => P(x) = -2/x, Q(x) = 2/x^2
P = sp.Rational(-2, 1) / x
Q = sp.Rational(2, 1) / x**2

y1 = x
y2 = x**2

# Step 1: Verify both are solutions
def verify_solution(y_expr, P_coeff, Q_coeff, label):
    dy = sp.diff(y_expr, x)
    ddy = sp.diff(y_expr, x, 2)
    residual = sp.simplify(ddy + P_coeff * dy + Q_coeff * y_expr)
    print(f"  Residual for {label}: {residual}")

print("Verifying solutions to y'' + P(x)y' + Q(x)y = 0:")
verify_solution(y1, P, Q, "y1 = x")
verify_solution(y2, P, Q, "y2 = x^2")

# Step 2: Compute Wronskian directly
W_direct = sp.Matrix([[y1, y2], [sp.diff(y1, x), sp.diff(y2, x)]]).det()
W_direct_simplified = sp.simplify(W_direct)
print(f"\nDirect Wronskian W(y1, y2) = {W_direct_simplified}")

# Step 3: Verify Abel's identity: W(x) = W(x0) * exp(-integral P dx)
# W(x) = C * exp(-integral(-2/x) dx) = C * exp(2 * ln x) = C * x^2
abel_integral = sp.integrate(P, x)
abel_factor = sp.exp(-abel_integral)
print(f"Abel integrating factor (W proportional to): {sp.simplify(abel_factor)}")

# W(1) from direct computation
W_at_1 = W_direct_simplified.subs(x, 1)
W_abel = W_at_1 * abel_factor / abel_factor.subs(x, 1)
print(f"Abel's identity reconstruction of W: {sp.simplify(W_abel)}")
print(f"Consistency check (direct - Abel): {sp.simplify(W_direct_simplified - W_abel)}")
```

The direct Wronskian gives $W = x^2$, which is nonzero for $x > 0$, confirming $\{x, x^2\}$ is a fundamental set on $(0, \infty)$. Abel's identity independently predicts $W \propto x^2$, and the consistency check closes the verification loop.

### 1.3 Integrating Factor Verification for First-Order Linear Equations

A first-order linear equation $y' + P(x) y = Q(x)$ admits the integrating factor $\mu(x) = e^{\int P(x)\,dx}$, which transforms the left side into an exact derivative $(\mu y)'$. The following script verifies this for a non-trivial example, then checks that the solution reconstructed from the integrating factor is identical to `dsolve`'s output.

```python
import sympy as sp

x = sp.Symbol('x', real=True)
y_func = sp.Function('y')

# Equation: y' + (2/x) y = x^2 * cos(x)   [on x > 0]
# P(x) = 2/x, Q(x) = x^2 * cos(x)
x_sym = sp.Symbol('x', positive=True)
P_coeff = 2 / x_sym
Q_coeff = x_sym**2 * sp.cos(x_sym)

# Step 1: Compute integrating factor
mu = sp.exp(sp.integrate(P_coeff, x_sym))
mu = sp.simplify(mu)
print("Integrating factor μ(x) =", mu)
# Expected: x^2

# Step 2: Multiply through and integrate
lhs_derivative = sp.simplify(mu * Q_coeff)
print("μ(x)Q(x) =", lhs_derivative)

integral_rhs = sp.integrate(lhs_derivative, x_sym)
print("∫μ(x)Q(x) dx =", integral_rhs)

C1 = sp.Symbol('C1')
y_manual = (integral_rhs + C1) / mu
y_manual_simplified = sp.simplify(y_manual)
print("\nManual solution y(x) =", y_manual_simplified)

# Step 3: Independent verification via dsolve
ode = sp.Eq(y_func(x_sym).diff(x_sym) + P_coeff * y_func(x_sym), Q_coeff)
y_dsolve = sp.dsolve(ode, y_func(x_sym))
print("dsolve solution:       ", y_dsolve.rhs)

# Step 4: Verify they differ only by arbitrary constant convention
difference = sp.simplify(y_manual_simplified - y_dsolve.rhs)
print("\nDifference (manual - dsolve):", difference)
# Should be 0 (SymPy may absorb constant differences into C1)

# Step 5: Residual verification for the dsolve solution
y_sol = y_dsolve.rhs
residual = sp.simplify(y_sol.diff(x_sym) + P_coeff * y_sol - Q_coeff)
print("ODE residual for dsolve solution:", residual)
```

The integrating factor $\mu(x) = x^2$ converts the equation to $(x^2 y)' = x^4 \cos x$, which integrates by parts. The manual solution and the `dsolve` output must agree up to relabeling of the arbitrary constant, confirmed by the difference check.

---

## Exercise 2: Boundary Value Stress Testing & Singularities

### 2.1 Sturm-Liouville Eigenvalue Verification

The Sturm-Liouville problem

$$\frac{d}{dx}\!\left[p(x) y'\right] + q(x) y + \lambda w(x) y = 0, \quad y(a) = y(b) = 0$$

with $p(x) > 0$ and $w(x) > 0$ on $[a, b]$ has a countably infinite sequence of real eigenvalues $\lambda_1 < \lambda_2 < \cdots \to \infty$ with corresponding eigenfunctions $\phi_n$ that form a complete orthogonal set in $L^2([a, b], w)$. The classical verification target is the simplest nontrivial case: $y'' + \lambda y = 0$ on $[0, \pi]$ with $y(0) = y(\pi) = 0$. The eigenvalues are $\lambda_n = n^2$ for $n \in \mathbb{Z}_{>0}$, with eigenfunctions $\phi_n(x) = \sin(nx)$.

The following script verifies the first five eigenvalue-eigenfunction pairs, confirms orthogonality in $L^2([0, \pi])$, and checks normalization.

```python
import sympy as sp
import numpy as np

x = sp.Symbol('x', real=True)

# Sturm-Liouville: y'' + lambda * y = 0 on [0, pi], BCs y(0)=y(pi)=0
# Eigenvalues: lambda_n = n^2, eigenfunctions: phi_n = sin(n*x)

n_max = 5
eigenvalues = [n**2 for n in range(1, n_max + 1)]
eigenfunctions = [sp.sin(n * x) for n in range(1, n_max + 1)]

print("=== Eigenfunction Verification ===")
for n, (lam, phi) in enumerate(zip(eigenvalues, eigenfunctions), start=1):
    # Verify: phi'' + lambda * phi = 0
    residual = sp.simplify(phi.diff(x, 2) + lam * phi)
    bc0 = phi.subs(x, 0)
    bc_pi = sp.simplify(phi.subs(x, sp.pi))
    print(f"n={n}: λ={lam}, residual={residual}, y(0)={bc0}, y(π)={bc_pi}")

print("\n=== Orthogonality Matrix <φ_m, φ_n> on [0,π] ===")
gram = sp.zeros(n_max, n_max)
for i in range(n_max):
    for j in range(n_max):
        inner = sp.integrate(eigenfunctions[i] * eigenfunctions[j], (x, 0, sp.pi))
        gram[i, j] = sp.simplify(inner)
sp.pprint(gram)

print("\n=== Norms ||φ_n||² ===")
for n, phi in enumerate(eigenfunctions, start=1):
    norm_sq = sp.integrate(phi**2, (x, 0, sp.pi))
    print(f"  ||φ_{n}||² = {norm_sq}")
```

The Gram matrix must be diagonal with entries $\pi/2$, reflecting the orthogonality relation $\int_0^\pi \sin(mx)\sin(nx)\,dx = \frac{\pi}{2}\delta_{mn}$. Each eigenfunction residual must print as $0$, and both boundary conditions must be satisfied exactly.

### 2.2 Frobenius Method at Regular Singular Points

The equation $x^2 y'' + x p_0 y' + q_0 y = 0$ has $x = 0$ as a regular singular point when $\lim_{x\to 0} x P(x) = p_0$ and $\lim_{x\to 0} x^2 Q(x) = q_0$ are finite. The Frobenius method assumes $y = x^r \sum_{k=0}^\infty a_k x^k$ and derives the indicial equation $r(r-1) + p_0 r + q_0 = 0$. The roots $r_1, r_2$ of the indicial equation determine the structure of the two linearly independent solutions.

Consider Bessel's equation of order $\nu$:

$$x^2 y'' + x y' + (x^2 - \nu^2) y = 0.$$

Here $p_0 = 1$, $q_0 = -\nu^2$, and the indicial equation is $r^2 - \nu^2 = 0$, giving $r = \pm\nu$. For $\nu = 0$, the roots coincide, requiring a logarithmic second solution. The following script uses SymPy's series expansion to verify the Frobenius series for $J_0(x)$ to order $x^8$ against the known power series

$$J_0(x) = \sum_{m=0}^\infty \frac{(-1)^m}{(m!)^2} \left(\frac{x}{2}\right)^{2m}.$$

```python
import sympy as sp

x = sp.Symbol('x', positive=True)
y_func = sp.Function('y')

nu = 0  # Bessel equation of order 0: x^2 y'' + x y' + x^2 y = 0

# Step 1: Confirm indicial equation
r = sp.Symbol('r')
# indicial: r(r-1) + p0*r + q0 = 0, p0 = 1, q0 = -nu^2
indicial = r * (r - 1) + 1 * r + (-nu**2)
indicial_eq = sp.Eq(indicial, 0)
roots = sp.solve(indicial_eq, r)
print("Indicial equation:", indicial_eq)
print("Indicial roots:", roots)
# Both roots = 0 → expect logarithmic second solution (not needed here for J_0 primary)

# Step 2: Construct J_0(x) truncated Frobenius series to order x^8
def J0_series(x_sym, terms):
    result = sp.Integer(0)
    for m in range(terms):
        coeff = ((-1)**m) / (sp.factorial(m)**2)
        result += coeff * (x_sym / 2)**(2 * m)
    return result

J0 = J0_series(x, 5)  # terms: m = 0,1,2,3,4 → up to x^8
print("\nJ_0(x) Frobenius series (order x^8):")
sp.pprint(sp.expand(J0))

# Step 3: Verify J_0 satisfies Bessel's equation to order x^6
# (Residual will have O(x^8) terms from truncation)
J0_deriv1 = sp.diff(J0, x)
J0_deriv2 = sp.diff(J0, x, 2)
bessel_residual = x**2 * J0_deriv2 + x * J0_deriv1 + x**2 * J0
bessel_residual_expanded = sp.expand(bessel_residual)
# Collect terms and show that all coefficients through x^6 vanish
bessel_series = sp.series(bessel_residual_expanded, x, 0, 9)
print("\nBessel residual as series in x (all terms through x^8 must vanish):")
sp.pprint(bessel_series)

# Step 4: Cross-check using SymPy's built-in Bessel J_0
J0_builtin = sp.besselj(0, x)
J0_builtin_series = sp.series(J0_builtin, x, 0, 10).removeO()
J0_manual_series = sp.series(J0, x, 0, 10).removeO()
series_diff = sp.expand(J0_builtin_series - J0_manual_series)
print("\nDifference between SymPy builtin J_0 series and manual construction:")
sp.pprint(sp.series(series_diff, x, 0, 10))
```

The residual when substituted into Bessel's equation must produce zero through order $x^8$ from the five-term truncation, with the first nonzero term appearing at $x^{10}$. The difference between the manually constructed Frobenius series and SymPy's built-in `besselj(0, x)` must vanish through the computed order.

### 2.3 Blow-Up Detection and Domain of Existence

The nonlinear IVP $y' = y^2$, $y(0) = 1$ has the unique solution $y(x) = 1/(1-x)$, which blows up at $x = 1$. The Picard-Lindelöf theorem guarantees local existence but cannot a priori determine the maximal interval. This exercise verifies the blow-up analytically and tests how symbolic and numerical methods behave near the singularity.

```python
import sympy as sp
import numpy as np
from scipy.integrate import solve_ivp
import warnings

x_sym = sp.Symbol('x', real=True)
y_func = sp.Function('y')

# Step 1: Symbolic solution
ode_nonlinear = sp.Eq(y_func(x_sym).diff(x_sym), y_func(x_sym)**2)
sol = sp.dsolve(ode_nonlinear, y_func(x_sym))
print("General solution:", sol)

C1 = sp.Symbol('C1')
C1_val = sp.solve(sol.rhs.subs(x_sym, 0) - 1, C1)[0]
particular = sol.rhs.subs(C1, C1_val)
print("Particular solution y(x) =", particular)
# Expected: 1/(1 - x)

# Step 2: Verify the residual and blow-up point
residual = sp.simplify(particular.diff(x_sym) - particular**2)
print("ODE residual:", residual)

singularities = sp.singularities(particular, x_sym)
print("Singularities of y(x):", singularities)

# Step 3: Lipschitz analysis near blow-up
# f(x, y) = y^2  =>  ∂f/∂y = 2y
# Near y → ∞, the Lipschitz constant L → ∞: uniqueness theory breaks down globally.
print("\nLipschitz constant near blow-up:")
y_sym = sp.Symbol('y', real=True)
f = y_sym**2
L_expr = sp.diff(f, y_sym)
print(f"  ∂f/∂y = {L_expr} → unbounded as y → ∞")

# Step 4: Numerical integration showing blow-up
def rhs(t, y_vec):
    return [y_vec[0]**2]

x_span = (0.0, 0.999)
x_eval = np.linspace(0.0, 0.999, 500)
y0 = [1.0]

with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    sol_numerical = solve_ivp(rhs, x_span, y0, method='RK45',
                               t_eval=x_eval, rtol=1e-10, atol=1e-12,
                               dense_output=False)

# Compare numerical to analytical at several points
x_check = np.array([0.0, 0.5, 0.9, 0.99, 0.999])
print("\nNumerical vs. analytical comparison:")
print(f"{'x':>8} {'y_numerical':>18} {'y_exact':>18} {'abs_error':>18}")
for x_val in x_check:
    idx = np.argmin(np.abs(sol_numerical.t - x_val))
    if idx < len(sol_numerical.y[0]):
        y_num = sol_numerical.y[0][idx]
        y_exact = 1.0 / (1.0 - x_val)
        print(f"{x_val:>8.4f} {y_num:>18.6f} {y_exact:>18.6f} {abs(y_num - y_exact):>18.2e}")
```

This exercise makes the abstract statement of Picard-Lindelöf concrete: the theorem guarantees existence on a small interval around $x = 0$, but the maximal interval $(−\infty, 1)$ can only be determined by analyzing the solution itself. The numerical integrator loses accuracy as $x \to 1^-$ because the stiffness of the problem grows without bound, illustrating why symbolic methods are essential near singularities.

---

## Exercise 3: Algorithmic Implementation of Formal Structures

### 3.1 Implementing the Picard Iteration as a Convergent Algorithm

The constructive proof of Picard-Lindelöf builds the solution as the uniform limit of the iteration sequence

$$y_0(x) = y_0, \quad y_{n+1}(x) = y_0 + \int_{x_0}^x f(t,\, y_n(t))\,dt.$$

This is not merely a proof technique—it is a computable algorithm for constructing approximate solutions, and it converges in the sup-norm on $[x_0 - h, x_0 + h]$ for $h < 1/L$ where $L$ is the Lipschitz constant. The following implementation runs five iterations for $y' = y$, $y(0) = 1$, and verifies that each iterate equals the partial sum of $e^x$.

```python
import sympy as sp

x = sp.Symbol('x', real=True)

# IVP: y' = y, y(0) = 1
# Exact solution: e^x
# Picard iterate n should equal sum_{k=0}^{n} x^k / k!

def picard_iterate(f_expr, y_symbol, x_symbol, x0, y0, n_iterations):
    """
    Compute n_iterations steps of Picard iteration for dy/dx = f(x, y), y(x0) = y0.
    Returns list of iterates as SymPy expressions.
    """
    iterates = [sp.sympify(y0)]
    current = sp.sympify(y0)
    for k in range(n_iterations):
        integrand = f_expr.subs(y_symbol, current)
        next_iterate = y0 + sp.integrate(integrand, (x_symbol, x0, x_symbol))
        next_iterate = sp.expand(next_iterate)
        iterates.append(next_iterate)
        current = next_iterate
    return iterates

y_sym = sp.Symbol('y', real=True)
f = y_sym  # dy/dx = y

x0_val = 0
y0_val = 1
n_iter = 6

iterates = picard_iterate(f, y_sym, x, x0_val, y0_val, n_iter)

print("Picard Iterates for y' = y, y(0) = 1:")
for k, iterate in enumerate(iterates):
    expected_partial_sum = sum(x**j / sp.factorial(j) for j in range(k + 1))
    match = sp.simplify(iterate - expected_partial_sum) == 0
    print(f"  y_{k}(x) = {iterate}")
    print(f"         Expected partial sum of e^x to degree {k}: match = {match}")

# Verify convergence: compute |y_n(x) - e^x| as a series
print("\n--- Truncation Error Analysis ---")
e_x = sp.exp(x)
for k, iterate in enumerate(iterates):
    error_series = sp.series(e_x - iterate, x, 0, k + 3)
    leading_term = sp.series(e_x - iterate, x, 0, k + 3).removeO()
    print(f"  e^x - y_{k}(x) = O(x^{k+1}): first nonzero term = {sp.nsimplify(leading_term)}")
```

Each iterate $y_n(x) = \sum_{k=0}^n x^k/k!$ matches the truncated Taylor series of $e^x$ exactly, and the error is $O(x^{n+1})$. This is not a coincidence but a theorem: the Picard iterates for linear equations with polynomial coefficients reproduce the Taylor series term by term.

### 3.2 Formal Verification Structure: Encoding an ODE Solution Property in Lean 4

Lean 4 with Mathlib provides formal proof verification for mathematical claims. The following encodes the claim that if $y : \mathbb{R} \to \mathbb{R}$ satisfies $y' = ky$ and $y(0) = y_0$, then $y(x) = y_0 e^{kx}$. This requires Mathlib's `Analysis.ODE.Gronwall` and `Analysis.SpecialFunctions.ExpDeriv` libraries. The proof uses the uniqueness of solutions to linear ODEs, reducing the verification to checking that $y_0 e^{kx}$ satisfies the equation and the initial condition, then invoking the uniqueness theorem.

```lean
-- File: ODE_Verification.lean
-- Requires: Mathlib4
-- Build: lake build after adding to lakefile.lean

import Mathlib.Analysis.ODE.Gronwall
import Mathlib.Analysis.SpecialFunctions.ExpDeriv
import Mathlib.Analysis.Calculus.Deriv.Basic

open Real MeasureTheory

/-- The function f(x) = y0 * exp(k * x) satisfies the linear ODE f' = k * f
    with initial condition f(0) = y0.  -/
theorem exponential_solves_linear_ode (k y0 : ℝ) :
    let f : ℝ → ℝ := fun x => y0 * Real.exp (k * x)
    (∀ x : ℝ, HasDerivAt f (k * f x) x) ∧ f 0 = y0 := by
  constructor
  · intro x
    have hderiv : HasDerivAt (fun x => Real.exp (k * x)) (k * Real.exp (k * x)) x := by
      have := (Real.hasDerivAt_exp (k * x)).comp x
              ((hasDerivAt_id x).const_mul k)
      simp [mul_comm] at this ⊢
      exact this
    have : HasDerivAt (fun x => y0 * Real.exp (k * x)) (y0 * (k * Real.exp (k * x))) x :=
      hderiv.const_mul y0
    simp only [show y0 * (k * Real.exp (k * x)) = k * (y0 * Real.exp (k * x)) by ring]
    exact this
  · simp [Real.exp_zero]
```

This Lean proof is minimal and compilable with `lake build` against Mathlib4. It encodes two properties simultaneously: that the derivative of $y_0 e^{kx}$ at every point $x$ equals $k$ times the function value, and that the initial condition holds. The `ring` tactic closes the algebraic rearrangement $y_0(k e^{kx}) = k(y_0 e^{kx})$, and `simp [Real.exp_zero]` closes $y_0 e^0 = y_0$. This is the formal proof artifact that makes the claim machine-verifiable.

### 3.3 Phase Plane Analysis of the Van der Pol Oscillator

The Van der Pol oscillator

$$\ddot{x} - \mu(1 - x^2)\dot{x} + x = 0, \quad \mu > 0$$

is a paradigmatic nonlinear second-order ODE with a stable limit cycle. Converting to a first-order system with $\dot{x} = y$ gives

$$\dot{x} = y, \quad \dot{y} = \mu(1 - x^2)y - x.$$

The existence of the limit cycle follows from the Poincaré-Bendixson theorem: the vector field has a unique unstable equilibrium at the origin and a trapping region in the phase plane, so trajectories must converge to a closed orbit. The following script verifies the equilibrium structure symbolically and computes the Jacobian eigenvalues to confirm the origin is an unstable spiral for $\mu > 0$.

```python
import sympy as sp
import numpy as np
from scipy.integrate import solve_ivp

x_sym, y_sym, mu_sym = sp.symbols('x y mu', real=True)

# Van der Pol system
f1 = y_sym
f2 = mu_sym * (1 - x_sym**2) * y_sym - x_sym

# Step 1: Find equilibria
eq_points = sp.solve([f1, f2], [x_sym, y_sym])
print("Equilibria:", eq_points)
# Expected: (0, 0) only

# Step 2: Jacobian at equilibrium (0, 0)
F = sp.Matrix([f1, f2])
state = sp.Matrix([x_sym, y_sym])
J = F.jacobian(state)
J_at_origin = J.subs([(x_sym, 0), (y_sym, 0)])
print("\nJacobian at origin:")
sp.pprint(J_at_origin)

# Step 3: Eigenvalues as functions of mu
eigenvals = J_at_origin.eigenvals()
print("\nEigenvalues of Jacobian at origin:")
for eigval, mult in eigenvals.items():
    real_part = sp.re(eigval)
    imag_part = sp.im(eigval)
    real_simplified = sp.simplify(real_part)
    print(f"  λ = {eigval}  (Re = {real_simplified}, multiplicity = {mult})")

# Step 4: Confirm unstable for mu > 0
mu_test = sp.Symbol('mu', positive=True)
J_pos = J_at_origin.subs(mu_sym, mu_test)
eigenvals_pos = J_pos.eigenvals()
print("\nWith mu > 0, eigenvalue real parts:")
for eigval in eigenvals_pos:
    re_part = sp.simplify(sp.re(eigval.subs(mu_sym, mu_test)))
    print(f"  Re(λ) = {re_part}  → positive means unstable spiral")

# Step 5: Numerical phase portrait showing limit cycle
mu_val = 1.0

def vdp(t, state):
    x_v, y_v = state
    return [y_v, mu_val * (1 - x_v**2) * y_v - x_v]

t_span = (0, 50)
t_eval = np.linspace(0, 50, 5000)

# Two initial conditions: inside and outside the expected limit cycle
ic_inner = [0.1, 0.0]
ic_outer = [4.0, 0.0]

sol_inner = solve_ivp(vdp, t_span, ic_inner, t_eval=t_eval, rtol=1e-10, atol=1e-12)
sol_outer = solve_ivp(vdp, t_span, ic_outer, t_eval=t_eval, rtol=1e-10, atol=1e-12)

# Verify both trajectories converge to approximately the same final amplitude
late_idx = t_eval > 40
amp_inner = np.max(np.abs(sol_inner.y[0][late_idx]))
amp_outer = np.max(np.abs(sol_outer.y[0][late_idx]))
print(f"\nLimit cycle amplitude from inner IC: {amp_inner:.6f}")
print(f"Limit cycle amplitude from outer IC: {amp_outer:.6f}")
print(f"Amplitude difference (should be < 0.01): {abs(amp_inner - amp_outer):.6f}")
```

The Jacobian eigenvalues at the origin are $\lambda = \frac{\mu \pm \sqrt{\mu^2 - 4}}{2}$. For $0 < \mu < 2$ these are complex with positive real part $\mu/2 > 0$, confirming the origin is an unstable spiral. Both trajectories—one starting inside, one outside the limit cycle—converge to the same amplitude, verifying the Poincaré-Bendixson conclusion numerically.

---

## Formal Axioms Cheat Sheet & Verification Reference

The following reference collects the core theorems used throughout these exercises, states them precisely, and pairs each with the computational verification strategy its proof suggests. This is a practitioner's reference, not a glossary: each entry explains not only what the theorem says but how to operationalize it as a test.

**Picard-Lindelöf Existence and Uniqueness.** For $y' = f(x,y)$ with $f$ continuous on a closed rectangle $R$ and Lipschitz in $y$ with constant $L$, there exists a unique solution on the interval $|x - x_0| \le h := \min(a,\, b/M)$ where $M = \sup_R |f|$. The computational verification strategy is: (1) compute $L = \sup_R |\partial f/\partial y|$ symbolically; (2) solve the IVP; (3) substitute the solution back and simplify the residual to zero; (4) verify the initial condition algebraically.

$$L = \sup_{(x,y) \in R} \left|\frac{\partial f}{\partial y}\right| < \infty \implies \text{unique solution on } |x - x_0| \le \min\!\left(a,\, \frac{b}{M}\right).$$

**Abel's Identity.** If $y_1, y_2$ are solutions of $y'' + P(x)y' + Q(x)y = 0$ on an interval $I$ where $P$ is continuous, then

$$W(y_1, y_2)(x) = W(y_1, y_2)(x_0)\, \exp\!\left(-\int_{x_0}^x P(t)\,dt\right).$$

The verification strategy is to compute the Wronskian directly from the definition, compute it from Abel's formula, and confirm they are equal as symbolic expressions.

**Indicial Equation for Frobenius Method.** At a regular singular point $x = 0$ of $y'' + P(x)y' + Q(x)y = 0$, writing $p_0 = \lim_{x\to 0} xP(x)$ and $q_0 = \lim_{x\to 0} x^2 Q(x)$, the indicial equation is

$$r(r-1) + p_0 r + q_0 = 0.$$

If $r_1 - r_2 \notin \mathbb{Z}_{\ge 0}$, two Frobenius series solutions exist. If $r_1 = r_2$ or $r_1 - r_2 \in \mathbb{Z}_{>0}$, the second solution involves a logarithmic term. Verification: substitute the Frobenius series into the ODE and confirm the residual is $O(x^N)$ for a chosen truncation order $N$.

**Sturm-Liouville Orthogonality.** For the problem $-(py')' + qy = \lambda w y$ with separated boundary conditions at $a$ and $b$, eigenfunctions $\phi_m$ and $\phi_n$ corresponding to distinct eigenvalues $\lambda_m \ne \lambda_n$ satisfy

$$\int_a^b \phi_m(x)\, \phi_n(x)\, w(x)\,dx = 0.$$

Verification: compute the integral symbolically for the first $N$ pairs and confirm it equals $\|\phi_n\|^2 \delta_{mn}$.

**Picard Iteration Convergence Rate.** The $n$-th Picard iterate satisfies

$$\|y_{n+1} - y_n\|_{[x_0 - h, x_0 + h]} \le \frac{(Lh)^n}{n!} \|y_1 - y_0\|_{[x_0-h,x_0+h]},$$

so the iterate sequence converges uniformly at a rate dominated by $(Lh)^n / n!$. Verification: for the IVP $y' = y$, $y(0) = 1$, confirm that $y_n(x) = \sum_{k=0}^n x^k/k!$ and that the truncation error in the sup-norm on $[-h, h]$ decays as $(h^{n+1}/(n+1)!)$ using series comparison.

**Poincaré-Bendixson Trapping Condition.** A trajectory of $\dot{\mathbf{x}} = \mathbf{F}(\mathbf{x})$ in $\mathbb{R}^2$ that remains in a compact positively invariant region containing no equilibrium must approach a limit cycle. The verification strategy is: (1) confirm all equilibria via $\mathbf{F} = 0$; (2) classify their stability via Jacobian eigenvalues; (3) identify the trapping region (for Van der Pol, the annular region $r_1 \le \|\mathbf{x}\| \le r_2$); (4) confirm numerically that trajectories from both inside and outside converge to the same closed orbit.

**Gronwall's Inequality.** If $u : [a, b] \to \mathbb{R}$ is nonneg­ative and satisfies $u(t) \le \alpha + \int_a^t \beta(s) u(s)\,ds$ for a constant $\alpha \ge 0$ and integrable $\beta \ge 0$, then

$$u(t) \le \alpha \exp\!\left(\int_a^t \beta(s)\,ds\right).$$

This inequality underlies both the uniqueness proof in Picard-Lindelöf and continuous dependence on initial conditions. For a linear ODE with Lipschitz constant $L$, two solutions $y$ and $\tilde{y}$ starting from initial conditions $y_0$ and $\tilde{y}_0$ satisfy $|y(x) - \tilde{y}(x)| \le |y_0 - \tilde{y}_0| e^{L|x - x_0|}$. Verification: for $y' = y$ on $[0, 1]$, confirm numerically that two solutions starting at $y_0 = 1$ and $\tilde{y}_0 = 1 + \varepsilon$ differ by at most $\varepsilon e^1$ at $x = 1$, using `solve_ivp` with `rtol=1e-12`.

```python
import numpy as np
from scipy.integrate import solve_ivp

# Gronwall continuous dependence check for y' = y on [0, 1]
def linear_ode(t, y_vec):
    return [y_vec[0]]

epsilon = 1e-4
y0_base = [1.0]
y0_perturbed = [1.0 + epsilon]
t_span = (0.0, 1.0)
t_eval = np.array([1.0])

sol_base = solve_ivp(linear_ode, t_span, y0_base, t_eval=t_eval,
                      rtol=1e-12, atol=1e-14)
sol_pert = solve_ivp(linear_ode, t_span, y0_perturbed, t_eval=t_eval,
                      rtol=1e-12, atol=1e-14)

actual_diff = abs(sol_pert.y[0, 0] - sol_base.y[0, 0])
gronwall_bound = epsilon * np.exp(1.0)

print(f"Actual difference at x=1:  {actual_diff:.8e}")
print(f"Gronwall bound ε·e^1:      {gronwall_bound:.8e}")
print(f"Bound satisfied: {actual_diff <= gronwall_bound}")
```

The bound is satisfied by a factor of exactly $e$, which is tight because the Lipschitz constant of $f(x, y) = y$ is $L = 1$ and the Gronwall exponent is $e^{L \cdot 1} = e$. For a linear equation this estimate is not merely a bound but an equality, since the two solutions differ by $\varepsilon e^x$ exactly.
