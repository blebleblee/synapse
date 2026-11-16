# Lesson 4: Differentiation — Derivatives, Mean Value Theorems, Taylor's Theorem

## 1. First-Principles Intuition & Invariants

Differentiation stands as one of the most elegant confluences of algebraic manipulation and geometric intuition in the entire edifice of mathematical analysis. Where continuity captured the notion of functions that preserve proximity—functions for which small perturbations in input yield small perturbations in output—differentiability captures the notion of functions that possess a **well-defined linear approximation** at each point in their domain. This linear approximation, encoded by the derivative, transforms the study of arbitrary nonlinear phenomena into the study of linear transformations that vary smoothly across the domain.

The core invariant underpinning differentiation is this: a function $f: \mathbb{R} \to \mathbb{R}$ is differentiable at a point $a$ if and only if the secant line slopes $\frac{f(x) - f(a)}{x - a}$ converge to a unique limiting value as $x$ approaches $a$. This limiting value, denoted $f'(a)$, represents the instantaneous rate of change of $f$ at $a$, and geometrically corresponds to the slope of the unique tangent line to the graph of $f$ at the point $(a, f(a))$. The formal definition crystallizes this intuition with analytical precision:

$$f'(a) = \lim_{h \to 0} \frac{f(a+h) - f(a)}{h}$$

provided this limit exists and is finite. The existence of this limit imposes stringent constraints on the local behavior of $f$ near $a$. The difference quotient $\frac{f(a+h) - f(a)}{h}$ measures the average rate of change of $f$ over the interval $[a, a+h]$ (or $[a+h, a]$ when $h < 0$). For this average rate to converge to a definite value as $h \to 0$, the function must not exhibit wild oscillations, jump discontinuities, or corner singularities at $a$.

The relationship between differentiability and continuity emerges immediately from the definition. If $f$ is differentiable at $a$, then we may write

$$f(a+h) - f(a) = \frac{f(a+h) - f(a)}{h} \cdot h$$

Taking limits as $h \to 0$, the right-hand side becomes $f'(a) \cdot 0 = 0$, which forces $\lim_{h \to 0} [f(a+h) - f(a)] = 0$, and therefore $\lim_{x \to a} f(x) = f(a)$. Thus differentiability implies continuity. The converse fails spectacularly, as demonstrated by the function $f(x) = |x|$ at $x = 0$: this function is continuous everywhere, yet at the origin the left-hand derivative $\lim_{h \to 0^-} \frac{|h|}{h} = -1$ differs from the right-hand derivative $\lim_{h \to 0^+} \frac{|h|}{h} = 1$, so no single tangent line exists.

The derivative, when it exists, encodes the **best linear approximation** to $f$ near $a$ in the following precise sense. Write

$$f(a+h) = f(a) + f'(a) h + r(h)$$

where the remainder term $r(h)$ satisfies $\lim_{h \to 0} \frac{r(h)}{h} = 0$. This formulation asserts that $f(a) + f'(a) h$ approximates $f(a+h)$ with an error $r(h)$ that vanishes faster than $h$ itself. We say that $r(h)$ is $o(h)$ as $h \to 0$, using Landau's little-o notation. The linear function $L(x) = f(a) + f'(a)(x - a)$ is the unique affine function that matches both the value and the slope of $f$ at $a$, and it provides the optimal linear approximation to $f$ in a neighborhood of $a$.

The derivative operator $\frac{d}{dx}$ transforms functions into functions, mapping $f$ to $f'$. This operator exhibits linearity: for any differentiable functions $f, g$ and any scalars $\alpha, \beta \in \mathbb{R}$, we have

$$\frac{d}{dx}[\alpha f(x) + \beta g(x)] = \alpha f'(x) + \beta g'(x)$$

This linearity emerges directly from the limit laws governing sums and scalar multiples. The product rule and quotient rule, by contrast, introduce nonlinear interactions:

$$\frac{d}{dx}[f(x) g(x)] = f'(x) g(x) + f(x) g'(x)$$

$$\frac{d}{dx}\left[\frac{f(x)}{g(x)}\right] = \frac{f'(x) g(x) - f(x) g'(x)}{[g(x)]^2}$$

To derive the product rule rigorously, we write

$$\frac{f(a+h)g(a+h) - f(a)g(a)}{h} = \frac{f(a+h)g(a+h) - f(a)g(a+h) + f(a)g(a+h) - f(a)g(a)}{h}$$

$$= g(a+h) \cdot \frac{f(a+h) - f(a)}{h} + f(a) \cdot \frac{g(a+h) - g(a)}{h}$$

Taking limits as $h \to 0$, the first term converges to $g(a) f'(a)$ (using the continuity of $g$ at $a$, which follows from differentiability), and the second term converges to $f(a) g'(a)$. The quotient rule follows from the product rule and the chain rule applied to $g(x)^{-1}$.

The chain rule governs the composition of differentiable functions. If $g$ is differentiable at $a$ and $f$ is differentiable at $g(a)$, then the composition $f \circ g$ is differentiable at $a$, with derivative

$$(f \circ g)'(a) = f'(g(a)) \cdot g'(a)$$

The proof requires careful handling of the case where $g(a+h) = g(a)$ for $h$ in a punctured neighborhood of zero. Define $\phi(k) = \frac{f(g(a) + k) - f(g(a))}{k}$ for $k \neq 0$ and $\phi(0) = f'(g(a))$. Then $\phi$ is continuous at $k = 0$ by the differentiability of $f$ at $g(a)$. Write $k = g(a+h) - g(a)$. Then

$$\frac{(f \circ g)(a+h) - (f \circ g)(a)}{h} = \frac{f(g(a+h)) - f(g(a))}{h} = \phi(k) \cdot \frac{g(a+h) - g(a)}{h}$$

As $h \to 0$, we have $k \to 0$ (by continuity of $g$ at $a$), so $\phi(k) \to f'(g(a))$ and $\frac{g(a+h) - g(a)}{h} \to g'(a)$, yielding the chain rule.

The inverse function theorem provides conditions under which a differentiable bijection possesses a differentiable inverse. If $f$ is continuous and strictly monotone on an interval $I$, and if $f$ is differentiable at $a \in I$ with $f'(a) \neq 0$, then the inverse function $f^{-1}$ is differentiable at $b = f(a)$, with derivative

$$(f^{-1})'(b) = \frac{1}{f'(a)} = \frac{1}{f'(f^{-1}(b))}$$

This result follows from the limit

$$(f^{-1})'(b) = \lim_{k \to 0} \frac{f^{-1}(b+k) - f^{-1}(b)}{k}$$

Setting $h = f^{-1}(b+k) - f^{-1}(b)$, we have $b + k = f(f^{-1}(b) + h) = f(a+h)$, so $k = f(a+h) - f(a)$. As $k \to 0$, continuity of $f^{-1}$ forces $h \to 0$. Thus

$$(f^{-1})'(b) = \lim_{h \to 0} \frac{h}{f(a+h) - f(a)} = \frac{1}{\lim_{h \to 0} \frac{f(a+h) - f(a)}{h}} = \frac{1}{f'(a)}$$

provided $f'(a) \neq 0$, ensuring the denominator limit exists and is nonzero.

## 2. Core Architecture & Mechanics

The mean value theorem and its precursors—Rolle's theorem and the extreme value theorem—form the structural backbone of differential calculus. These theorems exploit the global topological properties of continuous functions on closed bounded intervals to deduce the existence of points with specific local derivative properties. The logical dependency flows as follows: the extreme value theorem (from Lesson 2) guarantees that a continuous function on a compact interval attains its maximum and minimum; Fermat's theorem on local extrema links these extremal points to critical points where the derivative vanishes; Rolle's theorem applies Fermat's theorem to functions that take equal values at the endpoints; and the mean value theorem generalizes Rolle's theorem to arbitrary continuous functions that are differentiable on the interior.

**Fermat's Theorem on Local Extrema.** If $f: I \to \mathbb{R}$ is differentiable at an interior point $a$ of $I$, and if $f$ attains a local maximum or local minimum at $a$, then $f'(a) = 0$.

*Proof.* Suppose $f$ attains a local maximum at $a$. Then there exists $\delta > 0$ such that $f(x) \leq f(a)$ for all $x \in (a - \delta, a + \delta)$. For $h \in (0, \delta)$, we have $f(a+h) \leq f(a)$, so

$$\frac{f(a+h) - f(a)}{h} \leq 0$$

Taking the limit as $h \to 0^+$, we obtain $f'(a) \leq 0$. For $h \in (-\delta, 0)$, we have $f(a+h) \leq f(a)$, so

$$\frac{f(a+h) - f(a)}{h} \geq 0$$

(note the inequality reverses because we divide by negative $h$). Taking the limit as $h \to 0^-$, we obtain $f'(a) \geq 0$. Combining these inequalities yields $f'(a) = 0$. The proof for a local minimum is identical. $\square$

Fermat's theorem asserts that interior extremal points of differentiable functions must be critical points. The converse fails: not every critical point is an extremum, as demonstrated by $f(x) = x^3$ at $x = 0$, where $f'(0) = 0$ yet $f$ has neither a local maximum nor a local minimum at the origin.

**Rolle's Theorem.** Let $f: [a, b] \to \mathbb{R}$ be continuous on $[a, b]$ and differentiable on $(a, b)$. If $f(a) = f(b)$, then there exists at least one point $c \in (a, b)$ such that $f'(c) = 0$.

*Proof.* By the extreme value theorem, $f$ attains its maximum $M$ and minimum $m$ on $[a, b]$. If $M = m$, then $f$ is constant on $[a, b]$, so $f'(c) = 0$ for every $c \in (a, b)$. If $M > m$, then at least one of $M$ or $m$ differs from the common endpoint value $f(a) = f(b)$. Without loss of generality, suppose $M > f(a)$. Then the maximum $M$ is attained at some point $c \in (a, b)$ (since $f(a) = f(b) < M$, the maximum cannot occur at the endpoints). By Fermat's theorem, $f'(c) = 0$. $\square$

Rolle's theorem possesses a natural geometric interpretation: if a differentiable curve starts and ends at the same height, then at some interior point the tangent line must be horizontal. This theorem serves as the engine for the mean value theorem, which removes the restriction that the endpoint values coincide.

**Mean Value Theorem (MVT).** Let $f: [a, b] \to \mathbb{R}$ be continuous on $[a, b]$ and differentiable on $(a, b)$. Then there exists at least one point $c \in (a, b)$ such that

$$f'(c) = \frac{f(b) - f(a)}{b - a}$$

*Proof.* Define the auxiliary function

$$g(x) = f(x) - f(a) - \frac{f(b) - f(a)}{b - a} (x - a)$$

This function $g$ represents the vertical displacement between $f(x)$ and the secant line connecting $(a, f(a))$ to $(b, f(b))$. Observe that $g(a) = f(a) - f(a) - 0 = 0$ and

$$g(b) = f(b) - f(a) - \frac{f(b) - f(a)}{b - a} (b - a) = f(b) - f(a) - (f(b) - f(a)) = 0$$

Thus $g$ satisfies the hypotheses of Rolle's theorem: it is continuous on $[a, b]$, differentiable on $(a, b)$, and $g(a) = g(b)$. By Rolle's theorem, there exists $c \in (a, b)$ such that $g'(c) = 0$. Computing the derivative,

$$g'(x) = f'(x) - \frac{f(b) - f(a)}{b - a}$$

Setting $g'(c) = 0$ yields

$$f'(c) = \frac{f(b) - f(a)}{b - a}$$

as required. $\square$

The mean value theorem asserts that for any differentiable function on an interval, there exists at least one interior point where the instantaneous rate of change (the derivative) equals the average rate of change over the entire interval. This theorem bridges local derivative information with global function behavior, and it underpins nearly every major result in differential calculus.

**Consequences of the Mean Value Theorem.** The MVT enables us to deduce global properties of a function from local derivative information. We establish several fundamental corollaries.

*Corollary 1 (Constant Function Characterization).* If $f$ is differentiable on an interval $I$ and $f'(x) = 0$ for all $x \in I$, then $f$ is constant on $I$.

*Proof.* Fix any two points $a, b \in I$ with $a < b$. Applying the MVT to $f$ on $[a, b]$, there exists $c \in (a, b)$ such that

$$f(b) - f(a) = f'(c)(b - a) = 0 \cdot (b - a) = 0$$

Thus $f(b) = f(a)$. Since $a$ and $b$ were arbitrary, $f$ is constant on $I$. $\square$

*Corollary 2 (Monotonicity Criterion).* Let $f$ be differentiable on an interval $I$. Then:
- If $f'(x) > 0$ for all $x \in I$, then $f$ is strictly increasing on $I$.
- If $f'(x) \geq 0$ for all $x \in I$, then $f$ is increasing (non-decreasing) on $I$.
- If $f'(x) < 0$ for all $x \in I$, then $f$ is strictly decreasing on $I$.
- If $f'(x) \leq 0$ for all $x \in I$, then $f$ is decreasing (non-increasing) on $I$.

*Proof.* Suppose $f'(x) > 0$ for all $x \in I$. Fix $a, b \in I$ with $a < b$. By the MVT, there exists $c \in (a, b)$ such that

$$f(b) - f(a) = f'(c)(b - a)$$

Since $f'(c) > 0$ and $b - a > 0$, we have $f(b) - f(a) > 0$, so $f(b) > f(a)$. Thus $f$ is strictly increasing. The other cases follow analogously. $\square$

*Corollary 3 (Lipschitz Continuity from Bounded Derivative).* If $f$ is differentiable on an interval $I$ and $|f'(x)| \leq M$ for all $x \in I$, then $f$ is Lipschitz continuous on $I$ with Lipschitz constant $M$:

$$|f(x) - f(y)| \leq M |x - y| \quad \text{for all } x, y \in I$$

*Proof.* For any $x, y \in I$ with $x < y$, the MVT yields $c \in (x, y)$ such that

$$f(y) - f(x) = f'(c)(y - x)$$

Taking absolute values,

$$|f(y) - f(x)| = |f'(c)| \, |y - x| \leq M |y - x|$$

This inequality holds for all $x, y \in I$ (if $y < x$, interchange the roles). $\square$

These corollaries demonstrate how the MVT converts local derivative bounds and sign conditions into global quantitative estimates and qualitative monotonicity properties. This conversion mechanism is essential for optimization, fixed-point theorems, and the qualitative theory of ordinary differential equations.

**Cauchy's Mean Value Theorem.** The classical MVT generalizes to a two-function version that proves essential in the rigorous derivation of L'Hôpital's rule. Let $f, g: [a, b] \to \mathbb{R}$ be continuous on $[a, b]$ and differentiable on $(a, b)$. Then there exists $c \in (a, b)$ such that

$$[f(b) - f(a)] g'(c) = [g(b) - g(a)] f'(c)$$

If $g'(c) \neq 0$ and $g(b) \neq g(a)$, this can be rewritten as

$$\frac{f'(c)}{g'(c)} = \frac{f(b) - f(a)}{g(b) - g(a)}$$

*Proof.* Define the auxiliary function

$$h(x) = [f(b) - f(a)] g(x) - [g(b) - g(a)] f(x)$$

Then $h$ is continuous on $[a, b]$ and differentiable on $(a, b)$. Computing the endpoint values,

$$h(a) = [f(b) - f(a)] g(a) - [g(b) - g(a)] f(a) = f(b) g(a) - g(b) f(a)$$

$$h(b) = [f(b) - f(a)] g(b) - [g(b) - g(a)] f(b) = f(b) g(b) - f(a) g(b) - g(b) f(b) + g(a) f(b) = f(b) g(a) - g(b) f(a)$$

Thus $h(a) = h(b)$. By Rolle's theorem, there exists $c \in (a, b)$ such that $h'(c) = 0$. Computing the derivative,

$$h'(x) = [f(b) - f(a)] g'(x) - [g(b) - g(a)] f'(x)$$

Setting $h'(c) = 0$ yields the desired relation. $\square$

**L'Hôpital's Rule.** The Cauchy MVT provides the foundation for resolving indeterminate forms of type $\frac{0}{0}$ and $\frac{\infty}{\infty}$. We state and prove the $\frac{0}{0}$ case rigorously.

*Theorem (L'Hôpital's Rule, $\frac{0}{0}$ form).* Let $f, g: (a, b) \to \mathbb{R}$ be differentiable with $g'(x) \neq 0$ for all $x \in (a, b)$. Suppose $\lim_{x \to a^+} f(x) = \lim_{x \to a^+} g(x) = 0$ and $\lim_{x \to a^+} \frac{f'(x)}{g'(x)} = L$ (where $L$ may be finite or infinite). Then $\lim_{x \to a^+} \frac{f(x)}{g(x)} = L$.

*Proof.* Extend $f$ and $g$ to $[a, b)$ by defining $f(a) = g(a) = 0$. Then $f$ and $g$ are continuous on $[a, b)$ and differentiable on $(a, b)$. Fix any $x \in (a, b)$. By Cauchy's MVT applied to $f$ and $g$ on $[a, x]$, there exists $c_x \in (a, x)$ such that

$$\frac{f(x) - f(a)}{g(x) - g(a)} = \frac{f'(c_x)}{g'(c_x)}$$

Since $f(a) = g(a) = 0$, this simplifies to

$$\frac{f(x)}{g(x)} = \frac{f'(c_x)}{g'(c_x)}$$

Note that $g(x) \neq 0$ for $x \in (a, b)$ sufficiently close to $a$, because otherwise $g$ would have two zeros $a$ and $x$ in $[a, x]$, and Rolle's theorem would yield a point where $g' = 0$, contradicting the hypothesis. As $x \to a^+$, we have $c_x \to a^+$ (since $c_x \in (a, x)$). By hypothesis, $\lim_{c \to a^+} \frac{f'(c)}{g'(c)} = L$. Therefore,

$$\lim_{x \to a^+} \frac{f(x)}{g(x)} = \lim_{x \to a^+} \frac{f'(c_x)}{g'(c_x)} = L$$

completing the proof. $\square$

The $\frac{\infty}{\infty}$ case requires additional technical care, typically handled by reciprocal substitutions or by demonstrating that the $\frac{\infty}{\infty}$ form can be reduced to a $\frac{0}{0}$ form. L'Hôpital's rule is a workhorse tool in asymptotic analysis, providing systematic resolution of indeterminate limits that arise in the study of power series, integral asymptotics, and algorithm complexity analysis.

**Taylor's Theorem: Polynomial Approximation and Remainder Forms.** The derivative provides the optimal linear approximation to a function near a point. Taylor's theorem extends this idea to polynomial approximations of arbitrary degree, quantifying the approximation error through various remainder formulas. If $f$ is sufficiently differentiable near a point $a$, we can approximate $f(x)$ by the Taylor polynomial

$$P_n(x) = f(a) + f'(a)(x-a) + \frac{f''(a)}{2!}(x-a)^2 + \cdots + \frac{f^{(n)}(a)}{n!}(x-a)^n = \sum_{k=0}^n \frac{f^{(k)}(a)}{k!}(x-a)^k$$

The remainder $R_n(x) = f(x) - P_n(x)$ measures the approximation error. Taylor's theorem provides explicit formulas for this remainder, enabling precise quantitative control over approximation quality.

*Theorem (Taylor's Theorem with Lagrange Remainder).* Let $f: [a, b] \to \mathbb{R}$ be $(n+1)$ times continuously differentiable on $[a, b]$. Then for any $x \in [a, b]$, there exists $c$ strictly between $a$ and $x$ such that

$$f(x) = \sum_{k=0}^n \frac{f^{(k)}(a)}{k!}(x-a)^k + \frac{f^{(n+1)}(c)}{(n+1)!}(x-a)^{n+1}$$

The term $R_n(x) = \frac{f^{(n+1)}(c)}{(n+1)!}(x-a)^{n+1}$ is called the Lagrange form of the remainder.

*Proof.* Fix $x \in [a, b]$ with $x \neq a$. Define the constant $M$ by

$$f(x) = \sum_{k=0}^n \frac{f^{(k)}(a)}{k!}(x-a)^k + M(x-a)^{n+1}$$

Our goal is to show that $M = \frac{f^{(n+1)}(c)}{(n+1)!}$ for some $c$ between $a$ and $x$. Define the auxiliary function

$$\phi(t) = f(x) - \sum_{k=0}^n \frac{f^{(k)}(t)}{k!}(x-t)^k - M(x-t)^{n+1}$$

for $t \in [a, x]$. Observe that $\phi(x) = f(x) - f(x) - 0 = 0$ and, by the definition of $M$, $\phi(a) = 0$. Since $\phi$ is continuous on $[a, x]$ and differentiable on $(a, x)$, Rolle's theorem guarantees the existence of $c_1 \in (a, x)$ such that $\phi'(c_1) = 0$.

We compute $\phi'(t)$. Using the product rule and chain rule,

$$\phi'(t) = 0 - \sum_{k=0}^n \frac{d}{dt}\left[\frac{f^{(k)}(t)}{k!}(x-t)^k\right] - M \frac{d}{dt}(x-t)^{n+1}$$

$$= -\sum_{k=0}^n \left[\frac{f^{(k+1)}(t)}{k!}(x-t)^k + \frac{f^{(k)}(t)}{k!} \cdot k(x-t)^{k-1} \cdot (-1)\right] + M(n+1)(x-t)^n$$

$$= -\sum_{k=0}^n \frac{f^{(k+1)}(t)}{k!}(x-t)^k + \sum_{k=0}^n \frac{f^{(k)}(t)}{(k-1)!}(x-t)^{k-1} + M(n+1)(x-t)^n$$

Reindexing the second sum by replacing $k$ with $k+1$,

$$\phi'(t) = -\sum_{k=0}^n \frac{f^{(k+1)}(t)}{k!}(x-t)^k + \sum_{k=0}^{n-1} \frac{f^{(k+1)}(t)}{k!}(x-t)^k + M(n+1)(x-t)^n$$

Most terms cancel, leaving

$$\phi'(t) = -\frac{f^{(n+1)}(t)}{n!}(x-t)^n + M(n+1)(x-t)^n = (x-t)^n \left[M(n+1) - \frac{f^{(n+1)}(t)}{n!}\right]$$

Setting $\phi'(c_1) = 0$, we have

$$(x-c_1)^n \left[M(n+1) - \frac{f^{(n+1)}(c_1)}{n!}\right] = 0$$

Since $c_1 \in (a, x)$, we have $x - c_1 \neq 0$. Therefore,

$$M(n+1) - \frac{f^{(n+1)}(c_1)}{n!} = 0 \implies M = \frac{f^{(n+1)}(c_1)}{(n+1)!}$$

Substituting back, we obtain

$$f(x) = \sum_{k=0}^n \frac{f^{(k)}(a)}{k!}(x-a)^k + \frac{f^{(n+1)}(c_1)}{(n+1)!}(x-a)^{n+1}$$

as required. $\square$

The Lagrange remainder provides a pointwise error estimate: if we can bound $|f^{(n+1)}(c)|$ on the interval between $a$ and $x$, we obtain a uniform bound on the approximation error. For instance, to approximate $e^x$ near $x = 0$ using the degree $n$ Taylor polynomial, we note that $f^{(k)}(x) = e^x$ for all $k$, so

$$e^x = \sum_{k=0}^n \frac{x^k}{k!} + \frac{e^c}{(n+1)!} x^{n+1}$$

for some $c$ between $0$ and $x$. If $|x| \leq 1$, then $|e^c| \leq e$, so

$$\left|e^x - \sum_{k=0}^n \frac{x^k}{k!}\right| \leq \frac{e}{(n+1)!}$$

This bound decays factorially in $n$, demonstrating the exponential function's exceptional approximability by polynomials.

*Theorem (Taylor's Theorem with Cauchy Remainder).* Under the same hypotheses, there exists $c$ strictly between $a$ and $x$ such that

$$R_n(x) = \frac{f^{(n+1)}(c)}{n!}(x-c)^n(x-a)$$

*Proof Sketch.* Apply Cauchy's mean value theorem iteratively, using auxiliary functions constructed from the Taylor polynomial and a power function. The details are technical but follow the same strategy as the Lagrange proof. $\square$

The Cauchy remainder is sometimes more convenient for asymptotic analysis, as it isolates the factor $(x-a)$ explicitly.

*Theorem (Taylor's Theorem with Integral Remainder).* If $f$ is $(n+1)$ times continuously differentiable, then

$$R_n(x) = \int_a^x \frac{f^{(n+1)}(t)}{n!}(x-t)^n \, dt$$

*Proof.* We proceed by induction on $n$. For $n = 0$, the fundamental theorem of calculus yields

$$f(x) - f(a) = \int_a^x f'(t) \, dt$$

which is the $n = 0$ case. Assume the result holds for $n$. Integrating by parts with $u = f^{(n+1)}(t)$ and $dv = (x-t)^n \, dt$, we have $du = f^{(n+2)}(t) \, dt$ and $v = -\frac{(x-t)^{n+1}}{n+1}$. Thus

$$\int_a^x \frac{f^{(n+1)}(t)}{n!}(x-t)^n \, dt = \frac{1}{n!} \left[-\frac{f^{(n+1)}(t)(x-t)^{n+1}}{n+1}\Big|_a^x + \int_a^x \frac{f^{(n+2)}(t)(x-t)^{n+1}}{n+1} \, dt\right]$$

$$= \frac{f^{(n+1)}(a)(x-a)^{n+1}}{(n+1)!} + \int_a^x \frac{f^{(n+2)}(t)}{(n+1)!}(x-t)^{n+1} \, dt$$

This expresses the $n$-th order remainder in terms of the $(n+1)$-th order Taylor term plus the $(n+1)$-th order integral remainder, confirming the induction step. $\square$

The integral remainder form is particularly useful in probabilistic and statistical contexts, where integration against density functions arises naturally. It also provides a direct route to proving the mean value theorem (the $n = 0$ case) and Cauchy's mean value theorem.

## 3. High-Performance Optimization & Failure Modes

The practical deployment of differentiation techniques in rigorous analysis demands careful attention to edge cases, failure modes, and optimization strategies. Many common errors in applied calculus stem from neglecting hypotheses, misapplying theorems to inappropriate function classes, or failing to verify differentiability at critical points.

**Edge Case: Differentiability at Endpoints.** The mean value theorem and Taylor's theorem require differentiability on the open interval $(a, b)$, with continuity extending to the closed interval $[a, b]$. Endpoint derivatives are not required. This distinction is essential: the function $f(x) = \sqrt{x}$ on $[0, 1]$ satisfies the MVT hypotheses despite having an infinite right-hand derivative at $x = 0$. The MVT guarantees the existence of $c \in (0, 1)$ with $f'(c) = \frac{\sqrt{1} - \sqrt{0}}{1 - 0} = 1$, and indeed $f'(x) = \frac{1}{2\sqrt{x}}$, so $c = \frac{1}{4}$ satisfies $f'(c) = 1$.

Failure to distinguish between one-sided and two-sided derivatives at endpoints leads to spurious contradictions. When applying the MVT, always verify that the function is differentiable on the interior, and that the derivative is bounded or well-behaved where needed.

**Edge Case: Critical Points and the First Derivative Test.** Fermat's theorem identifies critical points as candidates for local extrema, but not every critical point is an extremum. The first derivative test resolves this ambiguity by examining the sign of $f'$ on either side of the critical point $c$:
- If $f'(x) > 0$ for $x < c$ (near $c$) and $f'(x) < 0$ for $x > c$ (near $c$), then $f$ has a local maximum at $c$.
- If $f'(x) < 0$ for $x < c$ (near $c$) and $f'(x) > 0$ for $x > c$ (near $c$), then $f$ has a local minimum at $c$.
- If $f'(x)$ does not change sign at $c$, then $f$ has neither a local maximum nor a local minimum at $c$.

The second derivative test provides an alternative when $f''(c)$ exists and is nonzero: if $f'(c) = 0$ and $f''(c) > 0$, then $f$ has a local minimum at $c$; if $f'(c) = 0$ and $f''(c) < 0$, then $f$ has a local maximum at $c$. If $f''(c) = 0$, the test is inconclusive, and higher-order derivatives or the first derivative test must be employed.

**Optimization Workflow: Bounded Closed Interval Optimization.** To find the global maximum and minimum of a continuous function $f$ on $[a, b]$, execute the following protocol:

1. Identify all critical points $c \in (a, b)$ where $f'(c) = 0$ or $f'(c)$ does not exist.
2. Evaluate $f$ at each critical point: $f(c_1), f(c_2), \ldots, f(c_k)$.
3. Evaluate $f$ at the endpoints: $f(a)$ and $f(b)$.
4. The global maximum is $\max\{f(a), f(b), f(c_1), \ldots, f(c_k)\}$, and the global minimum is $\min\{f(a), f(b), f(c_1), \ldots, f(c_k)\}$.

This protocol is exhaustive: the extreme value theorem guarantees that the global maximum and minimum are attained, and they must occur either at a critical point or at an endpoint. Failure to check endpoints is a common error that leads to incorrect optimization results.

**Failure Mode: Misapplication of L'Hôpital's Rule.** L'Hôpital's rule applies only to indeterminate forms $\frac{0}{0}$ or $\frac{\infty}{\infty}$. Applying it to determinate forms yields nonsense. For instance,

$$\lim_{x \to 0} \frac{\sin x}{x^2}$$

is of the form $\frac{0}{0}$, so L'Hôpital's rule yields

$$\lim_{x \to 0} \frac{\cos x}{2x}$$

which is of the form $\frac{1}{0}$, indicating the original limit diverges to $\pm \infty$. Indeed, $\lim_{x \to 0^+} \frac{\sin x}{x^2} = +\infty$. However, applying L'Hôpital's rule again (incorrectly, since $\frac{1}{0}$ is not indeterminate) would give

$$\lim_{x \to 0} \frac{-\sin x}{2}$$

which is $0$, contradicting the correct answer. Always verify the indeterminate form before each application of L'Hôpital's rule.

Another common error is circular reasoning. Using L'Hôpital's rule to prove $\lim_{x \to 0} \frac{\sin x}{x} = 1$ requires knowing that the derivative of $\sin x$ is $\cos x$, which in turn requires knowing $\lim_{x \to 0} \frac{\sin x}{x} = 1$ (this limit is used in the first-principles proof of $\frac{d}{dx}\sin x = \cos x$). Such circular arguments are invalid. The limit $\lim_{x \to 0} \frac{\sin x}{x} = 1$ must be established independently, typically via geometric arguments involving arc length and chord length inequalities.

**Optimization Strategy: Taylor Series Computation and Caching.** Computing high-order Taylor polynomials requires repeated differentiation, which can be computationally expensive for complicated functions. For functions arising from compositions, products, and quotients, symbolic differentiation via the chain rule, product rule, and quotient rule generates increasingly complex expressions. Two strategies mitigate this cost:

1. **Automatic Differentiation (Forward Mode).** Represent the function as a computation graph, and propagate derivative information forward through the graph using the chain rule. Each elementary operation (addition, multiplication, exponentiation, trigonometric functions) has a known derivative rule, enabling automatic construction of the derivative function without symbolic manipulation.

2. **Caching Derivative Values.** When evaluating Taylor polynomials at many points near a fixed center $a$, compute and cache the values $f(a), f'(a), f''(a), \ldots, f^{(n)}(a)$ once, then evaluate the polynomial via Horner's method or direct summation. This avoids redundant differentiation.

For numerical evaluation of Taylor series in floating-point arithmetic, the Lagrange remainder provides error bounds that guide the choice of truncation degree $n$. To achieve absolute error $\epsilon$, select $n$ such that

$$\frac{M}{(n+1)!} |x-a|^{n+1} \leq \epsilon$$

where $M$ is a bound on $|f^{(n+1)}|$ on the interval between $a$ and $x$. This strategy is foundational in numerical analysis libraries that compute transcendental functions via Taylor series with provable error bounds.

**Edge Case: Rolle's Theorem with Multiplicities.** If $f$ has multiple roots in $[a, b]$, Rolle's theorem can be applied iteratively. Specifically, if $f$ has $k$ distinct roots in $[a, b]$, then $f'$ has at least $k-1$ roots in $(a, b)$. This principle extends to higher derivatives: if $f$ has a root of multiplicity $m$ at $x = a$, then $f(a) = f'(a) = \cdots = f^{(m-1)}(a) = 0$ and $f^{(m)}(a) \neq 0$. This characterization is essential in root-finding algorithms and in the study of polynomial factorization.

**Boundary Cases in Taylor Expansions.** The Taylor series $\sum_{k=0}^\infty \frac{f^{(k)}(a)}{k!}(x-a)^k$ converges to $f(x)$ only within the radius of convergence $R$, determined by the growth rate of $f^{(k)}(a)$ as $k \to \infty$. For analytic functions (functions equal to their Taylor series), $R > 0$, and the series provides a global representation of $f$ within the disk $|x - a| < R$. For non-analytic smooth functions, the Taylor series may converge to a different function or diverge entirely. The canonical example is

$$f(x) = \begin{cases} e^{-1/x^2} & x \neq 0 \\ 0 & x = 0 \end{cases}$$

This function is infinitely differentiable at $x = 0$, with $f^{(k)}(0) = 0$ for all $k$, so the Taylor series centered at $0$ is identically zero, yet $f(x) \neq 0$ for $x \neq 0$. This example demonstrates that infinite differentiability does not guarantee analyticity.

**Practical Heuristic: Verifying MVT Applicability.** Before invoking the mean value theorem, always verify:
1. Continuity on the closed interval $[a, b]$.
2. Differentiability on the open interval $(a, b)$.
3. That the derivative does not exhibit pathological behavior (e.g., unbounded oscillation) that might invalidate the conclusion.

For piecewise-defined functions, check continuity and differentiability at the junction points explicitly. A function may be continuous at a junction yet fail to be differentiable there, violating the MVT hypotheses.

**Resource Scaling: Derivative Computation Complexity.** Computing the $n$-th derivative of a function via symbolic differentiation scales poorly with $n$ for complicated functions. For elementary functions (polynomials, rational functions, exponentials, logarithms, trigonometric functions), the $n$-th derivative can often be computed in closed form using induction. For compositions and products, the complexity grows combinatorially. The Faà di Bruno formula expresses the $n$-th derivative of a composition $f \circ g$ in terms of the derivatives of $f$ and $g$:

$$\frac{d^n}{dx^n}[f(g(x))] = \sum \frac{n!}{m_1! \, m_2! \cdots m_n!} f^{(m_1 + m_2 + \cdots + m_n)}(g(x)) \prod_{j=1}^n \left(\frac{g^{(j)}(x)}{j!}\right)^{m_j}$$

where the sum ranges over all nonnegative integer solutions to $\sum_{j=1}^n j m_j = n$. This formula is computationally expensive for large $n$, and in practice, numerical differentiation via finite differences or automatic differentiation is often more efficient.

The mean value theorem, Taylor's theorem, and their corollaries constitute the core machinery for translating local derivative information into global function properties, for constructing polynomial approximations with quantified error, and for resolving indeterminate limits. Mastery of these theorems, their proofs, and their edge cases is indispensable for rigorous analysis, optimization theory, numerical analysis, and the qualitative study of dynamical systems. Every application of these theorems demands careful verification of hypotheses and awareness of the boundary conditions under which the conclusions hold.
