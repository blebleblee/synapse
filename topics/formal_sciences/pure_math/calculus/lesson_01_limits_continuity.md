# Lesson 1: Limits, Continuity, Rigorous Foundations

## 1. First-Principles Intuition & Invariants

The development of rigorous calculus in the nineteenth century represents one of mathematics' greatest triumphs over intuition. For nearly two centuries after Newton and Leibniz, calculus operated on geometrical intuition and infinitesimal reasoning—powerful heuristics that produced correct results but rested on logical quicksand. The function $f(x) = \sin(1/x)$ near zero, which oscillates infinitely many times in any neighborhood of the origin, or Dirichlet's function $D(x)$ which equals one on rationals and zero on irrationals, exposed the inadequacy of naive approaches. These pathological cases forced mathematicians to construct calculus from the ground up using the language of sets, sequences, and logical quantifiers.

The epsilon-delta framework, crystallized by Weierstrass in the 1860s, transformed calculus from an art into a science. At its core lies a single profound insight: we can capture the notion of "arbitrarily close" using a game between two players. Given a challenge tolerance $\varepsilon > 0$ (epsilon, representing how close we demand the output to be), we must produce a response radius $\delta > 0$ (delta, controlling how close the input must be) such that staying within $\delta$ of our target point guarantees staying within $\varepsilon$ of our target value. This formulation eliminates all appeals to motion, infinitesimals, or geometric intuition, grounding limits purely in the algebra of inequalities over the real numbers.

The construction rests on the completeness axiom of the real numbers: every nonempty set of real numbers that is bounded above has a least upper bound (supremum). This single axiom distinguishes $\mathbb{R}$ from $\mathbb{Q}$ and enables the fundamental theorems of calculus. Without completeness, sequences like the decimal expansion of $\sqrt{2}$ would fail to converge, the intermediate value theorem would fail (consider $f(x) = x^2 - 2$ over the rationals), and the entire edifice would collapse. Completeness ensures that Cauchy sequences converge, monotone bounded sequences converge, and nested closed intervals have nonempty intersection—three equivalent characterizations that we exploit throughout analysis.

Every limit statement translates into a quantified logical assertion. When we write $\lim_{x \to c} f(x) = L$, we mean: for all $\varepsilon > 0$, there exists $\delta > 0$ such that for all $x$ satisfying $0 < |x - c| < \delta$, we have $|f(x) - L| < \varepsilon$. The quantifier structure $\forall \varepsilon > 0 \, \exists \delta > 0 \, \forall x$ encodes the adversarial game: the challenger picks any positive $\varepsilon$ (no matter how small), we respond with a $\delta$, and our response must work for all $x$ in the punctured $\delta$-neighborhood of $c$. The punctured condition $0 < |x - c|$ is critical—it excludes the point $c$ itself, allowing us to define limits at points where the function is undefined or discontinuous, such as $\lim_{x \to 0} \frac{\sin x}{x} = 1$ despite the function being undefined at zero.

Continuity represents the natural refinement where the limit value matches the function value. A function $f: \mathbb{R} \to \mathbb{R}$ is continuous at $c$ if $\lim_{x \to c} f(x) = f(c)$, which unpacks to: for all $\varepsilon > 0$, there exists $\delta > 0$ such that for all $x$ satisfying $|x - c| < \delta$, we have $|f(x) - f(c)| < \varepsilon$. Note the absence of the punctured condition—continuity includes the point itself. This definition formalizes the intuition that small changes in input produce small changes in output, but with precise quantitative control. The function $f(x) = x^2$ is continuous everywhere because given $\varepsilon > 0$ and a point $c$, we can choose $\delta = \min(1, \varepsilon/(2|c| + 1))$ and verify through algebraic manipulation that $|x - c| < \delta$ implies $|x^2 - c^2| < \varepsilon$.

The sequential characterization of limits provides an equivalent but often more tractable perspective. A function satisfies $\lim_{x \to c} f(x) = L$ if and only if for every sequence $(x_n)$ with $x_n \to c$ and $x_n \neq c$, we have $f(x_n) \to L$. This equivalence, which we will prove rigorously, allows us to leverage sequence convergence machinery—a simpler object than function limits since sequences involve only the natural numbers as a domain. To show a limit does not exist, we need only exhibit two sequences approaching $c$ along which the function approaches different values. For instance, $\lim_{x \to 0} \sin(1/x)$ does not exist because the sequences $x_n = 1/(2\pi n)$ and $y_n = 1/(\pi/2 + 2\pi n)$ both approach zero, yet $\sin(1/x_n) = 0$ while $\sin(1/y_n) = 1$.

The distinction between pointwise and uniform continuity becomes crucial when studying function spaces and constructing Riemann integrals. A function $f: [a,b] \to \mathbb{R}$ is uniformly continuous if for all $\varepsilon > 0$, there exists $\delta > 0$ such that for all $x, y \in [a,b]$ satisfying $|x - y| < \delta$, we have $|f(x) - f(y)| < \varepsilon$. The quantifier structure has shifted: $\forall \varepsilon > 0 \, \exists \delta > 0 \, \forall x, y$ versus pointwise continuity's $\forall \varepsilon > 0 \, \forall c \in [a,b] \, \exists \delta > 0 \, \forall x$. In uniform continuity, a single $\delta$ must work simultaneously for all points in the domain, whereas pointwise continuity permits $\delta$ to depend on both $\varepsilon$ and the specific point $c$. The function $f(x) = x^2$ on $\mathbb{R}$ is continuous everywhere but not uniformly continuous—as $x$ grows large, we need progressively smaller $\delta$ values to control the quadratic growth. However, every continuous function on a compact interval $[a,b]$ is uniformly continuous, a profound result we establish through the Heine-Cantor theorem.

## 2. Core Architecture & Mechanics

We now construct the epsilon-delta machinery from axioms, proving the fundamental limit laws and their consequences. Throughout, we work within the real number system $\mathbb{R}$ equipped with the standard metric $d(x,y) = |x - y|$ and assume the completeness axiom.

**Definition (Limit of a Function).** Let $f: D \to \mathbb{R}$ where $D \subseteq \mathbb{R}$, let $c$ be a limit point of $D$ (meaning every punctured neighborhood of $c$ contains points of $D$), and let $L \in \mathbb{R}$. We write $\lim_{x \to c} f(x) = L$ if:

$$\forall \varepsilon > 0 \, \exists \delta > 0 \, \forall x \in D : \left(0 < |x - c| < \delta \implies |f(x) - L| < \varepsilon\right)$$

The requirement that $c$ be a limit point ensures we can approach $c$ from within the domain $D$, though $c$ itself need not belong to $D$. For example, in defining $\lim_{x \to 0} \frac{\sin x}{x}$, the domain is $\mathbb{R} \setminus \{0\}$ but zero is a limit point.

**Theorem (Uniqueness of Limits).** If $\lim_{x \to c} f(x) = L$ and $\lim_{x \to c} f(x) = M$, then $L = M$.

*Proof.* Assume for contradiction that $L \neq M$, so $|L - M| = \varepsilon_0 > 0$. Set $\varepsilon = \varepsilon_0/2$. By the limit definition, there exists $\delta_1 > 0$ such that $0 < |x - c| < \delta_1$ implies $|f(x) - L| < \varepsilon$, and there exists $\delta_2 > 0$ such that $0 < |x - c| < \delta_2$ implies $|f(x) - M| < \varepsilon$. Let $\delta = \min(\delta_1, \delta_2)$ and choose any $x$ with $0 < |x - c| < \delta$ (such $x$ exists since $c$ is a limit point). Then:

$$|L - M| = |L - f(x) + f(x) - M| \leq |L - f(x)| + |f(x) - M| < \varepsilon + \varepsilon = \varepsilon_0$$

But $|L - M| = \varepsilon_0$, yielding the contradiction $\varepsilon_0 < \varepsilon_0$. Therefore $L = M$. $\square$

**Theorem (Limit Laws).** Suppose $\lim_{x \to c} f(x) = L$ and $\lim_{x \to c} g(x) = M$. Then:

1. **Sum Law:** $\lim_{x \to c} [f(x) + g(x)] = L + M$
2. **Product Law:** $\lim_{x \to c} [f(x) \cdot g(x)] = L \cdot M$
3. **Quotient Law:** If $M \neq 0$, then $\lim_{x \to c} \frac{f(x)}{g(x)} = \frac{L}{M}$
4. **Scalar Multiple Law:** For any $k \in \mathbb{R}$, $\lim_{x \to c} k f(x) = k L$

*Proof of Sum Law.* Let $\varepsilon > 0$. We must produce $\delta > 0$ such that $0 < |x - c| < \delta$ implies $|(f(x) + g(x)) - (L + M)| < \varepsilon$. Since $\lim_{x \to c} f(x) = L$, there exists $\delta_1 > 0$ such that $0 < |x - c| < \delta_1$ implies $|f(x) - L| < \varepsilon/2$. Since $\lim_{x \to c} g(x) = M$, there exists $\delta_2 > 0$ such that $0 < |x - c| < \delta_2$ implies $|g(x) - M| < \varepsilon/2$. Set $\delta = \min(\delta_1, \delta_2)$. Then for $0 < |x - c| < \delta$:

$$|(f(x) + g(x)) - (L + M)| = |(f(x) - L) + (g(x) - M)| \leq |f(x) - L| + |g(x) - M| < \frac{\varepsilon}{2} + \frac{\varepsilon}{2} = \varepsilon$$

This completes the proof. $\square$

*Proof of Product Law.* Let $\varepsilon > 0$. We use the algebraic identity:

$$f(x) \cdot g(x) - L \cdot M = f(x) \cdot g(x) - L \cdot g(x) + L \cdot g(x) - L \cdot M = (f(x) - L) \cdot g(x) + L \cdot (g(x) - M)$$

Therefore:

$$|f(x) \cdot g(x) - L \cdot M| \leq |f(x) - L| \cdot |g(x)| + |L| \cdot |g(x) - M|$$

Since $\lim_{x \to c} g(x) = M$, there exists $\delta_0 > 0$ such that $0 < |x - c| < \delta_0$ implies $|g(x) - M| < 1$, hence $|g(x)| < |M| + 1$ by the triangle inequality. Set $B = \max(|M| + 1, |L|, 1)$. Choose $\delta_1 > 0$ such that $0 < |x - c| < \delta_1$ implies $|f(x) - L| < \varepsilon/(2B)$, and $\delta_2 > 0$ such that $0 < |x - c| < \delta_2$ implies $|g(x) - M| < \varepsilon/(2B)$. Let $\delta = \min(\delta_0, \delta_1, \delta_2)$. Then for $0 < |x - c| < \delta$:

$$|f(x) \cdot g(x) - L \cdot M| \leq |f(x) - L| \cdot |g(x)| + |L| \cdot |g(x) - M| < \frac{\varepsilon}{2B} \cdot B + B \cdot \frac{\varepsilon}{2B} = \varepsilon$$

This completes the proof. $\square$

The quotient law follows from the product law once we establish that $\lim_{x \to c} 1/g(x) = 1/M$ when $M \neq 0$. We omit the technical details but note the key inequality: if $|g(x) - M| < |M|/2$, then $|g(x)| > |M|/2$, ensuring $1/g(x)$ remains bounded near $c$.

**Theorem (Squeeze Theorem).** Suppose $f(x) \leq g(x) \leq h(x)$ for all $x$ in some punctured neighborhood of $c$, and $\lim_{x \to c} f(x) = \lim_{x \to c} h(x) = L$. Then $\lim_{x \to c} g(x) = L$.

*Proof.* Let $\varepsilon > 0$. There exists $\delta_1 > 0$ such that $0 < |x - c| < \delta_1$ implies $|f(x) - L| < \varepsilon$, hence $L - \varepsilon < f(x) < L + \varepsilon$. There exists $\delta_2 > 0$ such that $0 < |x - c| < \delta_2$ implies $|h(x) - L| < \varepsilon$, hence $L - \varepsilon < h(x) < L + \varepsilon$. Let $\delta = \min(\delta_1, \delta_2)$. For $0 < |x - c| < \delta$:

$$L - \varepsilon < f(x) \leq g(x) \leq h(x) < L + \varepsilon$$

Therefore $|g(x) - L| < \varepsilon$, establishing $\lim_{x \to c} g(x) = L$. $\square$

We now establish the sequential characterization, which provides a bridge between function limits and sequence limits.

**Theorem (Sequential Characterization of Limits).** Let $f: D \to \mathbb{R}$ and let $c$ be a limit point of $D$. Then $\lim_{x \to c} f(x) = L$ if and only if for every sequence $(x_n)$ in $D \setminus \{c\}$ with $\lim_{n \to \infty} x_n = c$, we have $\lim_{n \to \infty} f(x_n) = L$.

*Proof (Forward Direction).* Assume $\lim_{x \to c} f(x) = L$ and let $(x_n)$ be any sequence in $D \setminus \{c\}$ with $x_n \to c$. We must show $f(x_n) \to L$. Let $\varepsilon > 0$. Since $\lim_{x \to c} f(x) = L$, there exists $\delta > 0$ such that $0 < |x - c| < \delta$ implies $|f(x) - L| < \varepsilon$. Since $x_n \to c$, there exists $N$ such that $n \geq N$ implies $|x_n - c| < \delta$. Since $x_n \neq c$, we have $0 < |x_n - c| < \delta$ for $n \geq N$, hence $|f(x_n) - L| < \varepsilon$. This proves $f(x_n) \to L$.

*Proof (Reverse Direction, Contrapositive).* Assume $\lim_{x \to c} f(x) \neq L$. Then the negation of the limit definition holds: there exists $\varepsilon_0 > 0$ such that for all $\delta > 0$, there exists $x$ with $0 < |x - c| < \delta$ yet $|f(x) - L| \geq \varepsilon_0$. For each $n \in \mathbb{N}$, set $\delta = 1/n$ and choose $x_n \in D$ with $0 < |x_n - c| < 1/n$ and $|f(x_n) - L| \geq \varepsilon_0$. Then $(x_n)$ is a sequence in $D \setminus \{c\}$ with $x_n \to c$ (since $|x_n - c| < 1/n \to 0$), but $f(x_n) \not\to L$ (since $|f(x_n) - L| \geq \varepsilon_0$ for all $n$). This completes the contrapositive. $\square$

The sequential characterization immediately implies that if two sequences approaching $c$ yield different function values in the limit, the function limit does not exist. This technique efficiently handles many discontinuous functions.

**Definition (Continuity).** A function $f: D \to \mathbb{R}$ is continuous at $c \in D$ if $\lim_{x \to c} f(x) = f(c)$, which unpacks to:

$$\forall \varepsilon > 0 \, \exists \delta > 0 \, \forall x \in D : \left(|x - c| < \delta \implies |f(x) - f(c)| < \varepsilon\right)$$

Note that continuity requires $c \in D$ (so $f(c)$ is defined) and uses the non-punctured condition $|x - c| < \delta$.

Equivalently, by the sequential characterization, $f$ is continuous at $c$ if and only if for every sequence $(x_n)$ in $D$ with $x_n \to c$, we have $f(x_n) \to f(c)$. This formulation often simplifies proofs.

**Theorem (Composition of Continuous Functions).** If $f: D \to \mathbb{R}$ is continuous at $c \in D$ and $g: E \to \mathbb{R}$ is continuous at $f(c)$ where $f(D) \subseteq E$, then $g \circ f: D \to \mathbb{R}$ is continuous at $c$.

*Proof.* Let $\varepsilon > 0$. Since $g$ is continuous at $f(c)$, there exists $\eta > 0$ such that $|y - f(c)| < \eta$ implies $|g(y) - g(f(c))| < \varepsilon$. Since $f$ is continuous at $c$, there exists $\delta > 0$ such that $|x - c| < \delta$ implies $|f(x) - f(c)| < \eta$. Combining these: if $|x - c| < \delta$, then $|f(x) - f(c)| < \eta$, hence $|g(f(x)) - g(f(c))| < \varepsilon$. Therefore $g \circ f$ is continuous at $c$. $\square$

This theorem justifies the standard calculus chain rule intuition and allows us to build complex continuous functions from simpler pieces. The polynomials, rational functions (away from zero denominators), trigonometric functions, exponentials, and logarithms are all continuous on their natural domains, and compositions of these remain continuous.

**Definition (Uniform Continuity).** A function $f: D \to \mathbb{R}$ is uniformly continuous on $D$ if:

$$\forall \varepsilon > 0 \, \exists \delta > 0 \, \forall x, y \in D : \left(|x - y| < \delta \implies |f(x) - f(y)| < \varepsilon\right)$$

The quantifier order $\forall \varepsilon \, \exists \delta \, \forall x, y$ means a single $\delta$ works uniformly for all pairs of points, independent of location in the domain.

**Example (Non-Uniform Continuity).** Consider $f(x) = x^2$ on $\mathbb{R}$. This function is continuous everywhere but not uniformly continuous. To see why, fix $\varepsilon = 1$ and suppose for contradiction that some $\delta > 0$ works uniformly. Choose $N > 1/\delta$ and set $x = N$, $y = N + \delta/2$. Then $|x - y| = \delta/2 < \delta$, yet:

$$|f(x) - f(y)| = |N^2 - (N + \delta/2)^2| = |N^2 - N^2 - N\delta - \delta^2/4| = N\delta + \delta^2/4 > N\delta > \frac{1}{\delta} \cdot \delta = 1 = \varepsilon$$

This contradicts uniform continuity. The failure occurs because as $N$ grows, we need progressively smaller $\delta$ to control the quadratic growth, but uniform continuity demands a fixed $\delta$ independent of location.

**Theorem (Heine-Cantor).** Every continuous function $f: [a,b] \to \mathbb{R}$ on a closed bounded interval is uniformly continuous.

*Proof.* Assume for contradiction that $f$ is not uniformly continuous. Then there exists $\varepsilon_0 > 0$ such that for all $\delta > 0$, there exist $x, y \in [a,b]$ with $|x - y| < \delta$ yet $|f(x) - f(y)| \geq \varepsilon_0$. For each $n \in \mathbb{N}$, choose $x_n, y_n \in [a,b]$ with $|x_n - y_n| < 1/n$ and $|f(x_n) - f(y_n)| \geq \varepsilon_0$.

Since $(x_n)$ is a bounded sequence in $[a,b]$, by the Bolzano-Weierstrass theorem, there exists a convergent subsequence $x_{n_k} \to c$ for some $c \in [a,b]$. For this subsequence, $|y_{n_k} - c| \leq |y_{n_k} - x_{n_k}| + |x_{n_k} - c| < 1/n_k + |x_{n_k} - c| \to 0$, hence $y_{n_k} \to c$ as well. By continuity of $f$ at $c$, we have $f(x_{n_k}) \to f(c)$ and $f(y_{n_k}) \to f(c)$, hence $|f(x_{n_k}) - f(y_{n_k})| \to 0$. But $|f(x_{n_k}) - f(y_{n_k})| \geq \varepsilon_0$ for all $k$, a contradiction. Therefore $f$ is uniformly continuous. $\square$

This result critically depends on the compactness of $[a,b]$. The proof technique—extracting a convergent subsequence via Bolzano-Weierstrass—appears throughout analysis and forms the core of many existence theorems.

## 3. High-Performance Optimization & Failure Modes

We now establish the two fundamental existence theorems for continuous functions on compact intervals: the Intermediate Value Theorem (IVT) and the Extreme Value Theorem (EVT). These results underpin root-finding algorithms, optimization procedures, and fixed-point iterations across computational mathematics.

**Theorem (Intermediate Value Theorem).** Let $f: [a,b] \to \mathbb{R}$ be continuous with $f(a) \neq f(b)$. For any value $L$ strictly between $f(a)$ and $f(b)$, there exists $c \in (a,b)$ such that $f(c) = L$.

*Proof.* Without loss of generality, assume $f(a) < L < f(b)$ (the case $f(a) > L > f(b)$ follows by considering $-f$). Define the set:

$$S = \{x \in [a,b] : f(x) < L\}$$

Note that $a \in S$ (since $f(a) < L$), so $S$ is nonempty, and $S$ is bounded above by $b$. By the completeness axiom, $S$ has a least upper bound; let $c = \sup S$. We have $a \leq c \leq b$.

We claim that $f(c) = L$. Assume for contradiction that $f(c) \neq L$. 

**Case 1:** Suppose $f(c) < L$. Let $\varepsilon = L - f(c) > 0$. By continuity of $f$ at $c$, there exists $\delta > 0$ such that $|x - c| < \delta$ implies $|f(x) - f(c)| < \varepsilon$. In particular, for $x \in (c, c+\delta) \cap [a,b]$, we have $f(x) < f(c) + \varepsilon = L$, hence $x \in S$. But this contradicts $c = \sup S$ since we found elements of $S$ larger than $c$.

**Case 2:** Suppose $f(c) > L$. Let $\varepsilon = f(c) - L > 0$. By continuity at $c$, there exists $\delta > 0$ such that $|x - c| < \delta$ implies $|f(x) - f(c)| < \varepsilon$, hence $f(x) > f(c) - \varepsilon = L$. This means $(c - \delta, c + \delta) \cap [a,b]$ contains no elements of $S$, so $c - \delta/2$ is an upper bound for $S$, contradicting $c = \sup S$.

Both cases yield contradictions, so we must have $f(c) = L$. Since $f(a) < L$ and $f(b) > L$, we have $a < c < b$, completing the proof. $\square$

The IVT is not merely an existence theorem—it provides the theoretical foundation for bisection root-finding algorithms. Given a continuous function $f$ with $f(a)$ and $f(b)$ of opposite signs, the IVT guarantees a root in $(a,b)$. Bisection iteratively narrows the interval by testing the midpoint, halving the search space at each step. After $n$ iterations, the interval width is $(b-a)/2^n$, giving linear convergence (in the logarithmic sense). More sophisticated methods like Newton-Raphson achieve quadratic convergence but sacrifice the IVT's guaranteed convergence.

**Theorem (Extreme Value Theorem).** Let $f: [a,b] \to \mathbb{R}$ be continuous. Then $f$ attains both a maximum and a minimum on $[a,b]$: there exist $c_{\min}, c_{\max} \in [a,b]$ such that $f(c_{\min}) \leq f(x) \leq f(c_{\max})$ for all $x \in [a,b]$.

*Proof (Maximum Existence).* Define $M = \sup\{f(x) : x \in [a,b]\}$, the least upper bound of $f([a,b])$. We must show that $M$ is finite and is actually attained, i.e., there exists $c_{\max} \in [a,b]$ with $f(c_{\max}) = M$.

First, we show $M < \infty$. Assume for contradiction that $f$ is unbounded above. Then for each $n \in \mathbb{N}$, there exists $x_n \in [a,b]$ with $f(x_n) > n$. By Bolzano-Weierstrass, the bounded sequence $(x_n)$ has a convergent subsequence $x_{n_k} \to c$ for some $c \in [a,b]$. By continuity, $f(x_{n_k}) \to f(c)$, so $(f(x_{n_k}))$ is bounded. But $f(x_{n_k}) > n_k \to \infty$, a contradiction. Therefore $M < \infty$.

Now we show $M$ is attained. By definition of supremum, for each $n \in \mathbb{N}$, there exists $x_n \in [a,b]$ with $M - 1/n < f(x_n) \leq M$. By Bolzano-Weierstrass, $(x_n)$ has a convergent subsequence $x_{n_k} \to c_{\max}$ for some $c_{\max} \in [a,b]$. By continuity, $f(x_{n_k}) \to f(c_{\max})$. But $M - 1/n_k < f(x_{n_k}) \leq M$ and $1/n_k \to 0$, so by the squeeze theorem, $f(x_{n_k}) \to M$. By uniqueness of sequence limits, $f(c_{\max}) = M$. The minimum existence follows by applying the same argument to $-f$. $\square$

The EVT fails spectacularly when either hypothesis is violated. The function $f(x) = x$ on the open interval $(0,1)$ is continuous but has no maximum (supremum is $1$, never attained). The function $f(x) = 1/x$ on $(0,1]$ is continuous but unbounded. The function $f(x) = 0$ for $x \in [0,1)$ and $f(1) = 1$ on $[0,1]$ is discontinuous and fails to attain its supremum at interior points. The EVT's hypotheses—continuity and compactness—are both essential.

Computationally, the EVT underpins optimization algorithms. Gradient descent, simulated annealing, and branch-and-bound methods all rely on the existence of global extrema on compact domains. For unconstrained optimization over $\mathbb{R}^n$, we often impose growth conditions (coercivity: $f(x) \to \infty$ as $\|x\| \to \infty$) to ensure level sets are compact, restoring the EVT's applicability.

**Theorem (Continuity of Inverse Functions).** Let $f: [a,b] \to \mathbb{R}$ be continuous and strictly monotone (either strictly increasing or strictly decreasing). Then $f$ is a bijection onto its image $[f(a), f(b)]$ (or $[f(b), f(a)]$ if decreasing), and the inverse function $f^{-1}: f([a,b]) \to [a,b]$ is continuous.

*Proof (Increasing Case).* Assume $f$ is strictly increasing. By the IVT, $f([a,b])$ contains every value between $f(a)$ and $f(b)$, hence $f([a,b]) = [f(a), f(b)]$. Injectivity follows from strict monotonicity: if $x < y$, then $f(x) < f(y)$, so $f(x) \neq f(y)$. Thus $f$ is a bijection.

To show $f^{-1}$ is continuous, let $y_0 \in (f(a), f(b))$ and set $x_0 = f^{-1}(y_0)$. Let $\varepsilon > 0$. We must find $\delta > 0$ such that $|y - y_0| < \delta$ implies $|f^{-1}(y) - f^{-1}(y_0)| < \varepsilon$. 

Choose $x_1 = \max(a, x_0 - \varepsilon)$ and $x_2 = \min(b, x_0 + \varepsilon)$. Since $f$ is strictly increasing, $f(x_1) < f(x_0) < f(x_2)$. Set $\delta = \min(f(x_0) - f(x_1), f(x_2) - f(x_0))$. Then for $|y - y_0| < \delta$, we have $f(x_1) < y < f(x_2)$. Since $f$ is a bijection onto $[f(a), f(b)]$, there exists unique $x \in [x_1, x_2]$ with $f(x) = y$, i.e., $x = f^{-1}(y)$. Therefore $|f^{-1}(y) - f^{-1}(y_0)| = |x - x_0| \leq |x_2 - x_1| = 2\varepsilon$. Adjusting $\varepsilon$ by a factor of $2$ completes the proof. The boundary cases $y_0 = f(a)$ or $y_0 = f(b)$ require minor modifications (one-sided continuity). $\square$

This theorem explains why inverse trigonometric functions ($\arcsin$, $\arctan$, etc.) are continuous: they are inverses of continuous, strictly monotone restrictions of sine and tangent. The theorem also justifies differentiation of inverse functions: if $f$ is differentiable with $f'(x_0) \neq 0$, then $f$ is locally strictly monotone near $x_0$, ensuring the local inverse is continuous and differentiable.

**Failure Mode: Discontinuities and Non-Existence of Limits.** Not all functions have limits at all points. The Dirichlet function $D(x) = \begin{cases} 1 & x \in \mathbb{Q} \\ 0 & x \in \mathbb{R} \setminus \mathbb{Q} \end{cases}$ has no limit at any point $c \in \mathbb{R}$. To see this, note that every neighborhood of $c$ contains both rationals and irrationals. Let $(x_n)$ be a sequence of rationals approaching $c$ and $(y_n)$ a sequence of irrationals approaching $c$. Then $D(x_n) = 1 \to 1$ and $D(y_n) = 0 \to 0$, violating the sequential characterization. This function is discontinuous everywhere and highlights the necessity of the epsilon-delta framework—geometric intuition completely fails.

**Failure Mode: Uniform Continuity on Unbounded Domains.** Many functions continuous on $\mathbb{R}$ fail to be uniformly continuous. We have seen $f(x) = x^2$. Another classic example is $f(x) = \sin(x^2)$. While $\sin$ itself is uniformly continuous on $\mathbb{R}$ (Lipschitz with constant $1$), the composition with $x^2$ destroys uniform continuity. As $x$ increases, $x^2$ grows quadratically, causing $\sin(x^2)$ to oscillate faster and faster, requiring progressively smaller $\delta$ values. The failure mechanism is the unbounded derivative: functions with bounded derivative on $\mathbb{R}$ are uniformly continuous (Lipschitz functions), but $(\sin(x^2))' = 2x \cos(x^2)$ is unbounded.

**Optimization: Lipschitz Continuity.** A function $f: D \to \mathbb{R}$ is Lipschitz continuous with constant $K$ if $|f(x) - f(y)| \leq K|x - y|$ for all $x, y \in D$. Lipschitz continuity implies uniform continuity (take $\delta = \varepsilon/K$) and is preserved under addition and composition. In numerical analysis, Lipschitz constants govern convergence rates of iterative methods. For instance, in the contraction mapping theorem (Banach fixed point theorem), a Lipschitz constant $K < 1$ guarantees unique fixed points and exponential convergence: $|x_n - x^*| \leq K^n |x_0 - x^*|$.

**Optimization: Modulus of Continuity.** For a continuous function $f$ on a compact interval $[a,b]$, the modulus of continuity $\omega(\delta) = \sup\{|f(x) - f(y)| : x, y \in [a,b], |x - y| \leq \delta\}$ quantifies how much $f$ can change over distance $\delta$. By Heine-Cantor, $\omega(\delta) \to 0$ as $\delta \to 0$. The modulus governs approximation quality: polynomial interpolation, finite element methods, and numerical quadrature all have error bounds proportional to $\omega(\delta)$ for appropriate $\delta$. Functions with smaller moduli (smoother functions) admit better approximations with fewer degrees of freedom.

**Failure Mode: Non-Compact Domains and the EVT.** The EVT requires compactness. On non-compact domains, continuous functions can fail to attain extrema. Consider $f(x) = e^{-x^2}$ on $\mathbb{R}$: this function is continuous, has infimum $0$ (never attained), and supremum $1$ (attained at $x = 0$). The failure to attain the infimum reflects the non-compactness of $\mathbb{R}$. In optimization, we often add constraints to restore compactness (bounded feasible regions, penalty functions, or compactification techniques) or impose coercivity conditions ($f(x) \to \infty$ as $\|x\| \to \infty$) to ensure sublevel sets are compact.

**Advanced Topic: Sequential Compactness and Completeness.** A metric space is sequentially compact if every sequence has a convergent subsequence. For subsets of $\mathbb{R}^n$, the Heine-Borel theorem characterizes compactness: a set is compact if and only if it is closed and bounded. This equivalence fails in infinite-dimensional spaces, leading to rich distinctions in functional analysis. The closed unit ball in $\ell^2$ (square-summable sequences) is closed and bounded but not compact—the standard basis vectors $e_n = (0, \ldots, 0, 1, 0, \ldots)$ form a bounded sequence with no convergent subsequence. Generalizing continuity theorems to infinite dimensions requires careful attention to topology.

**Computational Consideration: Interval Arithmetic and Verified Numerics.** The IVT and bisection method enable rigorous computation with guaranteed error bounds. Interval arithmetic represents numbers as intervals $[a,b]$ and propagates intervals through arithmetic operations, maintaining rigorous enclosures. Given $f$ continuous and computable interval extensions, bisection combined with interval evaluation can rigorously verify root existence and location. This underlies computer-assisted proofs in dynamical systems (e.g., Tucker's rigorous proof of the Lorenz attractor) and validated solutions of differential equations.

The epsilon-delta framework, while initially abstract, provides the precise language for error analysis, convergence proofs, and algorithmic correctness across all of numerical mathematics. Every finite-precision computation introduces errors; epsilon-delta reasoning quantifies these errors and establishes when approximations suffice. The limit laws translate to propagation of floating-point errors through arithmetic. Uniform continuity governs when discretization (finite differences, quadrature rules) approximates continuous objects. The IVT and EVT guarantee solutions exist before we attempt to compute them. Mastery of rigorous real analysis is not pedantry—it is the foundation for writing correct, robust, and verifiable numerical software.
