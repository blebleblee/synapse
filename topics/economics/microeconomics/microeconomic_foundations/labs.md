# Operational Verification Labs: Microeconomic Foundations

## Objective & Operational Lab Setup

These operational verification labs constitute a rigorous practitioner's workbench for testing, validating, and stress-testing the core behavioral predictions and equilibrium mechanisms of microeconomic theory. You will construct consumer demand systems from first principles, estimate price elasticities from real market transaction data, calibrate production functions against firm-level observations, simulate competitive equilibrium under varying market structures, and diagnose welfare losses from policy interventions. Each exercise demands hands-on manipulation of empirical datasets, numerical optimization routines, and simulation models that replicate the foundational theorems of microeconomics in operational settings.

The laboratory environment integrates three primary toolchains. First, you will deploy Python with NumPy, SciPy, and Pandas for numerical optimization, constraint handling, and data manipulation. The `scipy.optimize` module provides nonlinear solvers for utility maximization, cost minimization, and equilibrium price discovery. Second, you will utilize spreadsheet environments—Excel or Google Sheets—equipped with Solver add-ins for constrained optimization problems, enabling transparent inspection of marginal conditions and shadow prices. Third, you will employ R with the `micEcon` and `systemfit` packages for demand system estimation, particularly the Almost Ideal Demand System (AIDS) and translog functional forms that nest classical demand specifications.

Operational prerequisites include a working Python 3.9+ installation with the scientific stack (`pip install numpy scipy pandas matplotlib statsmodels`), access to a spreadsheet application with nonlinear optimization capabilities, and R 4.0+ with econometric packages (`install.packages(c("micEcon", "systemfit", "AER"))`). You will work with real-world datasets: the Bureau of Labor Statistics Consumer Expenditure Survey (CEX) for demand estimation, the U.S. Census Annual Survey of Manufacturers (ASM) for production function analysis, and historical commodity price series from the Federal Reserve Economic Data (FRED) repository for elasticity measurement. Download the CEX public-use microdata files, ASM establishment-level data, and FRED API access credentials before proceeding.

The theoretical grounding rests on the duality between primal optimization problems—utility maximization subject to budget constraints, cost minimization subject to production requirements—and their dual representations through indirect utility functions, expenditure functions, and profit functions. You will verify Shephard's Lemma, Roy's Identity, and Hotelling's Lemma numerically, demonstrating that these theoretical relationships hold to machine precision under well-behaved functional forms. The labs expose you to the computational realities of demand system singularity (when budget shares sum to unity, imposing linear dependence), the curse of dimensionality in high-dimensional preference spaces, and the non-uniqueness of equilibrium in markets with production externalities or increasing returns.

Each exercise follows a diagnostic protocol: specify the theoretical model, parameterize functional forms, solve the optimization problem numerically, verify first-order and second-order conditions, compute comparative statics through numerical differentiation, and stress-test the solution against parameter perturbations and functional form misspecification. You will document sensitivity of equilibrium outcomes to preference parameters, technology coefficients, and market structure assumptions, building intuition for which theoretical predictions remain robust under empirical calibration and which collapse under realistic parameter values.

---

## Exercise 1: Foundational Practical Implementation

### Lab 1.1: Consumer Utility Maximization and Marshallian Demand Derivation

This lab constructs a consumer's optimal consumption bundle by solving the constrained utility maximization problem numerically, deriving Marshallian demand functions, and verifying Roy's Identity through finite-difference approximation. You will parameterize a Cobb-Douglas utility function, impose a linear budget constraint, solve for the optimal bundle using nonlinear optimization, compute the indirect utility function, and confirm that numerical differentiation of indirect utility with respect to prices recovers the Marshallian demand quantities.

Begin by specifying the Cobb-Douglas utility function $U(x_1, x_2) = x_1^{\alpha} x_2^{1-\alpha}$ with preference parameter $\alpha = 0.6$, representing the consumer's relative taste intensity for good 1. The consumer faces prices $p_1 = 2$, $p_2 = 3$, and possesses income $m = 120$. The budget constraint is $p_1 x_1 + p_2 x_2 \leq m$. The Marshallian demand functions, derived analytically via Lagrangian methods, are $x_1^*(p_1, p_2, m) = \frac{\alpha m}{p_1}$ and $x_2^*(p_1, p_2, m) = \frac{(1-\alpha) m}{p_2}$. You will verify these closed-form solutions numerically and then extend to non-separable utility functions lacking analytical solutions.

Create a Python script `consumer_optimization.py` and define the utility function, budget constraint, and numerical solver:

```python
import numpy as np
from scipy.optimize import minimize
import matplotlib.pyplot as plt

# Parameters
alpha = 0.6
p1, p2 = 2.0, 3.0
m = 120.0

# Utility function (negative for minimization)
def utility(x):
    return -(x[0]**alpha * x[1]**(1 - alpha))

# Budget constraint (equality constraint: p1*x1 + p2*x2 = m)
def budget_constraint(x):
    return p1 * x[0] + p2 * x[1] - m

# Initial guess
x0 = np.array([10.0, 10.0])

# Constraint dictionary
constraints = {'type': 'eq', 'fun': budget_constraint}

# Bounds (non-negativity)
bounds = [(0, None), (0, None)]

# Solve
result = minimize(utility, x0, method='SLSQP', bounds=bounds, constraints=constraints)

x1_opt, x2_opt = result.x
U_opt = -result.fun

print(f"Optimal Bundle: x1 = {x1_opt:.4f}, x2 = {x2_opt:.4f}")
print(f"Maximized Utility: U = {U_opt:.4f}")
print(f"Budget Exhaustion Check: {p1*x1_opt + p2*x2_opt:.4f} (should equal {m})")

# Analytical solution for verification
x1_analytical = alpha * m / p1
x2_analytical = (1 - alpha) * m / p2
U_analytical = x1_analytical**alpha * x2_analytical**(1 - alpha)

print(f"\nAnalytical Solution: x1 = {x1_analytical:.4f}, x2 = {x2_analytical:.4f}")
print(f"Analytical Utility: U = {U_analytical:.4f}")
print(f"Numerical Error: {np.abs(U_opt - U_analytical):.6e}")
```

Execute this script. The numerical solver should recover the analytical Marshallian demands $x_1^* = 36$ and $x_2^* = 16$ to within numerical tolerance (typically $10^{-8}$). The budget constraint verification confirms full expenditure of income. Document any discrepancies beyond $10^{-6}$, which indicate either solver convergence failure or constraint violation.

Next, compute the indirect utility function $V(p_1, p_2, m)$, which represents maximum attainable utility as a function of prices and income. For Cobb-Douglas utility, the closed form is $V(p_1, p_2, m) = \frac{m}{p_1^\alpha p_2^{1-\alpha}} \alpha^\alpha (1-\alpha)^{1-\alpha}$. You will verify Roy's Identity, which states that Marshallian demand can be recovered from the indirect utility function via $x_i^* = -\frac{\partial V / \partial p_i}{\partial V / \partial m}$.

Extend the script to compute numerical derivatives of the indirect utility function:

```python
# Indirect utility function
def indirect_utility(p1, p2, m, alpha):
    return (m / (p1**alpha * p2**(1-alpha))) * (alpha**alpha) * ((1-alpha)**(1-alpha))

# Compute V at baseline
V_base = indirect_utility(p1, p2, m, alpha)

# Numerical derivatives using finite differences
epsilon = 1e-6

dV_dp1 = (indirect_utility(p1 + epsilon, p2, m, alpha) - V_base) / epsilon
dV_dp2 = (indirect_utility(p1, p2 + epsilon, m, alpha) - V_base) / epsilon
dV_dm = (indirect_utility(p1, p2, m + epsilon, alpha) - V_base) / epsilon

# Roy's Identity
x1_roy = -dV_dp1 / dV_dm
x2_roy = -dV_dp2 / dV_dm

print(f"\nRoy's Identity Verification:")
print(f"x1 from Roy: {x1_roy:.4f}, x1 from optimization: {x1_opt:.4f}")
print(f"x2 from Roy: {x2_roy:.4f}, x2 from optimization: {x2_opt:.4f}")
print(f"Roy Error x1: {np.abs(x1_roy - x1_opt):.6e}")
print(f"Roy Error x2: {np.abs(x2_roy - x2_opt):.6e}")
```

The Roy's Identity verification should produce errors below $10^{-4}$, confirming the duality relationship. If errors exceed this threshold, reduce the finite-difference step size `epsilon` or increase the optimization solver tolerance.

Now extend to a Constant Elasticity of Substitution (CES) utility function $U(x_1, x_2) = \left( \alpha x_1^\rho + (1-\alpha) x_2^\rho \right)^{1/\rho}$, where $\rho = -1$ yields $\sigma = 1/(1-\rho) = 0.5$ elasticity of substitution. CES utility lacks closed-form Marshallian demands for arbitrary $\rho$, requiring numerical solution. Modify the utility function:

```python
# CES utility parameters
rho = -1.0
sigma = 1.0 / (1.0 - rho)

def utility_ces(x):
    return -((alpha * x[0]**rho + (1 - alpha) * x[1]**rho)**(1/rho))

# Resolve with CES
result_ces = minimize(utility_ces, x0, method='SLSQP', bounds=bounds, constraints=constraints)
x1_ces, x2_ces = result_ces.x
U_ces = -result_ces.fun

print(f"\nCES Utility Optimal Bundle: x1 = {x1_ces:.4f}, x2 = {x2_ces:.4f}")
print(f"CES Maximized Utility: U = {U_ces:.4f}")
```

Document the CES solution. With $\sigma = 0.5$ (strong complementarity), the consumer allocates quantities more evenly compared to Cobb-Douglas, as the goods are less substitutable. Compute the elasticity of substitution empirically by perturbing the price ratio and measuring the induced change in quantity ratio.

### Lab 1.2: Hicksian Demand and Expenditure Minimization with Shephard's Lemma

This lab solves the dual cost-minimization problem: minimize expenditure $p_1 x_1 + p_2 x_2$ subject to achieving a target utility level $\bar{U}$. The solution yields Hicksian (compensated) demand functions $h_i(p_1, p_2, \bar{U})$, which hold utility constant. You will verify Shephard's Lemma, which asserts that Hicksian demand equals the derivative of the expenditure function with respect to price: $h_i = \frac{\partial E(p_1, p_2, \bar{U})}{\partial p_i}$.

Specify the target utility level as the maximized utility from Lab 1.1: $\bar{U} = U_{\text{opt}}$. The expenditure minimization problem is:

$$
\min_{x_1, x_2} \, p_1 x_1 + p_2 x_2 \quad \text{subject to} \quad x_1^\alpha x_2^{1-\alpha} \geq \bar{U}
$$

For Cobb-Douglas utility, the closed-form Hicksian demands are $h_1(p_1, p_2, \bar{U}) = \left(\frac{\alpha}{1-\alpha}\right)^{1-\alpha} \bar{U} \left(\frac{p_2}{p_1}\right)^{1-\alpha}$ and $h_2(p_1, p_2, \bar{U}) = \left(\frac{1-\alpha}{\alpha}\right)^\alpha \bar{U} \left(\frac{p_1}{p_2}\right)^\alpha$. The expenditure function is $E(p_1, p_2, \bar{U}) = \bar{U} \left(\frac{p_1}{\alpha}\right)^\alpha \left(\frac{p_2}{1-\alpha}\right)^{1-\alpha}$.

Implement the expenditure minimization in Python:

```python
# Objective: total expenditure
def expenditure(x):
    return p1 * x[0] + p2 * x[1]

# Utility constraint (inequality: U(x1, x2) >= U_bar)
U_bar = U_opt

def utility_constraint(x):
    return x[0]**alpha * x[1]**(1 - alpha) - U_bar

# Constraint dictionary (inequality: g(x) >= 0)
constraints_hicks = {'type': 'ineq', 'fun': utility_constraint}

# Solve Hicksian demand
result_hicks = minimize(expenditure, x0, method='SLSQP', bounds=bounds, constraints=constraints_hicks)
h1, h2 = result_hicks.x
E_min = result_hicks.fun

print(f"\nHicksian Demand: h1 = {h1:.4f}, h2 = {h2:.4f}")
print(f"Minimum Expenditure: E = {E_min:.4f}")
print(f"Income Consistency Check: E = {E_min:.4f}, m = {m:.4f} (should be equal)")

# Analytical Hicksian demands
h1_analytical = ((alpha / (1 - alpha))**(1 - alpha)) * U_bar * ((p2 / p1)**(1 - alpha))
h2_analytical = (((1 - alpha) / alpha)**alpha) * U_bar * ((p1 / p2)**alpha)
E_analytical = U_bar * ((p1 / alpha)**alpha) * ((p2 / (1 - alpha))**(1 - alpha))

print(f"\nAnalytical Hicksian: h1 = {h1_analytical:.4f}, h2 = {h2_analytical:.4f}")
print(f"Analytical Expenditure: E = {E_analytical:.4f}")
print(f"Numerical Error (Hicksian): {np.abs(E_min - E_analytical):.6e}")
```

The numerical expenditure should equal the consumer's income $m = 120$ to within tolerance, confirming that at optimal Marshallian quantities, expenditure minimization and utility maximization are dual problems yielding identical solutions. The Hicksian demands will coincide with Marshallian demands at the baseline prices because both problems yield the same consumption bundle when evaluated at the same utility level and prices.

Now verify Shephard's Lemma by numerically differentiating the expenditure function with respect to prices:

```python
# Expenditure function
def expenditure_function(p1, p2, U_bar, alpha):
    return U_bar * ((p1 / alpha)**alpha) * ((p2 / (1 - alpha))**(1 - alpha))

# Compute E at baseline
E_base = expenditure_function(p1, p2, U_bar, alpha)

# Numerical derivatives
dE_dp1 = (expenditure_function(p1 + epsilon, p2, U_bar, alpha) - E_base) / epsilon
dE_dp2 = (expenditure_function(p1, p2 + epsilon, U_bar, alpha) - E_base) / epsilon

print(f"\nShephard's Lemma Verification:")
print(f"h1 from Shephard: {dE_dp1:.4f}, h1 from optimization: {h1:.4f}")
print(f"h2 from Shephard: {dE_dp2:.4f}, h2 from optimization: {h2:.4f}")
print(f"Shephard Error h1: {np.abs(dE_dp1 - h1):.6e}")
print(f"Shephard Error h2: {np.abs(dE_dp2 - h2):.6e}")
```

Shephard's Lemma errors should remain below $10^{-4}$. This duality verification is critical: it confirms that Hicksian demand functions are indeed the partial derivatives of the expenditure function, a foundational result linking primal and dual representations of consumer choice.

### Lab 1.3: Slutsky Equation Decomposition of Price Effects

This lab decomposes the total effect of a price change on Marshallian demand into substitution and income effects, operationalizing the Slutsky equation. You will increase the price of good 1, compute the new Marshallian demand, then decompose this change into a substitution effect (holding utility constant via Hicksian demand) and an income effect (adjusting for the income loss due to the price increase).

The Slutsky equation in elasticity form is:

$$
\frac{\partial x_i}{\partial p_j} = \frac{\partial h_i}{\partial p_j} - x_j \frac{\partial x_i}{\partial m}
$$

where the first term is the substitution effect (negative semidefinite) and the second term is the income effect (sign depends on whether the good is normal or inferior).

Perturb the price of good 1 from $p_1 = 2$ to $p_1' = 2.5$ while holding $p_2 = 3$ and $m = 120$ constant. Resolve the utility maximization problem:

```python
# New price
p1_new = 2.5

# Redefine budget constraint
def budget_constraint_new(x):
    return p1_new * x[0] + p2 * x[1] - m

constraints_new = {'type': 'eq', 'fun': budget_constraint_new}

# Resolve Marshallian demand
result_new = minimize(utility, x0, method='SLSQP', bounds=bounds, constraints=constraints_new)
x1_new, x2_new = result_new.x
U_new = -result_new.fun

print(f"\nAfter Price Increase (p1 = {p1_new}):")
print(f"New Marshallian Demand: x1 = {x1_new:.4f}, x2 = {x2_new:.4f}")
print(f"New Utility: U = {U_new:.4f}")

# Total effect
delta_x1_total = x1_new - x1_opt
delta_x2_total = x2_new - x2_opt

print(f"Total Effect on x1: {delta_x1_total:.4f}")
print(f"Total Effect on x2: {delta_x2_total:.4f}")
```

The price increase reduces $x_1$ demand (own-price effect is negative) and increases $x_2$ demand (cross-price effect, as goods are gross substitutes). Now isolate the substitution effect by computing Hicksian demand at the new price $p_1'$ but holding utility at the original level $\bar{U} = U_{\text{opt}}$:

```python
# Hicksian demand at new price, original utility
def utility_constraint_original(x):
    return x[0]**alpha * x[1]**(1 - alpha) - U_opt

constraints_hicks_new = {'type': 'ineq', 'fun': utility_constraint_original}

def expenditure_new(x):
    return p1_new * x[0] + p2 * x[1]

result_hicks_new = minimize(expenditure_new, x0, method='SLSQP', bounds=bounds, constraints=constraints_hicks_new)
h1_new, h2_new = result_hicks_new.x

print(f"\nHicksian Demand at New Price (p1 = {p1_new}), Original Utility:")
print(f"h1 = {h1_new:.4f}, h2 = {h2_new:.4f}")

# Substitution effect
delta_x1_sub = h1_new - x1_opt
delta_x2_sub = h2_new - x2_opt

print(f"Substitution Effect on x1: {delta_x1_sub:.4f}")
print(f"Substitution Effect on x2: {delta_x2_sub:.4f}")

# Income effect
delta_x1_income = delta_x1_total - delta_x1_sub
delta_x2_income = delta_x2_total - delta_x2_sub

print(f"Income Effect on x1: {delta_x1_income:.4f}")
print(f"Income Effect on x2: {delta_x2_income:.4f}")
```

The substitution effect for good 1 is negative (consumers substitute away from the more expensive good), while the income effect is also negative (the price increase reduces real income, decreasing consumption of the normal good). Both effects reinforce, yielding a large total negative effect on $x_1$. For good 2, the substitution effect is positive (substitute toward the relatively cheaper good), but the income effect is negative (reduced real income). The net effect depends on the magnitudes.

Verify the Slutsky equation numerically by comparing the computed decomposition against the Slutsky identity. Compute the income derivative of Marshallian demand by re-solving at a slightly higher income:

```python
# Income derivative (numerical)
m_perturb = m + epsilon

def budget_constraint_income(x):
    return p1 * x[0] + p2 * x[1] - m_perturb

constraints_income = {'type': 'eq', 'fun': budget_constraint_income}

result_income = minimize(utility, x0, method='SLSQP', bounds=bounds, constraints=constraints_income)
x1_income_perturb, x2_income_perturb = result_income.x

dx1_dm = (x1_income_perturb - x1_opt) / epsilon
dx2_dm = (x2_income_perturb - x2_opt) / epsilon

print(f"\nIncome Derivatives: dx1/dm = {dx1_dm:.4f}, dx2/dm = {dx2_dm:.4f}")

# Slutsky verification
slutsky_x1 = delta_x1_sub - x1_opt * dx1_dm * (p1_new - p1)
slutsky_x2 = delta_x2_sub - x2_opt * dx2_dm * (p1_new - p1)

print(f"Slutsky Check x1: Computed Total = {delta_x1_total:.4f}, Slutsky = {slutsky_x1:.4f}")
print(f"Slutsky Check x2: Computed Total = {delta_x2_total:.4f}, Slutsky = {slutsky_x2:.4f}")
```

The Slutsky check should confirm that the decomposition identity holds to numerical precision. Discrepancies beyond $10^{-3}$ indicate insufficient solver precision or finite-difference error accumulation.

---

## Exercise 2: Parameter Variation & Empirical Analysis

### Lab 2.1: Demand System Estimation with Real Consumer Expenditure Data

This lab estimates a complete demand system from household-level expenditure data, recovering price and income elasticities for multiple goods. You will implement the Almost Ideal Demand System (AIDS) using aggregate consumption shares and price indices from the Bureau of Labor Statistics Consumer Expenditure Survey. The AIDS model parameterizes budget shares as functions of prices and total expenditure, nesting homogeneity, symmetry, and adding-up restrictions inherent in rational consumer behavior.

The AIDS budget share equation for good $i$ is:

$$
w_i = \alpha_i + \sum_j \gamma_{ij} \ln p_j + \beta_i \ln\left(\frac{m}{P}\right)
$$

where $w_i = \frac{p_i x_i}{m}$ is the budget share, $P$ is a price index (typically the Stone index $\ln P = \sum_k w_k \ln p_k$), and parameters satisfy $\sum_i \alpha_i = 1$, $\sum_i \gamma_{ij} = 0$ (homogeneity), $\sum_i \beta_i = 0$ (adding-up), and $\gamma_{ij} = \gamma_{ji}$ (symmetry from Slutsky conditions).

Download the CEX annual public-use microdata files from the BLS website. Extract quarterly expenditure data for four aggregate categories: food at home, transportation, housing, and other goods. Construct price indices for each category using the CPI-U detailed series from FRED. Merge expenditure and price data at the household-quarter level, computing budget shares $w_{it}$ and log real expenditure $\ln(m_t / P_t)$.

Load the data in R and estimate the AIDS system using the `systemfit` package, which handles cross-equation restrictions:

```r
library(systemfit)
library(AER)

# Load preprocessed CEX data
# Assume data.frame 'cex_data' with columns: quarter, w_food, w_transport, w_housing, w_other,
# ln_p_food, ln_p_transport, ln_p_housing, ln_p_other, ln_real_exp

# Drop one equation (w_other) due to adding-up constraint
# Estimate three equations jointly

# Define equation formulas
eq_food <- w_food ~ ln_p_food + ln_p_transport + ln_p_housing + ln_real_exp
eq_transport <- w_transport ~ ln_p_food + ln_p_transport + ln_p_housing + ln_real_exp
eq_housing <- w_housing ~ ln_p_food + ln_p_transport + ln_p_housing + ln_real_exp

# System of equations
system <- list(food = eq_food, transport = eq_transport, housing = eq_housing)

# Estimate with SUR (Seemingly Unrelated Regression)
aids_fit <- systemfit(system, method = "SUR", data = cex_data)

# Display results
summary(aids_fit)

# Extract coefficients
coef_matrix <- coef(aids_fit)
print(coef_matrix)
```

The estimation output provides $\hat{\alpha}_i$, $\hat{\gamma}_{ij}$, and $\hat{\beta}_i$ for each equation. Verify that the homogeneity restriction $\sum_j \gamma_{ij} = 0$ holds by summing the estimated price coefficients for each good. The adding-up constraint should be satisfied by construction (one equation dropped). Test the symmetry restriction $\gamma_{ij} = \gamma_{ji}$ using a Wald test:

```r
# Symmetry restriction: gamma_food_transport = gamma_transport_food, etc.
# Extract relevant coefficients and construct restriction matrix R
# For simplicity, test one pair:

# Retrieve coefficients from each equation
gamma_ft_food <- coef(aids_fit)["food_ln_p_transport"]
gamma_tf_transport <- coef(aids_fit)["transport_ln_p_food"]

# Test equality
restriction <- c(gamma_ft_food - gamma_tf_transport)
vcov_matrix <- vcov(aids_fit)

# Extract relevant variances and covariance
# (Requires mapping coefficient indices; simplified here)

# Wald statistic: (R beta)' (R V R')^{-1} (R beta)
# If difference is insignificant, symmetry holds

print(paste("Symmetry Test (Food-Transport):", restriction))
```

Compute price and expenditure elasticities from the estimated AIDS parameters. The Marshallian price elasticity of good $i$ with respect to price $j$ is:

$$
\epsilon_{ij} = -\delta_{ij} + \frac{\gamma_{ij}}{w_i} - \beta_i \frac{w_j}{w_i}
$$

where $\delta_{ij}$ is the Kronecker delta (1 if $i=j$, 0 otherwise). The expenditure elasticity is $\eta_i = 1 + \frac{\beta_i}{w_i}$. Evaluate these at sample mean budget shares:

```r
# Mean budget shares
w_mean <- colMeans(cex_data[, c("w_food", "w_transport", "w_housing")])

# Retrieve beta coefficients
beta_food <- coef(aids_fit)["food_ln_real_exp"]
beta_transport <- coef(aids_fit)["transport_ln_real_exp"]
beta_housing <- coef(aids_fit)["housing_ln_real_exp"]

# Expenditure elasticities
eta_food <- 1 + beta_food / w_mean["w_food"]
eta_transport <- 1 + beta_transport / w_mean["w_transport"]
eta_housing <- 1 + beta_housing / w_mean["w_housing"]

print(paste("Expenditure Elasticity Food:", eta_food))
print(paste("Expenditure Elasticity Transport:", eta_transport))
print(paste("Expenditure Elasticity Housing:", eta_housing))

# Own-price elasticity for food
gamma_ff <- coef(aids_fit)["food_ln_p_food"]
epsilon_ff <- -1 + gamma_ff / w_mean["w_food"] - beta_food / w_mean["w_food"]

print(paste("Own-Price Elasticity Food:", epsilon_ff))

# Cross-price elasticity: food with respect to transport price
gamma_ft <- coef(aids_fit)["food_ln_p_transport"]
epsilon_ft <- gamma_ft / w_mean["w_food"] - beta_food * w_mean["w_transport"] / w_mean["w_food"]

print(paste("Cross-Price Elasticity Food-Transport:", epsilon_ft))
```

Interpret the results. If $\eta_{\text{food}} < 1$, food is a necessity (expenditure elasticity below unity). If $\epsilon_{ff} < -1$, food demand is elastic with respect to its own price. If $\epsilon_{ft} > 0$, food and transportation are gross substitutes. Document these empirical magnitudes, comparing them to textbook priors and prior literature estimates.

### Lab 2.2: Production Function Estimation and Returns to Scale Measurement

This lab estimates a Cobb-Douglas production function from firm-level data, testing for constant, increasing, or decreasing returns to scale. You will use the U.S. Census Annual Survey of Manufacturers establishment-level data, regressing log output on log capital and log labor inputs, and conducting hypothesis tests on the sum of input elasticities.

The Cobb-Douglas production function is $Y = A K^\alpha L^\beta$, where $Y$ is output, $K$ is capital stock, $L$ is labor input, and $A$ is total factor productivity. Taking logarithms yields a linear regression:

$$
\ln Y = \ln A + \alpha \ln K + \beta \ln L + \epsilon
$$

Returns to scale are determined by $\alpha + \beta$: constant if $\alpha + \beta = 1$, increasing if $> 1$, decreasing if $< 1$. Download the ASM public-use file, extracting establishment-level observations of value of shipments (output proxy), book value of assets (capital proxy), and total employment (labor proxy) for the manufacturing sector.

Load the data in Python and estimate the production function via OLS:

```python
import pandas as pd
import statsmodels.api as sm
from statsmodels.iolib.summary2 import summary_col

# Load ASM data
# Assume CSV file 'asm_data.csv' with columns: output, capital, labor
asm = pd.read_csv('asm_data.csv')

# Log transformation
asm['ln_output'] = np.log(asm['output'])
asm['ln_capital'] = np.log(asm['capital'])
asm['ln_labor'] = np.log(asm['labor'])

# Drop missing values
asm = asm.dropna(subset=['ln_output', 'ln_capital', 'ln_labor'])

# OLS regression
X = asm[['ln_capital', 'ln_labor']]
X = sm.add_constant(X)
y = asm['ln_output']

model = sm.OLS(y, X).fit()
print(model.summary())

# Extract coefficients
alpha_hat = model.params['ln_capital']
beta_hat = model.params['ln_labor']
returns_to_scale = alpha_hat + beta_hat

print(f"\nEstimated Capital Elasticity (alpha): {alpha_hat:.4f}")
print(f"Estimated Labor Elasticity (beta): {beta_hat:.4f}")
print(f"Returns to Scale (alpha + beta): {returns_to_scale:.4f}")
```

The estimated coefficients $\hat{\alpha}$ and $\hat{\beta}$ represent the output elasticities with respect to capital and labor. If $\hat{\alpha} + \hat{\beta} \approx 1$, the technology exhibits constant returns to scale, consistent with perfect competition and zero long-run economic profits. Test the null hypothesis $H_0: \alpha + \beta = 1$ using a Wald test:

```python
# Wald test for constant returns to scale
from statsmodels.stats.stattools import omni_normtest

# Restriction: alpha + beta - 1 = 0
# Define restriction matrix R and vector q: R * params = q
R = np.array([[0, 1, 1]])  # [constant, ln_capital, ln_labor]
q = np.array([1])

# Wald test
wald_test = model.wald_test(R, scalar=True)
print(f"\nWald Test for Constant Returns to Scale:")
print(f"F-statistic: {wald_test.fvalue[0][0]:.4f}")
print(f"P-value: {wald_test.pvalue:.4f}")

if wald_test.pvalue > 0.05:
    print("Fail to reject H0: Constant returns to scale.")
else:
    print("Reject H0: Returns to scale differ from constant.")
```

If the p-value exceeds 0.05, you fail to reject constant returns to scale. If rejected, the sign of $\hat{\alpha} + \hat{\beta} - 1$ indicates the direction: positive implies increasing returns (economies of scale), negative implies decreasing returns (dis economies of scale).

Address endogeneity concerns arising from simultaneity bias: firms choose capital and labor in response to productivity shocks, violating the exogeneity assumption. Estimate a fixed-effects model to control for time-invariant establishment heterogeneity:

```python
# Assume panel structure with columns: establishment_id, year, ln_output, ln_capital, ln_labor
# Load panel data
asm_panel = pd.read_csv('asm_panel_data.csv')

# Fixed effects regression using entity dummies (within estimator)
from linearmodels.panel import PanelOLS

# Set index
asm_panel = asm_panel.set_index(['establishment_id', 'year'])

# Fixed effects model
fe_model = PanelOLS(asm_panel['ln_output'], 
                     asm_panel[['ln_capital', 'ln_labor']], 
                     entity_effects=True).fit()

print(fe_model.summary)

alpha_fe = fe_model.params['ln_capital']
beta_fe = fe_model.params['ln_labor']
returns_fe = alpha_fe + beta_fe

print(f"\nFixed Effects Estimates:")
print(f"Capital Elasticity: {alpha_fe:.4f}, Labor Elasticity: {beta_fe:.4f}")
print(f"Returns to Scale (FE): {returns_fe:.4f}")
```

The fixed-effects estimator differences out establishment-specific productivity levels, mitigating omitted variable bias. Compare the OLS and FE estimates: if OLS $\hat{\alpha}$ is larger than FE $\hat{\alpha}$, this suggests upward bias from unobserved productivity correlating positively with capital investment.

Extend to a translog production function, which relaxes the constant-elasticity assumption of Cobb-Douglas:

$$
\ln Y = \beta_0 + \beta_K \ln K + \beta_L \ln L + \frac{1}{2} \beta_{KK} (\ln K)^2 + \frac{1}{2} \beta_{LL} (\ln L)^2 + \beta_{KL} (\ln K)(\ln L) + \epsilon
$$

Estimate this flexible form and test whether the translog collapses to Cobb-Douglas ($\beta_{KK} = \beta_{LL} = \beta_{KL} = 0$):

```python
# Translog specification
asm['ln_capital_sq'] = asm['ln_capital']**2
asm['ln_labor_sq'] = asm['ln_labor']**2
asm['ln_capital_labor'] = asm['ln_capital'] * asm['ln_labor']

X_translog = asm[['ln_capital', 'ln_labor', 'ln_capital_sq', 'ln_labor_sq', 'ln_capital_labor']]
X_translog = sm.add_constant(X_translog)

model_translog = sm.OLS(y, X_translog).fit()
print(model_translog.summary())

# Test Cobb-Douglas restriction
# H0: beta_KK = beta_LL = beta_KL = 0
R_cd = np.array([[0, 0, 0, 1, 0, 0],
                  [0, 0, 0, 0, 1, 0],
                  [0, 0, 0, 0, 0, 1]])
q_cd = np.array([0, 0, 0])

wald_cd = model_translog.wald_test(R_cd, scalar=False)
print(f"\nWald Test for Cobb-Douglas Restriction:")
print(f"F-statistic: {wald_cd.fvalue[0][0]:.4f}, P-value: {wald_cd.pvalue:.4f}")
```

If the Cobb-Douglas restriction is rejected, the translog provides a superior fit, indicating non-constant elasticities of substitution and scale economies that vary with input levels.

### Lab 2.3: Competitive Equilibrium Simulation in a Pure Exchange Economy

This lab simulates a two-agent, two-good pure exchange economy (Edgeworth box), computing the competitive equilibrium price ratio and verifying the First Fundamental Welfare Theorem. You will parameterize agent endowments and preferences, solve for the Walrasian equilibrium, and confirm that the equilibrium allocation lies on the contract curve and is Pareto efficient.

Specify two agents, A and B, with Cobb-Douglas utility functions $U^A(x_1^A, x_2^A) = (x_1^A)^{0.5} (x_2^A)^{0.5}$ and $U^B(x_1^B, x_2^B) = (x_1^B)^{0.7} (x_2^B)^{0.3}$. Agent A's endowment is $\omega^A = (10, 5)$ and agent B's endowment is $\omega^B = (5, 10)$. Total endowments are $X_1 = 15$, $X_2 = 15$.

In competitive equilibrium, agents maximize utility subject to their budget constraints $p_1 x_1^i + p_2 x_2^i = p_1 \omega_1^i + p_2 \omega_2^i$, and markets clear: $x_1^A + x_1^B = X_1$ and $x_2^A + x_2^B = X_2$. Normalize $p_2 = 1$ and solve for the equilibrium relative price $p \equiv p_1 / p_2$.

Agent demands given price $p$ are:

$$
x_1^A(p) = \frac{0.5 (p \cdot 10 + 1 \cdot 5)}{p}, \quad x_2^A(p) = \frac{0.5 (p \cdot 10 + 1 \cdot 5)}{1}
$$

$$
x_1^B(p) = \frac{0.7 (p \cdot 5 + 1 \cdot 10)}{p}, \quad x_2^B(p) = \frac{0.3 (p \cdot 5 + 1 \cdot 10)}{1}
$$

Market clearing for good 1 requires $x_1^A(p) + x_1^B(p) = 15$. Solve for $p^*$:

```python
# Parameters
alpha_A, alpha_B = 0.5, 0.7
omega_A = np.array([10.0, 5.0])
omega_B = np.array([5.0, 10.0])
X_total = omega_A + omega_B

# Demand functions
def demand_A(p):
    m_A = p * omega_A[0] + omega_A[1]
    x1_A = alpha_A * m_A / p
    x2_A = (1 - alpha_A) * m_A
    return np.array([x1_A, x2_A])

def demand_B(p):
    m_B = p * omega_B[0] + omega_B[1]
    x1_B = alpha_B * m_B / p
    x2_B = (1 - alpha_B) * m_B
    return np.array([x1_B, x2_B])

# Market clearing condition for good 1
def excess_demand_1(p):
    return demand_A(p)[0] + demand_B(p)[0] - X_total[0]

# Solve for equilibrium price
from scipy.optimize import fsolve

p_eq = fsolve(excess_demand_1, x0=1.0)[0]

# Equilibrium allocations
x_A_eq = demand_A(p_eq)
x_B_eq = demand_B(p_eq)

print(f"Equilibrium Relative Price: p* = {p_eq:.4f}")
print(f"Agent A Allocation: x1_A = {x_A_eq[0]:.4f}, x2_A = {x_A_eq[1]:.4f}")
print(f"Agent B Allocation: x1_B = {x_B_eq[0]:.4f}, x2_B = {x_B_eq[1]:.4f}")

# Verify market clearing for good 2
excess_2 = x_A_eq[1] + x_B_eq[1] - X_total[1]
print(f"Market Clearing Good 2 (excess demand): {excess_2:.6e}")
```

The equilibrium price $p^*$ clears the market for good 1, and by Walras' Law, good 2 also clears. Verify that the equilibrium allocation is Pareto efficient by checking that marginal rates of substitution (MRS) are equalized across agents. The MRS for agent $i$ is:

$$
\text{MRS}^i = \frac{\partial U^i / \partial x_1}{\partial U^i / \partial x_2} = \frac{\alpha^i x_2^i}{(1 - \alpha^i) x_1^i}
$$

Compute MRS at equilibrium:

```python
# MRS calculations
MRS_A = (alpha_A * x_A_eq[1]) / ((1 - alpha_A) * x_A_eq[0])
MRS_B = (alpha_B * x_B_eq[1]) / ((1 - alpha_B) * x_B_eq[0])

print(f"\nMarginal Rate of Substitution:")
print(f"MRS^A = {MRS_A:.4f}, MRS^B = {MRS_B:.4f}")
print(f"MRS Equality (should be equal at equilibrium): {np.abs(MRS_A - MRS_B):.6e}")

# Both should equal the price ratio
print(f"Price Ratio p* = {p_eq:.4f}")
print(f"Tangency Check: MRS^A - p* = {np.abs(MRS_A - p_eq):.6e}")
print(f"Tangency Check: MRS^B - p* = {np.abs(MRS_B - p_eq):.6e}")
```

At competitive equilibrium, $\text{MRS}^A = \text{MRS}^B = p^*$, confirming that indifference curves are tangent to each other and to the price line, the hallmark of Pareto efficiency. Any deviation would imply gains from trade, contradicting equilibrium.

Visualize the Edgeworth box with endowment point, contract curve, and equilibrium allocation:

```python
import matplotlib.pyplot as plt

# Contract curve: MRS^A = MRS^B implies a locus in the box
# For Cobb-Douglas: x2^A / x1^A = (alpha_A / (1 - alpha_A)) * (1 - alpha_B) / alpha_B * (x2^B / x1^B)
# Given x1^A + x1^B = X1, x2^A + x2^B = X2, solve parametrically

# Generate contract curve points
x1_A_range = np.linspace(0.1, X_total[0] - 0.1, 100)
x2_A_contract = []

for x1_A_val in x1_A_range:
    x1_B_val = X_total[0] - x1_A_val
    # From MRS equality: (alpha_A * x2_A) / ((1-alpha_A) * x1_A) = (alpha_B * x2_B) / ((1-alpha_B) * x1_B)
    # x2_A / x1_A = [(alpha_A) / (1-alpha_A)] * [(1-alpha_B) / alpha_B] * [x2_B / x1_B]
    # Also x2_A + x2_B = X2, so x2_B = X2 - x2_A
    # Solve: x2_A = f(x1_A, x1_B, X2)
    
    # Simplified: MRS^A = MRS^B
    # (alpha_A * x2_A) / ((1-alpha_A) * x1_A) = (alpha_B * (X2 - x2_A)) / ((1-alpha_B) * x1_B)
    # Solve for x2_A
    numerator = alpha_A * alpha_B * X_total[1] * (1 - alpha_B) * x1_B_val
    denominator = (1 - alpha_A) * alpha_B * (1 - alpha_B) * x1_A_val + alpha_A * alpha_B * (1 - alpha_B) * x1_B_val
    x2_A_val = numerator / denominator if denominator != 0 else 0
    x2_A_contract.append(x2_A_val)

# Plot Edgeworth box
fig, ax = plt.subplots(figsize=(8, 8))

# Box boundaries
ax.set_xlim(0, X_total[0])
ax.set_ylim(0, X_total[1])
ax.set_xlabel('Good 1 (Agent A perspective)')
ax.set_ylabel('Good 2 (Agent A perspective)')
ax.set_title('Edgeworth Box: Competitive Equilibrium')

# Endowment point
ax.plot(omega_A[0], omega_A[1], 'ro', markersize=10, label='Endowment')

# Equilibrium allocation
ax.plot(x_A_eq[0], x_A_eq[1], 'go', markersize=10, label='Equilibrium')

# Contract curve
ax.plot(x1_A_range, x2_A_contract, 'b-', linewidth=2, label='Contract Curve')

# Budget line through equilibrium (slope = -p*)
x1_budget = np.linspace(0, X_total[0], 100)
# Budget: p * x1 + x2 = p * omega1 + omega2
# x2 = (p * omega_A[0] + omega_A[1]) - p * x1
x2_budget = (p_eq * omega_A[0] + omega_A[1]) - p_eq * x1_budget
ax.plot(x1_budget, x2_budget, 'r--', linewidth=1.5, label=f'Budget Line (p={p_eq:.2f})')

ax.legend()
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('edgeworth_box_equilibrium.png', dpi=150)
plt.show()

print("\nEdgeworth box plot saved as 'edgeworth_box_equilibrium.png'")
```

The visualization confirms that the equilibrium allocation lies on the contract curve (Pareto set) and that the budget line (representing the competitive price ratio) is tangent to both agents' indifference curves at the equilibrium point.

---

## Exercise 3: Stress Testing, Boundary Failure & Recovery Protocol

### Lab 3.1: Non-Convex Preferences and Equilibrium Non-Existence

This lab investigates the breakdown of competitive equilibrium existence when preferences violate convexity, a foundational assumption in general equilibrium theory. You will construct a counterexample with non-convex indifference curves, demonstrate that Walrasian equilibrium fails to exist, and explore alternative solution concepts such as price-taking behavior with indivisible goods.

Specify a utility function with a non-convex region: $U(x_1, x_2) = \min(x_1, x_2) + x_1 x_2$, which combines Leontief (perfect complements) and supermodular (increasing marginal rate of substitution) components. The indifference curves are kinked at $x_1 = x_2$ and bow inward (non-convex to the origin) away from the diagonal.

Attempt to solve the utility maximization problem numerically under prices $p_1 = 1$, $p_2 = 1$, and income $m = 10$:

```python
# Non-convex utility
def utility_nonconvex(x):
    return -(np.minimum(x[0], x[1]) + x[0] * x[1])

# Budget constraint
p1_nc, p2_nc, m_nc = 1.0, 1.0, 10.0

def budget_nc(x):
    return p1_nc * x[0] + p2_nc * x[1] - m_nc

constraints_nc = {'type': 'eq', 'fun': budget_nc}
bounds_nc = [(0, None), (0, None)]

# Initial guess on diagonal
x0_nc = np.array([5.0, 5.0])

result_nc = minimize(utility_nonconvex, x0_nc, method='SLSQP', bounds=bounds_nc, constraints=constraints_nc)

print(f"Non-Convex Optimization Result:")
print(f"Success: {result_nc.success}")
print(f"Optimal Bundle: x1 = {result_nc.x[0]:.4f}, x2 = {result_nc.x[1]:.4f}")
print(f"Maximized Utility: {-result_nc.fun:.4f}")
```

The solver may fail to converge or report local optima, as the objective function is non-concave. To diagnose, compute the Hessian matrix of the utility function at candidate points to check for negative semi-definiteness (concavity condition):

```python
from scipy.optimize import approx_fprime

# Hessian approximation via finite differences
def hessian_fd(func, x, epsilon=1e-5):
    n = len(x)
    H = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            x_pp = x.copy(); x_pp[i] += epsilon; x_pp[j] += epsilon
            x_pm = x.copy(); x_pm[i] += epsilon; x_pm[j] -= epsilon
            x_mp = x.copy(); x_mp[i] -= epsilon; x_mp[j] += epsilon
            x_mm = x.copy(); x_mm[i] -= epsilon; x_mm[j] -= epsilon
            H[i, j] = (func(x_pp) - func(x_pm) - func(x_mp) + func(x_mm)) / (4 * epsilon**2)
    return H

# Evaluate Hessian at a point off the diagonal
x_test = np.array([3.0, 7.0])
H = hessian_fd(lambda x: -utility_nonconvex(x), x_test)

eigenvalues = np.linalg.eigvalsh(H)
print(f"\nHessian Eigenvalues at x = {x_test}: {eigenvalues}")

if np.any(eigenvalues > 0):
    print("Utility function is NOT concave (positive eigenvalue detected).")
else:
    print("Utility function is concave at this point.")
```

If any eigenvalue is positive, the utility function is not globally concave, violating the convexity of preferences. This leads to multiple local maxima and potential non-existence of a unique demand function.

Demonstrate non-existence of Walrasian equilibrium in a two-agent exchange economy with these preferences. Set up agents with identical non-convex utilities and symmetric endowments, then search for a market-clearing price:

```python
# Two agents with non-convex utility: U(x1, x2) = min(x1, x2) + x1*x2
# Endowments: Agent A has (8, 2), Agent B has (2, 8)
omega_A_nc = np.array([8.0, 2.0])
omega_B_nc = np.array([2.0, 8.0])
X_total_nc = omega_A_nc + omega_B_nc  # (10, 10)

def utility_nc(x):
    return np.minimum(x[0], x[1]) + x[0] * x[1]

# Demand function via optimization (may have multiple solutions)
def demand_nc(p, omega, m_income):
    def obj(x):
        return -utility_nc(x)
    
    def budget_c(x):
        return p * x[0] + x[1] - m_income
    
    cons = {'type': 'eq', 'fun': budget_c}
    bnds = [(0, None), (0, None)]
    
    # Try multiple initial guesses to find global optimum
    results = []
    for x0_init in [np.array([0.5, m_income - 0.5]), np.array([m_income / (p + 1), m_income / (p + 1)])]:
        res = minimize(obj, x0_init, method='SLSQP', bounds=bnds, constraints=cons)
        if res.success:
            results.append((res.x, -res.fun))
    
    # Return the best result
    if len(results) == 0:
        return None
    best = max(results, key=lambda r: r[1])
    return best[0]

# Attempt to find equilibrium price
def excess_demand_nc(p):
    m_A = p * omega_A_nc[0] + omega_A_nc[1]
    m_B = p * omega_B_nc[0] + omega_B_nc[1]
    
    x_A = demand_nc(p, omega_A_nc, m_A)
    x_B = demand_nc(p, omega_B_nc, m_B)
    
    if x_A is None or x_B is None:
        return np.inf  # Demand not well-defined
    
    return x_A[0] + x_B[0] - X_total_nc[0]

# Search for equilibrium
p_range = np.linspace(0.1, 5.0, 50)
excess_vals = []

for p_test in p_range:
    ed = excess_demand_nc(p_test)
    excess_vals.append(ed)
    print(f"Price p = {p_test:.2f}, Excess Demand Good 1: {ed:.4f}")

# Plot excess demand
plt.figure(figsize=(10, 6))
plt.plot(p_range, excess_vals, 'b-', linewidth=2)
plt.axhline(0, color='r', linestyle='--', label='Market Clearing')
plt.xlabel('Relative Price p')
plt.ylabel('Excess Demand for Good 1')
plt.title('Excess Demand Function with Non-Convex Preferences')
plt.legend()
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('excess_demand_nonconvex.png', dpi=150)
plt.show()

print("\nExcess demand plot saved. Inspect for zero-crossing (equilibrium).")
```

If the excess demand function does not cross zero or crosses multiple times with discontinuities, competitive equilibrium fails to exist or is not unique. The non-convexity breaks the standard proof of equilibrium existence (which relies on Brouwer or Kakutani fixed-point theorems applied to convex-valued demand correspondences). This lab demonstrates a fundamental boundary of general equilibrium theory: without convexity, decentralized markets may fail to coordinate agents efficiently.

### Lab 3.2: Externalities, Missing Markets, and Pigouvian Taxation

This lab quantifies the welfare loss from a negative production externality and evaluates the corrective Pigouvian tax required to restore Pareto efficiency. You will simulate a competitive market with pollution spillovers, compute the unregulated equilibrium, measure deadweight loss, and calibrate the optimal tax rate that internalizes the external cost.

Consider a market for a good whose production generates pollution, imposing external costs on third parties. The competitive supply curve reflects private marginal cost (PMC), while the social marginal cost (SMC) includes the external damage. Demand is linear $Q^d = 100 - P$, private supply is $Q^s = P$ (PMC = $P$), and the marginal external cost is $\text{MEC} = 0.5 Q$.

The competitive equilibrium ignores the externality, equating private supply and demand:

$$
100 - P = P \implies P^* = 50, \quad Q^* = 50
$$

The social optimum equates demand with social marginal cost $\text{SMC} = \text{PMC} + \text{MEC} = P + 0.5 Q$:

$$
100 - Q = Q + 0.5 Q \implies 1.5 Q = 100 \implies Q^{\text{opt}} = \frac{100}{1.5} \approx 66.67
$$

Wait, this implies overproduction, but externalities typically cause overproduction when SMC > PMC. Let me recalculate. If $P = Q$ (supply) and $\text{SMC} = Q + 0.5 Q = 1.5 Q$, then at social optimum:

$$
100 - Q = 1.5 Q \implies Q^{\text{opt}} = \frac{100}{2.5} = 40, \quad P^{\text{opt}} = 60
$$

The unregulated market produces $Q^* = 50 > Q^{\text{opt}} = 40$, overproducing by 10 units. Implement this in Python:

```python
# Market parameters
def demand(P):
    return 100 - P

def supply(P):
    return P

def mec(Q):
    return 0.5 * Q

# Competitive equilibrium
from scipy.optimize import fsolve

def market_eq(P):
    return demand(P) - supply(P)

P_star = fsolve(market_eq, x0=50)[0]
Q_star = supply(P_star)

print(f"Competitive Equilibrium: P* = {P_star:.2f}, Q* = {Q_star:.2f}")

# Social optimum: demand = PMC + MEC
def social_opt(Q):
    P_demand = 100 - Q
    SMC = Q + mec(Q)  # PMC = Q, MEC = 0.5 Q
    return P_demand - SMC

Q_opt = fsolve(social_opt, x0=40)[0]
P_opt = 100 - Q_opt

print(f"Social Optimum: P_opt = {P_opt:.2f}, Q_opt = {Q_opt:.2f}")

# Deadweight loss (DWL)
# DWL = integral from Q_opt to Q_star of (SMC - Demand) dQ
# Demand = 100 - Q, SMC = 1.5 Q
from scipy.integrate import quad

def dwl_integrand(Q):
    return (1.5 * Q) - (100 - Q)

DWL, _ = quad(dwl_integrand, Q_opt, Q_star)

print(f"\nDeadweight Loss from Externality: {DWL:.2f}")
```

The deadweight loss measures the welfare reduction due to overproduction. To correct this, impose a Pigouvian tax equal to the marginal external cost at the optimal quantity:

$$
t = \text{MEC}(Q^{\text{opt}}) = 0.5 \times 40 = 20
$$

The tax shifts the private supply curve upward by $t$, making the new supply $Q^s = P - t$. Verify that the tax restores the social optimum:

```python
# Pigouvian tax
t_pigouvian = mec(Q_opt)

print(f"\nPigouvian Tax: t = {t_pigouvian:.2f}")

# New equilibrium with tax: Demand = Supply + tax
# 100 - P = P - t
def taxed_eq(P):
    return demand(P) - (P - t_pigouvian)

P_tax = fsolve(taxed_eq, x0=50)[0]
Q_tax = demand(P_tax)

print(f"Equilibrium with Tax: P_tax = {P_tax:.2f}, Q_tax = {Q_tax:.2f}")
print(f"Verification: Q_tax should equal Q_opt = {Q_opt:.2f}, Difference: {np.abs(Q_tax - Q_opt):.4f}")
```

The tax induces the competitive equilibrium to align with the social optimum, eliminating the deadweight loss. Visualize the supply-demand diagram with externality and tax:

```python
Q_range = np.linspace(0, 100, 200)
P_demand = 100 - Q_range
P_supply = Q_range
P_smc = 1.5 * Q_range

plt.figure(figsize=(10, 7))
plt.plot(Q_range, P_demand, 'b-', linewidth=2, label='Demand')
plt.plot(Q_range, P_supply, 'r-', linewidth=2, label='Private Supply (PMC)')
plt.plot(Q_range, P_smc, 'g-', linewidth=2, label='Social Supply (SMC)')

# Competitive equilibrium
plt.plot(Q_star, P_star, 'ro', markersize=10, label=f'Competitive Eq. (Q={Q_star:.1f}, P={P_star:.1f})')

# Social optimum
plt.plot(Q_opt, P_opt, 'go', markersize=10, label=f'Social Optimum (Q={Q_opt:.1f}, P={P_opt:.1f})')

# Deadweight loss triangle
plt.fill_between([Q_opt, Q_star], [P_opt, P_star], [100 - Q_opt, 100 - Q_star], alpha=0.3, color='red', label='Deadweight Loss')

plt.xlabel('Quantity')
plt.ylabel('Price')
plt.title('Externality, Market Failure, and Pigouvian Taxation')
plt.legend()
plt.grid(True, alpha=0.3)
plt.xlim(0, 100)
plt.ylim(0, 100)
plt.tight_layout()
plt.savefig('externality_pigouvian_tax.png', dpi=150)
plt.show()

print("Externality diagram saved as 'externality_pigouvian_tax.png'")
```

This lab operationalizes the Pigouvian tax mechanism, a cornerstone policy tool for internalizing externalities. In practice, calibrating the tax requires empirical estimation of the marginal external damage function, often derived from environmental damage assessments or epidemiological studies linking pollution exposure to health costs.

### Lab 3.3: Asymmetric Information and Adverse Selection in Insurance Markets

This lab models adverse selection in an insurance market where buyers have private information about their risk types, leading to market unraveling. You will simulate a pooling equilibrium, demonstrate how it collapses when the price reflects average risk, and explore separating equilibria with screening contracts.

Consider a population of individuals with two risk types: high-risk (probability of loss $\pi_H = 0.4$) and low-risk ($\pi_L = 0.1$). The loss amount is $L = 100$. The fraction of high-risk types is $\lambda = 0.3$. Individuals have utility function $U(W) = \sqrt{W}$ (risk-averse) and initial wealth $W_0 = 200$. Insurers are risk-neutral and competitive, pricing at actuarially fair rates if types are known.

In a pooling equilibrium, insurers cannot distinguish types and charge a single premium reflecting average risk. The average loss probability is:

$$
\bar{\pi} = \lambda \pi_H + (1 - \lambda) \pi_L = 0.3 \times 0.4 + 0.7 \times 0.1 = 0.19
$$

The pooling premium for full coverage is $P_{\text{pool}} = \bar{\pi} \times L = 0.19 \times 100 = 19$. Low-risk individuals face an actuarially unfair price ($19 > 0.1 \times 100 = 10$), while high-risk individuals face a favorable price ($19 < 0.4 \times 100 = 40$).

Compute expected utility for each type under full coverage:

```python
# Parameters
pi_H, pi_L = 0.4, 0.1
L = 100.0
W0 = 200.0
lambda_frac = 0.3
pi_avg = lambda_frac * pi_H + (1 - lambda_frac) * pi_L

# Utility function
def utility(W):
    return np.sqrt(W)

# Pooling premium
P_pool = pi_avg * L

print(f"Pooling Premium: P_pool = {P_pool:.2f}")

# Expected utility with insurance (full coverage)
# High-risk: certain wealth W0 - P_pool
EU_H_insured = utility(W0 - P_pool)

# Low-risk: certain wealth W0 - P_pool
EU_L_insured = utility(W0 - P_pool)

print(f"\nExpected Utility with Pooling Insurance:")
print(f"High-risk: EU_H = {EU_H_insured:.4f}")
print(f"Low-risk: EU_L = {EU_L_insured:.4f}")

# Expected utility without insurance (self-insurance)
# High-risk: EU = pi_H * U(W0 - L) + (1 - pi_H) * U(W0)
EU_H_no_ins = pi_H * utility(W0 - L) + (1 - pi_H) * utility(W0)

# Low-risk
EU_L_no_ins = pi_L * utility(W0 - L) + (1 - pi_L) * utility(W0)

print(f"\nExpected Utility without Insurance:")
print(f"High-risk: EU_H = {EU_H_no_ins:.4f}")
print(f"Low-risk: EU_L = {EU_L_no_ins:.4f}")

# Participation decision
print(f"\nParticipation Decision:")
if EU_H_insured > EU_H_no_ins:
    print("High-risk types BUY insurance.")
else:
    print("High-risk types REJECT insurance.")

if EU_L_insured > EU_L_no_ins:
    print("Low-risk types BUY insurance.")
else:
    print("Low-risk types REJECT insurance.")
```

If low-risk individuals reject the pooling contract (because $EU_{L,\text{insured}} < EU_{L,\text{no ins}}$), the pool composition shifts entirely to high-risk types. Insurers update the premium to $P = \pi_H \times L = 40$, but then high-risk individuals also find insurance too expensive at this price if it exceeds their willingness to pay. This iterative process can lead to complete market unraveling, with no insurance sold—a classic adverse selection failure.

To prevent unraveling, insurers can offer separating contracts that screen types. A high-coverage contract targets high-risk individuals, and a low-coverage (partial insurance) contract targets low-risk individuals. The low-coverage contract is designed to be unattractive to high-risk types (incentive compatibility) while providing sufficient value to low-risk types.

Design separating contracts:

```python
# High-coverage contract: full coverage for high-risk
# Premium: P_H = pi_H * L = 40
P_H = pi_H * L
coverage_H = L

# Low-coverage contract: partial coverage for low-risk
# Coverage fraction alpha, premium P_L = pi_L * alpha * L
# Choose alpha such that low-risk accepts and high-risk rejects

# Incentive compatibility: high-risk should prefer high-coverage contract
# EU_H(high contract) >= EU_H(low contract)

# Participation: low-risk should accept low-coverage contract
# EU_L(low contract) >= EU_L(no insurance)

# Simplify: set alpha such that low-risk is indifferent to self-insurance
# EU_L(insured) = pi_L * U(W0 - alpha*L - P_L) + (1 - pi_L) * U(W0 - P_L)
# where P_L = pi_L * alpha * L

# For full separation, solve for alpha that satisfies IC and PC constraints
# Here, use alpha = 0.5 (half coverage) as a candidate

alpha = 0.5
P_L = pi_L * alpha * L
coverage_L = alpha * L

# Expected utilities under separating contracts
# High-risk with high-coverage
EU_H_high = utility(W0 - P_H)

# High-risk with low-coverage
# EU = pi_H * U(W0 - (L - coverage_L) - P_L) + (1 - pi_H) * U(W0 - P_L)
# After loss, out-of-pocket = L - coverage_L
EU_H_low = pi_H * utility(W0 - (L - coverage_L) - P_L) + (1 - pi_H) * utility(W0 - P_L)

# Low-risk with low-coverage
EU_L_low = pi_L * utility(W0 - (L - coverage_L) - P_L) + (1 - pi_L) * utility(W0 - P_L)

print(f"\nSeparating Contracts:")
print(f"High-coverage: Premium = {P_H:.2f}, Coverage = {coverage_H:.2f}")
print(f"Low-coverage: Premium = {P_L:.2f}, Coverage = {coverage_L:.2f}")

print(f"\nIncentive Compatibility Check (High-risk):")
print(f"EU_H(high) = {EU_H_high:.4f}, EU_H(low) = {EU_H_low:.4f}")
if EU_H_high > EU_H_low:
    print("High-risk prefers high-coverage contract (IC satisfied).")
else:
    print("High-risk prefers low-coverage contract (IC violated).")

print(f"\nParticipation Check (Low-risk):")
print(f"EU_L(low) = {EU_L_low:.4f}, EU_L(no ins) = {EU_L_no_ins:.4f}")
if EU_L_low > EU_L_no_ins:
    print("Low-risk accepts low-coverage contract (PC satisfied).")
else:
    print("Low-risk rejects low-coverage contract (PC violated).")
```

Adjust the coverage fraction $\alpha$ iteratively until both incentive compatibility and participation constraints bind. The separating equilibrium involves distortion away from first-best: low-risk individuals receive incomplete insurance (inefficient underinsurance) to prevent high-risk types from mimicking them. This deadweight loss is the cost of information asymmetry.

This lab operationalizes screening and signaling mechanisms, foundational concepts in contract theory and information economics. Real-world applications include insurance deductibles, warranties, and employment contracts with performance-based pay structures.

---

## Operational Reference Guide & Diagnostic Checklist

### Utility Maximization and Demand Derivation

**Verification Checklist:**
- Budget constraint binding at optimum: $p_1 x_1^* + p_2 x_2^* = m$ (tolerance $< 10^{-6}$)
- First-order conditions (Lagrangian): $\frac{\partial U / \partial x_i}{\lambda} = p_i$ for all goods
- Roy's Identity: numerical derivative of indirect utility recovers Marshallian demand (error $< 10^{-4}$)
- Shephard's Lemma: numerical derivative of expenditure function equals Hicksian demand (error $< 10^{-4}$)
- Slutsky decomposition: total effect = substitution effect + income effect (error $< 10^{-3}$)

**Common Failure Modes:**
- Non-convex preferences: optimizer converges to local maximum, not global. Mitigation: test multiple initial guesses, verify Hessian negative semi-definite.
- Corner solutions: zero consumption of a good when $\frac{\partial U / \partial x_i}{p_i} < \lambda$ at boundary. Check complementary slackness conditions.
- Finite-difference step size: too large causes discretization error, too small causes numerical cancellation. Use adaptive step sizes or automatic differentiation.

**Parameter Sensitivity:**
- Income elasticity $\eta_i = \frac{\partial x_i}{\partial m} \frac{m}{x_i}$: necessities have $\eta < 1$, luxuries $\eta > 1$, inferior goods $\eta < 0$.
- Own-price elasticity $\epsilon_{ii} = \frac{\partial x_i}{\partial p_i} \frac{p_i}{x_i}$: always negative by law of demand (exceptions: Giffen goods, which require strong income effects overwhelming substitution).
- Cross-price elasticity $\epsilon_{ij} = \frac{\partial x_i}{\partial p_j} \frac{p_j}{x_i}$: positive for substitutes, negative for complements.

### Production Function Estimation

**Verification Checklist:**
- Returns to scale test: $\hat{\alpha} + \hat{\beta} = 1$ (constant), $> 1$ (increasing), $< 1$ (decreasing). Wald test $p$-value threshold 0.05.
- Fixed effects vs. OLS comparison: if fixed-effects coefficients differ substantially, unobserved heterogeneity (firm-specific productivity) biases OLS.
- Translog flexibility: reject Cobb-Douglas restriction if translog second-order terms jointly significant (F-test $p < 0.05$).
- Residual diagnostics: plot residuals vs. fitted values to detect heteroskedasticity, run Breusch-Pagan test.

**Common Failure Modes:**
- Simultaneity bias: output and inputs jointly determined, violating exogeneity. Mitigation: instrumental variables (lagged inputs, cost shifters), control function approach.
- Measurement error: book value of capital poorly proxies productive capital stock. Use perpetual inventory method to construct capital series.
- Selection bias: sample excludes exiting firms (survivors), upward-biasing productivity estimates. Correct via Heckman selection model.

**Parameter Sensitivity:**
- Capital elasticity $\hat{\alpha}$ typically ranges 0.2–0.4 in U.S. manufacturing. Values outside this range warrant scrutiny.
- Labor elasticity $\hat{\beta}$ typically 0.6–0.8. Low estimates suggest labor hoarding or measurement error in hours worked.

### Competitive Equilibrium Simulation

**Verification Checklist:**
- Market clearing: excess demand for all goods within tolerance ($< 10^{-6}$).
- Walras' Law: if $n-1$ markets clear, $n$-th market clears by construction. Verify numerically.
- MRS equalization: $\text{MRS}^i = \text{MRS}^j = p_1 / p_2$ for all agents at equilibrium (Pareto efficiency).
- Budget exhaustion: $p_1 x_1^i + p_2 x_2^i = p_1 \omega_1^i + p_2 \omega_2^i$ for all agents.

**Common Failure Modes:**
- Multiple equilibria: non-convex production sets or preferences yield non-unique equilibria. Document all equilibria found via different initial guesses.
- Boundary equilibria: equilibrium prices hit zero or infinity, indicating extreme scarcity or abundance. Check for degenerate endowments.
- Cycling: excess demand function does not satisfy gross substitutability, causing oscillatory behavior in tatonnement. Use Newton's method for global convergence.

**Parameter Sensitivity:**
- Equilibrium price highly sensitive to endowment distribution when goods are poor substitutes (low elasticity of substitution).
- Income effects dominate substitution effects when preference parameters $\alpha$ close to 0 or 1, yielding large price responses.

### Externality and Pigouvian Taxation

**Verification Checklist:**
- Pigouvian tax rate: $t^* = \text{MEC}(Q^{\text{opt}})$. Tax-inclusive equilibrium quantity equals social optimum ($|Q_{\text{tax}} - Q^{\text{opt}}| < 10^{-3}$).
- Deadweight loss: area between SMC and demand curves from $Q^{\text{opt}}$ to $Q^*$. Numerical integration error $< 10^{-2}$.
- Revenue-recycling: tax revenue $= t^* \times Q^{\text{opt}}$. Use for lump-sum transfers to restore budget balance.

**Common Failure Modes:**
- Non-constant MEC: if marginal external cost varies non-linearly with quantity, optimal tax is quantity-dependent (first-best Pigouvian tax becomes second-best).
- General equilibrium feedbacks: taxing one sector shifts demand to substitutes, generating externalities elsewhere. Partial equilibrium analysis underestimates required tax.
- Political economy constraints: optimal tax may be politically infeasible. Model second-best policies (quotas, standards).

### Asymmetric Information and Adverse Selection

**Verification Checklist:**
- Incentive compatibility: high-risk types prefer high-coverage contract to low-coverage. Slack in constraint $\geq 0$.
- Participation constraint: low-risk types accept low-coverage contract over self-insurance. Slack $\geq 0$.
- Market unraveling: if pooling premium exceeds low-risk willingness-to-pay, pool collapses. Verify iteratively.

**Common Failure Modes:**
- No separating equilibrium: when risk types too similar, no contract menu screens types. Pooling equilibrium Pareto-dominates separation.
- Cream-skimming: entrant insurers offer contracts targeting only low-risk types, destabilizing pooling equilibrium. Model as dynamic game.
- Moral hazard confound: ex-post behavior (effort) also unobserved, complicating identification of adverse selection vs. moral hazard.

**Parameter Sensitivity:**
- Risk aversion coefficient: more risk-averse consumers value insurance more, raising willingness-to-pay and stabilizing separating equilibria.
- Loss probability spread $\pi_H - \pi_L$: large spread makes screening easier (incentive compatibility constraint less binding).

### Software and Reproducibility Notes

All numerical exercises use open-source software: Python 3.9+ (NumPy 1.21+, SciPy 1.7+, Pandas 1.3+, Statsmodels 0.13+, Matplotlib 3.4+), R 4.0+ (systemfit 1.1+, AER 1.2+, micEcon 0.6+), and standard spreadsheet applications. Random seed control (`np.random.seed(42)`) ensures reproducibility. Solver tolerance settings: `tol=1e-8` for SLSQP, `xtol=1e-6` for nonlinear root-finding. Document optimizer exit codes: 0=success, 1=max iterations, 2=step size below tolerance.

For large-scale simulations (>10,000 agents), parallelize using `multiprocessing` in Python or `foreach` with `doParallel` in R. Profile bottlenecks with `cProfile` (Python) or `Rprof` (R). Store results in HDF5 format (`h5py` in Python, `rhdf5` in R) for efficient I/O.

Version-control analytical code with Git, tagging releases corresponding to specific results. Archive datasets with DOI references (Zenodo, Dataverse). Include computational environment specifications (`requirements.txt`, `sessionInfo()`) in reproducibility archives.
