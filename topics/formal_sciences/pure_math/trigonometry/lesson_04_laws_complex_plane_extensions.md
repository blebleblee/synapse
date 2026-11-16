# Lesson 4: Laws of Triangles, Complex Exponentials, and Analytic Extensions

## 1. First-Principles Intuition & Invariants

Trigonometry announces its deepest ambitions not in the right triangle, but the moment you abandon it. The right triangle is a scaffold: pedagogically convenient, computationally tractable, but structurally impoverished. The moment you generalize to an oblique triangle — no right angle, no obvious altitude, no axis-aligned symmetry — you are forced to confront the fact that the trigonometric ratios sine and cosine are not properties of triangles at all. They are properties of angles, and their true operating domain is the entire real line, then the complex plane, and ultimately the full analytic landscape of holomorphic functions. This lesson traces that expansion systematically, beginning at the oblique triangle, passing through Euler's formula, climbing into hyperbolic analysis, and grounding every step in Taylor series from first principles.

The law of sines and the law of cosines are not mere formulas to memorize. They are invariants: relationships that hold for every triangle in the Euclidean plane regardless of its shape, encoding deep structural constraints between the edge lengths and the angles that subtend them. Understanding why they are true — not just that they are — requires you to build them from scratch, and the construction is surprisingly economical. It demands only the definition of sine as a ratio and the Pythagorean theorem, yet it yields relationships powerful enough to solve every triangle determination problem in classical geometry.

Consider an oblique triangle $ABC$ with vertices labeled so that side $a$ lies opposite angle $A$, side $b$ lies opposite angle $B$, and side $c$ lies opposite angle $C$. The fundamental constraint is that $A + B + C = \pi$ (we always work in radians). There is no assumed right angle. The operative question is: given partial information about the triangle, can we determine the rest? The answer is yes, and the machinery that provides it encodes a beautiful symmetry in the relationship between angles and their opposite sides.

### The Law of Sines: Proof from the Circumradius

Drop an altitude from vertex $C$ to side $c$, landing at a point $H$ on the line through $A$ and $B$. If $H$ lies between $A$ and $B$, the triangle is acute; if $H$ lies outside the segment, the triangle is obtuse. Both cases yield the same algebraic result, so we treat the acute case without loss of generality in the exposition. The altitude has length $h_c$, and by the definition of sine applied to angle $A$ within the right triangle $AHC$:

$$h_c = b \sin A$$

Applied to angle $B$ within the right triangle $BHC$:

$$h_c = a \sin B$$

Setting these equal: $b \sin A = a \sin B$, which rearranges immediately to

$$\frac{a}{\sin A} = \frac{b}{\sin B}$$

Repeating the argument by dropping an altitude from $A$ to side $a$ gives $\frac{b}{\sin B} = \frac{c}{\sin C}$, completing the law of sines:

$$\frac{a}{\sin A} = \frac{b}{\sin B} = \frac{c}{\sin C} = 2R$$

The appearance of $2R$ — where $R$ is the circumradius of the triangle — is not a coincidence or a bookkeeping artifact. It is a theorem in its own right, known as the extended law of sines, and it deserves a proof.

**Theorem (Extended Law of Sines).** For any triangle $ABC$ inscribed in a circle of radius $R$, the common ratio $a / \sin A$ equals $2R$.

**Proof.** Place the circumscribed circle at the origin with radius $R$. Let $D$ be the point on the circle diametrically opposite $A$, so $AD$ is a diameter of length $2R$. The angle $\angle ABD$ inscribed in a semicircle is a right angle (Thales' theorem), so $BD \perp AB$. Now consider the arc $BC$: the inscribed angle theorem states that any inscribed angle subtending arc $BC$ is equal to the central angle subtending that arc divided by two. The central angle subtending arc $BC$ equals $2A$ (since $\angle BAC = A$ is inscribed and subtends the same arc). The inscribed angle $\angle BDC$ also subtends arc $BC$, hence $\angle BDC = A$. In the right triangle $ABD$, we have $BD = AD \sin(\angle BDC) = 2R \sin A$. But by our earlier derivation, $BD = a$ only when the configuration is set up so that $BD$ corresponds to side $a$. More precisely, by the inscribed angle theorem applied directly in triangle $ABD$: $\sin(\angle ADB) = a / AD = a / 2R$, and $\angle ADB = A$ because both angles subtend arc $AB$ from the same side. Therefore $\sin A = a / 2R$, giving $a / \sin A = 2R$. $\blacksquare$

The circumradius formula has immediate computational value. Given three sides of a triangle, Heron's formula yields the area, which then yields $R$ through $R = abc / (4K)$ where $K$ is the area. Given two angles and an enclosed side, the circumradius materializes from a single division.

### The Law of Cosines: Proof from the Distance Formula

The law of cosines generalizes the Pythagorean theorem to arbitrary triangles. It states that for a triangle $ABC$ with the standard notation above:

$$c^2 = a^2 + b^2 - 2ab\cos C$$

The proof is an application of Cartesian coordinates applied directly to the Euclidean distance formula. Place $C$ at the origin and $B$ on the positive $x$-axis. Then $B = (a, 0)$ and $A = (b\cos C, b\sin C)$, since the angle at $C$ between sides $CA$ and $CB$ is $\angle C$, the side $CA$ has length $b$, and $A$ lies at angle $C$ from the $x$-axis. The distance $c = AB$ is then:

$$c^2 = (b\cos C - a)^2 + (b\sin C - 0)^2$$

Expanding:

$$c^2 = b^2\cos^2 C - 2ab\cos C + a^2 + b^2\sin^2 C$$

$$c^2 = b^2(\cos^2 C + \sin^2 C) + a^2 - 2ab\cos C$$

$$c^2 = a^2 + b^2 - 2ab\cos C$$

The Pythagorean identity $\cos^2 C + \sin^2 C = 1$ does the essential work in the final collapse. When $C = \pi/2$, $\cos C = 0$ and the law of cosines reduces exactly to $c^2 = a^2 + b^2$, confirming the Pythagorean theorem as a degenerate case. The law of cosines is therefore strictly stronger: it subsumes the Pythagorean theorem and handles every triangle, not just right-angled ones.

The area formula for an oblique triangle follows immediately from the altitude construction used in the law of sines proof. The area $K$ of a triangle is one-half base times height. Using base $c$ and the altitude $h_c = b\sin A$:

$$K = \frac{1}{2}ab\sin C = \frac{1}{2}bc\sin A = \frac{1}{2}ac\sin B$$

All three expressions are equivalent by symmetry, and each requires knowing two sides and the included angle. This is not an approximation or a convenient shorthand; it is an exact formula, derivable in two lines from the altitude construction and the definition of sine.

### From Trigonometric Ratios to Analytic Functions

Having established the triangle laws, we have used sine and cosine as geometric ratios, defined for angles in $[0, \pi]$. But the deeper structure of these functions only becomes visible when we extend them to all real inputs — and then beyond, to complex inputs. The vehicle for this extension is not geometric reasoning but analytic: the Taylor series.

The Taylor series for a smooth function $f$ around $x = 0$ is the power series whose coefficients are $f^{(n)}(0)/n!$. For this to be a valid representation of $f$, the series must converge to $f$ on the domain of interest, not merely be formally derivable. For $\sin x$ and $\cos x$, the series converges absolutely for every $x \in \mathbb{R}$, and in fact for every $x \in \mathbb{C}$ — a fact that licenses the analytic continuation we need.

We derive the series by computing derivatives at the origin. Let $f(x) = \sin x$. The derivative chain is $f'(x) = \cos x$, $f''(x) = -\sin x$, $f'''(x) = -\cos x$, $f^{(4)}(x) = \sin x$, and the pattern repeats with period 4. Evaluating at $x = 0$: $f(0) = 0$, $f'(0) = 1$, $f''(0) = 0$, $f'''(0) = -1$, and the cycle repeats. The Taylor series is therefore:

$$\sin x = x - \frac{x^3}{3!} + \frac{x^5}{5!} - \frac{x^7}{7!} + \cdots = \sum_{n=0}^{\infty} \frac{(-1)^n x^{2n+1}}{(2n+1)!}$$

For $g(x) = \cos x$: $g(0) = 1$, $g'(0) = 0$, $g''(0) = -1$, $g'''(0) = 0$, and again the period-4 pattern gives:

$$\cos x = 1 - \frac{x^2}{2!} + \frac{x^4}{4!} - \frac{x^6}{6!} + \cdots = \sum_{n=0}^{\infty} \frac{(-1)^n x^{2n}}{(2n)!}$$

That these series converge everywhere on $\mathbb{R}$ follows from the ratio test. For $\sin x$, the ratio of successive terms is $|x|^2 / ((2n+2)(2n+3)) \to 0$ as $n \to \infty$ for any fixed $x$, so the radius of convergence is infinite.

Now notice something remarkable: these are power series with real coefficients and unrestricted radius of convergence. There is no geometric obstruction preventing us from substituting a complex number $z \in \mathbb{C}$ for $x$. The series converge absolutely for all $z \in \mathbb{C}$, and the resulting functions are holomorphic (complex-differentiable) everywhere. This is the analytic extension of sine and cosine to the complex plane, and it is conceptually distinct from any geometric definition.

## 2. Core Architecture & Mechanics

### Euler's Formula: Derivation and Structure

Euler's formula is not an observation but a theorem, and its proof requires nothing more than the three Taylor series we have already derived for $\sin x$, $\cos x$, and $e^x$. The exponential series is:

$$e^x = \sum_{n=0}^{\infty} \frac{x^n}{n!} = 1 + x + \frac{x^2}{2!} + \frac{x^3}{3!} + \frac{x^4}{4!} + \cdots$$

Substitute $x = i\theta$ where $i^2 = -1$ and $\theta \in \mathbb{R}$:

$$e^{i\theta} = 1 + i\theta + \frac{(i\theta)^2}{2!} + \frac{(i\theta)^3}{3!} + \frac{(i\theta)^4}{4!} + \frac{(i\theta)^5}{5!} + \cdots$$

Compute the powers of $i$: $i^0 = 1$, $i^1 = i$, $i^2 = -1$, $i^3 = -i$, $i^4 = 1$, and the cycle repeats. Substituting:

$$e^{i\theta} = 1 + i\theta - \frac{\theta^2}{2!} - \frac{i\theta^3}{3!} + \frac{\theta^4}{4!} + \frac{i\theta^5}{5!} - \cdots$$

Separating real and imaginary parts:

$$e^{i\theta} = \left(1 - \frac{\theta^2}{2!} + \frac{\theta^4}{4!} - \cdots\right) + i\left(\theta - \frac{\theta^3}{3!} + \frac{\theta^5}{5!} - \cdots\right)$$

The first parenthetical is exactly the Taylor series for $\cos\theta$. The second is exactly the Taylor series for $\sin\theta$. Therefore:

$$\boxed{e^{i\theta} = \cos\theta + i\sin\theta}$$

This is Euler's formula. Its proof is complete, and its depth is structural rather than numeric. The exponential function, defined axiomatically through its power series, automatically encodes rotation in the complex plane when fed a purely imaginary argument. The real part traces the cosine of the angle; the imaginary part traces the sine. The complex unit circle $|z| = 1$ is parametrized exactly by $e^{i\theta}$ as $\theta$ ranges over $[0, 2\pi)$.

Euler's identity, often called the most beautiful equation in mathematics, is the special case $\theta = \pi$:

$$e^{i\pi} + 1 = 0$$

It is not a miracle or a numerical coincidence. It is a direct consequence of $\cos\pi = -1$ and $\sin\pi = 0$, combined with Euler's formula. The five constants $e, i, \pi, 1, 0$ appear not because of deep metaphysical resonance but because the Taylor series for $e^x$, $\cos x$, and $\sin x$ interlock precisely as the power-of-$i$ cycle dictates.

### Inverting Euler's Formula: Sine and Cosine from the Exponential

Euler's formula enables an algebraic inversion that expresses the real trigonometric functions in terms of complex exponentials. Write Euler's formula for $\theta$ and for $-\theta$:

$$e^{i\theta} = \cos\theta + i\sin\theta$$
$$e^{-i\theta} = \cos\theta - i\sin\theta$$

Adding these two equations gives $e^{i\theta} + e^{-i\theta} = 2\cos\theta$, so:

$$\cos\theta = \frac{e^{i\theta} + e^{-i\theta}}{2}$$

Subtracting the second from the first gives $e^{i\theta} - e^{-i\theta} = 2i\sin\theta$, so:

$$\sin\theta = \frac{e^{i\theta} - e^{-i\theta}}{2i}$$

These expressions are not alternative definitions; they are identities, true for all real $\theta$ and by analytic continuation for all complex $z$. They are the standard method for proving trigonometric identities via algebra on exponentials, because exponential multiplication is simpler than sum-to-product transformations.

As a concrete illustration, derive the double-angle formula for cosine from the exponential form. The goal is to compute $\cos(2\theta)$:

$$\cos(2\theta) = \frac{e^{2i\theta} + e^{-2i\theta}}{2} = \frac{(e^{i\theta})^2 + (e^{-i\theta})^2}{2}$$

Using $(a + b)^2 = a^2 + 2ab + b^2$ and $(a - b)^2 = a^2 - 2ab + b^2$ where $a = e^{i\theta}$ and $b = e^{-i\theta}$:

$$(e^{i\theta} + e^{-i\theta})^2 = e^{2i\theta} + 2e^{i\theta}e^{-i\theta} + e^{-2i\theta} = e^{2i\theta} + 2 + e^{-2i\theta}$$

So $e^{2i\theta} + e^{-2i\theta} = (e^{i\theta} + e^{-i\theta})^2 - 2 = (2\cos\theta)^2 - 2 = 4\cos^2\theta - 2$. Substituting:

$$\cos(2\theta) = \frac{4\cos^2\theta - 2}{2} = 2\cos^2\theta - 1$$

This matches the standard double-angle formula. The same technique — writing the target angle's exponential in terms of the half-angle exponential and expanding algebraically — derives every product-to-sum formula, power reduction formula, and sum-to-product identity systematically, without trigonometric identities as a prerequisite.

### The Structural Relationship Between Circular and Hyperbolic Functions

The exponential form of sine and cosine reveals a structural kinship with the hyperbolic functions that is invisible from the geometric definition. The hyperbolic cosine and sine are defined by:

$$\cosh x = \frac{e^x + e^{-x}}{2}, \qquad \sinh x = \frac{e^x - e^{-x}}{2}$$

Compare with the circular formulas:

$$\cos\theta = \frac{e^{i\theta} + e^{-i\theta}}{2}, \qquad \sin\theta = \frac{e^{i\theta} - e^{-i\theta}}{2i}$$

The structural parallel is exact. The only difference is that the circular functions are evaluated at imaginary arguments of the exponential, while the hyperbolic functions use real arguments. This immediately implies the Osborn-Euler relations connecting the two families:

$$\cos(ix) = \cosh(x), \qquad \sin(ix) = i\sinh(x)$$

**Derivation of $\cos(ix) = \cosh(x)$:** Applying Euler's formula with $\theta = ix$ gives $e^{i(ix)} = e^{-x}$, so

$$\cos(ix) = \frac{e^{i(ix)} + e^{-i(ix)}}{2} = \frac{e^{-x} + e^{x}}{2} = \cosh x$$

**Derivation of $\sin(ix) = i\sinh(x)$:**

$$\sin(ix) = \frac{e^{i(ix)} - e^{-i(ix)}}{2i} = \frac{e^{-x} - e^{x}}{2i} = \frac{-(e^x - e^{-x})}{2i} = \frac{e^x - e^{-x}}{2} \cdot \frac{-1}{i}$$

Since $-1/i = i$ (because $i \cdot (-1/i) = -1 \cdot (1) \cdot ... $, more cleanly: multiply numerator and denominator of $-1/i$ by $i$ to get $-i/i^2 = -i/(-1) = i$), we have:

$$\sin(ix) = i \cdot \frac{e^x - e^{-x}}{2} = i\sinh x$$

These relations allow every hyperbolic identity to be derived from its circular counterpart by substitution. The Pythagorean identity $\cos^2\theta + \sin^2\theta = 1$ becomes the hyperbolic identity $\cosh^2 x - \sinh^2 x = 1$ under the substitution $\theta = ix$:

$$\cos^2(ix) + \sin^2(ix) = 1$$
$$\cosh^2(x) + (i\sinh x)^2 = 1$$
$$\cosh^2(x) - \sinh^2(x) = 1$$

The sign flip from $+$ to $-$ is entirely accounted for by $i^2 = -1$. There is no separate proof needed for the hyperbolic Pythagorean identity; it is a shadow of the circular identity cast through the imaginary axis.

The Taylor series for $\cosh x$ and $\sinh x$ follow directly from those for $\cos$ and $\sin$ by the same substitution mechanism. Since $\cosh x = \cos(ix)$ and the series for $\cos$ is $\sum_{n=0}^\infty (-1)^n x^{2n}/(2n)!$, substitute $ix$ for $x$:

$$\cosh x = \sum_{n=0}^{\infty} \frac{(-1)^n (ix)^{2n}}{(2n)!} = \sum_{n=0}^{\infty} \frac{(-1)^n i^{2n} x^{2n}}{(2n)!} = \sum_{n=0}^{\infty} \frac{(-1)^n (-1)^n x^{2n}}{(2n)!} = \sum_{n=0}^{\infty} \frac{x^{2n}}{(2n)!}$$

since $i^{2n} = (i^2)^n = (-1)^n$. The alternating signs cancel: $(-1)^n \cdot (-1)^n = (-1)^{2n} = 1$. Thus:

$$\cosh x = 1 + \frac{x^2}{2!} + \frac{x^4}{4!} + \frac{x^6}{6!} + \cdots$$

This is the cosine series with the signs uniformly $+1$, reflecting the fact that $\cosh x \geq 1$ for all real $x$, while $\cos x$ oscillates. Similarly, $\sinh x$ has the same series as $\sin x$ but with uniform positive signs:

$$\sinh x = x + \frac{x^3}{3!} + \frac{x^5}{5!} + \cdots = \sum_{n=0}^{\infty} \frac{x^{2n+1}}{(2n+1)!}$$

The structural diagram of these relationships is worth making explicit. The exponential function $e^z$ over $\mathbb{C}$ is the common ancestor; circular and hyperbolic trigonometry are two orthogonal slices through it.

```
                        e^z  (entire function on ℂ)
                       /           \
            z = iθ (imaginary)    z = x (real)
           /                              \
  e^{iθ} = cosθ + i sinθ          e^x = cosh x + sinh x
  (Euler's formula)                (hyperbolic decomposition)
           \                              /
            \______________________________/
                     z = x + iθ
           e^{x+iθ} = e^x(cosθ + i sinθ)
           (general complex exponential)
```

The bottom row is the full complex exponential in Cartesian coordinates: modulus $e^x$, argument $\theta$. Every complex number's exponential is a scaled rotation, and $e^x = \cosh x + \sinh x$ is simply the real-valued decomposition of $e^x$ into its even and odd parts, exactly as $e^{i\theta} = \cos\theta + i\sin\theta$ decomposes the complex exponential into its real and imaginary parts.

## 3. High-Performance Optimization & Failure Modes

### Precision and Stability in Series Truncation

The Taylor series for sine and cosine are entire functions — they converge everywhere — but truncating the series at a finite number of terms introduces a remainder whose behavior depends sensitively on the input. The remainder after $N$ terms of the sine series is bounded by the Lagrange form:

$$|R_N(x)| \leq \frac{|x|^{N+1}}{(N+1)!}$$

For small $x$, this remainder is negligible quickly: $\sin(0.1) \approx 0.1 - 0.001/6 = 0.09983\overline{3}$, accurate to six decimal places with just two terms. For large $x$, however, the terms of the Taylor series grow before they begin to shrink, because the factorial in the denominator grows faster than the power in the numerator, but the crossover point occurs around $n \approx |x|$. For $x = 10$, the terms grow until $n \approx 10$ and then decay; the partial sums oscillate wildly before converging. This is catastrophic cancellation: large positive and negative terms cancel to produce a small result, and floating-point arithmetic cannot represent the intermediate large terms with sufficient precision to yield an accurate final answer.

The standard computational resolution is argument reduction: exploit the periodicity $\sin(x + 2\pi k) = \sin(x)$ to reduce any $x$ to the interval $[-\pi/4, \pi/4]$ before applying the series. Within this compact interval, the series is well-conditioned and three to four terms suffice for double-precision accuracy. The reduction requires a precise value of $\pi$ (or $2\pi$), and the accuracy of the computed $\pi$ propagates directly into the reduced argument — a critical point for implementations working near multiples of $\pi$.

A related instability arises in the law of cosines. When the angle $C$ is very small (nearly degenerate triangle with $C \approx 0$), $\cos C \approx 1 - C^2/2$ and the formula $c^2 = a^2 + b^2 - 2ab\cos C$ requires subtracting two nearly equal quantities, $a^2 + b^2$ and $2ab\cos C \approx 2ab$. When $a \approx b$, both are approximately $a^2$, and the difference $c^2$ is small relative to the operands. This is catastrophic cancellation in the triangle context. The numerically stable alternative is to use the half-angle substitution $\cos C = 1 - 2\sin^2(C/2)$, giving:

$$c^2 = a^2 + b^2 - 2ab(1 - 2\sin^2(C/2)) = (a - b)^2 + 4ab\sin^2(C/2)$$

Now the two terms $(a-b)^2$ and $4ab\sin^2(C/2)$ are both non-negative and no catastrophic cancellation can occur. For small $C$, $\sin(C/2) \approx C/2$ and the formula gives $c^2 \approx (a-b)^2 + ab C^2$, which is well-conditioned throughout.

### Analytic Continuation and the Zeros of the Sine Function

The analytic extension of sine to the complex plane $\sin z = (e^{iz} - e^{-iz})/(2i)$ is holomorphic on all of $\mathbb{C}$, making $\sin z$ an entire function. Its zeros on $\mathbb{R}$ are $z = n\pi$ for $n \in \mathbb{Z}$. The question of whether $\sin z$ acquires additional zeros in $\mathbb{C}$ is answered by solving $e^{iz} = e^{-iz}$, equivalently $e^{2iz} = 1$. Writing $z = x + iy$, this becomes $e^{2i(x+iy)} = e^{2ix - 2y} = 1$. For this to hold, we need $e^{-2y} = 1$ (hence $y = 0$) and $e^{2ix} = 1$ (hence $x = n\pi$). The zeros of $\sin z$ in $\mathbb{C}$ are exactly the real zeros $z = n\pi$; no complex zeros exist. This is a constraint on the entire function $\sin z$ that follows from the symmetry of the defining exponential representation.

An important failure mode in complex analysis arises when attempting to extend the inverse functions. On $\mathbb{R}$, $\arcsin$ is defined on $[-1, 1]$ with range $[-\pi/2, \pi/2]$ by restricting to a monotone branch. In $\mathbb{C}$, $\sin z$ is surjective onto all of $\mathbb{C}$ (by the intermediate and extreme value arguments generalized via Picard's theorem), and so the inverse $\arcsin$ can be defined for all complex inputs — but only by choosing a branch cut to make it single-valued. The standard branch cut for $\arcsin z$ runs along the real axis for $|x| > 1$. The complex logarithm, with its own branch cut, appears in the formula:

$$\arcsin z = -i \log\left(iz + \sqrt{1 - z^2}\right)$$

The square root $\sqrt{1-z^2}$ requires its own branch cut. Any computation crossing these branch cuts will produce discontinuous jumps — the analog of the sign flip when crossing the branch cut of the real square root at zero. In symbolic computation systems and computer algebra kernels, tracking branch cuts for composed inverse trigonometric functions is one of the most persistent sources of incorrect simplification. The identity $\arcsin(-z) = -\arcsin(z)$ holds on the principal branch but can fail when the branch cut is crossed during a symbolic manipulation.

### The Convexity and Growth Structure of Hyperbolic Functions

The hyperbolic functions exhibit qualitative behavior opposite to their circular counterparts in ways that matter for analysis and optimization. Whereas $\cos x$ is bounded and oscillatory on $\mathbb{R}$, $\cosh x$ is unbounded and convex, satisfying $\cosh x \geq 1$ with the unique minimum $\cosh(0) = 1$. The growth rate of $\cosh x$ is exponential: $\cosh x \sim e^x/2$ as $x \to +\infty$.

This growth structure makes $\cosh$ a natural regularization factor in transforms and integrals. The function $1/\cosh x = \text{sech}(x)$ decays exponentially and is integrable with the exact value:

$$\int_{-\infty}^{\infty} \text{sech}(x)\, dx = \pi$$

This integral can be evaluated by residue calculus, and its value $\pi$ is a reflection of the connection between hyperbolic functions and circular functions through the imaginary argument. The poles of $\text{sech}(z) = 1/\cosh(z)$ occur where $\cosh(z) = 0$, which requires $e^z + e^{-z} = 0$, giving $e^{2z} = -1 = e^{i\pi}$, so $z = i\pi(n + 1/2)$ for $n \in \mathbb{Z}$ — purely imaginary poles, spaced $i\pi$ apart along the imaginary axis.

The sum-to-product and product-to-sum identities for hyperbolic functions follow by the Osborn rule: take any trigonometric identity, replace $\sin$ with $\sinh$ and $\cos$ with $\cosh$, and negate any product of two $\sinh$ terms. The negation rule comes directly from $\sin(ix) = i\sinh x$: when squaring, $\sin^2(ix) = -\sinh^2 x$. For example, the circular identity

$$\cos(A + B) = \cos A \cos B - \sin A \sin B$$

becomes under the Osborn rule:

$$\cosh(A + B) = \cosh A \cosh B + \sinh A \sinh B$$

The sign of the second term flips from $-$ to $+$ because it involves the product of two sinh terms, each contributing an $i$ when analytically continued from the circular case, and $i \cdot i = -1$ accounts for the sign reversal. The derivation from first principles via the exponential:

$$\cosh(A+B) = \frac{e^{A+B} + e^{-(A+B)}}{2}$$

Expanding $e^{A+B} = e^A e^B$ and $e^{-(A+B)} = e^{-A}e^{-B}$:

$$= \frac{e^A e^B + e^{-A}e^{-B}}{2}$$

Adding and subtracting $e^A e^{-B}$ and $e^{-A}e^B$ in the numerator:

$$= \frac{(e^A e^B + e^{-A}e^{-B}) + (e^A e^{-B} + e^{-A}e^B) - (e^A e^{-B} + e^{-A}e^B)}{2}$$

Reorganizing by grouping:

$$= \frac{e^A e^B + e^{-A}e^{-B}}{2} = \frac{(e^A + e^{-A})(e^B + e^{-B})}{4} \cdot 2 - \frac{(e^A - e^{-A})(e^B - e^{-B})}{4} \cdot (-2)$$

More cleanly: use $(e^A + e^{-A})(e^B + e^{-B}) = e^{A+B} + e^{A-B} + e^{-A+B} + e^{-(A+B)}$ and $(e^A - e^{-A})(e^B - e^{-B}) = e^{A+B} - e^{A-B} - e^{-A+B} + e^{-(A+B)}$. Adding:

$$\cosh(A+B) = \frac{(e^A + e^{-A})(e^B + e^{-B}) + (e^A - e^{-A})(e^B - e^{-B})}{4}$$

Wait, let us be precise: $(e^A + e^{-A})(e^B + e^{-B}) + (e^A - e^{-A})(e^B - e^{-B}) = 2e^{A+B} + 2e^{-(A+B)}$. Dividing by 4 gives $(e^{A+B} + e^{-(A+B)})/2 = \cosh(A+B)$. So:

$$\cosh(A+B) = \frac{e^A + e^{-A}}{2}\cdot\frac{e^B + e^{-B}}{2} + \frac{e^A - e^{-A}}{2}\cdot\frac{e^B - e^{-B}}{2} = \cosh A \cosh B + \sinh A \sinh B$$

The derivation is complete, the Osborn sign rule is verified from exponential algebra, and no separate memorization of hyperbolic identities is necessary. Every identity in hyperbolic trigonometry reduces to algebraic manipulation of $e^x$.

The lesson's arc has moved from the elementary but under-appreciated laws of oblique triangles, through the Taylor series foundations that extend sine and cosine analytically to the complex plane, into Euler's formula as an algebraic theorem rather than a numerical wonder, and finally into the hyperbolic functions as the real-axis shadow of the same exponential function evaluated at imaginary arguments. The unifying thread throughout is the exponential function $e^z$ as the master object, with trigonometric and hyperbolic functions as its natural projections onto coordinate axes of the complex plane.
