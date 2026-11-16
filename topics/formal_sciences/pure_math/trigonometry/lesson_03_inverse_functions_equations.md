# Lesson 3: Inverse Trigonometric Functions and Equation Solving

## 1. First-Principles Intuition & Invariants

The story of inverse trigonometric functions begins with an inconvenient truth about the circular functions themselves: they are periodic, and periodicity is the enemy of invertibility. A function admits an inverse precisely when it is bijective — when every element of its codomain is the image of exactly one element of its domain. The sine function, mapping $\mathbb{R} \to [-1, 1]$, violates this condition emphatically. The equation $\sin\theta = \frac{1}{2}$ is satisfied by $\theta = \frac{\pi}{6}$, yes, but also by $\theta = \frac{5\pi}{6}$, and by $\frac{\pi}{6} + 2\pi k$ and $\frac{5\pi}{6} + 2\pi k$ for every integer $k \in \mathbb{Z}$. No inverse can be defined on a domain that collapses infinitely many inputs to the same output.

The resolution is a surgical restriction of domain — not an approximation or a convenience, but a principled choice that preserves the full range of the function while restoring injectivity. The mathematician's task is to identify a *maximal connected interval* on which the function is strictly monotone. Strict monotonicity guarantees injectivity, the connected interval guarantees the full range $[-1,1]$ is achieved, and the choice of *maximal* ensures we are not discarding information unnecessarily. For $\sin$, the canonical choice is the interval $\left[-\frac{\pi}{2}, \frac{\pi}{2}\right]$. On this interval, $\sin$ is strictly increasing from $-1$ to $1$. On any strictly larger connected interval, strict monotonicity would be violated — the sine function turns around at $\frac{\pi}{2}$, so extending even slightly to the right reintroduces non-injectivity.

This is not the only valid choice. The interval $\left[\frac{\pi}{2}, \frac{3\pi}{2}\right]$, on which sine is strictly decreasing, would work equally well analytically, but the convention $\left[-\frac{\pi}{2}, \frac{\pi}{2}\right]$ is universal, chosen partly for elegance (it is symmetric about zero) and partly because it makes $\arcsin$ an odd function, a symmetry property with downstream algebraic utility.

For cosine, the situation is parallel but the canonical restricted domain is $[0, \pi]$, on which $\cos$ is strictly decreasing from $1$ to $-1$. The interval $[-\pi, 0]$ would also work, but $[0, \pi]$ is preferred because it makes $\arccos$ a function with a clean, positive range. For tangent, the natural restriction is the open interval $\left(-\frac{\pi}{2}, \frac{\pi}{2}\right)$, the unique maximal open interval centered at the origin on which $\tan$ is strictly increasing and continuous. The endpoints are excluded because $\tan$ has vertical asymptotes there; the range on this open interval is all of $\mathbb{R}$, making $\arctan : \mathbb{R} \to \left(-\frac{\pi}{2}, \frac{\pi}{2}\right)$ a bijection between the entire real line and a bounded open interval.

**Definition (Arcsine).** The function $\arcsin : [-1, 1] \to \left[-\frac{\pi}{2}, \frac{\pi}{2}\right]$ is defined as the inverse of $\sin\big|_{\left[-\frac{\pi}{2}, \frac{\pi}{2}\right]}$. That is, for $y \in [-1,1]$,

$$\arcsin(y) = x \iff \sin(x) = y \text{ and } x \in \left[-\frac{\pi}{2}, \frac{\pi}{2}\right].$$

**Definition (Arccosine).** The function $\arccos : [-1, 1] \to [0, \pi]$ is defined as the inverse of $\cos\big|_{[0,\pi]}$. For $y \in [-1,1]$,

$$\arccos(y) = x \iff \cos(x) = y \text{ and } x \in [0, \pi].$$

**Definition (Arctangent).** The function $\arctan : \mathbb{R} \to \left(-\frac{\pi}{2}, \frac{\pi}{2}\right)$ is defined as the inverse of $\tan\big|_{\left(-\frac{\pi}{2}, \frac{\pi}{2}\right)}$. For $y \in \mathbb{R}$,

$$\arctan(y) = x \iff \tan(x) = y \text{ and } x \in \left(-\frac{\pi}{2}, \frac{\pi}{2}\right).$$

These definitions carry immediate and important corollaries. Because $\sin$ is an odd function, its restriction to $\left[-\frac{\pi}{2}, \frac{\pi}{2}\right]$ is also odd, and the inverse of an odd bijection is odd. Therefore $\arcsin$ is an odd function: $\arcsin(-x) = -\arcsin(x)$ for all $x \in [-1,1]$. Similarly, $\arctan$ is odd. Arccosine, by contrast, is not odd — the restricted domain $[0,\pi]$ is not symmetric about zero. Instead, $\arccos$ satisfies the identity $\arccos(-x) = \pi - \arccos(x)$, which follows immediately from the symmetry $\cos(\pi - \theta) = -\cos\theta$.

A core invariant governs all three inverse functions and must be internalized before any equation-solving work: the composition identities are *not* uniformly bidirectional. The full inverse relationship $f^{-1}(f(x)) = x$ holds only within the restricted domain.

For $\arcsin$:

$$\sin(\arcsin(x)) = x \quad \text{for all } x \in [-1, 1]$$

$$\arcsin(\sin(\theta)) = \theta \quad \text{if and only if } \theta \in \left[-\frac{\pi}{2}, \frac{\pi}{2}\right]$$

For $\arccos$:

$$\cos(\arccos(x)) = x \quad \text{for all } x \in [-1, 1]$$

$$\arccos(\cos(\theta)) = \theta \quad \text{if and only if } \theta \in [0, \pi]$$

For $\arctan$:

$$\tan(\arctan(x)) = x \quad \text{for all } x \in \mathbb{R}$$

$$\arctan(\tan(\theta)) = \theta \quad \text{if and only if } \theta \in \left(-\frac{\pi}{2}, \frac{\pi}{2}\right)$$

The asymmetry matters enormously in practice. A practitioner who writes $\arcsin(\sin(5\pi/6)) = 5\pi/6$ has committed an error because $5\pi/6 \notin \left[-\frac{\pi}{2}, \frac{\pi}{2}\right]$. The correct computation recognizes that $\sin(5\pi/6) = \sin(\pi/6) = 1/2$, and $\arcsin(1/2) = \pi/6$. The function $\theta \mapsto \arcsin(\sin(\theta))$ is not the identity on $\mathbb{R}$; it is a sawtooth function that folds the real line back into $\left[-\frac{\pi}{2}, \frac{\pi}{2}\right]$ with period $2\pi$.

There is a beautiful and practically useful family of identities connecting $\arcsin$, $\arccos$, and $\arctan$ to each other and to right-triangle geometry. Because $\sin\theta + \cos(\frac{\pi}{2}-\theta) = 0$ vanishes trivially — more precisely, because $\cos(\frac{\pi}{2}-\theta) = \sin\theta$ — if $x \in [-1,1]$ and $\alpha = \arcsin(x)$, then $\cos(\frac{\pi}{2}-\alpha) = x$ and $\frac{\pi}{2}-\alpha \in [0, \pi]$, so by the definition of $\arccos$ we obtain the complementary angle identity:

$$\arcsin(x) + \arccos(x) = \frac{\pi}{2} \quad \text{for all } x \in [-1, 1].$$

This identity is not a coincidence but a reflection of the geometric fact that $\arcsin(x)$ and $\arccos(x)$ are complementary angles in a right triangle whose hypotenuse is 1 and whose opposite side has length $x$. The identity reduces one of the three inverse functions to an expression involving the other, a useful reduction in both manual derivation and symbolic computation.

## 2. Core Architecture & Mechanics

Understanding the inverse trigonometric functions in depth requires dissecting two interlocking structures: the geometric algebra that produces explicit expressions for composed inverse functions, and the solution architecture for trigonometric equations, which translates the analytic machinery of inverse functions into a systematic procedure for finding solution sets.

### The Right-Triangle Extraction Principle

The most powerful technique for evaluating expressions like $\sin(\arctan(x))$ or $\cos(\arcsin(x))$ without a calculator is what we might call right-triangle extraction. The idea is to interpret the inner inverse function as an angle, draw the right triangle that realizes that angle, and read off the outer trigonometric function from the triangle's side lengths using the Pythagorean theorem.

Consider $\cos(\arcsin(x))$ for $x \in [-1,1]$. Set $\theta = \arcsin(x)$, so $\theta \in \left[-\frac{\pi}{2}, \frac{\pi}{2}\right]$ and $\sin\theta = x$. In a right triangle with hypotenuse 1 and opposite side $x$, the adjacent side has length $\sqrt{1-x^2}$ by the Pythagorean theorem. Since $\theta \in \left[-\frac{\pi}{2}, \frac{\pi}{2}\right]$, we have $\cos\theta \geq 0$, so there is no sign ambiguity and

$$\cos(\arcsin(x)) = \sqrt{1-x^2}.$$

The same logic produces $\sin(\arccos(x)) = \sqrt{1-x^2}$ — an identity superficially identical, but derived from a different triangle and valid on the same domain $[-1,1]$.

For $\tan(\arcsin(x))$ with $x \in (-1, 1)$: setting $\theta = \arcsin(x)$ and using the same triangle, the side opposite $\theta$ is $x$ and the adjacent side is $\sqrt{1-x^2}$, giving

$$\tan(\arcsin(x)) = \frac{x}{\sqrt{1-x^2}}.$$

The case $\sin(\arctan(x))$ requires a different triangle. Set $\theta = \arctan(x)$, so $\tan\theta = x$. We build a right triangle with opposite side $x$ and adjacent side $1$, giving hypotenuse $\sqrt{1+x^2}$. Since $\theta \in \left(-\frac{\pi}{2}, \frac{\pi}{2}\right)$ implies $\cos\theta > 0$, the hypotenuse carries no ambiguity, yielding

$$\sin(\arctan(x)) = \frac{x}{\sqrt{1+x^2}}, \qquad \cos(\arctan(x)) = \frac{1}{\sqrt{1+x^2}}.$$

These two identities appear frequently in calculus (the integral of $\frac{1}{1+x^2}$ is exactly $\arctan(x) + C$, a fact connected to the second identity through differentiation) and in Fourier analysis, signal processing formulations, and the normalization of probability distributions.

### Addition Formulas for Inverse Tangent

The arctangent addition formula is a fundamental tool. We wish to find $\arctan(a) + \arctan(b)$ as a single expression. Set $\alpha = \arctan(a)$ and $\beta = \arctan(b)$, so $\tan\alpha = a$ and $\tan\beta = b$. The tangent addition formula gives

$$\tan(\alpha + \beta) = \frac{\tan\alpha + \tan\beta}{1 - \tan\alpha\tan\beta} = \frac{a+b}{1-ab},$$

provided $ab \neq 1$. However, the value $\arctan\!\left(\frac{a+b}{1-ab}\right)$ lives in $\left(-\frac{\pi}{2}, \frac{\pi}{2}\right)$, while $\alpha + \beta$ may lie outside this interval. The complete identity requires a correction term:

$$\arctan(a) + \arctan(b) = \begin{cases} \arctan\!\left(\dfrac{a+b}{1-ab}\right) & \text{if } ab < 1, \\[6pt] \arctan\!\left(\dfrac{a+b}{1-ab}\right) + \pi & \text{if } ab > 1,\ a > 0, \\[6pt] \arctan\!\left(\dfrac{a+b}{1-ab}\right) - \pi & \text{if } ab > 1,\ a < 0. \end{cases}$$

The correction arises because when $ab > 1$, both $\alpha$ and $\beta$ have the same sign and their sum exceeds $\frac{\pi}{2}$ in magnitude, pushing $\alpha + \beta$ outside the principal range of $\arctan$. The correction of $\pm\pi$ restores the angle to the correct branch. A classical corollary is Machin's formula, $\frac{\pi}{4} = 4\arctan\!\left(\frac{1}{5}\right) - \arctan\!\left(\frac{1}{239}\right)$, which follows by applying the addition formula iteratively and was used historically for high-precision computation of $\pi$.

### Solution Architecture for Trigonometric Equations

Solving a trigonometric equation systematically demands a clear separation between two tasks: finding all solutions within a *principal interval*, and then extending to the *general solution* on $\mathbb{R}$ using the period of the function. The inverse trigonometric functions serve as the instrument for the first task.

The fundamental structure of the general solution is determined by the symmetry of each circular function.

**Sine equations.** The equation $\sin\theta = c$ for $c \in [-1,1]$ has, within any interval of length $2\pi$, exactly two solutions (or one if $c = \pm 1$). The principal solution is $\theta_0 = \arcsin(c) \in \left[-\frac{\pi}{2}, \frac{\pi}{2}\right]$. The second solution within $[0, 2\pi)$ exploits the symmetry $\sin(\pi - \theta) = \sin\theta$: it is $\pi - \theta_0$. The general solution is therefore

$$\theta = \arcsin(c) + 2\pi k \quad \text{or} \quad \theta = \pi - \arcsin(c) + 2\pi k, \quad k \in \mathbb{Z}.$$

**Cosine equations.** The equation $\cos\theta = c$ for $c \in [-1,1]$ uses the symmetry $\cos(-\theta) = \cos\theta$. The principal solution is $\theta_0 = \arccos(c) \in [0, \pi]$, and the second solution is $-\theta_0$. The general solution is

$$\theta = \pm\arccos(c) + 2\pi k, \quad k \in \mathbb{Z}.$$

**Tangent equations.** Because $\tan$ has period $\pi$ (not $2\pi$), and because its restriction to $\left(-\frac{\pi}{2}, \frac{\pi}{2}\right)$ already covers all of $\mathbb{R}$ as its range, $\tan\theta = c$ has exactly one solution per period-$\pi$ interval. The general solution is simply

$$\theta = \arctan(c) + \pi k, \quad k \in \mathbb{Z}.$$

The elegance of these templates lies in their uniformity. Any trigonometric equation, however complex, reduces to one of these three templates after algebraic manipulation. The process unfolds in three stages: algebraic reduction to isolate a single trigonometric function; application of the appropriate inverse function to extract the principal solution; and construction of the full solution family using the symmetry and periodicity of the function.

We examine this process through a fully worked example at escalating levels of sophistication.

**Example 1.** Solve $2\sin^2\theta - \sin\theta - 1 = 0$ for $\theta \in [0, 2\pi)$.

Treat $u = \sin\theta$ as the unknown variable. The equation becomes $2u^2 - u - 1 = 0$, which factors as $(2u + 1)(u - 1) = 0$. Thus $u = -\frac{1}{2}$ or $u = 1$.

For $\sin\theta = 1$: the unique solution in $[0, 2\pi)$ is $\theta = \frac{\pi}{2}$.

For $\sin\theta = -\frac{1}{2}$: the principal value is $\arcsin\!\left(-\frac{1}{2}\right) = -\frac{\pi}{6}$, which lies outside $[0, 2\pi)$. Applying the general solution template and selecting $k=1$ gives $-\frac{\pi}{6} + 2\pi = \frac{11\pi}{6}$, and $\pi - \left(-\frac{\pi}{6}\right) = \frac{7\pi}{6}$. Both $\frac{7\pi}{6}$ and $\frac{11\pi}{6}$ lie in $[0, 2\pi)$.

The solution set is $\left\{\frac{\pi}{2},\, \frac{7\pi}{6},\, \frac{11\pi}{6}\right\}$.

**Example 2.** Solve $\cos(2\theta) = \cos\theta$ for $\theta \in [0, 2\pi)$.

Expanding $\cos(2\theta) = 2\cos^2\theta - 1$, the equation becomes $2\cos^2\theta - 1 = \cos\theta$, or $2\cos^2\theta - \cos\theta - 1 = 0$. Factoring: $(2\cos\theta + 1)(\cos\theta - 1) = 0$, so $\cos\theta = -\frac{1}{2}$ or $\cos\theta = 1$.

For $\cos\theta = 1$: $\theta = 0$.

For $\cos\theta = -\frac{1}{2}$: the principal value is $\arccos\!\left(-\frac{1}{2}\right) = \frac{2\pi}{3}$, and the second solution is $-\frac{2\pi}{3} + 2\pi = \frac{4\pi}{3}$.

The solution set is $\left\{0,\, \frac{2\pi}{3},\, \frac{4\pi}{3}\right\}$.

Alternatively, the original equation $\cos(2\theta) = \cos\theta$ can be solved directly using the identity $\cos A = \cos B \iff A = \pm B + 2\pi k$. This gives $2\theta = \theta + 2\pi k$ (yielding $\theta = 2\pi k$) or $2\theta = -\theta + 2\pi k$ (yielding $\theta = \frac{2\pi k}{3}$). Both approaches yield the same solution set, and verifying that they agree is a useful internal consistency check.

**Example 3.** Solve $\tan^2\theta - (1+\sqrt{3})\tan\theta + \sqrt{3} = 0$ for $\theta \in [0, 2\pi)$.

This factors as $(\tan\theta - 1)(\tan\theta - \sqrt{3}) = 0$. So $\tan\theta = 1$ or $\tan\theta = \sqrt{3}$.

For $\tan\theta = 1$: $\arctan(1) = \frac{\pi}{4}$, and the general solution $\frac{\pi}{4} + \pi k$ gives $\theta = \frac{\pi}{4}$ and $\theta = \frac{5\pi}{4}$ in $[0, 2\pi)$.

For $\tan\theta = \sqrt{3}$: $\arctan(\sqrt{3}) = \frac{\pi}{3}$, and the general solution $\frac{\pi}{3} + \pi k$ gives $\theta = \frac{\pi}{3}$ and $\theta = \frac{4\pi}{3}$ in $[0, 2\pi)$.

The solution set is $\left\{\frac{\pi}{4},\, \frac{\pi}{3},\, \frac{5\pi}{4},\, \frac{4\pi}{3}\right\}$.

The following diagram summarizes the full solution-finding pipeline:

```
INPUT: f(θ) = c

        │
        ▼
┌───────────────────────────────┐
│  ALGEBRAIC REDUCTION          │
│  Isolate a single circular    │
│  function via substitution,   │
│  factoring, or identities.    │
└──────────────┬────────────────┘
               │
               ▼
┌───────────────────────────────┐
│  IDENTIFY FUNCTION TYPE       │
│                               │
│  sin θ = c │ cos θ = c │ tan θ = c
└──────┬──────┴────┬─────┴───┬──┘
       │           │         │
       ▼           ▼         ▼
 θ₀=arcsin(c)  θ₀=arccos(c) θ₀=arctan(c)
 θ₁=π−θ₀       θ₁=−θ₀      (one solution
                             per period)
       │           │         │
       └───────────┴─────────┘
               │
               ▼
┌───────────────────────────────┐
│  GENERAL SOLUTION             │
│  Add period multiples:        │
│  sin/cos → +2πk              │
│  tan     → +πk               │
└──────────────┬────────────────┘
               │
               ▼
┌───────────────────────────────┐
│  FILTER TO REQUIRED INTERVAL  │
│  Select k ∈ ℤ such that       │
│  solution lies in [a, b).     │
└───────────────────────────────┘
```

## 3. High-Performance Optimization & Failure Modes

The machinery developed above is robust when applied correctly, but it harbors several subtle failure modes that trap even careful practitioners. Understanding them not as isolated mistakes but as structural phenomena — each arising from a specific invariant of the inverse functions — transforms error avoidance from vigilance into comprehension.

### Domain Restriction Violations

The most pervasive failure mode is ignoring the range constraints of the inverse functions. A student asked to verify that $\arcsin(\sin(2\pi/3)) = 2\pi/3$ may write this down without checking that $2\pi/3 \in \left[-\frac{\pi}{2}, \frac{\pi}{2}\right]$. It does not. The correct evaluation is $\sin(2\pi/3) = \frac{\sqrt{3}}{2}$ and $\arcsin\!\left(\frac{\sqrt{3}}{2}\right) = \frac{\pi}{3}$. The error is not arithmetic but conceptual: the composition $\arcsin \circ \sin$ is not the identity outside the restricted domain.

This failure mode becomes critical in equation solving whenever solutions are proposed but not checked against the original equation's domain. The equation $\arcsin(2x+1) = \frac{\pi}{6}$ requires not only that $\sin\!\left(\frac{\pi}{6}\right) = 2x+1$, giving $x = -\frac{1}{4}$, but also that the argument $2x+1 = \frac{1}{2}$ satisfies the domain condition $2x+1 \in [-1,1]$. Here it does, but the check is mandatory in general.

### Extraneous Solutions from Squaring

Squaring both sides of a trigonometric equation to eliminate radicals or simplify expressions is a legitimate algebraic technique, but it introduces extraneous solutions by collapsing the sign information of both sides. Consider the equation $\sin\theta + \cos\theta = 1$. Squaring gives $1 + 2\sin\theta\cos\theta = 1$, so $\sin(2\theta) = 0$, which yields $2\theta = \pi k$, or $\theta = \frac{\pi k}{2}$, producing the candidates $\{0, \frac{\pi}{2}, \pi, \frac{3\pi}{2}\}$ in $[0, 2\pi)$. Substituting back: $\theta = 0$ gives $0+1=1$ ✓, $\theta = \frac{\pi}{2}$ gives $1+0=1$ ✓, $\theta = \pi$ gives $0+(-1)=-1 \neq 1$ ✗, $\theta = \frac{3\pi}{2}$ gives $-1+0=-1 \neq 1$ ✗. The squaring operation introduced $\theta = \pi$ and $\theta = \frac{3\pi}{2}$ as extraneous solutions. The mandatory verification step is not bureaucratic formality; it is load-bearing mathematics.

### Missing Solutions from Range Truncation

The inverse of the previous failure mode is equally damaging: missing solutions by implicitly treating an inverse function as though it covers the full circle. The equation $\cos\theta = -\frac{\sqrt{2}}{2}$ has two solutions in $[0, 2\pi)$. A practitioner who writes $\theta = \arccos\!\left(-\frac{\sqrt{2}}{2}\right) = \frac{3\pi}{4}$ and stops has found only half of the solution set. The second solution, $\theta = \frac{5\pi}{4}$, follows from the symmetry $\cos(2\pi - \theta_0) = \cos\theta_0$. The general solution template $\theta = \pm\arccos(c) + 2\pi k$ exists precisely to prevent this omission; it encodes both branches of the cosine's symmetry.

For the sine and tangent cases, the template $\theta = \arcsin(c) + 2\pi k$ and $\theta = \pi - \arcsin(c) + 2\pi k$ must both be written. The two branches are independent families, and no algebraic manipulation reduces one to the other unless $c = \pm 1$.

### Equations Involving Composed Expressions

A subtler failure arises with equations like $\arcsin(x) + \arccos(x) = \frac{\pi}{2}$. Rather than attempting to invert both sides or isolate one term, the practitioner should recognize this as the complementary angle identity, valid for all $x \in [-1,1]$, and conclude the equation holds everywhere on its natural domain. Algebraic manipulation is not needed; identity recognition terminates the problem.

More demanding is an equation like $\arctan(x) + \arctan\!\left(\frac{1}{x}\right) = \frac{\pi}{2}$ for $x > 0$. Setting $\alpha = \arctan(x)$ and $\beta = \arctan\!\left(\frac{1}{x}\right)$, we have $\tan\alpha = x$ and $\tan\beta = 1/x$. If $x > 0$, then both $\alpha, \beta \in \left(0, \frac{\pi}{2}\right)$, and $\tan(\alpha + \beta) = \frac{x + 1/x}{1 - x\cdot(1/x)} = \frac{x+1/x}{0}$, which is undefined. An undefined tangent at a sum of two angles in $\left(0, \frac{\pi}{2}\right)$ means that sum equals $\frac{\pi}{2}$, confirming the identity. For $x < 0$, the analogous argument shows $\arctan(x) + \arctan\!\left(\frac{1}{x}\right) = -\frac{\pi}{2}$. The sign of $x$ determines which branch applies — another instance where domain tracking is not optional.

### Equations with Multiple Angles

Equations of the form $\sin(n\theta) = c$ require particular care. The substitution $\phi = n\theta$ converts the equation to $\sin\phi = c$, but the interval for $\phi$ must be rescaled. If $\theta \in [0, 2\pi)$, then $\phi = n\theta \in [0, 2\pi n)$, so we must collect all solutions of $\sin\phi = c$ in the larger interval $[0, 2\pi n)$ and then divide each by $n$. Missing the rescaling of the interval is the standard error; it systematically discards $n-1$ out of every $n$ solution families.

**Example.** Solve $\sin(2\theta) = \frac{\sqrt{3}}{2}$ for $\theta \in [0, 2\pi)$.

Let $\phi = 2\theta \in [0, 4\pi)$. Then $\sin\phi = \frac{\sqrt{3}}{2}$, with principal value $\arcsin\!\left(\frac{\sqrt{3}}{2}\right) = \frac{\pi}{3}$. The general solution is $\phi = \frac{\pi}{3} + 2\pi k$ or $\phi = \pi - \frac{\pi}{3} + 2\pi k = \frac{2\pi}{3} + 2\pi k$.

For $\phi \in [0, 4\pi)$:

$$\phi \in \left\{\frac{\pi}{3},\ \frac{2\pi}{3},\ \frac{\pi}{3}+2\pi,\ \frac{2\pi}{3}+2\pi\right\} = \left\{\frac{\pi}{3},\ \frac{2\pi}{3},\ \frac{7\pi}{3},\ \frac{8\pi}{3}\right\}.$$

Dividing by 2: $\theta \in \left\{\frac{\pi}{6},\ \frac{\pi}{3},\ \frac{7\pi}{6},\ \frac{4\pi}{3}\right\}$.

Had we searched only in $\phi \in [0, 2\pi)$, we would have found only $\frac{\pi}{6}$ and $\frac{\pi}{3}$, losing half the solution set.

### Continuity and the Intermediate Value as a Diagnostic

When a trigonometric equation's solution set is unexpected — empty when solutions seem likely, or yielding a single solution when two are expected — the intermediate value theorem and the monotonicity structure of the inverse functions serve as diagnostics. If $f(\theta) = c$ on a closed interval $[a,b]$ and $f$ is continuous with $f(a) < c < f(b)$, the equation has at least one solution by IVT. If $f$ is strictly monotone on $[a,b]$, it has exactly one. These facts allow a practitioner to predict the solution count before computing, and to detect errors when the computed count disagrees with the prediction.

The inverse trigonometric functions are themselves continuous on their domains: $\arcsin$ and $\arccos$ are continuous on $[-1,1]$, and $\arctan$ is continuous on all of $\mathbb{R}$. Their derivatives, derivable by implicit differentiation, are

$$\frac{d}{dx}\arcsin(x) = \frac{1}{\sqrt{1-x^2}}, \quad \frac{d}{dx}\arccos(x) = -\frac{1}{\sqrt{1-x^2}}, \quad \frac{d}{dx}\arctan(x) = \frac{1}{1+x^2}.$$

The first two blow up as $x \to \pm 1$, confirming that $\arcsin$ and $\arccos$ have vertical tangents at the endpoints of their domains — the same points where $\sin$ and $\cos$ have horizontal tangents on their restricted domains, as the inverse function theorem demands. The derivative of $\arctan$ is bounded above by 1 (achieved at $x=0$) and decays as $x \to \pm\infty$, reflecting the deceleration of the tangent function's inverse as the asymptotes of $\tan$ are approached. These derivative formulas are the analytical heart of integral calculus involving inverse trigonometric functions, and their derivation via the inverse function theorem closes the loop between the geometric construction of these functions and their analytic properties.

The lesson's invariants can be stated compactly as a working principle: every inverse trigonometric expression carries both a value and a range constraint, and both must be tracked simultaneously. Dropping the range constraint is the universal source of error in this subject — it converts a precisely defined function into an ambiguous multi-valued relation, and from that point forward, any calculation is building on sand.
