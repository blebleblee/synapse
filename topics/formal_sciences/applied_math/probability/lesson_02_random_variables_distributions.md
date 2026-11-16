# Lesson 2: Random Variables, Distributions, Transformations

## 1. First-Principles Intuition & Invariants

The notion of a random variable sits at the conceptual boundary between the abstract machinery of probability theory—sigma-algebras, measurable spaces, and probability measures—and the concrete numerical outcomes we observe in experiments, simulations, and computational models. In Lesson 1, we established that a probability space $(\Omega, \mathcal{F}, P)$ provides the foundational substrate: $\Omega$ enumerates all possible outcomes, $\mathcal{F}$ identifies which collections of outcomes are measurable, and $P$ assigns probabilities to these measurable events. Yet in practice, we rarely manipulate raw outcomes directly. Instead, we extract numerical summaries, compute expectations, and reason about the distributions of derived quantities.

A random variable is the formal mechanism that bridges this gap. Mathematically, a random variable $X$ is a measurable function $X : \Omega \to \mathbb{R}$ that maps each outcome $\omega \in \Omega$ to a real number $X(\omega)$. The measurability condition demands that for every Borel set $B \subseteq \mathbb{R}$, the preimage $X^{-1}(B) = \{\omega \in \Omega : X(\omega) \in B\}$ belongs to the sigma-algebra $\mathcal{F}$, ensuring we can meaningfully compute probabilities such as $P(X \in B)$. This construction is not merely pedantic formalism—it guarantees that the pushforward measure $P_X$ induced on $\mathbb{R}$ by $X$ is well-defined, and it is this induced distribution that we manipulate when computing expectations, variances, and moment generating functions.

The distinction between discrete and continuous random variables emerges from the structure of their supports and the nature of their induced distributions. A discrete random variable $X$ assumes values in a countable subset of $\mathbb{R}$, and its distribution is fully characterized by a probability mass function (PMF) $p_X(x) = P(X = x)$. The PMF concentrates probability on isolated points, and sums over the support yield all probabilistic quantities of interest. In contrast, a continuous random variable possesses a probability density function (PDF) $f_X(x)$ such that $P(X \in [a,b]) = \int_a^b f_X(x) \, dx$. Individual points carry zero probability under continuous distributions—a consequence of the Lebesgue measure assigning zero mass to singleton sets—so we integrate over intervals rather than summing over points.

The cumulative distribution function (CDF) $F_X(x) = P(X \le x)$ provides a unified representation valid for both discrete and continuous cases, as well as for mixed or singular distributions. The CDF is always right-continuous, non-decreasing, with $\lim_{x \to -\infty} F_X(x) = 0$ and $\lim_{x \to \infty} F_X(x) = 1$. For discrete random variables, the CDF exhibits jump discontinuities at each point in the support, with jump heights equal to the PMF values. For continuous random variables, the CDF is absolutely continuous, and the Radon-Nikodym theorem guarantees that $f_X(x) = \frac{dF_X}{dx}(x)$ almost everywhere. This derivative relationship forms the backbone of transformation techniques: when we apply a transformation $Y = g(X)$ to a continuous random variable, we must account for how the density "stretches" or "compresses" under the change of variables, leading to the Jacobian factor in the derived PDF.

Expectation and variance, the first two moments of a distribution, quantify central tendency and dispersion. The expectation $\mathbb{E}[X]$ represents the probability-weighted average of $X$, but its rigorous definition as a Lebesgue-Stieltjes integral $\mathbb{E}[X] = \int_\mathbb{R} x \, dF_X(x)$ unifies discrete and continuous cases. For discrete $X$, this reduces to the sum $\sum_{x} x \cdot p_X(x)$, while for continuous $X$ it becomes the Lebesgue integral $\int_\mathbb{R} x \cdot f_X(x) \, dx$. The variance $\text{Var}(X) = \mathbb{E}[(X - \mathbb{E}[X])^2]$ measures the expected squared deviation from the mean, and the algebraic identity $\text{Var}(X) = \mathbb{E}[X^2] - (\mathbb{E}[X])^2$ simplifies computational efforts.

Moment generating functions (MGFs) encode the entire sequence of moments into a single analytic object. Defined as $M_X(t) = \mathbb{E}[e^{tX}]$, the MGF possesses the remarkable property that the $n$-th moment $\mathbb{E}[X^n]$ equals the $n$-th derivative $M_X^{(n)}(0)$, provided the MGF exists in a neighborhood of the origin. The MGF also characterizes distributions uniquely—two random variables with identical MGFs in some interval around zero are identically distributed—and it transforms convolutions into products, rendering the MGF indispensable for proving limit theorems and computing distributions of sums of independent random variables.

Throughout this lesson, we maintain strict measure-theoretic rigor while emphasizing computational practicality. We derive PMFs and PDFs from first principles, compute expectations and variances through both direct integration and MGF differentiation, and execute change-of-variables transformations to obtain derived distributions. The interplay between abstract theory and concrete calculation forms the essential character of modern probability theory, and mastery of both dimensions is non-negotiable for practitioners working in statistical inference, stochastic simulation, and theoretical computer science.

## 2. Core Architecture & Mechanics

### Discrete Random Variables and Probability Mass Functions

A discrete random variable $X$ partitions the sample space $\Omega$ into countably many level sets $\{\omega : X(\omega) = x_i\}$ for $i = 1, 2, 3, \ldots$, where each $x_i$ belongs to the range of $X$. The probability mass function $p_X : \mathbb{R} \to [0,1]$ assigns to each value $x$ the probability $p_X(x) = P(X = x) = P(\{\omega \in \Omega : X(\omega) = x\})$. The PMF must satisfy two axioms: non-negativity $p_X(x) \ge 0$ for all $x$, and normalization $\sum_{x} p_X(x) = 1$, where the sum extends over the support $\text{supp}(X) = \{x : p_X(x) > 0\}$.

Consider the canonical example of a fair six-sided die. The sample space is $\Omega = \{1, 2, 3, 4, 5, 6\}$, the random variable $X$ is the identity map $X(\omega) = \omega$, and the PMF is $p_X(k) = 1/6$ for $k \in \{1, 2, 3, 4, 5, 6\}$. To compute the probability that the die shows an even number, we sum over the relevant points:

$$P(X \in \{2, 4, 6\}) = p_X(2) + p_X(4) + p_X(6) = \frac{1}{6} + \frac{1}{6} + \frac{1}{6} = \frac{1}{2}.$$

The expectation of a discrete random variable is the probability-weighted sum of its values:

$$\mathbb{E}[X] = \sum_{x \in \text{supp}(X)} x \cdot p_X(x).$$

For the fair die, this becomes

$$\mathbb{E}[X] = 1 \cdot \frac{1}{6} + 2 \cdot \frac{1}{6} + 3 \cdot \frac{1}{6} + 4 \cdot \frac{1}{6} + 5 \cdot \frac{1}{6} + 6 \cdot \frac{1}{6} = \frac{21}{6} = 3.5.$$

The second moment is

$$\mathbb{E}[X^2] = 1^2 \cdot \frac{1}{6} + 2^2 \cdot \frac{1}{6} + 3^2 \cdot \frac{1}{6} + 4^2 \cdot \frac{1}{6} + 5^2 \cdot \frac{1}{6} + 6^2 \cdot \frac{1}{6} = \frac{1 + 4 + 9 + 16 + 25 + 36}{6} = \frac{91}{6},$$

yielding the variance

$$\text{Var}(X) = \mathbb{E}[X^2] - (\mathbb{E}[X])^2 = \frac{91}{6} - \left(\frac{7}{2}\right)^2 = \frac{91}{6} - \frac{49}{4} = \frac{182 - 147}{12} = \frac{35}{12} \approx 2.917.$$

The Bernoulli distribution models a single binary trial with success probability $p$. The random variable $X$ takes the value $1$ with probability $p$ and $0$ with probability $1-p$, so the PMF is $p_X(1) = p$ and $p_X(0) = 1-p$. The expectation is

$$\mathbb{E}[X] = 0 \cdot (1-p) + 1 \cdot p = p,$$

and the second moment is $\mathbb{E}[X^2] = 0^2 \cdot (1-p) + 1^2 \cdot p = p$ since $X^2 = X$ for binary-valued $X$. Thus the variance is

$$\text{Var}(X) = p - p^2 = p(1-p).$$

The binomial distribution $\text{Binomial}(n, p)$ counts the number of successes in $n$ independent Bernoulli trials, each with success probability $p$. The PMF is

$$p_X(k) = \binom{n}{k} p^k (1-p)^{n-k}, \quad k = 0, 1, 2, \ldots, n.$$

The binomial coefficient $\binom{n}{k} = \frac{n!}{k!(n-k)!}$ enumerates the number of ways to choose $k$ successes among $n$ trials. The expectation and variance satisfy $\mathbb{E}[X] = np$ and $\text{Var}(X) = np(1-p)$, which can be derived by expressing $X$ as the sum $X = X_1 + X_2 + \cdots + X_n$ of independent Bernoulli random variables and applying linearity of expectation and the independence property for variance.

The Poisson distribution models the number of rare events occurring in a fixed interval when events happen independently at a constant average rate $\lambda$. The PMF is

$$p_X(k) = \frac{\lambda^k e^{-\lambda}}{k!}, \quad k = 0, 1, 2, \ldots$$

Normalization follows from the Taylor series $e^\lambda = \sum_{k=0}^\infty \frac{\lambda^k}{k!}$, which implies $\sum_{k=0}^\infty \frac{\lambda^k e^{-\lambda}}{k!} = e^{-\lambda} \cdot e^\lambda = 1$. The expectation is

$$\mathbb{E}[X] = \sum_{k=0}^\infty k \cdot \frac{\lambda^k e^{-\lambda}}{k!} = e^{-\lambda} \sum_{k=1}^\infty \frac{\lambda^k}{(k-1)!} = e^{-\lambda} \lambda \sum_{j=0}^\infty \frac{\lambda^j}{j!} = \lambda e^{-\lambda} \cdot e^\lambda = \lambda.$$

The second moment calculation begins with

$$\mathbb{E}[X^2] = \sum_{k=0}^\infty k^2 \cdot \frac{\lambda^k e^{-\lambda}}{k!} = \mathbb{E}[X(X-1)] + \mathbb{E}[X].$$

We compute

$$\mathbb{E}[X(X-1)] = \sum_{k=0}^\infty k(k-1) \cdot \frac{\lambda^k e^{-\lambda}}{k!} = e^{-\lambda} \sum_{k=2}^\infty \frac{\lambda^k}{(k-2)!} = e^{-\lambda} \lambda^2 \sum_{j=0}^\infty \frac{\lambda^j}{j!} = \lambda^2,$$

so $\mathbb{E}[X^2] = \lambda^2 + \lambda$, yielding variance $\text{Var}(X) = \lambda^2 + \lambda - \lambda^2 = \lambda$. The Poisson distribution exhibits the remarkable property that its mean and variance are equal, a diagnostic feature used in statistical model validation.

The cumulative distribution function for a discrete random variable is

$$F_X(x) = P(X \le x) = \sum_{x_i \le x} p_X(x_i),$$

a right-continuous step function with jumps of height $p_X(x_i)$ at each support point $x_i$. The CDF satisfies $F_X(-\infty) = 0$ and $F_X(\infty) = 1$, and probabilities of intervals are computed via $P(a < X \le b) = F_X(b) - F_X(a)$.

### Continuous Random Variables and Probability Density Functions

A continuous random variable $X$ possesses a probability density function $f_X : \mathbb{R} \to [0, \infty)$ such that for any Borel set $B$,

$$P(X \in B) = \int_B f_X(x) \, dx.$$

The PDF must satisfy non-negativity $f_X(x) \ge 0$ and normalization $\int_{-\infty}^\infty f_X(x) \, dx = 1$. Unlike the PMF, the PDF does not represent probabilities of individual points—indeed, $P(X = x) = 0$ for all $x$ under continuous distributions—but rather probability density, with $P(X \in [x, x+dx]) \approx f_X(x) \, dx$ for infinitesimal $dx$.

The cumulative distribution function is

$$F_X(x) = P(X \le x) = \int_{-\infty}^x f_X(t) \, dt,$$

and the fundamental theorem of calculus guarantees that $f_X(x) = \frac{dF_X}{dx}(x)$ at all points where $F_X$ is differentiable. The CDF is continuous, non-decreasing, and right-continuous, with $F_X(-\infty) = 0$ and $F_X(\infty) = 1$.

The uniform distribution $\text{Uniform}(a, b)$ assigns equal density to every point in the interval $[a, b]$. The PDF is

$$f_X(x) = \begin{cases} \frac{1}{b-a} & \text{if } x \in [a, b], \\ 0 & \text{otherwise}.\end{cases}$$

Normalization is immediate: $\int_a^b \frac{1}{b-a} \, dx = \frac{b-a}{b-a} = 1$. The CDF is

$$F_X(x) = \begin{cases} 0 & \text{if } x < a, \\ \frac{x-a}{b-a} & \text{if } x \in [a, b], \\ 1 & \text{if } x > b.\end{cases}$$

The expectation is

$$\mathbb{E}[X] = \int_a^b x \cdot \frac{1}{b-a} \, dx = \frac{1}{b-a} \cdot \frac{x^2}{2} \bigg|_a^b = \frac{b^2 - a^2}{2(b-a)} = \frac{(b-a)(b+a)}{2(b-a)} = \frac{a+b}{2},$$

the midpoint of the interval. The second moment is

$$\mathbb{E}[X^2] = \int_a^b x^2 \cdot \frac{1}{b-a} \, dx = \frac{1}{b-a} \cdot \frac{x^3}{3} \bigg|_a^b = \frac{b^3 - a^3}{3(b-a)} = \frac{(b-a)(b^2 + ab + a^2)}{3(b-a)} = \frac{b^2 + ab + a^2}{3},$$

yielding variance

$$\text{Var}(X) = \frac{b^2 + ab + a^2}{3} - \left(\frac{a+b}{2}\right)^2 = \frac{b^2 + ab + a^2}{3} - \frac{a^2 + 2ab + b^2}{4} = \frac{4b^2 + 4ab + 4a^2 - 3a^2 - 6ab - 3b^2}{12} = \frac{(b-a)^2}{12}.$$

The exponential distribution $\text{Exp}(\lambda)$ with rate parameter $\lambda > 0$ models the time until the first event in a Poisson process. The PDF is

$$f_X(x) = \begin{cases} \lambda e^{-\lambda x} & \text{if } x \ge 0, \\ 0 & \text{if } x < 0.\end{cases}$$

Normalization follows from $\int_0^\infty \lambda e^{-\lambda x} \, dx = \lambda \cdot \left[-\frac{1}{\lambda} e^{-\lambda x}\right]_0^\infty = \lambda \cdot \frac{1}{\lambda} = 1$. The CDF is

$$F_X(x) = \int_0^x \lambda e^{-\lambda t} \, dt = 1 - e^{-\lambda x}, \quad x \ge 0.$$

The expectation is computed via integration by parts:

$$\mathbb{E}[X] = \int_0^\infty x \cdot \lambda e^{-\lambda x} \, dx.$$

Let $u = x$ and $dv = \lambda e^{-\lambda x} dx$, so $du = dx$ and $v = -e^{-\lambda x}$. Then

$$\mathbb{E}[X] = \left[-x e^{-\lambda x}\right]_0^\infty + \int_0^\infty e^{-\lambda x} \, dx = 0 + \left[-\frac{1}{\lambda} e^{-\lambda x}\right]_0^\infty = \frac{1}{\lambda}.$$

For the second moment, we compute

$$\mathbb{E}[X^2] = \int_0^\infty x^2 \cdot \lambda e^{-\lambda x} \, dx.$$

Let $u = x^2$ and $dv = \lambda e^{-\lambda x} dx$, so $du = 2x \, dx$ and $v = -e^{-\lambda x}$:

$$\mathbb{E}[X^2] = \left[-x^2 e^{-\lambda x}\right]_0^\infty + \int_0^\infty 2x e^{-\lambda x} \, dx = 0 + \frac{2}{\lambda} \int_0^\infty \lambda x e^{-\lambda x} \, dx = \frac{2}{\lambda} \cdot \frac{1}{\lambda} = \frac{2}{\lambda^2}.$$

Thus the variance is

$$\text{Var}(X) = \frac{2}{\lambda^2} - \left(\frac{1}{\lambda}\right)^2 = \frac{2}{\lambda^2} - \frac{1}{\lambda^2} = \frac{1}{\lambda^2}.$$

The exponential distribution exhibits the memoryless property: $P(X > s + t \mid X > s) = P(X > t)$ for all $s, t \ge 0$. This follows from

$$P(X > s + t \mid X > s) = \frac{P(X > s + t)}{P(X > s)} = \frac{e^{-\lambda(s+t)}}{e^{-\lambda s}} = e^{-\lambda t} = P(X > t).$$

The normal (Gaussian) distribution $\mathcal{N}(\mu, \sigma^2)$ with mean $\mu$ and variance $\sigma^2$ is ubiquitous in probability theory and statistics due to the central limit theorem. The PDF is

$$f_X(x) = \frac{1}{\sqrt{2\pi\sigma^2}} \exp\left(-\frac{(x-\mu)^2}{2\sigma^2}\right), \quad x \in \mathbb{R}.$$

The standard normal distribution $\mathcal{N}(0, 1)$ has PDF

$$\phi(x) = \frac{1}{\sqrt{2\pi}} e^{-x^2/2}.$$

Normalization $\int_{-\infty}^\infty \phi(x) \, dx = 1$ follows from the Gaussian integral identity $\int_{-\infty}^\infty e^{-x^2/2} \, dx = \sqrt{2\pi}$, which can be proved by converting to polar coordinates and computing

$$\left(\int_{-\infty}^\infty e^{-x^2/2} \, dx\right)^2 = \int_{-\infty}^\infty \int_{-\infty}^\infty e^{-(x^2 + y^2)/2} \, dx \, dy = \int_0^{2\pi} \int_0^\infty e^{-r^2/2} r \, dr \, d\theta = 2\pi \cdot 1 = 2\pi.$$

The expectation of the standard normal is zero by symmetry: $\mathbb{E}[X] = \int_{-\infty}^\infty x \phi(x) \, dx = 0$ since the integrand is an odd function. The variance is

$$\text{Var}(X) = \mathbb{E}[X^2] = \int_{-\infty}^\infty x^2 \phi(x) \, dx = \frac{1}{\sqrt{2\pi}} \int_{-\infty}^\infty x^2 e^{-x^2/2} \, dx.$$

Integration by parts with $u = x$ and $dv = x e^{-x^2/2} dx$ gives $du = dx$ and $v = -e^{-x^2/2}$:

$$\mathbb{E}[X^2] = \frac{1}{\sqrt{2\pi}} \left(\left[-x e^{-x^2/2}\right]_{-\infty}^\infty + \int_{-\infty}^\infty e^{-x^2/2} \, dx\right) = \frac{1}{\sqrt{2\pi}} \cdot \sqrt{2\pi} = 1.$$

For the general normal distribution $\mathcal{N}(\mu, \sigma^2)$, we use the standardization $Z = (X - \mu)/\sigma$ to deduce $\mathbb{E}[X] = \mu$ and $\text{Var}(X) = \sigma^2$.

### Expectation and Variance as Lebesgue-Stieltjes Integrals

The expectation $\mathbb{E}[X]$ admits a unified representation as a Lebesgue-Stieltjes integral with respect to the CDF $F_X$:

$$\mathbb{E}[X] = \int_{-\infty}^\infty x \, dF_X(x).$$

When $X$ is discrete with PMF $p_X$, the measure $dF_X$ assigns point masses, and the integral reduces to the sum $\sum_x x \cdot p_X(x)$. When $X$ is continuous with PDF $f_X$, the measure $dF_X(x) = f_X(x) \, dx$, and the integral becomes the Lebesgue integral $\int_{-\infty}^\infty x f_X(x) \, dx$. This formulation extends naturally to expectations of functions of $X$:

$$\mathbb{E}[g(X)] = \int_{-\infty}^\infty g(x) \, dF_X(x).$$

For discrete $X$, this is $\sum_x g(x) p_X(x)$, and for continuous $X$, it is $\int_{-\infty}^\infty g(x) f_X(x) \, dx$.

The variance is the expectation of the squared deviation:

$$\text{Var}(X) = \mathbb{E}[(X - \mathbb{E}[X])^2] = \int_{-\infty}^\infty (x - \mu)^2 \, dF_X(x),$$

where $\mu = \mathbb{E}[X]$. The algebraic identity

$$\text{Var}(X) = \mathbb{E}[X^2] - (\mathbb{E}[X])^2$$

simplifies computation by avoiding the need to first compute the mean before integrating. This follows from expanding the square:

$$\mathbb{E}[(X - \mu)^2] = \mathbb{E}[X^2 - 2\mu X + \mu^2] = \mathbb{E}[X^2] - 2\mu \mathbb{E}[X] + \mu^2 = \mathbb{E}[X^2] - 2\mu^2 + \mu^2 = \mathbb{E}[X^2] - \mu^2.$$

The standard deviation $\sigma_X = \sqrt{\text{Var}(X)}$ measures dispersion in the same units as $X$ and is often more interpretable than variance.

### Moment Generating Functions

The moment generating function (MGF) of a random variable $X$ is defined as

$$M_X(t) = \mathbb{E}[e^{tX}] = \int_{-\infty}^\infty e^{tx} \, dF_X(x),$$

provided this expectation exists for $t$ in some neighborhood of zero. The MGF encodes all moments of $X$ through its Taylor expansion. Assuming we can interchange differentiation and expectation (justified when $M_X(t)$ exists in an open interval around the origin), we have

$$M_X(t) = \mathbb{E}\left[\sum_{n=0}^\infty \frac{(tX)^n}{n!}\right] = \sum_{n=0}^\infty \frac{t^n}{n!} \mathbb{E}[X^n].$$

Differentiating $n$ times and evaluating at $t = 0$ yields

$$M_X^{(n)}(0) = \mathbb{E}[X^n],$$

the $n$-th moment of $X$. In particular, $M_X'(0) = \mathbb{E}[X]$ and $M_X''(0) = \mathbb{E}[X^2]$, so $\text{Var}(X) = M_X''(0) - (M_X'(0))^2$.

The MGF possesses the uniqueness property: if $M_X(t) = M_Y(t)$ for all $t$ in some neighborhood of zero, then $X$ and $Y$ have the same distribution. This makes the MGF a powerful tool for identifying distributions and proving convergence in distribution.

For the Bernoulli distribution with success probability $p$, the MGF is

$$M_X(t) = \mathbb{E}[e^{tX}] = e^{t \cdot 0} \cdot (1-p) + e^{t \cdot 1} \cdot p = (1-p) + pe^t.$$

Differentiating gives $M_X'(t) = pe^t$, so $M_X'(0) = p = \mathbb{E}[X]$. The second derivative is $M_X''(t) = pe^t$, so $M_X''(0) = p$, and $\text{Var}(X) = p - p^2 = p(1-p)$.

For the Poisson distribution with rate $\lambda$, the MGF is

$$M_X(t) = \mathbb{E}[e^{tX}] = \sum_{k=0}^\infty e^{tk} \cdot \frac{\lambda^k e^{-\lambda}}{k!} = e^{-\lambda} \sum_{k=0}^\infty \frac{(\lambda e^t)^k}{k!} = e^{-\lambda} \cdot e^{\lambda e^t} = e^{\lambda(e^t - 1)}.$$

Differentiating yields

$$M_X'(t) = e^{\lambda(e^t - 1)} \cdot \lambda e^t,$$

so $M_X'(0) = \lambda = \mathbb{E}[X]$. The second derivative is

$$M_X''(t) = e^{\lambda(e^t - 1)} \cdot (\lambda e^t)^2 + e^{\lambda(e^t - 1)} \cdot \lambda e^t,$$

so $M_X''(0) = \lambda^2 + \lambda$, yielding $\text{Var}(X) = \lambda^2 + \lambda - \lambda^2 = \lambda$.

For the exponential distribution with rate $\lambda$, the MGF is

$$M_X(t) = \int_0^\infty e^{tx} \cdot \lambda e^{-\lambda x} \, dx = \lambda \int_0^\infty e^{-((\lambda - t)x)} \, dx = \lambda \cdot \frac{1}{\lambda - t} = \frac{\lambda}{\lambda - t},$$

valid for $t < \lambda$. Differentiating gives

$$M_X'(t) = \frac{\lambda}{(\lambda - t)^2},$$

so $M_X'(0) = \frac{1}{\lambda} = \mathbb{E}[X]$. The second derivative is

$$M_X''(t) = \frac{2\lambda}{(\lambda - t)^3},$$

so $M_X''(0) = \frac{2}{\lambda^2}$, and $\text{Var}(X) = \frac{2}{\lambda^2} - \frac{1}{\lambda^2} = \frac{1}{\lambda^2}$.

For the normal distribution $\mathcal{N}(\mu, \sigma^2)$, the MGF is

$$M_X(t) = e^{\mu t + \sigma^2 t^2 / 2}.$$

This can be derived by completing the square in the exponent of the integrand:

$$M_X(t) = \int_{-\infty}^\infty e^{tx} \cdot \frac{1}{\sqrt{2\pi\sigma^2}} \exp\left(-\frac{(x-\mu)^2}{2\sigma^2}\right) dx.$$

The exponent is

$$tx - \frac{(x-\mu)^2}{2\sigma^2} = -\frac{1}{2\sigma^2}\left(x^2 - 2\mu x + \mu^2 - 2\sigma^2 tx\right) = -\frac{1}{2\sigma^2}\left(x^2 - 2(\mu + \sigma^2 t)x + \mu^2\right).$$

Completing the square:

$$x^2 - 2(\mu + \sigma^2 t)x + \mu^2 = \left(x - (\mu + \sigma^2 t)\right)^2 - (\mu + \sigma^2 t)^2 + \mu^2,$$

so the exponent becomes

$$-\frac{1}{2\sigma^2}\left(\left(x - (\mu + \sigma^2 t)\right)^2 - 2\mu\sigma^2 t - \sigma^4 t^2\right) = -\frac{(x - (\mu + \sigma^2 t))^2}{2\sigma^2} + \mu t + \frac{\sigma^2 t^2}{2}.$$

Factoring out the constant term:

$$M_X(t) = e^{\mu t + \sigma^2 t^2 / 2} \int_{-\infty}^\infty \frac{1}{\sqrt{2\pi\sigma^2}} \exp\left(-\frac{(x - (\mu + \sigma^2 t))^2}{2\sigma^2}\right) dx = e^{\mu t + \sigma^2 t^2 / 2},$$

since the integral is the PDF of $\mathcal{N}(\mu + \sigma^2 t, \sigma^2)$, which integrates to $1$.

Differentiating the MGF gives $M_X'(t) = (\mu + \sigma^2 t) e^{\mu t + \sigma^2 t^2 / 2}$, so $M_X'(0) = \mu = \mathbb{E}[X]$. The second derivative is

$$M_X''(t) = \sigma^2 e^{\mu t + \sigma^2 t^2 / 2} + (\mu + \sigma^2 t)^2 e^{\mu t + \sigma^2 t^2 / 2},$$

so $M_X''(0) = \sigma^2 + \mu^2$, and $\text{Var}(X) = \sigma^2 + \mu^2 - \mu^2 = \sigma^2$.

### Change of Variables and Transformations of Random Variables

Suppose $X$ is a continuous random variable with PDF $f_X$, and we define a new random variable $Y = g(X)$ for some function $g : \mathbb{R} \to \mathbb{R}$. We seek the PDF $f_Y$ of $Y$. The general strategy is to compute the CDF of $Y$ and then differentiate:

$$F_Y(y) = P(Y \le y) = P(g(X) \le y) = P(X \in g^{-1}((-\infty, y])).$$

If $g$ is strictly increasing, then $g^{-1}((-\infty, y]) = (-\infty, g^{-1}(y)]$, so

$$F_Y(y) = F_X(g^{-1}(y)).$$

Differentiating with respect to $y$ using the chain rule:

$$f_Y(y) = \frac{dF_Y}{dy}(y) = f_X(g^{-1}(y)) \cdot \frac{d}{dy} g^{-1}(y) = f_X(g^{-1}(y)) \cdot \frac{1}{g'(g^{-1}(y))}.$$

Setting $x = g^{-1}(y)$, so $y = g(x)$ and $dy = g'(x) dx$, we can write

$$f_Y(y) = f_X(x) \cdot \frac{1}{g'(x)} = \frac{f_X(x)}{|g'(x)|},$$

where the absolute value accounts for the case when $g$ is strictly decreasing. This formula is the univariate change-of-variables theorem:

$$f_Y(y) = f_X(g^{-1}(y)) \cdot \left|\frac{d}{dy} g^{-1}(y)\right|.$$

Consider the transformation $Y = aX + b$ where $a \neq 0$. The inverse is $X = (Y - b)/a = g^{-1}(Y)$, so

$$f_Y(y) = f_X\left(\frac{y - b}{a}\right) \cdot \frac{1}{|a|}.$$

If $X \sim \mathcal{N}(\mu, \sigma^2)$, then $Y = aX + b \sim \mathcal{N}(a\mu + b, a^2 \sigma^2)$. To verify this, we compute

$$f_Y(y) = \frac{1}{|a|} \cdot \frac{1}{\sqrt{2\pi\sigma^2}} \exp\left(-\frac{\left(\frac{y-b}{a} - \mu\right)^2}{2\sigma^2}\right) = \frac{1}{\sqrt{2\pi(a^2\sigma^2)}} \exp\left(-\frac{(y - (a\mu + b))^2}{2a^2\sigma^2}\right),$$

which is the PDF of $\mathcal{N}(a\mu + b, a^2\sigma^2)$.

For the transformation $Y = X^2$ where $X$ has PDF $f_X$ supported on $\mathbb{R}$, the CDF of $Y$ is

$$F_Y(y) = P(X^2 \le y) = P(-\sqrt{y} \le X \le \sqrt{y}) = F_X(\sqrt{y}) - F_X(-\sqrt{y}), \quad y \ge 0.$$

Differentiating with respect to $y$:

$$f_Y(y) = f_X(\sqrt{y}) \cdot \frac{1}{2\sqrt{y}} + f_X(-\sqrt{y}) \cdot \frac{1}{2\sqrt{y}} = \frac{f_X(\sqrt{y}) + f_X(-\sqrt{y})}{2\sqrt{y}}.$$

If $X \sim \mathcal{N}(0, 1)$, then

$$f_Y(y) = \frac{1}{2\sqrt{y}} \cdot \frac{2}{\sqrt{2\pi}} e^{-y/2} = \frac{1}{\sqrt{2\pi y}} e^{-y/2}, \quad y > 0.$$

This is the PDF of the chi-squared distribution with one degree of freedom, $\chi^2_1$.

For the exponential transformation $Y = e^X$ where $X$ has PDF $f_X$, the inverse is $X = \ln Y$, so

$$f_Y(y) = f_X(\ln y) \cdot \frac{1}{y}, \quad y > 0.$$

If $X \sim \mathcal{N}(\mu, \sigma^2)$, then

$$f_Y(y) = \frac{1}{y\sigma\sqrt{2\pi}} \exp\left(-\frac{(\ln y - \mu)^2}{2\sigma^2}\right), \quad y > 0.$$

This is the PDF of the lognormal distribution $\text{Lognormal}(\mu, \sigma^2)$.

For multivariate transformations, the Jacobian determinant generalizes the derivative factor. If $(X_1, X_2, \ldots, X_n)$ has joint PDF $f_{\mathbf{X}}(\mathbf{x})$ and we define $(Y_1, Y_2, \ldots, Y_n) = \mathbf{g}(\mathbf{X})$ where $\mathbf{g} : \mathbb{R}^n \to \mathbb{R}^n$ is a bijection, then

$$f_{\mathbf{Y}}(\mathbf{y}) = f_{\mathbf{X}}(\mathbf{g}^{-1}(\mathbf{y})) \cdot \left|\det J_{\mathbf{g}^{-1}}(\mathbf{y})\right|,$$

where $J_{\mathbf{g}^{-1}}$ is the Jacobian matrix of $\mathbf{g}^{-1}$ with entries $(J_{\mathbf{g}^{-1}})_{ij} = \frac{\partial (g^{-1})_i}{\partial y_j}$.

Consider the polar transformation in $\mathbb{R}^2$: $(X, Y) = (R\cos\Theta, R\sin\Theta)$ where $R \ge 0$ and $\Theta \in [0, 2\pi)$. The inverse is $R = \sqrt{X^2 + Y^2}$ and $\Theta = \arctan(Y/X)$. The Jacobian matrix of the forward transformation $(R, \Theta) \mapsto (X, Y)$ is

$$J = \begin{pmatrix} \cos\Theta & -R\sin\Theta \\ \sin\Theta & R\cos\Theta \end{pmatrix},$$

with determinant $\det J = R\cos^2\Theta + R\sin^2\Theta = R$. Thus

$$f_{R,\Theta}(r, \theta) = f_{X,Y}(r\cos\theta, r\sin\theta) \cdot r.$$

If $X$ and $Y$ are independent standard normals, then

$$f_{X,Y}(x, y) = \frac{1}{2\pi} e^{-(x^2 + y^2)/2},$$

so

$$f_{R,\Theta}(r, \theta) = \frac{1}{2\pi} e^{-r^2/2} \cdot r = \left(\frac{1}{2\pi}\right) \cdot \left(r e^{-r^2/2}\right).$$

This factors as $f_\Theta(\theta) \cdot f_R(r)$ where $f_\Theta(\theta) = \frac{1}{2\pi}$ (uniform on $[0, 2\pi)$) and $f_R(r) = r e^{-r^2/2}$ for $r \ge 0$, showing that $R$ and $\Theta$ are independent and $R$ follows the Rayleigh distribution.

## 3. High-Performance Optimization & Failure Modes

The computational manipulation of random variables, distributions, and transformations requires careful attention to numerical stability, algorithmic complexity, and edge-case handling. Many probability computations involve integration, differentiation, and root-finding operations that are analytically tractable for standard distributions but numerically challenging for arbitrary or composite distributions. Understanding where exact methods fail and where approximations are required forms the essence of practical probabilistic computation.

Expectation and variance calculations for discrete distributions reduce to finite sums when the support is finite, but when the support is countably infinite (as in the Poisson or geometric distributions), truncation error analysis becomes critical. The tail probabilities of heavy-tailed distributions decay slowly, and naive truncation at a fixed threshold can introduce significant bias. For the Poisson distribution with large rate parameter $\lambda$, computing $\mathbb{E}[X] = \sum_{k=0}^\infty k \cdot p_X(k)$ directly is impractical, but the closed-form result $\mathbb{E}[X] = \lambda$ avoids computation entirely. In general, leveraging known moment formulas and MGF derivatives is far more efficient than direct numerical integration or summation.

For continuous distributions, numerical integration of the PDF to compute expectations, variances, and CDFs introduces quadrature error. Standard quadrature rules like Simpson's rule or Gaussian quadrature achieve exponential convergence for smooth integrands, but PDFs with singularities, discontinuities, or heavy tails require adaptive integration strategies. The Gaussian PDF $\phi(x) = \frac{1}{\sqrt{2\pi}} e^{-x^2/2}$ decays rapidly, and integrating over $[-5, 5]$ captures more than $99.9999\%$ of the probability mass, but the Cauchy distribution with PDF $f_X(x) = \frac{1}{\pi(1 + x^2)}$ has such heavy tails that $\mathbb{E}[X]$ does not exist—the integral $\int_{-\infty}^\infty x \cdot \frac{1}{\pi(1 + x^2)} \, dx$ diverges. Attempting to compute the expectation numerically will yield nonsensical results unless the divergence is detected through increasing integral estimates as the integration domain expands.

The cumulative distribution function $F_X(x)$ for standard distributions is often tabulated or approximated using special functions. The standard normal CDF $\Phi(x) = \int_{-\infty}^x \frac{1}{\sqrt{2\pi}} e^{-t^2/2} \, dt$ has no closed-form expression in terms of elementary functions, but highly accurate polynomial and rational approximations exist. The error function $\text{erf}(x) = \frac{2}{\sqrt{\pi}} \int_0^x e^{-t^2} \, dt$ satisfies $\Phi(x) = \frac{1}{2}\left(1 + \text{erf}\left(\frac{x}{\sqrt{2}}\right)\right)$, and numerical libraries provide precomputed implementations with relative error below $10^{-15}$. For custom distributions, numerical CDF evaluation via adaptive quadrature combined with memoization or interpolation can achieve both accuracy and speed.

Moment generating functions exist only when $\mathbb{E}[e^{tX}]$ is finite in a neighborhood of the origin. For heavy-tailed distributions like the Pareto or Cauchy, the MGF does not exist, and alternative techniques such as characteristic functions $\varphi_X(t) = \mathbb{E}[e^{itX}]$ (which always exist) must be employed. The characteristic function enjoys similar properties to the MGF—it uniquely determines the distribution and transforms convolutions into products—but its complex-valued nature complicates differentiation for moment extraction. The $n$-th moment can be recovered via $\mathbb{E}[X^n] = i^{-n} \varphi_X^{(n)}(0)$, but numerical differentiation of oscillatory complex functions introduces phase error. For distributions with finite moments but no MGF, direct integration or the method of moments provides more robust computational paths.

Transformation of random variables via the change-of-variables formula requires careful handling of the Jacobian and the domain of the inverse function. When $g$ is not injective, the preimage $g^{-1}(\{y\})$ may contain multiple points, and the PDF of $Y = g(X)$ must sum contributions from all preimages:

$$f_Y(y) = \sum_{x : g(x) = y} \frac{f_X(x)}{|g'(x)|}.$$

For the transformation $Y = X^2$ with $X \sim \mathcal{N}(0, 1)$, the preimages of $y > 0$ are $x = \pm\sqrt{y}$, yielding

$$f_Y(y) = \frac{f_X(\sqrt{y})}{|2\sqrt{y}|} + \frac{f_X(-\sqrt{y})}{|2\sqrt{y}|} = \frac{f_X(\sqrt{y}) + f_X(-\sqrt{y})}{2\sqrt{y}}.$$

Numerically, computing $f_Y(y)$ near $y = 0$ requires careful handling of the $1/\sqrt{y}$ singularity. While the singularity is integrable (the total probability mass is finite), naive evaluation at $y = 0$ will overflow. Analytical simplification or small-$y$ asymptotic expansions should be used to stabilize computation.

Multivariate transformations introduce additional complexity through the Jacobian determinant. For high-dimensional transformations, computing the determinant directly scales as $O(n^3)$, but structured transformations (orthogonal, triangular, diagonal) admit faster determinant calculations. The Box-Muller transformation converts two independent uniform random variables $U_1, U_2 \sim \text{Uniform}(0, 1)$ into two independent standard normals $Z_1, Z_2$ via

$$Z_1 = \sqrt{-2\ln U_1} \cos(2\pi U_2), \quad Z_2 = \sqrt{-2\ln U_1} \sin(2\pi U_2).$$

This transformation is numerically stable for $U_1 \in (0, 1)$, but $U_1 = 0$ causes a logarithmic singularity. In floating-point arithmetic, the smallest representable positive number is approximately $2.2 \times 10^{-308}$ in double precision, so $\ln U_1$ is bounded below by approximately $-708$, and $\sqrt{-2\ln U_1}$ is bounded above by $\sqrt{1416} \approx 37.6$, well within representable range. However, pseudorandom number generators that produce $U_1 = 0$ exactly must be guarded against.

The inverse CDF (quantile) method for sampling from a distribution $F_X$ relies on the identity $X = F_X^{-1}(U)$ where $U \sim \text{Uniform}(0, 1)$. This method is exact and general, but it requires the ability to compute $F_X^{-1}$ efficiently. For distributions with closed-form CDFs (uniform, exponential, Weibull), the inverse is trivial. For the exponential distribution, $F_X(x) = 1 - e^{-\lambda x}$ implies $x = -\frac{1}{\lambda} \ln(1 - u)$, and we can sample via $X = -\frac{1}{\lambda} \ln U$ since $1 - U$ has the same distribution as $U$. For distributions without closed-form CDFs (normal, gamma, beta), numerical root-finding or rational approximations to the quantile function are required, and precomputed lookup tables with interpolation can accelerate repeated sampling.

Failure modes in probabilistic computation often stem from inappropriate application of continuous approximations to discrete distributions or vice versa. The Poisson approximation to the binomial distribution $\text{Binomial}(n, p)$ is accurate when $n$ is large and $p$ is small with $np = \lambda$ held constant, but it fails when $p$ is not small or when $n$ is moderate. The normal approximation to the binomial, valid when $np$ and $n(1-p)$ are both large (typically $\ge 5$), introduces continuity correction: $P(X = k) \approx P(k - 0.5 < Y < k + 0.5)$ where $Y \sim \mathcal{N}(np, np(1-p))$. Omitting the continuity correction can introduce errors of several percentage points.

Underflow and overflow in MGF computations occur when $|tX|$ is large. For the exponential distribution, $M_X(t) = \frac{\lambda}{\lambda - t}$ diverges as $t \to \lambda^-$, and numerical evaluation for $t$ close to $\lambda$ loses precision. In such cases, working with the logarithm of the MGF (the cumulant generating function $K_X(t) = \ln M_X(t)$) avoids overflow and provides numerical stability. For the normal distribution, $K_X(t) = \mu t + \frac{\sigma^2 t^2}{2}$ is a simple quadratic, whereas $M_X(t) = e^{\mu t + \sigma^2 t^2 / 2}$ can overflow for large $|t|$.

Change-of-variables errors arise when the transformation is not bijective over the support of the original distribution. Consider $Y = |X|$ where $X \sim \mathcal{N}(0, 1)$. The transformation is not invertible globally, but restricted to $x \ge 0$ and $x < 0$ separately, we have two branches. The PDF of $Y$ must account for both branches:

$$f_Y(y) = f_X(y) + f_X(-y) = \frac{2}{\sqrt{2\pi}} e^{-y^2/2}, \quad y \ge 0.$$

This is the half-normal distribution. Forgetting to sum over all preimages leads to an incorrect PDF that integrates to less than one.

Numerical differentiation of the MGF to extract moments is subject to truncation and rounding error. The central difference formula

$$M_X'(t) \approx \frac{M_X(t + h) - M_X(t - h)}{2h}$$

achieves $O(h^2)$ accuracy for smooth $M_X$, but choosing $h$ too small amplifies rounding error while choosing $h$ too large increases truncation error. The optimal $h$ balances these errors and typically scales as $\epsilon^{1/3}$ where $\epsilon$ is machine precision (approximately $2.2 \times 10^{-16}$ in double precision), yielding $h \approx 6 \times 10^{-6}$. Automatic differentiation avoids numerical differentiation error entirely by propagating derivatives symbolically through the computation graph, and this is the preferred approach in modern probabilistic programming frameworks.

Edge cases in distribution support must be handled explicitly. The exponential distribution is supported on $[0, \infty)$, and its PDF is zero for $x < 0$. Numerical integration routines that sample negative $x$ values must return zero density rather than evaluating $\lambda e^{-\lambda x}$, which would produce incorrect positive values. Similarly, the beta distribution is supported on $[0, 1]$, and evaluations outside this interval must return zero. Failure to enforce support constraints leads to spurious probability mass and biased expectations.

Sampling from transformed distributions can exploit the transformation directly rather than sampling from the derived PDF. To sample from the lognormal distribution $Y = e^X$ where $X \sim \mathcal{N}(\mu, \sigma^2)$, we sample $X$ from the normal distribution and compute $Y = e^X$. This is far more efficient than numerically sampling from the lognormal PDF via rejection sampling or inverse CDF methods. In general, constructive sampling via transformations of standard distributions (normal, uniform, exponential) leverages well-optimized base samplers and avoids numerical inversion of CDFs or acceptance-rejection inefficiencies.

The calculus of probability distributions forms the computational substrate for statistical inference, stochastic optimization, and Monte Carlo simulation. Mastery of the mechanics—PMFs, PDFs, CDFs, expectations, variances, MGFs, and transformations—equips the practitioner to derive analytical results when possible and to design numerically stable, efficient algorithms when closed forms are unavailable. The interplay between exact symbolic manipulation and approximate numerical computation defines the pragmatic reality of applied probability theory.
