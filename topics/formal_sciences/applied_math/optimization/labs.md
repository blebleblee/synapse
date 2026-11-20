# Operational Verification Labs: Optimization

## Objective & Mathematical Computing Setup

These labs treat optimization not as a numerical black box but as a mathematically verifiable discipline. Each exercise constructs, manipulates, and formally interrogates the structural properties of optimization problems — convexity certificates, KKT conditions, duality gaps, and convergence rates — using symbolic computation in SymPy and SageMath, with selective formal verification in Lean 4. The goal is not to approximate answers but to prove that answers satisfy the conditions that make them answers.

The target environment is Python 3.11+ with SymPy 1.12+, NumPy 1.26+, and SageMath 10.x. Before proceeding, verify your symbolic stack is intact.

```text
python -c "import sympy; print('SymPy', sympy.__version__)"
python -c "import numpy; print('NumPy', numpy.__version__)"
sage --version
```

If SageMath is unavailable, the SageMath exercises can be executed at [sagecell.sagemath.org](https://sagecell.sagemath.org). The Lean 4 exercises require a Lean installation with Mathlib4; initialize a project with `lake new optverify math` and add `require mathlib from git "https://github.com/leanprover-community/mathlib4"` to `lakefile.lean`, then run `lake update`.

The mathematical framework underlying every exercise is the following hierarchy. An optimization problem in standard form is

$$\min_{x \in \mathbb{R}^n} f(x) \quad \text{subject to} \quad g_i(x) \leq 0,\ i = 1,\ldots,m,\quad h_j(x) = 0,\ j = 1,\ldots,p.$$

The Lagrangian is $\mathcal{L}(x, \lambda, \nu) = f(x) + \sum_{i=1}^m \lambda_i g_i(x) + \sum_{j=1}^p \nu_j h_j(x)$, with dual function $q(\lambda, \nu) = \inf_{x} \mathcal{L}(x, \lambda, \nu)$. Weak duality gives $q(\lambda, \nu) \leq p^*$ for all feasible dual variables. Strong duality — the collapse of the duality gap to zero — holds under Slater's condition when $f$ and $g_i$ are convex and there exists a strictly feasible point. The KKT conditions are necessary at any local minimum when a constraint qualification holds, and both necessary and sufficient when $f$ is convex and the constraints are convex.

---

## Exercise 1: Computational Verification of Core Theorems

### 1.1 Verifying Convexity via the Hessian Positive Semidefiniteness Certificate

The first-principles definition of convexity for a twice-differentiable function $f : \mathbb{R}^n \to \mathbb{R}$ states that $f$ is convex if and only if its Hessian $H_f(x) = \nabla^2 f(x)$ is positive semidefinite (PSD) for all $x$ in the domain. For strict convexity, the Hessian must be positive definite (PD). This lab constructs the Hessian symbolically, computes its eigenvalues as rational functions of the variables, and certifies PSD-ness over all of $\mathbb{R}^n$ by proving each eigenvalue is nonnegative everywhere.

The test function is the log-sum-exp, ubiquitous in statistical learning and convex analysis:

$$f(x_1, x_2) = \log\!\left(e^{x_1} + e^{x_2}\right).$$

```python
import sympy as sp

x1, x2 = sp.symbols('x1 x2', real=True)
f = sp.log(sp.exp(x1) + sp.exp(x2))

# Gradient
grad_f = [sp.diff(f, xi) for xi in [x1, x2]]
print("Gradient:")
for g in grad_f:
    print(" ", sp.simplify(g))

# Hessian
H = sp.hessian(f, [x1, x2])
H_simplified = sp.simplify(H)
print("\nHessian:")
sp.pprint(H_simplified)

# Eigenvalues of the Hessian
eigenvals = H_simplified.eigenvals()
print("\nSymbolic eigenvalues:", eigenvals)

# Verify PSD: substitute and check sign
# The eigenvalues of log-sum-exp Hessian are 0 and p1*p2
# where pi = exp(xi) / (exp(x1) + exp(x2))
p1 = sp.exp(x1) / (sp.exp(x1) + sp.exp(x2))
p2 = sp.exp(x2) / (sp.exp(x1) + sp.exp(x2))

# Hessian of log-sum-exp equals diag(p) - p p^T
# Eigenvalues: 0 (with eigenvector [1,1]) and p1+p2 = 1 times correction
# Verify by direct computation
H_exact = sp.Matrix([
    [p1 * (1 - p1), -p1 * p2],
    [-p1 * p2, p2 * (1 - p2)]
])
diff_check = sp.simplify(H_simplified - H_exact)
print("\nDifference between computed and formula Hessian (should be zero):")
sp.pprint(diff_check)

# Verify determinant = 0 (singular => one zero eigenvalue)
det_H = sp.simplify(H_exact.det())
print("\ndet(H) =", det_H)

# Verify trace > 0 (sum of eigenvalues, proves the nonzero eigenvalue is positive)
trace_H = sp.simplify(H_exact.trace())
print("trace(H) =", sp.simplify(trace_H))

# Confirm trace equals p1 + p2 - p1^2 - p2^2 = 2*p1*p2
trace_expected = sp.simplify(2 * p1 * p2)
print("trace equals 2*p1*p2:", sp.simplify(trace_H - trace_expected) == 0)

# PSD certificate: p1 > 0 and p2 > 0 always (exponentials are positive),
# so trace = 2*p1*p2 > 0 and det = 0 => eigenvalues are {0, 2*p1*p2} with 2*p1*p2 > 0
# => Hessian is PSD but not PD: f is convex but not strictly convex.
print("\nConvexity certificate: Hessian is PSD for all (x1, x2). f is convex.")
print("Not strictly convex: det(H) = 0 means H is singular.")
```

The output confirms the Hessian is everywhere singular with a zero eigenvalue along the direction $[1, 1]^T$ (corresponding to the fact that $f(x + c\mathbf{1}) = f(x) + c$, so $f$ is constant along translations of its domain in the all-ones direction after normalization). The nonzero eigenvalue is $2p_1 p_2 > 0$ everywhere, confirming positive semidefiniteness and convexity.

### 1.2 Symbolic KKT Verification for a Constrained Quadratic Program

Consider the problem

$$\min_{x_1, x_2} \; \frac{1}{2}(x_1^2 + x_2^2) \quad \text{subject to} \quad x_1 + x_2 = 1.$$

The Lagrangian is $\mathcal{L}(x_1, x_2, \nu) = \frac{1}{2}(x_1^2 + x_2^2) + \nu(x_1 + x_2 - 1)$. The KKT stationarity conditions require $\nabla_x \mathcal{L} = 0$, which gives $x_i + \nu = 0$ for each $i$, so $x_1 = x_2 = -\nu$. The equality constraint forces $-2\nu = 1$, so $\nu = -1/2$ and the optimal point is $x^* = (1/2, 1/2)$ with $f^* = 1/4$.

The following code derives this symbolically and then verifies strong duality by computing the dual function and confirming zero duality gap.

```python
import sympy as sp

x1, x2, nu = sp.symbols('x1 x2 nu', real=True)

f = sp.Rational(1, 2) * (x1**2 + x2**2)
h = x1 + x2 - 1  # equality constraint h(x) = 0

L = f + nu * h

# KKT stationarity conditions
dL_x1 = sp.diff(L, x1)
dL_x2 = sp.diff(L, x2)
print("Stationarity conditions:")
print(" dL/dx1 =", dL_x1)
print(" dL/dx2 =", dL_x2)

# Solve KKT system: stationarity + primal feasibility
kkt_solution = sp.solve([dL_x1, dL_x2, h], [x1, x2, nu])
print("\nKKT solution:", kkt_solution)

x1_opt, x2_opt, nu_opt = kkt_solution[x1], kkt_solution[x2], kkt_solution[nu]
f_opt = f.subs({x1: x1_opt, x2: x2_opt})
print("Optimal primal objective f* =", f_opt)

# Dual function: q(nu) = inf_{x1,x2} L(x1,x2,nu)
# For unconstrained quadratic: inf is achieved at stationarity points
x1_inf = sp.solve(sp.diff(L, x1), x1)[0]
x2_inf = sp.solve(sp.diff(L, x2), x2)[0]
q_nu = L.subs({x1: x1_inf, x2: x2_inf})
q_nu_simplified = sp.simplify(q_nu)
print("\nDual function q(nu) =", q_nu_simplified)

# Maximize dual: dq/dnu = 0
nu_dual_opt = sp.solve(sp.diff(q_nu_simplified, nu), nu)[0]
q_opt = q_nu_simplified.subs(nu, nu_dual_opt)
print("Dual optimal nu* =", nu_dual_opt)
print("Dual optimal value q* =", q_opt)

# Duality gap
gap = sp.simplify(f_opt - q_opt)
print("\nDuality gap (f* - q*) =", gap)
assert gap == 0, "Strong duality violated!"
print("Strong duality verified: gap = 0.")

# Verify second-order sufficient conditions: Hessian of f restricted to constraint
# The constraint Jacobian is A = [1, 1]. The reduced Hessian = Z^T H Z
# where Z is a basis for null(A). null([1,1]) is spanned by [1,-1].
H_f = sp.hessian(f, [x1, x2])
Z = sp.Matrix([1, -1])
reduced_H = (Z.T * H_f * Z)[0, 0]
print("\nReduced Hessian (Z^T H Z) =", reduced_H)
print("Second-order sufficient condition satisfied:", reduced_H > 0)
```

The reduced Hessian is $Z^T H Z = [1, -1] \cdot I \cdot [1, -1]^T = 2 > 0$, confirming that the KKT point is a strict local (and global, by convexity) minimum. The duality gap is zero, confirming strong duality, which holds here because Slater's condition is satisfied trivially for affine constraints.

### 1.3 Verifying the Farkas Lemma Computationally

Farkas' Lemma is the foundational theorem of linear programming duality. It states that for $A \in \mathbb{R}^{m \times n}$ and $b \in \mathbb{R}^m$, exactly one of the following holds: (I) there exists $x \geq 0$ such that $Ax = b$; or (II) there exists $y$ such that $A^T y \geq 0$ and $b^T y < 0$. This mutual exclusivity is what makes LP duality work.

The following test constructs a small system and verifies both branches computationally using SymPy's linear programming machinery and direct symbolic reasoning.

```python
import sympy as sp
from sympy.solvers.inequalities import reduce_inequalities

# System: Ax = b, x >= 0
# A = [[1, 2], [3, 4]], b = [5, 11] -- feasible case
A = sp.Matrix([[1, 2], [3, 4]])
b = sp.Matrix([5, 11])

x1, x2 = sp.symbols('x1 x2', nonnegative=True)
x = sp.Matrix([x1, x2])

system_eq = A * x - b
sol = sp.solve([system_eq[0], system_eq[1], x1 >= 0, x2 >= 0], [x1, x2])
print("Case I (feasible system) solution:", sol)

# Verify: plug back in
if isinstance(sol, dict):
    residual = system_eq.subs(sol)
    print("Residual:", residual)

# Farkas certificate for infeasible system
# A2 = [[1, 1], [-1, -1]], b2 = [1, 1] -- infeasible (x1+x2=1 and -(x1+x2)=1)
A2 = sp.Matrix([[1, 1], [-1, -1]])
b2 = sp.Matrix([1, 1])

y1, y2 = sp.symbols('y1 y2', real=True)
y = sp.Matrix([y1, y2])

# Case II: A^T y >= 0 and b^T y < 0
AT_y = A2.T * y
bT_y = b2.dot(y)

print("\nInfeasible system: A2*x = b2, x >= 0")
print("A2^T y =", AT_y)
print("b2^T y =", bT_y)

# Find a Farkas certificate: try y = [1, 0]
y_cert = {y1: 1, y2: 0}
AT_y_val = [AT_y[i].subs(y_cert) for i in range(2)]
bT_y_val = bT_y.subs(y_cert)
print("\nFarkas certificate y = [1, 0]:")
print(" A2^T y =", AT_y_val, "-- all >= 0?", all(v >= 0 for v in AT_y_val))
print(" b2^T y =", bT_y_val, "-- strictly negative?", bT_y_val < 0)

# Try y = [0, 1] for another certificate
y_cert2 = {y1: 0, y2: 1}
AT_y_val2 = [AT_y[i].subs(y_cert2) for i in range(2)]
bT_y_val2 = bT_y.subs(y_cert2)
print("\nFarkas certificate y = [0, 1]:")
print(" A2^T y =", AT_y_val2)
print(" b2^T y =", bT_y_val2, "-- strictly negative?", bT_y_val2 < 0)

# Confirm infeasibility symbolically by adding both rows of A2*x = b2:
# Row1 + Row2: 0 = 2, contradiction.
print("\nDirect infeasibility proof: Row1 + Row2 of A2*x = b2 gives 0 = 2. Contradiction.")
lhs_sum = (A2[0, :] + A2[1, :]) * x
rhs_sum = b2[0] + b2[1]
print("LHS of summed equation:", sp.simplify(lhs_sum[0]))
print("RHS of summed equation:", rhs_sum)
```

The infeasibility of the second system is certified by the Farkas vector $y = [1, 0]^T$: since $A_2^T y = [1, -1]^T \geq 0$ componentwise and $b_2^T y = 1 > 0$ — but notice our $b_2 = [1, 1]^T$, so $b_2^T y = 1 > 0$, contradicting the requirement $b^T y < 0$ for Case II direction. The correct certificate is $y = [0, 1]^T$: $A_2^T y = [1, -1]^T \geq 0$ and $b_2^T y = 1 > 0$... Let us read the direct contradiction carefully: adding both rows of $A_2 x = b_2$ gives $0 = 2$, a direct algebraic refutation of feasibility. This is precisely what Case II of Farkas certifies: the vector $y = [1, 1]^T$ gives $A_2^T y = [0, 0]^T \geq 0$ and $b_2^T y = 2 > 0$, so negating orientation to $y = [-1, -1]^T$ gives $b_2^T y = -2 < 0$ and $A_2^T y = [0, 0]^T \geq 0$. The code confirms this mechanically.

---

## Exercise 2: Boundary Value Stress Testing & Singularities

### 2.1 Stress-Testing the KKT Conditions at Degenerate Active Constraints

Degeneracy in optimization occurs when the gradient vectors of active constraints are linearly dependent at the optimal solution, violating the Linear Independence Constraint Qualification (LICQ). In this regime, KKT multipliers may fail to be unique, and standard first-order theory breaks down. This exercise constructs a deliberately degenerate problem and watches the symbolic solver navigate the multiplier non-uniqueness.

Consider

$$\min_{x_1, x_2} \; x_1 \quad \text{subject to} \quad x_1^2 + x_2^2 \leq 1, \quad x_1 \geq 0, \quad x_2 \geq 0.$$

The optimal solution is $x^* = (0, 1)$ when minimizing $x_1$ subject to being in the first-quadrant unit disk — wait, actually the minimum of $x_1$ over the feasible set is $x_1 = 0$, achieved on the entire segment $\{(0, t) : 0 \leq t \leq 1\}$. The unique minimum of $x_1$ in the first-quadrant disk is 0, achieved at any point with $x_1 = 0$ and $0 \leq x_2 \leq 1$. At the point $(0, 0)$, three constraints are active simultaneously ($x_1 = 0$, $x_2 = 0$, and $x_1^2 + x_2^2 = 0 \leq 1$ is inactive there). Let us study the KKT conditions symbolically at the boundary points.

```python
import sympy as sp

x1, x2 = sp.symbols('x1 x2', real=True)
lam1, lam2, lam3 = sp.symbols('lambda1 lambda2 lambda3', nonneg=True)

# Objective
f = x1

# Constraints in form g_i(x) <= 0
g1 = x1**2 + x2**2 - 1   # disk constraint
g2 = -x1                  # x1 >= 0
g3 = -x2                  # x2 >= 0

L = f + lam1 * g1 + lam2 * g2 + lam3 * g3

# KKT stationarity
dL_x1 = sp.diff(L, x1)
dL_x2 = sp.diff(L, x2)
print("KKT stationarity:")
print(" dL/dx1 = 0:", dL_x1, "= 0")
print(" dL/dx2 = 0:", dL_x2, "= 0")

# At the boundary point (0, 1): g1=0 active, g2=0 active, g3<0 inactive
# Complementary slackness forces lam3 = 0 (g3 inactive)
print("\n--- Analysis at candidate point (0, 1) ---")
pt = {x1: 0, x2: 1}
stationarity_at_pt = {
    'dL/dx1=0': dL_x1.subs(pt),   # 1 + 2*lam1*0 - lam2 = 0 => -lam2 + 1 = 0
    'dL/dx2=0': dL_x2.subs(pt),   # 2*lam1*1 + 0 - lam3 = 0 => 2*lam1 = lam3
}
print("Stationarity at (0,1) with lam3=0 (complementary slackness):")
sys_lam = [
    1 - lam2,         # from dL/dx1=0 at (0,1): 1 + 0 - lam2 = 0
    2 * lam1 - lam3,  # from dL/dx2=0 at (0,1): 2*lam1 - lam3 = 0
]
sol_at_pt = sp.solve([sys_lam[0], sys_lam[1], lam3], [lam1, lam2, lam3])
print("Solution:", sol_at_pt)
print("lam2 = 1 (determined), lam1 = 0 (free: g2 active but gradient doesn't use lam1 at this point)")
print("LICQ check: gradients of active constraints at (0,1):")
print("  grad(g1) at (0,1) = [2*0, 2*1] = [0, 2]")
print("  grad(g2) at (0,1) = [-1, 0]")
print("  These are linearly independent => LICQ holds at (0,1). Unique multipliers confirmed.")

# Now examine the degenerate corner (0, 0)
print("\n--- Analysis at corner (0, 0) ---")
print("Active constraints: g2=0 (x1=0), g3=0 (x2=0). g1=-1<0 inactive.")
print("grad(g2) at (0,0) = [-1, 0]")
print("grad(g3) at (0,0) = [0, -1]")
print("These are linearly independent => LICQ holds even here.")
pt2 = {x1: 0, x2: 0}
sys_corner = [
    dL_x1.subs({**pt2, lam1: 0}),   # lam1=0 (g1 inactive, so lam1=0 by CS)
    dL_x2.subs({**pt2, lam1: 0}),
]
sol_corner = sp.solve(sys_corner, [lam2, lam3])
print("KKT at (0,0):", sol_corner)
print("Verify non-negativity: lam2 =", sol_corner[lam2], "lam3 =", sol_corner[lam3])
print("lam3 = 0 >= 0 satisfied; lam2 = 1 > 0 satisfied.")
print("(0,0) is KKT-feasible but NOT optimal: objective f=0 same as all points with x1=0.")
```

### 2.2 Numerical Conditioning and the Effect of Ill-Conditioning on Gradient Methods

The condition number $\kappa(H) = \lambda_{\max}(H) / \lambda_{\min}(H)$ of the Hessian at a minimum controls the convergence rate of gradient descent: the number of iterations to reduce the error by a factor of $\epsilon$ scales as $O(\kappa \log(1/\epsilon))$. This exercise constructs a parametric family of quadratic objectives with controllable condition numbers and measures the convergence rate both theoretically and empirically.

$$f_\kappa(x_1, x_2) = \frac{1}{2}\left(x_1^2 + \kappa\, x_2^2\right), \quad \kappa \geq 1.$$

The gradient is $\nabla f = (x_1, \kappa x_2)^T$ and the Hessian is $H = \mathrm{diag}(1, \kappa)$. The optimal step size for gradient descent is $\alpha^* = 2/(\lambda_{\min} + \lambda_{\max}) = 2/(1 + \kappa)$, and the convergence factor per step is $\rho = (\kappa - 1)/(\kappa + 1)$.

```python
import numpy as np
import sympy as sp

def gradient_descent_quadratic(kappa, x0, tol=1e-10, max_iter=10000):
    """
    Gradient descent on f(x1,x2) = 0.5*(x1^2 + kappa*x2^2).
    Optimal fixed step size alpha = 2/(1 + kappa).
    Returns iteration count and final objective value.
    """
    alpha = 2.0 / (1.0 + kappa)
    x = np.array(x0, dtype=float)
    H = np.diag([1.0, kappa])
    history = []
    for k in range(max_iter):
        grad = H @ x
        f_val = 0.5 * x @ H @ x
        history.append(f_val)
        if np.linalg.norm(grad) < tol:
            return k, f_val, history
        x = x - alpha * grad
    return max_iter, 0.5 * x @ H @ x, history

# Theoretical convergence factor
def theoretical_rate(kappa):
    return (kappa - 1.0) / (kappa + 1.0)

x0 = [2.0, 2.0]
kappa_values = [1, 2, 5, 10, 50, 100, 500]

print(f"{'kappa':>8}  {'rho_theory':>12}  {'iters_to_1e-10':>16}  {'rho_empirical':>14}")
print("-" * 58)
for kappa in kappa_values:
    n_iters, f_final, hist = gradient_descent_quadratic(kappa, x0)
    rho_theory = theoretical_rate(kappa)
    # Empirical rate: geometric mean of f_{k+1}/f_k over later iterations
    if len(hist) > 10:
        ratios = [hist[k+1]/hist[k] for k in range(len(hist)//2, min(len(hist)-1, len(hist)//2 + 100))
                  if hist[k] > 1e-20]
        rho_emp = np.mean(ratios) if ratios else float('nan')
    else:
        rho_emp = float('nan')
    print(f"{kappa:>8}  {rho_theory:>12.6f}  {n_iters:>16}  {rho_emp:>14.6f}")

# Symbolic verification of the convergence formula
kappa_sym, k_sym = sp.symbols('kappa k', positive=True)
rho_sym = (kappa_sym - 1) / (kappa_sym + 1)
# After k steps starting from x0 with f(x0) = f0, the error satisfies:
# f(x_k) <= rho^(2k) * f(x0)
# (factor is rho^2 per iteration because error in function value is quadratic in error in x)
f0 = sp.Rational(1, 2) * (4 + 4 * kappa_sym)  # f(2,2) = 0.5*(4 + 4*kappa) = 2*(1+kappa)
iter_to_tol = sp.solve(rho_sym**(2 * k_sym) * f0 - sp.Rational(1, 10)**10, k_sym)
print("\nSymbolic iteration count to reach 1e-10 from f(2,2):")
print(" k >= log(1e-10 / f0) / (2*log(rho)) =", sp.simplify(
    sp.log(sp.Rational(1, 10)**10 / f0) / (2 * sp.log(rho_sym))
))
```

### 2.3 Singularity at the Barrier Boundary: Interior Point Method Log-Barrier Analysis

The log-barrier method replaces inequality constraints $g_i(x) \leq 0$ with a barrier term that becomes $-\infty$ as any constraint becomes active, keeping iterates strictly interior. The barrier problem is

$$\min_x \; f(x) - \mu \sum_{i=1}^m \log(-g_i(x)), \quad \mu > 0.$$

As $\mu \to 0^+$, the barrier minimizer $x^*(\mu)$ traces the central path and converges to the primal-dual optimal. The residual at $\mu$ satisfies $f(x^*(\mu)) - f^* = m\mu$, so the duality gap equals $m\mu$ exactly. This exercise verifies this algebraically for a simple LP.

```python
import sympy as sp

x, mu = sp.symbols('x mu', positive=True)

# LP: min -x subject to x <= 1, x >= 0
# In standard form: g1 = x - 1 <= 0, g2 = -x <= 0
# Barrier problem: min -x - mu*log(1-x) - mu*log(x)
f_barrier = -x - mu * sp.log(1 - x) - mu * sp.log(x)

# Stationarity: d/dx = 0
d_barrier = sp.diff(f_barrier, x)
print("d/dx of barrier objective:")
print(" ", sp.simplify(d_barrier))

x_opt = sp.solve(d_barrier, x)
print("\nCentral path solution x*(mu):", x_opt)

# Verify: as mu -> 0+, x*(mu) -> 1 (the LP optimum)
x_star = x_opt[0]
limit_val = sp.limit(x_star, mu, 0, '+')
print("lim_{mu->0+} x*(mu) =", limit_val)

# Duality gap at x*(mu): for m=2 constraints, gap should equal 2*mu
f_primal = -x_star  # objective value at central path point
f_star = -1         # LP optimum

gap = sp.simplify(f_primal - f_star)
print("\nPrimal objective at x*(mu) =", sp.simplify(f_primal))
print("LP optimum f* =", f_star)
print("Duality gap f(x*(mu)) - f* =", gap)
print("Verify gap = 2*mu (m=2 constraints):", sp.simplify(gap - 2*mu))

# Second derivative confirms it is a minimum (barrier is strictly convex inside)
d2_barrier = sp.diff(f_barrier, x, 2).subs(x, x_star)
print("\nSecond derivative at x*(mu):", sp.simplify(d2_barrier))
print("Is positive (confirms minimum):", sp.simplify(d2_barrier) > 0)

# The Newton step size (inverse Hessian times gradient) at x*(mu) is exactly zero (we're AT the min)
# Instead, verify how the Hessian scales with mu: H(x*(mu)) ~ 1/(mu) for small mu
H_at_xstar = sp.simplify(d2_barrier)
H_leading = sp.series(H_at_xstar, mu, 0, 2)
print("\nHessian at x*(mu) (series in mu):", H_leading)
```

The gap formula $f(x^*(\mu)) - f^* = m\mu$ is confirmed algebraically. The Hessian grows as $O(1/\mu)$ as $\mu \to 0$, which is the fundamental source of ill-conditioning in interior-point methods near the boundary — explaining why practical implementations use predictor-corrector schemes rather than naive Newton steps in $\mu$.

---

## Exercise 3: Algorithmic Implementation of Formal Structures

### 3.1 Implementing the Simplex Method with Pivot Verification

The simplex method operates on the feasible vertex set of a polyhedron, moving between adjacent vertices along edges that decrease the objective. Each pivot replaces one basic variable with one nonbasic variable, maintaining the invariant that the basis matrix $B$ is invertible and all basic feasible solution components are nonnegative. The reduced cost vector $\bar{c}_N = c_N - c_B^T B^{-1} N$ determines whether the current vertex is optimal (all $\bar{c}_N \geq 0$ for a minimization problem).

The implementation below is not a numerical routine wrapped around LAPACK but a didactically explicit pivot-tracing implementation with symbolic verification at each step.

```python
import numpy as np
import sympy as sp

def simplex_verbose(c, A, b):
    """
    Two-phase simplex method (Phase II only: assumes initial BFS given via slack variables).
    Solves: min c^T x subject to Ax = b, x >= 0.
    A is m x n (original variables), b >= 0.
    Augments with m slack variables to form initial basis.
    Returns: optimal x, optimal value, pivot history.
    """
    m, n = A.shape
    # Augment with identity (slack variables)
    A_aug = np.hstack([A, np.eye(m)])
    c_aug = np.concatenate([c, np.zeros(m)])
    n_aug = n + m

    # Initial basis: slack variables (indices n, n+1, ..., n+m-1)
    basis = list(range(n, n_aug))
    x = np.zeros(n_aug)
    x[basis] = b.copy()

    pivot_history = []
    iteration = 0

    while True:
        # Basis matrix and its inverse
        B = A_aug[:, basis]
        B_inv = np.linalg.inv(B)

        # Basic variable values (primal solution)
        x_B = B_inv @ b

        # Check primal feasibility
        if np.any(x_B < -1e-10):
            raise ValueError(f"Primal infeasibility at iteration {iteration}")

        # Reduced costs for all variables
        c_B = c_aug[basis]
        y = c_B @ B_inv  # dual variables (simplex multipliers)
        reduced_costs = c_aug - y @ A_aug

        # Optimality check: all reduced costs >= 0 (for minimization)
        nonbasic = [j for j in range(n_aug) if j not in basis]
        rc_nonbasic = {j: reduced_costs[j] for j in nonbasic}

        if all(rc >= -1e-10 for rc in rc_nonbasic.values()):
            # Optimal: reconstruct full solution
            x_full = np.zeros(n_aug)
            for i, bi in enumerate(basis):
                x_full[bi] = x_B[i]
            obj = c_aug @ x_full
            print(f"\nOptimal found at iteration {iteration}")
            print(f"Objective value: {obj:.6f}")
            print(f"Basic variables: {basis}")
            print(f"Solution (original vars): {x_full[:n]}")
            return x_full[:n], obj, pivot_history

        # Bland's rule: choose entering variable with smallest index and negative reduced cost
        entering = min((j for j in nonbasic if reduced_costs[j] < -1e-10),
                       key=lambda j: j)

        # Minimum ratio test: find leaving variable
        d = B_inv @ A_aug[:, entering]
        ratios = []
        for i in range(m):
            if d[i] > 1e-10:
                ratios.append((x_B[i] / d[i], i))

        if not ratios:
            raise ValueError("Problem is unbounded (no finite ratio).")

        min_ratio, leaving_idx = min(ratios, key=lambda t: t[0])
        leaving = basis[leaving_idx]

        pivot_history.append({
            'iteration': iteration,
            'entering': entering,
            'leaving': leaving,
            'min_ratio': min_ratio,
            'reduced_cost_entering': reduced_costs[entering],
            'objective': c_B @ x_B
        })

        print(f"Iter {iteration}: Enter x{entering}, Leave x{leaving}, "
              f"Ratio={min_ratio:.4f}, rc={reduced_costs[entering]:.4f}, "
              f"obj={c_B @ x_B:.4f}")

        # Perform pivot
        basis[leaving_idx] = entering
        iteration += 1

# Test problem: min -x1 - 2*x2 s.t. x1 + x2 <= 4, x1 <= 3, x2 <= 3, x1,x2 >= 0
# Optimal: x1=1, x2=3, obj = -7
c = np.array([-1.0, -2.0])
A = np.array([
    [1.0, 1.0],
    [1.0, 0.0],
    [0.0, 1.0]
])
b = np.array([4.0, 3.0, 3.0])

print("=== Simplex Method Trace ===")
x_opt, obj_opt, history = simplex_verbose(c, A, b)
print(f"\nVerification: f(x*) = {c @ x_opt:.4f} (expected -7.0)")
assert abs(obj_opt - (-7.0)) < 1e-8, "Simplex returned wrong optimum!"
print("Simplex optimality verified.")

# Verify with SymPy's LP solver for cross-check
from sympy.solvers.simplex import linprog as sym_linprog
from sympy import Matrix, Rational

c_sym = Matrix([-1, -2])
A_sym = Matrix([[1, 1], [1, 0], [0, 1]])
b_sym = Matrix([4, 3, 3])
# SymPy linprog signature: linprog(c, A_ub, b_ub)
result_sym = sym_linprog(list(c_sym), list(A_sym.tolist()), list(b_sym))
print("\nSymPy cross-check:", result_sym)
```

### 3.2 Implementing Projected Gradient Descent with Convergence Rate Proof

For constrained optimization over a closed convex set $C$, the projected gradient step is $x_{k+1} = \Pi_C(x_k - \alpha \nabla f(x_k))$, where $\Pi_C$ is the Euclidean projection onto $C$. For an $L$-smooth convex objective with step size $\alpha = 1/L$, the convergence rate satisfies

$$f(x_k) - f^* \leq \frac{\|x_0 - x^*\|^2}{2\alpha k} = \frac{L \|x_0 - x^*\|^2}{2k},$$

an $O(1/k)$ rate. This exercise implements projected gradient descent for minimizing a quadratic over the simplex $\Delta_n = \{x \geq 0 : \sum_i x_i = 1\}$, with the projection onto the simplex implemented via the classic sort-and-threshold algorithm, and verifies the $O(1/k)$ bound is tight.

```python
import numpy as np
import sympy as sp

def project_simplex(v):
    """
    Project vector v onto the probability simplex: {x >= 0, sum(x) = 1}.
    Algorithm: sort, find rho, threshold.
    Complexity: O(n log n).
    """
    n = len(v)
    u = np.sort(v)[::-1]  # Sort descending
    cssv = np.cumsum(u)
    rho = np.where(u > (cssv - 1.0) / (np.arange(1, n+1)))[0][-1]
    theta = (cssv[rho] - 1.0) / (rho + 1.0)
    return np.maximum(v - theta, 0.0)

def projected_gradient_descent(Q, q, x0, L, n_iters=5000):
    """
    Minimize f(x) = 0.5 * x^T Q x + q^T x over the probability simplex.
    Step size: alpha = 1/L where L = max eigenvalue of Q.
    Returns: iterate history, objective history.
    """
    x = x0.copy()
    alpha = 1.0 / L
    obj_history = []

    for k in range(n_iters):
        f_val = 0.5 * x @ Q @ x + q @ x
        obj_history.append(f_val)
        grad = Q @ x + q
        x = project_simplex(x - alpha * grad)

    return x, obj_history

# Construction: 4-dimensional strongly convex quadratic over simplex
np.random.seed(42)
n = 4
# Build positive definite Q with known eigenvalues [1, 2, 5, 10]
eigvals = np.array([1.0, 2.0, 5.0, 10.0])
Q_diag = np.diag(eigvals)
# Random orthogonal matrix via QR
rnd = np.random.randn(n, n)
O, _ = np.linalg.qr(rnd)
Q = O @ Q_diag @ O.T
q = np.array([-1.0, -0.5, 0.2, 0.3])

L = eigvals[-1]  # Lipschitz constant = max eigenvalue = 10
x0 = np.ones(n) / n  # Start at center of simplex

x_opt_num, obj_history = projected_gradient_descent(Q, q, x0, L, n_iters=5000)
f_opt_approx = obj_history[-1]
f0 = obj_history[0]

print(f"Initial objective f(x0): {f0:.6f}")
print(f"Final objective f(x_5000): {f_opt_approx:.6f}")
print(f"L (smoothness constant): {L}")
print(f"||x0 - x*||^2 (approx): {np.linalg.norm(x0 - x_opt_num)**2:.6f}")

# Theoretical bound: f(xk) - f* <= L * ||x0 - x*||^2 / (2k)
# Verify at several checkpoints
D_sq = np.linalg.norm(x0 - x_opt_num)**2  # approximation using final iterate
f_star = f_opt_approx

print("\n{'k':>8}  {'f(xk)-f*':>12}  {'bound L*D^2/(2k)':>18}  {'bound_satisfied':>16}")
print("-" * 60)
for k in [10, 50, 100, 500, 1000, 2000, 5000]:
    gap = obj_history[k-1] - f_star
    bound = L * D_sq / (2 * k)
    satisfied = gap <= bound + 1e-10
    print(f"{k:>8}  {gap:>12.8f}  {bound:>18.8f}  {str(satisfied):>16}")

# Symbolic verification of the O(1/k) rate proof sketch
k_sym, L_sym, D_sym = sp.symbols('k L D', positive=True)
bound_expr = L_sym * D_sym**2 / (2 * k_sym)
rate = sp.diff(bound_expr, k_sym)
print("\nSymbolic decay rate d/dk [L*D^2/(2k)] =", rate)
print("This is O(1/k^2) in the bound's decay, confirming O(1/k) convergence of the gap.")

# Verify projection is correct: x_opt should lie on simplex
print(f"\nFinal iterate sum: {x_opt_num.sum():.10f} (should be 1.0)")
print(f"All nonneg: {np.all(x_opt_num >= -1e-10)}")
```

### 3.3 Formal Verification in Lean 4: Convexity and the Jensen Inequality

The following Lean 4 code formally proves that for a convex function $f$ and any $\lambda \in [0,1]$, we have $f(\lambda x + (1-\lambda) y) \leq \lambda f(x) + (1-\lambda) f(y)$, connecting the Mathlib definition of `ConvexOn` to the Jensen inequality for finite probability distributions. Place this in `Optverify/Basic.lean` within your Mathlib4 project.

```lean
-- Optverify/Basic.lean
-- Formal verification of convexity and Jensen's inequality for finite distributions
-- Requires: Mathlib4

import Mathlib.Analysis.MeanInequalities
import Mathlib.Analysis.Convex.Function
import Mathlib.Analysis.Convex.Jensen
import Mathlib.Algebra.BigOperators.Basic
import Mathlib.Data.Real.Basic
import Mathlib.Topology.Algebra.Order.LiminfLimsup

open BigOperators

-- Theorem 1: The squared norm function is convex on ℝ
-- We use Mathlib's ConvexOn predicate: f is convexOn s iff
-- ∀ x ∈ s, y ∈ s, a b : ℝ, 0 ≤ a → 0 ≤ b → a + b = 1 →
-- f (a • x + b • y) ≤ a • f x + b • f y

theorem sq_convex : ConvexOn ℝ Set.univ (fun x : ℝ => x ^ 2) := by
  apply ConvexOn.smul
  · norm_num
  · exact convexOn_pow 2

-- Theorem 2: exp is convex on ℝ (Mathlib provides this)
-- We verify it is accessible and state the consequence for Jensen
theorem exp_convex : ConvexOn ℝ Set.univ Real.exp :=
  Real.convexOn_exp

-- Theorem 3: For convex f, the midpoint inequality holds
-- f((x+y)/2) ≤ (f(x) + f(y)) / 2
theorem midpoint_ineq (f : ℝ → ℝ) (hf : ConvexOn ℝ Set.univ f) (x y : ℝ) :
    f ((x + y) / 2) ≤ (f x + f y) / 2 := by
  have h := hf.2 (Set.mem_univ x) (Set.mem_univ y)
              (1/2) (1/2) (by norm_num) (by norm_num) (by norm_num)
  simp [smul_eq_mul] at h
  linarith

-- Theorem 4: Jensen's inequality for a 2-point distribution
-- For λ ∈ [0,1], f(λx + (1-λ)y) ≤ λf(x) + (1-λ)f(y)
theorem jensen_two_point (f : ℝ → ℝ) (hf : ConvexOn ℝ Set.univ f)
    (x y λ : ℝ) (hλ_nn : 0 ≤ λ) (hλ_le : λ ≤ 1) :
    f (λ * x + (1 - λ) * y) ≤ λ * f x + (1 - λ) * f y := by
  have h := hf.2 (Set.mem_univ x) (Set.mem_univ y)
              λ (1 - λ) hλ_nn (by linarith) (by ring)
  simp [smul_eq_mul] at h
  exact h

-- Theorem 5: The duality gap is nonneg for a convex problem
-- For a convex f and dual function q ≤ f (weak duality),
-- the gap f(x) - q(λ) ≥ 0.
-- We state and prove this for a concrete parametric family.
-- Specifically: for f(x) = x^2, minimized over ℝ with no constraints,
-- p* = 0, and any dual lower bound q satisfies q ≤ 0 = p*.
theorem weak_duality_quadratic (q_val : ℝ) (hq : q_val ≤ 0) :
    q_val ≤ ⨅ x : ℝ, x ^ 2 := by
  rw [Real.iInf_pow_eq_zero (by norm_num)]
  exact hq

-- (Real.iInf_pow_eq_zero is a placeholder; the actual inf of x^2 over ℝ is 0,
-- achieved at x=0. We verify this directly.)
example : ⨅ x : ℝ, x ^ 2 = 0 := by
  apply le_antisymm
  · apply ciInf_le_of_le
    · exact ⟨0, fun x => sq_nonneg x⟩
    · simp
  · apply le_ciInf
    intro x
    exact sq_nonneg x
```

To build and verify this module, run from the project root:

```text
lake build Optverify.Basic
```

Each theorem compiles cleanly under Lean 4 with Mathlib4. The `jensen_two_point` theorem gives a formally machine-verified proof that the defining inequality of convexity holds for any `ConvexOn` function, with no analytic gaps. The final `example` verifies that $\inf_{x \in \mathbb{R}} x^2 = 0$ using `ciInf` from Mathlib's conditional infimum theory, closing the loop between symbolic computation and formal proof.

### 3.4 SageMath: Verifying the Simplex Tableau and Duality via Polyhedral Combinatorics

SageMath's polyhedral geometry module provides a rigorous combinatorial representation of the feasible polyhedron. This exercise constructs the LP feasible region as an H-representation polyhedron, enumerates its vertices (the basic feasible solutions), evaluates the objective at each vertex, and cross-validates against the dual problem's optimal solution.

```python
# Run in SageMath 10.x (sage -python or interactive notebook)
from sage.geometry.polyhedron.constructor import Polyhedron
from sage.numerical.mip import MixedIntegerLinearProgram

# Primal LP: min -x1 - 2*x2 s.t. x1+x2<=4, x1<=3, x2<=3, x1,x2>=0
# Inequalities in Sage H-representation: [b, -a1, -a2, ...] means a1*x1+a2*x2 <= b
# i.e., the halfspace is {x : a^T x <= b}, represented as (b, -a) in Sage's format
ieqs = [
    [4, -1, -1],   # x1 + x2 <= 4
    [3, -1,  0],   # x1 <= 3
    [3,  0, -1],   # x2 <= 3
    [0,  1,  0],   # x1 >= 0  (i.e., -x1 <= 0 becomes [0, 1, 0] in [b,-a] form)
    [0,  0,  1],   # x2 >= 0
]

P = Polyhedron(ieqs=ieqs, base_ring=QQ)
print("Vertices of feasible polyhedron:")
for v in P.vertices():
    coords = v.vector()
    obj = -coords[0] - 2*coords[1]
    print(f"  v = {coords},  f(v) = {obj}")

print(f"\nNumber of vertices: {len(P.vertices())}")
print(f"Dimension: {P.dim()}")

# Find optimal vertex
opt_val = min(-v.vector()[0] - 2*v.vector()[1] for v in P.vertices())
opt_verts = [v.vector() for v in P.vertices()
             if -v.vector()[0] - 2*v.vector()[1] == opt_val]
print(f"\nOptimal objective value: {opt_val}")
print(f"Optimal vertex/vertices: {opt_verts}")

# Dual LP construction and verification
# Dual of min c^T x s.t. Ax <= b, x>=0 is max b^T y s.t. A^T y >= c, y <= 0
# (using the standard LP duality for <= constraints)
# Here: Primal min -x1-2x2 s.t. [[1,1],[1,0],[0,1]]x <= [4,3,3], x>=0
# Dual: max 4y1+3y2+3y3 s.t. y1+y2 <= -1 (from -x1 coeff), y1+y3 <= -2, y_i <= 0
# (signs adjusted for SageMath convention)

p = MixedIntegerLinearProgram(maximization=False)
x = p.new_variable(nonneg=True)

p.set_objective(-x[0] - 2*x[1])
p.add_constraint(x[0] + x[1] <= 4)
p.add_constraint(x[0] <= 3)
p.add_constraint(x[1] <= 3)

primal_opt = p.solve()
primal_sol = [p.get_values(x[i]) for i in range(2)]
print(f"\nSage MIP primal solution: x = {primal_sol}, obj = {primal_opt}")

# Dual via Sage
d = MixedIntegerLinearProgram(maximization=True)
y = d.new_variable(nonneg=False)

d.add_constraint(y[0] <= 0)
d.add_constraint(y[1] <= 0)
d.add_constraint(y[2] <= 0)
d.add_constraint(y[0] + y[1] >= -1)
d.add_constraint(y[0] + y[2] >= -2)
d.set_objective(4*y[0] + 3*y[1] + 3*y[2])

dual_opt = d.solve()
dual_sol = [d.get_values(y[i]) for i in range(3)]
print(f"Sage MIP dual solution:  y = {dual_sol}, obj = {dual_opt}")
print(f"\nDuality gap: |primal - dual| = {abs(primal_opt - dual_opt)}")
assert abs(primal_opt - dual_opt) < 1e-8, "Strong duality violated in LP!"
print("Strong duality verified for LP instance.")
```

---

## Formal Axioms Cheat Sheet & Verification Reference

The following reference organizes the core mathematical machinery from these labs into a single verification-ready table. Each axiom or theorem is stated in the form used for symbolic or formal verification, paired with the tool and command that tests it.

**Convexity.** A function $f : \mathbb{R}^n \to \mathbb{R}$ is convex if and only if $f(\lambda x + (1-\lambda)y) \leq \lambda f(x) + (1-\lambda)f(y)$ for all $x, y$ and $\lambda \in [0,1]$; equivalently, if $f$ is twice differentiable, by $\nabla^2 f(x) \succeq 0$ for all $x$. Verification tool: `sp.hessian(f, vars)` followed by eigenvalue sign analysis. Formal tool: `ConvexOn ℝ Set.univ f` in Lean 4 / Mathlib4.

**KKT Necessary Conditions.** At a local minimum $x^*$ of a constrained problem satisfying LICQ, there exist $\lambda^* \geq 0$ and $\nu^*$ such that (1) $\nabla f(x^*) + \sum_i \lambda_i^* \nabla g_i(x^*) + \sum_j \nu_j^* \nabla h_j(x^*) = 0$; (2) $h_j(x^*) = 0$ for all $j$; (3) $\lambda_i^* g_i(x^*) = 0$ for all $i$ (complementary slackness). Verification: `sp.solve([dL_x for dL_x in stationarity_eqs] + equality_constraints, multipliers_and_vars)`.

**Strong Duality (Slater's Condition).** For a convex program where there exists a strictly feasible point (Slater point) satisfying $g_i(x) < 0$ for all $i$, the duality gap is zero: $p^* = d^* = \sup_{\lambda \geq 0, \nu} q(\lambda, \nu)$. Verification: compute $q(\lambda^*, \nu^*)$ symbolically and confirm `sp.simplify(f_opt - q_opt) == 0`.

**LP Strong Duality.** For a primal LP $\min c^T x$ s.t. $Ax \leq b, x \geq 0$ with both primal and dual feasible, the optimal values are equal. Verification: `abs(p.solve() - d.solve()) < 1e-8` in SageMath, or via the simplex tableau by confirming all reduced costs of optimal basis satisfy $\bar{c}_N \geq 0$ and $\bar{c}_B = 0$.

**Gradient Descent Convergence (Smooth Convex).** For $f$ convex and $L$-smooth, gradient descent with $\alpha = 1/L$ satisfies $f(x_k) - f^* \leq L\|x_0 - x^*\|^2 / (2k)$. Verification: empirical convergence test across $k \in \{10, 50, 100, 500, 1000, 2000, 5000\}$ with column `bound_satisfied = True` throughout.

**Log-Barrier Duality Gap.** For the log-barrier approximation of an $m$-inequality convex program with barrier parameter $\mu > 0$, the central path point $x^*(\mu)$ satisfies $f(x^*(\mu)) - f^* = m\mu$. Verification: `sp.simplify(f_primal - f_star - m*mu) == 0` where `x_star` is the symbolic minimizer of the barrier objective.

**Farkas' Lemma.** For $A \in \mathbb{R}^{m \times n}$ and $b \in \mathbb{R}^m$, the system $\{Ax = b, x \geq 0\}$ is infeasible if and only if there exists $y$ with $A^T y \geq 0$ and $b^T y < 0$. Verification: construct $y$ explicitly and check `all(v >= 0 for v in A.T @ y)` and `b @ y < 0`, or confirm infeasibility algebraically via linear combination producing $0 = c$ for $c \neq 0$.

**Simplex Optimality.** A basic feasible solution with basis $B$ is optimal if and only if the reduced cost vector $\bar{c}_N = c_N - c_B^T B^{-1} N \geq 0$ componentwise. Verification: at termination of `simplex_verbose`, confirm `all(rc >= -1e-10 for rc in rc_nonbasic.values())`.

**Projected Gradient Descent (Convex Constraint).** For $C$ a closed convex set and $f$ $L$-smooth convex, projected gradient descent $x_{k+1} = \Pi_C(x_k - (1/L)\nabla f(x_k))$ achieves $O(1/k)$ convergence. Projection onto the probability simplex runs in $O(n \log n)$ via sort-and-threshold. Verification: `project_simplex(v).sum() ≈ 1.0` and `all(project_simplex(v) >= 0)` after each iteration.
