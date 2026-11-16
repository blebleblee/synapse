# Operational Verification Labs: Applied Statistics

## Objective & Mathematical Computing Setup

Applied statistics transcends theoretical abstraction by grounding probabilistic inference, hypothesis testing, and distributional modeling in computational verification. These operational verification labs target the analytical mathematician and computational practitioner who demands rigorous symbolic proof alongside numerical validation. The exercises herein verify foundational statistical theorems through symbolic algebra engines, stress-test distributional edge cases at boundary values and singularities, and implement formal statistical algorithms with complete computational transparency.

The operational environment integrates Python 3.11 or later with SymPy for symbolic computation, NumPy for numerical array operations, SciPy for statistical distributions and tests, and optionally SageMath for advanced symbolic manipulation or Lean/Coq for mechanized proof verification. The practitioner must establish a computing environment capable of symbolic differentiation, integration, limit evaluation, and matrix operations, as well as pseudorandom number generation with controlled seeds for reproducibility.

Begin by verifying the installation integrity of the primary toolchain. Execute the following diagnostic commands in a terminal session to confirm version compliance and functional imports:

```bash
python3 --version
python3 -c "import sympy; print('SymPy:', sympy.__version__)"
python3 -c "import numpy; print('NumPy:', numpy.__version__)"
python3 -c "import scipy; print('SciPy:', scipy.__version__)"
```

The output should confirm Python 3.11 or higher, SymPy 1.12 or later, NumPy 1.24 or later, and SciPy 1.10 or later. If any component is absent or outdated, install or upgrade using pip:

```bash
pip install --upgrade sympy numpy scipy matplotlib
```

For practitioners who prefer SageMath's integrated symbolic and numerical environment, download and install SageMath 9.8 or later from the official distribution. SageMath bundles Python, SymPy, NumPy, SciPy, and additional mathematical libraries into a cohesive computational algebra system. Launch SageMath via the command `sage` or execute scripts with `sage scriptname.py`.

The verification labs assume familiarity with measure-theoretic probability, parametric and nonparametric inference, and asymptotic theory. Each exercise proceeds from a formal mathematical statement—a theorem, lemma, or distributional property—through symbolic derivation and computational validation. The practitioner verifies claims by symbolic manipulation, numerical simulation, and boundary-case stress testing. This tripartite approach exposes subtle errors in hand-derived proofs, software implementation bugs, and pathological edge cases where formal conditions fail.

## Exercise 1: Computational Verification of Core Theorems

The central limit theorem (CLT) asserts that the standardized sum of independent and identically distributed random variables with finite mean $\mu$ and finite variance $\sigma^2$ converges in distribution to the standard normal distribution $\mathcal{N}(0, 1)$ as the sample size $n \to \infty$. Formally, let $X_1, X_2, \ldots, X_n$ be i.i.d. random variables with $\mathbb{E}[X_i] = \mu$ and $\text{Var}(X_i) = \sigma^2 < \infty$. Define the sample mean $\bar{X}_n = \frac{1}{n} \sum_{i=1}^n X_i$. The CLT states that the standardized sample mean

$$Z_n = \frac{\bar{X}_n - \mu}{\sigma / \sqrt{n}} = \frac{\sqrt{n}(\bar{X}_n - \mu)}{\sigma}$$

converges in distribution to $\mathcal{N}(0, 1)$ as $n \to \infty$. This convergence is denoted $Z_n \xrightarrow{d} \mathcal{N}(0, 1)$.

The first operational verification task establishes the CLT for exponential random variables $X_i \sim \text{Exp}(\lambda)$ with rate parameter $\lambda > 0$. The exponential distribution has mean $\mu = 1/\lambda$ and variance $\sigma^2 = 1/\lambda^2$. The probability density function is $f(x; \lambda) = \lambda e^{-\lambda x}$ for $x \geq 0$ and zero otherwise. The exponential distribution is strongly right-skewed, making it an excellent test case for the CLT, which applies regardless of the underlying distribution's shape provided the variance is finite.

Create a Python script named `clt_verification_exponential.py` with the following complete implementation:

```python
import numpy as np
import scipy.stats as stats
import matplotlib.pyplot as plt

# Set random seed for reproducibility
np.random.seed(42)

# Parameters
lambda_rate = 2.0  # Exponential rate parameter
mu = 1.0 / lambda_rate  # Theoretical mean
sigma = 1.0 / lambda_rate  # Theoretical standard deviation
sample_sizes = [5, 10, 30, 100, 500]
num_simulations = 10000

# Storage for standardized sample means
results = {}

for n in sample_sizes:
    standardized_means = []
    for _ in range(num_simulations):
        # Generate n i.i.d. exponential random variables
        sample = np.random.exponential(scale=1.0/lambda_rate, size=n)
        sample_mean = np.mean(sample)
        # Standardize
        z_n = (sample_mean - mu) / (sigma / np.sqrt(n))
        standardized_means.append(z_n)
    results[n] = np.array(standardized_means)

# Statistical verification: Kolmogorov-Smirnov test against N(0,1)
print("Central Limit Theorem Verification: Exponential Distribution")
print(f"Rate parameter λ = {lambda_rate}")
print(f"Theoretical mean μ = {mu:.4f}, standard deviation σ = {sigma:.4f}")
print(f"Number of simulations per sample size: {num_simulations}\n")

for n in sample_sizes:
    z_values = results[n]
    # Compute sample mean and variance of Z_n
    sample_mean_z = np.mean(z_values)
    sample_var_z = np.var(z_values, ddof=1)
    # Kolmogorov-Smirnov test
    ks_statistic, ks_pvalue = stats.kstest(z_values, 'norm')
    print(f"n = {n:4d} | E[Z_n] = {sample_mean_z:7.4f} | Var(Z_n) = {sample_var_z:7.4f} | "
          f"KS stat = {ks_statistic:.6f} | p-value = {ks_pvalue:.4f}")

# Visual verification: Q-Q plots
fig, axes = plt.subplots(2, 3, figsize=(15, 10))
axes = axes.flatten()

for idx, n in enumerate(sample_sizes):
    ax = axes[idx]
    stats.probplot(results[n], dist="norm", plot=ax)
    ax.set_title(f'Q-Q Plot: n = {n}')
    ax.grid(True, alpha=0.3)

axes[-1].axis('off')  # Hide the last unused subplot
plt.tight_layout()
plt.savefig('clt_verification_exponential_qq.png', dpi=300)
print("\nQ-Q plots saved to 'clt_verification_exponential_qq.png'")

# Histogram overlay with standard normal density
fig, axes = plt.subplots(2, 3, figsize=(15, 10))
axes = axes.flatten()

x_range = np.linspace(-4, 4, 200)
standard_normal_pdf = stats.norm.pdf(x_range, 0, 1)

for idx, n in enumerate(sample_sizes):
    ax = axes[idx]
    ax.hist(results[n], bins=50, density=True, alpha=0.6, color='blue', 
            edgecolor='black', label=f'Empirical (n={n})')
    ax.plot(x_range, standard_normal_pdf, 'r-', linewidth=2, label='N(0,1)')
    ax.set_xlabel('Standardized Sample Mean $Z_n$')
    ax.set_ylabel('Density')
    ax.set_title(f'Convergence to N(0,1): n = {n}')
    ax.legend()
    ax.grid(True, alpha=0.3)

axes[-1].axis('off')
plt.tight_layout()
plt.savefig('clt_verification_exponential_hist.png', dpi=300)
print("Histograms saved to 'clt_verification_exponential_hist.png'")
```

Execute the script with `python3 clt_verification_exponential.py`. The output displays the empirical mean and variance of the standardized sample mean $Z_n$ for increasing sample sizes $n$, alongside the Kolmogorov-Smirnov test statistic and p-value. For small $n$ such as 5, the empirical distribution deviates noticeably from $\mathcal{N}(0, 1)$, reflected in a lower KS p-value and visible departure in the Q-Q plot. As $n$ increases to 30, 100, and 500, the empirical mean approaches zero, the empirical variance approaches one, and the KS p-value increases, indicating failure to reject the null hypothesis that the empirical distribution matches $\mathcal{N}(0, 1)$. The Q-Q plots converge to the diagonal identity line, and the histograms overlay tightly with the standard normal density curve.

The second verification task addresses the law of large numbers (LLN) in both weak and strong forms. The weak law of large numbers (WLLN) states that for i.i.d. random variables $X_1, X_2, \ldots$ with finite mean $\mu$, the sample mean $\bar{X}_n$ converges in probability to $\mu$: for any $\epsilon > 0$,

$$\lim_{n \to \infty} P(|\bar{X}_n - \mu| \geq \epsilon) = 0.$$

The strong law of large numbers (SLLN) asserts almost sure convergence: with probability one,

$$\lim_{n \to \infty} \bar{X}_n = \mu.$$

Verify both laws computationally using the uniform distribution $X_i \sim \text{Uniform}(0, 1)$ with mean $\mu = 1/2$ and variance $\sigma^2 = 1/12$. Create the script `lln_verification_uniform.py`:

```python
import numpy as np
import matplotlib.pyplot as plt

# Set random seed for reproducibility
np.random.seed(123)

# Parameters
mu_true = 0.5  # True mean of Uniform(0,1)
max_n = 10000
num_realizations = 100  # Number of independent sequences for SLLN

# Generate a single long sequence for WLLN demonstration
sequence = np.random.uniform(0, 1, max_n)
cumulative_means = np.cumsum(sequence) / np.arange(1, max_n + 1)

# Generate multiple independent sequences for SLLN demonstration
slln_sequences = np.random.uniform(0, 1, (num_realizations, max_n))
slln_cumulative_means = np.cumsum(slln_sequences, axis=1) / np.arange(1, max_n + 1)

# WLLN verification: convergence in probability
# Check proportion of realizations within epsilon of mu at various n
epsilons = [0.1, 0.05, 0.01]
n_checkpoints = [10, 50, 100, 500, 1000, 5000, 10000]

print("Weak Law of Large Numbers Verification: Uniform(0,1)")
print(f"True mean μ = {mu_true}\n")

for epsilon in epsilons:
    print(f"Epsilon = {epsilon}")
    for n in n_checkpoints:
        deviations = np.abs(slln_cumulative_means[:, n-1] - mu_true)
        proportion_within_epsilon = np.mean(deviations < epsilon)
        print(f"  n = {n:5d} | P(|X̄_n - μ| < ε) ≈ {proportion_within_epsilon:.4f}")
    print()

# SLLN verification: almost sure convergence
print("Strong Law of Large Numbers Verification:")
print(f"Proportion of sequences converging to μ = {mu_true} as n → ∞\n")

# Define convergence as being within 0.01 of mu for the last 1000 observations
convergence_threshold = 0.01
convergence_window = 1000
converged_count = 0

for i in range(num_realizations):
    final_means = slln_cumulative_means[i, -convergence_window:]
    if np.all(np.abs(final_means - mu_true) < convergence_threshold):
        converged_count += 1

proportion_converged = converged_count / num_realizations
print(f"Sequences converged (within {convergence_threshold} for last {convergence_window} obs): "
      f"{converged_count}/{num_realizations} = {proportion_converged:.4f}")

# Visualization
fig, axes = plt.subplots(2, 1, figsize=(14, 10))

# WLLN: Single realization
ax1 = axes[0]
ax1.plot(range(1, max_n + 1), cumulative_means, linewidth=0.8, color='blue')
ax1.axhline(y=mu_true, color='red', linestyle='--', linewidth=2, label=f'True mean μ = {mu_true}')
ax1.set_xlabel('Sample Size n')
ax1.set_ylabel('Cumulative Sample Mean')
ax1.set_title('Weak Law of Large Numbers: Single Realization')
ax1.legend()
ax1.grid(True, alpha=0.3)

# SLLN: Multiple realizations
ax2 = axes[1]
for i in range(min(20, num_realizations)):  # Plot first 20 for clarity
    ax2.plot(range(1, max_n + 1), slln_cumulative_means[i, :], 
             linewidth=0.5, alpha=0.6)
ax2.axhline(y=mu_true, color='red', linestyle='--', linewidth=2, label=f'True mean μ = {mu_true}')
ax2.set_xlabel('Sample Size n')
ax2.set_ylabel('Cumulative Sample Mean')
ax2.set_title(f'Strong Law of Large Numbers: {min(20, num_realizations)} Independent Realizations')
ax2.legend()
ax2.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('lln_verification_uniform.png', dpi=300)
print("\nVisualization saved to 'lln_verification_uniform.png'")
```

Run the script with `python3 lln_verification_uniform.py`. The console output demonstrates that as $n$ increases, the proportion of sample means within $\epsilon$ of $\mu$ approaches unity for all tested $\epsilon$ values, confirming convergence in probability. The SLLN verification shows that nearly all independent sequences converge to $\mu = 0.5$ with high precision, with the proportion approaching one. The visualization displays the progressive tightening of sample means around the true mean as $n$ grows, with oscillations diminishing in amplitude.

The third core theorem is the delta method, which provides asymptotic distribution for functions of estimators. Let $\sqrt{n}(\hat{\theta}_n - \theta) \xrightarrow{d} \mathcal{N}(0, \sigma^2)$ where $\hat{\theta}_n$ is a consistent estimator of parameter $\theta$. For a continuously differentiable function $g$ with $g'(\theta) \neq 0$, the delta method asserts

$$\sqrt{n}(g(\hat{\theta}_n) - g(\theta)) \xrightarrow{d} \mathcal{N}(0, [g'(\theta)]^2 \sigma^2).$$

Verify the delta method symbolically and numerically using SymPy for symbolic differentiation and NumPy for Monte Carlo simulation. Consider $\hat{\theta}_n$ as the sample mean of exponential random variables with rate $\lambda = 1$, so $\theta = 1$ and $\sigma^2 = 1$. Apply the transformation $g(\theta) = 1/\theta$ to obtain the sample harmonic mean. Create `delta_method_verification.py`:

```python
import numpy as np
import sympy as sp
import scipy.stats as stats
import matplotlib.pyplot as plt

# Symbolic derivation of delta method
print("Delta Method Symbolic Verification")
print("=" * 60)

theta = sp.Symbol('theta', positive=True, real=True)
g = 1 / theta
g_prime = sp.diff(g, theta)

print(f"Function: g(θ) = {g}")
print(f"Derivative: g'(θ) = {g_prime}")
print()

# Numerical parameters
theta_true = 1.0  # True parameter (mean of Exp(1))
sigma_squared = 1.0  # Variance of sample mean from Exp(1)
lambda_rate = 1.0 / theta_true

# Evaluate derivative at true parameter
g_prime_val = float(g_prime.subs(theta, theta_true))
asymptotic_variance = (g_prime_val ** 2) * sigma_squared

print(f"True parameter θ = {theta_true}")
print(f"g'(θ) at θ = {theta_true}: {g_prime_val}")
print(f"Asymptotic variance [g'(θ)]² σ² = {asymptotic_variance}")
print()

# Monte Carlo simulation
np.random.seed(456)
n_values = [50, 100, 500, 1000, 5000]
num_simulations = 10000

results_delta = {}

for n in n_values:
    transformed_statistics = []
    for _ in range(num_simulations):
        sample = np.random.exponential(scale=1.0, size=n)
        theta_hat = np.mean(sample)
        g_theta_hat = 1.0 / theta_hat
        # Standardize according to delta method
        standardized = np.sqrt(n) * (g_theta_hat - 1.0/theta_true)
        transformed_statistics.append(standardized)
    results_delta[n] = np.array(transformed_statistics)

# Theoretical distribution under delta method
theoretical_std = np.sqrt(asymptotic_variance)

print("Monte Carlo Verification of Delta Method")
print(f"Theoretical asymptotic distribution: N(0, {asymptotic_variance:.4f})")
print(f"Theoretical standard deviation: {theoretical_std:.4f}\n")

for n in n_values:
    data = results_delta[n]
    empirical_mean = np.mean(data)
    empirical_std = np.std(data, ddof=1)
    # KS test against N(0, asymptotic_variance)
    ks_stat, ks_pval = stats.kstest(data, lambda x: stats.norm.cdf(x, 0, theoretical_std))
    print(f"n = {n:5d} | Mean = {empirical_mean:7.4f} | "
          f"Std = {empirical_std:7.4f} | KS p-value = {ks_pval:.4f}")

# Visualization
fig, axes = plt.subplots(2, 3, figsize=(15, 10))
axes = axes.flatten()

x_range = np.linspace(-6, 6, 300)
theoretical_pdf = stats.norm.pdf(x_range, 0, theoretical_std)

for idx, n in enumerate(n_values):
    ax = axes[idx]
    ax.hist(results_delta[n], bins=60, density=True, alpha=0.6, 
            color='green', edgecolor='black', label=f'Empirical (n={n})')
    ax.plot(x_range, theoretical_pdf, 'r-', linewidth=2, 
            label=f'N(0, {asymptotic_variance:.2f})')
    ax.set_xlabel('Standardized $\sqrt{n}(g(\\hat{\\theta}_n) - g(\\theta))$')
    ax.set_ylabel('Density')
    ax.set_title(f'Delta Method: n = {n}')
    ax.legend()
    ax.grid(True, alpha=0.3)

axes[-1].axis('off')
plt.tight_layout()
plt.savefig('delta_method_verification.png', dpi=300)
print("\nVisualization saved to 'delta_method_verification.png'")
```

Execute with `python3 delta_method_verification.py`. The symbolic output confirms $g'(\theta) = -1/\theta^2$, yielding $g'(1) = -1$ and asymptotic variance $(-1)^2 \cdot 1 = 1$. The Monte Carlo simulations demonstrate convergence of the empirical distribution to $\mathcal{N}(0, 1)$ as $n$ increases, with KS p-values increasing and empirical standard deviations approaching the theoretical value of 1.0. The histograms overlay tightly with the theoretical normal density for large $n$.

## Exercise 2: Boundary Value Stress Testing & Singularities

Statistical distributions exhibit pathological behavior at boundary values, parameter extremes, and singularities where standard asymptotic approximations fail or numerical implementations produce overflow, underflow, or catastrophic cancellation. Stress testing these edge cases exposes implementation fragility and clarifies the domains of validity for statistical procedures.

The first stress test examines the beta distribution $\text{Beta}(\alpha, \beta)$ with shape parameters $\alpha, \beta > 0$. The probability density function is

$$f(x; \alpha, \beta) = \frac{x^{\alpha - 1}(1 - x)^{\beta - 1}}{B(\alpha, \beta)}, \quad 0 \leq x \leq 1,$$

where $B(\alpha, \beta) = \Gamma(\alpha)\Gamma(\beta) / \Gamma(\alpha + \beta)$ is the beta function. The beta distribution exhibits singularities at $x = 0$ when $\alpha < 1$ and at $x = 1$ when $\beta < 1$, with the density approaching infinity as $x$ approaches these boundary points. For $\alpha = \beta = 0.5$, the density explodes at both endpoints. For $\alpha, \beta \to 0^+$, the distribution becomes increasingly pathological. For $\alpha, \beta \to \infty$, the distribution concentrates around its mean $\mu = \alpha / (\alpha + \beta)$ and approaches normality by the CLT.

Create `beta_distribution_stress_test.py` to probe these boundary regimes:

```python
import numpy as np
import scipy.stats as stats
import matplotlib.pyplot as plt
import warnings

warnings.filterwarnings('ignore')  # Suppress overflow warnings for extreme cases

print("Beta Distribution Boundary Value Stress Testing")
print("=" * 70)

# Test parameter configurations
test_cases = [
    (0.1, 0.1, "Extreme singularity at both endpoints"),
    (0.5, 0.5, "U-shaped: singularities at x=0 and x=1"),
    (1.0, 1.0, "Uniform distribution"),
    (2.0, 5.0, "Right-skewed"),
    (5.0, 2.0, "Left-skewed"),
    (50.0, 50.0, "Concentrated near 0.5 (large α, β)"),
    (0.01, 10.0, "Extreme singularity at x=0"),
    (10.0, 0.01, "Extreme singularity at x=1"),
]

# Evaluate density at boundary-proximate points
x_boundary_left = [0.0, 1e-10, 1e-6, 1e-3, 0.01, 0.1]
x_boundary_right = [0.9, 0.99, 0.999, 1.0 - 1e-6, 1.0 - 1e-10, 1.0]

for alpha, beta, description in test_cases:
    print(f"\nα = {alpha}, β = {beta}: {description}")
    beta_dist = stats.beta(alpha, beta)
    
    # Theoretical moments
    mean_theo = alpha / (alpha + beta)
    var_theo = (alpha * beta) / ((alpha + beta)**2 * (alpha + beta + 1))
    
    print(f"  Theoretical mean: {mean_theo:.6f}, variance: {var_theo:.6f}")
    
    # Sample statistics
    sample = beta_dist.rvs(size=100000, random_state=42)
    mean_emp = np.mean(sample)
    var_emp = np.var(sample, ddof=1)
    
    print(f"  Empirical mean:   {mean_emp:.6f}, variance: {var_emp:.6f}")
    
    # Boundary density evaluation
    print(f"  Density near x=0:")
    for x in x_boundary_left[:4]:
        try:
            pdf_val = beta_dist.pdf(x)
            if np.isfinite(pdf_val):
                print(f"    f({x:.2e}) = {pdf_val:.6e}")
            else:
                print(f"    f({x:.2e}) = {pdf_val}")
        except:
            print(f"    f({x:.2e}) = Error")
    
    print(f"  Density near x=1:")
    for x in x_boundary_right[-4:]:
        try:
            pdf_val = beta_dist.pdf(x)
            if np.isfinite(pdf_val):
                print(f"    f({x:.2e}) = {pdf_val:.6e}")
            else:
                print(f"    f({x:.2e}) = {pdf_val}")
        except:
            print(f"    f({x:.2e}) = Error")

# Visualization of pathological cases
fig, axes = plt.subplots(2, 4, figsize=(16, 8))
axes = axes.flatten()

x_plot = np.linspace(0.001, 0.999, 1000)  # Avoid exact 0 and 1

for idx, (alpha, beta, description) in enumerate(test_cases):
    ax = axes[idx]
    beta_dist = stats.beta(alpha, beta)
    
    # Careful PDF evaluation
    pdf_values = []
    for x_val in x_plot:
        try:
            pdf = beta_dist.pdf(x_val)
            if np.isfinite(pdf):
                pdf_values.append(pdf)
            else:
                pdf_values.append(np.nan)
        except:
            pdf_values.append(np.nan)
    
    ax.plot(x_plot, pdf_values, linewidth=1.5, color='darkblue')
    ax.set_xlabel('x')
    ax.set_ylabel('Density')
    ax.set_title(f'α={alpha}, β={beta}', fontsize=9)
    ax.grid(True, alpha=0.3)
    ax.set_xlim(0, 1)
    
    # Set y-axis limit intelligently
    finite_vals = [v for v in pdf_values if np.isfinite(v)]
    if finite_vals:
        y_max = np.percentile(finite_vals, 99)
        ax.set_ylim(0, y_max * 1.1)

plt.tight_layout()
plt.savefig('beta_distribution_stress_test.png', dpi=300)
print("\n" + "=" * 70)
print("Visualization saved to 'beta_distribution_stress_test.png'")
```

Execute with `python3 beta_distribution_stress_test.py`. The output reveals that for $\alpha, \beta < 1$, the density values near the boundaries explode to extremely large finite values or infinity, depending on numerical precision. SciPy's implementation handles these cases with graceful degradation, returning `inf` when the density exceeds floating-point representation. The empirical moments from large samples remain accurate despite the singularities, confirming that integration of the density (implemented via sampling) remains numerically stable. The visualizations show the U-shaped density for $\alpha = \beta = 0.5$, the uniform density for $\alpha = \beta = 1$, and the dramatic concentration for large $\alpha, \beta$.

The second stress test targets the chi-squared distribution $\chi^2_k$ with $k$ degrees of freedom, particularly in the limit $k \to 1^+$ where the density exhibits a singularity at zero. The probability density function for $k$ degrees of freedom is

$$f(x; k) = \frac{1}{2^{k/2} \Gamma(k/2)} x^{k/2 - 1} e^{-x/2}, \quad x > 0.$$

For $k = 1$, the exponent on $x$ is $1/2 - 1 = -1/2$, yielding a singularity at $x = 0$ where $f(x; 1) \sim x^{-1/2} \to \infty$ as $x \to 0^+$. For $k = 2$, the distribution reduces to an exponential distribution with rate $1/2$. For large $k$, the chi-squared distribution approaches normality with mean $k$ and variance $2k$ by the CLT applied to the sum of squared normal random variables.

Create `chisquared_stress_test.py`:

```python
import numpy as np
import scipy.stats as stats
import matplotlib.pyplot as plt

print("Chi-Squared Distribution Stress Testing")
print("=" * 70)

# Test degrees of freedom
df_values = [1, 2, 3, 5, 10, 20, 50, 100]

# Boundary evaluation near x = 0
x_near_zero = [1e-6, 1e-5, 1e-4, 1e-3, 1e-2, 1e-1, 0.5, 1.0]

for df in df_values:
    print(f"\nDegrees of freedom k = {df}")
    chi2_dist = stats.chi2(df)
    
    # Theoretical moments
    mean_theo = df
    var_theo = 2 * df
    
    print(f"  Theoretical: mean = {mean_theo}, variance = {var_theo}")
    
    # Empirical moments
    sample = chi2_dist.rvs(size=100000, random_state=99)
    mean_emp = np.mean(sample)
    var_emp = np.var(sample, ddof=1)
    
    print(f"  Empirical:   mean = {mean_emp:.4f}, variance = {var_emp:.4f}")
    
    # Density near x = 0
    print(f"  Density f(x; k={df}) near x=0:")
    for x in x_near_zero:
        pdf_val = chi2_dist.pdf(x)
        if np.isfinite(pdf_val):
            print(f"    x = {x:.2e}: f(x) = {pdf_val:.6e}")
        else:
            print(f"    x = {x:.2e}: f(x) = {pdf_val}")

# Asymptotic normality test for large k
print("\n" + "=" * 70)
print("Asymptotic Normality Test for Large k")
print("=" * 70)

large_k_values = [30, 50, 100, 200]

for k in large_k_values:
    chi2_dist = stats.chi2(k)
    sample = chi2_dist.rvs(size=10000, random_state=123)
    
    # Standardize
    standardized = (sample - k) / np.sqrt(2 * k)
    
    # KS test against N(0, 1)
    ks_stat, ks_pval = stats.kstest(standardized, 'norm')
    
    print(f"k = {k:3d} | KS statistic = {ks_stat:.6f} | p-value = {ks_pval:.4f}")

# Visualization
fig, axes = plt.subplots(2, 4, figsize=(16, 8))
axes = axes.flatten()

for idx, df in enumerate(df_values):
    ax = axes[idx]
    x_plot = np.linspace(0.001, max(df + 4*np.sqrt(2*df), 10), 500)
    chi2_dist = stats.chi2(df)
    pdf_values = chi2_dist.pdf(x_plot)
    
    ax.plot(x_plot, pdf_values, linewidth=1.5, color='darkred')
    ax.set_xlabel('x')
    ax.set_ylabel('Density')
    ax.set_title(f'χ²({df})')
    ax.grid(True, alpha=0.3)
    
    # Highlight mean
    ax.axvline(x=df, color='blue', linestyle='--', linewidth=1, alpha=0.7, label=f'Mean={df}')
    ax.legend(fontsize=8)

plt.tight_layout()
plt.savefig('chisquared_stress_test.png', dpi=300)
print("\nVisualization saved to 'chisquared_stress_test.png'")
```

Execute with `python3 chisquared_stress_test.py`. The output confirms that for $k = 1$, the density at $x = 10^{-6}$ is approximately $10^3$, increasing as $x \to 0^+$ according to the $x^{-1/2}$ singularity. For $k = 2$, the density at small $x$ remains finite and decreases exponentially. The asymptotic normality test shows that for $k \geq 50$, the standardized chi-squared variable is well-approximated by $\mathcal{N}(0, 1)$ with high KS p-values, confirming failure to reject the null hypothesis of normality.

The third stress test addresses numerical stability in hypothesis testing under extreme parameter regimes. Consider the two-sample $t$-test for equal means with unequal variances (Welch's $t$-test). Given two independent samples $X_1, \ldots, X_{n_1} \sim \mathcal{N}(\mu_1, \sigma_1^2)$ and $Y_1, \ldots, Y_{n_2} \sim \mathcal{N}(\mu_2, \sigma_2^2)$, the test statistic is

$$t = \frac{\bar{X} - \bar{Y}}{\sqrt{\frac{s_1^2}{n_1} + \frac{s_2^2}{n_2}}},$$

where $\bar{X}, \bar{Y}$ are sample means and $s_1^2, s_2^2$ are sample variances. Under the null hypothesis $\mu_1 = \mu_2$, the statistic approximately follows a $t$-distribution with degrees of freedom given by the Welch-Satterthwaite equation:

$$\nu = \frac{\left( \frac{s_1^2}{n_1} + \frac{s_2^2}{n_2} \right)^2}{\frac{(s_1^2/n_1)^2}{n_1 - 1} + \frac{(s_2^2/n_2)^2}{n_2 - 1}}.$$

Stress test this procedure when $\sigma_1 \gg \sigma_2$ or $n_1 \ll n_2$, and when sample variances are nearly zero due to identical observations. Create `welch_ttest_stress.py`:

```python
import numpy as np
import scipy.stats as stats

print("Welch's t-Test Stress Testing Under Extreme Parameter Regimes")
print("=" * 70)

np.random.seed(777)

# Test Case 1: Extreme variance ratio
print("\nTest Case 1: Extreme Variance Ratio σ1 >> σ2")
print("-" * 70)

n1, n2 = 30, 30
mu1, mu2 = 5.0, 5.0  # Null hypothesis true
sigma1, sigma2 = 100.0, 1.0  # Extreme ratio

sample1 = np.random.normal(mu1, sigma1, n1)
sample2 = np.random.normal(mu2, sigma2, n2)

t_stat, p_val = stats.ttest_ind(sample1, sample2, equal_var=False)

print(f"n1 = {n1}, n2 = {n2}, σ1 = {sigma1}, σ2 = {sigma2}")
print(f"Sample means: x̄ = {np.mean(sample1):.4f}, ȳ = {np.mean(sample2):.4f}")
print(f"Sample stds: s1 = {np.std(sample1, ddof=1):.4f}, s2 = {np.std(sample2, ddof=1):.4f}")
print(f"Welch's t-statistic: {t_stat:.6f}")
print(f"p-value: {p_val:.6f}")
print(f"Reject H0 at α=0.05: {p_val < 0.05}")

# Test Case 2: Extreme sample size imbalance
print("\n" + "-" * 70)
print("Test Case 2: Extreme Sample Size Imbalance n1 << n2")
print("-" * 70)

n1, n2 = 5, 500
mu1, mu2 = 10.0, 10.0
sigma1, sigma2 = 2.0, 2.0

sample1 = np.random.normal(mu1, sigma1, n1)
sample2 = np.random.normal(mu2, sigma2, n2)

t_stat, p_val = stats.ttest_ind(sample1, sample2, equal_var=False)

print(f"n1 = {n1}, n2 = {n2}, σ1 = {sigma1}, σ2 = {sigma2}")
print(f"Sample means: x̄ = {np.mean(sample1):.4f}, ȳ = {np.mean(sample2):.4f}")
print(f"Sample stds: s1 = {np.std(sample1, ddof=1):.4f}, s2 = {np.std(sample2, ddof=1):.4f}")
print(f"Welch's t-statistic: {t_stat:.6f}")
print(f"p-value: {p_val:.6f}")
print(f"Reject H0 at α=0.05: {p_val < 0.05}")

# Compute effective degrees of freedom manually
s1_sq = np.var(sample1, ddof=1)
s2_sq = np.var(sample2, ddof=1)
numerator = (s1_sq/n1 + s2_sq/n2)**2
denominator = (s1_sq/n1)**2/(n1-1) + (s2_sq/n2)**2/(n2-1)
df_welch = numerator / denominator
print(f"Welch-Satterthwaite degrees of freedom: {df_welch:.2f}")

# Test Case 3: Near-zero variance (constant observations)
print("\n" + "-" * 70)
print("Test Case 3: Near-Zero Variance (Constant Observations)")
print("-" * 70)

n1, n2 = 20, 20
sample1 = np.full(n1, 5.0)  # All identical
sample2 = np.full(n2, 5.0)  # All identical

# Add tiny noise to avoid exact zero variance
sample1 += np.random.normal(0, 1e-10, n1)
sample2 += np.random.normal(0, 1e-10, n2)

try:
    t_stat, p_val = stats.ttest_ind(sample1, sample2, equal_var=False)
    print(f"Sample means: x̄ = {np.mean(sample1):.10f}, ȳ = {np.mean(sample2):.10f}")
    print(f"Sample stds: s1 = {np.std(sample1, ddof=1):.2e}, s2 = {np.std(sample2, ddof=1):.2e}")
    print(f"Welch's t-statistic: {t_stat:.6f}")
    print(f"p-value: {p_val}")
except Exception as e:
    print(f"Exception raised: {e}")

# Test Case 4: One sample with zero variance
print("\n" + "-" * 70)
print("Test Case 4: One Sample with Exact Zero Variance")
print("-" * 70)

n1, n2 = 20, 20
sample1 = np.full(n1, 5.0)  # All exactly identical
sample2 = np.random.normal(5.0, 1.0, n2)

try:
    t_stat, p_val = stats.ttest_ind(sample1, sample2, equal_var=False)
    print(f"Sample means: x̄ = {np.mean(sample1):.4f}, ȳ = {np.mean(sample2):.4f}")
    print(f"Sample stds: s1 = {np.std(sample1, ddof=1):.2e}, s2 = {np.std(sample2, ddof=1):.4f}")
    print(f"Welch's t-statistic: {t_stat}")
    print(f"p-value: {p_val}")
except Exception as e:
    print(f"Exception raised: {e}")

# Test Case 5: Type I error rate under null hypothesis (Monte Carlo)
print("\n" + "-" * 70)
print("Test Case 5: Type I Error Rate Verification (α = 0.05)")
print("-" * 70)

num_trials = 10000
alpha = 0.05
rejections = 0

for _ in range(num_trials):
    sample1 = np.random.normal(0, 1, 30)
    sample2 = np.random.normal(0, 1, 30)
    _, p_val = stats.ttest_ind(sample1, sample2, equal_var=False)
    if p_val < alpha:
        rejections += 1

empirical_type1_error = rejections / num_trials
print(f"Number of trials: {num_trials}")
print(f"Number of rejections: {rejections}")
print(f"Empirical Type I error rate: {empirical_type1_error:.4f}")
print(f"Expected Type I error rate: {alpha}")
print(f"Difference: {abs(empirical_type1_error - alpha):.4f}")

print("\n" + "=" * 70)
```

Execute with `python3 welch_ttest_stress.py`. The output demonstrates that Welch's $t$-test remains numerically stable under extreme variance ratios and sample size imbalances, correctly failing to reject the null hypothesis when it is true. For near-zero variance cases, SciPy gracefully handles the numerical instability by returning `nan` for the p-value when both samples have identical values, signaling that the test is undefined rather than silently producing incorrect results. The Type I error rate verification confirms that under the null hypothesis with balanced samples, the empirical rejection rate converges to the nominal significance level $\alpha = 0.05$ within Monte Carlo error.

## Exercise 3: Algorithmic Implementation of Formal Structures

Statistical inference relies on formal algorithmic structures including maximum likelihood estimation (MLE), expectation-maximization (EM) algorithms, bootstrap resampling, and permutation tests. Implementing these algorithms from first principles verifies correctness, exposes numerical subtleties, and deepens understanding of the mathematical foundations.

The first implementation task constructs the Newton-Raphson algorithm for maximum likelihood estimation. Given independent observations $x_1, \ldots, x_n$ from a parametric distribution with density $f(x; \theta)$, the log-likelihood function is

$$\ell(\theta) = \sum_{i=1}^n \log f(x_i; \theta).$$

The MLE $\hat{\theta}_{\text{MLE}}$ maximizes $\ell(\theta)$. The Newton-Raphson update iterates

$$\theta^{(t+1)} = \theta^{(t)} - \frac{\ell'(\theta^{(t)})}{\ell''(\theta^{(t)})},$$

where $\ell'(\theta)$ is the score function and $\ell''(\theta)$ is the observed information. For the gamma distribution $\text{Gamma}(k, \theta)$ with known shape $k$ and unknown rate $\theta$, the density is

$$f(x; k, \theta) = \frac{\theta^k}{\Gamma(k)} x^{k-1} e^{-\theta x}, \quad x > 0.$$

The log-likelihood is

$$\ell(\theta) = n k \log \theta - \theta \sum_{i=1}^n x_i + (k-1) \sum_{i=1}^n \log x_i - n \log \Gamma(k).$$

The score function is

$$\ell'(\theta) = \frac{\partial \ell}{\partial \theta} = \frac{nk}{\theta} - \sum_{i=1}^n x_i.$$

The observed information is

$$\ell''(\theta) = \frac{\partial^2 \ell}{\partial \theta^2} = -\frac{nk}{\theta^2}.$$

Setting $\ell'(\theta) = 0$ yields the MLE $\hat{\theta}_{\text{MLE}} = nk / \sum_{i=1}^n x_i = k / \bar{x}$. Implement the Newton-Raphson algorithm with symbolic verification using SymPy. Create `newton_raphson_mle_gamma.py`:

```python
import numpy as np
import sympy as sp
import scipy.stats as stats

print("Newton-Raphson Maximum Likelihood Estimation: Gamma Distribution")
print("=" * 70)

# Symbolic derivation
print("\nSymbolic Derivation")
print("-" * 70)

theta_sym = sp.Symbol('theta', positive=True, real=True)
k_sym = sp.Symbol('k', positive=True, real=True)
n_sym = sp.Symbol('n', positive=True, integer=True)
S_sym = sp.Symbol('S', positive=True, real=True)  # Sum of observations

# Log-likelihood (without constant terms)
log_likelihood = n_sym * k_sym * sp.log(theta_sym) - theta_sym * S_sym

print(f"Log-likelihood: ℓ(θ) = {log_likelihood}")

# Score function
score = sp.diff(log_likelihood, theta_sym)
print(f"Score function: ℓ'(θ) = {score}")

# Observed information (negative second derivative)
obs_info = -sp.diff(score, theta_sym)
print(f"Observed information: -ℓ''(θ) = {obs_info}")

# Analytical MLE
mle_analytical = sp.solve(score, theta_sym)[0]
print(f"Analytical MLE: θ̂ = {mle_analytical}")

# Numerical implementation
print("\n" + "=" * 70)
print("Numerical Implementation")
print("-" * 70)

# Generate synthetic data
np.random.seed(2024)
k_true = 3.0
theta_true = 2.0
n = 200

data = np.random.gamma(shape=k_true, scale=1.0/theta_true, size=n)

print(f"True parameters: k = {k_true}, θ = {theta_true}")
print(f"Sample size: n = {n}")
print(f"Sample mean: {np.mean(data):.6f} (theoretical: {k_true/theta_true:.6f})")

# Newton-Raphson iteration
def log_likelihood_func(theta, k, data):
    n = len(data)
    S = np.sum(data)
    return n * k * np.log(theta) - theta * S

def score_func(theta, k, data):
    n = len(data)
    S = np.sum(data)
    return n * k / theta - S

def obs_info_func(theta, k, data):
    n = len(data)
    return n * k / (theta ** 2)

# Initial guess
theta_init = 1.0
theta_current = theta_init
tolerance = 1e-10
max_iterations = 100

print(f"\nNewton-Raphson Iteration (k fixed at {k_true}):")
print(f"Initial guess: θ⁽⁰⁾ = {theta_init}")
print()

for iteration in range(max_iterations):
    score_val = score_func(theta_current, k_true, data)
    obs_info_val = obs_info_func(theta_current, k_true, data)
    
    # Newton-Raphson update
    theta_next = theta_current + score_val / obs_info_val
    
    # Log-likelihood value
    ll_current = log_likelihood_func(theta_current, k_true, data)
    
    print(f"Iter {iteration:3d}: θ = {theta_current:.10f}, ℓ(θ) = {ll_current:.6f}, "
          f"ℓ'(θ) = {score_val:.6e}")
    
    # Convergence check
    if abs(theta_next - theta_current) < tolerance:
        print(f"\nConverged after {iteration + 1} iterations")
        theta_mle = theta_next
        break
    
    theta_current = theta_next
else:
    print(f"\nWarning: Maximum iterations ({max_iterations}) reached")
    theta_mle = theta_current

print(f"\nMLE estimate: θ̂ = {theta_mle:.10f}")

# Analytical MLE for comparison
theta_mle_analytical = k_true / np.mean(data)
print(f"Analytical MLE: θ̂ = {theta_mle_analytical:.10f}")
print(f"Difference: {abs(theta_mle - theta_mle_analytical):.2e}")

# Fisher information and standard error
fisher_info = obs_info_func(theta_mle, k_true, data)
std_error = 1.0 / np.sqrt(fisher_info)
print(f"\nFisher information: I(θ̂) = {fisher_info:.6f}")
print(f"Standard error: SE(θ̂) = {std_error:.6f}")

# 95% confidence interval (asymptotic normal approximation)
z_critical = 1.96
ci_lower = theta_mle - z_critical * std_error
ci_upper = theta_mle + z_critical * std_error
print(f"95% Confidence Interval: [{ci_lower:.6f}, {ci_upper:.6f}]")
print(f"True θ in CI: {ci_lower <= theta_true <= ci_upper}")

# Verify using SciPy's built-in MLE
print("\n" + "-" * 70)
print("Verification using SciPy's fit method:")
k_fit, loc_fit, scale_fit = stats.gamma.fit(data, floc=0, fa=k_true)
theta_scipy = 1.0 / scale_fit
print(f"SciPy MLE: θ̂ = {theta_scipy:.10f}")
print(f"Difference from manual implementation: {abs(theta_mle - theta_scipy):.2e}")

print("\n" + "=" * 70)
```

Execute with `python3 newton_raphson_mle_gamma.py`. The symbolic output confirms the score function $\ell'(\theta) = nk/\theta - S$ and observed information $-\ell''(\theta) = nk/\theta^2$. The Newton-Raphson iteration converges rapidly in 5-10 iterations to the MLE, matching the analytical solution $\hat{\theta} = k / \bar{x}$ to machine precision. The standard error computed from the Fisher information provides an asymptotic confidence interval that contains the true parameter with the expected coverage probability.

The second algorithmic implementation constructs the expectation-maximization (EM) algorithm for fitting a two-component Gaussian mixture model (GMM). Given observations $x_1, \ldots, x_n$ from a mixture distribution

$$f(x) = \pi_1 \mathcal{N}(x; \mu_1, \sigma_1^2) + \pi_2 \mathcal{N}(x; \mu_2, \sigma_2^2),$$

where $\pi_1 + \pi_2 = 1$ are mixing weights, the EM algorithm iterates between an E-step that computes the posterior probability (responsibility) that observation $x_i$ belongs to component $j$,

$$\gamma_{ij}^{(t)} = \frac{\pi_j^{(t)} \mathcal{N}(x_i; \mu_j^{(t)}, (\sigma_j^{(t)})^2)}{\sum_{k=1}^2 \pi_k^{(t)} \mathcal{N}(x_i; \mu_k^{(t)}, (\sigma_k^{(t)})^2)},$$

and an M-step that updates parameters:

$$\pi_j^{(t+1)} = \frac{1}{n} \sum_{i=1}^n \gamma_{ij}^{(t)},$$

$$\mu_j^{(t+1)} = \frac{\sum_{i=1}^n \gamma_{ij}^{(t)} x_i}{\sum_{i=1}^n \gamma_{ij}^{(t)}},$$

$$(\sigma_j^{(t+1)})^2 = \frac{\sum_{i=1}^n \gamma_{ij}^{(t)} (x_i - \mu_j^{(t+1)})^2}{\sum_{i=1}^n \gamma_{ij}^{(t)}}.$$

The algorithm monotonically increases the log-likelihood at each iteration. Create `em_algorithm_gmm.py`:

```python
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import norm

print("Expectation-Maximization Algorithm: Two-Component Gaussian Mixture")
print("=" * 70)

# Set random seed
np.random.seed(42)

# Generate synthetic data from a two-component mixture
n1, n2 = 150, 100
mu1_true, sigma1_true = -2.0, 1.0
mu2_true, sigma2_true = 3.0, 1.5
pi1_true, pi2_true = n1 / (n1 + n2), n2 / (n1 + n2)

data1 = np.random.normal(mu1_true, sigma1_true, n1)
data2 = np.random.normal(mu2_true, sigma2_true, n2)
data = np.concatenate([data1, data2])
np.random.shuffle(data)

n = len(data)

print(f"True parameters:")
print(f"  Component 1: π1 = {pi1_true:.4f}, μ1 = {mu1_true:.4f}, σ1 = {sigma1_true:.4f}")
print(f"  Component 2: π2 = {pi2_true:.4f}, μ2 = {mu2_true:.4f}, σ2 = {sigma2_true:.4f}")
print(f"Sample size: n = {n}\n")

# Initialize parameters (deliberately poor initialization)
pi1, pi2 = 0.5, 0.5
mu1, mu2 = 0.0, 1.0
sigma1, sigma2 = 1.0, 1.0

# EM algorithm parameters
max_iterations = 100
tolerance = 1e-6

# Storage for tracking
log_likelihoods = []
parameters_history = []

def compute_log_likelihood(data, pi1, mu1, sigma1, pi2, mu2, sigma2):
    """Compute the log-likelihood of the mixture model."""
    component1 = pi1 * norm.pdf(data, mu1, sigma1)
    component2 = pi2 * norm.pdf(data, mu2, sigma2)
    mixture = component1 + component2
    return np.sum(np.log(mixture + 1e-300))  # Add small constant to avoid log(0)

print("EM Algorithm Iteration:")
print("-" * 70)

for iteration in range(max_iterations):
    # E-step: Compute responsibilities
    component1_prob = pi1 * norm.pdf(data, mu1, sigma1)
    component2_prob = pi2 * norm.pdf(data, mu2, sigma2)
    total_prob = component1_prob + component2_prob + 1e-300  # Avoid division by zero
    
    gamma1 = component1_prob / total_prob
    gamma2 = component2_prob / total_prob
    
    # M-step: Update parameters
    n1_effective = np.sum(gamma1)
    n2_effective = np.sum(gamma2)
    
    pi1_new = n1_effective / n
    pi2_new = n2_effective / n
    
    mu1_new = np.sum(gamma1 * data) / n1_effective
    mu2_new = np.sum(gamma2 * data) / n2_effective
    
    sigma1_new = np.sqrt(np.sum(gamma1 * (data - mu1_new)**2) / n1_effective)
    sigma2_new = np.sqrt(np.sum(gamma2 * (data - mu2_new)**2) / n2_effective)
    
    # Compute log-likelihood
    ll = compute_log_likelihood(data, pi1_new, mu1_new, sigma1_new, pi2_new, mu2_new, sigma2_new)
    log_likelihoods.append(ll)
    parameters_history.append((pi1_new, mu1_new, sigma1_new, pi2_new, mu2_new, sigma2_new))
    
    print(f"Iter {iteration:3d}: ℓ = {ll:.4f} | π1={pi1_new:.4f}, μ1={mu1_new:.4f}, σ1={sigma1_new:.4f} | "
          f"π2={pi2_new:.4f}, μ2={mu2_new:.4f}, σ2={sigma2_new:.4f}")
    
    # Check convergence
    if iteration > 0:
        ll_change = log_likelihoods[-1] - log_likelihoods[-2]
        if ll_change < tolerance:
            print(f"\nConverged after {iteration + 1} iterations (Δℓ = {ll_change:.2e})")
            break
    
    # Update parameters for next iteration
    pi1, mu1, sigma1 = pi1_new, mu1_new, sigma1_new
    pi2, mu2, sigma2 = pi2_new, mu2_new, sigma2_new
else:
    print(f"\nMaximum iterations ({max_iterations}) reached")

print("\n" + "=" * 70)
print("Final Estimates vs True Parameters:")
print("-" * 70)
print(f"Component 1:")
print(f"  π1: {pi1:.4f} (true: {pi1_true:.4f})")
print(f"  μ1: {mu1:.4f} (true: {mu1_true:.4f})")
print(f"  σ1: {sigma1:.4f} (true: {sigma1_true:.4f})")
print(f"\nComponent 2:")
print(f"  π2: {pi2:.4f} (true: {pi2_true:.4f})")
print(f"  μ2: {mu2:.4f} (true: {mu2_true:.4f})")
print(f"  σ2: {sigma2:.4f} (true: {sigma2_true:.4f})")

# Visualization
fig, axes = plt.subplots(2, 1, figsize=(12, 10))

# Log-likelihood convergence
ax1 = axes[0]
ax1.plot(range(len(log_likelihoods)), log_likelihoods, 'o-', linewidth=2, markersize=4)
ax1.set_xlabel('Iteration')
ax1.set_ylabel('Log-Likelihood')
ax1.set_title('EM Algorithm Convergence')
ax1.grid(True, alpha=0.3)

# Final mixture model fit
ax2 = axes[1]
ax2.hist(data, bins=40, density=True, alpha=0.5, color='gray', edgecolor='black', label='Data')

x_range = np.linspace(data.min() - 1, data.max() + 1, 500)
component1_final = pi1 * norm.pdf(x_range, mu1, sigma1)
component2_final = pi2 * norm.pdf(x_range, mu2, sigma2)
mixture_final = component1_final + component2_final

ax2.plot(x_range, component1_final, 'b--', linewidth=2, label=f'Component 1 (π={pi1:.2f})')
ax2.plot(x_range, component2_final, 'r--', linewidth=2, label=f'Component 2 (π={pi2:.2f})')
ax2.plot(x_range, mixture_final, 'k-', linewidth=2, label='Mixture')
ax2.set_xlabel('x')
ax2.set_ylabel('Density')
ax2.set_title('Fitted Two-Component Gaussian Mixture Model')
ax2.legend()
ax2.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('em_algorithm_gmm.png', dpi=300)
print("\nVisualization saved to 'em_algorithm_gmm.png'")
print("=" * 70)
```

Execute with `python3 em_algorithm_gmm.py`. The console output displays the monotonically increasing log-likelihood across iterations, confirming the theoretical guarantee that EM never decreases the objective function. The algorithm converges within 20-30 iterations to parameter estimates closely matching the true values, with small deviations due to finite sample size and random initialization. The visualization shows the log-likelihood plateau and the fitted mixture model overlaying the empirical histogram with excellent fidelity. The decomposition into individual components reveals the learned separation between the two underlying Gaussian distributions.

The third algorithmic implementation constructs the nonparametric bootstrap for estimating the sampling distribution of a statistic without parametric assumptions. Given a sample $x_1, \ldots, x_n$, the bootstrap generates $B$ resamples $x_1^*, \ldots, x_n^*$ by sampling with replacement from the original data. For each resample, compute the statistic of interest $\hat{\theta}^*$. The empirical distribution of $\hat{\theta}_1^*, \ldots, \hat{\theta}_B^*$ approximates the sampling distribution of $\hat{\theta}$. Apply bootstrap to estimate the standard error and confidence interval for the sample median, a statistic without a closed-form variance formula. Create `bootstrap_median.py`:

```python
import numpy as np
import matplotlib.pyplot as plt
import scipy.stats as stats

print("Nonparametric Bootstrap: Median Standard Error and Confidence Interval")
print("=" * 70)

# Set random seed
np.random.seed(999)

# Generate data from a skewed distribution (log-normal)
mu_log, sigma_log = 0.0, 0.5
n = 100
data = np.random.lognormal(mu_log, sigma_log, n)

print(f"Sample size: n = {n}")
print(f"Sample median: {np.median(data):.6f}")
print(f"Sample mean: {np.mean(data):.6f}")
print(f"Sample std: {np.std(data, ddof=1):.6f}\n")

# Bootstrap parameters
B = 10000
alpha = 0.05

print(f"Bootstrap resamples: B = {B}")
print(f"Confidence level: {1 - alpha:.0%}\n")

# Bootstrap resampling
bootstrap_medians = np.zeros(B)

for b in range(B):
    resample = np.random.choice(data, size=n, replace=True)
    bootstrap_medians[b] = np.median(resample)

# Bootstrap standard error
bootstrap_se = np.std(bootstrap_medians, ddof=1)
print(f"Bootstrap Standard Error of Median: {bootstrap_se:.6f}")

# Bootstrap confidence intervals
# Method 1: Percentile method
ci_lower_percentile = np.percentile(bootstrap_medians, 100 * alpha / 2)
ci_upper_percentile = np.percentile(bootstrap_medians, 100 * (1 - alpha / 2))

print(f"\nPercentile Bootstrap CI ({1-alpha:.0%}): [{ci_lower_percentile:.6f}, {ci_upper_percentile:.6f}]")

# Method 2: Normal approximation (using bootstrap SE)
median_observed = np.median(data)
z_critical = stats.norm.ppf(1 - alpha / 2)
ci_lower_normal = median_observed - z_critical * bootstrap_se
ci_upper_normal = median_observed + z_critical * bootstrap_se

print(f"Normal Approximation CI ({1-alpha:.0%}): [{ci_lower_normal:.6f}, {ci_upper_normal:.6f}]")

# Method 3: Bias-corrected and accelerated (BCa) bootstrap
# Compute bias correction
z0 = stats.norm.ppf(np.mean(bootstrap_medians < median_observed))

# Compute acceleration (jackknife)
n_jackknife = n
jackknife_medians = np.zeros(n_jackknife)

for i in range(n_jackknife):
    jackknife_sample = np.delete(data, i)
    jackknife_medians[i] = np.median(jackknife_sample)

jackknife_mean = np.mean(jackknife_medians)
numerator = np.sum((jackknife_mean - jackknife_medians)**3)
denominator = 6 * (np.sum((jackknife_mean - jackknife_medians)**2))**(3/2)
acceleration = numerator / (denominator + 1e-10)

# BCa percentiles
z_alpha_lower = stats.norm.ppf(alpha / 2)
z_alpha_upper = stats.norm.ppf(1 - alpha / 2)

percentile_lower_bca = stats.norm.cdf(z0 + (z0 + z_alpha_lower) / (1 - acceleration * (z0 + z_alpha_lower)))
percentile_upper_bca = stats.norm.cdf(z0 + (z0 + z_alpha_upper) / (1 - acceleration * (z0 + z_alpha_upper)))

ci_lower_bca = np.percentile(bootstrap_medians, 100 * percentile_lower_bca)
ci_upper_bca = np.percentile(bootstrap_medians, 100 * percentile_upper_bca)

print(f"BCa Bootstrap CI ({1-alpha:.0%}): [{ci_lower_bca:.6f}, {ci_upper_bca:.6f}]")
print(f"  Bias correction z0: {z0:.6f}")
print(f"  Acceleration: {acceleration:.6f}")

# Visualization
fig, axes = plt.subplots(2, 1, figsize=(12, 10))

# Bootstrap distribution
ax1 = axes[0]
ax1.hist(bootstrap_medians, bins=50, density=True, alpha=0.6, color='blue', 
         edgecolor='black', label='Bootstrap Distribution')
ax1.axvline(median_observed, color='red', linestyle='--', linewidth=2, label=f'Observed Median = {median_observed:.3f}')
ax1.axvline(ci_lower_percentile, color='green', linestyle=':', linewidth=2, label='Percentile CI')
ax1.axvline(ci_upper_percentile, color='green', linestyle=':', linewidth=2)
ax1.set_xlabel('Median')
ax1.set_ylabel('Density')
ax1.set_title('Bootstrap Distribution of Sample Median')
ax1.legend()
ax1.grid(True, alpha=0.3)

# Original data distribution
ax2 = axes[1]
ax2.hist(data, bins=30, density=True, alpha=0.6, color='gray', edgecolor='black', label='Data')
ax2.axvline(median_observed, color='red', linestyle='--', linewidth=2, label=f'Median = {median_observed:.3f}')
ax2.axvline(np.mean(data), color='orange', linestyle='--', linewidth=2, label=f'Mean = {np.mean(data):.3f}')
ax2.set_xlabel('x')
ax2.set_ylabel('Density')
ax2.set_title('Original Data Distribution (Log-Normal)')
ax2.legend()
ax2.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('bootstrap_median.png', dpi=300)
print("\nVisualization saved to 'bootstrap_median.png'")
print("=" * 70)
```

Execute with `python3 bootstrap_median.py`. The output provides three bootstrap confidence intervals: the percentile method directly uses quantiles of the bootstrap distribution, the normal approximation assumes the bootstrap distribution is Gaussian with estimated standard error, and the bias-corrected and accelerated (BCa) method adjusts for bias and skewness. For skewed data like log-normal, the BCa interval often provides better coverage than the simpler methods. The visualization shows the bootstrap distribution centered near the observed median with empirical spread quantifying the estimation uncertainty. The original data histogram reveals the right-skewed log-normal shape, explaining why the median differs from the mean.

## Formal Axioms Cheat Sheet & Verification Reference

Statistical inference rests on a hierarchy of formal axioms from probability theory, measure theory, and functional analysis. This reference consolidates the foundational structures verified throughout the operational labs, providing precise statements for computational validation and formal proof development.

**Probability Axioms (Kolmogorov):** Let $(\Omega, \mathcal{F}, P)$ be a probability space where $\Omega$ is the sample space, $\mathcal{F}$ is a $\sigma$-algebra of events, and $P: \mathcal{F} \to [0, 1]$ is a probability measure satisfying: (1) Non-negativity: $P(A) \geq 0$ for all $A \in \mathcal{F}$. (2) Normalization: $P(\Omega) = 1$. (3) Countable additivity: For disjoint events $A_1, A_2, \ldots \in \mathcal{F}$, $P\left(\bigcup_{i=1}^\infty A_i\right) = \sum_{i=1}^\infty P(A_i)$. Computational verification proceeds by Monte Carlo estimation of probabilities for finite approximations to countable unions.

**Weak Law of Large Numbers:** Let $X_1, X_2, \ldots$ be i.i.d. random variables with $\mathbb{E}[X_i] = \mu$ and $\text{Var}(X_i) = \sigma^2 < \infty$. Then for any $\epsilon > 0$, $\lim_{n \to \infty} P(|\bar{X}_n - \mu| \geq \epsilon) = 0$, where $\bar{X}_n = \frac{1}{n}\sum_{i=1}^n X_i$. Verification via Chebyshev's inequality: $P(|\bar{X}_n - \mu| \geq \epsilon) \leq \frac{\sigma^2}{n\epsilon^2}$, implemented by computing empirical probabilities for varying $n$ and confirming convergence to zero.

**Strong Law of Large Numbers:** Under the same conditions, $P\left(\lim_{n \to \infty} \bar{X}_n = \mu\right) = 1$. Verification requires generating multiple independent sequences and confirming that almost all sequences converge to $\mu$ (proportion approaching 1).

**Central Limit Theorem (Lindeberg-Lévy):** Let $X_1, X_2, \ldots$ be i.i.d. with $\mathbb{E}[X_i] = \mu$ and $0 < \text{Var}(X_i) = \sigma^2 < \infty$. Then $\frac{\sqrt{n}(\bar{X}_n - \mu)}{\sigma} \xrightarrow{d} \mathcal{N}(0, 1)$. Verification via Kolmogorov-Smirnov test comparing the empirical CDF of standardized sample means against the standard normal CDF for increasing $n$.

**Delta Method:** If $\sqrt{n}(\hat{\theta}_n - \theta) \xrightarrow{d} \mathcal{N}(0, \sigma^2)$ and $g$ is continuously differentiable at $\theta$ with $g'(\theta) \neq 0$, then $\sqrt{n}(g(\hat{\theta}_n) - g(\theta)) \xrightarrow{d} \mathcal{N}(0, [g'(\theta)]^2 \sigma^2)$. Symbolic verification via SymPy differentiation of $g$, numerical verification via Monte Carlo simulation confirming the transformed statistic's distribution.

**Maximum Likelihood Estimation Consistency:** Under regularity conditions (identifiability, compactness, continuity), the MLE $\hat{\theta}_{\text{MLE}}$ is consistent: $\hat{\theta}_{\text{MLE}} \xrightarrow{p} \theta$ as $n \to \infty$. Verification via simulation studies showing convergence of MLE to true parameter as sample size increases.

**Asymptotic Normality of MLE:** Under regularity conditions, $\sqrt{n}(\hat{\theta}_{\text{MLE}} - \theta) \xrightarrow{d} \mathcal{N}(0, I(\theta)^{-1})$, where $I(\theta) = -\mathbb{E}[\ell''(\theta)]$ is the Fisher information. Verification via Monte Carlo: generate many samples, compute MLE for each, standardize using estimated Fisher information, and test normality.

**Cramér-Rao Lower Bound:** For any unbiased estimator $\hat{\theta}$ of parameter $\theta$, $\text{Var}(\hat{\theta}) \geq I(\theta)^{-1}$, where $I(\theta)$ is the Fisher information. The MLE achieves this bound asymptotically. Verification via comparing empirical variance of estimators against the Cramér-Rao bound.

**Likelihood Ratio Test Asymptotic Distribution:** Under the null hypothesis, the likelihood ratio statistic $-2\log\Lambda = 2(\ell(\hat{\theta}) - \ell(\theta_0)) \xrightarrow{d} \chi^2_k$ where $k$ is the difference in the number of free parameters between the full and restricted models (Wilks' theorem). Verification via Monte Carlo under the null hypothesis and chi-squared goodness-of-fit test.

**Neyman-Pearson Lemma:** For testing simple hypotheses $H_0: \theta = \theta_0$ versus $H_1: \theta = \theta_1$, the most powerful test of size $\alpha$ rejects $H_0$ when the likelihood ratio $\frac{f(x; \theta_1)}{f(x; \theta_0)} > k$ for constant $k$ determined by $\alpha$. Verification via simulation comparing power curves of likelihood ratio tests against other tests.

**Bootstrap Consistency:** For a statistic $T_n = g(X_1, \ldots, X_n)$ with $\sqrt{n}(T_n - \theta) \xrightarrow{d} G$ where $G$ is some distribution, the bootstrap distribution $\sqrt{n}(T_n^* - T_n)$ conditional on the sample converges to $G$ in probability. Verification via comparing bootstrap distribution quantiles against known asymptotic distributions.

**EM Algorithm Convergence:** The EM algorithm monotonically increases the log-likelihood: $\ell(\theta^{(t+1)}) \geq \ell(\theta^{(t)})$ with equality only at stationary points. The sequence $\{\ell(\theta^{(t)})\}$ converges to a local maximum. Verification via computing log-likelihood at each iteration and confirming monotonicity and convergence.

**Slutsky's Theorem:** If $X_n \xrightarrow{d} X$ and $Y_n \xrightarrow{p} c$ where $c$ is constant, then $X_n + Y_n \xrightarrow{d} X + c$, $X_n Y_n \xrightarrow{d} cX$, and $X_n / Y_n \xrightarrow{d} X / c$ (provided $c \neq 0$). Verification via simulation demonstrating convergence of combined statistics.

**Continuous Mapping Theorem:** If $X_n \xrightarrow{d} X$ and $g$ is continuous, then $g(X_n) \xrightarrow{d} g(X)$. If $X_n \xrightarrow{p} c$, then $g(X_n) \xrightarrow{p} g(c)$. Verification via applying transformations to convergent sequences and testing distributional convergence.

**Portmanteau Theorem:** For random variables $X_n$ and $X$, the following are equivalent: (1) $X_n \xrightarrow{d} X$. (2) $\mathbb{E}[f(X_n)] \to \mathbb{E}[f(X)]$ for all bounded continuous $f$. (3) $\limsup_n P(X_n \in F) \leq P(X \in F)$ for all closed $F$. (4) $\liminf_n P(X_n \in G) \geq P(X \in G)$ for all open $G$. Computational verification focuses on condition (2) via Monte Carlo integration.

The practitioner equipped with these formal statements and their computational implementations possesses both the theoretical foundation and operational capability to verify statistical claims rigorously, stress-test methodologies at pathological boundary cases, and implement novel inference algorithms with mathematical transparency. The synthesis of symbolic computation, numerical simulation, and formal proof verification constitutes the gold standard for applied statistical practice in the modern computational era.
