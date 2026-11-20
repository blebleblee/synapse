# Operational Verification Labs: Dynamical Systems

## Objective & Mathematical Computing Setup

This guide treats dynamical systems as objects of formal mathematical verification, not merely simulation. The goal is to establish rigorous computational proofs of qualitative properties: equilibrium existence and classification, limit cycle structure, stability in the sense of Lyapunov, bifurcation geometry, and the topological invariants that govern long-run behavior. Every result you produce here will be verified twice — once symbolically through SymPy or SageMath, and once through formal algebraic manipulation whose steps are themselves checkable. By the end of these labs you will have a working methodology for approaching any autonomous system $\dot{x} = f(x)$ with the same systematic rigor applied to a theorem in a proof assistant.

The computational environment requires Python 3.11 or later, with SymPy for symbolic algebra and calculus, NumPy for numerical cross-validation, and SageMath for Gröbner basis computations and polynomial system solving. Install and verify the environment as follows.

```text
pip install sympy numpy matplotlib scipy
python -c "import sympy; print(sympy.__version__)"
python -c "import numpy; print(numpy.__version__)"
```

For SageMath, use the standalone distribution or the SageMath kernel inside JupyterLab. The Lean 4 proof assistant with the Mathlib4 library handles formal structural verification in Exercise 3. Install via the `elan` toolchain manager:

```bash
curl https://raw.githubusercontent.com/leanprover/elan/master/elan-init.sh -sSf | sh
lake new dynamical_systems_lab
cd dynamical_systems_lab
echo 'require mathlib from git "https://github.com/leanprover-community/mathlib4"' >> lakefile.lean
lake update
```

Throughout this guide, every planar autonomous system takes the standard form $\dot{x} = f(x, y)$, $\dot{y} = g(x, y)$ where $f, g \in C^1(\mathbb{R}^2)$. An equilibrium point is any $(x^*, y^*)$ satisfying $f(x^*, y^*) = 0$ and $g(x^*, y^*) = 0$ simultaneously. The Jacobian matrix $J(x^*, y^*)$ evaluated at an equilibrium classifies its local behavior: the eigenvalues $\lambda_{1,2}$ of $J$ determine whether the equilibrium is a stable node ($\lambda_1, \lambda_2 < 0$, real), unstable node ($\lambda_1, \lambda_2 > 0$, real), saddle ($\lambda_1 < 0 < \lambda_2$), stable spiral ($\text{Re}(\lambda) < 0$, complex), unstable spiral ($\text{Re}(\lambda) > 0$, complex), or center ($\text{Re}(\lambda) = 0$, complex). These classifications are not mere labels; they encode the topological structure of the local phase portrait and, through the Hartman–Grobman theorem, govern the qualitative behavior of the nonlinear system in a neighborhood of each hyperbolic equilibrium.

---

## Exercise 1: Computational Verification of Core Theorems

### 1.1 Equilibrium Analysis and Jacobian Classification of the Lotka–Volterra System

The Lotka–Volterra predator–prey system is an ideal first subject because it admits two qualitatively distinct equilibria whose classification is analytically non-trivial: a saddle at the origin and a center at an interior point. The system is

$$\dot{x} = \alpha x - \beta x y, \qquad \dot{y} = \delta x y - \gamma y$$

where $\alpha, \beta, \gamma, \delta > 0$ are real parameters. The two equilibria are $E_0 = (0, 0)$ and $E^* = (\gamma/\delta,\, \alpha/\beta)$. At $E_0$, the Jacobian is diagonal with entries $\alpha$ and $-\gamma$, so the eigenvalues are $\lambda_1 = \alpha > 0$ and $\lambda_2 = -\gamma < 0$, confirming a saddle. At $E^*$, the Jacobian has zero trace and positive determinant $\alpha\gamma$, producing purely imaginary eigenvalues $\lambda_{1,2} = \pm i\sqrt{\alpha\gamma}$, which classifies $E^*$ as a center for the linearized system. The following SymPy program verifies every step of this classification symbolically, leaving no algebraic step unconfirmed.

```python
import sympy as sp

# Define symbolic parameters and state variables
alpha, beta, gamma, delta = sp.symbols('alpha beta gamma delta', positive=True)
x, y = sp.symbols('x y', real=True)

# Define the vector field
f = alpha*x - beta*x*y
g = delta*x*y - gamma*y

# Compute all equilibria by solving f=0, g=0 simultaneously
equilibria = sp.solve([f, g], [x, y], dict=True)
print("Equilibria:")
for eq in equilibria:
    print("  ", eq)

# Construct the Jacobian matrix of the vector field
F = sp.Matrix([f, g])
state = sp.Matrix([x, y])
J = F.jacobian(state)
print("\nJacobian (symbolic):")
sp.pprint(J)

# Classify E0 = (0, 0)
J_E0 = J.subs([(x, 0), (y, 0)])
eigenvals_E0 = J_E0.eigenvals()
print("\nJacobian at E0 = (0,0):")
sp.pprint(J_E0)
print("Eigenvalues at E0:", eigenvals_E0)

# Classify E* = (gamma/delta, alpha/beta)
x_star = gamma / delta
y_star = alpha / beta
J_Estar = J.subs([(x, x_star), (y, y_star)])
print("\nJacobian at E* = (gamma/delta, alpha/beta):")
sp.pprint(J_Estar)

# Compute trace and determinant to classify without full eigenvalue computation
tr_Estar = sp.simplify(J_Estar.trace())
det_Estar = sp.simplify(J_Estar.det())
print("Trace at E*:", tr_Estar)
print("Determinant at E*:", det_Estar)

# Characteristic polynomial and eigenvalues at E*
char_poly = J_Estar.charpoly(sp.Symbol('lam'))
print("Characteristic polynomial at E*:", char_poly)
eigenvals_Estar = J_Estar.eigenvals()
print("Eigenvalues at E*:", eigenvals_Estar)

# Discriminant of the characteristic polynomial
lam = sp.Symbol('lam')
cpoly_expr = char_poly.as_expr()
discriminant = sp.simplify(sp.discriminant(cpoly_expr, lam))
print("Discriminant of char poly at E*:", discriminant)
# A negative discriminant confirms complex conjugate eigenvalues
```

When you execute this, SymPy returns `trace = 0` and `det = alpha*gamma > 0` at $E^*$ symbolically, confirming purely imaginary eigenvalues $\pm i\sqrt{\alpha\gamma}$ without numerical substitution. The discriminant of the characteristic polynomial evaluates to $-4\alpha\gamma < 0$, which is negative because both parameters are positive, formally confirming that no real eigenvalues exist at the interior equilibrium.

### 1.2 Conservation Law Verification via the First Integral

The Lotka–Volterra system is Hamiltonian on the positive quadrant. Its conserved quantity, or first integral, is

$$H(x, y) = \delta x - \gamma \ln x + \beta y - \alpha \ln y$$

A function $H$ is a first integral of $\dot{x} = f(x,y)$, $\dot{y} = g(x,y)$ if and only if its total time derivative vanishes identically along all trajectories: $\dot{H} = \partial_x H \cdot f + \partial_y H \cdot g \equiv 0$. Verifying this symbolically confirms that every orbit lies on a level curve of $H$, which is precisely what forces $E^*$ to be a true center (not merely a linearization artifact) for the nonlinear system.

```python
import sympy as sp

alpha, beta, gamma, delta = sp.symbols('alpha beta gamma delta', positive=True)
x, y = sp.symbols('x y', positive=True)

# Define the first integral H(x, y)
H = delta*x - gamma*sp.ln(x) + beta*y - alpha*sp.ln(y)

# Define the vector field
f = alpha*x - beta*x*y
g = delta*x*y - gamma*y

# Compute dH/dt along trajectories: Lie derivative of H w.r.t. (f, g)
dH_dt = sp.diff(H, x)*f + sp.diff(H, y)*g
dH_dt_simplified = sp.simplify(dH_dt)
print("dH/dt along trajectories:", dH_dt_simplified)
# Expected output: 0

# Verify that the gradient of H vanishes at E*
x_star = gamma / delta
y_star = alpha / beta
grad_H_x = sp.diff(H, x).subs([(x, x_star), (y, y_star)])
grad_H_y = sp.diff(H, y).subs([(x, x_star), (y, y_star)])
grad_H_x_simplified = sp.simplify(grad_H_x)
grad_H_y_simplified = sp.simplify(grad_H_y)
print("dH/dx at E*:", grad_H_x_simplified)   # Expected: 0
print("dH/dy at E*:", grad_H_y_simplified)   # Expected: 0

# Verify H is strictly convex at E* by checking the Hessian is positive definite
H_xx = sp.diff(H, x, 2).subs([(x, x_star), (y, y_star)])
H_yy = sp.diff(H, y, 2).subs([(x, x_star), (y, y_star)])
H_xy = sp.diff(H, x, y).subs([(x, x_star), (y, y_star)])
Hessian = sp.Matrix([[H_xx, H_xy], [H_xy, H_yy]])
print("\nHessian of H at E*:")
sp.pprint(sp.simplify(Hessian))
det_Hessian = sp.simplify(Hessian.det())
print("det(Hessian):", det_Hessian)   # Must be > 0 for positive definiteness
print("H_xx at E*:", sp.simplify(H_xx))  # Must be > 0
```

The symbolic output `dH/dt = 0` is a formal proof that $H$ is conserved. The Hessian computation confirms that $E^*$ is a strict local minimum of $H$ on the positive quadrant: $H_{xx} = \gamma\delta/\gamma^2 = \delta/\gamma > 0$ and $\det(\text{Hess}) = \beta\delta/(\alpha\gamma) > 0$. Strict convexity of a conserved quantity at an equilibrium is exactly the condition under which the Lyapunov stability theorem (using $H - H(E^*)$ as the Lyapunov function) certifies that $E^*$ is Lyapunov stable — a result much stronger than what linearization alone can deliver.

### 1.3 Lyapunov Function Verification for a Nonlinear Spiral

Consider the system obtained by perturbing a linear center into a stable nonlinear spiral:

$$\dot{x} = -y - x(x^2 + y^2), \qquad \dot{y} = x - y(x^2 + y^2)$$

The candidate Lyapunov function is $V(x, y) = x^2 + y^2$. For $V$ to certify asymptotic stability of the origin, the Lyapunov conditions require: (1) $V(0,0) = 0$, (2) $V(x,y) > 0$ for $(x,y) \neq (0,0)$, and (3) $\dot{V}(x,y) < 0$ for all $(x,y) \neq (0,0)$. Condition (3) is the substantive one; it demands that $\partial_x V \cdot f + \partial_y V \cdot g < 0$ away from the origin.

```python
import sympy as sp

x, y = sp.symbols('x y', real=True)

# Define the system
f = -y - x*(x**2 + y**2)
g =  x - y*(x**2 + y**2)

# Define the Lyapunov candidate
V = x**2 + y**2

# Compute the Lie derivative dV/dt = grad(V) . (f, g)
dV_dt = sp.diff(V, x)*f + sp.diff(V, y)*g
dV_dt_expanded = sp.expand(dV_dt)
print("dV/dt (expanded):", dV_dt_expanded)

# Factor in terms of r^2 = x^2 + y^2
r2 = sp.Symbol('r2', positive=True)
dV_dt_substituted = dV_dt_expanded.subs(x**2 + y**2, r2)
print("dV/dt in terms of r^2:", dV_dt_substituted)
# Expected: -2*r2^2  (which is strictly negative for r2 > 0)

# Confirm symbolically that dV/dt = -2(x^2+y^2)^2
expected = -2*(x**2 + y**2)**2
difference = sp.expand(dV_dt_expanded - expected)
print("Verification residual (must be 0):", difference)

# Confirm V is positive definite by checking it equals a sum of squares
print("V positive definite (sum of squares):", sp.factor(V))

# Compute the rate of decay on the unit circle as a sanity check
dV_on_unit_circle = dV_dt_expanded.subs(y**2, 1 - x**2)
print("dV/dt on unit circle (x^2 + y^2 = 1):", sp.simplify(dV_on_unit_circle))
# Should simplify to -2
```

The key computation is $\dot{V} = 2x\dot{x} + 2y\dot{y} = 2x(-y - x(x^2+y^2)) + 2y(x - y(x^2+y^2)) = -2(x^2+y^2)^2$. Since $x^2 + y^2 \geq 0$ with equality only at the origin, we have $\dot{V} = -2(x^2+y^2)^2 \leq 0$ with equality only at $(0,0)$. This is a computational certificate of Lyapunov asymptotic stability: the origin is globally asymptotically stable on $\mathbb{R}^2 \setminus \{0\}$ in the sense that every trajectory converges to the origin as $t \to \infty$.

---

## Exercise 2: Boundary Value Stress Testing & Singularities

### 2.1 Bifurcation Curves and the Normal Form of the Hopf Bifurcation

The Hopf bifurcation theorem asserts that when a family of equilibria $x^*(\mu)$ has a Jacobian $J(\mu)$ whose eigenvalues cross the imaginary axis transversally at a critical parameter $\mu = \mu_c$ — meaning $\text{Re}(\lambda(\mu_c)) = 0$ and $\frac{d}{d\mu}\text{Re}(\lambda)|_{\mu=\mu_c} \neq 0$ — a limit cycle is born from $x^*$. The sign of the first Lyapunov coefficient $l_1$ determines whether the bifurcation is supercritical (stable limit cycle, $l_1 < 0$) or subcritical (unstable limit cycle, $l_1 > 0$). We work with the canonical normal form

$$\dot{x} = \mu x - y - x(x^2 + y^2), \qquad \dot{y} = x + \mu y - y(x^2 + y^2)$$

This system has an equilibrium at the origin for all $\mu$. The Jacobian at the origin has eigenvalues $\mu \pm i$. The transversality condition $\frac{d}{d\mu}\text{Re}(\lambda) = 1 \neq 0$ holds at $\mu = 0$. For $\mu > 0$, a stable limit cycle of radius $r = \sqrt{\mu}$ is born, confirming a supercritical Hopf bifurcation.

```python
import sympy as sp
import numpy as np
import matplotlib.pyplot as plt
from scipy.integrate import solve_ivp

mu_sym, x, y = sp.symbols('mu x y', real=True)

# Define the normal form vector field
f = mu_sym*x - y - x*(x**2 + y**2)
g = x + mu_sym*y - y*(x**2 + y**2)

# Jacobian at origin
F_vec = sp.Matrix([f, g])
state = sp.Matrix([x, y])
J = F_vec.jacobian(state).subs([(x, 0), (y, 0)])
print("Jacobian at origin:")
sp.pprint(J)

# Eigenvalues as functions of mu
eigenvalues = J.eigenvals()
print("\nEigenvalues:", eigenvalues)

# Extract real parts symbolically
lam = sp.Symbol('lam')
char_poly = J.charpoly(lam).as_expr()
roots = sp.solve(char_poly, lam)
real_parts = [sp.re(root) for root in roots]
print("Real parts of eigenvalues:", [sp.simplify(r) for r in real_parts])

# Transversality: d/dmu of Re(lambda) at mu=0
transversality = sp.diff(real_parts[0], mu_sym).subs(mu_sym, 0)
print("Transversality condition d/dmu Re(lambda)|_{mu=0}:", sp.simplify(transversality))

# Verify limit cycle in polar coordinates
# Convert: x = r*cos(theta), y = r*sin(theta)
# dr/dt = mu*r - r^3,  dtheta/dt = 1
r_sym = sp.Symbol('r', positive=True)
r_dot = mu_sym*r_sym - r_sym**3
# Fixed points of r_dot correspond to limit cycle radii
limit_cycle_radii = sp.solve(r_dot, r_sym)
print("\nLimit cycle radii (solutions of r_dot = 0):", limit_cycle_radii)
# r = 0 (equilibrium) and r = sqrt(mu) (limit cycle for mu > 0)

# Stability of limit cycle: sign of d(r_dot)/dr at r = sqrt(mu)
stability_derivative = sp.diff(r_dot, r_sym).subs(r_sym, sp.sqrt(mu_sym))
stability_simplified = sp.simplify(stability_derivative)
print("d(r_dot)/dr at limit cycle radius:", stability_simplified)
# Expected: -2*mu < 0 for mu > 0, confirming stable limit cycle

# Numerical phase portrait for mu = 0.5
def hopf_normal_form(t, state, mu):
    xv, yv = state
    dxdt = mu*xv - yv - xv*(xv**2 + yv**2)
    dydt = xv + mu*yv - yv*(xv**2 + yv**2)
    return [dxdt, dydt]

mu_val = 0.5
t_span = (0, 40)
t_eval = np.linspace(0, 40, 4000)
initial_conditions = [[0.1, 0.0], [1.5, 0.0], [0.3, 0.3]]

fig, ax = plt.subplots(figsize=(7, 7))
colors = ['royalblue', 'crimson', 'forestgreen']
for ic, color in zip(initial_conditions, colors):
    sol = solve_ivp(hopf_normal_form, t_span, ic, args=(mu_val,),
                    t_eval=t_eval, rtol=1e-10, atol=1e-12)
    ax.plot(sol.y[0], sol.y[1], color=color, linewidth=1.0,
            label=f'IC = {ic}')

# Overlay the theoretical limit cycle r = sqrt(mu)
theta_vals = np.linspace(0, 2*np.pi, 500)
r_lc = np.sqrt(mu_val)
ax.plot(r_lc*np.cos(theta_vals), r_lc*np.sin(theta_vals),
        'k--', linewidth=2, label=f'Limit cycle $r = \\sqrt{{\\mu}}$ = {r_lc:.4f}')

ax.set_xlabel('$x$', fontsize=13)
ax.set_ylabel('$y$', fontsize=13)
ax.set_title(f'Hopf Normal Form: Supercritical Bifurcation ($\\mu = {mu_val}$)', fontsize=13)
ax.legend(fontsize=10)
ax.set_aspect('equal')
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('hopf_bifurcation.png', dpi=150)
plt.show()
print(f"\nTheoretical limit cycle radius: sqrt({mu_val}) = {np.sqrt(mu_val):.6f}")
```

The polar coordinate reduction $\dot{r} = \mu r - r^3$ is the core insight. This is a one-dimensional gradient system with $\dot{r} = -\partial_r(\frac{r^4}{4} - \frac{\mu r^2}{2})$, so the nontrivial fixed point $r = \sqrt{\mu}$ (existing for $\mu > 0$) is always stable. The derivative $\partial_r \dot{r}|_{r=\sqrt{\mu}} = \mu - 3r^2|_{r=\sqrt{\mu}} = \mu - 3\mu = -2\mu < 0$, which SymPy confirms symbolically.

### 2.2 Saddle-Node Bifurcation and the Fold Catastrophe

The saddle-node bifurcation is the most elementary catastrophe in dynamical systems theory, described by the normal form $\dot{x} = \mu + x^2$. At $\mu < 0$, two equilibria exist at $x^* = \pm\sqrt{-\mu}$; at $\mu = 0$ they collide and annihilate; for $\mu > 0$ no equilibria exist and all trajectories escape to $+\infty$ in finite time. The collision occurs precisely where both $f = 0$ and $\partial_x f = 0$ hold simultaneously, which is the defining condition of a degenerate zero (a fold point of the graph of $f$).

```python
import sympy as sp
import numpy as np
import matplotlib.pyplot as plt

x, mu = sp.symbols('x mu', real=True)

# Saddle-node normal form
f = mu + x**2

# Find equilibria as functions of mu
equilibria = sp.solve(f, x)
print("Equilibria:", equilibria)
# x* = ±sqrt(-mu), real when mu < 0

# Determine stability: sign of df/dx at each equilibrium
df_dx = sp.diff(f, x)
print("df/dx:", df_dx)
for eq in equilibria:
    stability = sp.simplify(df_dx.subs(x, eq))
    print(f"  df/dx at x* = {eq}: {stability}")

# Verify the fold condition: f = 0 and df/dx = 0 simultaneously
fold_conditions = sp.solve([f, df_dx], [x, mu])
print("\nFold point (bifurcation point):", fold_conditions)
# Expected: x = 0, mu = 0

# Bifurcation diagram: plot x* vs mu
mu_neg = np.linspace(-2, 0, 300)
x_stable   = -np.sqrt(-mu_neg)   # stable branch (df/dx = 2x < 0)
x_unstable =  np.sqrt(-mu_neg)   # unstable branch (df/dx = 2x > 0)

fig, axes = plt.subplots(1, 2, figsize=(13, 5))

ax = axes[0]
ax.plot(mu_neg, x_stable,   'royalblue', linewidth=2.5, label='Stable ($df/dx < 0$)')
ax.plot(mu_neg, x_unstable, 'crimson',   linewidth=2.5, linestyle='--',
        label='Unstable ($df/dx > 0$)')
ax.scatter([0], [0], color='black', s=80, zorder=5, label='Bifurcation point')
ax.axvline(0, color='gray', linewidth=0.8, linestyle=':')
ax.set_xlabel('$\\mu$', fontsize=13)
ax.set_ylabel('$x^*$', fontsize=13)
ax.set_title('Saddle-Node Bifurcation Diagram', fontsize=13)
ax.legend(fontsize=10)
ax.grid(True, alpha=0.3)

# Phase line portraits for three parameter regimes
ax2 = axes[1]
x_range = np.linspace(-2.5, 2.5, 500)
for mu_val, color, label in [(-1, 'royalblue', '$\\mu=-1$'),
                               ( 0, 'darkorange', '$\\mu=0$'),
                               ( 1, 'crimson',    '$\\mu=1$')]:
    ax2.plot(x_range, mu_val + x_range**2, color=color, linewidth=2, label=label)
ax2.axhline(0, color='black', linewidth=1.0)
ax2.set_ylim(-2, 4)
ax2.set_xlabel('$x$', fontsize=13)
ax2.set_ylabel('$\\dot{x} = \\mu + x^2$', fontsize=13)
ax2.set_title('Phase Line: $\\dot{x} = \\mu + x^2$', fontsize=13)
ax2.legend(fontsize=10)
ax2.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('saddle_node_bifurcation.png', dpi=150)
plt.show()
```

### 2.3 Stress Testing Near a Degenerate Equilibrium: The Nilpotent Jacobian

A center is non-hyperbolic: its linearization has zero real parts, and the Hartman–Grobman theorem does not apply. Whether a non-hyperbolic equilibrium is truly a center or a spiral requires analyzing higher-order terms. The Bogdanov–Takens normal form $\dot{x} = y$, $\dot{y} = \mu_1 + \mu_2 y + x^2 + xy$ has a nilpotent Jacobian at the origin when $(\mu_1, \mu_2) = (0,0)$, meaning $J = \begin{pmatrix} 0 & 1 \\ 0 & 0 \end{pmatrix}$ has a repeated zero eigenvalue. Near this codimension-2 point, the parameter plane organizes into distinct regions separated by curves of saddle-node and Hopf bifurcations.

```python
import sympy as sp

x, y, mu1, mu2 = sp.symbols('x y mu1 mu2', real=True)

# Bogdanov-Takens normal form
f = y
g = mu1 + mu2*y + x**2 + x*y

F = sp.Matrix([f, g])
state = sp.Matrix([x, y])
J_full = F.jacobian(state)

# Jacobian at parameter origin (mu1=mu2=0) at equilibrium (0,0)
J_origin = J_full.subs([(x, 0), (y, 0), (mu1, 0), (mu2, 0)])
print("Jacobian at BT point (origin, mu=0):")
sp.pprint(J_origin)

# Confirm nilpotent: J^2 = 0
J_squared = J_origin**2
print("\nJ^2 (must be zero matrix for nilpotent):")
sp.pprint(J_squared)

# Find equilibria for general parameters
equilibria = sp.solve([f, g], [x, y], dict=True)
print("\nEquilibria of BT normal form:", equilibria)
# x = ±sqrt(-mu1), y = 0

# For mu1 < 0: two equilibria at (±sqrt(-mu1), 0)
# Analyze their Jacobian eigenvalues
x_eq_pos = sp.sqrt(-mu1)
y_eq_zero = sp.Integer(0)
J_at_pos = J_full.subs([(x, x_eq_pos), (y, y_eq_zero)])
print("\nJacobian at positive equilibrium (+sqrt(-mu1), 0):")
sp.pprint(sp.simplify(J_at_pos))
tr_pos = sp.simplify(J_at_pos.trace())
det_pos = sp.simplify(J_at_pos.det())
print("Trace:", tr_pos)
print("Determinant:", det_pos)
# det = 2*sqrt(-mu1)*sqrt(-mu1) + ... need explicit computation
# The saddle-node collision curve is precisely mu1 = 0

# Hopf bifurcation curve: trace = 0, det > 0
hopf_curve = sp.solve(tr_pos, mu2)
print("\nHopf bifurcation condition (trace=0):", hopf_curve)

# Verify characteristic polynomial at positive equilibrium
lam = sp.Symbol('lam')
char_poly_pos = J_at_pos.charpoly(lam).as_expr()
print("\nCharacteristic polynomial at positive equilibrium:")
sp.pprint(sp.expand(char_poly_pos))

# Saddle-node curve: det = 0 gives mu1 = 0
saddle_node_curve = sp.solve(det_pos, mu1)
print("\nSaddle-node bifurcation curve:", saddle_node_curve)
```

The Bogdanov–Takens analysis demonstrates why the Jacobian alone is insufficient for a full bifurcation picture: the codimension-2 structure at the origin organizes saddle-node curves (along $\mu_1 = 0$), Hopf bifurcation curves, and homoclinic bifurcation curves emanating from the BT point. This kind of degenerate stress test reveals the true complexity hidden at parameter boundaries.

---

## Exercise 3: Algorithmic Implementation of Formal Structures

### 3.1 Algorithmic Computation of the Poincaré Map and Period Detection

The Poincaré map converts the continuous-time question of limit cycle existence and stability into a discrete fixed-point problem. Given a planar system and a transversal section $\Sigma$ (typically a half-line through an equilibrium), the Poincaré map $\mathcal{P}: \Sigma \to \Sigma$ sends the initial point $p \in \Sigma$ to the first return point $\mathcal{P}(p)$. A fixed point of $\mathcal{P}$ corresponds to a periodic orbit, and $|\mathcal{P}'(p)| < 1$ at a fixed point certifies that the periodic orbit is asymptotically stable. The following implementation computes $\mathcal{P}$ numerically for the van der Pol oscillator $\ddot{x} - \mu(1 - x^2)\dot{x} + x = 0$, equivalently $\dot{x} = y$, $\dot{y} = \mu(1-x^2)y - x$.

```python
import numpy as np
from scipy.integrate import solve_ivp
from scipy.optimize import brentq
import matplotlib.pyplot as plt

def van_der_pol(t, state, mu):
    x, y = state
    dxdt = y
    dydt = mu*(1 - x**2)*y - x
    return [dxdt, dydt]

def compute_poincare_map(x0, mu, section_y=0.0, max_time=200.0, tol=1e-12):
    """
    Compute the Poincare return map on the section y = 0, x > 0.
    Given initial condition (x0, 0) with x0 > 0, integrate until the
    trajectory returns to y = 0 with x > 0 (one full revolution).
    Returns the x-coordinate of the first return.
    """
    state0 = [x0, section_y]
    
    def section_event(t, state, mu):
        # Trigger when y crosses zero in the downward direction
        return state[1]
    section_event.terminal = False
    section_event.direction = -1  # only downward crossings
    
    sol = solve_ivp(
        van_der_pol, [0, max_time], state0,
        args=(mu,), events=section_event,
        rtol=1e-12, atol=1e-14, dense_output=True, max_step=0.01
    )
    
    # The first event at t=0 is the initial condition itself (y=0).
    # We want the SECOND zero crossing of y with x > 0.
    if sol.t_events[0].shape[0] < 2:
        raise ValueError("Trajectory did not return to section within max_time.")
    
    # Find the return time by locating the first return crossing after initial
    # First event is t=0 itself; look for subsequent downward crossing
    return_times = sol.t_events[0]
    
    # Filter: only crossings with x > 0 and t > 0.1 (skip initial condition)
    for t_ret in return_times:
        if t_ret > 0.5:
            ret_state = sol.sol(t_ret)
            if ret_state[0] > 0:
                return ret_state[0]
    raise ValueError("No valid return crossing found.")

mu = 1.5
x0_values = np.linspace(0.5, 3.5, 40)
poincare_returns = []
for x0 in x0_values:
    try:
        px = compute_poincare_map(x0, mu)
        poincare_returns.append(px)
    except ValueError:
        poincare_returns.append(np.nan)

poincare_returns = np.array(poincare_returns)
valid = ~np.isnan(poincare_returns)

# The fixed point P(x*) = x* is the limit cycle radius on the section
# Find it by solving P(x) - x = 0 via interpolation
residual = poincare_returns[valid] - x0_values[valid]
# Find sign change to bracket the fixed point
sign_changes = np.where(np.diff(np.sign(residual)))[0]
fixed_point = None
if len(sign_changes) > 0:
    idx = sign_changes[0]
    x_lo = x0_values[valid][idx]
    x_hi = x0_values[valid][idx + 1]
    def residual_func(x0):
        return compute_poincare_map(x0, mu) - x0
    fixed_point = brentq(residual_func, x_lo, x_hi, xtol=1e-9, rtol=1e-10)
    print(f"Fixed point of Poincare map (limit cycle section): x* = {fixed_point:.8f}")

# Estimate derivative of Poincare map at fixed point (multiplier)
h = 1e-5
if fixed_point is not None:
    P_plus  = compute_poincare_map(fixed_point + h, mu)
    P_minus = compute_poincare_map(fixed_point - h, mu)
    multiplier = (P_plus - P_minus) / (2*h)
    print(f"Poincare multiplier |P'(x*)| = {abs(multiplier):.8f}")
    if abs(multiplier) < 1:
        print("VERDICT: Limit cycle is asymptotically stable (|multiplier| < 1)")
    else:
        print("VERDICT: Limit cycle is unstable (|multiplier| >= 1)")

# Phase portrait with limit cycle
fig, axes = plt.subplots(1, 2, figsize=(14, 6))

ax = axes[0]
t_long = np.linspace(0, 60, 10000)
for x0_ic in [0.2, 0.5, 2.0, 3.0]:
    sol = solve_ivp(van_der_pol, [0, 60], [x0_ic, 0.0],
                    args=(mu,), t_eval=t_long, rtol=1e-11, atol=1e-13)
    ax.plot(sol.y[0], sol.y[1], linewidth=0.8, alpha=0.8)
ax.set_xlabel('$x$', fontsize=13)
ax.set_ylabel('$\\dot{x}$', fontsize=13)
ax.set_title(f'Van der Pol Phase Portrait ($\\mu={mu}$)', fontsize=12)
ax.grid(True, alpha=0.3)

ax2 = axes[1]
ax2.plot(x0_values[valid], poincare_returns[valid], 'royalblue', linewidth=2,
         label='$\\mathcal{P}(x_0)$')
ax2.plot(x0_values[valid], x0_values[valid], 'k--', linewidth=1.5,
         label='$y = x_0$ (diagonal)')
if fixed_point is not None:
    ax2.scatter([fixed_point], [fixed_point], color='red', s=100, zorder=5,
                label=f'Fixed point $x^* = {fixed_point:.4f}$')
ax2.set_xlabel('$x_0$ (initial condition on section)', fontsize=12)
ax2.set_ylabel('$\\mathcal{P}(x_0)$ (first return)', fontsize=12)
ax2.set_title("Poincaré Return Map on $y=0,\\ x>0$", fontsize=12)
ax2.legend(fontsize=10)
ax2.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('poincare_van_der_pol.png', dpi=150)
plt.show()
```

### 3.2 Gröbner Basis Computation of Polynomial Equilibria via SageMath

When the vector field $f$ is polynomial, finding all equilibria is equivalent to solving a polynomial system, and Gröbner bases provide the canonical algorithmic tool. The ideal $I = \langle f_1, \ldots, f_n \rangle \subset \mathbb{Q}[x_1, \ldots, x_n]$ has the property that its variety $V(I) = \{x : f_i(x) = 0 \text{ for all } i\}$ is precisely the equilibrium set. The Gröbner basis of $I$ with respect to a lexicographic term order triangulates the system into a form solvable by back-substitution, generalizing Gaussian elimination to the nonlinear setting.

```python
# This block targets SageMath. Run via: sage poincare_groebner.sage
# or paste into a SageMath Jupyter cell.

from sage.all import *

# Define polynomial ring over rationals in three variables
R = PolynomialRing(QQ, ['x', 'y', 'z'], order='lex')
x, y, z = R.gens()

# A three-dimensional polynomial system (Lorenz-like cubic)
# dot_x = -x + y - x*z
# dot_y =  x - y + y*z
# dot_z =  x*y - z
f1 = -x + y - x*z
f2 =  x - y + y*z
f3 =  x*y - z

# Construct the ideal generated by the vector field components
I = R.ideal([f1, f2, f3])
print("Ideal generators:")
for gen in I.gens():
    print(" ", gen)

# Compute Gröbner basis in lex order (elimination ordering)
GB = I.groebner_basis()
print("\nGröbner basis (lex order):")
for poly in GB:
    print(" ", poly)
print(f"\nNumber of basis elements: {len(GB)}")

# The last element in a lex GB involves only the last variable z
# Factor it to find all admissible values of z
last_poly = GB[-1]
print("\nLast GB polynomial (univariate in z):", last_poly)
z_solutions = last_poly.univariate_polynomial().roots(ring=QQbar, multiplicities=False)
print("Solutions for z:", z_solutions)

# Back-substitute each z value to recover (x, y, z) equilibria
print("\nAll equilibria:")
for z_val in z_solutions:
    # Substitute z_val into earlier GB elements to solve for y, then x
    polys_subst = [poly.subs(z=z_val) for poly in GB[:-1]]
    # Build univariate polynomial in y
    R2 = PolynomialRing(QQbar, ['x_v', 'y_v'])
    xv, yv = R2.gens()
    polys_in_xy = [R2(str(p).replace('x','x_v').replace('y','y_v')) for p in polys_subst if p != 0]
    # Use primary decomposition for the reduced system
    I_reduced = R.ideal([p.subs(z=z_val) for p in [f1, f2, f3]])
    variety = I_reduced.variety(ring=QQbar)
    for pt in variety:
        print(f"  Equilibrium: x={pt[x]}, y={pt[y]}, z={pt[z]}")

# Verify dimension of the variety
print(f"\nIdeal dimension: {I.dimension()}")
print(f"Ideal is zero-dimensional: {I.dimension() == 0}")
```

The Gröbner basis computation reduces what appears to be a coupled nonlinear system to a triangular form. The final polynomial in the basis depends on $z$ alone and factors over $\overline{\mathbb{Q}}$ into linear and quadratic factors, each corresponding to a distinct equilibrium branch. This algorithmic approach is guaranteed to find all isolated equilibria of a zero-dimensional polynomial system, in contrast to numerical root-finding which may miss components.

### 3.3 Formal Verification in Lean 4: Lyapunov Stability of a Linear System

The following Lean 4 proof uses Mathlib4 to formally verify that the linear system $\dot{x} = Ax$ with $A = \begin{pmatrix} -1 & 0 \\ 0 & -2 \end{pmatrix}$ has a Lyapunov function $V(x) = x_1^2 + x_2^2$ satisfying all required conditions. This constitutes a machine-checkable certificate of stability that is independent of any numerical approximation.

```lean
-- File: DynamicalSystems/Lyapunov.lean
-- Requires: Mathlib4 via lake update

import Mathlib.Analysis.InnerProductSpace.Basic
import Mathlib.Analysis.Calculus.Deriv.Basic
import Mathlib.LinearAlgebra.Matrix.PosDef
import Mathlib.Tactic

namespace DynamicalSystems

/-!
# Lyapunov Stability Verification for a Diagonal Linear System

We verify that V(x) = x₁² + x₂² is a valid Lyapunov function for
the linear system ẋ = Ax where A = diag(-1, -2).

A function V : ℝⁿ → ℝ is a Lyapunov function for ẋ = f(x) if:
  1. V(0) = 0
  2. V(x) > 0 for x ≠ 0
  3. ∇V(x) · f(x) < 0 for x ≠ 0  (Lie derivative is strictly negative)
-/

-- Define the Lyapunov function V : ℝ² → ℝ
noncomputable def V (p : ℝ × ℝ) : ℝ := p.1^2 + p.2^2

-- Define the vector field f(x) = Ax for A = diag(-1, -2)
noncomputable def f_field (p : ℝ × ℝ) : ℝ × ℝ := (-p.1, -2 * p.2)

-- Lyapunov condition 1: V(0) = 0
theorem V_zero : V (0, 0) = 0 := by
  simp [V]

-- Lyapunov condition 2: V is positive definite
theorem V_pos_def (p : ℝ × ℝ) (hp : p ≠ (0, 0)) : V p > 0 := by
  simp [V]
  -- V(p) = p.1^2 + p.2^2 > 0 iff (p.1, p.2) ≠ (0, 0)
  rcases ne_iff_exists_ne.mp hp with ⟨_, _⟩
  · have h1 : p.1 ≠ 0 ∨ p.2 ≠ 0 := by
      intro h
      push_neg at h
      exact hp (Prod.ext h.1 h.2)
    rcases h1 with h | h
    · have := sq_pos_of_ne_zero p.1 h
      linarith [sq_nonneg p.2]
    · have := sq_pos_of_ne_zero p.2 h
      linarith [sq_nonneg p.1]

-- The Lie derivative dV/dt = ∇V · f
-- ∇V(p) = (2p₁, 2p₂), so ∇V(p) · f(p) = 2p₁(-p₁) + 2p₂(-2p₂) = -2p₁² - 4p₂²
noncomputable def lie_derivative (p : ℝ × ℝ) : ℝ :=
  2 * p.1 * (f_field p).1 + 2 * p.2 * (f_field p).2

-- Explicit computation: lie_derivative p = -2*p₁² - 4*p₂²
theorem lie_derivative_eq (p : ℝ × ℝ) :
    lie_derivative p = -2 * p.1^2 - 4 * p.2^2 := by
  simp [lie_derivative, f_field]
  ring

-- Lyapunov condition 3: Lie derivative is strictly negative away from origin
theorem lie_derivative_neg (p : ℝ × ℝ) (hp : p ≠ (0, 0)) :
    lie_derivative p < 0 := by
  rw [lie_derivative_eq]
  have h1 : p.1 ≠ 0 ∨ p.2 ≠ 0 := by
    intro h
    push_neg at h
    exact hp (Prod.ext h.1 h.2)
  rcases h1 with h | h
  · have := sq_pos_of_ne_zero p.1 h
    have := sq_nonneg p.2
    linarith
  · have := sq_pos_of_ne_zero p.2 h
    have := sq_nonneg p.1
    linarith

-- Master stability certificate: all three conditions hold simultaneously
theorem lyapunov_certificate :
    V (0, 0) = 0 ∧
    (∀ p : ℝ × ℝ, p ≠ (0, 0) → V p > 0) ∧
    (∀ p : ℝ × ℝ, p ≠ (0, 0) → lie_derivative p < 0) :=
  ⟨V_zero, V_pos_def, lie_derivative_neg⟩

#check lyapunov_certificate
-- Output: lyapunov_certificate :
--   V (0, 0) = 0 ∧ (∀ (p : ℝ × ℝ), p ≠ (0, 0) → V p > 0) ∧
--   (∀ (p : ℝ × ℝ), p ≠ (0, 0) → lie_derivative p < 0)

end DynamicalSystems
```

Build and verify this proof by running `lake build` in the project directory. A clean build with no errors constitutes a formal proof that the system satisfies all three Lyapunov conditions, certified by Lean's kernel. The structure of this proof generalizes directly: replace the definitions of `V` and `f_field` with any polynomial candidate and system, and the same proof strategy applies modulo the algebraic computations in the `ring` and `linarith` tactics.

---

## Formal Axioms Cheat Sheet & Verification Reference

This reference consolidates the principal theorems underlying the exercises, their precise hypotheses, and the SymPy or Lean commands used to verify each condition computationally.

**Lyapunov's Stability Theorem.** Let $x^* = 0$ be an equilibrium of $\dot{x} = f(x)$ on an open set $U \subset \mathbb{R}^n$. If there exists $V \in C^1(U)$ such that $V(0) = 0$, $V(x) > 0$ for $x \neq 0$ in $U$, and $\dot{V}(x) = \nabla V(x) \cdot f(x) \leq 0$ for $x \in U$, then the origin is Lyapunov stable. If additionally $\dot{V}(x) < 0$ for $x \neq 0$, then the origin is asymptotically stable. Verification command: `sp.simplify(sp.diff(V,x)*f + sp.diff(V,y)*g)` — the result must be identically zero (stability) or a negative-definite expression (asymptotic stability).

**Hartman–Grobman Theorem.** If $x^*$ is a hyperbolic equilibrium of $\dot{x} = f(x)$ (all eigenvalues of $J(x^*)$ have nonzero real part), then there exists a homeomorphism from a neighborhood of $x^*$ to a neighborhood of the origin that conjugates the flow of $\dot{x} = f(x)$ to the flow of the linearization $\dot{x} = J(x^*)x$. Hyperbolicity is verified computationally by confirming `all(sp.re(ev) != 0 for ev in J.eigenvals())`. When this check fails, higher-order analysis (normal forms, center manifold theory) is mandatory.

**Poincaré–Bendixson Theorem.** In a planar system, if a compact positively invariant region $K \subset \mathbb{R}^2$ contains no equilibrium point, then every trajectory with $\omega$-limit set in $K$ is a periodic orbit. Computational verification proceeds in two steps: first, establish that $K$ is positively invariant by confirming $f \cdot n < 0$ on $\partial K$ (where $n$ is the outward normal), which SymPy handles for polygonal or ellipsoidal boundaries; second, verify that $J(x,y)$ has nonzero trace at all points $(x,y) \in K$ (ruling out equilibria via Bendixson's criterion if the trace does not change sign).

**Bendixson–Dulac Criterion.** If there exists $B \in C^1(D)$ on a simply connected domain $D$ such that $\text{div}(Bf, Bg) = \partial_x(Bf) + \partial_y(Bg)$ does not change sign and is not identically zero in $D$, then the system has no closed orbits in $D$. SymPy verification:

```python
import sympy as sp
x, y = sp.symbols('x y', real=True)
# Example: Lotka-Volterra with Dulac function B = 1/(x*y)
B = 1 / (x * y)
f = sp.Symbol('alpha')*x - sp.Symbol('beta')*x*y
g = sp.Symbol('delta')*x*y - sp.Symbol('gamma')*y
divergence = sp.diff(B*f, x) + sp.diff(B*g, y)
print("Dulac divergence:", sp.simplify(divergence))
# A constant negative value confirms no closed orbits in the positive quadrant
```

**Hopf Bifurcation Theorem (Poincaré–Andronov–Hopf).** Let $\dot{x} = f(x; \mu)$ have an equilibrium $x^*(\mu)$ whose Jacobian has eigenvalues $\lambda(\mu) = \sigma(\mu) \pm i\omega(\mu)$ with $\sigma(\mu_c) = 0$, $\omega(\mu_c) \neq 0$, and $\sigma'(\mu_c) \neq 0$ (transversality). If the first Lyapunov coefficient $l_1 \neq 0$, then a unique limit cycle bifurcates from $x^*$ at $\mu = \mu_c$. The cycle is stable if $l_1 < 0$ (supercritical) and unstable if $l_1 > 0$ (subcritical). Transversality verification: `sp.diff(sp.re(eigenvalue), mu).subs(mu, mu_c)` must be nonzero.

**Gröbner Basis Completeness.** For a polynomial system $f_1 = \cdots = f_k = 0$ over $\mathbb{Q}$, the reduced Gröbner basis $G$ of the ideal $\langle f_1, \ldots, f_k \rangle$ with respect to a graded lexicographic order satisfies $V(I) = V(G)$ as varieties: every solution of the original system is a solution of the Gröbner basis, and vice versa. When the ideal is zero-dimensional ($\dim_\mathbb{Q}(\mathbb{Q}[x_1,\ldots,x_n]/I) < \infty$), the Gröbner basis in lexicographic order contains a univariate polynomial in $x_n$ whose roots enumerate all admissible values, enabling complete back-substitution. SageMath command: `I.groebner_basis()` with `order='lex'`; dimension check via `I.dimension()`.

**Poincaré Map Fixed Point Criterion.** A periodic orbit $\Gamma$ of period $T$ corresponds to a fixed point $p^*$ of the Poincaré map $\mathcal{P}: \Sigma \to \Sigma$ on a transversal $\Sigma$. The orbit is asymptotically stable if the multiplier $|\mathcal{P}'(p^*)| < 1$, unstable if $|\mathcal{P}'(p^*)| > 1$, and undetermined by this criterion if $|\mathcal{P}'(p^*)| = 1$. Numerical computation of the multiplier uses the central difference formula $\mathcal{P}'(p^*) \approx (\mathcal{P}(p^*+h) - \mathcal{P}(p^*-h))/(2h)$ with step size $h \approx 10^{-5}$ and integration tolerances set to $\text{rtol} = 10^{-12}$, $\text{atol} = 10^{-14}$.

| Theorem | Key Hypothesis to Verify | SymPy / SageMath Command |
|---|---|---|
| Lyapunov Stability | $\dot{V} \leq 0$ identically | `sp.simplify(dV_dt)` returns nonpositive expression |
| Lyapunov Asymptotic Stability | $\dot{V} < 0$ away from origin | expression factors as $-c \cdot (x^2+y^2)^k$ for $c > 0$ |
| Hartman–Grobman | All eigenvalues hyperbolic | `all(sp.re(ev) != 0 for ev in J.eigenvals().keys())` |
| Hopf Bifurcation | Transversality $\sigma'(\mu_c) \neq 0$ | `sp.diff(sigma, mu).subs(mu, mu_c) != 0` |
| Bendixson–Dulac | $\text{div}(Bf, Bg)$ one-signed | `sp.simplify(div)` is nonzero constant or one-signed |
| Poincaré–Bendixson | No equilibria in compact $K$ | `sp.solve([f, g], [x, y])` has no solutions in $K$ |
| Gröbner Completeness | Zero-dimensional ideal | `I.dimension() == 0` in SageMath |
| Poincaré Map Stability | $\|\mathcal{P}'(p^*)\| < 1$ | Central-difference multiplier computation |
