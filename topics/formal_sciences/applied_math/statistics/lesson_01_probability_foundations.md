# Lesson 1: Probability Foundations

## 1. First-Principles Intuition & Invariants

The mathematical theory of probability begins not with dice or cards, but with a recognition that uncertainty itself admits a precise algebraic structure. The historical path from Cardano's sixteenth-century musings on gambling odds to Kolmogorov's 1933 axiomatization spans three centuries of conceptual struggle, and the central difficulty was never the calculation of probabilities but rather the definition of what a probability *is*. The resolution, achieved by Kolmogorov, was to ground probability in measure theory: a probability space is a measure space of total mass one, and every theorem of probability becomes a theorem about a finite measure. This grounding is not merely aesthetic—it is what allows us to handle continuous distributions, infinite sequences of trials, and stochastic processes with the same rigor that we handle a coin flip.

### The Kolmogorov Axioms and the Probability Triple

A probability space is a triple $(\Omega, \mathcal{F}, P)$, where $\Omega$ is the sample space (the set of all elementary outcomes), $\mathcal{F} \subseteq 2^{\Omega}$ is a $\sigma$-algebra on $\Omega$ (the collection of events to which we assign probability), and $P : \mathcal{F} \to [0,1]$ is the probability measure. A $\sigma$-algebra must satisfy three closure properties: it contains $\Omega$ itself, it is closed under complementation (if $A \in \mathcal{F}$ then $A^c \in \mathcal{F}$), and it is closed under countable unions (if $A_1, A_2, \ldots \in \mathcal{F}$ then $\bigcup_{i=1}^{\infty} A_i \in \mathcal{F}$). These closure properties ensure that we can take limits of events—essential for continuous distributions and limit theorems.

The probability measure $P$ satisfies Kolmogorov's three axioms:

$$P(\Omega) = 1, \quad P(A) \geq 0 \text{ for all } A \in \mathcal{F}, \quad P\!\left(\bigcup_{i=1}^{\infty} A_i\right) = \sum_{i=1}^{\infty} P(A_i) \text{ when } A_i \cap A_j = \emptyset \text{ for } i \neq j.$$

The third axiom—countable additivity for pairwise disjoint events—is the one that separates measure-theoretic probability from naïve finite combinatorial probability. It is what allows us to integrate a density function to obtain a probability, and what allows the infinite sums that appear in the law of large numbers to be well-defined. Without countable additivity, we could not pass from discrete to continuous distributions in a unified framework.

From these axioms, a cascade of consequences follows immediately. We derive the complement rule by observing that $\Omega = A \cup A^c$ with $A \cap A^c = \emptyset$, so $1 = P(\Omega) = P(A) + P(A^c)$, giving $P(A^c) = 1 - P(A)$. The monotonicity property follows: if $A \subseteq B$ then $B = A \cup (B \setminus A)$ (disjoint union), so $P(B) = P(A) + P(B \setminus A) \geq P(A)$. The union bound (Boole's inequality) states that for any countable collection of events, $P\!\left(\bigcup_{i=1}^{\infty} A_i\right) \leq \sum_{i=1}^{\infty} P(A_i)$, proved by the inclusion-exclusion telescoping of indicator functions or by a direct measure-theoretic argument via Bonferroni inequalities.

**Theorem (Inclusion-Exclusion).** For any finite collection $A_1, \ldots, A_n \in \mathcal{F}$:

$$P\!\left(\bigcup_{i=1}^n A_i\right) = \sum_{k=1}^{n} (-1)^{k+1} \sum_{1 \leq i_1 < \cdots < i_k \leq n} P(A_{i_1} \cap \cdots \cap A_{i_k}).$$

*Proof.* The indicator function of the union can be written via the identity $\mathbf{1}_{\bigcup A_i} = 1 - \prod_{i=1}^n (1 - \mathbf{1}_{A_i})$. Expanding the product: $\prod_{i=1}^n (1 - \mathbf{1}_{A_i}) = \sum_{S \subseteq [n]} (-1)^{|S|} \prod_{i \in S} \mathbf{1}_{A_i} = \sum_{S \subseteq [n]} (-1)^{|S|} \mathbf{1}_{\bigcap_{i \in S} A_i}$, where the empty intersection is $\Omega$ (indicator 1). Therefore $\mathbf{1}_{\bigcup A_i} = \sum_{\emptyset \neq S \subseteq [n]} (-1)^{|S|+1} \mathbf{1}_{\bigcap_{i \in S} A_i}$. Taking expectations (i.e., integrating against $P$) yields the formula. $\blacksquare$

A critical structural property is the continuity of probability measures. If $A_1 \subseteq A_2 \subseteq A_3 \subseteq \cdots$ is an increasing sequence of events, then $P\!\left(\bigcup_{i=1}^\infty A_i\right) = \lim_{n \to \infty} P(A_n)$. The proof relies on writing the countable union as a disjoint union: let $B_1 = A_1$ and $B_n = A_n \setminus A_{n-1}$ for $n \geq 2$. Then $\bigcup A_i = \bigcup B_i$ (disjoint), and by countable additivity, $P(\bigcup A_i) = \sum P(B_i) = \lim \sum_{i=1}^n P(B_i) = \lim P(\bigcup_{i=1}^n B_i) = \lim P(A_n)$. The dual statement for decreasing sequences follows by complementation. This continuity property is essential for the construction of probability on infinite product spaces—the foundation of the law of large numbers.

### Conditional Probability and the Chain Rule

Given two events $A, B \in \mathcal{F}$ with $P(B) > 0$, the conditional probability of $A$ given $B$ is defined as $P(A \mid B) = P(A \cap B) / P(B)$. This is not merely a definition but a necessary consequence of the axioms when we wish to restrict the measure to the sub-$\sigma$-algebra generated by $B$. The function $P_B(\cdot) := P(\cdot \mid B)$ is itself a probability measure on $(\Omega, \mathcal{F})$, and verifying the Kolmogorov axioms is straightforward: $P_B(\Omega) = P(\Omega \cap B)/P(B) = 1$, non-negativity is inherited from $P$, and countable additivity follows from the countable additivity of $P$ applied to the intersections with $B$.

The chain rule (or multiplication rule) generalizes conditioning to multiple events. For events $A_1, \ldots, A_n$ with $P(A_1 \cap \cdots \cap A_{n-1}) > 0$:

$$P(A_1 \cap \cdots \cap A_n) = P(A_1) \cdot P(A_2 \mid A_1) \cdot P(A_3 \mid A_1 \cap A_2) \cdots P(A_n \mid A_1 \cap \cdots \cap A_{n-1}).$$

The proof proceeds by induction on $n$. The base case $n=2$ is the definition of conditional probability: $P(A_1 \cap A_2) = P(A_1) \cdot P(A_2 \mid A_1)$. For the inductive step, write $P(A_1 \cap \cdots \cap A_n) = P(A_1 \cap \cdots \cap A_{n-1}) \cdot P(A_n \mid A_1 \cap \cdots \cap A_{n-1})$ by applying the base case with $B = A_1 \cap \cdots \cap A_{n-1}$ and $A = A_n$, then apply the inductive hypothesis to the first factor. This decomposition is the backbone of generative models, where a joint distribution over a sequence of variables is factored into a product of conditionals.

### Independence

Two events $A$ and $B$ are independent if $P(A \cap B) = P(A) \cdot P(B)$. Independence is a statement about the measure, not about the events themselves: two events may be independent under one measure and dependent under another. The key consequence of independence is that conditioning on $B$ provides no information about $A$: $P(A \mid B) = P(A)$ (when $P(B) > 0$), and vice versa.

Mutual independence of $n$ events $A_1, \ldots, A_n$ is stronger than pairwise independence. The events are mutually independent if for every subset $S \subseteq \{1, \ldots, n\}$:

$$P\!\left(\bigcap_{i \in S} A_i\right) = \prod_{i \in S} P(A_i).$$

The distinction matters. The classic counterexample involves two fair coin flips with $\Omega = \{HH, HT, TH, TT\}$ and the events $A = \{\text{first flip is } H\}$, $B = \{\text{second flip is } H\}$, and $C = \{\text{the two flips agree}\} = \{HH, TT\}$. Each pair is independent (each pairwise intersection has probability $1/4 = (1/2)(1/2)$), yet $P(A \cap B \cap C) = P(\{HH\}) = 1/4 \neq 1/8 = P(A)P(B)P(C)$. Pairwise independence does not imply mutual independence, and this distinction has direct consequences in reliability theory and distributed systems, where redundant components may appear independent in pairs but share a common-mode failure.

### Bayes' Theorem and the Prior-Posterior Mechanism

Bayes' theorem is a consequence of the definition of conditional probability, but its epistemological significance is enormous: it provides the mechanism by which evidence updates beliefs.

**Theorem (Bayes).** If $P(B) > 0$ and $P(A) > 0$, then:

$$P(A \mid B) = \frac{P(B \mid A) \cdot P(A)}{P(B)}.$$

*Proof.* From the definition, $P(A \cap B) = P(A \mid B) \cdot P(B) = P(B \mid A) \cdot P(A)$. Dividing both sides by $P(B)$ yields the result. $\blacksquare$

When we have a partition $\{B_1, \ldots, B_n\}$ of $\Omega$ (a set of mutually exclusive, collectively exhaustive events), the law of total probability gives:

$$P(A) = \sum_{i=1}^{n} P(A \mid B_i) \cdot P(B_i),$$

which combined with Bayes' theorem yields the extended form:

$$P(B_j \mid A) = \frac{P(A \mid B_j) \cdot P(B_j)}{\sum_{i=1}^{n} P(A \mid B_i) \cdot P(B_i)}.$$

The computational structure here is that the prior probabilities $P(B_i)$ are updated by the likelihoods $P(A \mid B_i)$ and normalized to produce posterior probabilities $P(B_i \mid A)$. This is the exact mechanism underlying Bayesian inference, na&iuml;ve Bayes classifiers, and the forward-backward algorithm for hidden Markov models.

A concrete application illustrates the subtlety of Bayesian reasoning. Consider a medical test for a rare disease with prevalence $P(D) = 0.001$, sensitivity $P(T^+ \mid D) = 0.99$, and specificity $P(T^+ \mid D^c) = 0.05$ (false positive rate). The posterior probability of having the disease given a positive test is:

$$P(D \mid T^+) = \frac{0.99 \times 0.001}{0.99 \times 0.001 + 0.05 \times 0.999} = \frac{0.00099}{0.00099 + 0.04995} = \frac{0.00099}{0.05094} \approx 0.0194.$$

Despite a test that is $99\%$ sensitive and $95\%$ specific, the posterior probability of disease is under $2\%$. The mechanism is the base rate fallacy: the rare prior dominates the posterior because the false positive rate, applied to the large non-diseased population, overwhelms the true positives. This is not a paradox but a direct computation, and it demonstrates why Bayesian reasoning is indispensable in domains where prior probabilities are extreme.

## 2. Core Architecture & Mechanics

### Random Variables as Measurable Functions

A random variable $X$ is a measurable function $X : \Omega \to \mathbb{R}$, meaning that for every Borel set $B \in \mathcal{B}(\mathbb{R})$, the preimage $X^{-1}(B) = \{\omega \in \Omega : X(\omega) \in B\}$ belongs to $\mathcal{F}$. Measurability ensures that we can assign probabilities to statements of the form "$X \in B$" by computing $P(X \in B) = P(X^{-1}(B))$. The distribution of $X$ is the pushforward measure $P_X(B) = P(X^{-1}(B))$ on $(\mathbb{R}, \mathcal{B}(\mathbb{R}))$, and it fully characterizes the probabilistic behavior of $X$ without any further reference to the underlying sample space $\Omega$.

The cumulative distribution function (CDF) of $X$ is $F_X(x) = P(X \leq x)$. Every CDF is non-decreasing, right-continuous, satisfies $\lim_{x \to -\infty} F_X(x) = 0$ and $\lim_{x \to +\infty} F_X(x) = 1$, and conversely, every function with these properties is the CDF of some probability distribution on $\mathbb{R}$. The CDF is the universal interface for distributions: $P(a < X \leq b) = F_X(b) - F_X(a)$, and $P(X = x) = F_X(x) - F_X(x^-)$, where $F_X(x^-)$ is the left limit.

### Discrete Distributions and the Probability Mass Function

A random variable $X$ is discrete if its range is a countable set $\{x_1, x_2, \ldots\}$, in which case its distribution is specified by the probability mass function (PMF) $p_X(x_i) = P(X = x_i)$, with $\sum_i p_X(x_i) = 1$. The CDF is a step function: $F_X(x) = \sum_{x_i \leq x} p_X(x_i)$.

The **Bernoulli distribution** $\text{Bern}(p)$ models a single binary trial: $P(X=1) = p$, $P(X=0) = 1-p$. Its CDF is $F(x) = 0$ for $x < 0$, $F(x) = 1-p$ for $0 \leq x < 1$, $F(x) = 1$ for $x \geq 1$. The Bernoulli is the atom from which discrete probability is constructed: sums of independent Bernoulli trials yield the binomial distribution, and geometric waiting times arise from sequences of Bernoulli trials.

The **Binomial distribution** $\text{Bin}(n, p)$ is the distribution of $X = \sum_{i=1}^n X_i$ where $X_i \sim \text{Bern}(p)$ independently. Its PMF is:

$$P(X = k) = \binom{n}{k} p^k (1-p)^{n-k}, \quad k = 0, 1, \ldots, n.$$

The derivation is combinatorial: among the $2^n$ possible outcome sequences of $n$ Bernoulli trials, exactly $\binom{n}{k}$ sequences have $k$ successes, and each such sequence has probability $p^k(1-p)^{n-k}$ by independence. The expectation is $np$ (proved below via linearity of expectation) and the variance is $np(1-p)$ (proved via the independence of the $X_i$).

The **Geometric distribution** $\text{Geom}(p)$ counts the number of trials until the first success in a sequence of independent Bernoulli trials: $P(X = k) = (1-p)^{k-1} p$ for $k = 1, 2, 3, \ldots$. The CDF is $F(k) = 1 - (1-p)^k$ by summing the geometric series. The geometric distribution has the memoryless property: $P(X > m + n \mid X > m) = P(X > n)$ for all $m, n \geq 0$. The proof is a direct computation: $P(X > m + n \mid X > m) = P(X > m+n) / P(X > m) = (1-p)^{m+n} / (1-p)^m = (1-p)^n = P(X > n)$. Among discrete distributions on the positive integers, the geometric is the unique distribution with this property.

The **Poisson distribution** $\text{Pois}(\lambda)$ arises as the limit of $\text{Bin}(n, \lambda/n)$ as $n \to \infty$ (the law of rare events). Its PMF is:

$$P(X = k) = \frac{\lambda^k e^{-\lambda}}{k!}, \quad k = 0, 1, 2, \ldots$$

The limit derivation is instructive. Fix $k$ and let $n \to \infty$ with $np \to \lambda$:

$$\binom{n}{k} p^k (1-p)^{n-k} = \frac{n(n-1)\cdots(n-k+1)}{k!} \left(\frac{\lambda}{n}\right)^k \left(1 - \frac{\lambda}{n}\right)^{n-k}.$$

The first factor approaches $\lambda^k / k!$ since $n(n-1)\cdots(n-k+1)/n^k \to 1$, and $(1 - \lambda/n)^{n-k} \to e^{-\lambda}$ since $(1-\lambda/n)^n \to e^{-\lambda}$ and $(1-\lambda/n)^{-k} \to 1$. The Poisson distribution models counts of rare events: photon arrivals in quantum optics, mutations in a genome, and packet arrivals in network traffic modeling. Its expectation and variance are both $\lambda$, a characterization property that we will prove using the moment generating function.

### Continuous Distributions and the Probability Density Function

A random variable $X$ is (absolutely) continuous if there exists a function $f_X : \mathbb{R} \to [0, \infty)$, the probability density function (PDF), such that:

$$P(X \in B) = \int_B f_X(x)\, dx \quad \text{for all } B \in \mathcal{B}(\mathbb{R}).$$

The PDF satisfies $\int_{-\infty}^{\infty} f_X(x)\, dx = 1$, and $F_X(x) = \int_{-\infty}^{x} f_X(t)\, dt$. Wherever $f_X$ is continuous, $F_X$ is differentiable with $F_X'(x) = f_X(x)$, and more generally $f_X(x) = F_X'(x)$ almost everywhere (Lebesgue's differentiation theorem). Probabilities are obtained by integrating the density over intervals: $P(a \leq X \leq b) = \int_a^b f_X(x)\, dx = F_X(b) - F_X(a)$.

The **Uniform distribution** $U(a, b)$ has constant density $f(x) = 1/(b-a)$ on $[a,b]$ and zero elsewhere. Its CDF is $F(x) = (x-a)/(b-a)$ for $x \in [a,b]$. The uniform is the simplest continuous distribution and serves as the foundation for inverse-transform sampling: if $U \sim U(0,1)$ and $F$ is a continuous CDF, then $X = F^{-1}(U)$ has CDF $F$. The proof is immediate: $P(X \leq x) = P(F^{-1}(U) \leq x) = P(U \leq F(x)) = F(x)$, since $P(U \leq u) = u$ for $u \in [0,1]$. This is the mechanism by which random number generators that produce uniform variates (e.g., Mersenne Twister) can simulate any continuous distribution.

The **Exponential distribution** $\text{Exp}(\lambda)$ has density $f(x) = \lambda e^{-\lambda x}$ for $x \geq 0$ and CDF $F(x) = 1 - e^{-\lambda x}$. Like its discrete counterpart, the geometric, the exponential is memoryless: $P(X > s + t \mid X > s) = P(X > t)$. The proof mirrors the geometric case: $P(X > s+t \mid X > s) = e^{-\lambda(s+t)} / e^{-\lambda s} = e^{-\lambda t} = P(X > t)$. Among continuous distributions on $[0, \infty)$, the exponential is the unique memoryless distribution (this follows from the functional equation $\bar{F}(s+t) = \bar{F}(s)\bar{F}(t)$ whose measurable solutions are exactly $e^{-\lambda t}$). The exponential distribution is the inter-arrival time distribution for a Poisson process: if $N(t)$ counts events in $[0,t]$ with $N(t) \sim \text{Pois}(\lambda t)$, then the time until the first event is $\text{Exp}(\lambda)$.

The **Normal (Gaussian) distribution** $\mathcal{N}(\mu, \sigma^2)$ has density:

$$f(x) = \frac{1}{\sigma\sqrt{2\pi}} \exp\!\left(-\frac{(x-\mu)^2}{2\sigma^2}\right), \quad x \in \mathbb{R}.$$

The normalizing constant $1/(\sigma\sqrt{2\pi})$ is derived by computing the Gaussian integral. Let $I = \int_{-\infty}^{\infty} e^{-x^2/2}\, dx$. Then:

$$I^2 = \int_{-\infty}^{\infty} \int_{-\infty}^{\infty} e^{-(x^2+y^2)/2}\, dx\, dy = \int_0^{2\pi} \int_0^{\infty} e^{-r^2/2} r\, dr\, d\theta = 2\pi \int_0^{\infty} r e^{-r^2/2}\, dr = 2\pi \cdot 1 = 2\pi,$$

so $I = \sqrt{2\pi}$, and the density integrates to 1. The substitution $z = (x - \mu)/\sigma$ transforms $\mathcal{N}(\mu, \sigma^2)$ to the standard normal $\mathcal{N}(0,1)$, whose CDF is $\Phi(z) = \int_{-\infty}^{z} \frac{1}{\sqrt{2\pi}} e^{-t^2/2}\, dt$. This integral has no closed form and is evaluated numerically, typically via the error function $\text{erf}(z) = \frac{2}{\sqrt{\pi}} \int_0^z e^{-t^2}\, dt$, with $\Phi(z) = \frac{1}{2}(1 + \text{erf}(z/\sqrt{2}))$.

The **Gamma distribution** $\Gamma(\alpha, \beta)$ generalizes the exponential with density:

$$f(x) = \frac{\beta^\alpha}{\Gamma(\alpha)} x^{\alpha - 1} e^{-\beta x}, \quad x > 0,$$

where $\Gamma(\alpha) = \int_0^{\infty} t^{\alpha-1} e^{-t}\, dt$ is the gamma function. When $\alpha = 1$, this reduces to $\text{Exp}(\beta)$; when $\alpha = n/2$ and $\beta = 1/2$, it gives the chi-squared distribution with $n$ degrees of freedom, which arises as the distribution of $\sum_{i=1}^n Z_i^2$ for independent standard normal $Z_i$.

### Expectation: The Linear Functional

The expectation (or expected value) of a random variable is its probability-weighted average. For a discrete $X$ with PMF $p_X$, the expectation is $E[X] = \sum_i x_i\, p_X(x_i)$, provided the sum converges absolutely (i.e., $\sum |x_i| p_X(x_i) < \infty$). For a continuous $X$ with density $f_X$, $E[X] = \int_{-\infty}^{\infty} x\, f_X(x)\, dx$, provided $\int |x| f_X(x)\, dx < \infty$. Absolute convergence is required so that the expectation is well-defined regardless of the order of summation or integration; conditional convergence would make the expectation dependent on the particular limiting procedure, which is unacceptable for a measure-theoretic quantity.

The most important property of expectation is **linearity**: $E[aX + bY] = aE[X] + bE[Y]$ for constants $a, b$ and random variables $X, Y$ (with finite expectations). Crucially, this holds *without any independence assumption*. The proof for the discrete case is:

$$E[aX + bY] = \sum_{i,j} (a x_i + b y_j) P(X = x_i, Y = y_j) = a \sum_i x_i \sum_j P(X = x_i, Y = y_j) + b \sum_j y_j \sum_i P(X = x_i, Y = y_j) = aE[X] + bE[Y],$$

where the inner sums recover the marginals $P(X = x_i)$ and $P(Y = y_j)$ respectively. The continuous case is proved by Fubini's theorem, which allows the interchange of the order of integration under the absolute convergence condition.

Linearity of expectation is the single most powerful tool in probabilistic combinatorics. The indicator method decomposes $X = \sum_{i=1}^n \mathbf{1}_{A_i}$ into indicators of events $A_i$, then $E[X] = \sum E[\mathbf{1}_{A_i}] = \sum P(A_i)$. For the binomial $X \sim \text{Bin}(n,p)$, write $X = \sum_{i=1}^n X_i$ with $X_i \sim \text{Bern}(p)$, so $E[X] = \sum E[X_i] = \sum p = np$. No independence is needed for this argument—only linearity. The variance, by contrast, does require independence for the simple formula.

The **Law of the Unconscious Statistician (LOTUS)** states that for any measurable function $g$, $E[g(X)] = \sum_i g(x_i) p_X(x_i)$ in the discrete case and $\int g(x) f_X(x)\, dx$ in the continuous case, without needing to derive the distribution of $g(X)$ first. This is not an additional axiom but a theorem: it follows from the change-of-variables formula for the pushforward measure $P_X$ and the definition of the Lebesgue integral.

### Variance, Covariance, and Correlation

The variance of $X$ is $\text{Var}(X) = E[(X - E[X])^2] = E[X^2] - (E[X])^2$. The second equality, sometimes called the computational formula, is derived by expanding the square:

$$E[(X - \mu)^2] = E[X^2 - 2\mu X + \mu^2] = E[X^2] - 2\mu E[X] + \mu^2 = E[X^2] - 2\mu^2 + \mu^2 = E[X^2] - \mu^2.$$

For independent $X$ and $Y$, $\text{Var}(X + Y) = \text{Var}(X) + \text{Var}(Y)$. The proof does not require independence but only that $\text{Cov}(X, Y) = 0$, which is guaranteed by independence. The covariance is $\text{Cov}(X, Y) = E[(X - E[X])(Y - E[Y])] = E[XY] - E[X]E[Y]$, and when $X$ and $Y$ are independent, $E[XY] = E[X]E[Y]$ (proved by Fubini's theorem or by factoring the joint PMF/density), so $\text{Cov}(X, Y) = 0$. The converse is false: $\text{Cov}(X, Y) = 0$ does not imply independence. For example, let $X \sim U(-1, 1)$ and $Y = X^2$. Then $\text{Cov}(X, Y) = E[X^3] - E[X]E[X^2] = 0 - 0 = 0$ (by symmetry of $X$), yet $Y$ is a deterministic function of $X$. Zero covariance means uncorrelated, not independent.

For the binomial $X \sim \text{Bin}(n,p)$ with $X = \sum X_i$ and $X_i \sim \text{Bern}(p)$ independent, $\text{Var}(X) = \sum \text{Var}(X_i) = n \cdot p(1-p)$, since each $\text{Var}(X_i) = E[X_i^2] - (E[X_i])^2 = p - p^2 = p(1-p)$ (using $X_i^2 = X_i$ for a 0-1 variable). For the Poisson $X \sim \text{Pois}(\lambda)$, we will show below via the MGF that $E[X] = \text{Var}(X) = \lambda$.

**Chebyshev's inequality** provides a distribution-free bound on tail probabilities. For any $X$ with finite mean $\mu$ and variance $\sigma^2$:

$$P(|X - \mu| \geq k) \leq \frac{\sigma^2}{k^2} \quad \text{for all } k > 0.$$

*Proof.* Let $Y = X - \mu$. Then $\text{Var}(X) = E[Y^2] = \int_0^\infty P(Y^2 \geq t)\, dt \geq \int_0^{k^2} P(Y^2 \geq k^2)\, dt = k^2 \cdot P(|Y| \geq k)$, where the inequality uses $P(Y^2 \geq t) \geq P(Y^2 \geq k^2)$ for $t \leq k^2$. Rearranging gives the result. Alternatively, $E[Y^2] \geq E[Y^2 \cdot \mathbf{1}_{|Y| \geq k}] \geq k^2 P(|Y| \geq k)$. $\blacksquare$

Chebyshev's inequality is the foundation of the Weak Law of Large Numbers, and although its bounds are often loose, its power lies in being completely distribution-free.

### Moment Generating Functions

The moment generating function (MGF) of $X$ is $M_X(t) = E[e^{tX}]$, defined for all $t$ where this expectation is finite. The MGF, when it exists in a neighborhood of $t = 0$, uniquely determines the distribution: if two distributions have the same MGF in an open interval containing zero, they are the same distribution. This follows from the uniqueness of the Laplace transform (a consequence of the uniqueness theorem for characteristic functions via analytic continuation, since $M_X(t) = \varphi_X(-it)$ where $\varphi_X$ is the characteristic function).

The name comes from the fact that $E[X^n] = M_X^{(n)}(0)$, the $n$-th derivative evaluated at zero. The derivation is by differentiating under the integral sign:

$$M_X^{(n)}(t) = \frac{d^n}{dt^n} E[e^{tX}] = E\!\left[\frac{d^n}{dt^n} e^{tX}\right] = E[X^n e^{tX}],$$

and evaluating at $t = 0$ gives $M_X^{(n)}(0) = E[X^n]$. Differentiation under the integral is justified by the dominated convergence theorem when $M_X(t)$ exists in a neighborhood of zero.

The MGF has a key convolution property: if $X$ and $Y$ are independent, then $M_{X+Y}(t) = M_X(t) \cdot M_Y(t)$. The proof is $E[e^{t(X+Y)}] = E[e^{tX} e^{tY}] = E[e^{tX}] E[e^{tY}]$ by independence (factoring the joint expectation). This makes the MGF the tool of choice for analyzing sums of independent random variables.

For the **Poisson distribution** $X \sim \text{Pois}(\lambda)$:

$$M_X(t) = \sum_{k=0}^{\infty} e^{tk} \frac{\lambda^k e^{-\lambda}}{k!} = e^{-\lambda} \sum_{k=0}^{\infty} \frac{(\lambda e^t)^k}{k!} = e^{-\lambda} e^{\lambda e^t} = e^{\lambda(e^t - 1)}.$$

The first derivative is $M_X'(t) = \lambda e^t e^{\lambda(e^t - 1)}$, so $E[X] = M_X'(0) = \lambda$. The second derivative is $M_X''(t) = (\lambda e^t + \lambda^2 e^{2t}) e^{\lambda(e^t - 1)}$, so $E[X^2] = M_X''(0) = \lambda + \lambda^2$, giving $\text{Var}(X) = E[X^2] - (E[X])^2 = \lambda + \lambda^2 - \lambda^2 = \lambda$.

For the **normal distribution** $X \sim \mathcal{N}(\mu, \sigma^2)$:

$$M_X(t) = \int_{-\infty}^{\infty} e^{tx} \frac{1}{\sigma\sqrt{2\pi}} e^{-(x-\mu)^2/(2\sigma^2)} dx.$$

Completing the square in the exponent: $tx - (x-\mu)^2/(2\sigma^2) = -(x - (\mu + \sigma^2 t))^2/(2\sigma^2) + \mu t + \sigma^2 t^2/2$. The integral of the Gaussian kernel is $\sigma\sqrt{2\pi}$, leaving:

$$M_X(t) = e^{\mu t + \sigma^2 t^2/2}.$$

From this, $M_X'(0) = \mu$ (so $E[X] = \mu$) and $M_X''(0) = \sigma^2 + \mu^2$ (so $E[X^2] = \sigma^2 + \mu^2$ and $\text{Var}(X) = \sigma^2$). The convolution property then shows that the sum of independent normals is normal: if $X_i \sim \mathcal{N}(\mu_i, \sigma_i^2)$ independently, then $M_{\sum X_i}(t) = \prod e^{\mu_i t + \sigma_i^2 t^2/2} = e^{(\sum \mu_i) t + (\sum \sigma_i^2) t^2/2}$, which is the MGF of $\mathcal{N}(\sum \mu_i, \sum \sigma_i^2)$. This is a foundational result for the Central Limit Theorem.

The cumulant generating function $K_X(t) = \log M_X(t)$ decomposes the MGF into cumulants: $K_X(t) = \sum_{n=1}^{\infty} \kappa_n \frac{t^n}{n!}$, where $\kappa_n$ is the $n$-th cumulant. The first cumulant $\kappa_1 = E[X]$ is the mean, $\kappa_2 = \text{Var}(X)$ is the variance, and $\kappa_3 = E[(X - \mu)^3]$ is the third central moment (skewness). For the normal distribution, $K_X(t) = \mu t + \sigma^2 t^2/2$, so all cumulants of order 3 and higher vanish—this is a characterization of the normal distribution. The vanishing of higher cumulants is what makes the normal distribution the universal attractor in the CLT.

### Joint Distributions and the Multivariate Normal

For random variables $X$ and $Y$, the joint CDF is $F_{X,Y}(x,y) = P(X \leq x, Y \leq y)$. In the discrete case, the joint PMF is $p_{X,Y}(x_i, y_j) = P(X = x_i, Y = y_j)$, and marginals are obtained by summing: $p_X(x_i) = \sum_j p_{X,Y}(x_i, y_j)$. In the continuous case, the joint density $f_{X,Y}(x,y)$ satisfies $P((X,Y) \in D) = \iint_D f_{X,Y}(x,y)\, dx\, dy$, and marginals are $f_X(x) = \int f_{X,Y}(x,y)\, dy$.

Conditional densities are defined via $f_{Y|X}(y \mid x) = f_{X,Y}(x,y) / f_X(x)$ (when $f_X(x) > 0$), which is the continuous analog of Bayes' theorem. The continuous version of the law of total probability is $f_Y(y) = \int f_{Y|X}(y \mid x) f_X(x)\, dx$.

The **multivariate normal** distribution $\mathcal{N}(\boldsymbol{\mu}, \boldsymbol{\Sigma})$ for $\boldsymbol{X} \in \mathbb{R}^n$ has density:

$$f(\mathbf{x}) = \frac{1}{(2\pi)^{n/2} |\boldsymbol{\Sigma}|^{1/2}} \exp\!\left(-\frac{1}{2}(\mathbf{x} - \boldsymbol{\mu})^T \boldsymbol{\Sigma}^{-1} (\mathbf{x} - \boldsymbol{\mu})\right),$$

where $\boldsymbol{\mu} \in \mathbb{R}^n$ is the mean vector and $\boldsymbol{\Sigma}$ is the $n \times n$ positive definite covariance matrix with entries $\Sigma_{ij} = \text{Cov}(X_i, X_j)$. The matrix $\boldsymbol{\Sigma}$ encodes all pairwise dependencies: diagonal entries are variances, off-diagonal entries are covariances, and the precision matrix $\boldsymbol{\Sigma}^{-1}$ (the inverse covariance) encodes conditional dependencies. This connection between the covariance matrix and conditional independence is the basis of Gaussian graphical models, where zeros in the precision matrix indicate conditional independence between variables given the rest.

A key property: uncorrelated jointly normal random variables are independent. If $\mathbf{X} \sim \mathcal{N}(\boldsymbol{\mu}, \boldsymbol{\Sigma})$ and $\Sigma_{ij} = 0$ for $i \neq j$, then $\boldsymbol{\Sigma}$ is diagonal, $\boldsymbol{\Sigma}^{-1}$ is diagonal, the joint density factors as a product of marginal densities, and $X_i$ and $X_j$ are independent. This is a special property of the normal distribution that does not hold in general.

The affine transformation property is central to applications. If $\mathbf{X} \sim \mathcal{N}(\boldsymbol{\mu}, \boldsymbol{\Sigma})$ and $\mathbf{Y} = \mathbf{A}\mathbf{X} + \mathbf{b}$ for a constant matrix $\mathbf{A}$ and vector $\mathbf{b}$, then $\mathbf{Y} \sim \mathcal{N}(\mathbf{A}\boldsymbol{\mu} + \mathbf{b}, \mathbf{A}\boldsymbol{\Sigma}\mathbf{A}^T)$. The proof uses the MGF: $M_{\mathbf{Y}}(\mathbf{t}) = E[e^{\mathbf{t}^T \mathbf{Y}}] = E[e^{\mathbf{t}^T(\mathbf{A}\mathbf{X}+\mathbf{b})}] = e^{\mathbf{t}^T \mathbf{b}} M_{\mathbf{X}}(\mathbf{A}^T \mathbf{t}) = e^{\mathbf{t}^T \mathbf{b}} e^{(\mathbf{A}^T\mathbf{t})^T \boldsymbol{\mu} + \frac{1}{2}(\mathbf{A}^T\mathbf{t})^T \boldsymbol{\Sigma} (\mathbf{A}^T\mathbf{t})} = e^{(\mathbf{A}\boldsymbol{\mu}+\mathbf{b})^T \mathbf{t} + \frac{1}{2}\mathbf{t}^T \mathbf{A}\boldsymbol{\Sigma}\mathbf{A}^T \mathbf{t}}$, which is the MGF of $\mathcal{N}(\mathbf{A}\boldsymbol{\mu}+\mathbf{b}, \mathbf{A}\boldsymbol{\Sigma}\mathbf{A}^T)$. This property underlies linear regression (where residuals are modeled as Gaussian), Kalman filtering (where the state and observation are jointly Gaussian and the posterior is computed in closed form by the Kalman update equations), and principal component analysis (where the eigendecomposition of $\boldsymbol{\Sigma}$ identifies the principal axes).

## 3. High-Performance Optimization & Failure Modes

### The Law of Large Numbers

The Law of Large Numbers (LLN) is the formalization of the intuition that sample averages converge to population expectations. The **Weak Law** states that if $X_1, X_2, \ldots$ are i.i.d. with $E[X_i] = \mu$ and $\text{Var}(X_i) = \sigma^2 < \infty$, then $\bar{X}_n = \frac{1}{n}\sum_{i=1}^n X_i$ converges in probability to $\mu$: for any $\varepsilon > 0$, $P(|\bar{X}_n - \mu| > \varepsilon) \to 0$ as $n \to \infty$.

*Proof (via Chebyshev).* Since $\text{Var}(\bar{X}_n) = \text{Var}(X_1/n + \cdots + X_n/n) = \sigma^2/n$ (using independence), Chebyshev's inequality gives $P(|\bar{X}_n - \mu| > \varepsilon) \leq \sigma^2/(n\varepsilon^2) \to 0$. $\blacksquare$

The **Strong Law** strengthens convergence in probability to almost sure convergence: $P(\lim_{n\to\infty} \bar{X}_n = \mu) = 1$. The proof of the strong law is substantially more involved and requires either the Borel-Cantelli lemmas or Kolmogorov's inequality (a maximal inequality for sums of independent random variables). The strong law implies the weak law but not vice versa, and the distinction matters: convergence in probability only guarantees that the probability of deviation goes to zero, while almost sure convergence guarantees that with probability one, the sequence eventually stays close to $\mu$ forever. For Monte Carlo integration, where we estimate $\int_0^1 g(x)\, dx \approx \frac{1}{n}\sum_{i=1}^n g(U_i)$ with $U_i \sim U(0,1)$, the strong law guarantees almost sure convergence of the estimator, while the weak law only guarantees convergence in distribution of the estimator.

### The Central Limit Theorem

The Central Limit Theorem (CLT) is the most important result in probability theory, and its statement is a marvel of mathematical economy: the sum of many independent, identically distributed random variables (with finite variance) converges in distribution to a normal random variable, regardless of the shape of the original distribution.

**Theorem (Lindeberg-Lévy CLT).** Let $X_1, X_2, \ldots$ be i.i.d. with $E[X_i] = \mu$ and $\text{Var}(X_i) = \sigma^2 \in (0, \infty)$. Then:

$$Z_n = \frac{\sum_{i=1}^n X_i - n\mu}{\sigma\sqrt{n}} \xrightarrow{d} \mathcal{N}(0, 1) \quad \text{as } n \to \infty.$$

*Proof (via MGFs).* Let $Y_i = (X_i - \mu)/\sigma$ so that $E[Y_i] = 0$, $E[Y_i^2] = 1$, and $Z_n = \frac{1}{\sqrt{n}} \sum_{i=1}^n Y_i$. The MGF of $Z_n$ is:

$$M_{Z_n}(t) = \left[M_{Y_1}\!\left(\frac{t}{\sqrt{n}}\right)\right]^n$$

by independence and identical distribution. Expanding $M_{Y_1}(s)$ around $s = 0$:

$$M_{Y_1}(s) = E[e^{sY_1}] = 1 + s \cdot E[Y_1] + \frac{s^2}{2} E[Y_1^2] + o(s^2) = 1 + \frac{s^2}{2} + o(s^2).$$

Therefore $M_{Y_1}(t/\sqrt{n}) = 1 + \frac{t^2}{2n} + o(1/n)$, and:

$$M_{Z_n}(t) = \left(1 + \frac{t^2}{2n} + o(1/n)\right)^n \to e^{t^2/2}$$

as $n \to \infty$, using the limit $(1 + a/n + o(1/n))^n \to e^a$. The limit $e^{t^2/2}$ is the MGF of $\mathcal{N}(0,1)$. By the continuity theorem (convergence of MGFs in a neighborhood of zero implies convergence in distribution), $Z_n \xrightarrow{d} \mathcal{N}(0,1)$. $\blacksquare$

The deeper version—the Lindeberg-Feller CLT—drops the identical distribution requirement and replaces it with the Lindeberg condition: for independent (not necessarily identically distributed) $X_i$ with $E[X_i] = 0$ and $\text{Var}(X_i) = \sigma_i^2$, let $s_n^2 = \sum_{i=1}^n \sigma_i^2$. The Lindeberg condition requires:

$$\frac{1}{s_n^2} \sum_{i=1}^n E\!\left[X_i^2 \cdot \mathbf{1}_{|X_i| > \varepsilon s_n}\right] \to 0 \quad \text{for all } \varepsilon > 0.$$

This condition ensures that no single term dominates the sum, which is the real content of the CLT: the limiting distribution is Gaussian if and only if the sum is not dominated by any single component. The Lindeberg condition is both necessary and sufficient (the Lindeberg-Feller theorem), making it a sharp characterization.

The practical consequence is that the CLT provides a universal approximation for sampling distributions. For a sample mean $\bar{X}_n$ from any distribution with finite variance, $\bar{X}_n \approx \mathcal{N}(\mu, \sigma^2/n)$ for large $n$. This is the basis for confidence intervals ($\bar{X}_n \pm z_{\alpha/2} \cdot \sigma/\sqrt{n}$), hypothesis testing (the $z$-test and $t$-test), and the bootstrap (which resamples the empirical distribution and relies on the CLT for the validity of percentile intervals). In signal processing, the CLT justifies modeling thermal noise as Gaussian, since it is the aggregate of many independent microscopic contributions. In statistical mechanics, the Maxwell-Boltzmann distribution of velocities is a Gaussian, derivable from the CLT applied to the many independent collisions a particle undergoes.

### Failure Mode: Heavy Tails and the Breakdown of the CLT

The CLT requires $\sigma^2 < \infty$. When the variance is infinite, the CLT fails, and the limit is not Gaussian but rather a stable distribution. The canonical example is the **Cauchy distribution**, with density $f(x) = \frac{1}{\pi(1+x^2)}$. The Cauchy has no mean (the integral $\int |x| f(x)\, dx = \infty$) and no variance. The sample mean $\bar{X}_n$ of Cauchy random variables has the same distribution as a single Cauchy random variable—averaging provides no concentration. The proof uses characteristic functions: $\varphi_X(t) = e^{-|t|}$, so $\varphi_{\bar{X}_n}(t) = (e^{-|t|/n})^n = e^{-|t|}$, which is the same characteristic function. This is a dramatic failure of the LLN: no amount of averaging reduces the variability of the sample mean.

More generally, distributions with power-law tails $P(|X| > x) \sim x^{-\alpha}$ for $0 < \alpha < 2$ have infinite variance and converge to $\alpha$-stable distributions rather than Gaussian ones. The Generalized Central Limit Theorem characterizes this: the sum of i.i.d. random variables with tail index $\alpha$ converges to a stable distribution with parameter $\alpha$, and the Gaussian case $\alpha = 2$ is a boundary case. The stable distributions have characteristic functions of the form $\varphi(t) = \exp(-|t|^\alpha (1 - i\beta \text{sgn}(t) \tan(\pi\alpha/2)))$ for $\alpha \neq 1$, where $\beta$ is a skewness parameter.

The practical implication is that in domains with heavy-tailed distributions—financial returns (where daily log-returns exhibit power-law tails with $\alpha \approx 3$), network traffic (with self-similar, long-range-dependent structure), and extreme value theory (floods, earthquakes, insurance losses)—the CLT-based Gaussian approximation is misleading. Confidence intervals based on $\sigma/\sqrt{n}$ will be too narrow, risk estimates will underestimate tail probabilities, and the sample mean will converge much more slowly than $\sqrt{n}$. The correct tools in these regimes are extreme value theory (the Fisher-Tippett-Gnedenko theorem for maxima, with the generalized extreme value distribution), robust estimation (using medians and trimmed means whose breakdown points are higher), and stable distribution fitting.

### Failure Mode: MGF Non-Existence

The MGF $M_X(t) = E[e^{tX}]$ may not exist for any $t \neq 0$. The log-normal distribution, with density $f(x) = \frac{1}{x\sigma\sqrt{2\pi}} e^{-(\ln x - \mu)^2/(2\sigma^2)}$ for $x > 0$, provides the classic example. Its moments all exist ($E[X^n] = e^{n\mu + n^2\sigma^2/2}$), yet $E[e^{tX}] = \infty$ for all $t > 0$. The reason is that $e^{tx}$ grows faster than any polynomial in $x$, while the log-normal density decays like $e^{-(\ln x)^2/(2\sigma^2)}$, which is slower than any power of $x$ in the sense that $x^{-p} e^{-(\ln x)^2/(2\sigma^2)} \to 0$ slower than $e^{-tx}$ grows. Concretely, substituting $u = \ln x$ gives $E[e^{tX}] = \frac{1}{\sigma\sqrt{2\pi}} \int_{-\infty}^{\infty} e^{te^u} e^{-(u-\mu)^2/(2\sigma^2)} du$, and $te^u - (u-\mu)^2/(2\sigma^2) \to +\infty$ as $u \to +\infty$ for any $t > 0$, so the integral diverges.

This means that the MGF cannot be used to identify the log-normal distribution, and the moment problem for the log-normal is *indeterminate*: there exist other distributions with the same sequence of moments. This is the Stieltjes moment problem, and the log-normal is the standard example of a distribution that is not uniquely determined by its moments. The correct tool in this situation is the characteristic function $\varphi_X(t) = E[e^{itX}]$, which exists for *all* distributions (since $|e^{itX}| = 1$) and uniquely determines the distribution via the Lévy inversion theorem. The characteristic function plays the role of the MGF in the full generality of probability theory, and the CLT proof above can be reformulated entirely in terms of characteristic functions, which is the approach taken in rigorous treatments (e.g., Durrett, Billingsley).

### Failure Mode: Correlation, Dependence, and Misapplied Independence

The CLT and LLN require independence. When observations are dependent, the effective sample size is smaller than $n$, and the standard $\sigma/\sqrt{n}$ confidence interval is too narrow. The correction is to use the effective sample size $n_{\text{eff}} = n / (1 + 2\sum_{k=1}^{\infty} \rho_k)$, where $\rho_k$ is the lag-$k$ autocorrelation. For an AR(1) process $X_t = \phi X_{t-1} + \epsilon_t$ with $|\phi| < 1$, $\rho_k = \phi^k$, and $n_{\text{eff}} = n(1-\phi)/(1+\phi)$, which can be dramatically smaller than $n$ when $\phi$ is close to 1.

A subtler failure occurs with exchangeable sequences that are not independent. De Finetti's theorem states that an infinite exchangeable sequence is conditionally i.i.d. given a latent parameter $\theta$, but the unconditional (marginal) distribution of $\bar{X}_n$ has larger variance than the i.i.d. case because of the additional uncertainty in $\theta$. Ignoring this overdispersion leads to underestimating uncertainty, a common error in hierarchical models and in meta-analysis where between-study heterogeneity is present.

The distinction between uncorrelated and independent also causes failures. In numerical integration via quasi-Monte Carlo methods, low-discrepancy sequences (Sobol, Halton) produce samples that are deterministically uncorrelated but not independent, and the convergence rate can be $O((\log n)^d / n)$ rather than $O(1/\sqrt{n})$, which is faster for moderate dimensions $d$. However, the Koksma-Hlawka inequality that bounds the integration error depends on the total variation of the integrand, and for functions with singularities or high variation, the advantage of quasi-Monte Carlo disappears.

### Convergence Modes and Their Hierarchy

The distinction between convergence in distribution, convergence in probability, convergence in $L^p$, and almost sure convergence is not pedantic—it determines which operations are valid. Convergence in distribution ($\xrightarrow{d}$) is the weakest: $X_n \xrightarrow{d} X$ means $F_{X_n}(x) \to F_X(x)$ at all continuity points of $F_X$. This does not imply that $X_n$ and $X$ are defined on the same probability space, and it is not preserved under continuous mapping of joint distributions unless joint convergence is established. Convergence in probability ($\xrightarrow{p}$) is stronger: $P(|X_n - X| > \varepsilon) \to 0$ for all $\varepsilon > 0$, and it does require a common probability space. Convergence in $L^p$ ($\xrightarrow{L^p}$) means $E[|X_n - X|^p] \to 0$ and implies convergence in probability by Markov's inequality: $P(|X_n - X| > \varepsilon) \leq E[|X_n - X|^p] / \varepsilon^p \to 0$. Almost sure convergence ($\xrightarrow{a.s.}$) means $P(X_n \to X) = 1$ and implies convergence in probability. The hierarchy is:

$$\xrightarrow{L^p} \implies \xrightarrow{p} \implies \xrightarrow{d}, \quad \xrightarrow{a.s.} \implies \xrightarrow{p} \implies \xrightarrow{d}.$$

The Scheffé lemma provides a useful tool: if $f_n \to f$ pointwise and $\int f_n \to \int f$ (both being densities), then $\int |f_n - f| \to 0$, which is $L^1$ convergence of densities. Slutsky's theorem states that if $X_n \xrightarrow{d} X$ and $Y_n \xrightarrow{p} c$ (constant), then $X_n + Y_n \xrightarrow{d} X + c$ and $X_n Y_n \xrightarrow{d} cX$. This is used constantly in statistical applications: if $\bar{X}_n \xrightarrow{d} \mathcal{N}(\mu, \sigma^2/n)$ and $S_n^2 \xrightarrow{p} \sigma^2$ (by the LLN applied to $(X_i - \bar{X}_n)^2$), then $\sqrt{n}(\bar{X}_n - \mu)/S_n \xrightarrow{d} \mathcal{N}(0,1)$, which is the theoretical basis for the $t$-test.

The continuous mapping theorem states that if $X_n \xrightarrow{d} X$ and $g$ is continuous (or continuous a.s. with respect to the distribution of $X$), then $g(X_n) \xrightarrow{d} g(X)$. This is used to derive the distribution of transformed statistics: if $\bar{X}_n \xrightarrow{d} \mathcal{N}(\mu, \sigma^2/n)$, then $e^{\bar{X}_n} \xrightarrow{d} \text{Lognormal}(\mu, \sigma^2/n)$, and $\bar{X}_n^2 \xrightarrow{p} \mu^2$. The delta method extends this to smooth transformations: if $\sqrt{n}(\bar{X}_n - \mu) \xrightarrow{d} \mathcal{N}(0, \sigma^2)$ and $g$ is differentiable at $\mu$ with $g'(\mu) \neq 0$, then $\sqrt{n}(g(\bar{X}_n) - g(\mu)) \xrightarrow{d} \mathcal{N}(0, \sigma^2 [g'(\mu)]^2)$. The proof uses the first-order Taylor expansion $g(\bar{X}_n) - g(\mu) \approx g'(\mu)(\bar{X}_n - \mu)$ and Slutsky's theorem.

The delta method is the mechanism behind variance-stabilizing transformations. For a Poisson sample $X_i \sim \text{Pois}(\lambda)$, $\text{Var}(\bar{X}_n) = \lambda/n$ depends on the parameter $\lambda$, violating the homoscedasticity assumption of many statistical procedures. Applying $g(x) = \sqrt{x}$ (so $g'(\lambda) = 1/(2\sqrt{\lambda})$) gives $\sqrt{n}(\sqrt{\bar{X}_n} - \sqrt{\lambda}) \xrightarrow{d} \mathcal{N}(0, \lambda \cdot 1/(4\lambda)) = \mathcal{N}(0, 1/4)$, so the variance of $\sqrt{\bar{X}_n}$ is approximately $1/(4n)$, independent of $\lambda$. This transformation stabilizes the variance and is used in ANOVA for count data. Similar transformations exist for the binomial (arcsine transformation $g(p) = \arcsin\sqrt{p}$) and the correlation coefficient (Fisher's $z$-transform $g(r) = \frac{1}{2}\ln\frac{1+r}{1-r}$), each derived by solving the differential equation $[g'(\mu)]^2 \text{Var}(X) = \text{const}$ for $g$.

### Computational Considerations in Practice

The numerical evaluation of distribution functions requires care. The normal CDF $\Phi$ has no closed form and is computed via rational approximations (the Abramowitz and Stegun approximation, or the Wichura AS241 algorithm for high precision). The inverse $\Phi^{-1}$ (needed for quantile-based confidence intervals and QQ-plots) is computed via the Acklam algorithm or, for high precision, via Newton's method with a rational starting approximation. The gamma function $\Gamma(\alpha)$ is computed via the Lanczos approximation for moderate $\alpha$ and via Stirling's series for large $\alpha$, with the log-gamma function $\ln \Gamma(\alpha)$ preferred to avoid overflow. The incomplete gamma function $P(a, x) = \frac{1}{\Gamma(a)} \int_0^x t^{a-1} e^{-t}\, dt$ (needed for the gamma CDF and chi-squared tests) is computed via series expansion for $x < a + 1$ and continued fraction expansion for $x \geq a + 1$, a switch that maintains numerical stability across the parameter space.

For sampling, the inverse-transform method (uniform to any continuous distribution via $F^{-1}$) is universal but inefficient when $F^{-1}$ is expensive. Rejection sampling (von Neumann's method) generates samples from a distribution $f$ by proposing from an envelope $g$ and accepting with probability $f(x)/(cg(x))$, where $c \geq 1$ is chosen so $f(x) \leq c \cdot g(x)$ for all $x$. The acceptance rate is $1/c$, so a tight envelope is essential. The Box-Muller method generates two independent standard normals from two uniforms: $Z_1 = \sqrt{-2\ln U_1}\cos(2\pi U_2)$ and $Z_2 = \sqrt{-2\ln U_1}\sin(2\pi U_2)$, which follows from transforming to polar coordinates and using the independence of the radius and angle of a bivariate normal. The Marsaglia polar method is a variant that avoids the trigonometric calls by using rejection on the unit disk, trading one uniform for the cost of a rejection, and is faster in practice because the trigonometric evaluations are replaced by a simple rejection step.

The Alias method (Walker's algorithm) samples from a discrete distribution over $n$ outcomes in $O(1)$ time per sample after $O(n)$ preprocessing, by constructing a table of alias probabilities that partitions the unit interval into $n$ segments, each associated with two outcomes. This is the optimal approach for repeated sampling from a fixed discrete distribution (e.g., sampling from a large categorical distribution in natural language models or in Monte Carlo tree search), where the preprocessing cost is amortized over many samples.
