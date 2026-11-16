# Operational Verification Labs: Neoclassical

## Objective & Operational Lab Setup

These operational verification labs systematically reconstruct the core analytical machinery of neoclassical economic theory through hands-on computational implementation, empirical calibration, and boundary-condition stress testing. The neoclassical school—emerging from the marginal revolution of the 1870s through Jevons, Menger, and Walras, and formalized by Marshall, Hicks, Samuelson, and Arrow-Debreu—rests on three foundational pillars: rational optimization by agents with well-defined preferences, market-clearing equilibrium through price adjustment, and Pareto efficiency of competitive outcomes under ideal conditions. Unlike classical political economy's focus on labor value and long-run growth, or Keynesian emphasis on aggregate demand failures, neoclassical economics analyzes resource allocation through marginal analysis, substitution effects, and general equilibrium interdependence.

Your operational objective across these three exercises is to translate abstract neoclassical propositions into concrete, testable economic models. You will construct utility maximization problems with explicit functional forms, derive Marshallian and Hicksian demand systems analytically and numerically, calibrate general equilibrium models to match empirical price and quantity data, and probe the welfare theorems' boundaries by introducing market failures. Each exercise builds progressively: from individual consumer optimization to multi-market equilibrium to welfare analysis under friction. By the end, you will possess operational command over the neoclassical toolkit—capable of diagnosing whether observed market outcomes align with neoclassical predictions, quantifying efficiency losses from distortions, and articulating precisely where neoclassical theory's idealized assumptions break down in practice.

Establish your analytical research environment by preparing a computational workspace combining spreadsheet modeling, symbolic algebra, and numerical optimization. Install Python 3.10 or later with the scientific stack: NumPy for matrix operations and numerical solvers, SciPy for constrained optimization and root-finding, Matplotlib for visualization of indifference curves and equilibrium diagrams, and SymPy for symbolic differentiation of utility functions and Lagrangian derivations. Alternatively, MATLAB or R with optimization libraries (optim, nloptr) will serve equivalently. Prepare a spreadsheet application—Excel, LibreOffice Calc, or Google Sheets—for parameter sweeps, elasticity tables, and comparative statics. Create a project directory structure: `/data/` for empirical price and quantity datasets, `/models/` for Python scripts implementing optimization and equilibrium solvers, `/results/` for output tables and figures, and `/notebooks/` for Jupyter notebooks documenting each exercise's workflow. Download a sample consumer expenditure dataset (e.g., Bureau of Labor Statistics Consumer Expenditure Survey microdata or OECD household consumption aggregates) to anchor your calibration exercises in real-world consumption patterns. Verify your setup by running a minimal test: solve a two-good Cobb-Douglas utility maximization problem numerically and confirm that the tangency condition—marginal rate of substitution equals price ratio—holds at the computed optimum to machine precision.

The neoclassical framework's strength lies in its rigorous mathematical formulation and empirical falsifiability. Unlike verbal classical theory or institutional narrative, neoclassical models yield precise quantitative predictions: demand elasticities, consumer surplus magnitudes, deadweight loss triangles, and comparative statics of equilibrium shifts. These labs train you to operationalize that precision, moving from stylized textbook diagrams to operational models capable of ingesting real data, generating forecasts, and identifying where theory diverges from observation. The 80/20 rule governs our approach: eighty percent of effort goes to constructing working models, calibrating parameters, and interpreting results; twenty percent to understanding the underlying mathematical proofs that guarantee existence and uniqueness of equilibrium. You will write code, not merely read equations. You will fit models to data, not merely sketch curves. You will quantify welfare losses, not merely state that they exist.

Prepare to engage neoclassical economics as an operational discipline. The exercises ahead demand computational rigor, empirical grounding, and diagnostic skepticism. When a model fails to match data, you will investigate whether the failure stems from misspecification of preferences, omitted constraints, or genuine violation of neoclassical assumptions. When equilibrium existence theorems require convexity, you will test non-convex cases and observe algorithmic breakdown. When welfare theorems promise efficiency, you will introduce externalities and measure the resulting inefficiency. This is neoclassical economics as engineering discipline: building models, testing predictions, and learning from failures.

## Exercise 1: Foundational Practical Implementation

Construct a complete consumer optimization model implementing the neoclassical theory of demand from first principles. Begin with a representative consumer possessing a Cobb-Douglas utility function over two goods, subject to a linear budget constraint. This canonical case serves as the operational foundation for all consumer theory: it admits closed-form solutions, satisfies the requisite convexity and monotonicity axioms, and generates demand functions exhibiting intuitive comparative statics. The Cobb-Douglas functional form $U(x_1, x_2) = x_1^\alpha x_2^{1-\alpha}$ with $\alpha \in (0,1)$ represents constant expenditure shares—a consumer allocates fraction $\alpha$ of income to good 1 and fraction $1-\alpha$ to good 2 regardless of prices—matching empirical regularity in many consumption categories. Your task is to solve this optimization problem analytically via Lagrangian methods, implement the solution numerically in Python, verify the tangency condition at the optimum, and construct visualizations of the consumer's indifference map, budget constraint, and optimal bundle.

Formulate the consumer's problem mathematically. The consumer chooses quantities $x_1 \geq 0$ and $x_2 \geq 0$ to maximize $U(x_1, x_2) = x_1^\alpha x_2^{1-\alpha}$ subject to the budget constraint $p_1 x_1 + p_2 x_2 = m$, where $p_1, p_2 > 0$ denote prices and $m > 0$ denotes income. The Lagrangian is $\mathcal{L}(x_1, x_2, \lambda) = x_1^\alpha x_2^{1-\alpha} + \lambda(m - p_1 x_1 - p_2 x_2)$. Taking first-order conditions: $\frac{\partial \mathcal{L}}{\partial x_1} = \alpha x_1^{\alpha - 1} x_2^{1-\alpha} - \lambda p_1 = 0$, $\frac{\partial \mathcal{L}}{\partial x_2} = (1-\alpha) x_1^\alpha x_2^{-\alpha} - \lambda p_2 = 0$, and $\frac{\partial \mathcal{L}}{\partial \lambda} = m - p_1 x_1 - p_2 x_2 = 0$. Dividing the first equation by the second eliminates $\lambda$, yielding the tangency condition: $\frac{\alpha x_2}{(1-\alpha) x_1} = \frac{p_1}{p_2}$, or equivalently $\frac{MU_1}{MU_2} = \frac{p_1}{p_2}$. Solving this simultaneously with the budget constraint produces the Marshallian demand functions: $x_1^*(p_1, p_2, m) = \frac{\alpha m}{p_1}$ and $x_2^*(p_1, p_2, m) = \frac{(1-\alpha) m}{p_2}$. These demand functions exhibit unit income elasticity (homogeneous of degree one in income) and are homogeneous of degree zero in $(p_1, p_2, m)$, satisfying no-money-illusion. Verify analytically that indirect utility $V(p_1, p_2, m) = U(x_1^*, x_2^*) = \left(\frac{\alpha m}{p_1}\right)^\alpha \left(\frac{(1-\alpha) m}{p_2}\right)^{1-\alpha}$ is strictly increasing in $m$ and strictly decreasing in $p_1, p_2$.

Implement this solution numerically in Python to handle the general case and build computational infrastructure for later exercises. Create a Python script `consumer_optimization.py` containing the following components. Define a function `cobb_douglas_utility(x1, x2, alpha)` returning $x_1^\alpha x_2^{1-\alpha}$. Define a function `budget_constraint(x1, p1, p2, m)` returning $x_2 = (m - p_1 x_1)/p_2$ to parametrize the budget line. Implement the analytical Marshallian demand solution in `marshallian_demand(p1, p2, m, alpha)` returning $(x_1^*, x_2^*)$ using the closed-form expressions derived above. For verification and extension to non-Cobb-Douglas cases, implement a numerical optimizer: define an objective function `negative_utility(x, alpha)` returning $-U(x[0], x[1])$ (negated for minimization), then use `scipy.optimize.minimize` with method `SLSQP` (Sequential Least Squares Programming), imposing the budget constraint as an equality constraint and non-negativity bounds. The code structure:

```python
import numpy as np
from scipy.optimize import minimize
import matplotlib.pyplot as plt

def cobb_douglas_utility(x1, x2, alpha):
    return (x1 ** alpha) * (x2 ** (1 - alpha))

def marshallian_demand(p1, p2, m, alpha):
    x1_star = (alpha * m) / p1
    x2_star = ((1 - alpha) * m) / p2
    return x1_star, x2_star

def negative_utility(x, alpha):
    return -cobb_douglas_utility(x[0], x[1], alpha)

def budget_constraint_eq(x, p1, p2, m):
    return p1 * x[0] + p2 * x[1] - m

def solve_consumer_numerical(p1, p2, m, alpha, x0):
    constraints = {'type': 'eq', 'fun': budget_constraint_eq, 'args': (p1, p2, m)}
    bounds = [(1e-6, None), (1e-6, None)]
    result = minimize(negative_utility, x0, args=(alpha,), method='SLSQP', 
                      bounds=bounds, constraints=constraints)
    if result.success:
        return result.x, -result.fun
    else:
        raise ValueError("Optimization failed: " + result.message)

# Test case: p1=2, p2=3, m=120, alpha=0.6
p1, p2, m, alpha = 2.0, 3.0, 120.0, 0.6
x1_analytical, x2_analytical = marshallian_demand(p1, p2, m, alpha)
x_numerical, u_numerical = solve_consumer_numerical(p1, p2, m, alpha, x0=[30, 20])

print(f"Analytical solution: x1={x1_analytical:.4f}, x2={x2_analytical:.4f}")
print(f"Numerical solution: x1={x_numerical[0]:.4f}, x2={x_numerical[1]:.4f}")
print(f"Utility at optimum: {cobb_douglas_utility(x1_analytical, x2_analytical, alpha):.4f}")
print(f"Budget satisfied: {p1*x1_analytical + p2*x2_analytical:.4f} = {m}")
```

Run this script and verify that analytical and numerical solutions agree to within numerical tolerance (typically $10^{-6}$). For the test case parameters, the analytical solution yields $x_1^* = (0.6 \times 120)/2 = 36$ and $x_2^* = (0.4 \times 120)/3 = 16$. Confirm the budget binds exactly: $2 \times 36 + 3 \times 16 = 72 + 48 = 120$. Compute the marginal rate of substitution at the optimum: $MRS = \frac{MU_1}{MU_2} = \frac{\alpha x_2}{(1-\alpha) x_1} = \frac{0.6 \times 16}{0.4 \times 36} = \frac{9.6}{14.4} = \frac{2}{3}$, which matches the price ratio $p_1/p_2 = 2/3$, confirming tangency.

Visualize the consumer's optimization problem geometrically to build intuition for the underlying mechanics. Generate a contour plot of indifference curves in $(x_1, x_2)$ space, overlay the budget line, and mark the optimal bundle. Extend the plotting code:

```python
def plot_consumer_equilibrium(p1, p2, m, alpha):
    fig, ax = plt.subplots(figsize=(10, 8))
    
    # Generate grid for indifference curves
    x1_range = np.linspace(0.1, 80, 400)
    x2_range = np.linspace(0.1, 60, 400)
    X1, X2 = np.meshgrid(x1_range, x2_range)
    U = cobb_douglas_utility(X1, X2, alpha)
    
    # Plot indifference curves
    levels = np.linspace(10, 150, 12)
    contours = ax.contour(X1, X2, U, levels=levels, cmap='Blues', alpha=0.6)
    ax.clabel(contours, inline=True, fontsize=8)
    
    # Budget line
    x1_budget = np.linspace(0, m/p1, 200)
    x2_budget = (m - p1 * x1_budget) / p2
    ax.plot(x1_budget, x2_budget, 'r-', linewidth=2.5, label=f'Budget: {p1}x₁ + {p2}x₂ = {m}')
    
    # Optimal bundle
    x1_star, x2_star = marshallian_demand(p1, p2, m, alpha)
    ax.plot(x1_star, x2_star, 'ro', markersize=12, label=f'Optimum: ({x1_star:.1f}, {x2_star:.1f})')
    
    # Tangency: plot indifference curve through optimum
    u_star = cobb_douglas_utility(x1_star, x2_star, alpha)
    ax.contour(X1, X2, U, levels=[u_star], colors=['green'], linewidths=2.5)
    
    ax.set_xlabel('Good 1 (x₁)', fontsize=12)
    ax.set_ylabel('Good 2 (x₂)', fontsize=12)
    ax.set_title(f'Neoclassical Consumer Equilibrium (α={alpha}, p₁={p1}, p₂={p2}, m={m})', fontsize=14)
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)
    ax.set_xlim(0, m/p1 * 1.1)
    ax.set_ylim(0, m/p2 * 1.1)
    plt.tight_layout()
    plt.savefig('results/consumer_equilibrium.png', dpi=300)
    plt.show()

plot_consumer_equilibrium(p1, p2, m, alpha)
```

Examine the resulting figure. The budget line slopes downward with slope $-p_1/p_2 = -2/3$, intersecting the $x_1$-axis at $m/p_1 = 60$ and the $x_2$-axis at $m/p_2 = 40$. Indifference curves bow inward toward the origin, reflecting diminishing marginal rate of substitution (convex preferences). The optimal bundle sits where the budget line is tangent to the highest attainable indifference curve, neither at a corner nor in the interior of the budget set's interior—illustrating the fundamental neoclassical result that rational choice equates marginal tradeoffs (MRS) with market tradeoffs (price ratio).

Extend the model to compute and visualize the price-consumption curve and derive the demand curve for good 1. Vary $p_1$ from 0.5 to 5 while holding $p_2 = 3$, $m = 120$, and $\alpha = 0.6$ constant. For each $p_1$, compute the optimal bundle $(x_1^*, x_2^*)$ and record the pairs $(p_1, x_1^*)$. Plot the price-consumption curve in $(x_1, x_2)$ space and the demand curve in $(p_1, x_1)$ space:

```python
def compute_demand_curve(p2, m, alpha, p1_range):
    results = []
    for p1 in p1_range:
        x1_star, x2_star = marshallian_demand(p1, p2, m, alpha)
        results.append({'p1': p1, 'x1': x1_star, 'x2': x2_star})
    return results

p1_range = np.linspace(0.5, 5.0, 50)
demand_data = compute_demand_curve(p2, m, alpha, p1_range)

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))

# Price-consumption curve
x1_vals = [d['x1'] for d in demand_data]
x2_vals = [d['x2'] for d in demand_data]
ax1.plot(x1_vals, x2_vals, 'b-', linewidth=2)
ax1.set_xlabel('Good 1 (x₁)', fontsize=12)
ax1.set_ylabel('Good 2 (x₂)', fontsize=12)
ax1.set_title('Price-Consumption Curve (varying p₁)', fontsize=14)
ax1.grid(True, alpha=0.3)

# Demand curve
p1_vals = [d['p1'] for d in demand_data]
ax2.plot(x1_vals, p1_vals, 'r-', linewidth=2)
ax2.set_xlabel('Quantity of Good 1 (x₁)', fontsize=12)
ax2.set_ylabel('Price of Good 1 (p₁)', fontsize=12)
ax2.set_title('Marshallian Demand Curve for Good 1', fontsize=14)
ax2.grid(True, alpha=0.3)
ax2.invert_yaxis()

plt.tight_layout()
plt.savefig('results/demand_analysis.png', dpi=300)
plt.show()
```

The demand curve should exhibit the characteristic downward slope: as $p_1$ rises, $x_1^*$ falls, confirming the law of demand for normal goods. For Cobb-Douglas preferences, the demand curve is a rectangular hyperbola in $(x_1, p_1)$ space because $x_1^* = \alpha m / p_1$ implies $p_1 x_1^* = \alpha m$ is constant—expenditure on good 1 remains fixed regardless of price, corresponding to unit price elasticity. Compute the price elasticity of demand analytically: $\epsilon_{x_1, p_1} = \frac{d x_1^*}{d p_1} \frac{p_1}{x_1^*} = \frac{-\alpha m / p_1^2}{1} \frac{p_1}{\alpha m / p_1} = -1$. Verify this numerically by selecting two adjacent points from your demand curve data and computing the arc elasticity: $\epsilon \approx \frac{\Delta x_1 / x_1}{\Delta p_1 / p_1}$. For $p_1 = 2.0$ and $p_1 = 2.1$, compute $x_1(2.0) = 36$ and $x_1(2.1) = 34.286$, yielding $\epsilon = \frac{(34.286 - 36)/36}{(2.1 - 2.0)/2.0} = \frac{-0.0476}{0.05} = -0.952$, approximately $-1$ as theory predicts.

Finally, decompose the price effect into substitution and income effects via the Slutsky equation, a cornerstone of neoclassical demand theory. When $p_1$ increases from $p_1^0$ to $p_1^1$, the total change in $x_1^*$ can be decomposed into two components: the substitution effect (movement along the original indifference curve to the new price ratio) and the income effect (shift to a lower indifference curve due to real income reduction). Implement the Hicksian (compensated) demand function, which holds utility constant instead of income. For Cobb-Douglas utility, the expenditure function is $e(p_1, p_2, u) = u \left(\frac{p_1}{\alpha}\right)^\alpha \left(\frac{p_2}{1-\alpha}\right)^{1-\alpha}$. Hicksian demand is $h_1(p_1, p_2, u) = \frac{\partial e}{\partial p_1} = \alpha u \left(\frac{p_1}{\alpha}\right)^{\alpha - 1} \left(\frac{p_2}{1-\alpha}\right)^{1-\alpha}$. Simplify to $h_1 = \alpha^{1-\alpha} (1-\alpha)^{-(1-\alpha)} u p_1^{-\alpha} p_2^{1-\alpha}$. Substitute the original utility level $u^0 = U(x_1^0, x_2^0)$ where $(x_1^0, x_2^0)$ is the Marshallian demand at $p_1^0$. Compute the substitution effect as $\Delta x_1^{SE} = h_1(p_1^1, p_2, u^0) - x_1(p_1^0, p_2, m)$ and the income effect as $\Delta x_1^{IE} = x_1(p_1^1, p_2, m) - h_1(p_1^1, p_2, u^0)$. Verify that $\Delta x_1^{SE} + \Delta x_1^{IE} = x_1(p_1^1, p_2, m) - x_1(p_1^0, p_2, m)$, the total effect.

Implement this decomposition:

```python
def hicksian_demand_cobb_douglas(p1, p2, u, alpha):
    coefficient = (alpha ** (1 - alpha)) * ((1 - alpha) ** (-(1 - alpha)))
    h1 = coefficient * u * (p1 ** (-alpha)) * (p2 ** (1 - alpha))
    return h1

def slutsky_decomposition(p1_0, p1_1, p2, m, alpha):
    # Initial bundle and utility
    x1_0, x2_0 = marshallian_demand(p1_0, p2, m, alpha)
    u_0 = cobb_douglas_utility(x1_0, x2_0, alpha)
    
    # Final bundle
    x1_1, x2_1 = marshallian_demand(p1_1, p2, m, alpha)
    
    # Hicksian demand at new price, old utility
    h1_1 = hicksian_demand_cobb_douglas(p1_1, p2, u_0, alpha)
    
    # Decomposition
    substitution_effect = h1_1 - x1_0
    income_effect = x1_1 - h1_1
    total_effect = x1_1 - x1_0
    
    return {
        'x1_initial': x1_0,
        'x1_final': x1_1,
        'h1_compensated': h1_1,
        'substitution_effect': substitution_effect,
        'income_effect': income_effect,
        'total_effect': total_effect
    }

decomp = slutsky_decomposition(p1_0=2.0, p1_1=2.5, p2=3.0, m=120.0, alpha=0.6)
print("\nSlutsky Decomposition (p1: 2.0 → 2.5):")
for key, value in decomp.items():
    print(f"  {key}: {value:.4f}")
```

For the test case ($p_1$ rising from 2.0 to 2.5), the output should show that the substitution effect is negative (consumer substitutes away from the now-relatively-expensive good 1), the income effect is also negative (consumer is poorer in real terms and buys less of the normal good 1), and both reinforce to produce a larger total negative effect. This confirms that for normal goods, income and substitution effects work in the same direction, unambiguously delivering downward-sloping demand. For inferior goods, the income effect would be positive, potentially overwhelming the substitution effect and producing an upward-sloping Giffen demand—a theoretical curiosity flagged by the neoclassical apparatus but rarely observed empirically.

Document your results in a report summarizing analytical derivations, numerical verification, visualizations, and elasticity calculations. Confirm that all numerical solutions reproduce the analytical closed-form solution within tolerance, that tangency conditions hold at optima, and that Slutsky decomposition satisfies the accounting identity. This exercise establishes your operational foundation in neoclassical consumer theory: you can now specify utility functions, solve optimization problems, compute demand systems, and decompose price effects—skills that extend directly to multi-good settings, non-homothetic preferences, and general equilibrium analysis in subsequent exercises.

## Exercise 2: Parameter Variation & Empirical Analysis

Extend the foundational consumer model to a two-consumer, two-good pure exchange economy and construct a computable general equilibrium (CGE) system. This exercise operationalizes the Arrow-Debreu general equilibrium framework in miniature, demonstrating how decentralized markets aggregate individual optimization to determine equilibrium prices and allocations. The Edgeworth box diagram provides geometric intuition, but your task is computational: implement a market-clearing algorithm, calibrate preference parameters to match empirical consumption shares, perform comparative statics under parameter variations, and verify the First Welfare Theorem by computing Pareto efficiency metrics at equilibrium. This lab bridges individual optimization and economy-wide equilibrium, revealing how price signals coordinate dispersed agents and how parameter shifts propagate through general equilibrium linkages.

Specify the exchange economy formally. Two consumers, $A$ and $B$, possess initial endowments $\omega^A = (\omega_1^A, \omega_2^A)$ and $\omega^B = (\omega_1^B, \omega_2^B)$ of goods 1 and 2. Total endowments are $\Omega_1 = \omega_1^A + \omega_1^B$ and $\Omega_2 = \omega_2^A + \omega_2^B$, which remain fixed (no production). Each consumer has Cobb-Douglas preferences: $U^A(x_1^A, x_2^A) = (x_1^A)^{\alpha^A} (x_2^A)^{1-\alpha^A}$ and $U^B(x_1^B, x_2^B) = (x_1^B)^{\alpha^B} (x_2^B)^{1-\alpha^B}$. Consumers trade at prices $(p_1, p_2)$ to maximize utility subject to their budget constraints $p_1 x_1^i + p_2 x_2^i = p_1 \omega_1^i + p_2 \omega_2^i$ for $i \in \{A, B\}$. Competitive equilibrium is a price vector $(p_1^*, p_2^*)$ and allocation $((x_1^{A*}, x_2^{A*}), (x_1^{B*}, x_2^{B*}))$ such that: (i) each consumer maximizes utility given prices and endowment income, and (ii) markets clear: $x_1^{A*} + x_1^{B*} = \Omega_1$ and $x_2^{A*} + x_2^{B*} = \Omega_2$. By Walras' Law, if one market clears, the other clears automatically given budget balance.

Derive the market excess demand function and solve for equilibrium prices. From Exercise 1, consumer $i$'s Marshallian demand for good 1 is $x_1^i(p_1, p_2) = \frac{\alpha^i (p_1 \omega_1^i + p_2 \omega_2^i)}{p_1}$. Aggregate demand for good 1 is $X_1^D(p_1, p_2) = x_1^A + x_1^B = \frac{\alpha^A (p_1 \omega_1^A + p_2 \omega_2^A)}{p_1} + \frac{\alpha^B (p_1 \omega_1^B + p_2 \omega_2^B)}{p_1}$. Aggregate supply is $X_1^S = \Omega_1$. Excess demand is $Z_1(p_1, p_2) = X_1^D(p_1, p_2) - \Omega_1$. Normalize the price of good 2 to unity ($p_2 = 1$, a standard numeraire choice) and denote the relative price of good 1 as $p \equiv p_1$. Then $Z_1(p) = \frac{\alpha^A (p \omega_1^A + \omega_2^A) + \alpha^B (p \omega_1^B + \omega_2^B)}{p} - \Omega_1$. Equilibrium price $p^*$ solves $Z_1(p^*) = 0$. Rearrange to obtain a linear equation in $p$: $\alpha^A (p \omega_1^A + \omega_2^A) + \alpha^B (p \omega_1^B + \omega_2^B) = p \Omega_1$. Collecting terms: $p[\alpha^A \omega_1^A + \alpha^B \omega_1^B - \Omega_1] = -(\alpha^A \omega_2^A + \alpha^B \omega_2^B)$. The equilibrium relative price is $p^* = \frac{\alpha^A \omega_2^A + \alpha^B \omega_2^B}{\Omega_1 - (\alpha^A \omega_1^A + \alpha^B \omega_1^B)}$. This closed-form solution exists and is unique provided the denominator is positive, which requires that the weighted average preference for good 1 does not exceed total endowment—a mild condition satisfied in typical calibrations.

Implement the general equilibrium solver in Python. Create a script `general_equilibrium.py` containing functions to compute excess demand, solve for equilibrium price, and allocate consumption bundles:

```python
import numpy as np
from scipy.optimize import fsolve
import matplotlib.pyplot as plt

def excess_demand_good1(p, omega_A, omega_B, alpha_A, alpha_B):
    Omega_1 = omega_A[0] + omega_B[0]
    Omega_2 = omega_A[1] + omega_B[1]
    
    # Income at prices (p, 1)
    income_A = p * omega_A[0] + omega_A[1]
    income_B = p * omega_B[0] + omega_B[1]
    
    # Marshallian demands for good 1
    x1_A = (alpha_A * income_A) / p
    x1_B = (alpha_B * income_B) / p
    
    # Excess demand
    Z1 = (x1_A + x1_B) - Omega_1
    return Z1

def solve_equilibrium(omega_A, omega_B, alpha_A, alpha_B, p_init=1.0):
    # Solve excess demand = 0
    p_eq = fsolve(excess_demand_good1, p_init, args=(omega_A, omega_B, alpha_A, alpha_B))[0]
    
    # Compute equilibrium allocations
    income_A = p_eq * omega_A[0] + omega_A[1]
    income_B = p_eq * omega_B[0] + omega_B[1]
    
    x1_A = (alpha_A * income_A) / p_eq
    x2_A = ((1 - alpha_A) * income_A) / 1.0
    
    x1_B = (alpha_B * income_B) / p_eq
    x2_B = ((1 - alpha_B) * income_B) / 1.0
    
    return {
        'p_eq': p_eq,
        'allocation_A': (x1_A, x2_A),
        'allocation_B': (x1_B, x2_B),
        'utility_A': (x1_A ** alpha_A) * (x2_A ** (1 - alpha_A)),
        'utility_B': (x1_B ** alpha_B) * (x2_B ** (1 - alpha_B))
    }

# Calibrate to empirical case: symmetric preferences, asymmetric endowments
omega_A = np.array([40.0, 20.0])  # Consumer A: 40 units good 1, 20 units good 2
omega_B = np.array([20.0, 40.0])  # Consumer B: 20 units good 1, 40 units good 2
alpha_A = 0.6  # Consumer A prefers good 1
alpha_B = 0.4  # Consumer B prefers good 2

eq = solve_equilibrium(omega_A, omega_B, alpha_A, alpha_B)

print("General Equilibrium Results:")
print(f"  Equilibrium relative price (p1/p2): {eq['p_eq']:.4f}")
print(f"  Consumer A allocation: ({eq['allocation_A'][0]:.4f}, {eq['allocation_A'][1]:.4f})")
print(f"  Consumer B allocation: ({eq['allocation_B'][0]:.4f}, {eq['allocation_B'][1]:.4f})")
print(f"  Consumer A utility: {eq['utility_A']:.4f}")
print(f"  Consumer B utility: {eq['utility_B']:.4f}")

# Verify market clearing
Omega_1 = omega_A[0] + omega_B[0]
Omega_2 = omega_A[1] + omega_B[1]
total_x1 = eq['allocation_A'][0] + eq['allocation_B'][0]
total_x2 = eq['allocation_A'][1] + eq['allocation_B'][1]
print(f"\nMarket Clearing Verification:")
print(f"  Good 1: Demand={total_x1:.4f}, Supply={Omega_1:.4f}, Excess={total_x1 - Omega_1:.6f}")
print(f"  Good 2: Demand={total_x2:.4f}, Supply={Omega_2:.4f}, Excess={total_x2 - Omega_2:.6f}")
```

Run the script and verify that markets clear to within numerical tolerance (excess demand $< 10^{-6}$). For the given calibration, the equilibrium price should emerge endogenously from the interaction of preferences and endowments. Consumer A, endowed with more of good 1 but preferring good 1, will trade some good 1 for good 2. Consumer B, endowed with more of good 2 but preferring good 2, will trade some good 2 for good 1. The equilibrium price adjusts to balance these offsetting demands, ensuring aggregate demand equals aggregate supply in both markets simultaneously.

Visualize the equilibrium in an Edgeworth box diagram, the classical geometric representation of two-agent exchange economies. The Edgeworth box dimensions are $\Omega_1 \times \Omega_2$, with consumer A's origin at the lower-left and consumer B's origin at the upper-right. Any point in the box represents a feasible allocation: A's consumption is measured from the lower-left, B's from the upper-right. Endowment point $\omega$ lies within the box, and the equilibrium allocation lies on the contract curve (locus of tangencies between agents' indifference curves). Implement the visualization:

```python
def plot_edgeworth_box(omega_A, omega_B, alpha_A, alpha_B, eq):
    Omega_1 = omega_A[0] + omega_B[0]
    Omega_2 = omega_A[1] + omega_B[1]
    
    fig, ax = plt.subplots(figsize=(10, 10))
    
    # Draw box
    ax.plot([0, Omega_1, Omega_1, 0, 0], [0, 0, Omega_2, Omega_2, 0], 'k-', linewidth=2)
    
    # Endowment point
    ax.plot(omega_A[0], omega_A[1], 'bo', markersize=10, label='Endowment ω')
    
    # Equilibrium allocation
    x_A_eq = eq['allocation_A']
    ax.plot(x_A_eq[0], x_A_eq[1], 'ro', markersize=12, label='Equilibrium allocation')
    
    # Budget line through endowment at equilibrium prices
    p = eq['p_eq']
    income_A = p * omega_A[0] + omega_A[1]
    x1_budget = np.linspace(0, Omega_1, 200)
    x2_budget = (income_A - p * x1_budget) / 1.0
    # Clip to box
    valid = (x2_budget >= 0) & (x2_budget <= Omega_2)
    ax.plot(x1_budget[valid], x2_budget[valid], 'g--', linewidth=2, label=f'Budget line (p={p:.3f})')
    
    # Indifference curves for A through endowment and equilibrium
    u_A_endow = (omega_A[0] ** alpha_A) * (omega_A[1] ** (1 - alpha_A))
    u_A_eq = eq['utility_A']
    
    for u_level, style, lbl in [(u_A_endow, 'b:', 'IC_A (endowment)'), (u_A_eq, 'r-', 'IC_A (equilibrium)')]:
        x1_ic = np.linspace(0.1, Omega_1, 300)
        x2_ic = (u_level / (x1_ic ** alpha_A)) ** (1 / (1 - alpha_A))
        valid_ic = (x2_ic >= 0) & (x2_ic <= Omega_2)
        ax.plot(x1_ic[valid_ic], x2_ic[valid_ic], style, linewidth=1.5, label=lbl, alpha=0.7)
    
    ax.set_xlabel('Good 1 for Consumer A (x₁ᴬ)', fontsize=12)
    ax.set_ylabel('Good 2 for Consumer A (x₂ᴬ)', fontsize=12)
    ax.set_title('Edgeworth Box: General Equilibrium', fontsize=14)
    ax.legend(fontsize=10, loc='upper right')
    ax.grid(True, alpha=0.3)
    ax.set_xlim(0, Omega_1)
    ax.set_ylim(0, Omega_2)
    plt.tight_layout()
    plt.savefig('results/edgeworth_box.png', dpi=300)
    plt.show()

plot_edgeworth_box(omega_A, omega_B, alpha_A, alpha_B, eq)
```

The resulting diagram should show the endowment point off the contract curve, the equilibrium allocation on the contract curve (where A's and B's indifference curves are tangent), and the budget line passing through both points at the equilibrium price slope. This tangency condition is the graphical manifestation of the First Welfare Theorem: competitive equilibrium allocations are Pareto efficient—no reallocation can make one consumer better off without making the other worse off.

Verify Pareto efficiency computationally by checking that the marginal rates of substitution are equalized across consumers at the equilibrium allocation. For consumer $i$, $MRS^i = \frac{\alpha^i x_2^i}{(1 - \alpha^i) x_1^i}$. Compute:

```python
def verify_pareto_efficiency(eq, alpha_A, alpha_B):
    x1_A, x2_A = eq['allocation_A']
    x1_B, x2_B = eq['allocation_B']
    
    MRS_A = (alpha_A * x2_A) / ((1 - alpha_A) * x1_A)
    MRS_B = (alpha_B * x2_B) / ((1 - alpha_B) * x1_B)
    
    print(f"\nPareto Efficiency Check:")
    print(f"  MRS_A = {MRS_A:.6f}")
    print(f"  MRS_B = {MRS_B:.6f}")
    print(f"  Equilibrium price ratio (p1/p2) = {eq['p_eq']:.6f}")
    print(f"  MRS equality satisfied: {np.isclose(MRS_A, MRS_B, atol=1e-5)}")
    print(f"  MRS = price ratio: {np.isclose(MRS_A, eq['p_eq'], atol=1e-5)}")

verify_pareto_efficiency(eq, alpha_A, alpha_B)
```

Both consumers' MRS should equal the equilibrium price ratio to within numerical tolerance, confirming that the allocation lies on the contract curve and is Pareto efficient. This verifies the First Welfare Theorem: under complete markets, no externalities, perfect competition, and convex preferences, competitive equilibrium is Pareto optimal.

Perform comparative statics by varying preference parameters and endowments, tracing out how equilibrium prices and allocations respond. This operationalizes the neoclassical claim that prices adjust to equilibrate markets under parameter shocks. Construct three scenarios: (1) increase consumer A's preference for good 1 ($\alpha^A$ rises from 0.6 to 0.7), (2) redistribute endowments (transfer 10 units of good 1 from B to A), and (3) symmetric preference shift (both consumers' $\alpha$ increase by 0.1). For each scenario, compute the new equilibrium and record changes in relative price, allocations, and utilities:

```python
def comparative_statics_analysis():
    scenarios = [
        {
            'name': 'Baseline',
            'omega_A': np.array([40.0, 20.0]),
            'omega_B': np.array([20.0, 40.0]),
            'alpha_A': 0.6,
            'alpha_B': 0.4
        },
        {
            'name': 'Increased α_A (0.6 → 0.7)',
            'omega_A': np.array([40.0, 20.0]),
            'omega_B': np.array([20.0, 40.0]),
            'alpha_A': 0.7,
            'alpha_B': 0.4
        },
        {
            'name': 'Endowment redistribution (10 units good 1: B → A)',
            'omega_A': np.array([50.0, 20.0]),
            'omega_B': np.array([10.0, 40.0]),
            'alpha_A': 0.6,
            'alpha_B': 0.4
        },
        {
            'name': 'Symmetric preference shift (both α increase by 0.1)',
            'omega_A': np.array([40.0, 20.0]),
            'omega_B': np.array([20.0, 40.0]),
            'alpha_A': 0.7,
            'alpha_B': 0.5
        }
    ]
    
    results = []
    for scenario in scenarios:
        eq = solve_equilibrium(scenario['omega_A'], scenario['omega_B'], 
                               scenario['alpha_A'], scenario['alpha_B'])
        results.append({
            'scenario': scenario['name'],
            'p_eq': eq['p_eq'],
            'x1_A': eq['allocation_A'][0],
            'x2_A': eq['allocation_A'][1],
            'x1_B': eq['allocation_B'][0],
            'x2_B': eq['allocation_B'][1],
            'u_A': eq['utility_A'],
            'u_B': eq['utility_B']
        })
    
    import pandas as pd
    df = pd.DataFrame(results)
    print("\nComparative Statics Results:")
    print(df.to_string(index=False))
    df.to_csv('results/comparative_statics.csv', index=False)
    
    return df

cs_results = comparative_statics_analysis()
```

Analyze the results systematically. When consumer A's preference for good 1 strengthens ($\alpha^A$ rises), excess demand for good 1 increases at the original price, driving $p_1$ upward relative to $p_2$. The higher relative price for good 1 induces both consumers to substitute toward good 2, but A's stronger preference sustains higher demand. Consumer A ends up consuming more of good 1 at equilibrium despite the price increase, while B consumes less. When endowments are redistributed toward A, A becomes wealthier and B poorer, but equilibrium price may shift ambiguously depending on the distribution of preferences. In the symmetric preference shift scenario, both consumers demand more of good 1, unambiguously raising $p_1/p_2$. Trace these mechanisms by examining the excess demand function's response to parameter changes.

Calibrate the model to real-world consumption data to ground the analysis empirically. Download household expenditure shares from the Bureau of Labor Statistics Consumer Expenditure Survey (CEX) or OECD National Accounts, focusing on two broad aggregates—say, food and non-food consumption. Compute average expenditure shares: if households spend 20% on food and 80% on non-food, interpret these as revealing underlying preference parameters under the assumption of Cobb-Douglas utility. For a representative consumer, $\alpha = 0.2$ for food and $1 - \alpha = 0.8$ for non-food. Construct a two-type model (low-income and high-income households) by assigning differential endowments and calibrating $\alpha$ parameters to match observed expenditure shares for each type. Solve for equilibrium prices and allocations, then perform policy counterfactuals: impose a consumption tax on food (raising $p_1$), compute the new equilibrium, and measure welfare losses via equivalent variation—the income change that would make consumers as well off under the tax as they were originally. This exercise demonstrates how neoclassical CGE models inform policy analysis: quantifying distributional impacts of taxation, trade liberalization, or subsidy reforms.

Implement a simple tax counterfactual:

```python
def equilibrium_with_tax(omega_A, omega_B, alpha_A, alpha_B, tau, p_init=1.0):
    # tau is ad valorem tax on good 1: consumer price = (1 + tau) * producer price
    # Producer price p solves market clearing; consumer pays (1+tau)*p
    
    def excess_demand_with_tax(p):
        p_consumer = (1 + tau) * p
        income_A = p * omega_A[0] + omega_A[1]
        income_B = p * omega_B[0] + omega_B[1]
        
        x1_A = (alpha_A * income_A) / p_consumer
        x1_B = (alpha_B * income_B) / p_consumer
        
        Omega_1 = omega_A[0] + omega_B[0]
        return (x1_A + x1_B) - Omega_1
    
    p_producer = fsolve(excess_demand_with_tax, p_init)[0]
    p_consumer = (1 + tau) * p_producer
    
    income_A = p_producer * omega_A[0] + omega_A[1]
    income_B = p_producer * omega_B[0] + omega_B[1]
    
    x1_A = (alpha_A * income_A) / p_consumer
    x2_A = ((1 - alpha_A) * income_A) / 1.0
    
    x1_B = (alpha_B * income_B) / p_consumer
    x2_B = ((1 - alpha_B) * income_B) / 1.0
    
    return {
        'p_producer': p_producer,
        'p_consumer': p_consumer,
        'tau': tau,
        'allocation_A': (x1_A, x2_A),
        'allocation_B': (x1_B, x2_B),
        'utility_A': (x1_A ** alpha_A) * (x2_A ** (1 - alpha_A)),
        'utility_B': (x1_B ** alpha_B) * (x2_B ** (1 - alpha_B))
    }

eq_baseline = solve_equilibrium(omega_A, omega_B, alpha_A, alpha_B)
eq_tax = equilibrium_with_tax(omega_A, omega_B, alpha_A, alpha_B, tau=0.25)

print("\nTax Counterfactual Analysis (25% tax on good 1):")
print(f"Baseline equilibrium price: {eq_baseline['p_eq']:.4f}")
print(f"With-tax producer price: {eq_tax['p_producer']:.4f}")
print(f"With-tax consumer price: {eq_tax['p_consumer']:.4f}")
print(f"\nUtility changes:")
print(f"  Consumer A: {eq_baseline['utility_A']:.4f} → {eq_tax['utility_A']:.4f} (Δ = {eq_tax['utility_A'] - eq_baseline['utility_A']:.4f})")
print(f"  Consumer B: {eq_baseline['utility_B']:.4f} → {eq_tax['utility_B']:.4f} (Δ = {eq_tax['utility_B'] - eq_baseline['utility_B']:.4f})")
```

The tax raises the consumer price of good 1, reducing quantities demanded and decreasing both consumers' utilities—a deadweight loss arising from the tax wedge between consumer and producer prices. Quantify this welfare loss by computing the compensating variation: the additional income each consumer would need under the tax regime to restore their baseline utility. For Cobb-Douglas utility, equivalent variation can be calculated from the expenditure function. This exercise demonstrates neoclassical welfare economics in action: measuring efficiency costs of market interventions and identifying Pareto-improving policy reforms.

Document your comparative statics findings, calibration procedure, and tax analysis in a comprehensive report. Include tables of equilibrium outcomes across scenarios, figures showing how equilibrium prices respond to parameter variations, and welfare metrics quantifying policy impacts. This exercise establishes mastery of computable general equilibrium modeling—a workhorse tool of applied neoclassical economics used in trade policy analysis, tax reform evaluation, and climate policy modeling.

## Exercise 3: Stress Testing, Boundary Failure & Recovery Protocol

Probe the limits of neoclassical theory by introducing market failures, non-convexities, and mechanisms that violate the assumptions underlying the welfare theorems. This exercise stress-tests the neoclassical apparatus, revealing where its predictions break down and what institutional repairs restore efficiency. You will implement three scenarios: (1) a consumption externality violating the First Welfare Theorem, (2) increasing returns to scale in production destroying equilibrium existence, and (3) asymmetric information generating adverse selection and market unraveling. For each failure mode, you will diagnose the breakdown mechanism, quantify the efficiency loss, and design corrective institutions (Pigouvian taxes, regulatory constraints, or signaling mechanisms) that recover welfare-optimal outcomes. This exercise transforms you from neoclassical technician to institutional designer, capable of identifying when markets fail and crafting mechanisms to correct them.

Begin with a consumption externality—specifically, a negative externality in which one consumer's consumption of good 1 imposes utility costs on the other. Modify the utility functions from Exercise 2 to include an externality term: $U^A(x_1^A, x_2^A; x_1^B) = (x_1^A)^{\alpha^A} (x_2^A)^{1-\alpha^A} - \gamma (x_1^B)$ and $U^B(x_1^B, x_2^B; x_1^A) = (x_1^B)^{\alpha^B} (x_2^B)^{1-\alpha^B} - \gamma (x_1^A)$, where $\gamma > 0$ measures the externality strength. Each consumer's consumption of good 1 imposes a linear utility penalty on the other—imagine pollution from consumption, congestion, or positional goods. In competitive equilibrium, consumers ignore the external cost they impose, taking others' consumption as given. This leads to overconsumption of good 1 relative to the social optimum, violating the First Welfare Theorem.

Implement the competitive equilibrium with externality. Each consumer solves $\max_{x_1^i, x_2^i} (x_1^i)^{\alpha^i} (x_2^i)^{1-\alpha^i}$ subject to the budget constraint, treating the other's consumption $x_1^{-i}$ as exogenous (taking the externality as given, not internalized). The first-order conditions yield the same Marshallian demand functions as before: $x_1^i = \frac{\alpha^i m^i}{p_1}$, where $m^i = p_1 \omega_1^i + p_2 \omega_2^i$. Solve for competitive equilibrium as in Exercise 2, then evaluate true utilities (including externality costs):

```python
def solve_equilibrium_with_externality(omega_A, omega_B, alpha_A, alpha_B, gamma):
    # Competitive equilibrium ignores externality (same demand as before)
    eq_comp = solve_equilibrium(omega_A, omega_B, alpha_A, alpha_B)
    
    # True utilities accounting for externality
    x1_A, x2_A = eq_comp['allocation_A']
    x1_B, x2_B = eq_comp['allocation_B']
    
    u_A_true = (x1_A ** alpha_A) * (x2_A ** (1 - alpha_A)) - gamma * x1_B
    u_B_true = (x1_B ** alpha_B) * (x2_B ** (1 - alpha_B)) - gamma * x1_A
    
    return {
        'equilibrium': eq_comp,
        'u_A_true': u_A_true,
        'u_B_true': u_B_true,
        'u_A_ignoring_ext': eq_comp['utility_A'],
        'u_B_ignoring_ext': eq_comp['utility_B']
    }

gamma = 0.5  # Externality strength
eq_ext = solve_equilibrium_with_externality(omega_A, omega_B, alpha_A, alpha_B, gamma)

print("\nCompetitive Equilibrium with Externality:")
print(f"  Consumer A utility (ignoring externality): {eq_ext['u_A_ignoring_ext']:.4f}")
print(f"  Consumer A utility (true, with externality): {eq_ext['u_A_true']:.4f}")
print(f"  Consumer B utility (ignoring externality): {eq_ext['u_B_ignoring_ext']:.4f}")
print(f"  Consumer B utility (true, with externality): {eq_ext['u_B_true']:.4f}")
```

The competitive equilibrium allocations are identical to the no-externality case, but true utilities are lower because external costs are realized but not internalized. This demonstrates market failure: competitive equilibrium is no longer Pareto efficient because each consumer imposes uncompensated harm on the other.

Compute the social optimum by solving a planner's problem that internalizes the externality. The social planner maximizes a weighted sum of utilities, say $W = U^A + U^B$, subject to resource constraints $x_1^A + x_1^B = \Omega_1$ and $x_2^A + x_2^B = \Omega_2$. With the externality included, $W = (x_1^A)^{\alpha^A} (x_2^A)^{1-\alpha^A} + (x_1^B)^{\alpha^B} (x_2^B)^{1-\alpha^B} - \gamma(x_1^A + x_1^B)$. Form the Lagrangian: $\mathcal{L} = W + \lambda_1(\Omega_1 - x_1^A - x_1^B) + \lambda_2(\Omega_2 - x_2^A - x_2^B)$. First-order conditions: $\alpha^A (x_1^A)^{\alpha^A - 1} (x_2^A)^{1-\alpha^A} - \gamma = \lambda_1$, $\alpha^B (x_1^B)^{\alpha^B - 1} (x_2^B)^{1-\alpha^B} - \gamma = \lambda_1$, and analogous conditions for good 2. The key difference from competitive equilibrium: the planner equates marginal social benefit (private marginal utility minus externality cost $\gamma$) to the shadow price $\lambda_1$, whereas competitive agents equate private marginal utility to price, ignoring $\gamma$.

Implement the social planner's optimization numerically:

```python
from scipy.optimize import minimize

def social_welfare_with_externality(x, alpha_A, alpha_B, gamma):
    x1_A, x2_A, x1_B, x2_B = x
    u_A = (x1_A ** alpha_A) * (x2_A ** (1 - alpha_A))
    u_B = (x1_B ** alpha_B) * (x2_B ** (1 - alpha_B))
    W = u_A + u_B - gamma * (x1_A + x1_B)
    return -W  # Negative for minimization

def solve_social_optimum_with_externality(omega_A, omega_B, alpha_A, alpha_B, gamma):
    Omega_1 = omega_A[0] + omega_B[0]
    Omega_2 = omega_A[1] + omega_B[1]
    
    constraints = [
        {'type': 'eq', 'fun': lambda x: x[0] + x[2] - Omega_1},  # x1_A + x1_B = Omega_1
        {'type': 'eq', 'fun': lambda x: x[1] + x[3] - Omega_2}   # x2_A + x2_B = Omega_2
    ]
    bounds = [(1e-6, None)] * 4
    
    x0 = [Omega_1/2, Omega_2/2, Omega_1/2, Omega_2/2]
    result = minimize(social_welfare_with_externality, x0, args=(alpha_A, alpha_B, gamma),
                      method='SLSQP', bounds=bounds, constraints=constraints)
    
    if not result.success:
        raise ValueError("Social optimum optimization failed: " + result.message)
    
    x1_A, x2_A, x1_B, x2_B = result.x
    u_A = (x1_A ** alpha_A) * (x2_A ** (1 - alpha_A)) - gamma * x1_B
    u_B = (x1_B ** alpha_B) * (x2_B ** (1 - alpha_B)) - gamma * x1_A
    
    return {
        'allocation_A': (x1_A, x2_A),
        'allocation_B': (x1_B, x2_B),
        'u_A_true': u_A,
        'u_B_true': u_B,
        'total_welfare': u_A + u_B
    }

so_ext = solve_social_optimum_with_externality(omega_A, omega_B, alpha_A, alpha_B, gamma)

print("\nSocial Optimum with Externality:")
print(f"  Allocation A: ({so_ext['allocation_A'][0]:.4f}, {so_ext['allocation_A'][1]:.4f})")
print(f"  Allocation B: ({so_ext['allocation_B'][0]:.4f}, {so_ext['allocation_B'][1]:.4f})")
print(f"  Consumer A utility: {so_ext['u_A_true']:.4f}")
print(f"  Consumer B utility: {so_ext['u_B_true']:.4f}")
print(f"  Total welfare: {so_ext['total_welfare']:.4f}")

# Welfare loss from competitive equilibrium
comp_welfare = eq_ext['u_A_true'] + eq_ext['u_B_true']
welfare_loss = so_ext['total_welfare'] - comp_welfare
print(f"\nWelfare Loss from Market Failure: {welfare_loss:.4f} ({100*welfare_loss/so_ext['total_welfare']:.2f}%)")
```

The social optimum prescribes lower consumption of good 1 than competitive equilibrium, reducing the externality burden. The welfare loss quantifies the efficiency cost of market failure—resources misallocated due to unpriced external costs. This is the canonical Pigouvian externality problem, motivating corrective taxation.

Design and implement a Pigouvian tax that decentralizes the social optimum. The optimal tax per unit of good 1 equals the marginal external cost: $\tau^* = \gamma$. With the tax, consumers face price $p_1 + \tau$ and internalize the externality. Modify the equilibrium solver to include the tax and verify that the taxed competitive equilibrium replicates the social optimum:

```python
def equilibrium_with_pigouvian_tax(omega_A, omega_B, alpha_A, alpha_B, gamma, tau):
    # Consumers face price p1 + tau for good 1
    # Solve for producer price p1 such that markets clear
    
    def excess_demand_with_tax(p1):
        p1_consumer = p1 + tau
        income_A = p1 * omega_A[0] + omega_A[1]
        income_B = p1 * omega_B[0] + omega_B[1]
        
        x1_A = (alpha_A * income_A) / p1_consumer
        x1_B = (alpha_B * income_B) / p1_consumer
        
        Omega_1 = omega_A[0] + omega_B[0]
        return (x1_A + x1_B) - Omega_1
    
    p1_producer = fsolve(excess_demand_with_tax, 1.0)[0]
    p1_consumer = p1_producer + tau
    
    income_A = p1_producer * omega_A[0] + omega_A[1]
    income_B = p1_producer * omega_B[0] + omega_B[1]
    
    x1_A = (alpha_A * income_A) / p1_consumer
    x2_A = ((1 - alpha_A) * income_A) / 1.0
    
    x1_B = (alpha_B * income_B) / p1_consumer
    x2_B = ((1 - alpha_B) * income_B) / 1.0
    
    u_A_true = (x1_A ** alpha_A) * (x2_A ** (1 - alpha_A)) - gamma * x1_B
    u_B_true = (x1_B ** alpha_B) * (x2_B ** (1 - alpha_B)) - gamma * x1_A
    
    return {
        'p1_producer': p1_producer,
        'p1_consumer': p1_consumer,
        'allocation_A': (x1_A, x2_A),
        'allocation_B': (x1_B, x2_B),
        'u_A_true': u_A_true,
        'u_B_true': u_B_true,
        'total_welfare': u_A_true + u_B_true
    }

tau_pigouvian = gamma  # Optimal tax = marginal external cost
eq_taxed = equilibrium_with_pigouvian_tax(omega_A, omega_B, alpha_A, alpha_B, gamma, tau_pigouvian)

print("\nEquilibrium with Pigouvian Tax (τ = γ):")
print(f"  Producer price: {eq_taxed['p1_producer']:.4f}")
print(f"  Consumer price: {eq_taxed['p1_consumer']:.4f}")
print(f"  Allocation A: ({eq_taxed['allocation_A'][0]:.4f}, {eq_taxed['allocation_A'][1]:.4f})")
print(f"  Allocation B: ({eq_taxed['allocation_B'][0]:.4f}, {eq_taxed['allocation_B'][1]:.4f})")
print(f"  Total welfare: {eq_taxed['total_welfare']:.4f}")
print(f"\nWelfare comparison:")
print(f"  Social optimum welfare: {so_ext['total_welfare']:.4f}")
print(f"  Taxed equilibrium welfare: {eq_taxed['total_welfare']:.4f}")
print(f"  Welfare restoration: {np.isclose(eq_taxed['total_welfare'], so_ext['total_welfare'], atol=1e-3)}")
```

The Pigouvian tax should fully restore the social optimum, demonstrating the neoclassical prescription for correcting externalities: price the external cost, internalizing it into private decision-making. This exercise illustrates both market failure and institutional repair, operationalizing Pigou's insight that taxes can align private and social incentives.

Shift to a production economy with increasing returns to scale, violating the convexity assumption required for competitive equilibrium existence. Introduce a single firm producing good 2 from good 1 using a technology exhibiting increasing returns: $x_2 = f(z_1) = A z_1^\beta$ with $\beta > 1$, where $z_1$ is input of good 1. Marginal product $f'(z_1) = A \beta z_1^{\beta - 1}$ is increasing in $z_1$, implying declining average cost: $AC(z_1) = f(z_1)/z_1 = A z_1^{\beta - 1}$ falls as output rises. Under perfect competition, firms price at marginal cost, but with increasing returns, $MC < AC$, so competitive firms cannot break even—profits are negative. This destroys equilibrium existence: no competitive equilibrium exists with positive production.

Implement a model demonstrating equilibrium non-existence. Suppose a consumer with endowment $\omega_1 = 100$ of good 1 and utility $U(x_1, x_2) = x_1^{0.5} x_2^{0.5}$ faces a firm with technology $x_2 = 2 z_1^{1.5}$. Attempt to solve for competitive equilibrium where the firm prices at marginal cost:

```python
def production_equilibrium_increasing_returns(omega_1, A, beta, alpha):
    # Firm's marginal cost: MC = 1 / f'(z1) in terms of good 1 per unit of good 2
    # f(z1) = A * z1^beta, f'(z1) = A * beta * z1^(beta-1)
    # At competitive equilibrium, p2/p1 = MC = 1 / (A * beta * z1^(beta-1))
    # But firm's profit: π = p2 * f(z1) - p1 * z1 = p1 * [p2/p1 * A * z1^beta - z1]
    # With p2/p1 = MC, profit becomes: π = p1 * [A * z1^beta / (A * beta * z1^(beta-1)) - z1]
    #                                     = p1 * [z1/beta - z1] = p1 * z1 * (1/beta - 1)
    # Since beta > 1, profit is negative: no equilibrium with positive production
    
    print("\nIncreasing Returns Production Model:")
    print(f"  Technology: x2 = {A} * z1^{beta}")
    print(f"  Returns to scale: beta = {beta} > 1 (increasing returns)")
    
    # Attempt to compute equilibrium assuming firm operates
    # Consumer demand: x1 = alpha * income / p1, x2 = (1-alpha) * income / p2
    # Income = p1 * omega_1 (endowment value)
    # Firm's first-order condition: p2 = p1 * MC(z1)
    
    # At equilibrium, x2 = consumer demand for good 2 = firm output
    # x2 = (1-alpha) * p1 * omega_1 / p2 = A * z1^beta
    # Also, z1 = omega_1 - x1 (resource constraint)
    
    # This system generally has no solution with positive profit for beta > 1
    print("  Competitive equilibrium does NOT exist with positive production.")
    print("  Reason: Marginal cost < Average cost implies negative profit.")
    print("  Institutional remedy: Natural monopoly regulation or public provision.")
    
    # Compute hypothetical monopoly outcome for comparison
    # Monopolist maximizes profit taking demand into account
    # This requires solving a constrained optimization beyond competitive framework
    print("\n  Alternative: Monopoly or regulated pricing (not implemented here).")

production_equilibrium_increasing_returns(omega_1=100, A=2.0, beta=1.5, alpha=0.5)
```

This scenario reveals a fundamental boundary of neoclassical theory: competitive equilibrium requires convex production sets (constant or decreasing returns), and increasing returns break existence. The institutional remedy is regulation (average-cost pricing, Ramsey pricing) or public ownership—moving outside the competitive market framework. This exercise trains diagnostic ability: recognizing when neoclassical assumptions fail and what alternative mechanisms apply.

Conclude with an adverse selection model, demonstrating information asymmetry leading to market unraveling. Implement the classic Akerlof "lemons" market: sellers know their car's quality (high or low), buyers do not. High-quality cars are worth $v_H = 10,000$ to buyers and cost sellers $c_H = 8,000$; low-quality cars are worth $v_L = 5,000$ to buyers and cost sellers $c_L = 4,000$. Fraction $\theta$ of cars are high-quality. If buyers cannot observe quality, they are willing to pay at most the expected value $p^* = \theta v_H + (1-\theta) v_L$. If $p^* < c_H$, high-quality sellers exit, leaving only low-quality cars. If $p^* < c_L$ even with only lemons, the market collapses entirely.

Implement this model:

```python
def adverse_selection_lemons_market(v_H, c_H, v_L, c_L, theta):
    print("\nAdverse Selection: Lemons Market")
    print(f"  High-quality car: buyer value = {v_H}, seller cost = {c_H}")
    print(f"  Low-quality car: buyer value = {v_L}, seller cost = {c_L}")
    print(f"  Fraction high-quality (θ): {theta}")
    
    # Buyer's willingness to pay given belief theta
    buyer_wtp = theta * v_H + (1 - theta) * v_L
    print(f"\n  Buyer's willingness to pay (expected value): {buyer_wtp:.2f}")
    
    # Determine market equilibrium
    if buyer_wtp >= c_H:
        print("  Outcome: Both high- and low-quality cars trade (pooling equilibrium).")
        print(f"    Market price: {buyer_wtp:.2f}")
        print("    Welfare: First-best (no selection issue).")
    elif c_L <= buyer_wtp < c_H:
        print("  Outcome: Only low-quality cars trade (adverse selection).")
        print(f"    High-quality sellers exit because {buyer_wtp:.2f} < {c_H}.")
        # Buyer updates belief: theta_new = 0
        buyer_wtp_updated = v_L
        print(f"    Buyer's updated willingness to pay: {buyer_wtp_updated:.2f}")
        if buyer_wtp_updated >= c_L:
            print(f"    Market price: {buyer_wtp_updated:.2f}")
            print("    Welfare loss: High-quality cars (surplus-generating) do not trade.")
        else:
            print("    Market collapses: even lemons do not trade.")
    else:
        print("  Outcome: Market collapse (no trade).")
        print(f"    Even with only lemons, {buyer_wtp:.2f} < {c_L}.")
    
    # Quantify welfare loss
    first_best_surplus = theta * (v_H - c_H) + (1 - theta) * (v_L - c_L)
    if buyer_wtp >= c_H:
        actual_surplus = first_best_surplus
    elif c_L <= buyer_wtp < c_H:
        actual_surplus = (1 - theta) * (v_L - c_L)
    else:
        actual_surplus = 0
    
    welfare_loss = first_best_surplus - actual_surplus
    print(f"\n  First-best total surplus: {first_best_surplus:.2f}")
    print(f"  Actual total surplus: {actual_surplus:.2f}")
    print(f"  Welfare loss from adverse selection: {welfare_loss:.2f} ({100*welfare_loss/first_best_surplus:.1f}%)")
    
    return {
        'buyer_wtp': buyer_wtp,
        'first_best_surplus': first_best_surplus,
        'actual_surplus': actual_surplus,
        'welfare_loss': welfare_loss
    }

# Test cases
print("=" * 60)
print("Case 1: Moderate information asymmetry (θ = 0.5)")
adverse_selection_lemons_market(v_H=10000, c_H=8000, v_L=5000, c_L=4000, theta=0.5)

print("\n" + "=" * 60)
print("Case 2: Severe information asymmetry (θ = 0.3)")
adverse_selection_lemons_market(v_H=10000, c_H=8000, v_L=5000, c_L=4000, theta=0.3)
```

In Case 1, with $\theta = 0.5$, buyer's willingness to pay is $0.5 \times 10000 + 0.5 \times 5000 = 7500$, which is less than $c_H = 8000$, so high-quality sellers exit. Only lemons trade, generating welfare loss equal to the foregone high-quality surplus. In Case 2, with $\theta = 0.3$, willingness to pay falls further, potentially collapsing the market entirely if updated beliefs push expected value below even $c_L$. This model demonstrates the Second Welfare Theorem's fragility: asymmetric information prevents Pareto-improving trades, violating the theorem's assumptions. The institutional remedy involves signaling (warranties, certifications) or screening (inspections, reputation mechanisms) to credibly convey quality information.

Design a signaling mechanism to separate high-quality from low-quality sellers. Suppose high-quality sellers can obtain a costly certification (cost $k$) that credibly signals quality. If $k < v_H - c_H$ (benefit of trading high-quality exceeds certification cost) and $k > v_L - c_L$ (lemons sellers cannot profitably mimic), a separating equilibrium exists: high-quality sellers certify, low-quality do not, buyers pay $v_H$ for certified cars and $v_L$ for uncertified. Implement this:

```python
def signaling_equilibrium(v_H, c_H, v_L, c_L, k):
    print("\nSignaling Equilibrium with Certification")
    print(f"  Certification cost (k): {k}")
    
    # High-quality seller's net surplus from certifying and trading
    surplus_H_certify = v_H - c_H - k
    # Low-quality seller's net surplus from certifying (mimicking)
    surplus_L_certify = v_L - c_L - k
    
    print(f"  High-quality seller surplus (certify): {surplus_H_certify:.2f}")
    print(f"  Low-quality seller surplus (certify): {surplus_L_certify:.2f}")
    
    if surplus_H_certify > 0 and surplus_L_certify < 0:
        print("  Separating equilibrium exists:")
        print("    - High-quality sellers certify and trade at price = v_H.")
        print("    - Low-quality sellers do not certify; trade at price = v_L.")
        print("    - Full information restored; first-best welfare achieved (minus certification cost).")
        total_surplus = (v_H - c_H - k) + (v_L - c_L)
        print(f"  Total surplus: {total_surplus:.2f}")
        return total_surplus
    else:
        print("  Separating equilibrium does NOT exist with this certification cost.")
        if surplus_L_certify >= 0:
            print("    Reason: Low-quality sellers can profitably mimic (k too low).")
        if surplus_H_certify <= 0:
            print("    Reason: High-quality sellers will not certify (k too high).")
        return None

print("=" * 60)
signaling_equilibrium(v_H=10000, c_H=8000, v_L=5000, c_L=4000, k=1500)
print("\n" + "=" * 60)
signaling_equilibrium(v_H=10000, c_H=8000, v_L=5000, c_L=4000, k=500)
```

For $k = 1500$, high-quality sellers gain $10000 - 8000 - 1500 = 500$ from certifying, while low-quality sellers lose $5000 - 4000 - 1500 = -500$, sustaining separation. For $k = 500$, low-quality sellers could profitably mimic, collapsing the signal. This exercise demonstrates how institutions (certification, warranties, reputations) can overcome information failures, restoring neoclassical efficiency under appropriate design.

Compile a diagnostic report synthesizing all three failure modes. Document the mechanisms of breakdown: externalities (unpriced social costs), non-convexities (increasing returns destroying competitive equilibrium), and asymmetric information (adverse selection unraveling markets). For each, present quantitative welfare loss calculations, institutional remedies, and conditions under which neoclassical efficiency can be restored. Include plots comparing competitive equilibrium, social optimum, and remediated equilibrium outcomes. This exercise completes your operational mastery: you now recognize not only when neoclassical theory applies, but precisely where its assumptions fail and how to design institutions that correct those failures.

## Operational Reference Guide & Diagnostic Checklist

### Core Neoclassical Principles Verified

**Consumer Optimization:** Every consumer optimization problem must satisfy the tangency condition at the optimum: marginal rate of substitution equals the price ratio. Numerically verify $|MRS - (p_1/p_2)| < 10^{-5}$. If this fails, check constraint binding (interior solution requires $p_1 x_1 + p_2 x_2 = m$ exactly) or boundary conditions (corner solutions at $x_i = 0$ require $MRS \neq$ price ratio). For Cobb-Douglas utility, analytical solution provides a closed-form check: $x_1^* = \alpha m / p_1$ must hold.

**Budget Exhaustion:** Competitive equilibrium allocations must exhaust each consumer's budget. Verify $p_1 x_1^i + p_2 x_2^i = p_1 \omega_1^i + p_2 \omega_2^i$ for all $i$ to within numerical tolerance. If violated, re-solve the optimization with tighter constraint tolerance or check for solver convergence issues.

**Market Clearing:** General equilibrium requires all markets to clear simultaneously. Verify $\sum_i x_j^i = \sum_i \omega_j^i$ for all goods $j$. By Walras' Law, if $n-1$ markets clear and budgets balance, the $n$-th market clears automatically. Check numerically that excess demands $|Z_j(p^*)| < 10^{-5}$ at computed equilibrium prices.

**Pareto Efficiency (First Welfare Theorem):** At competitive equilibrium without externalities or non-convexities, all consumers' marginal rates of substitution must be equalized: $MRS^A = MRS^B = \cdots = p_1/p_2$. Numerically verify pairwise equality to within tolerance. If violated, diagnose whether externalities, public goods, or information asymmetries are present.

**Slutsky Decomposition Identity:** For any price change, verify that substitution effect plus income effect equals total effect: $\Delta x_1^{SE} + \Delta x_1^{IE} = \Delta x_1^{total}$. Compute Hicksian demand at the original utility level and confirm the accounting identity holds numerically.

### Diagnostic Workflow for Computational Equilibrium

**Step 1: Specify Functional Forms and Parameters.** Choose utility functions (Cobb-Douglas, CES, quasi-linear), endowments, and preference parameters. For calibration to data, infer parameters from expenditure shares or elasticity estimates.

**Step 2: Derive or Compute Demand Functions.** For simple functional forms, derive Marshallian demand analytically. For complex utilities, implement numerical optimization using `scipy.optimize.minimize` with SLSQP method, imposing budget constraint and non-negativity bounds.

**Step 3: Construct Excess Demand Function.** Aggregate individual demands and subtract aggregate supply. For pure exchange economies, supply equals total endowments. For production economies, include firm supply derived from profit maximization.

**Step 4: Solve for Equilibrium Prices.** Use root-finding (`scipy.optimize.fsolve` or `scipy.optimize.root`) to solve excess demand equals zero. Normalize one price (numeraire) and solve for relative prices. Verify solution by checking that computed prices yield zero excess demand in all markets.

**Step 5: Verify Optimality Conditions.** Check tangency (MRS = price ratio), budget balance, and market clearing. Compute utilities and welfare metrics. For comparative statics, vary parameters and re-solve, recording equilibrium responses.

**Step 6: Test Boundary Cases.** Probe corner solutions, zero prices, and extreme parameter values. Verify that non-negativity constraints bind correctly and that algorithms handle boundary cases gracefully.

### Common Implementation Pitfalls and Remedies

**Numerical Instability Near Boundaries:** When quantities approach zero, logarithmic or power utility functions may produce infinite marginal utilities. Add small lower bounds ($x_i \geq \epsilon$ with $\epsilon = 10^{-6}$) to prevent division by zero and log of zero errors.

**Non-Uniqueness of Equilibrium:** General equilibrium models may have multiple equilibria, especially with non-convex preferences or production sets. Use multiple initial guesses for root-finding algorithms to detect multiplicity. Plot excess demand as a function of price to visualize zero-crossings.

**Failure to Converge:** If optimization or root-finding fails to converge, check the following: (1) Are functional forms well-behaved (differentiable, strictly quasi-concave utilities)? (2) Are constraints feasible (e.g., endowments positive)? (3) Is the initial guess reasonable? (4) Are optimization tolerances too tight for floating-point precision?

**Externalities and Non-Convexities:** When First Welfare Theorem fails, distinguish the cause. Externalities show up as divergence between private and social marginal costs. Non-convexities manifest as increasing returns or non-convex indifference curves, preventing existence or uniqueness of competitive equilibrium. Information asymmetries require explicit modeling of beliefs and signaling/screening mechanisms.

### Parameter Calibration to Empirical Data

**Expenditure Shares:** For Cobb-Douglas utility $U = x_1^\alpha x_2^{1-\alpha}$, expenditure shares are constant: $\alpha = p_1 x_1 / m$. Estimate $\alpha$ from household expenditure surveys by computing average expenditure share on good 1. For CES utility $U = (\alpha x_1^\rho + (1-\alpha) x_2^\rho)^{1/\rho}$, estimate elasticity of substitution $\sigma = 1/(1-\rho)$ from price variation regressions.

**Demand Elasticities:** Estimate price elasticity $\epsilon_{x_1, p_1}$ from time-series or cross-sectional price-quantity data using log-linear regression: $\ln(x_1) = \beta_0 + \epsilon \ln(p_1) + \text{controls}$. Income elasticity $\eta_{x_1, m}$ similarly from $\ln(x_1) = \gamma_0 + \eta \ln(m) + \text{controls}$. Calibrate utility parameters to match estimated elasticities.

**Endowment Distributions:** For general equilibrium models, calibrate endowments to match observed income distributions or wealth holdings. Use survey data (e.g., Survey of Consumer Finances) to assign initial allocations to representative agents.

### Welfare Measurement and Policy Evaluation

**Consumer Surplus:** For partial equilibrium, compute area under demand curve above price: $CS = \int_{p^*}^\infty x_1(p) \, dp$. For Cobb-Douglas, $CS$ does not have a closed form, but changes in surplus can be computed via compensating or equivalent variation.

**Compensating Variation (CV):** Income change required to restore original utility after a price change: $e(p^1, u^0) - m^0$, where $e(p, u)$ is the expenditure function. For Cobb-Douglas, $e(p_1, p_2, u) = u \left(\frac{p_1}{\alpha}\right)^\alpha \left(\frac{p_2}{1-\alpha}\right)^{1-\alpha}$.

**Equivalent Variation (EV):** Income change at original prices equivalent to the utility change: $m^0 - e(p^0, u^1)$.

**Deadweight Loss (DWL):** Welfare loss from taxation or market distortions. For a per-unit tax $\tau$ on good 1, DWL equals the difference between social surplus at optimum and taxed equilibrium. Compute numerically as difference in aggregate utility or sum of consumer and producer surplus.

**Pareto Frontier:** For two-agent models, compute the set of Pareto-efficient allocations by varying weights in a social welfare function $W = \lambda U^A + (1-\lambda) U^B$ and solving for each $\lambda \in [0, 1]$. Plot the resulting $(U^A, U^B)$ pairs to visualize the Pareto frontier. Competitive equilibrium with transfers can implement any point on this frontier (Second Welfare Theorem).

### Stress Testing Protocol

**Externality Robustness:** Vary externality parameter $\gamma$ from zero to values exceeding private benefits. At $\gamma = 0$, equilibrium should be Pareto efficient. As $\gamma$ increases, welfare loss grows. Compute optimal Pigouvian tax $\tau^* = \gamma$ and verify welfare restoration.

**Returns-to-Scale Boundary:** Test production functions with $\beta$ ranging from 0.5 (decreasing returns) through 1.0 (constant returns) to 1.5 (increasing returns). Verify that competitive equilibrium exists and is unique for $\beta \leq 1$, and fails to exist or requires alternative institutions for $\beta > 1$.

**Information Asymmetry Threshold:** Vary fraction of high-quality goods $\theta$ and certification cost $k$. Identify threshold values where markets collapse versus separate into quality tiers. Plot welfare as a function of $\theta$ and $k$ to map the parameter space into regions of market success, adverse selection, and complete unraveling.

**Preference Heterogeneity:** Introduce agents with diverse preference parameters $\alpha^i$ drawn from a distribution. Solve many-agent general equilibrium (using iterative algorithms or fixed-point methods). Verify that aggregate behavior approximates representative-agent model predictions when heterogeneity is small, and deviates when heterogeneity is large.

### Software and Tool Stack

**Python Scientific Stack:** NumPy for array operations, SciPy for optimization and root-finding, Matplotlib for visualization. Install via `pip install numpy scipy matplotlib` or Anaconda distribution.

**Symbolic Math:** SymPy for analytical differentiation and Lagrangian formulation. Useful for verifying first-order conditions and deriving closed-form solutions. Install via `pip install sympy`.

**Data Handling:** Pandas for importing and processing empirical datasets (CSV, Excel). Install via `pip install pandas`.

**Jupyter Notebooks:** Interactive environment for exploratory analysis, parameter sweeps, and inline plotting. Launch via `jupyter notebook` after installation.

**Optimization Solvers:** For large-scale CGE models, consider specialized solvers like GAMS, AMPL, or Julia's JuMP package. These handle high-dimensional problems more efficiently than general-purpose Python optimizers.

**Verification Scripts:** Maintain a test suite checking known analytical solutions (e.g., Cobb-Douglas equilibrium, Slutsky equation identity). Run tests after code changes to catch regressions.

### Reporting and Documentation Standards

**Model Specification Section:** Clearly document utility functions, endowments, technologies, and parameter values. State assumptions explicitly (e.g., "Preferences are strictly convex and monotonic").

**Equilibrium Results Table:** Present equilibrium prices, quantities, and utilities in a structured table. Include verification metrics (excess demands, tangency conditions, market clearing).

**Comparative Statics Analysis:** Tabulate equilibrium outcomes across parameter variations. Plot equilibrium price as a function of varied parameter. Explain economic intuition for observed responses.

**Welfare Metrics:** Report consumer surplus, total welfare, and deadweight loss where applicable. Quantify efficiency losses from market failures and gains from institutional corrections.

**Code Availability:** Provide complete, runnable scripts in appendices or supplementary materials. Ensure reproducibility by specifying random seeds, solver tolerances, and software versions.

This operational reference guide and diagnostic checklist equips you to implement, verify, and troubleshoot neoclassical economic models independently. You have now completed a full cycle: constructing individual optimization problems, aggregating to general equilibrium, calibrating to data, performing comparative statics, and stress-testing at the boundaries where neoclassical assumptions fail. These labs transform theoretical neoclassical economics into operational practice, preparing you for applied policy analysis, empirical research, and institutional design.
