# Lesson 2: Statistical Inference Frameworks

## 1. First-Principles Intuition & Invariants

Statistical inference occupies the conceptual bridge between observable data and the unobservable probability distributions that generate them. Where probability theory provides the forward map from distributions to data realizations, inference reverses this arrow: given a finite sample drawn from an unknown distribution, we seek to estimate parameters, test hypotheses about distributional structure, and quantify the uncertainty inherent in these conclusions. This reversal transforms statistical inference into an inverse problem, inherently ill-posed without additional structural assumptions.

The foundational invariant distinguishing inference from pure probability is the asymmetry of information. Nature selects a true parameter $\theta_0$ from a parameter space $\Theta$ and generates observations $X_1, X_2, \ldots, X_n$ according to a probability model $P_{\theta_0}$. The statistician observes only the data and must reverse-engineer $\theta_0$ or properties thereof. This epistemic asymmetry demands a shift from deductive certainty to inductive reasoning under uncertainty, where conclusions carry probabilistic guarantees conditional on the assumed model.

The model itself constitutes a critical assumption: we postulate a parametric family $\{P_\theta : \theta \in \Theta\}$ of probability distributions and assume the true data-generating process belongs to this family. This model specification encodes both structural knowledge and ignorance. A Gaussian location model $X_i \sim \mathcal{N}(\mu, \sigma^2)$ with unknown $\mu$ encodes the belief that data scatter symmetrically around a central value with exponentially decaying tails, but remains agnostic about $\mu$ itself. Model misspecification—when the true distribution lies outside the postulated family—represents the most catastrophic failure mode in inference, often undetectable from data alone.

Within a correctly specified model, inference divides into three major frameworks: point estimation seeks a single best guess $\hat{\theta}(X_1, \ldots, X_n)$ for the true parameter; hypothesis testing adjudicates between competing model specifications through binary decisions; and interval estimation constructs regions $C(X_1, \ldots, X_n)$ containing $\theta_0$ with specified probability. These frameworks interconnect through duality relationships—confidence intervals invert hypothesis tests, and likelihood ratios unify both—but diverge in their operational criteria and philosophical underpinnings.

The efficiency frontier of inference is governed by information geometry. Fisher information quantifies the rate at which log-likelihood curvature accumulates with sample size, measuring how sharply the data discriminate between nearby parameter values. For a scalar parameter $\theta$ and likelihood $L(\theta; X) = f(X; \theta)$, the Fisher information is defined as

$$I(\theta) = \mathbb{E}_\theta\left[\left(\frac{\partial}{\partial\theta} \log f(X; \theta)\right)^2\right] = -\mathbb{E}_\theta\left[\frac{\partial^2}{\partial\theta^2} \log f(X; \theta)\right],$$

where the equality follows from differentiating the identity $\int f(x; \theta) \, dx = 1$ under regularity conditions. High Fisher information implies steep likelihood gradients, enabling precise parameter localization from finite data. The Cramér-Rao inequality establishes Fisher information as the universal lower bound for estimator variance, asserting that no unbiased estimator can concentrate faster than $1/I(\theta)$ around the true value.

Sufficiency provides the algebraic mechanism for lossless data compression. A statistic $T(X_1, \ldots, X_n)$ is sufficient for $\theta$ if the conditional distribution of data given $T$ does not depend on $\theta$, formalized by the factorization theorem: $T$ is sufficient if and only if the joint density factors as $f(x_1, \ldots, x_n; \theta) = g(T(x_1, \ldots, x_n); \theta) h(x_1, \ldots, x_n)$, where $h$ is parameter-free. Sufficiency guarantees that $T$ captures all inferential information about $\theta$, allowing the raw data to be discarded without loss. The sample mean $\bar{X} = n^{-1}\sum_{i=1}^n X_i$ is sufficient for the mean of a Gaussian distribution, collapsing $n$ observations into a single number without sacrificing inference quality.

The transition from finite-sample theory to asymptotic approximation unlocks computational tractability. As sample size $n \to \infty$, maximum likelihood estimators converge to Gaussian distributions centered at the true parameter with variance determined by Fisher information, enabling confidence interval construction and hypothesis test calibration through standardization. Asymptotic normality transforms exact small-sample distributions—often intractable special functions—into universally accessible Gaussian approximations, though finite-sample performance requires careful validation through simulation or exact methods.

## 2. Core Architecture & Mechanics

Point estimation transforms data into a single numerical summary $\hat{\theta}$ intended to approximate the true parameter $\theta_0$. The method of moments exploits population moment equations by substituting sample moments for their theoretical counterparts. For a distribution parameterized by $\theta$, the population moment equations $\mathbb{E}_\theta[X^k] = m_k(\theta)$ relate moments to parameters. The method of moments estimator solves the empirical moment equations $n^{-1}\sum_{i=1}^n X_i^k = m_k(\hat{\theta})$ for $\hat{\theta}$.

Consider the Gamma distribution $X \sim \text{Gamma}(\alpha, \beta)$ with density $f(x; \alpha, \beta) = \frac{\beta^\alpha}{\Gamma(\alpha)} x^{\alpha-1} e^{-\beta x}$ for $x > 0$. The population moments are $\mathbb{E}[X] = \alpha/\beta$ and $\text{Var}(X) = \alpha/\beta^2$. Setting sample mean $\bar{X} = \alpha/\beta$ and sample variance $S^2 = \alpha/\beta^2$ yields the method of moments estimators

$$\hat{\alpha} = \frac{\bar{X}^2}{S^2}, \quad \hat{\beta} = \frac{\bar{X}}{S^2}.$$

This approach is computationally trivial—requiring only sample moments—but sacrifices efficiency by ignoring higher-order distributional structure.

Maximum likelihood estimation (MLE) instead seeks the parameter value maximizing the probability of observing the realized data. For independent observations $X_1, \ldots, X_n$ with joint density $f(x_1, \ldots, x_n; \theta) = \prod_{i=1}^n f(x_i; \theta)$, the likelihood function $L(\theta; x_1, \ldots, x_n) = \prod_{i=1}^n f(x_i; \theta)$ measures the model's predictive accuracy for each $\theta$. The maximum likelihood estimator maximizes this function:

$$\hat{\theta}_{\text{MLE}} = \arg\max_{\theta \in \Theta} L(\theta; X_1, \ldots, X_n).$$

Equivalently, since logarithm is monotone, we maximize the log-likelihood $\ell(\theta) = \sum_{i=1}^n \log f(X_i; \theta)$, converting products to sums and exponentials to polynomials.

For the Gaussian location model $X_i \sim \mathcal{N}(\mu, \sigma^2)$ with known variance $\sigma^2$, the log-likelihood is

$$\ell(\mu) = -\frac{n}{2} \log(2\pi\sigma^2) - \frac{1}{2\sigma^2} \sum_{i=1}^n (X_i - \mu)^2.$$

Differentiating with respect to $\mu$ yields

$$\frac{\partial \ell}{\partial \mu} = \frac{1}{\sigma^2} \sum_{i=1}^n (X_i - \mu).$$

Setting this equal to zero gives $\hat{\mu}_{\text{MLE}} = n^{-1}\sum_{i=1}^n X_i = \bar{X}$, the sample mean. The second derivative $\frac{\partial^2 \ell}{\partial \mu^2} = -n/\sigma^2 < 0$ confirms this is a maximum. The observed Fisher information is $I_n(\mu) = n/\sigma^2$, growing linearly with sample size.

For the Gaussian scale model $X_i \sim \mathcal{N}(0, \sigma^2)$ with known zero mean, the log-likelihood is

$$\ell(\sigma^2) = -\frac{n}{2} \log(2\pi\sigma^2) - \frac{1}{2\sigma^2} \sum_{i=1}^n X_i^2.$$

Differentiating with respect to $\sigma^2$ yields

$$\frac{\partial \ell}{\partial \sigma^2} = -\frac{n}{2\sigma^2} + \frac{1}{2(\sigma^2)^2} \sum_{i=1}^n X_i^2.$$

Setting this to zero gives $\hat{\sigma}^2_{\text{MLE}} = n^{-1}\sum_{i=1}^n X_i^2$. Note this is the sample average of squared observations, not the sample variance formula $S^2 = (n-1)^{-1}\sum_{i=1}^n (X_i - \bar{X})^2$. The MLE utilizes the known zero mean, whereas $S^2$ estimates the mean simultaneously.

When both $\mu$ and $\sigma^2$ are unknown in $X_i \sim \mathcal{N}(\mu, \sigma^2)$, the log-likelihood becomes

$$\ell(\mu, \sigma^2) = -\frac{n}{2} \log(2\pi) - \frac{n}{2} \log(\sigma^2) - \frac{1}{2\sigma^2} \sum_{i=1}^n (X_i - \mu)^2.$$

Differentiating and setting to zero yields $\hat{\mu}_{\text{MLE}} = \bar{X}$ and $\hat{\sigma}^2_{\text{MLE}} = n^{-1}\sum_{i=1}^n (X_i - \bar{X})^2$, the biased sample variance.

Estimator quality is formalized through four fundamental properties. An estimator $\hat{\theta}$ is unbiased if $\mathbb{E}_\theta[\hat{\theta}] = \theta$ for all $\theta \in \Theta$, ensuring no systematic error. The sample mean $\bar{X}$ for Gaussian location is unbiased since $\mathbb{E}[\bar{X}] = n^{-1}\sum_{i=1}^n \mathbb{E}[X_i] = \mu$. The MLE for Gaussian variance $\hat{\sigma}^2_{\text{MLE}} = n^{-1}\sum_{i=1}^n (X_i - \bar{X})^2$ is biased downward: by the chi-squared distribution theory, $(n-1)S^2/\sigma^2 \sim \chi^2_{n-1}$, so $\mathbb{E}[\hat{\sigma}^2_{\text{MLE}}] = \frac{n-1}{n}\sigma^2 \neq \sigma^2$. The bias correction factor $(n-1)/n$ reflects the loss of one degree of freedom from estimating $\mu$.

Consistency requires convergence to the true parameter as sample size grows: $\hat{\theta}_n \xrightarrow{P} \theta_0$ as $n \to \infty$. The weak law of large numbers guarantees $\bar{X} \to \mu$ in probability for the Gaussian location model. The MLE is consistent under regularity conditions through the law of large numbers applied to the score function: the true parameter maximizes expected log-likelihood, and sample approximations converge uniformly.

Efficiency measures variance among unbiased estimators. An unbiased estimator is efficient if it attains the Cramér-Rao lower bound. The Cramér-Rao inequality asserts that for any unbiased estimator $\hat{\theta}$ of $\theta$,

$$\text{Var}_\theta(\hat{\theta}) \geq \frac{1}{n I(\theta)},$$

where $I(\theta)$ is the Fisher information per observation. The proof employs the Cauchy-Schwarz inequality on the covariance between $\hat{\theta}$ and the score function $U(\theta) = \frac{\partial}{\partial\theta} \log f(X; \theta)$. Under regularity, $\mathbb{E}_\theta[U(\theta)] = 0$, and

$$\text{Cov}(\hat{\theta}, U(\theta)) = \mathbb{E}_\theta[\hat{\theta} U(\theta)] - \mathbb{E}_\theta[\hat{\theta}] \mathbb{E}_\theta[U(\theta)] = \mathbb{E}_\theta[\hat{\theta} U(\theta)].$$

By the chain rule applied to $\mathbb{E}_\theta[\hat{\theta}] = \theta$,

$$\frac{\partial}{\partial\theta} \mathbb{E}_\theta[\hat{\theta}] = 1 = \mathbb{E}_\theta\left[\hat{\theta} \frac{\partial}{\partial\theta} \log f(X; \theta)\right] = \mathbb{E}_\theta[\hat{\theta} U(\theta)],$$

so $\text{Cov}(\hat{\theta}, U(\theta)) = 1$. The Cauchy-Schwarz inequality gives

$$1 = |\text{Cov}(\hat{\theta}, U(\theta))|^2 \leq \text{Var}(\hat{\theta}) \cdot \text{Var}(U(\theta)) = \text{Var}(\hat{\theta}) \cdot I(\theta),$$

yielding $\text{Var}(\hat{\theta}) \geq 1/I(\theta)$. For $n$ independent observations, $I_n(\theta) = n I(\theta)$, giving the Cramér-Rao bound $\text{Var}(\hat{\theta}) \geq 1/(n I(\theta))$.

The sample mean $\bar{X}$ for Gaussian location achieves this bound: $\text{Var}(\bar{X}) = \sigma^2/n$ and $I(\mu) = 1/\sigma^2$, so $\text{Var}(\bar{X}) = 1/(n I(\mu))$. Efficient estimators saturate the information-theoretic limit, extracting maximal information from data.

Sufficiency compresses data without information loss. The Neyman factorization theorem provides the operational characterization: $T(X_1, \ldots, X_n)$ is sufficient for $\theta$ if and only if the joint density factors as

$$f(x_1, \ldots, x_n; \theta) = g(T(x_1, \ldots, x_n); \theta) \cdot h(x_1, \ldots, x_n),$$

where $g$ depends on $\theta$ and $T$ while $h$ is parameter-free. For the Gaussian location model $X_i \sim \mathcal{N}(\mu, \sigma^2)$ with known $\sigma^2$, the joint density is

$$f(x_1, \ldots, x_n; \mu) = \prod_{i=1}^n \frac{1}{\sqrt{2\pi\sigma^2}} \exp\left(-\frac{(x_i - \mu)^2}{2\sigma^2}\right) = \left(\frac{1}{2\pi\sigma^2}\right)^{n/2} \exp\left(-\frac{\sum_{i=1}^n (x_i - \mu)^2}{2\sigma^2}\right).$$

Expanding the exponent gives

$$\sum_{i=1}^n (x_i - \mu)^2 = \sum_{i=1}^n x_i^2 - 2\mu \sum_{i=1}^n x_i + n\mu^2 = \sum_{i=1}^n x_i^2 - 2n\mu\bar{x} + n\mu^2,$$

where $\bar{x} = n^{-1}\sum_{i=1}^n x_i$. Grouping terms involving $\mu$ yields

$$f(x_1, \ldots, x_n; \mu) = \exp\left(-\frac{n(\bar{x} - \mu)^2}{2\sigma^2}\right) \cdot \left(\frac{1}{2\pi\sigma^2}\right)^{n/2} \exp\left(-\frac{\sum_{i=1}^n x_i^2 - n\bar{x}^2}{2\sigma^2}\right).$$

The first factor depends on $\mu$ and $\bar{x}$ only; the second is parameter-free. Thus $T(X_1, \ldots, X_n) = \bar{X}$ is sufficient, compressing $n$ observations into a single number without losing inferential content about $\mu$.

The Rao-Blackwell theorem strengthens sufficiency's role: any unbiased estimator can be improved by conditioning on a sufficient statistic. If $\hat{\theta}$ is unbiased for $\theta$ and $T$ is sufficient, then $\tilde{\theta} = \mathbb{E}[\hat{\theta} \mid T]$ is also unbiased and has variance no larger than $\hat{\theta}$. The proof follows from the law of total variance:

$$\text{Var}(\hat{\theta}) = \mathbb{E}[\text{Var}(\hat{\theta} \mid T)] + \text{Var}(\mathbb{E}[\hat{\theta} \mid T]) \geq \text{Var}(\tilde{\theta}),$$

since the first term is non-negative. Minimal sufficient statistics—those coarsest among all sufficient statistics—represent maximal data compression.

Hypothesis testing shifts from estimation to binary decision-making. A null hypothesis $H_0$ specifies a restricted parameter set $\Theta_0 \subset \Theta$, while the alternative $H_1$ corresponds to $\Theta_1 = \Theta \setminus \Theta_0$. A test partitions the sample space into rejection region $R$ and acceptance region $R^c$, rejecting $H_0$ if $(X_1, \ldots, X_n) \in R$. Type I error occurs when $H_0$ is true but we reject; Type II error occurs when $H_1$ is true but we accept. The significance level $\alpha = \sup_{\theta \in \Theta_0} P_\theta(R)$ bounds Type I error probability, while power $\beta(\theta) = P_\theta(R)$ for $\theta \in \Theta_1$ measures ability to detect alternatives.

The Neyman-Pearson lemma solves the test design problem for simple hypotheses: when testing $H_0: \theta = \theta_0$ against $H_1: \theta = \theta_1$, the likelihood ratio test (LRT) maximizes power at level $\alpha$. The LRT rejects $H_0$ when

$$\Lambda(x_1, \ldots, x_n) = \frac{f(x_1, \ldots, x_n; \theta_1)}{f(x_1, \ldots, x_n; \theta_0)} > c,$$

where $c$ is chosen so $P_{\theta_0}(\Lambda > c) = \alpha$. The proof uses the fundamental lemma: for any other test with rejection region $R'$ satisfying $P_{\theta_0}(R') \leq \alpha$, if $\Lambda(x) > c$ implies $x \in R$ and $\Lambda(x) < c$ implies $x \notin R$, then

$$P_{\theta_1}(R) - P_{\theta_1}(R') = \int_{R \setminus R'} f(x; \theta_1) \, dx - \int_{R' \setminus R} f(x; \theta_1) \, dx.$$

On $R \setminus R'$, $\Lambda(x) > c$ implies $f(x; \theta_1) > c f(x; \theta_0)$, so

$$\int_{R \setminus R'} f(x; \theta_1) \, dx > c \int_{R \setminus R'} f(x; \theta_0) \, dx.$$

Similarly, on $R' \setminus R$, $\Lambda(x) < c$ implies

$$\int_{R' \setminus R} f(x; \theta_1) \, dx < c \int_{R' \setminus R} f(x; \theta_0) \, dx.$$

The level constraint $P_{\theta_0}(R') \leq \alpha = P_{\theta_0}(R)$ gives

$$\int_{R' \setminus R} f(x; \theta_0) \, dx \leq \int_{R \setminus R'} f(x; \theta_0) \, dx,$$

so $P_{\theta_1}(R) - P_{\theta_1}(R') \geq 0$, proving the LRT is most powerful.

For composite hypotheses, the generalized likelihood ratio test (GLRT) compares maximum likelihoods under null and full parameter spaces:

$$\Lambda_{\text{GLRT}} = \frac{\sup_{\theta \in \Theta_0} L(\theta; X_1, \ldots, X_n)}{\sup_{\theta \in \Theta} L(\theta; X_1, \ldots, X_n)}.$$

Under $H_0$, the asymptotic distribution of $-2 \log \Lambda_{\text{GLRT}}$ is chi-squared with degrees of freedom equal to $\dim(\Theta) - \dim(\Theta_0)$, provided regularity conditions hold. This result, due to Wilks, enables asymptotic calibration of composite tests through chi-squared quantiles.

The $p$-value quantifies evidence against $H_0$ as the smallest significance level at which the observed data would lead to rejection. For test statistic $T(X_1, \ldots, X_n)$ with larger values indicating greater evidence against $H_0$, the $p$-value is

$$p = \sup_{\theta \in \Theta_0} P_\theta(T(X_1, \ldots, X_n) \geq T_{\text{obs}}),$$

where $T_{\text{obs}}$ is the observed statistic value. A $p$-value of $0.03$ means that if $H_0$ were true, data at least as extreme as observed would occur with probability $0.03$. Low $p$-values indicate incompatibility between data and null hypothesis, though they do not measure the probability that $H_0$ is true—a common misinterpretation. The $p$-value is a random variable uniform on $[0, 1]$ when $H_0$ holds, ensuring proper Type I error control.

Confidence intervals invert hypothesis tests to produce parameter ranges consistent with data. A $1 - \alpha$ confidence interval is a random set $C(X_1, \ldots, X_n)$ satisfying

$$P_\theta(\theta \in C(X_1, \ldots, X_n)) \geq 1 - \alpha \quad \text{for all } \theta \in \Theta.$$

The coverage probability is computed over the sampling distribution of data, not over $\theta$. Once data are observed, $\theta$ either lies in $C$ or not—the probability refers to the procedure's long-run frequency properties.

For Gaussian location $X_i \sim \mathcal{N}(\mu, \sigma^2)$ with known $\sigma^2$, the standardized sample mean $Z = \frac{\bar{X} - \mu}{\sigma/\sqrt{n}} \sim \mathcal{N}(0, 1)$ has distribution independent of $\mu$. A $1 - \alpha$ confidence interval for $\mu$ is

$$C = \left[\bar{X} - z_{\alpha/2} \frac{\sigma}{\sqrt{n}}, \bar{X} + z_{\alpha/2} \frac{\sigma}{\sqrt{n}}\right],$$

where $z_{\alpha/2}$ is the $(1 - \alpha/2)$-quantile of the standard normal. The coverage is exact:

$$P_\mu(\mu \in C) = P_\mu\left(|\bar{X} - \mu| \leq z_{\alpha/2} \frac{\sigma}{\sqrt{n}}\right) = P\left(|Z| \leq z_{\alpha/2}\right) = 1 - \alpha.$$

When $\sigma^2$ is unknown, $Z$ is replaced by the $t$-statistic $T = \frac{\bar{X} - \mu}{S/\sqrt{n}}$, where $S^2 = (n-1)^{-1}\sum_{i=1}^n (X_i - \bar{X})^2$. Under Gaussianity, $T \sim t_{n-1}$, the $t$-distribution with $n-1$ degrees of freedom, yielding the confidence interval

$$C = \left[\bar{X} - t_{n-1, \alpha/2} \frac{S}{\sqrt{n}}, \bar{X} + t_{n-1, \alpha/2} \frac{S}{\sqrt{n}}\right].$$

Asymptotic theory replaces exact finite-sample distributions with large-$n$ Gaussian approximations. The central limit theorem (CLT) asserts that for independent identically distributed $X_i$ with mean $\mu$ and variance $\sigma^2 < \infty$,

$$\frac{\sqrt{n}(\bar{X} - \mu)}{\sigma} \xrightarrow{d} \mathcal{N}(0, 1) \quad \text{as } n \to \infty.$$

The convergence is in distribution: cumulative distribution functions converge pointwise at continuity points. The CLT requires no distributional specification beyond finite variance, providing universal Gaussian approximation for standardized averages.

For maximum likelihood estimators, asymptotic normality follows from Taylor expansion of the score function around the true parameter. Under regularity—continuous derivatives, parameter identifiability, and Fisher information positivity—the MLE satisfies

$$\sqrt{n}(\hat{\theta}_{\text{MLE}} - \theta_0) \xrightarrow{d} \mathcal{N}\left(0, \frac{1}{I(\theta_0)}\right).$$

The asymptotic variance attains the Cramér-Rao bound, establishing MLE asymptotic efficiency. The proof expands the score evaluated at the MLE:

$$0 = \frac{\partial \ell}{\partial \theta}\Big|_{\hat{\theta}_{\text{MLE}}} = \frac{\partial \ell}{\partial \theta}\Big|_{\theta_0} + \frac{\partial^2 \ell}{\partial \theta^2}\Big|_{\theta_0} (\hat{\theta}_{\text{MLE}} - \theta_0) + o_P(1).$$

The first term $U_n(\theta_0) = \frac{\partial \ell}{\partial \theta}\Big|_{\theta_0} = \sum_{i=1}^n U(\theta_0; X_i)$ is a sum of independent score functions with mean zero and variance $n I(\theta_0)$, so $U_n(\theta_0)/\sqrt{n} \xrightarrow{d} \mathcal{N}(0, I(\theta_0))$ by the CLT. The second term $\frac{\partial^2 \ell}{\partial \theta^2}\Big|_{\theta_0} = \sum_{i=1}^n \frac{\partial^2}{\partial \theta^2} \log f(X_i; \theta_0)$ converges by the law of large numbers to $-n I(\theta_0)$. Rearranging gives

$$\sqrt{n}(\hat{\theta}_{\text{MLE}} - \theta_0) = -\left(n^{-1} \frac{\partial^2 \ell}{\partial \theta^2}\Big|_{\theta_0}\right)^{-1} \frac{U_n(\theta_0)}{\sqrt{n}} \xrightarrow{d} \mathcal{N}\left(0, \frac{1}{I(\theta_0)}\right).$$

The delta method extends asymptotic normality to transformations. If $\sqrt{n}(\hat{\theta} - \theta_0) \xrightarrow{d} \mathcal{N}(0, \sigma^2)$ and $g$ is differentiable at $\theta_0$ with $g'(\theta_0) \neq 0$, then

$$\sqrt{n}(g(\hat{\theta}) - g(\theta_0)) \xrightarrow{d} \mathcal{N}(0, \sigma^2 [g'(\theta_0)]^2).$$

The proof applies the Taylor expansion $g(\hat{\theta}) - g(\theta_0) \approx g'(\theta_0)(\hat{\theta} - \theta_0)$ combined with Slutsky's theorem for products of convergent sequences.

## 3. High-Performance Optimization & Failure Modes

Numerical optimization of likelihood functions encounters multiple stability and convergence challenges. The log-likelihood surface may exhibit multimodality, flat plateaus, or unbounded regions, defeating standard optimization algorithms. For mixture models like $f(x; \theta) = \sum_{k=1}^K \pi_k \mathcal{N}(x; \mu_k, \sigma_k^2)$, the likelihood is invariant under label permutations, creating $K!$ equivalent global maxima. Initialization near a saddle point or local maximum traps gradient-based optimizers. The expectation-maximization (EM) algorithm exploits latent variable structure to monotonically increase likelihood via alternating expectation and maximization steps, guaranteeing convergence to a stationary point though not necessarily the global maximum.

Numerical precision limits afflict likelihood computations when densities span orders of magnitude. For large $n$, products $\prod_{i=1}^n f(x_i; \theta)$ underflow to zero in finite-precision arithmetic. Log-likelihood $\ell(\theta) = \sum_{i=1}^n \log f(x_i; \theta)$ avoids this by summing log-densities, but care is required when densities involve exponentials. The log-sum-exp trick stabilizes computations like $\log\left(\sum_{k=1}^K e^{a_k}\right)$ by factoring the maximum: $\log\left(e^{a_{\max}}\sum_{k=1}^K e^{a_k - a_{\max}}\right) = a_{\max} + \log\left(\sum_{k=1}^K e^{a_k - a_{\max}}\right)$, preventing overflow and underflow simultaneously.

Hypothesis test calibration failures arise from violated distributional assumptions. The $t$-test assumes Gaussian data; heavy-tailed distributions inflate Type I error rates beyond the nominal level $\alpha$. For $n = 10$ observations from a Cauchy distribution, the $t$-test with $\alpha = 0.05$ may reject $H_0$ with empirical frequency $0.15$, tripling the intended error rate. Robustness to model misspecification motivates nonparametric and permutation tests that replace distributional assumptions with weaker invariance conditions.

The $p$-value's Uniform$[0, 1]$ distribution under the null hypothesis is exact only when test statistics have continuous distributions. For discrete test statistics, the $p$-value distribution is stochastically larger than uniform, making tests conservative. For example, testing $H_0: p = 0.5$ in a binomial experiment with $n = 10$ trials using the test statistic $T = \sum_{i=1}^{10} X_i$, the smallest achievable $p$-value is $2 P(T \geq 10) = 2 \cdot 2^{-10} \approx 0.002$. No observed data can produce $p = 0.001$, so the test rejects at level $\alpha = 0.001$ with probability zero, sacrificing power.

Confidence interval coverage degradation under model misspecification manifests asymmetrically. When constructing intervals for Gaussian mean $\mu$ but data are skewed with skewness $\gamma_1 \neq 0$, the nominal $95\%$ interval $[\bar{X} - 1.96 S/\sqrt{n}, \bar{X} + 1.96 S/\sqrt{n}]$ may cover $\mu$ with empirical frequency $0.92$ or $0.97$ depending on skewness sign. The CLT guarantees asymptotic coverage as $n \to \infty$, but finite-sample behavior requires higher-order corrections like the Edgeworth expansion, which adjusts Gaussian quantiles by $O(n^{-1/2})$ terms involving skewness and kurtosis.

Multiple testing inflates family-wise error rates through repeated hypothesis tests. Testing $m$ independent null hypotheses at level $\alpha$ each, the probability of at least one Type I error is $1 - (1 - \alpha)^m \approx m\alpha$ for small $\alpha$. For $m = 100$ and $\alpha = 0.05$, the family-wise error rate reaches $0.994$, virtually guaranteeing false discoveries. The Bonferroni correction controls family-wise error by testing each hypothesis at level $\alpha/m$, ensuring $P(\text{at least one Type I error}) \leq m \cdot \frac{\alpha}{m} = \alpha$. However, Bonferroni is conservative when tests are dependent or when controlling the false discovery rate—expected proportion of false discoveries among rejections—is more appropriate than family-wise error control.

Sample size calculations balance statistical power against resource constraints. For testing $H_0: \mu = \mu_0$ against $H_1: \mu = \mu_1$ in the Gaussian location model with known $\sigma^2$ at level $\alpha$ and desired power $1 - \beta$, the required sample size satisfies

$$n = \left(\frac{z_{\alpha/2} + z_\beta}{\mu_1 - \mu_0}\right)^2 \sigma^2.$$

The numerator $z_{\alpha/2} + z_\beta$ balances Type I and Type II error quantiles, while the denominator scales inversely with effect size $\mu_1 - \mu_0$. Detecting a one standard deviation shift ($\mu_1 - \mu_0 = \sigma$) with $\alpha = 0.05$ and $\beta = 0.20$ requires $n \approx (1.96 + 0.84)^2 \approx 7.85$, so $n = 8$ observations suffice. Halving the effect size quadruples the required sample size, illustrating the steep cost of detecting subtle differences.

Bootstrap resampling provides distribution-free uncertainty quantification when analytic variance formulas are intractable. Given data $X_1, \ldots, X_n$ and estimator $\hat{\theta}$, the bootstrap generates $B$ resamples by drawing $n$ observations with replacement from the empirical distribution, computing $\hat{\theta}^{(b)}$ for each resample $b = 1, \ldots, B$. The bootstrap variance estimator is $\widehat{\text{Var}}(\hat{\theta}) = (B-1)^{-1}\sum_{b=1}^B (\hat{\theta}^{(b)} - \bar{\theta}^*)^2$, where $\bar{\theta}^* = B^{-1}\sum_{b=1}^B \hat{\theta}^{(b)}$. Bootstrap percentile confidence intervals use quantiles of $\{\hat{\theta}^{(b)}\}$: the $1 - \alpha$ interval is $[\hat{\theta}^{(\alpha/2 \cdot B)}, \hat{\theta}^{((1-\alpha/2) \cdot B)}]$ after sorting. The bootstrap is consistent for smooth functionals under mild regularity, though extreme quantiles and non-smooth estimators require more sophisticated techniques like the $m$-out-of-$n$ bootstrap or subsampling.

Bayesian inference offers an alternative paradigm by treating parameters as random variables. Prior distribution $\pi(\theta)$ encodes initial beliefs; the likelihood $L(\theta; x_1, \ldots, x_n)$ updates these via Bayes' theorem to the posterior distribution:

$$\pi(\theta \mid x_1, \ldots, x_n) = \frac{L(\theta; x_1, \ldots, x_n) \pi(\theta)}{\int_\Theta L(\theta; x_1, \ldots, x_n) \pi(\theta) \, d\theta}.$$

Posterior intervals quantify parameter uncertainty directly as probability statements: $P(\theta \in [a, b] \mid x_1, \ldots, x_n) = \int_a^b \pi(\theta \mid x_1, \ldots, x_n) \, d\theta$. The posterior mean $\mathbb{E}[\theta \mid x_1, \ldots, x_n]$ minimizes posterior expected squared error, while the posterior mode (maximum a posteriori, MAP) generalizes the MLE by incorporating prior information. Bayesian credible intervals have direct probabilistic interpretation unlike frequentist confidence intervals, but require specifying priors—a contentious choice in objective settings.

The Bernstein-von Mises theorem bridges Bayesian and frequentist asymptotics: under regularity, the posterior distribution concentrates around the MLE with Gaussian shape matching the inverse Fisher information. For large $n$, Bayesian and frequentist intervals coincide asymptotically, though finite-sample behavior depends critically on prior specification. Improper priors—unnormalized densities like $\pi(\mu) \propto 1$—enable objective Bayesian inference but may yield improper posteriors or paradoxes in hierarchical models.

Empirical Bayes estimation compromises between full Bayesian modeling and purely frequentist approaches by estimating hyperparameters from data. For hierarchical model $X_i \mid \theta_i \sim f(x; \theta_i)$ and prior $\theta_i \sim \pi(\theta; \lambda)$, the marginal distribution $m(x; \lambda) = \int f(x; \theta) \pi(\theta; \lambda) \, d\theta$ depends on hyperparameter $\lambda$. Empirical Bayes substitutes MLE $\hat{\lambda}$ obtained by maximizing $\prod_{i=1}^n m(X_i; \lambda)$, then computes posteriors using $\pi(\theta; \hat{\lambda})$. This hybrid approach inherits frequentist optimality properties while leveraging Bayesian shrinkage, though it underestimates posterior uncertainty by treating $\hat{\lambda}$ as fixed rather than random.

Sequential analysis and stopping rules violate fixed-sample theory's independence assumptions, inflating Type I error when data collection continues until significance is achieved. Optional stopping without correction—performing interim analyses and stopping when $p < \alpha$—can inflate actual Type I error arbitrarily. The sequential probability ratio test (SPRT) addresses this by computing likelihood ratios at each stage and stopping when thresholds corresponding to desired error probabilities are crossed, maintaining exact error control. Group sequential designs for clinical trials specify a finite number of interim analyses with adjusted critical values from alpha spending functions, balancing early stopping benefits against multiple testing penalties.

Variance estimation for complex survey designs requires accounting for stratification, clustering, and unequal sampling weights. The naive variance formula $S^2/n$ ignores design structure, underestimating true standard errors and yielding liberal confidence intervals. Design-based variance estimators like the Taylor linearization method or replicate variance estimation (jackknife, bootstrap, balanced repeated replication) properly reflect sampling variability. Survey software packages implement these adjustments, though analysts must correctly specify design variables.

Measurement error and missing data introduce bias and efficiency loss. When covariates are measured with error—$W_i = X_i + U_i$ with $U_i$ independent noise—regression coefficients are attenuated toward zero by factor $\sigma^2_X/(\sigma^2_X + \sigma^2_U)$, where $\sigma^2_X$ and $\sigma^2_U$ are signal and noise variances. Simulation extrapolation (SIMEX) estimates this attenuation by artificially inflating measurement error in bootstrap replicates and extrapolating to the zero-error limit. Missing data mechanisms—missing completely at random (MCAR), missing at random (MAR), and missing not at random (MNAR)—determine whether complete-case analysis is unbiased. Multiple imputation generates $M$ completed datasets by filling missing values from their posterior predictive distribution, analyzes each separately, and combines results via Rubin's rules to account for both within- and between-imputation variability.

Computational scaling for massive datasets exploits stochastic gradient methods and data sketching. Standard MLE requires computing full-sample log-likelihood gradients at each iteration, scaling linearly in $n$. Stochastic gradient descent (SGD) approximates gradients using mini-batches of size $b \ll n$, reducing iteration cost from $O(n)$ to $O(b)$ while introducing noise that typically accelerates early optimization. Variance reduction techniques like SVRG (stochastic variance reduced gradient) interpolate between full-gradient stability and stochastic efficiency. Core-set constructions distill large datasets into weighted subsamples of size $O(\varepsilon^{-1} d \log d)$—where $d$ is parameter dimension—such that MLE on the core-set approximates the full-data MLE within $\varepsilon$ relative error. These geometric summarizations enable inference on billion-scale datasets using commodity hardware.

The interplay between statistical efficiency and computational complexity defines modern inference's practical frontier. Exact finite-sample optimality—maximizing power subject to error constraints—yields intractable tests for all but the simplest models. Asymptotic approximations trade finite-sample guarantees for computational feasibility, with error bounds of order $O(n^{-1/2})$ or $O(n^{-1})$ from higher-order expansions. Understanding when asymptotic regimes apply—requiring sample sizes ranging from tens to thousands depending on distributional tail behavior—separates successful applied inference from ritual misapplication of formulas divorced from underlying assumptions.
