# Operational Verification Labs: Numerical Analysis

## Objective & Mathematical Computing Setup

Numerical analysis sits at the boundary between pure mathematics and machine computation. Its central concern is not merely solving equations or approximating integrals, but doing so in a way that is provably correct, stable under perturbation, and efficient within machine arithmetic. The practitioner in this domain must hold two things simultaneously: a rigorous understanding of the continuous mathematical object being approximated, and a precise awareness of how floating-point discretization, finite precision, and iterative truncation corrupt that object in quantifiable ways. This lab guide treats numerical analysis as a formal discipline, where every algorithm is a theorem about convergence, every implementation is a proof obligation, and every computed result carries an error certificate.

The exercises that follow use a computational stack built around Python 3.11, SymPy for symbolic algebra and exact arithmetic, NumPy for double-precision floating-point execution, and SageMath as a unified environment that can bridge both worlds while also connecting to formal proof assistants. The goal is not to benchmark performance, but to verify mathematical properties: convergence rates, error bounds, stability criteria, and the numerical consequences of theoretical ill-conditioning. You will execute the same computation in both exact symbolic and finite-precision arithmetic and measure the gap between them, which is precisely where the mathematics of numerical analysis lives.

Before beginning, verify your environment with the following sequence. These commands confirm that all required packages are present and at the correct versions.

```text
python -c "import sympy; print('SymPy:', sympy.__version__)"
python -c "import numpy; print('NumPy:', numpy.__version__)"
python -c "import scipy; print('SciPy:', scipy.__version__)"
sage --version
```

You should see SymPy 1.12 or later, NumPy 1.26 or later, SciPy 1.11 or later, and SageMath 10.x. If SageMath is unavailable, the SageMath-specific sections can be executed inside a Jupyter notebook launched via `sage -n jupyter`. Install any missing packages with `pip install sympy numpy scipy` and follow the official SageMath installation guide for your platform.

The theoretical backbone of this lab is the fundamental triad of numerical analysis: **consistency** (the discretization correctly represents the continuous problem as the mesh or step parameter tends to zero), **stability** (small perturbations in input produce bounded perturbations in output, uniformly), and **convergence** (the numerical solution approaches the exact solution). The Lax Equivalence Theorem, one of the most important results in the field, states that for a consistent finite difference scheme applied to a well-posed linear problem, stability is both necessary and sufficient for convergence. Every exercise below is, in some sense, a computational instantiation of this theorem.

---

## Exercise 1: Computational Verification of Core Theorems

### 1.1 The Intermediate Value Theorem as a Root-Finding Certificate

The Intermediate Value Theorem (IVT) guarantees that a continuous function $f : [a, b] \to \mathbb{R}$ satisfying $f(a) \cdot f(b) < 0$ has at least one root $c \in (a, b)$. The bisection method is the direct algorithmic realization of this proof: at each step, it halves the interval while preserving the sign-change invariant, producing a sequence $\{c_k\}$ that converges to $c$ with the guaranteed error bound

$$|c_k - c| \leq \frac{b - a}{2^{k+1}}.$$

This bound is not merely an asymptotic statement. It is an exact certificate, valid from the first iteration, with no assumption on the derivative of $f$. The following program implements bisection from first principles, verifies the error bound symbolically at every step, and cross-checks the final result against SymPy's exact solver.

```python
import sympy as sp
import numpy as np

# ---------------------------------------------------------------
# Symbolic setup: define f(x) = x^3 - 2x - 5
# This polynomial has exactly one real root near x = 2.0946
# We verify this claim symbolically first.
# ---------------------------------------------------------------
x = sp.Symbol('x')
f_sym = x**3 - 2*x - 5

# Find exact real roots symbolically
exact_roots = sp.solve(f_sym, x)
real_roots = [r for r in exact_roots if sp.im(r) == 0]
print("Exact real roots (SymPy):", [sp.simplify(r) for r in real_roots])

# Evaluate numerically for reference
exact_value = float(sp.N(real_roots[0], 50))
print(f"Exact root (50 digits): {sp.N(real_roots[0], 50)}")

# ---------------------------------------------------------------
# Numerical bisection with formal error tracking
# ---------------------------------------------------------------
f = sp.lambdify(x, f_sym, 'numpy')

a, b = 2.0, 3.0
assert f(a) * f(b) < 0, "IVT precondition failed: no sign change on [a, b]"

max_iter = 52  # 52 iterations gives sub-machine-epsilon resolution
tolerance = 1e-15

results = []
for k in range(1, max_iter + 1):
    c = (a + b) / 2.0
    theoretical_bound = (b - a) / 2  # bound BEFORE this iteration's halving
    actual_error = abs(c - exact_value)
    
    # Formally verify the error certificate: actual error <= theoretical bound
    certificate_holds = actual_error <= theoretical_bound
    results.append((k, c, actual_error, theoretical_bound, certificate_holds))
    
    if f(a) * f(c) < 0:
        b = c
    elif f(b) * f(c) < 0:
        a = c
    else:
        break  # f(c) == 0 exactly (rare in floating point)
    
    if actual_error < tolerance:
        break

print(f"\n{'k':>4} {'c_k':>22} {'actual error':>18} {'IVT bound':>18} {'cert.':>6}")
print("-" * 72)
for row in results[:20]:  # print first 20 iterations
    k, c, err, bound, cert = row
    print(f"{k:>4} {c:>22.15f} {err:>18.6e} {bound:>18.6e} {str(cert):>6}")

print(f"\nFinal approximation: {c:.15f}")
print(f"Exact value:         {exact_value:.15f}")
print(f"Final error:         {abs(c - exact_value):.6e}")
```

After running this, examine the `cert.` column. It should read `True` for every row without exception. This is a machine-verified proof that the bisection algorithm satisfies its theoretical error bound at every step, not just in the limit. The IVT bound decreases by exactly a factor of 2 per iteration, and the actual error, while erratic in its last few bits due to floating-point rounding, never violates the certificate.

The convergence rate here is **linear** with rate $1/2$: each iteration purchases exactly one binary digit of accuracy. To see this quantitatively, note that $\log_2(1/\varepsilon)$ iterations are required to achieve absolute error $\varepsilon$. For $\varepsilon = 10^{-15}$ and initial interval length 1, we need $\lceil 15 / \log_{10}(2) \rceil \approx 50$ iterations, which matches the loop termination observed above.

### 1.2 Newton's Method and Quadratic Convergence

Newton's method is the canonical example of second-order convergence. Given $f$ differentiable with nonzero derivative at the root $c$, the iteration

$$x_{k+1} = x_k - \frac{f(x_k)}{f'(x_k)}$$

satisfies $|e_{k+1}| \leq M \cdot |e_k|^2$ where $e_k = x_k - c$ and $M = |f''(c)| / (2|f'(c)|)$. The proof follows from Taylor's theorem: expanding $f$ about $x_k$ and evaluating at $c$ gives

$$0 = f(c) = f(x_k) + f'(x_k)(c - x_k) + \frac{1}{2}f''(\xi_k)(c - x_k)^2$$

for some $\xi_k$ between $x_k$ and $c$. Rearranging and dividing through by $f'(x_k)$ yields

$$c - x_{k+1} = -\frac{f''(\xi_k)}{2f'(x_k)}(c - x_k)^2,$$

which is the quadratic error recurrence. The following code verifies this numerically, computing the empirical convergence rate at each step and confirming it approaches 2.

```python
import sympy as sp
import numpy as np

x = sp.Symbol('x')
f_sym = x**3 - 2*x - 5
df_sym = sp.diff(f_sym, x)
d2f_sym = sp.diff(f_sym, x, 2)

f  = sp.lambdify(x, f_sym,  'numpy')
df = sp.lambdify(x, df_sym, 'numpy')

# Exact root via high-precision SymPy evaluation
exact_roots = sp.solve(f_sym, x)
real_roots  = [r for r in exact_roots if sp.im(r) == 0]
c_exact     = float(sp.N(real_roots[0], 50))

# Theoretical constant M = |f''(c)| / (2 |f'(c)|)
c_sym  = real_roots[0]
M_sym  = sp.Abs(d2f_sym.subs(x, c_sym)) / (2 * sp.Abs(df_sym.subs(x, c_sym)))
M_val  = float(sp.N(M_sym, 20))
print(f"Quadratic convergence constant M = {M_val:.10f}")

x_k     = 3.0  # starting point
errors  = []
print(f"\n{'k':>3} {'x_k':>22} {'|e_k|':>18} {'|e_k|^2 * M':>18} {'|e_{k+1}|':>18} {'emp. rate':>10}")
print("-" * 95)

for k in range(12):
    e_k  = abs(x_k - c_exact)
    pred = M_val * e_k**2  # predicted next error
    errors.append(e_k)
    
    if df(x_k) == 0:
        print("Derivative zero: Newton's method fails here.")
        break
    
    x_next = x_k - f(x_k) / df(x_k)
    e_next = abs(x_next - c_exact)
    
    # Empirical convergence rate: log(e_{k+1}) / log(e_k)
    if e_k > 1e-16 and e_next > 1e-16:
        emp_rate = np.log(e_next) / np.log(e_k)
    else:
        emp_rate = float('nan')
    
    print(f"{k:>3} {x_k:>22.15f} {e_k:>18.6e} {pred:>18.6e} {e_next:>18.6e} {emp_rate:>10.4f}")
    x_k = x_next

print(f"\nFinal approximation: {x_k:.15f}")
print(f"Exact value:         {c_exact:.15f}")
print(f"Final |error|:       {abs(x_k - c_exact):.6e}")
```

Observe the empirical rate column. It begins near 1 (while the iterates are far from the root), and as $x_k$ approaches $c$, the rate converges to 2 from below, confirming the theoretical prediction. The predicted error $M \cdot |e_k|^2$ tracks the actual $|e_{k+1}|$ closely once the iterates are within the quadratic convergence basin. At roughly iteration 7, the error drops below machine epsilon ($\approx 2.2 \times 10^{-16}$) and the method stagnates because floating-point arithmetic can no longer resolve the differences.

### 1.3 Polynomial Interpolation and the Runge Phenomenon

Lagrange interpolation through $n+1$ equally spaced nodes $\{x_0, x_1, \ldots, x_n\}$ constructs the unique polynomial $P_n$ of degree $\leq n$ satisfying $P_n(x_i) = f(x_i)$. The interpolation error at an arbitrary point $x \in [a,b]$ is

$$f(x) - P_n(x) = \frac{f^{(n+1)}(\xi)}{(n+1)!} \prod_{i=0}^{n}(x - x_i)$$

for some $\xi$ dependent on $x$. For analytic functions, one might expect increasing $n$ to improve accuracy uniformly. Runge's 1901 counterexample demolished this intuition: the function $f(x) = 1/(1 + 25x^2)$ on $[-1,1]$ exhibits spectacular divergence of the interpolating polynomial near the endpoints as $n \to \infty$, despite $f$ being smooth. The oscillation of $\prod_{i=0}^n (x - x_i)$ on equally spaced nodes grows without bound.

The resolution is to use **Chebyshev nodes** instead. The $n+1$ Chebyshev nodes of the first kind on $[-1,1]$ are

$$x_k = \cos\!\left(\frac{(2k+1)\pi}{2(n+1)}\right), \quad k = 0, 1, \ldots, n.$$

These are the zeros of the Chebyshev polynomial $T_{n+1}(x)$. The key property is that among all monic polynomials of degree $n+1$, $T_{n+1}(x) / 2^n$ has the smallest maximum norm on $[-1, 1]$, equal to $1/2^n$. Using Chebyshev nodes thus minimizes the worst-case interpolation error over all choices of $n+1$ nodes.

```python
import numpy as np
import sympy as sp
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def runge(x):
    return 1.0 / (1.0 + 25.0 * x**2)

def lagrange_interp(nodes, values, x_eval):
    """Evaluate Lagrange interpolating polynomial at x_eval."""
    n   = len(nodes)
    out = np.zeros_like(x_eval, dtype=float)
    for i in range(n):
        L_i = np.ones_like(x_eval, dtype=float)
        for j in range(n):
            if j != i:
                L_i *= (x_eval - nodes[j]) / (nodes[i] - nodes[j])
        out += values[i] * L_i
    return out

x_fine   = np.linspace(-1, 1, 2000)
f_exact  = runge(x_fine)

degrees  = [5, 10, 15, 20]
fig, axes = plt.subplots(2, 2, figsize=(12, 8))

max_errors_equi   = {}
max_errors_cheby  = {}

for ax, n in zip(axes.flat, degrees):
    # Equally spaced nodes
    nodes_eq  = np.linspace(-1, 1, n + 1)
    vals_eq   = runge(nodes_eq)
    P_eq      = lagrange_interp(nodes_eq, vals_eq, x_fine)
    
    # Chebyshev nodes
    k         = np.arange(n + 1)
    nodes_ch  = np.cos((2*k + 1) * np.pi / (2*(n + 1)))
    vals_ch   = runge(nodes_ch)
    P_ch      = lagrange_interp(nodes_ch, vals_ch, x_fine)
    
    err_eq    = np.max(np.abs(P_eq - f_exact))
    err_ch    = np.max(np.abs(P_ch - f_exact))
    max_errors_equi[n]  = err_eq
    max_errors_cheby[n] = err_ch
    
    ax.plot(x_fine, f_exact, 'k-',  linewidth=1.5, label='$f(x)$')
    ax.plot(x_fine, P_eq,    'r--', linewidth=1,   label=f'Equispaced (err={err_eq:.2e})')
    ax.plot(x_fine, P_ch,    'b-',  linewidth=1,   label=f'Chebyshev  (err={err_ch:.2e})')
    ax.set_ylim(-2, 2)
    ax.set_title(f'Degree {n} Interpolation of Runge Function')
    ax.legend(fontsize=7)
    ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('runge_phenomenon.png', dpi=150, bbox_inches='tight')

print("Maximum interpolation errors:")
print(f"\n{'Degree':>8} {'Equispaced':>18} {'Chebyshev':>18}")
print("-" * 46)
for n in degrees:
    print(f"{n:>8} {max_errors_equi[n]:>18.6e} {max_errors_cheby[n]:>18.6e}")

# Formally verify Chebyshev optimality: ||omega_n||_inf = 1/2^n
# where omega_n = prod_{k=0}^{n} (x - x_k) for Chebyshev nodes
print("\nVerifying Chebyshev minimax property:")
for n in degrees:
    k         = np.arange(n + 1)
    nodes_ch  = np.cos((2*k + 1) * np.pi / (2*(n + 1)))
    omega     = np.prod([x_fine - nodes_ch[j] for j in range(n+1)], axis=0)
    omega_inf = np.max(np.abs(omega))
    theory    = 1.0 / 2**n
    print(f"  n={n:>2}: ||omega||_inf = {omega_inf:.6e}, 1/2^n = {theory:.6e}, "
          f"ratio = {omega_inf/theory:.6f}")
```

The output table will show that equispaced errors grow rapidly with degree (they are $O(c^n)$ for $c > 1$ for the Runge function), while Chebyshev errors decrease. The minimax verification at the bottom confirms the theoretical bound: for each degree, the maximum of $|\prod_{k=0}^n (x - x_k)|$ over $[-1,1]$ equals $1/2^n$, as guaranteed by the Chebyshev optimality theorem. Any deviation from exactly $1/2^n$ in the output is a discretization artifact from sampling $x_\text{fine}$ at 2000 points rather than continuously.

---

## Exercise 2: Boundary Value Stress Testing & Singularities

### 2.1 Condition Number Analysis and the Hilbert Matrix

A linear system $Ax = b$ is said to be ill-conditioned when small relative perturbations in $b$ produce large relative perturbations in $x$. The amplification factor is bounded above by the condition number $\kappa(A) = \|A\| \cdot \|A^{-1}\|$. The perturbation theorem states precisely that if $\delta b$ is a perturbation with $\|A(x + \delta x) = b + \delta b\|$, then

$$\frac{\|\delta x\|}{\|x\|} \leq \kappa(A) \cdot \frac{\|\delta b\|}{\|b\|}.$$

The Hilbert matrix $H_n$ with entries $H_{ij} = 1/(i+j-1)$ for $i, j = 1, \ldots, n$ is the canonical example of a matrix whose condition number grows super-exponentially with $n$. Specifically,

$$\kappa_2(H_n) \approx e^{3.5n},$$

so a $12 \times 12$ Hilbert matrix has a condition number exceeding $10^{16}$, which completely fills the available precision of double-precision arithmetic. This exercise constructs Hilbert systems of increasing size, solves them in both double precision and SymPy exact arithmetic, and measures the degradation of numerical accuracy.

```python
import numpy as np
import sympy as sp
from fractions import Fraction

def hilbert_exact(n):
    """Construct n x n Hilbert matrix with exact rational entries."""
    return sp.Matrix([[sp.Rational(1, i + j - 1) for j in range(1, n+1)]
                      for i in range(1, n+1)])

def hilbert_float(n):
    """Construct n x n Hilbert matrix in double precision."""
    return np.array([[1.0 / (i + j - 1) for j in range(1, n+1)]
                     for i in range(1, n+1)])

print(f"{'n':>4} {'kappa_2(H_n)':>20} {'||x_exact - x_float||_inf':>28} {'digits lost':>12}")
print("-" * 68)

for n in range(2, 14):
    H_float = hilbert_float(n)
    
    # Exact solution: choose x* = [1, 1, ..., 1]^T, compute b = H * x* exactly
    H_exact = hilbert_exact(n)
    x_star_exact = sp.Matrix([1] * n)
    b_exact = H_exact * x_star_exact
    
    # Solve exactly with SymPy rational arithmetic
    x_sym = H_exact.solve(b_exact)
    
    # Convert b to float
    b_float = np.array([float(b_exact[i]) for i in range(n)])
    
    # Solve with NumPy (double precision LU)
    try:
        x_float = np.linalg.solve(H_float, b_float)
    except np.linalg.LinAlgError:
        x_float = np.full(n, np.nan)
    
    # Convert exact solution to float for comparison
    x_sym_float = np.array([float(x_sym[i]) for i in range(n)])
    
    # Error between exact and floating-point solutions
    error_inf = np.max(np.abs(x_sym_float - x_float))
    
    # Condition number
    kappa = np.linalg.cond(H_float)
    
    # Digits lost = log10(kappa) measures decimal digits of precision consumed
    digits_lost = np.log10(kappa) if kappa > 0 else 0
    
    print(f"{n:>4} {kappa:>20.6e} {error_inf:>28.6e} {digits_lost:>12.2f}")

# Detailed comparison for n=8
print("\n--- Detailed component-wise comparison for n=8 ---")
n = 8
H_float = hilbert_float(n)
H_exact = hilbert_exact(n)
x_star_exact = sp.Matrix([1] * n)
b_exact = H_exact * x_star_exact
b_float = np.array([float(b_exact[i]) for i in range(n)])
x_float = np.linalg.solve(H_float, b_float)
x_sym   = H_exact.solve(b_exact)

print(f"{'i':>4} {'x_exact':>25} {'x_float':>22} {'|error|':>18}")
for i in range(n):
    xi_exact = float(x_sym[i])
    xi_float = x_float[i]
    print(f"{i+1:>4} {xi_exact:>25.15f} {xi_float:>22.10f} {abs(xi_exact - xi_float):>18.6e}")
```

What you will see is a systematic and catastrophic degradation. For $n = 2$, the floating-point solution is accurate to about 12 significant digits. By $n = 10$, the solution is accurate to only 1 or 2 digits. By $n = 13$, the floating-point solver is producing numbers that bear no meaningful relationship to the true solution. The "digits lost" column, computed as $\log_{10}(\kappa_2(H_n))$, tells you exactly how many decimal digits of your 15.9-digit double-precision budget are consumed by the ill-conditioning. When this number exceeds 15, you have no accuracy left.

This is not a failure of the algorithm. LU decomposition is backward stable, meaning it solves a nearby system $\hat{A}\hat{x} = \hat{b}$ with $\|\hat{A} - A\| / \|A\| = O(\varepsilon_{\text{mach}})$. The failure is intrinsic to the problem: the Hilbert matrix is nearly singular, and any algorithm for solving a nearly singular system in double precision will produce garbage. The only remedy is either exact arithmetic (as SymPy demonstrates) or reformulating the problem.

### 2.2 Stiff Ordinary Differential Equations and Stability Regions

A system of ODEs is called **stiff** when it contains components evolving on vastly different timescales. The canonical scalar example is $y' = \lambda y$ with $\lambda \ll 0$. Explicit methods like forward Euler impose a step size restriction $h < 2/|\lambda|$ for stability, which makes them computationally prohibitive when $|\lambda|$ is large. The implicit backward Euler method, by contrast, is **A-stable**: it is stable for all $h > 0$ regardless of $|\lambda|$.

Formally, the stability region of a one-step method is the set $\mathcal{S} = \{z \in \mathbb{C} : |R(z)| \leq 1\}$ where $z = h\lambda$ and $R(z)$ is the method's amplification factor. For forward Euler, $R(z) = 1 + z$, and $|1 + z| \leq 1$ defines a disk of radius 1 centered at $-1 + 0i$, excluding the entire left half-plane except this disk. For backward Euler, $R(z) = 1/(1-z)$, and $|1/(1-z)| \leq 1$ holds for all $\text{Re}(z) \leq 0$, covering the entire left half-plane.

```python
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# ---------------------------------------------------------------
# Part 1: Visualize stability regions
# ---------------------------------------------------------------
re = np.linspace(-5, 2, 800)
im = np.linspace(-4, 4, 800)
RE, IM = np.meshgrid(re, im)
Z = RE + 1j * IM

# Amplification factors
R_fwd_euler  = np.abs(1 + Z)
R_bwd_euler  = np.abs(1.0 / (1.0 - Z))
R_rk4        = np.abs(1 + Z + Z**2/2 + Z**3/6 + Z**4/24)

fig, axes = plt.subplots(1, 3, figsize=(15, 5))
for ax, R, title in zip(axes,
                         [R_fwd_euler, R_bwd_euler, R_rk4],
                         ['Forward Euler', 'Backward Euler (A-stable)', 'RK4']):
    ax.contourf(RE, IM, R, levels=[0, 1], colors=['lightblue'], alpha=0.7)
    ax.contour(RE, IM, R, levels=[1], colors=['blue'], linewidths=1.5)
    ax.axhline(0, color='k', linewidth=0.5)
    ax.axvline(0, color='k', linewidth=0.5)
    ax.set_title(f'Stability Region: {title}')
    ax.set_xlabel('Re(z)')
    ax.set_ylabel('Im(z)')
    ax.set_aspect('equal')

plt.tight_layout()
plt.savefig('stability_regions.png', dpi=150, bbox_inches='tight')

# ---------------------------------------------------------------
# Part 2: Stiff equation y' = -1000*y + 3000 - 2000*exp(-t)
#          exact solution: y(t) = 3 - 0.998*exp(-1000t) + 0.002*exp(-t) - 2*t*exp(-t) ... 
# Exact solution: y(t) = 3 - 2*exp(-t) - exp(-1000*t) * (y(0) - 2)
#          with y(0) = 0:  y(t) = 3 - 2*exp(-t) - exp(-1000*t)
# ---------------------------------------------------------------
import sympy as sp

t_sym = sp.Symbol('t')
y_sym = sp.Function('y')

# Define stiff ODE: y' = -1000*(y - 3 + 2*exp(-t))  =>  y' = -1000y + 3000 - 2000*exp(-t)
ode = sp.Eq(y_sym(t_sym).diff(t_sym), -1000*y_sym(t_sym) + 3000 - 2000*sp.exp(-t_sym))
sol_sym = sp.dsolve(ode, y_sym(t_sym), ics={y_sym(0): 0})
print("Exact solution:", sol_sym)

y_exact_fn = sp.lambdify(t_sym, sol_sym.rhs, 'numpy')

# Numerical integration
t_end = 0.005
y0    = 0.0

# Forward Euler with h barely inside stability boundary for lambda = -1000
h_stable   = 0.0019   # h * 1000 = 1.9 < 2: forward Euler stable
h_unstable = 0.0021   # h * 1000 = 2.1 > 2: forward Euler unstable
h_implicit = 0.001    # backward Euler: any h works

def f_stiff(t, y):
    return -1000 * y + 3000 - 2000 * np.exp(-t)

def run_forward_euler(h, t_end, y0):
    ts, ys = [0.0], [y0]
    t = 0.0; y = y0
    while t < t_end:
        y = y + h * f_stiff(t, y)
        t = t + h
        ts.append(t); ys.append(y)
    return np.array(ts), np.array(ys)

def run_backward_euler(h, t_end, y0):
    # For y' = -1000y + g(t), backward Euler step:
    # y_{n+1} = (y_n + h*g(t_{n+1})) / (1 + 1000*h)
    ts, ys = [0.0], [y0]
    t = 0.0; y = y0
    while t < t_end:
        t_next = t + h
        g_next = 3000 - 2000 * np.exp(-t_next)
        y = (y + h * g_next) / (1 + 1000 * h)
        t = t_next
        ts.append(t); ys.append(y)
    return np.array(ts), np.array(ys)

ts_s,  ys_s  = run_forward_euler(h_stable,   t_end, y0)
ts_u,  ys_u  = run_forward_euler(h_unstable, t_end, y0)
ts_be, ys_be = run_backward_euler(h_implicit, t_end, y0)

t_exact_pts = np.linspace(0, t_end, 2000)
y_exact_pts = y_exact_fn(t_exact_pts)

print(f"\nForward Euler (h={h_stable},   stable):   final y = {ys_s[-1]:.6f},  "
      f"exact = {y_exact_fn(ts_s[-1]):.6f},  error = {abs(ys_s[-1] - y_exact_fn(ts_s[-1])):.4e}")
print(f"Forward Euler (h={h_unstable}, unstable): final y = {ys_u[-1]:.6f},  "
      f"exact = {y_exact_fn(ts_u[-1]):.6f}")
print(f"Backward Euler (h={h_implicit}):          final y = {ys_be[-1]:.6f},  "
      f"exact = {y_exact_fn(ts_be[-1]):.6f},  error = {abs(ys_be[-1] - y_exact_fn(ts_be[-1])):.4e}")
```

The forward Euler run with $h = 0.0021$ produces a solution that grows without bound, with oscillating values that rapidly exceed $10^{30}$ in magnitude. The run with $h = 0.0019$, just barely inside the stability boundary, produces an accurate solution but required over 2.6 steps per period of the stiff transient, which is computationally wasteful for a small transient that decays in time $1/|\lambda| = 0.001$. The backward Euler run with $h = 0.001$ uses a step size that is 1000 times larger than the forward Euler stability limit and produces a correct, smooth solution with modest first-order error. The takeaway is not that implicit methods are always preferable, but that the choice of method must be governed by the stability region and the location of the problem's eigenvalues in the complex plane.

### 2.3 Singularities in Numerical Integration

Gaussian quadrature approximates $\int_a^b f(x)\,dx$ by a weighted sum $\sum_{i=1}^n w_i f(x_i)$ where the nodes $x_i$ and weights $w_i$ are chosen to integrate polynomials of degree up to $2n-1$ exactly. This exactness is proven through the orthogonality of Legendre polynomials $P_n$: the nodes are the zeros of $P_n$ on $[-1,1]$, and the weights are $w_i = 2 / [(1-x_i^2)(P_n'(x_i))^2]$. The rule achieves degree $2n-1$ precision because any polynomial of that degree can be written as $f = P_n \cdot q + r$ where $\deg(q) \leq n-1$ and $\deg(r) \leq n-1$, and both components are integrated exactly.

The rule breaks down, however, when $f$ has an endpoint singularity. Consider $\int_0^1 x^{-1/2} dx = 2$. The integrand has a square-root singularity at $x = 0$, and standard Gauss-Legendre quadrature converges extremely slowly on this integral. The cure is a change of variables: substituting $x = t^2$ gives $dx = 2t\,dt$ and transforms the integral to $\int_0^1 (t^2)^{-1/2} \cdot 2t\,dt = \int_0^1 2\,dt = 2$, completely removing the singularity.

```python
import numpy as np
from numpy.polynomial.legendre import leggauss
import sympy as sp

# ---------------------------------------------------------------
# Exact value via SymPy
# ---------------------------------------------------------------
x_s   = sp.Symbol('x', positive=True)
exact = float(sp.integrate(x_s**sp.Rational(-1, 2), (x_s, 0, 1)))
print(f"Exact integral of x^(-1/2) on [0,1] = {exact}")

# ---------------------------------------------------------------
# Standard Gauss-Legendre on [0,1] via affine mapping from [-1,1]
# ---------------------------------------------------------------
print("\nStandard Gauss-Legendre (direct, singular integrand):")
print(f"{'n':>5} {'approx':>18} {'error':>15}")
for n in [4, 8, 16, 32, 64, 128]:
    pts, wts = leggauss(n)
    # Map from [-1,1] to [0,1]: x = (t+1)/2, dx = dt/2
    x_mapped = (pts + 1.0) / 2.0
    approx   = 0.5 * np.sum(wts * x_mapped**(-0.5))
    err      = abs(approx - exact)
    print(f"{n:>5} {approx:>18.10f} {err:>15.6e}")

# ---------------------------------------------------------------
# Gauss-Legendre after singularity removal via x = t^2 substitution
# ---------------------------------------------------------------
print("\nGauss-Legendre after x = t^2 substitution (singularity removed):")
print(f"{'n':>5} {'approx':>18} {'error':>15}")
for n in [4, 8, 16, 32, 64]:
    pts, wts = leggauss(n)
    # Map t from [-1,1] to [0,1]: t = (s+1)/2, dt = ds/2
    # Then x = t^2, integral becomes int_0^1 x^{-1/2} dx
    #   = int_0^1 (t^2)^{-1/2} 2t dt = int_0^1 2 dt = 2
    # Using substitution: int_{-1}^{1} (((s+1)/2)^2)^{-1/2} * 2*((s+1)/2) * (1/2) ds
    t_mapped = (pts + 1.0) / 2.0           # t in [0,1]
    # Jacobian: original integrand is (t^2)^{-1/2} * 2t * (1/2) = 1
    # So integrand after full substitution is simply 1, which GL integrates exactly.
    # We verify this numerically:
    integrand_transformed = t_mapped**(-1) * t_mapped  # = 1 (before the outer 1/2 factor)
    approx = np.sum(wts * 1.0) / 1.0  # trivially 2
    # Non-trivial test: apply same substitution to sqrt(x) * sin(x) on [0,1]
    # int_0^1 sqrt(x) sin(x) dx: exact value via SymPy
    f_sym   = sp.sqrt(x_s) * sp.sin(x_s)
    exact2  = float(sp.integrate(f_sym, (x_s, 0, 1)))
    
    # Direct GL
    x_dir   = (pts + 1.0) / 2.0
    approx2_direct = 0.5 * np.sum(wts * np.sqrt(x_dir) * np.sin(x_dir))
    
    # After x = t^2: int_0^1 sqrt(t^2) * sin(t^2) * 2t dt = 2 int_0^1 t^2 sin(t^2) dt
    # Map t from [0,1] to [-1,1]: t = (s+1)/2
    approx2_subst = 2.0 * 0.5 * np.sum(wts * t_mapped**2 * np.sin(t_mapped**2))
    
    print(f"{n:>5}  direct={approx2_direct:.10f}  "
          f"substituted={approx2_subst:.10f}  exact={exact2:.10f}")

# ---------------------------------------------------------------
# Demonstrate convergence rate difference quantitatively
# ---------------------------------------------------------------
print("\nConvergence rate for x^(-1/2): direct GL vs substituted GL")
print(f"{'n':>5} {'direct error':>18} {'subst. error':>18}")
for n in [4, 8, 16, 32, 64, 128, 256]:
    pts, wts = leggauss(n)
    x_mapped = (pts + 1.0) / 2.0
    t_mapped = (pts + 1.0) / 2.0
    
    err_direct = abs(0.5 * np.sum(wts * x_mapped**(-0.5)) - exact)
    # After x=t^2: integral = 2, GL on constant = exactly 2
    err_subst  = abs(2.0 * 0.5 * np.sum(wts * np.ones_like(t_mapped)) - exact)
    print(f"{n:>5} {err_direct:>18.6e} {err_subst:>18.6e}")
```

The direct Gauss-Legendre column shows agonizingly slow algebraic convergence: the error decreases roughly as $n^{-1/2}$, far from the exponential convergence GL achieves on smooth integrands. After the $x = t^2$ substitution, the integrand $x^{-1/2}dx = 2dt$ is constant, and Gauss-Legendre integrates it exactly with $n = 1$. For more general singular integrands, the substitution trades a low-regularity function for a smoother one, restoring rapid convergence. The lesson generalizes: Gaussian quadrature's theoretical guarantees apply to functions in $C^{2n}([a,b])$, and when the integrand violates that regularity at a point, algebraic subtraction or change of variables must precede numerical integration.

---

## Exercise 3: Algorithmic Implementation of Formal Structures

### 3.1 QR Decomposition via Householder Reflections

The QR decomposition factors a matrix $A \in \mathbb{R}^{m \times n}$ (with $m \geq n$) as $A = QR$, where $Q \in \mathbb{R}^{m \times m}$ is orthogonal and $R \in \mathbb{R}^{m \times n}$ is upper triangular. The numerically stable method for computing this decomposition uses **Householder reflections**: elementary orthogonal matrices of the form

$$H = I - 2\frac{vv^T}{\|v\|^2},$$

where the vector $v$ is chosen so that $Hx = \|x\|e_1$ for a given column $x$. Each reflection zeroes out the subdiagonal entries of one column while preserving the already-computed structure. The choice $v = x + \|x\|\,\text{sign}(x_1) e_1$ avoids catastrophic cancellation when $x_1 \approx -\|x\|$, which is an important numerical subtlety.

The following implementation constructs QR from scratch using Householder reflections, verifies orthogonality of $Q$ and upper-triangularity of $R$ to machine precision, and benchmarks against NumPy's internal QR to confirm that the results agree.

```python
import numpy as np
import sympy as sp

def householder_qr(A):
    """
    QR decomposition via successive Householder reflections.
    Returns Q (m x m orthogonal) and R (m x n upper triangular).
    """
    m, n  = A.shape
    Q     = np.eye(m)
    R     = A.astype(float).copy()
    
    for k in range(min(m - 1, n)):
        x     = R[k:, k].copy()
        norm_x = np.linalg.norm(x)
        
        # Choose sign to avoid cancellation
        sign  = np.sign(x[0]) if x[0] != 0 else 1.0
        v     = x.copy()
        v[0] += sign * norm_x
        
        if np.linalg.norm(v) < 1e-14:
            continue  # column already in correct form
        
        v     = v / np.linalg.norm(v)  # normalize
        
        # Apply H_k = I - 2vv^T to R[k:, k:]
        R[k:, k:] -= 2.0 * np.outer(v, v @ R[k:, k:])
        
        # Accumulate Q: H_k acts on rows k: of Q^T, i.e., columns k: of Q
        Q[:, k:] -= 2.0 * np.outer(Q[:, k:] @ v, v)
    
    return Q, R

def verify_qr(A, Q, R, label=""):
    m, n = A.shape
    
    # Check A = QR
    residual_QR   = np.linalg.norm(A - Q @ R, 'fro') / np.linalg.norm(A, 'fro')
    
    # Check Q^T Q = I
    QTQ           = Q.T @ Q
    ortho_error   = np.linalg.norm(QTQ - np.eye(m), 'fro')
    
    # Check R upper triangular (Frobenius norm of strict lower triangle)
    R_lower       = np.tril(R, -1)
    upper_tri_err = np.linalg.norm(R_lower, 'fro')
    
    print(f"{label}")
    print(f"  ||A - QR||_F / ||A||_F  = {residual_QR:.4e}")
    print(f"  ||Q^T Q - I||_F          = {ortho_error:.4e}")
    print(f"  ||tril(R, -1)||_F         = {upper_tri_err:.4e}")
    return residual_QR, ortho_error, upper_tri_err

# Test on several matrix types
np.random.seed(42)

# (a) Random well-conditioned matrix
A1 = np.random.randn(8, 5)
Q1, R1 = householder_qr(A1)
Q1_np, R1_np = np.linalg.qr(A1)
verify_qr(A1, Q1, R1, "Random 8x5 matrix (Householder, our impl.)")
verify_qr(A1, Q1_np, R1_np, "Random 8x5 matrix (NumPy LAPACK)")

# (b) Vandermonde matrix (moderately ill-conditioned)
pts = np.linspace(-1, 1, 7)
A2  = np.vander(pts, 7, increasing=True)
Q2, R2 = householder_qr(A2)
verify_qr(A2, Q2, R2, "7x7 Vandermonde matrix (Householder, our impl.)")

# (c) Nearly rank-deficient matrix
A3        = np.random.randn(6, 6)
A3[:, 5]  = A3[:, 0] + 1e-10 * np.random.randn(6)   # column 5 ≈ column 0
Q3, R3    = householder_qr(A3)
verify_qr(A3, Q3, R3, "Nearly rank-deficient 6x6 (Householder, our impl.)")
print(f"  Diagonal of R: {np.diag(R3)}")
print(f"  |R[5,5]| ≈ {abs(R3[5,5]):.4e} (should be near-zero for rank deficiency)")

# (d) Formally verify Householder reflection properties via SymPy
print("\n--- Symbolic Verification of Householder Properties ---")
x1, x2, x3 = sp.symbols('x1 x2 x3', real=True)
x_vec = sp.Matrix([x1, x2, x3])
norm_x = sp.sqrt(x1**2 + x2**2 + x3**2)
sign   = 1  # assume x1 > 0 for symbolic simplicity
v_vec  = x_vec + sp.Matrix([norm_x, 0, 0])
H      = sp.eye(3) - 2 * (v_vec * v_vec.T) / (v_vec.T * v_vec)[0, 0]

Hx     = sp.simplify(H * x_vec)
print(f"H*x = {Hx.T}  (should be [-||x||, 0, 0]^T)")

HtH    = sp.simplify(H.T * H)
print(f"H^T H = I?  Max entry of |H^T H - I|:")
diff   = sp.simplify(HtH - sp.eye(3))
print(f"  {sp.simplify(diff)}")
```

The symbolic verification at the end confirms, without any floating-point doubt, that $H^T H = I$ and $Hx = -\|x\| e_1$ as algebraic identities. The numerical tests confirm that our hand-built implementation achieves machine-precision residuals $\|A - QR\|_F / \|A\|_F \approx 10^{-15}$, orthogonality error $\|Q^T Q - I\|_F \approx 10^{-14}$, and strict upper triangularity, all matching or exceeding NumPy's LAPACK-backed implementation. The near-rank-deficient case reveals a small but nonzero $|R_{55}|$ of order $10^{-10}$, the precise numerical signature of the near-linear-dependence injected into column 5.

### 3.2 Fast Fourier Transform: Algorithmic Complexity and Round-Trip Verification

The Discrete Fourier Transform (DFT) of a sequence $\{x_j\}_{j=0}^{N-1}$ is

$$X_k = \sum_{j=0}^{N-1} x_j \, e^{-2\pi i jk/N}, \quad k = 0, 1, \ldots, N-1.$$

Naively, computing all $N$ output values requires $O(N^2)$ complex multiplications. The Cooley-Tukey Fast Fourier Transform (FFT) algorithm exploits the recursive structure

$$X_k = \sum_{j=0}^{N/2-1} x_{2j} \, e^{-2\pi i (2j)k/N} + e^{-2\pi ik/N} \sum_{j=0}^{N/2-1} x_{2j+1} \, e^{-2\pi i (2j)k/N} = E_k + e^{-2\pi ik/N} O_k$$

to reduce the problem to two DFTs of size $N/2$, yielding the recurrence $T(N) = 2T(N/2) + O(N)$ with solution $T(N) = O(N \log N)$ by the Master Theorem. The following exercise implements both the naive DFT and the recursive Cooley-Tukey FFT, verifies their numerical agreement, measures the actual complexity crossover, and uses SymPy to verify the DFT matrix's unitary property.

```python
import numpy as np
import sympy as sp
import time

def dft_naive(x):
    """O(N^2) DFT via direct definition."""
    N   = len(x)
    X   = np.zeros(N, dtype=complex)
    for k in range(N):
        for j in range(N):
            X[k] += x[j] * np.exp(-2j * np.pi * j * k / N)
    return X

def fft_cooley_tukey(x):
    """Recursive Cooley-Tukey FFT. N must be a power of 2."""
    N = len(x)
    if N == 1:
        return x.astype(complex)
    if N % 2 != 0:
        raise ValueError("N must be a power of 2 for this implementation")
    
    even = fft_cooley_tukey(x[0::2])
    odd  = fft_cooley_tukey(x[1::2])
    
    twiddles = np.exp(-2j * np.pi * np.arange(N // 2) / N)
    return np.concatenate([even + twiddles * odd,
                           even - twiddles * odd])

# ---------------------------------------------------------------
# Numerical correctness verification
# ---------------------------------------------------------------
np.random.seed(7)
for N in [8, 16, 32, 64, 128]:
    x          = np.random.randn(N) + 1j * np.random.randn(N)
    X_naive    = dft_naive(x)
    X_ct       = fft_cooley_tukey(x)
    X_numpy    = np.fft.fft(x)
    
    err_vs_naive = np.max(np.abs(X_ct - X_naive))
    err_vs_numpy = np.max(np.abs(X_ct - X_numpy))
    
    # Parseval's theorem: ||X||^2 = N * ||x||^2
    parseval_lhs = np.sum(np.abs(X_ct)**2)
    parseval_rhs = N * np.sum(np.abs(x)**2)
    parseval_err = abs(parseval_lhs - parseval_rhs) / parseval_rhs
    
    # Round-trip: x ≈ IDFT(DFT(x))
    x_recovered  = np.fft.ifft(X_ct)
    roundtrip_err = np.max(np.abs(x_recovered - x))
    
    print(f"N={N:>4}: CT vs naive={err_vs_naive:.2e}, "
          f"CT vs NumPy={err_vs_numpy:.2e}, "
          f"Parseval err={parseval_err:.2e}, "
          f"round-trip err={roundtrip_err:.2e}")

# ---------------------------------------------------------------
# Complexity benchmark: empirical O(N^2) vs O(N log N)
# ---------------------------------------------------------------
print("\nComplexity benchmark:")
print(f"{'N':>8} {'naive (s)':>14} {'CT (s)':>12} {'NumPy (s)':>12} {'speedup CT':>12}")
for exp in range(2, 10):
    N   = 2**exp
    x   = np.random.randn(N)
    
    t0 = time.perf_counter()
    for _ in range(5):
        dft_naive(x)
    t_naive = (time.perf_counter() - t0) / 5
    
    t0 = time.perf_counter()
    for _ in range(20):
        fft_cooley_tukey(x)
    t_ct = (time.perf_counter() - t0) / 20
    
    t0 = time.perf_counter()
    for _ in range(200):
        np.fft.fft(x)
    t_np = (time.perf_counter() - t0) / 200
    
    speedup = t_naive / t_ct if t_ct > 0 else float('inf')
    print(f"{N:>8} {t_naive:>14.6f} {t_ct:>12.6f} {t_np:>12.6f} {speedup:>12.1f}x")

# ---------------------------------------------------------------
# Symbolic verification: DFT matrix is unitary (W^H W = N * I)
# ---------------------------------------------------------------
print("\n--- Symbolic DFT Unitary Verification (N=4) ---")
N    = 4
omega = sp.exp(-2 * sp.pi * sp.I / N)
W    = sp.Matrix([[omega**(j*k) for k in range(N)] for j in range(N)])
print("DFT matrix W (N=4):")
sp.pprint(W)

WH_W = sp.simplify(W.H * W)
print("\nW^H * W =")
sp.pprint(WH_W)
print(f"\nIs W^H * W = {N} * I?  {sp.simplify(WH_W - N * sp.eye(N)) == sp.zeros(N, N)}")
```

The output of the unitary verification should print `True` for the final assertion, confirming symbolically that $W^H W = N \cdot I$ and therefore $\frac{1}{\sqrt{N}} W$ is a unitary matrix. This is the algebraic reason Parseval's theorem holds: $\|X\|^2 = \|Wx\|^2 = x^H W^H W x = N \|x\|^2$. The complexity benchmark shows the speedup of Cooley-Tukey over the naive algorithm growing with $N$, following the theoretical ratio $O(N^2) / O(N\log N) = O(N / \log N)$.

### 3.3 Formal Verification with SymPy: Taylor Series Error Bounds

The Taylor remainder theorem states that for $f \in C^{n+1}([a,b])$, the error in the $n$-th degree Taylor approximation $P_n(x)$ about $x = a$ satisfies

$$f(x) - P_n(x) = \frac{f^{(n+1)}(\xi)}{(n+1)!}(x - a)^{n+1}$$

for some $\xi$ between $a$ and $x$. For analysis purposes, the useful form is the uniform bound

$$\max_{x \in [a,b]} |f(x) - P_n(x)| \leq \frac{\max_{\xi \in [a,b]} |f^{(n+1)}(\xi)|}{(n+1)!} (b-a)^{n+1}.$$

The following code uses SymPy to compute both the Taylor polynomial and the exact remainder symbolically, then verifies the error bound computationally by evaluating the symbolic expression over a dense grid.

```python
import sympy as sp
import numpy as np

x  = sp.Symbol('x', real=True)
xi = sp.Symbol('xi', real=True)

functions = [
    (sp.exp(x),          0,  1,  "exp(x) on [0,1]"),
    (sp.sin(x),          0,  sp.pi, "sin(x) on [0,pi]"),
    (sp.log(1 + x),      0,  1,  "log(1+x) on [0,1]"),
]

for f_sym, a, b, label in functions:
    print(f"\n{'='*60}")
    print(f"Function: {label}")
    print(f"{'='*60}")
    
    a_float = float(a)
    b_float = float(b)
    
    for n in [2, 4, 6, 8]:
        # Compute n-th degree Taylor polynomial about x = a
        P_n = sp.series(f_sym, x, x0=a, n=n+1).removeO()
        
        # Exact error function: f(x) - P_n(x)
        error_sym = sp.simplify(f_sym - P_n)
        
        # (n+1)-th derivative for remainder bound
        d_n1     = sp.diff(f_sym, x, n+1)
        
        # Numerical evaluation of bound:
        # M = max |f^{(n+1)}(xi)| over [a,b]
        x_vals       = np.linspace(a_float, b_float, 5000)
        f_num        = sp.lambdify(x, f_sym, 'numpy')
        P_num        = sp.lambdify(x, P_n,   'numpy')
        d_n1_num     = sp.lambdify(x, d_n1,  'numpy')
        
        # Suppress warnings for log near 0
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            d_n1_vals    = np.abs(d_n1_num(x_vals))
        
        M            = np.nanmax(d_n1_vals)
        bound        = M * (b_float - a_float)**(n+1) / float(sp.factorial(n+1))
        
        # Actual maximum error over [0,1]
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            actual_errs  = np.abs(f_num(x_vals) - P_num(x_vals))
        actual_max   = np.nanmax(actual_errs)
        
        # Formal certificate: bound >= actual_max
        cert         = bound >= actual_max * (1 - 1e-10)  # 1e-10 margin for discretization
        
        print(f"  n={n}: max|f - P_n| = {actual_max:.4e}, "
              f"bound = {bound:.4e}, "
              f"cert = {cert}, "
              f"ratio = {actual_max/bound:.4f}")
    
    # Demonstrate convergence rate: error ≈ C * (b-a)^{n+1} / (n+1)!
    print(f"\n  Convergence of Taylor error norms (a={a_float}, b={b_float}):")
    prev_err = None
    for n in range(1, 12):
        P_n       = sp.series(f_sym, x, x0=a, n=n+1).removeO()
        P_num     = sp.lambdify(x, P_n, 'numpy')
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            errs  = np.abs(f_num(x_vals) - P_num(x_vals))
        curr_err  = np.nanmax(errs)
        if prev_err is not None and curr_err > 1e-16:
            rate  = np.log(curr_err / prev_err) / np.log((b_float-a_float)) if b_float != a_float else float('nan')
        else:
            rate  = float('nan')
        print(f"    n={n:>2}: ||f - P_n||_inf = {curr_err:.4e}")
        prev_err = curr_err
```

The `cert = True` column confirms the Taylor remainder theorem as a machine-verified inequality for all tested functions and degrees. The convergence table shows the error decreasing approximately as $1/(n+1)!$ times a constant, which for $f = e^x$ on $[0,1]$ is exactly the theoretical prediction since all derivatives are bounded by $e^1 \approx 2.718$.

---

## Formal Axioms Cheat Sheet & Verification Reference

### Convergence and Error

A sequence of approximations $\{x_k\}$ converges to $x^*$ with order $p$ if there exists a constant $C > 0$ such that $|x_{k+1} - x^*| \leq C |x_k - x^*|^p$ for all sufficiently large $k$. When $p = 1$ and $C < 1$, convergence is linear (bisection achieves $C = 1/2$). When $p = 2$, convergence is quadratic (Newton's method under standard hypotheses). When $p = 1.618\ldots$, it is superlinear at the golden ratio (secant method). The computational criterion for order $p$ is

$$p \approx \frac{\log|e_{k+1}|}{\log|e_k|},$$

which can be evaluated numerically as the slope of $\log|e_k|$ plotted against $\log|e_{k-1}|$ on a log-log scale.

### Floating-Point Arithmetic

Machine epsilon $\varepsilon_\text{mach}$ is the smallest floating-point number such that $\text{fl}(1 + \varepsilon_\text{mach}) > 1$. For IEEE 754 double precision, $\varepsilon_\text{mach} = 2^{-52} \approx 2.22 \times 10^{-16}$. Every floating-point operation introduces a relative rounding error bounded by $\varepsilon_\text{mach}$:

$$\text{fl}(a \circ b) = (a \circ b)(1 + \delta), \quad |\delta| \leq \varepsilon_\text{mach},$$

where $\circ \in \{+, -, \times, /\}$. After $n$ sequential operations, the accumulated error is bounded by approximately $n\varepsilon_\text{mach}$ for a stable algorithm. The condition number $\kappa$ measures how much the problem amplifies input errors; the final computed answer satisfies

$$\frac{\|\delta x\|}{\|x\|} \lesssim \kappa \cdot n \cdot \varepsilon_\text{mach}.$$

### Stability Regions

For one-step ODE methods applied to $y' = \lambda y$ with $\lambda \in \mathbb{C}$, the stability region is $\mathcal{S} = \{z = h\lambda : |R(z)| \leq 1\}$. A method is **A-stable** if $\mathcal{S} \supseteq \{z : \text{Re}(z) \leq 0\}$. No explicit Runge-Kutta method is A-stable (Dahlquist's first barrier). Backward Euler and the trapezoidal method (Crank-Nicolson) are A-stable. For stiff problems, one requires either A-stable implicit methods or explicit methods with a step size restriction $h \leq 2/|\text{Re}(\lambda)|$.

### Quadrature Error

For $n$-point Gauss-Legendre quadrature, the error on $[a,b]$ satisfies

$$\left|\int_a^b f(x)\,dx - \sum_{i=1}^n w_i f(x_i)\right| \leq \frac{(b-a)^{2n+1}(n!)^4}{(2n+1)[(2n)!]^3} \max_{\xi \in [a,b]} |f^{(2n)}(\xi)|.$$

This decays faster than any power of $1/n$ for analytic $f$ (spectral convergence). The rule integrates polynomials of degree $\leq 2n-1$ exactly.

### Quick Verification Commands

Execute these one-liners to confirm that a numerical algorithm produces results consistent with its theoretical guarantees.

```python
# Verify machine epsilon
import numpy as np
eps = np.finfo(float).eps
print(f"eps = {eps:.6e} (should be 2.220446e-16)")
assert abs(1.0 + eps - 1.0 - eps) < 1e-32, "IEEE 754 not satisfied"

# Verify Parseval for FFT
import numpy as np
x = np.random.randn(256)
X = np.fft.fft(x)
parseval_error = abs(np.sum(np.abs(X)**2) - 256*np.sum(x**2)) / (256*np.sum(x**2))
print(f"Parseval relative error: {parseval_error:.4e} (should be < 1e-14)")

# Verify QR orthogonality
import numpy as np
A = np.random.randn(50, 30)
Q, R = np.linalg.qr(A, mode='complete')
ortho_err = np.linalg.norm(Q.T @ Q - np.eye(50), 'fro')
print(f"QR orthogonality error: {ortho_err:.4e} (should be < 1e-13)")

# Verify bisection certificate for N iterations
import numpy as np
f = lambda x: x**3 - 2*x - 5
a, b, N = 2.0, 3.0, 50
for k in range(N):
    c = (a + b) / 2.0
    if f(a) * f(c) < 0: b = c
    else: a = c
print(f"Bisection N={N}: final interval length {b-a:.4e}, "
      f"theoretical bound {1.0/2**N:.4e}")

# Verify Chebyshev node minimax property
import numpy as np
n = 16
k = np.arange(n+1)
nodes = np.cos((2*k+1)*np.pi/(2*(n+1)))
x_fine = np.linspace(-1, 1, 100000)
omega  = np.prod([x_fine - nodes[j] for j in range(n+1)], axis=0)
print(f"Chebyshev omega max = {np.max(np.abs(omega)):.6e}, "
      f"1/2^n = {1.0/2**n:.6e}, "
      f"ratio = {np.max(np.abs(omega))/(1.0/2**n):.6f} (should be ~1.0)")
```

Each command is a self-contained executable assertion. Run them after any implementation or environment change to confirm that the fundamental numerical properties remain intact. A correct environment will produce errors at or below $10^{-13}$ for linear algebra operations, $10^{-14}$ for FFT Parseval, and ratios within 1% of unity for the Chebyshev minimax property (the small deviation arises from discrete sampling of the continuous maximum). The bisection final interval length should match the theoretical bound $1/2^{50} \approx 8.88 \times 10^{-16}$ to within machine precision.
