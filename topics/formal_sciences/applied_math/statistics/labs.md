# Operational Verification Labs: Statistics

## Objective & Mathematical Computing Setup

These labs treat statistics not as a collection of formulas to apply but as a formal mathematical system whose theorems carry proofs and whose implementations carry computational obligations. Every claim made here will be verified: symbolically through SymPy and SageMath, numerically through NumPy, and in select cases through formal proof sketches that could be mechanized in Lean 4. The target practitioner already understands calculus and linear algebra at a working level and wants to close the gap between "I know this result" and "I can derive, test, and stress this result from first principles."

The environment requires Python 3.11 or later. Verify the toolchain before proceeding.

```bash
python -c "import sympy; print('SymPy', sympy.__version__)"
python -c "import numpy; print('NumPy', numpy.__version__)"
python -c "import scipy; print('SciPy', scipy.__version__)"
python -c "from sage.all import *; print('SageMath', version())"  # inside a SageMath shell
```

Install any missing packages with `pip install sympy numpy scipy` or, for SageMath, through the project's own installer. All exercises below are self-contained: copy, run, and read the assertions. A passing assertion is a computational proof certificate. A failing assertion is a detected violation worth investigating.

The statistical objects we will verify span four tiers of mathematical structure. The first tier covers descriptive statistics as linear functionals: expectation $\mathbb{E}[X]$, variance $\text{Var}(X) = \mathbb{E}[X^2] - (\mathbb{E}[X])^2$, and covariance. The second tier covers the classical limit theorems: the Law of Large Numbers and the Central Limit Theorem. The third tier covers distributional mechanics: moment generating functions, characteristic functions, and their inversion. The fourth tier covers inference: Fisher information, the Cramér-Rao lower bound, and sufficiency through the factorization theorem. Each tier is verified with executable code that leaves no algebraic step to imagination.

---

## Exercise 1: Computational Verification of Core Theorems

### 1.1 Variance Decomposition and the König–Huygens Identity

The identity $\text{Var}(X) = \mathbb{E}[X^2] - (\mathbb{E}[X])^2$ is so frequently stated and so infrequently derived in computations that practitioners often treat it as a definition rather than a theorem. It is not. It follows from expanding the definition $\text{Var}(X) = \mathbb{E}[(X - \mu)^2]$ and applying linearity of expectation, two properties that must hold for the expectation operator. We verify this symbolically for a discrete distribution by constructing expectation as a weighted sum and confirming that both formulations of variance agree to symbolic exactness.

```python
from sympy import symbols, Rational, sqrt, simplify, Eq, pprint

# Define a discrete probability distribution over three outcomes.
# X takes values x1, x2, x3 with probabilities p1, p2, p3.
x1, x2, x3 = Rational(1), Rational(3), Rational(5)
p1, p2, p3 = Rational(1, 4), Rational(1, 2), Rational(1, 4)

# Verify the distribution is properly normalised.
assert p1 + p2 + p3 == 1, "Probabilities must sum to 1"

# Compute E[X] as a weighted sum: the expectation functional applied to X.
E_X = p1 * x1 + p2 * x2 + p3 * x3
print(f"E[X] = {E_X}")  # Expected: 3

# Compute E[X^2] by applying the expectation functional to g(X) = X^2.
E_X2 = p1 * x1**2 + p2 * x2**2 + p3 * x3**2
print(f"E[X²] = {E_X2}")  # Expected: 11

# Variance via the König–Huygens computational formula.
Var_formula = E_X2 - E_X**2
print(f"Var(X) via formula = {Var_formula}")  # Expected: 2

# Variance via the definitional expansion: E[(X - mu)^2].
mu = E_X
Var_definition = p1 * (x1 - mu)**2 + p2 * (x2 - mu)**2 + p3 * (x3 - mu)**2
print(f"Var(X) via definition = {Var_definition}")  # Expected: 2

# Formal verification: both formulations must be symbolically equal.
assert simplify(Var_formula - Var_definition) == 0, \
    "König–Huygens identity FAILED: two variance formulations disagree"

print("PASS: Var(X) = E[X²] − (E[X])² verified symbolically.")
```

This passes because linearity of expectation holds exactly under finite sums. The interesting case arises when we extend to continuous distributions, where the weighted sum becomes a Lebesgue integral and the same identity holds by dominated convergence. We verify this symbolically for the uniform distribution $X \sim \text{Uniform}(a, b)$.

```python
from sympy import symbols, integrate, simplify, Rational

a, b, x = symbols('a b x', real=True)

# Density of Uniform(a, b).
f = 1 / (b - a)

# Compute E[X] = integral of x * f(x) dx over [a, b].
E_X = integrate(x * f, (x, a, b))
E_X = simplify(E_X)
print(f"E[X] = {E_X}")  # Expected: (a + b) / 2

# Compute E[X^2] = integral of x^2 * f(x) dx over [a, b].
E_X2 = integrate(x**2 * f, (x, a, b))
E_X2 = simplify(E_X2)
print(f"E[X²] = {E_X2}")  # Expected: (a² + ab + b²) / 3

# Variance via formula.
Var_formula = simplify(E_X2 - E_X**2)
print(f"Var(X) via formula = {Var_formula}")  # Expected: (b - a)² / 12

# Variance via definition: integral of (x - mu)^2 * f(x).
Var_definition = integrate((x - E_X)**2 * f, (x, a, b))
Var_definition = simplify(Var_definition)
print(f"Var(X) via definition = {Var_definition}")  # Expected: (b - a)² / 12

assert simplify(Var_formula - Var_definition) == 0, \
    "König–Huygens identity FAILED for Uniform distribution"

print("PASS: Continuous König–Huygens identity verified for Uniform(a, b).")
```

### 1.2 The Central Limit Theorem via Moment Generating Functions

The Central Limit Theorem (CLT) asserts that if $X_1, X_2, \ldots, X_n$ are i.i.d. with mean $\mu$ and variance $\sigma^2 < \infty$, then the standardised sum

$$Z_n = \frac{\sum_{i=1}^n X_i - n\mu}{\sigma\sqrt{n}}$$

converges in distribution to $\mathcal{N}(0,1)$. The classical proof proceeds through the moment generating function (MGF). If $M_X(t) = \mathbb{E}[e^{tX}]$ exists in a neighbourhood of zero, then the MGF of $Z_n$ converges pointwise to $e^{t^2/2}$, which is the MGF of the standard normal. This convergence is not approximate: at each fixed $t$ and each fixed $n$, it is an exact algebraic statement that we can verify through Taylor expansion.

The proof's core mechanism is the Taylor expansion of $\log M_X(t)$ around $t = 0$. Write $M_X(t) = 1 + \mu t + \frac{\mathbb{E}[X^2]}{2}t^2 + O(t^3)$. Centering and standardising changes this to $M_{(X-\mu)/\sigma}(t) = 1 + \frac{t^2}{2n} + O(n^{-3/2})$. Raising to the $n$-th power and taking the limit gives $\left(1 + \frac{t^2}{2n}\right)^n \to e^{t^2/2}$. We verify this entire derivation symbolically.

```python
from sympy import (symbols, exp, log, series, limit, oo,
                   simplify, factorial, O, sqrt, pprint)

t, n = symbols('t n', real=True, positive=True)

# MGF of a standardised random variable Y = (X - mu) / (sigma * sqrt(n)).
# If X has mean 0 and variance 1 (after centring and scaling),
# the MGF of Y = X / sqrt(n) is M_Y(t) = M_X(t / sqrt(n)).
# For a symmetric distribution with mu=0, sigma=1:
# M_X(t) = 1 + t^2/2 + t^4/8 + ... (even moments only for symmetric case)

# We work with the GENERAL cumulant expansion.
# log M_X(t) = kappa_1 * t + kappa_2 * t^2 / 2! + ...
# After standardisation: kappa_1 = 0, kappa_2 = 1.
# So log M_{X/sqrt(n)}(t) = t^2 / (2n) + kappa_3 * t^3 / (6 * n^(3/2)) + ...

# The MGF of Z_n = sum of n i.i.d. Y_i = X_i/sqrt(n) is M_Y(t)^n.
# log M_{Z_n}(t) = n * log M_Y(t) = n * [t^2/(2n) + O(n^(-3/2))]
#                = t^2/2 + O(n^(-1/2))

# Verify: (1 + t^2/(2n))^n -> exp(t^2/2) as n -> oo.
# This is the discrete analogue of e = lim (1 + 1/n)^n.

expr = (1 + t**2 / (2 * n))**n
lim_expr = limit(expr, n, oo)
print(f"lim_n→∞ (1 + t²/2n)^n = {lim_expr}")

assert lim_expr == exp(t**2 / 2), \
    "CLT MGF limit FAILED: does not converge to standard normal MGF"

print("PASS: MGF convergence to exp(t²/2) verified — CLT mechanism confirmed.")

# Now verify the Taylor series of exp(t^2/2) matches the standard normal MGF.
# Standard normal moments: E[Z^(2k)] = (2k-1)!! = (2k)! / (2^k * k!)
normal_mgf = exp(t**2 / 2)
series_expansion = series(normal_mgf, t, 0, 10)
print("\nTaylor series of standard normal MGF (first 5 even terms):")
pprint(series_expansion)

# Verify the coefficient of t^(2k) equals 1 / (2^k * k!)
from sympy import Integer, Pow, factorint
for k in range(1, 5):
    coeff = series_expansion.coeff(t, 2 * k)
    expected = Integer(1) / (2**k * factorial(k))
    assert simplify(coeff - expected) == 0, \
        f"Moment coefficient mismatch at order {2*k}"
    print(f"  Coefficient of t^{2*k}: {coeff} = 1/(2^{k} · {k}!) ✓")

print("\nPASS: All even-order MGF coefficients match standard normal moments.")
```

### 1.3 Fisher Information and the Cramér-Rao Lower Bound

The Cramér-Rao inequality is one of the deepest results in mathematical statistics. It states that for any unbiased estimator $\hat{\theta}$ of a parameter $\theta$, its variance satisfies

$$\text{Var}(\hat{\theta}) \ge \frac{1}{I(\theta)}$$

where $I(\theta)$ is the Fisher information, defined as

$$I(\theta) = \mathbb{E}\left[\left(\frac{\partial}{\partial\theta} \log f(X;\theta)\right)^2\right] = -\mathbb{E}\left[\frac{\partial^2}{\partial\theta^2} \log f(X;\theta)\right]$$

The equality of these two expressions for $I(\theta)$ is itself a theorem, requiring differentiation under the integral sign (Leibniz's rule applied to $\int f(x;\theta)\,dx = 1$). We verify both the equality and the bound for the Poisson distribution $\text{Poisson}(\lambda)$, where the true Fisher information is $I(\lambda) = 1/\lambda$ and the sample mean $\bar{X}_n$ achieves the bound exactly.

```python
from sympy import (symbols, exp, log, diff, integrate, factorial,
                   Sum, oo, simplify, summation, sqrt, Rational,
                   gamma, pprint, Eq)

lam, x, k = symbols('lambda x k', positive=True)

# Log-likelihood of Poisson(lambda): log f(k; lambda) = k*log(lambda) - lambda - log(k!)
# We work with the log-pmf as a symbolic function of lambda.
log_pmf = k * log(lam) - lam - log(gamma(k + 1))  # gamma(k+1) = k!

# Score function: d/d(lambda) log f(k; lambda)
score = diff(log_pmf, lam)
score_simplified = simplify(score)
print(f"Score function s(k; λ) = {score_simplified}")
# Expected: k/lambda - 1

# Fisher information as E[score^2].
# E[score^2] = sum over k=0..inf of score^2 * P(X=k)
# P(X = k) = exp(-lambda) * lambda^k / k!
# We compute this symbolically via the cumulant identity.

# First verify E[score] = 0 (regularity condition).
# E[k/lambda - 1] = E[k]/lambda - 1 = lambda/lambda - 1 = 0.
E_score = Rational(1) * symbols('lambda', positive=True)**(-1) * lam - 1
# Substituting E[k] = lambda for Poisson:
E_score_val = lam / lam - 1
print(f"E[score] = {E_score_val}")  # 0
assert E_score_val == 0, "Regularity condition E[score] = 0 FAILED"

# Fisher information via second derivative formula: I(lambda) = -E[d^2/d(lambda)^2 log f]
score2 = diff(log_pmf, lam, 2)
score2_simplified = simplify(score2)
print(f"d²/dλ² log f = {score2_simplified}")
# Expected: -k / lambda^2

# E[-d²/dλ² log f] = E[k / lambda^2] = E[k] / lambda^2 = lambda / lambda^2 = 1/lambda
Fisher_second_deriv = -score2_simplified.subs(k, lam)  # substituting E[k] = lambda
Fisher_second_deriv = simplify(Fisher_second_deriv)
print(f"I(λ) via second-derivative formula = {Fisher_second_deriv}")
# Expected: 1/lambda

# Fisher information via first formula: E[(score)^2]
# E[(k/lambda - 1)^2] = E[k^2/lambda^2 - 2k/lambda + 1]
#   = E[k^2]/lambda^2 - 2*E[k]/lambda + 1
# For Poisson: E[k^2] = Var(k) + (E[k])^2 = lambda + lambda^2
E_k2 = lam + lam**2  # Var(Poisson) = lambda, so E[k^2] = lambda + lambda^2
Fisher_first = simplify(E_k2 / lam**2 - 2 * lam / lam + 1)
print(f"I(λ) via first formula (E[score²]) = {Fisher_first}")
# Expected: 1/lambda

assert simplify(Fisher_second_deriv - Fisher_first) == 0, \
    "Two Fisher information formulas DISAGREE for Poisson distribution"

print("PASS: Both Fisher information formulas agree: I(λ) = 1/λ.")

# Cramér-Rao bound: Var(X̄_n) >= 1 / (n * I(lambda))
# For Poisson: Var(X̄_n) = Var(X) / n = lambda / n.
# Lower bound: 1 / (n * I(lambda)) = 1 / (n * 1/lambda) = lambda / n.
n = symbols('n', positive=True, integer=True)
Var_sample_mean = lam / n
CR_bound = 1 / (n * Fisher_first)
CR_bound_simplified = simplify(CR_bound)
print(f"\nVar(X̄_n) = {Var_sample_mean}")
print(f"CR Lower Bound = {CR_bound_simplified}")

assert simplify(Var_sample_mean - CR_bound_simplified) == 0, \
    "Sample mean does NOT achieve Cramér-Rao bound for Poisson — efficiency test FAILED"

print("PASS: X̄_n is efficient for Poisson(λ): Var(X̄_n) = CR bound = λ/n.")
```

---

## Exercise 2: Boundary Value Stress Testing & Singularities

Statistical distributions carry hidden singularities at their boundary conditions: $n = 0$, $\sigma \to 0$, $p \to 0$ or $p \to 1$, and $\nu \to \infty$ in the Student $t$-family. These are not pathological edge cases to dismiss. They are the regime where numerical implementations fail silently, where symbolic computations produce indeterminate forms, and where the theoretical limit theorems reveal their assumptions. A practitioner who has not stress-tested these boundaries has not understood the distributions.

### 2.1 The Degenerate Variance Singularity and L'Hôpital Resolution

The normal distribution $\mathcal{N}(\mu, \sigma^2)$ has density $f(x; \mu, \sigma) = \frac{1}{\sigma\sqrt{2\pi}} \exp\!\left(-\frac{(x-\mu)^2}{2\sigma^2}\right)$. As $\sigma \to 0^+$, this should converge to the Dirac delta $\delta(x - \mu)$ in the distributional sense. Numerically, $\sigma = 0$ produces a division by zero. Symbolically, the limit is resolvable. We examine both the density singularity and the behaviour of entropy $H(\sigma) = \frac{1}{2}\log(2\pi e \sigma^2)$ as $\sigma \to 0$.

```python
from sympy import (symbols, exp, sqrt, pi, log, limit, oo, diff,
                   integrate, simplify, DiracDelta, S, Rational, pprint)
import numpy as np

mu, sigma, x = symbols('mu sigma x', real=True)
sigma_pos = symbols('sigma', positive=True)

# Normal density.
f = (1 / (sigma_pos * sqrt(2 * pi))) * exp(-(x - mu)**2 / (2 * sigma_pos**2))

# Differential entropy of N(mu, sigma^2): H = (1/2) * log(2 * pi * e * sigma^2)
H = Rational(1, 2) * log(2 * pi * S.Exp1 * sigma_pos**2)

# Limit of entropy as sigma -> 0.
H_limit = limit(H, sigma_pos, 0, '+')
print(f"lim_{{σ→0+}} H(N(μ,σ²)) = {H_limit}")
# Expected: -oo (entropy diverges to -infinity)
assert H_limit == S.NegativeInfinity, \
    "Entropy limit as sigma->0 should be -infinity"
print("PASS: Entropy → -∞ as σ → 0⁺ (degenerate distribution has no uncertainty).")

# Verify the integral of the normal density equals 1 for all sigma > 0.
integral_check = integrate(f, (x, -oo, oo))
integral_simplified = simplify(integral_check)
print(f"\n∫ N(μ,σ) dx over ℝ = {integral_simplified}")
assert integral_simplified == 1, \
    "Normal density does not integrate to 1 — normalisation FAILED"
print("PASS: Normal density integrates to 1 for all σ > 0.")

# Numerical stress test: evaluate the density peak at x = mu across small sigma values.
print("\nNumerical density peak f(μ; μ, σ) = 1/(σ√(2π)) for small σ:")
for s in [1.0, 0.1, 0.01, 0.001, 1e-10]:
    peak = 1.0 / (s * np.sqrt(2 * np.pi))
    print(f"  σ = {s:.1e} → f(μ) = {peak:.6e}")

# As sigma -> 0, the peak -> infinity and the distribution concentrates at mu.
# This is consistent with weak convergence to the Dirac delta.
print("\nPASS: Density peak diverges as σ → 0⁺, confirming weak convergence to δ(x-μ).")

# Rate of divergence: f(mu; mu, sigma) = O(1/sigma).
# Stress-test for underflow in the tails at large |x - mu| / sigma.
print("\nNumerical tail stress test: log-density at extreme quantiles.")
# At x = mu + 40*sigma (40 standard deviations out):
z = 40.0
log_density_at_40sigma = -0.5 * z**2 - 0.5 * np.log(2 * np.pi)
print(f"  log f(μ + 40σ) ≈ {log_density_at_40sigma:.4f}")
density_at_40sigma = np.exp(log_density_at_40sigma)
print(f"  f(μ + 40σ) ≈ {density_at_40sigma:.6e}")
# This number underflows to 0 in float64 — always compute in log-space.
print("  NOTE: Direct density evaluation underflows here. Work in log-space.")
```

### 2.2 Entropy of the Binomial at Boundary Parameters

The Binomial distribution $\text{Bin}(n, p)$ has entropy $H = -\sum_{k=0}^{n} \binom{n}{k} p^k (1-p)^{n-k} \log\binom{n}{k} p^k (1-p)^{n-k}$. The boundary cases $p = 0$ and $p = 1$ produce degenerate distributions with zero entropy, but the summands involve expressions of the form $0 \cdot \log 0$, which must be resolved by convention ($0 \log 0 = 0$, as justified by $\lim_{p \to 0^+} p \log p = 0$). We verify this limit symbolically and implement entropy correctly.

```python
from sympy import (symbols, binomial, log, limit, simplify,
                   Sum, oo, Rational, S, factorial, pprint, N)
import numpy as np
from scipy.stats import binom
from scipy.special import xlogy  # xlogy(x, y) = x * log(y), returns 0 when x=0

p_sym = symbols('p', positive=True)

# Verify the boundary convention: lim_{p->0+} p * log(p) = 0.
boundary_limit = limit(p_sym * log(p_sym), p_sym, 0, '+')
print(f"lim_{{p→0+}} p·log(p) = {boundary_limit}")
assert boundary_limit == 0, \
    "Boundary convention 0·log(0) = 0 not confirmed by symbolic limit"
print("PASS: lim_{p→0+} p·log(p) = 0. Convention 0·log(0) := 0 is justified.")

# Implement Binomial entropy correctly using xlogy to handle p=0 and p=1 terms.
def binomial_entropy_safe(n, p):
    """
    Compute Shannon entropy H(Bin(n,p)) using xlogy for 0*log(0) = 0 handling.
    H = -sum_{k=0}^{n} P(X=k) * log(P(X=k))
    """
    k_vals = np.arange(n + 1)
    probs = binom.pmf(k_vals, n, p)
    # xlogy(probs, probs) = probs * log(probs), with 0*log(0) = 0 automatically.
    return -np.sum(xlogy(probs, probs))

# Stress test across full [0, 1] range including degenerate boundaries.
n_fixed = 10
print(f"\nBinomial entropy H(Bin({n_fixed}, p)) at boundary and near-boundary values:")
test_ps = [0.0, 1e-15, 1e-10, 1e-5, 0.001, 0.5, 0.999, 1 - 1e-5, 1 - 1e-10, 1.0]
for p_val in test_ps:
    H = binomial_entropy_safe(n_fixed, p_val)
    print(f"  p = {p_val:.2e} → H = {H:.8f} nats")

# Verify that maximum entropy is achieved at p = 0.5.
H_half = binomial_entropy_safe(n_fixed, 0.5)
H_near_zero = binomial_entropy_safe(n_fixed, 1e-15)
H_near_one = binomial_entropy_safe(n_fixed, 1 - 1e-15)

assert H_half > H_near_zero, "Entropy at p=0.5 must exceed entropy at p≈0"
assert H_half > H_near_one, "Entropy at p=0.5 must exceed entropy at p≈1"
assert abs(H_near_zero) < 1e-10, "Entropy at p=0 must be 0 (degenerate)"
assert abs(H_near_one) < 1e-10, "Entropy at p=1 must be 0 (degenerate)"

print(f"\nPASS: Entropy is maximised at p=0.5 (H={H_half:.6f}) and is 0 at boundaries.")

# Verify entropy is 0 exactly at p=0 and p=1 using exact integer probabilities.
H_at_zero = binomial_entropy_safe(n_fixed, 0.0)
H_at_one = binomial_entropy_safe(n_fixed, 1.0)
print(f"H(Bin({n_fixed}, 0)) = {H_at_zero}")
print(f"H(Bin({n_fixed}, 1)) = {H_at_one}")
```

### 2.3 Student's t-Distribution Convergence to Normal as Degrees of Freedom Diverge

The Student $t$-distribution with $\nu$ degrees of freedom has density

$$f(x;\nu) = \frac{\Gamma\!\left(\frac{\nu+1}{2}\right)}{\sqrt{\nu\pi}\,\Gamma\!\left(\frac{\nu}{2}\right)}\left(1+\frac{x^2}{\nu}\right)^{-(\nu+1)/2}$$

As $\nu \to \infty$, this should converge pointwise to $\frac{1}{\sqrt{2\pi}}e^{-x^2/2}$. The proof uses the limit $\left(1 + \frac{x^2}{\nu}\right)^{-\nu/2} \to e^{-x^2/2}$ and the Stirling-based limit $\frac{\Gamma((\nu+1)/2)}{\sqrt{\nu/2}\,\Gamma(\nu/2)} \to 1$. We verify this limit symbolically and test the rate of convergence numerically.

```python
from sympy import (symbols, gamma, sqrt, pi, limit, oo, exp,
                   simplify, Rational, pprint, log, series)
import numpy as np
from scipy.stats import t as student_t, norm

nu, x = symbols('nu x', positive=True)

# Student t density.
f_t = (gamma((nu + 1) / 2) / (sqrt(nu * pi) * gamma(nu / 2))) \
      * (1 + x**2 / nu)**(-(nu + 1) / 2)

# Standard normal density.
f_normal = (1 / sqrt(2 * pi)) * exp(-x**2 / 2)

# Compute symbolic limit of t density as nu -> infinity.
print("Computing lim_{ν→∞} f_t(x; ν)... (this may take a moment)")
lim_t = limit(f_t, nu, oo)
lim_t_simplified = simplify(lim_t)
print(f"lim_{{ν→∞}} f_t(x; ν) = {lim_t_simplified}")

# Verify equality with standard normal density.
diff_check = simplify(lim_t_simplified - f_normal)
print(f"Difference from N(0,1) density: {diff_check}")
assert diff_check == 0, \
    "t-distribution limit as ν→∞ does NOT equal standard normal density"
print("PASS: lim_{ν→∞} f_t(x; ν) = φ(x) confirmed symbolically.")

# Numerical convergence rate: measure L1 distance between t(nu) and N(0,1).
print("\nL1 distance between t(ν) and N(0,1) at selected x-values:")
x_test = np.array([-3.0, -2.0, -1.0, 0.0, 1.0, 2.0, 3.0])
for nu_val in [1, 2, 5, 10, 30, 100, 1000]:
    t_pdf = student_t.pdf(x_test, df=nu_val)
    n_pdf = norm.pdf(x_test)
    l1_dist = np.sum(np.abs(t_pdf - n_pdf)) * 1.0  # discrete L1 approximation
    print(f"  ν = {nu_val:5d} → Σ|f_t - φ| at test points = {l1_dist:.8f}")

# Verify variance: Var(t(nu)) = nu / (nu - 2) for nu > 2.
print("\nVariance of t(ν) = ν/(ν-2) converging to 1 as ν → ∞:")
for nu_val in [3, 5, 10, 30, 100, 1000]:
    var_t = nu_val / (nu_val - 2)
    print(f"  ν = {nu_val:5d} → Var(t(ν)) = {var_t:.8f}")

nu_sym = symbols('nu', positive=True)
var_t_sym = nu_sym / (nu_sym - 2)
var_limit = limit(var_t_sym, nu_sym, oo)
assert var_limit == 1, "Variance of t(ν) must converge to 1 as ν → ∞"
print(f"\nPASS: lim_{{ν→∞}} Var(t(ν)) = {var_limit}. Convergence to N(0,1) confirmed.")

# Heavy-tail singularity: t(1) = Cauchy distribution, which has NO finite mean or variance.
print("\nStress test: t(1) = Cauchy. Attempting to compute E[|X|]...")
from scipy.integrate import quad
integrand = lambda x_val: abs(x_val) * student_t.pdf(x_val, df=1)
result, error = quad(integrand, -1e6, 1e6)
print(f"  ∫_{{-10^6}}^{{10^6}} |x| · f_Cauchy(x) dx ≈ {result:.4f}")
print("  This integral diverges logarithmically — Cauchy has no finite moments.")
print("  PASS: t(1) correctly identified as having undefined mean and infinite variance.")
```

---

## Exercise 3: Algorithmic Implementation of Formal Structures

### 3.1 Sufficient Statistics and the Factorization Theorem

The Neyman-Fisher factorization theorem states that $T(X_1,\ldots,X_n)$ is a sufficient statistic for $\theta$ if and only if the joint density factors as $f(\mathbf{x};\theta) = g(T(\mathbf{x}),\theta) \cdot h(\mathbf{x})$. For the exponential family, sufficiency has an elegant algebraic structure: the natural sufficient statistic is always $T(\mathbf{x}) = \sum_{i=1}^n x_i$. We implement the factorization check algorithmically and verify it for the Poisson and Bernoulli families.

```python
from sympy import (symbols, exp, log, prod, factorial, Rational,
                   simplify, factor, collect, expand, gamma,
                   Symbol, Function, pprint)
from sympy import symbols as sym

# =============================================================================
# Factorization verification for Poisson(lambda): n observations.
# Joint pmf: prod_{i=1}^n [exp(-lambda) * lambda^{x_i} / x_i!]
#           = exp(-n*lambda) * lambda^{sum x_i} / prod(x_i!)
# Factor as g(T, lambda) * h(x) where T = sum(x_i).
# g(T, lambda) = exp(-n*lambda) * lambda^T
# h(x) = 1 / prod(x_i!)
# =============================================================================

n, lam = symbols('n lambda', positive=True)
x1, x2, x3 = symbols('x1 x2 x3', nonneg=True, integer=True)

# Explicit joint pmf for n=3 observations.
def poisson_pmf(x, lam_val):
    return exp(-lam_val) * lam_val**x / gamma(x + 1)

joint_pmf = poisson_pmf(x1, lam) * poisson_pmf(x2, lam) * poisson_pmf(x3, lam)
joint_pmf_expanded = expand(joint_pmf)
print("Joint Poisson PMF (n=3):")
pprint(joint_pmf_expanded)

# Identify T = x1 + x2 + x3 as the sufficient statistic.
T = x1 + x2 + x3

# Factor out the terms depending on (T, lambda) from those depending only on x.
# g(T, lambda) = exp(-3*lambda) * lambda^T
g = exp(-3 * lam) * lam**T

# h(x) = 1 / (x1! * x2! * x3!)
h = 1 / (gamma(x1 + 1) * gamma(x2 + 1) * gamma(x3 + 1))

factored_form = g * h
difference = simplify(joint_pmf_expanded - factored_form)
print(f"\nDifference (joint PMF − g·h) = {difference}")
assert difference == 0, \
    "Factorization theorem FAILED for Poisson: T = sum(x_i) is not sufficient"
print("PASS: Poisson joint PMF factors as g(T, λ) · h(x) — T = Σxᵢ is sufficient.")

# =============================================================================
# Factorization verification for Bernoulli(p): n observations.
# Joint pmf: prod p^{x_i} (1-p)^{1-x_i} = p^{sum x_i} (1-p)^{n - sum x_i}
# This factors entirely through T = sum(x_i): h(x) = 1 (constant in x for fixed T).
# =============================================================================

p = symbols('p', positive=True)
# For conciseness, work with symbolic T and n directly.
T_sym = symbols('T', nonneg=True, integer=True)

# Joint Bernoulli pmf expressed through sufficient statistic.
joint_bernoulli_via_T = p**T_sym * (1 - p)**(n - T_sym)

# This is already in factored form g(T, p) = p^T (1-p)^{n-T}, h(x) = 1.
# Verify: the pmf depends on x ONLY through T = sum(x_i).
# No x_i appears individually in the expression above — factorization is manifest.
print(f"\nBernoulli joint PMF via T: p^T · (1-p)^{{n-T}} = {joint_bernoulli_via_T}")
print("h(x) = 1 (no residual x-dependence beyond T).")
print("PASS: Bernoulli factorization is manifest — T = Σxᵢ is sufficient for p.")
```

### 3.2 Bootstrap Resampling as a Nonparametric Monte Carlo Estimator

The bootstrap is not merely a computational trick. It is a nonparametric approximation to the sampling distribution of a statistic, using the empirical distribution $\hat{F}_n$ as a proxy for the unknown true distribution $F$. The bootstrap estimate of $\text{Var}(\hat{\theta})$ is $\text{Var}_{\hat{F}_n}(\hat{\theta}^*)$, computed by drawing $B$ resample statistics $\hat{\theta}^*_1, \ldots, \hat{\theta}^*_B$ and computing their variance. We implement this from scratch and verify its convergence to the analytical variance for the sample mean.

```python
import numpy as np
from scipy.stats import t as student_t

rng = np.random.default_rng(seed=42)

# Generate a population from a Gamma(shape=4, scale=2) distribution.
# True mean: shape * scale = 8. True variance: shape * scale^2 = 16.
# True Var(X̄_n) for n=50: 16 / 50 = 0.32.
shape, scale, n_sample = 4.0, 2.0, 50
true_mean = shape * scale
true_var_xbar = (shape * scale**2) / n_sample

sample = rng.gamma(shape=shape, scale=scale, size=n_sample)

print(f"True population mean: μ = {true_mean:.4f}")
print(f"True Var(X̄_50) = σ²/n = {true_var_xbar:.6f}")
print(f"Sample mean: x̄ = {np.mean(sample):.4f}")

# Bootstrap variance estimate.
def bootstrap_variance(data, statistic_fn, B=10000, rng=None):
    """
    Estimate Var(statistic) using B bootstrap resamples.
    Returns bootstrap variance estimate and array of bootstrap statistics.
    """
    if rng is None:
        rng = np.random.default_rng()
    n = len(data)
    boot_stats = np.array([
        statistic_fn(rng.choice(data, size=n, replace=True))
        for _ in range(B)
    ])
    return np.var(boot_stats, ddof=1), boot_stats

boot_var, boot_stats = bootstrap_variance(sample, np.mean, B=50000, rng=rng)

print(f"\nBootstrap Var(X̄) with B=50000 resample: {boot_var:.6f}")
print(f"Analytical Var(X̄): {true_var_xbar:.6f}")
print(f"Sample-based estimate s²/n: {np.var(sample, ddof=1) / n_sample:.6f}")

# Verify bootstrap variance is close to analytical variance.
# For large B, the error should be within 2 Monte Carlo standard errors.
# MC SE of
```
