# Lesson 2: Statistical Estimation Theory with Hypothesis Testing

## 1. First-Principles Intuition & Invariants

Statistical estimation theory emerges from a fundamental epistemic tension: we observe finite samples drawn from unknown probability distributions, yet we must make precise inferential claims about the generative mechanisms governing those distributions. The classical parametric paradigm posits that nature selects a parameter vector $\theta \in \Theta$ from some parameter space, which fully specifies a probability distribution $P_\theta$ over the sample space. Our task is to construct estimators—functions of the observed data—that recover $\theta$ with quantifiable precision, and to devise rigorous tests that adjudicate between competing hypotheses about $\theta$ under controlled error probabilities.

The distinction between **estimation** and **testing** is architectural, not merely semantic. Estimation produces a point or interval approximation to an unknown parameter, optimizing for criteria such as bias, variance, and mean squared error. Hypothesis testing, by contrast, partitions the parameter space into disjoint regions corresponding to null and alternative hypotheses, then constructs decision rules that bound Type I error (false rejection of the null) while maximizing power (true rejection when the alternative holds). The Neyman-Pearson framework formalizes this tradeoff through the notion of most powerful tests, leveraging likelihood ratios to achieve optimality under simple hypotheses.

Consider the prototypical problem: we observe independent and identically distributed random variables $X_1, X_2, \ldots, X_n \sim P_\theta$, where $\theta$ is unknown. The **likelihood function** $L(\theta \mid \mathbf{x}) = \prod_{i=1}^n f_\theta(x_i)$ quantifies the probability density (or mass) of the observed data under parameter $\theta$. Maximum likelihood estimation (MLE) selects the parameter value that maximizes $L(\theta \mid \mathbf{x})$, equivalently maximizing the log-likelihood $\ell(\theta) = \sum_{i=1}^n \log f_\theta(x_i)$. This principle, introduced by R.A. Fisher in the 1920s, dominates modern statistical practice due to its asymptotic optimality: under regularity conditions, the MLE is consistent (converges in probability to the true parameter), asymptotically normal (satisfies a central limit theorem), and asymptotically efficient (achieves the Cramér-Rao lower bound for variance).

The **method of moments** provides an alternative constructive approach. If the distribution $P_\theta$ is characterized by $k$ parameters, we equate the first $k$ sample moments $\frac{1}{n}\sum_{i=1}^n X_i^j$ to their population counterparts $\mathbb{E}_\theta[X^j]$ and solve the resulting system of equations for $\theta$. While computationally simpler than MLE, method-of-moments estimators often sacrifice efficiency, though they remain consistent under mild regularity conditions.

The concept of **sufficiency** refines our understanding of data reduction. A statistic $T(\mathbf{X})$ is sufficient for $\theta$ if the conditional distribution of the data given $T$ does not depend on $\theta$. The Fisher-Neyman factorization theorem provides the operational criterion: $T$ is sufficient if and only if the likelihood factors as $L(\theta \mid \mathbf{x}) = g(T(\mathbf{x}), \theta) h(\mathbf{x})$, where $h$ does not involve $\theta$. Sufficiency implies that $T$ captures all information in the sample relevant to inference about $\theta$; no further data processing can improve estimation.

The **Cramér-Rao lower bound** establishes a fundamental limit on estimator variance. For any unbiased estimator $\hat{\theta}$ of $\theta$, the variance satisfies
$$
\text{Var}_\theta(\hat{\theta}) \ge \frac{1}{I(\theta)},
$$
where $I(\theta) = \mathbb{E}_\theta\left[\left(\frac{\partial}{\partial\theta}\log f_\theta(X)\right)^2\right]$ is the Fisher information. An estimator achieving this bound is called **efficient**. The MLE, under regularity conditions, is asymptotically efficient: for large $n$, $\sqrt{n}(\hat{\theta}_{\text{MLE}} - \theta) \xrightarrow{d} N(0, 1/I(\theta))$.

Hypothesis testing introduces a decision-theoretic layer. We partition the parameter space as $\Theta = \Theta_0 \cup \Theta_1$, where $\Theta_0$ represents the null hypothesis $H_0$ and $\Theta_1$ the alternative $H_1$. A test is a measurable function $\phi: \mathcal{X}^n \to \{0, 1\}$, where $\phi(\mathbf{x}) = 1$ indicates rejection of $H_0$. The **size** of the test is $\alpha = \sup_{\theta \in \Theta_0} \mathbb{P}_\theta(\phi(\mathbf{X}) = 1)$, the maximum Type I error probability. The **power function** $\beta(\theta) = \mathbb{P}_\theta(\phi(\mathbf{X}) = 1)$ quantifies the probability of rejection as a function of $\theta$; for $\theta \in \Theta_1$, $\beta(\theta)$ is the power against that alternative.

The **Neyman-Pearson lemma** provides the fundamental optimality result for simple hypotheses. Suppose $H_0: \theta = \theta_0$ versus $H_1: \theta = \theta_1$. The most powerful test of size $\alpha$ rejects $H_0$ when the likelihood ratio $\Lambda(\mathbf{x}) = \frac{L(\theta_1 \mid \mathbf{x})}{L(\theta_0 \mid \mathbf{x})}$ exceeds a threshold $c$, chosen such that $\mathbb{P}_{\theta_0}(\Lambda(\mathbf{X}) > c) = \alpha$. No other test of size $\alpha$ achieves higher power against $\theta_1$.

**Confidence regions** provide interval estimates with frequentist coverage guarantees. A $1-\alpha$ confidence set $C(\mathbf{X})$ satisfies $\mathbb{P}_\theta(\theta \in C(\mathbf{X})) \ge 1-\alpha$ for all $\theta \in \Theta$. The duality between testing and confidence sets is profound: inverting a family of level-$\alpha$ tests yields a $1-\alpha$ confidence region, and conversely, a confidence region defines a family of tests by rejecting $H_0: \theta = \theta_0$ if and only if $\theta_0 \notin C(\mathbf{x})$.

The asymptotic machinery underlying large-sample inference rests on three pillars: the law of large numbers (ensuring consistency), the central limit theorem (yielding asymptotic normality), and the delta method (propagating asymptotic distributions through smooth transformations). These tools justify the widespread practice of constructing Wald, likelihood ratio, and score tests, all of which share asymptotic chi-squared null distributions under composite hypotheses.

## 2. Core Architecture & Mechanics

The operational pipeline for statistical estimation and testing proceeds through several stages: model specification, likelihood construction, optimization or moment matching, asymptotic analysis, and decision rule formulation. We dissect each stage with concrete derivations.

### Maximum Likelihood Estimation: Algebraic Derivation

Consider $n$ independent observations $X_1, \ldots, X_n$ from a normal distribution $N(\mu, \sigma^2)$, where both $\mu$ and $\sigma^2$ are unknown. The likelihood function is
$$
L(\mu, \sigma^2 \mid \mathbf{x}) = \prod_{i=1}^n \frac{1}{\sqrt{2\pi\sigma^2}} \exp\left(-\frac{(x_i - \mu)^2}{2\sigma^2}\right) = (2\pi\sigma^2)^{-n/2} \exp\left(-\frac{1}{2\sigma^2}\sum_{i=1}^n (x_i - \mu)^2\right).
$$
The log-likelihood simplifies to
$$
\ell(\mu, \sigma^2) = -\frac{n}{2}\log(2\pi) - \frac{n}{2}\log(\sigma^2) - \frac{1}{2\sigma^2}\sum_{i=1}^n (x_i - \mu)^2.
$$
Taking the partial derivative with respect to $\mu$ and setting to zero yields
$$
\frac{\partial \ell}{\partial \mu} = \frac{1}{\sigma^2}\sum_{i=1}^n (x_i - \mu) = 0 \quad \Rightarrow \quad \hat{\mu}_{\text{MLE}} = \frac{1}{n}\sum_{i=1}^n x_i = \bar{x}.
$$
For $\sigma^2$, we compute
$$
\frac{\partial \ell}{\partial \sigma^2} = -\frac{n}{2\sigma^2} + \frac{1}{2(\sigma^2)^2}\sum_{i=1}^n (x_i - \mu)^2 = 0 \quad \Rightarrow \quad \hat{\sigma}^2_{\text{MLE}} = \frac{1}{n}\sum_{i=1}^n (x_i - \bar{x})^2.
$$
This estimator is the sample variance (without Bessel's correction). While $\hat{\mu}_{\text{MLE}}$ is unbiased, $\hat{\sigma}^2_{\text{MLE}}$ is biased: $\mathbb{E}[\hat{\sigma}^2_{\text{MLE}}] = \frac{n-1}{n}\sigma^2$. However, both estimators are consistent and asymptotically efficient.

### Method of Moments: Systematic Construction

For the same normal model, the method of moments equates sample and population moments. The first two population moments are $\mathbb{E}[X] = \mu$ and $\mathbb{E}[X^2] = \mu^2 + \sigma^2$. The sample counterparts are $\bar{x}$ and $\frac{1}{n}\sum_{i=1}^n x_i^2$. Setting them equal:
$$
\hat{\mu}_{\text{MM}} = \bar{x}, \quad \hat{\mu}_{\text{MM}}^2 + \hat{\sigma}^2_{\text{MM}} = \frac{1}{n}\sum_{i=1}^n x_i^2.
$$
Solving for $\hat{\sigma}^2_{\text{MM}}$:
$$
\hat{\sigma}^2_{\text{MM}} = \frac{1}{n}\sum_{i=1}^n x_i^2 - \bar{x}^2 = \frac{1}{n}\sum_{i=1}^n (x_i - \bar{x})^2 = \hat{\sigma}^2_{\text{MLE}}.
$$
In this case, the method of moments and MLE coincide for $\sigma^2$. This is not universal; for many distributions, MLE and method-of-moments estimators diverge in finite samples.

### Fisher Information and the Cramér-Rao Bound

For a scalar parameter $\theta$, the Fisher information from a single observation is
$$
I(\theta) = \mathbb{E}_\theta\left[\left(\frac{\partial}{\partial\theta}\log f_\theta(X)\right)^2\right] = -\mathbb{E}_\theta\left[\frac{\partial^2}{\partial\theta^2}\log f_\theta(X)\right],
$$
where the second equality holds under regularity (differentiability and dominated convergence conditions). For $n$ independent observations, $I_n(\theta) = n I(\theta)$. The Cramér-Rao bound asserts that for any unbiased estimator $\hat{\theta}$,
$$
\text{Var}_\theta(\hat{\theta}) \ge \frac{1}{I_n(\theta)} = \frac{1}{n I(\theta)}.
$$

**Example:** For $X \sim \text{Bernoulli}(p)$, the likelihood for one observation is $f_p(x) = p^x (1-p)^{1-x}$, so
$$
\log f_p(x) = x \log p + (1-x)\log(1-p).
$$
The score function is
$$
\frac{\partial}{\partial p}\log f_p(x) = \frac{x}{p} - \frac{1-x}{1-p} = \frac{x - p}{p(1-p)}.
$$
The Fisher information is
$$
I(p) = \mathbb{E}_p\left[\left(\frac{X - p}{p(1-p)}\right)^2\right] = \frac{1}{p^2(1-p)^2}\mathbb{E}_p[(X - p)^2] = \frac{p(1-p)}{p^2(1-p)^2} = \frac{1}{p(1-p)}.
$$
For $n$ observations, $I_n(p) = \frac{n}{p(1-p)}$, so the Cramér-Rao bound is $\frac{p(1-p)}{n}$. The sample proportion $\hat{p} = \bar{X}$ has variance exactly $\frac{p(1-p)}{n}$, achieving the bound; it is an efficient estimator.

### Sufficiency and the Factorization Theorem

A statistic $T(\mathbf{X})$ is sufficient for $\theta$ if the conditional distribution $P_\theta(\mathbf{X} \in A \mid T(\mathbf{X}) = t)$ does not depend on $\theta$. The Fisher-Neyman factorization theorem provides the practical criterion: $T$ is sufficient if and only if
$$
L(\theta \mid \mathbf{x}) = g(T(\mathbf{x}), \theta) h(\mathbf{x}),
$$
where $h$ is independent of $\theta$.

**Example:** For $X_1, \ldots, X_n \sim \text{Exponential}(\lambda)$, the density is $f_\lambda(x) = \lambda e^{-\lambda x}$ for $x \ge 0$. The likelihood is
$$
L(\lambda \mid \mathbf{x}) = \prod_{i=1}^n \lambda e^{-\lambda x_i} = \lambda^n e^{-\lambda \sum_{i=1}^n x_i}.
$$
This factors as $g(T(\mathbf{x}), \lambda) \cdot h(\mathbf{x})$ with $T(\mathbf{x}) = \sum_{i=1}^n x_i$ and $h(\mathbf{x}) = 1$. Thus $T(\mathbf{X}) = \sum_{i=1}^n X_i$ is sufficient for $\lambda$. Since $X_i \sim \text{Exponential}(\lambda)$ implies $\sum_{i=1}^n X_i \sim \text{Gamma}(n, \lambda)$, all inference can be conducted through this univariate statistic regardless of sample size $n$.

### Neyman-Pearson Lemma: Rigorous Statement and Proof

**Theorem (Neyman-Pearson Lemma):** Let $X_1, \ldots, X_n$ be observations with joint density $f_\theta(\mathbf{x})$. Consider testing $H_0: \theta = \theta_0$ versus $H_1: \theta = \theta_1$. For a given $\alpha \in (0, 1)$, define the likelihood ratio statistic
$$
\Lambda(\mathbf{x}) = \frac{f_{\theta_1}(\mathbf{x})}{f_{\theta_0}(\mathbf{x})}.
$$
The test that rejects $H_0$ when $\Lambda(\mathbf{x}) > c$, where $c$ is chosen such that $\mathbb{P}_{\theta_0}(\Lambda(\mathbf{X}) > c) = \alpha$, is the most powerful test of size $\alpha$. That is, for any other test $\phi'$ with $\mathbb{P}_{\theta_0}(\phi'(\mathbf{X}) = 1) \le \alpha$, we have
$$
\mathbb{P}_{\theta_1}(\Lambda(\mathbf{X}) > c) \ge \mathbb{P}_{\theta_1}(\phi'(\mathbf{X}) = 1).
$$

**Proof:** Let $\phi(\mathbf{x}) = \mathbb{1}\{\Lambda(\mathbf{x}) > c\}$ be the Neyman-Pearson test, and $\phi'$ any other test of size at most $\alpha$. We must show $\mathbb{E}_{\theta_1}[\phi(\mathbf{X})] \ge \mathbb{E}_{\theta_1}[\phi'(\mathbf{X})]$, or equivalently,
$$
\int (\phi(\mathbf{x}) - \phi'(\mathbf{x})) f_{\theta_1}(\mathbf{x}) d\mathbf{x} \ge 0.
$$
Note that $\phi(\mathbf{x}) = 1$ implies $\Lambda(\mathbf{x}) > c$, hence $f_{\theta_1}(\mathbf{x}) > c f_{\theta_0}(\mathbf{x})$. Similarly, $\phi(\mathbf{x}) = 0$ implies $f_{\theta_1}(\mathbf{x}) \le c f_{\theta_0}(\mathbf{x})$. Thus,
$$
(\phi(\mathbf{x}) - \phi'(\mathbf{x})) f_{\theta_1}(\mathbf{x}) \ge c (\phi(\mathbf{x}) - \phi'(\mathbf{x})) f_{\theta_0}(\mathbf{x}).
$$
Integrating both sides:
$$
\int (\phi(\mathbf{x}) - \phi'(\mathbf{x})) f_{\theta_1}(\mathbf{x}) d\mathbf{x} \ge c \int (\phi(\mathbf{x}) - \phi'(\mathbf{x})) f_{\theta_0}(\mathbf{x}) d\mathbf{x}.
$$
The right-hand integral is $\mathbb{P}_{\theta_0}(\phi(\mathbf{X}) = 1) - \mathbb{P}_{\theta_0}(\phi'(\mathbf{X}) = 1) = \alpha - \mathbb{P}_{\theta_0}(\phi'(\mathbf{X}) = 1) \ge 0$ by assumption. Hence the left-hand side is non-negative, establishing the result. $\square$

**Practical Implementation:** For $n$ observations from $N(\mu, 1)$ with $H_0: \mu = 0$ versus $H_1: \mu = \mu_1 > 0$, the likelihood ratio is
$$
\Lambda(\mathbf{x}) = \frac{\prod_{i=1}^n \frac{1}{\sqrt{2\pi}} e^{-(x_i - \mu_1)^2/2}}{\prod_{i=1}^n \frac{1}{\sqrt{2\pi}} e^{-x_i^2/2}} = \exp\left(\mu_1 \sum_{i=1}^n x_i - \frac{n\mu_1^2}{2}\right).
$$
Taking logarithms, $\log \Lambda(\mathbf{x}) = \mu_1 n \bar{x} - \frac{n\mu_1^2}{2}$. Since $\mu_1 > 0$, this is increasing in $\bar{x}$, so the most powerful test rejects $H_0$ when $\bar{x} > c$, where $c$ is chosen such that $\mathbb{P}_0(\bar{X} > c) = \alpha$. Under $H_0$, $\bar{X} \sim N(0, 1/n)$, so $c = \frac{z_\alpha}{\sqrt{n}}$, where $z_\alpha$ is the upper $\alpha$ quantile of the standard normal distribution.

### Power Functions and Sample Size Determination

The power function $\beta(\theta) = \mathbb{P}_\theta(\text{reject } H_0)$ characterizes test performance across the parameter space. For the above one-sided $z$-test, under $H_1: \mu = \mu_1$,
$$
\beta(\mu_1) = \mathbb{P}_{\mu_1}\left(\bar{X} > \frac{z_\alpha}{\sqrt{n}}\right) = \mathbb{P}\left(Z > z_\alpha - \mu_1\sqrt{n}\right) = \Phi(\mu_1\sqrt{n} - z_\alpha),
$$
where $Z \sim N(0, 1)$ and $\Phi$ is the standard normal CDF. To achieve power $1-\beta$ at $\mu_1$, we require
$$
\mu_1\sqrt{n} - z_\alpha = z_{1-\beta} \quad \Rightarrow \quad n = \left(\frac{z_\alpha + z_{1-\beta}}{\mu_1}\right)^2.
$$

**Example:** To detect $\mu_1 = 0.5$ with $\alpha = 0.05$ and power $0.8$, we have $z_{0.05} = 1.645$ and $z_{0.2} = 0.842$, yielding
$$
n = \left(\frac{1.645 + 0.842}{0.5}\right)^2 = (4.974)^2 \approx 24.7 \quad \Rightarrow \quad n = 25.
$$

### Confidence Intervals via Pivotal Quantities

A **pivotal quantity** is a function $Q(\mathbf{X}, \theta)$ whose distribution does not depend on $\theta$. For $X_1, \ldots, X_n \sim N(\mu, \sigma^2)$ with $\sigma^2$ known, the quantity $Z = \frac{\bar{X} - \mu}{\sigma/\sqrt{n}}$ is standard normal regardless of $\mu$. Thus,
$$
\mathbb{P}\left(-z_{\alpha/2} \le \frac{\bar{X} - \mu}{\sigma/\sqrt{n}} \le z_{\alpha/2}\right) = 1 - \alpha.
$$
Rearranging yields the $1-\alpha$ confidence interval
$$
\left[\bar{X} - z_{\alpha/2} \frac{\sigma}{\sqrt{n}}, \bar{X} + z_{\alpha/2} \frac{\sigma}{\sqrt{n}}\right].
$$

When $\sigma^2$ is unknown, we use the $t$-statistic $T = \frac{\bar{X} - \mu}{S/\sqrt{n}}$, where $S^2 = \frac{1}{n-1}\sum_{i=1}^n (X_i - \bar{X})^2$. Under normality, $T \sim t_{n-1}$, yielding
$$
\left[\bar{X} - t_{n-1, \alpha/2} \frac{S}{\sqrt{n}}, \bar{X} + t_{n-1, \alpha/2} \frac{S}{\sqrt{n}}\right].
$$

### Asymptotic Distribution Theory: The Delta Method

Suppose $\sqrt{n}(\hat{\theta}_n - \theta) \xrightarrow{d} N(0, \sigma^2)$. For a smooth function $g$ with $g'(\theta) \neq 0$, the delta method asserts
$$
\sqrt{n}(g(\hat{\theta}_n) - g(\theta)) \xrightarrow{d} N(0, \sigma^2 [g'(\theta)]^2).
$$

**Proof Sketch:** By Taylor expansion,
$$
g(\hat{\theta}_n) - g(\theta) = g'(\theta)(\hat{\theta}_n - \theta) + o_p(|\hat{\theta}_n - \theta|).
$$
Multiplying by $\sqrt{n}$,
$$
\sqrt{n}(g(\hat{\theta}_n) - g(\theta)) = g'(\theta) \sqrt{n}(\hat{\theta}_n - \theta) + o_p(1) \xrightarrow{d} N(0, \sigma^2 [g'(\theta)]^2). \quad \square
$$

**Application:** For $X_1, \ldots, X_n \sim \text{Bernoulli}(p)$, $\sqrt{n}(\hat{p} - p) \xrightarrow{d} N(0, p(1-p))$. To estimate the odds $\psi = \frac{p}{1-p}$, set $g(p) = \frac{p}{1-p}$, so $g'(p) = \frac{1}{(1-p)^2}$. Then
$$
\sqrt{n}\left(\frac{\hat{p}}{1-\hat{p}} - \frac{p}{1-p}\right) \xrightarrow{d} N\left(0, p(1-p) \cdot \frac{1}{(1-p)^4}\right) = N\left(0, \frac{p}{(1-p)^3}\right).
$$

### Likelihood Ratio Tests for Composite Hypotheses

For composite hypotheses $H_0: \theta \in \Theta_0$ versus $H_1: \theta \in \Theta_1$, the generalized likelihood ratio statistic is
$$
\Lambda(\mathbf{x}) = \frac{\sup_{\theta \in \Theta_0} L(\theta \mid \mathbf{x})}{\sup_{\theta \in \Theta} L(\theta \mid \mathbf{x})}.
$$
Under regularity conditions, Wilks' theorem asserts that $-2\log\Lambda(\mathbf{X}) \xrightarrow{d} \chi^2_k$ under $H_0$, where $k = \dim(\Theta) - \dim(\Theta_0)$ is the difference in dimensionality. This provides an asymptotic level-$\alpha$ test: reject $H_0$ if $-2\log\Lambda(\mathbf{x}) > \chi^2_{k, \alpha}$.

**Example:** For $X_1, \ldots, X_n \sim N(\mu, \sigma^2)$, test $H_0: \mu = \mu_0$ versus $H_1: \mu \neq \mu_0$ with $\sigma^2$ unknown. Under $H_0$, the MLE is $\hat{\sigma}^2_0 = \frac{1}{n}\sum_{i=1}^n (x_i - \mu_0)^2$. Under the unrestricted model, $\hat{\mu} = \bar{x}$ and $\hat{\sigma}^2 = \frac{1}{n}\sum_{i=1}^n (x_i - \bar{x})^2$. The likelihood ratio statistic is
$$
\Lambda(\mathbf{x}) = \frac{L(\mu_0, \hat{\sigma}^2_0 \mid \mathbf{x})}{L(\hat{\mu}, \hat{\sigma}^2 \mid \mathbf{x})} = \left(\frac{\hat{\sigma}^2}{\hat{\sigma}^2_0}\right)^{n/2}.
$$
Under $H_0$, $-2\log\Lambda(\mathbf{X}) \xrightarrow{d} \chi^2_1$, providing an asymptotic test. For finite samples, the exact $t$-test based on $T = \frac{\bar{X} - \mu_0}{S/\sqrt{n}}$ is preferred.

## 3. High-Performance Optimization & Failure Modes

The computational and statistical efficiency of estimation procedures depends critically on problem structure, numerical stability, and sample size asymptotics. Optimization of estimation workflows involves leveraging sufficiency for dimension reduction, employing numerically stable algorithms for likelihood maximization, and applying variance reduction techniques in simulation-based inference.

### Computational Efficiency via Sufficient Statistics

When a low-dimensional sufficient statistic $T(\mathbf{X})$ exists, all inference can be conducted through $T$ rather than the full data vector $\mathbf{X}$. For exponential families—distributions whose densities factor as
$$
f_\theta(x) = h(x) \exp\left(\sum_{j=1}^k \eta_j(\theta) T_j(x) - A(\theta)\right),
$$
the statistic $\mathbf{T}(\mathbf{X}) = \left(\sum_{i=1}^n T_1(X_i), \ldots, \sum_{i=1}^n T_k(X_i)\right)$ is sufficient. This $k$-dimensional vector, regardless of sample size $n$, encodes all inferential content. For instance, in the normal model $N(\mu, \sigma^2)$, the pair $(\sum_{i=1}^n X_i, \sum_{i=1}^n X_i^2)$ is sufficient, reducing $n$-dimensional data to two scalars.

In large-scale applications, precomputing sufficient statistics enables online updating: as new data arrive, updating $T$ requires constant-time operations rather than reprocessing the entire dataset. This is exploited in streaming algorithms for mean estimation, variance estimation, and online linear regression.

### Numerical Optimization for Maximum Likelihood

Direct maximization of the log-likelihood $\ell(\theta)$ employs iterative algorithms such as Newton-Raphson, Fisher scoring, and the Expectation-Maximization (EM) algorithm. Newton-Raphson updates the parameter estimate via
$$
\theta^{(t+1)} = \theta^{(t)} - \left[H_{\ell}(\theta^{(t)})\right]^{-1} \nabla \ell(\theta^{(t)}),
$$
where $H_{\ell}$ is the Hessian matrix of second derivatives. Near the maximum, this achieves quadratic convergence. However, computing and inverting the Hessian is expensive for high-dimensional $\theta$; Fisher scoring replaces $H_{\ell}$ with its expectation, the observed Fisher information matrix, which may be more stable.

The EM algorithm applies when the model involves latent variables $Z$. The E-step computes the expected log-likelihood $Q(\theta \mid \theta^{(t)}) = \mathbb{E}_{Z \mid \mathbf{X}, \theta^{(t)}}[\log L(\theta \mid \mathbf{X}, Z)]$, and the M-step maximizes $Q$ with respect to $\theta$. Each iteration monotonically increases the observed-data log-likelihood, guaranteeing convergence to a local maximum (though not necessarily global).

**Numerical Stability:** Log-likelihood functions often involve products of many small probabilities, risking underflow. Computing $\ell(\theta) = \sum_{i=1}^n \log f_\theta(x_i)$ directly avoids this. For likelihood ratios in hypothesis tests, computing $\log \Lambda(\mathbf{x}) = \ell(\theta_1) - \ell(\theta_0)$ is numerically superior to forming the ratio $\frac{L(\theta_1)}{L(\theta_0)}$.

### Variance Reduction and Effective Sample Size

In simulation-based inference (e.g., Monte Carlo hypothesis tests or bootstrap confidence intervals), variance reduction techniques improve efficiency. Antithetic variates exploit negative correlation: if estimating $\mathbb{E}[g(U)]$ for $U \sim \text{Uniform}(0,1)$, simulate $U_i$ and $1 - U_i$ in pairs, reducing variance compared to independent sampling. Control variates leverage auxiliary variables with known expectations to correct bias in simulation estimates.

The **effective sample size** in dependent data settings (e.g., Markov chain Monte Carlo) accounts for autocorrelation. If samples $\theta^{(1)}, \ldots, \theta^{(M)}$ from a Markov chain have autocorrelation function $\rho(k)$, the effective sample size is
$$
n_{\text{eff}} = \frac{M}{1 + 2\sum_{k=1}^\infty \rho(k)}.
$$
Estimator variances scale as $1/n_{\text{eff}}$ rather than $1/M$, necessitating thinning or longer chains for precision.

### Robustness and Breakdown Points

Classical estimators such as the sample mean are sensitive to outliers: a single erroneous observation can arbitrarily inflate $\bar{X}$. The **breakdown point** of an estimator is the minimum fraction of contaminated data required to drive the estimate to infinity. For the mean, the breakdown point is $1/n$, vanishing as $n \to \infty$. The median, by contrast, has breakdown point $1/2$: up to half the data can be corrupted before the median becomes uninformative.

Robust alternatives include $M$-estimators, which minimize $\sum_{i=1}^n \rho((X_i - \mu)/\sigma)$ for a loss function $\rho$ less sensitive than squared error. The Huber loss
$$
\rho_c(u) = \begin{cases}
\frac{1}{2}u^2 & \text{if } |u| \le c, \\
c|u| - \frac{1}{2}c^2 & \text{if } |u| > c,
\end{cases}
$$
balances efficiency and robustness: it is quadratic near zero (like least squares) and linear in the tails (like absolute deviation), downweighting outliers.

### Multiple Testing and False Discovery Rate Control

When conducting $m$ hypothesis tests simultaneously, controlling the family-wise error rate (FWER)—the probability of any false rejection—at level $\alpha$ requires stringent adjustments. The Bonferroni correction tests each hypothesis at level $\alpha/m$, ensuring $\text{FWER} \le \alpha$ by the union bound. However, this is conservative, reducing power substantially for large $m$.

The **false discovery rate** (FDR), the expected proportion of false rejections among all rejections, offers a less conservative criterion. The Benjamini-Hochberg procedure controls FDR at level $\alpha$: order the $p$-values $p_{(1)} \le p_{(2)} \le \cdots \le p_{(m)}$ and reject hypotheses $H_{(1)}, \ldots, H_{(k)}$, where $k$ is the largest index such that $p_{(k)} \le \frac{k}{m}\alpha$. This procedure is adaptive and more powerful than Bonferroni in large-scale testing regimes such as genomics and neuroimaging.

### Computational Complexity and Asymptotic Trade-offs

Estimation algorithms exhibit varying computational complexity. Method-of-moments estimators typically require $O(n)$ operations to compute sample moments and $O(1)$ to solve the resulting equations, yielding $O(n)$ total complexity. Maximum likelihood, by contrast, requires iterative optimization: each Newton-Raphson iteration costs $O(nk^2)$ for $k$ parameters (computing the gradient and Hessian), and convergence may require $O(\log \frac{1}{\epsilon})$ iterations for precision $\epsilon$, yielding $O(nk^2 \log \frac{1}{\epsilon})$ total cost.

For massive datasets, stochastic gradient methods replace full-data gradients with mini-batch approximations, reducing per-iteration cost from $O(n)$ to $O(b)$ for batch size $b \ll n$. While more iterations are required, the overall complexity often improves to $O(k^2 \sqrt{n})$ or better under strong convexity.

### Boundary Cases and Failure Modes

Regularity conditions underlying asymptotic theory—differentiability of the likelihood, compactness of the parameter space, identifiability—can fail in practice. When the true parameter lies on the boundary of $\Theta$ (e.g., testing $H_0: \sigma^2 = 0$ in a normal model), the MLE may not be asymptotically normal; instead, it may converge to a truncated distribution. Mixture models and hidden Markov models exhibit non-identifiability: multiple parameter values yield identical distributions, causing the likelihood to have flat ridges and the MLE to be ill-defined.

Sparse or separation issues arise in logistic regression when a covariate perfectly predicts the response: the MLE for that coefficient diverges to $\pm\infty$, though predictions remain well-defined. Penalized estimators such as ridge or LASSO regression mitigate this by adding a regularization term $\lambda \|\theta\|_2^2$ or $\lambda \|\theta\|_1$ to the negative log-likelihood, inducing finite estimates at the cost of bias.

### Confidence Interval Coverage and Conservativeness

Nominal $1-\alpha$ confidence intervals are designed to cover the true parameter with probability at least $1-\alpha$ for all $\theta$. In finite samples, coverage may be conservative (exceeding $1-\alpha$) or anticonservative (falling below $1-\alpha$). For discrete distributions, exact coverage is often unattainable: the binomial proportion interval based on the normal approximation can have actual coverage as low as $0.92$ for nominal $0.95$ level when $n$ is small and $p$ near $0$ or $1$. The Clopper-Pearson exact interval, based on inverting the binomial test, guarantees coverage $\ge 1-\alpha$ but is conservative, yielding wider intervals on average.

### Sequential Testing and the Sequential Probability Ratio Test

In settings where data arrive sequentially and testing can terminate early, the **sequential probability ratio test (SPRT)** minimizes expected sample size under both hypotheses. For $H_0: \theta = \theta_0$ versus $H_1: \theta = \theta_1$, the SPRT computes the cumulative likelihood ratio $\Lambda_n = \prod_{i=1}^n \frac{f_{\theta_1}(X_i)}{f_{\theta_0}(X_i)}$ after each observation. The test rejects $H_0$ if $\Lambda_n \ge B$, accepts $H_0$ if $\Lambda_n \le A$, and continues sampling otherwise. The boundaries $A$ and $B$ are chosen to achieve desired Type I and Type II error probabilities via Wald's approximation:
$$
A \approx \frac{\beta}{1-\alpha}, \quad B \approx \frac{1-\beta}{\alpha}.
$$
The SPRT is optimal in the sense of Wald and Wolfowitz: it minimizes the expected sample size under both hypotheses among all tests with the same error probabilities.

**Practical Implementation:** For $X_i \sim N(\mu, 1)$ testing $H_0: \mu = 0$ versus $H_1: \mu = 1$, the log-likelihood ratio after $n$ observations is
$$
\log \Lambda_n = \sum_{i=1}^n (X_i - 1/2) = n\bar{X}_n - \frac{n}{2}.
$$
Continue sampling while $\log A < \log \Lambda_n < \log B$. For $\alpha = \beta = 0.05$, $A \approx 0.053$ and $B \approx 19$, so continue while $-2.94 < n\bar{X}_n - n/2 < 2.94$. This often terminates with far fewer observations than fixed-sample tests, especially when the true parameter is far from the boundary between hypotheses.

### Connections to Decision Theory and Bayesian Estimation

Frequentist estimation embeds naturally in statistical decision theory. An estimator $\hat{\theta}$ incurs loss $L(\theta, \hat{\theta})$; common choices include squared error $L(\theta, \hat{\theta}) = (\theta - \hat{\theta})^2$ and absolute error $L(\theta, \hat{\theta}) = |\theta - \hat{\theta}|$. The **risk** is $R(\theta, \hat{\theta}) = \mathbb{E}_\theta[L(\theta, \hat{\theta}(\mathbf{X}))]$. An estimator is **admissible** if no other estimator has uniformly lower risk; it is **minimax** if it minimizes $\sup_\theta R(\theta, \hat{\theta})$.

Bayesian estimators, which minimize posterior expected loss, often coincide with frequentist estimators under specific priors. For squared error loss, the Bayes estimator is the posterior mean $\mathbb{E}[\theta \mid \mathbf{X}]$; for absolute error, the posterior median. The James-Stein estimator, which shrinks the sample mean toward a common center, dominates the MLE under squared error in dimension $\ge 3$, illustrating that the MLE, though asymptotically optimal, is inadmissible in finite samples for multivariate normal estimation.

This duality between frequentist and Bayesian frameworks enriches both: frequentist asymptotic theory often validates Bayesian approximations (e.g., the Bernstein-von Mises theorem), while Bayesian credible intervals offer computational advantages when exact sampling distributions are intractable. The practitioner fluent in both paradigms can select tools matched to the inferential goal—frequentist methods when calibration across hypothetical replications is paramount, Bayesian methods when incorporating prior information or quantifying uncertainty conditional on observed data.
