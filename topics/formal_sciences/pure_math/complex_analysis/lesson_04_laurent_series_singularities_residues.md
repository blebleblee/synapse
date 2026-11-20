# Lesson 4: Laurent Series, Isolated Singularities, and the Residue Theorem

## 1. First-Principles Intuition & Invariants

Complex analysis earns its extraordinary power not despite singularities but precisely because of them. When a function fails to be analytic at an isolated point, that failure encodes global information about the function's behavior across the entire plane. The Laurent series is the instrument that makes this encoding legible, and the residue theorem is what transforms that encoded information into a computational engine of remarkable efficiency.

Recall from Cauchy's theorem that a holomorphic function on a simply connected domain integrates to zero around any closed contour within that domain. The moment we puncture the domain — removing a single point where holomorphicity fails — this no longer holds, and the contour integral around the puncture can be nonzero. The magnitude and character of that failure is exactly what the residue measures. Understanding why requires us to first understand what Laurent series are, what they represent geometrically, and how they classify the nature of a singularity.

### From Taylor to Laurent: Expanding in Annular Domains

A Taylor series $\sum_{n=0}^{\infty} a_n (z - z_0)^n$ converges in a disk centered at $z_0$ where the function is holomorphic. But when $z_0$ is itself a point of non-analyticity, the Taylor series breaks down entirely. The natural generalization is to consider not a disk but an **annulus**: the region

$$A(z_0; r, R) = \{ z \in \mathbb{C} : r < |z - z_0| < R \}$$

for $0 \leq r < R \leq \infty$. On this annulus, a function that is holomorphic throughout admits a two-sided power series expansion known as the **Laurent series**.

**Theorem (Laurent Expansion).** Let $f$ be holomorphic on the annulus $A(z_0; r, R)$. Then $f$ admits a unique representation

$$f(z) = \sum_{n=-\infty}^{\infty} a_n (z - z_0)^n$$

converging absolutely and uniformly on every compact sub-annulus $A(z_0; r', R')$ with $r < r' < R' < R$, where the coefficients are given by

$$a_n = \frac{1}{2\pi i} \oint_\gamma \frac{f(\zeta)}{(\zeta - z_0)^{n+1}} \, d\zeta$$

for any positively oriented simple closed contour $\gamma$ lying in $A(z_0; r, R)$ and winding once around $z_0$.

The proof proceeds by separating $f(z)$ into two contributions using the Cauchy integral formula applied to an annular region bounded by an outer circle $C_R$ of radius near $R$ and an inner circle $C_r$ of radius near $r$. For $z$ in the annulus, Cauchy's formula gives

$$f(z) = \frac{1}{2\pi i} \oint_{C_R} \frac{f(\zeta)}{\zeta - z} \, d\zeta - \frac{1}{2\pi i} \oint_{C_r} \frac{f(\zeta)}{\zeta - z} \, d\zeta$$

the negative sign arising from the orientation of the inner contour. The outer integral is handled exactly as in the Taylor series derivation: since $|\zeta - z_0| > |z - z_0|$ on $C_R$, we expand

$$\frac{1}{\zeta - z} = \frac{1}{(\zeta - z_0) - (z - z_0)} = \frac{1}{\zeta - z_0} \cdot \frac{1}{1 - \frac{z-z_0}{\zeta - z_0}} = \sum_{n=0}^{\infty} \frac{(z-z_0)^n}{(\zeta - z_0)^{n+1}}$$

yielding the **analytic part** $\sum_{n=0}^{\infty} a_n (z - z_0)^n$. For the inner integral, since $|z - z_0| > |\zeta - z_0|$ on $C_r$, the roles are reversed and we expand

$$\frac{1}{\zeta - z} = \frac{-1}{(z - z_0) - (\zeta - z_0)} = \frac{-1}{z - z_0} \cdot \frac{1}{1 - \frac{\zeta - z_0}{z - z_0}} = -\sum_{n=0}^{\infty} \frac{(\zeta - z_0)^n}{(z - z_0)^{n+1}}$$

Reindexing with $m = -(n+1)$, so $n = -(m+1)$, the inner integral contributes $\sum_{n=-\infty}^{-1} a_n (z - z_0)^n$, which is the **principal part**. Together they produce the full bilateral Laurent series. Uniqueness follows from the orthogonality of the terms: integrating $\sum a_n (\zeta - z_0)^n$ against $(\zeta - z_0)^{-(m+1)}$ around any contour in the annulus isolates the single coefficient $a_m$.

The Laurent series thus naturally decomposes as

$$f(z) = \underbrace{\sum_{n=-\infty}^{-1} a_n (z - z_0)^n}_{\text{principal part}} + \underbrace{\sum_{n=0}^{\infty} a_n (z - z_0)^n}_{\text{analytic part}}$$

The analytic part is holomorphic on the entire disk $|z - z_0| < R$. The principal part converges for all $z \neq z_0$ (since it is a power series in $1/(z-z_0)$) and encodes the singular behavior near $z_0$.

### Isolated Singularities and Their Classification

A point $z_0$ is an **isolated singularity** of $f$ if $f$ is holomorphic in some punctured disk $0 < |z - z_0| < \varepsilon$ but not at $z_0$ itself. The Laurent expansion on this punctured disk provides the definitive classification.

A **removable singularity** occurs when the principal part is identically zero: all coefficients $a_n = 0$ for $n < 0$. In this case the Laurent series reduces to a Taylor series, and $f$ extends holomorphically to $z_0$ by simply defining $f(z_0) = a_0$. Riemann's theorem on removable singularities provides a clean analytic characterization: $z_0$ is removable if and only if $f$ is bounded in some punctured neighborhood of $z_0$. The function $f(z) = \sin(z)/z$ is the canonical example. Near $z = 0$,

$$\frac{\sin z}{z} = \frac{1}{z}\left(z - \frac{z^3}{3!} + \frac{z^5}{5!} - \cdots\right) = 1 - \frac{z^2}{6} + \frac{z^4}{120} - \cdots$$

The principal part vanishes; the singularity is removable; and extending by $f(0) = 1$ yields an entire function.

A **pole of order $m$** occurs when the principal part is a finite, nonzero sum terminating at $a_{-m}$:

$$f(z) = \frac{a_{-m}}{(z-z_0)^m} + \frac{a_{-m+1}}{(z-z_0)^{m-1}} + \cdots + \frac{a_{-1}}{z - z_0} + a_0 + a_1(z-z_0) + \cdots$$

with $a_{-m} \neq 0$. Equivalently, $z_0$ is a pole of order $m$ if and only if $\lim_{z \to z_0} |f(z)| = \infty$, and more precisely if and only if $(z - z_0)^m f(z)$ has a removable singularity at $z_0$ with nonzero limit $a_{-m}$. A pole of order one is called a **simple pole**. The function $f(z) = 1/(z^2(z-1))$ has a pole of order two at $z = 0$ and a simple pole at $z = 1$.

An **essential singularity** occurs when the principal part is an infinite series: infinitely many coefficients $a_n$ with $n < 0$ are nonzero. The behavior near an essential singularity is catastrophically wild, and this wildness is precisely quantified by the Casorati-Weierstrass theorem.

### The Casorati-Weierstrass Theorem

**Theorem (Casorati-Weierstrass).** If $z_0$ is an essential singularity of $f$, then for every punctured neighborhood $U = \{0 < |z - z_0| < \varepsilon\}$ and every $w_0 \in \mathbb{C}$, every $\delta > 0$ satisfies $f(U) \cap \{|w - w_0| < \delta\} \neq \emptyset$. In other words, the image $f(U)$ is dense in $\mathbb{C}$.

The proof is a clean argument by contradiction. Suppose the conclusion fails: there exists $w_0 \in \mathbb{C}$, $\delta > 0$, and $\varepsilon > 0$ such that $|f(z) - w_0| \geq \delta$ for all $z \in U$. Define

$$g(z) = \frac{1}{f(z) - w_0}$$

on $U$. Then $g$ is holomorphic on $U$ with $|g(z)| \leq 1/\delta$, so $g$ is bounded. By Riemann's removable singularity theorem, $g$ extends holomorphically to $z_0$. If $g(z_0) \neq 0$, then $f(z) = w_0 + 1/g(z)$ extends holomorphically to $z_0$, contradicting the assumption that $z_0$ is a singularity. If $g(z_0) = 0$, then $z_0$ is a zero of $g$ of some finite order $m \geq 1$, which means $f(z) = w_0 + 1/g(z)$ has a pole of order $m$ at $z_0$, again contradicting the assumption of an essential singularity.

The canonical example is $f(z) = e^{1/z}$ at $z = 0$. The Laurent expansion is

$$e^{1/z} = \sum_{n=0}^{\infty} \frac{1}{n! \, z^n} = 1 + \frac{1}{z} + \frac{1}{2z^2} + \frac{1}{6z^3} + \cdots$$

which has infinitely many nonzero principal part coefficients. For any target $w_0 \neq 0$, the equation $e^{1/z} = w_0$ gives $1/z = \log w_0 + 2\pi i k$ for integer $k$, producing solutions $z = 1/(\log w_0 + 2\pi i k)$ accumulating at $0$ as $k \to \infty$. The stronger statement — that $f(U)$ omits at most one value in $\hat{\mathbb{C}}$ — is Picard's great theorem, which lies deeper in the theory and is typically approached through the uniformization theorem or elliptic modular functions.

### The Residue: Definition and Its Geometric Meaning

Among all the Laurent coefficients, the coefficient $a_{-1}$ plays a privileged role. It is called the **residue** of $f$ at $z_0$:

$$\text{Res}(f, z_0) = a_{-1} = \frac{1}{2\pi i} \oint_\gamma f(z) \, dz$$

where $\gamma$ is any positively oriented simple closed contour encircling $z_0$ once and no other singularity. This follows immediately from the coefficient formula with $n = -1$: for $n \neq -1$, the integral $\oint_\gamma (z-z_0)^n \, dz = 0$ because $(z-z_0)^n$ has a holomorphic antiderivative $(z-z_0)^{n+1}/(n+1)$ when $n \neq -1$. The term $(z-z_0)^{-1}$, however, has no single-valued holomorphic antiderivative in a punctured neighborhood of $z_0$ — the logarithm branches — which is precisely why it contributes a nonzero integral. The residue is the obstruction to holomorphic antidifferentiability, and the contour integral around an isolated singularity measures exactly this obstruction.

## 2. Core Architecture & Mechanics

### Computing Residues: A Practitioner's Toolkit

The residue theorem's utility in evaluating integrals rests entirely on the ability to compute residues efficiently without computing the full Laurent expansion. Several formulas serve different structural situations, each derivable from first principles.

**Residue at a simple pole.** If $z_0$ is a simple pole of $f$, then

$$\text{Res}(f, z_0) = \lim_{z \to z_0} (z - z_0) f(z)$$

This follows because the Laurent expansion has the form $f(z) = a_{-1}/(z-z_0) + a_0 + a_1(z-z_0) + \cdots$, so $(z-z_0)f(z) = a_{-1} + a_0(z-z_0) + \cdots \to a_{-1}$ as $z \to z_0$.

**Residue via the quotient formula.** When $f(z) = p(z)/q(z)$ where $p$ and $q$ are holomorphic near $z_0$, $p(z_0) \neq 0$, and $z_0$ is a simple zero of $q$,

$$\text{Res}(f, z_0) = \frac{p(z_0)}{q'(z_0)}$$

The derivation is clean: since $q(z_0) = 0$ and $q'(z_0) \neq 0$, we can write $q(z) = (z - z_0)q'(z_0) + O((z-z_0)^2)$, so

$$\lim_{z \to z_0} (z - z_0) \frac{p(z)}{q(z)} = \lim_{z \to z_0} \frac{(z-z_0) p(z)}{(z-z_0)q'(z_0) + O((z-z_0)^2)} = \frac{p(z_0)}{q'(z_0)}$$

**Residue at a pole of order $m$.** If $z_0$ is a pole of order $m$, the residue is extracted by

$$\text{Res}(f, z_0) = \frac{1}{(m-1)!} \lim_{z \to z_0} \frac{d^{m-1}}{dz^{m-1}} \left[ (z - z_0)^m f(z) \right]$$

The function $(z-z_0)^m f(z)$ has a removable singularity at $z_0$ by assumption, and its Taylor expansion begins $a_{-m} + a_{-(m-1)}(z-z_0) + \cdots + a_{-1}(z-z_0)^{m-1} + \cdots$. The $(m-1)$-st derivative of this at $z_0$ extracts exactly $(m-1)! \cdot a_{-1}$, dividing by $(m-1)!$ yields $a_{-1}$.

To illustrate these formulas concretely, consider computing the residues of

$$f(z) = \frac{z^2}{(z^2 + 1)^2}$$

The denominator $(z^2+1)^2 = (z-i)^2(z+i)^2$ vanishes to second order at $z = i$ and $z = -i$, so both are poles of order two.

At $z = i$: define $g(z) = (z-i)^2 f(z) = z^2/(z+i)^2$. Then

$$\text{Res}(f, i) = g'(i)$$

Differentiating by the quotient rule:

$$g'(z) = \frac{2z(z+i)^2 - z^2 \cdot 2(z+i)}{(z+i)^4} = \frac{2z(z+i) - 2z^2}{(z+i)^3} = \frac{2zi + 2z^2 - 2z^2}{(z+i)^3} = \frac{2zi}{(z+i)^3}$$

Evaluating at $z = i$:

$$g'(i) = \frac{2i \cdot i}{(2i)^3} = \frac{-2}{-8i} = \frac{1}{4i} = -\frac{i}{4}$$

By symmetry (replacing $i$ with $-i$ throughout), one finds $\text{Res}(f, -i) = i/4$.

### The Residue Theorem

**Theorem (Residue Theorem).** Let $U \subseteq \mathbb{C}$ be an open set and $f$ holomorphic on $U$ except at finitely many isolated singularities $z_1, z_2, \ldots, z_k \in U$. Let $\gamma$ be a positively oriented simple closed contour in $U$ whose interior lies in $U$, and suppose none of the $z_j$ lie on $\gamma$. Then

$$\oint_\gamma f(z) \, dz = 2\pi i \sum_{j=1}^{k} n(\gamma, z_j) \cdot \text{Res}(f, z_j)$$

where $n(\gamma, z_j)$ is the winding number of $\gamma$ around $z_j$.

The proof reduces cleanly to Cauchy's theorem once the singularities are isolated. Around each $z_j$ lying inside $\gamma$, draw a small positively oriented circle $C_j$ of radius $\varepsilon_j$ small enough that the disks are mutually disjoint and contained within $\gamma$. Connect $\gamma$ to each $C_j$ and each $C_j$ to the next using pairs of parallel line segments forming thin corridors. The resulting composite contour bounds a region on which $f$ is holomorphic, so by Cauchy's theorem the integral over the composite contour is zero. The corridor contributions cancel in pairs, the integral over $\gamma$ equals the sum of integrals over each small circle $C_j$, and each $\oint_{C_j} f(z) \, dz = 2\pi i \, \text{Res}(f, z_j)$ by definition of the residue. The winding number generalizes this to contours winding multiple times around individual singularities.

The relationship to Cauchy's integral theorem and formula is transparent: Cauchy's theorem is the residue theorem with no singularities inside $\gamma$ (empty sum, integral zero); Cauchy's integral formula $\oint_\gamma f(z)/(z-z_0) \, dz = 2\pi i f(z_0)$ is the residue theorem applied to $g(z) = f(z)/(z-z_0)$ which has a simple pole at $z_0$ with residue $\lim_{z \to z_0}(z-z_0) \cdot f(z)/(z-z_0) = f(z_0)$.

### Contour Architecture for Real Integral Evaluation

The practical power of the residue theorem emerges through the design of contours in $\mathbb{C}$ whose integrals decompose into the target real integral plus manageable remainder terms. The key structural insight is that if the integral over a portion of the contour (typically a large semicircle or arc) vanishes as the radius grows, then the full contour integral equals the real integral alone. This vanishing is quantified by Jordan's lemma.

**Jordan's Lemma.** Let $f$ be meromorphic with $|f(z)| \to 0$ uniformly as $|z| \to \infty$ along the upper half-plane. Then for $\lambda > 0$,

$$\lim_{R \to \infty} \int_{\Gamma_R} f(z) e^{i\lambda z} \, dz = 0$$

where $\Gamma_R$ is the semicircular arc from $R$ to $-R$ through the upper half-plane. The proof uses the estimate $\sin\theta \geq 2\theta/\pi$ for $\theta \in [0, \pi/2]$ to bound the exponential decay of $e^{i\lambda z} = e^{i\lambda R e^{i\theta}} = e^{-\lambda R \sin\theta} e^{i\lambda R \cos\theta}$, giving

$$\left| \int_{\Gamma_R} f(z) e^{i\lambda z} \, dz \right| \leq \pi R \max_{|z|=R} |f(z)| \cdot \frac{1}{\lambda R} \cdot \lambda = \frac{\pi}{\lambda} \max_{|z|=R, \text{Im}z \geq 0} |f(z)|$$

which tends to zero as $R \to \infty$ under the hypothesis.

The standard contour strategies are organized by the form of the integrand:

For rational functions $\int_{-\infty}^{\infty} R(x) \, dx$ where $R(z)$ decays like $1/z^2$ or faster, the **semicircular contour** in the upper half-plane closes the integral. For integrands of the form $R(x) e^{i\lambda x}$ or $R(x) \cos\lambda x$, Jordan's lemma justifies the same closure. For integrands involving $\log z$ or $z^\alpha$ with $\alpha \notin \mathbb{Z}$, the **keyhole contour** wraps around the branch cut on the positive real axis. For integrands of the form $R(\cos\theta, \sin\theta)$ over $[0, 2\pi]$, the **unit circle parametrization** $z = e^{i\theta}$ converts the problem to a contour integral around the unit circle.

```text
SEMICIRCULAR CONTOUR                 KEYHOLE CONTOUR

         Im(z)                              Im(z)
           |                                  |
    Γ_R    |                                  |
   ___     |                                  |
  /   \    |                              __  |
 |     |   |                             /  \ |
 |  *  |   |     Re(z)                  | *  *|------------- Re(z)
 |     |   |                             \__/ |
  \___/    |                                  | branch cut
           |                                  | on (0, +∞)
-R         0         R

  -R ----[real axis]---- R
```

## 3. High-Performance Optimization & Failure Modes

### Systematic Integral Evaluation: Four Worked Examples

The craft of residue-based integration is not merely applying a theorem — it is selecting the right contour geometry, verifying that auxiliary integrals vanish, and tracking branch cuts and indentations with precision. We work through four canonical families with complete derivations.

**Example 1: A rational integral over the real line.**

Evaluate

$$I = \int_{-\infty}^{\infty} \frac{dx}{x^4 + 1}$$

Consider $f(z) = 1/(z^4 + 1)$ and integrate around the standard upper semicircular contour $\gamma = [-R, R] \cup \Gamma_R$. The function $f$ has poles where $z^4 = -1 = e^{i\pi}$, giving $z_k = e^{i(\pi + 2\pi k)/4}$ for $k = 0, 1, 2, 3$. The poles in the upper half-plane (where $\text{Im}(z) > 0$) are $z_0 = e^{i\pi/4} = (1+i)/\sqrt{2}$ and $z_1 = e^{i3\pi/4} = (-1+i)/\sqrt{2}$.

Since all poles are simple, we use the quotient formula with $p(z) = 1$ and $q(z) = z^4 + 1$, $q'(z) = 4z^3$:

$$\text{Res}(f, z_0) = \frac{1}{4z_0^3} = \frac{1}{4 e^{i3\pi/4}} = \frac{e^{-i3\pi/4}}{4}$$

$$\text{Res}(f, z_1) = \frac{1}{4z_1^3} = \frac{1}{4 e^{i9\pi/4}} = \frac{e^{-i9\pi/4}}{4} = \frac{e^{-i\pi/4}}{4}$$

The sum of residues is

$$\text{Res}(f, z_0) + \text{Res}(f, z_1) = \frac{1}{4}\left(e^{-i3\pi/4} + e^{-i\pi/4}\right) = \frac{1}{4}\left(-\frac{1}{\sqrt{2}} - \frac{i}{\sqrt{2}} + \frac{1}{\sqrt{2}} - \frac{i}{\sqrt{2}}\right) = \frac{1}{4} \cdot \left(-\frac{2i}{\sqrt{2}}\right) = -\frac{i}{2\sqrt{2}}$$

By the residue theorem and the vanishing of the semicircular integral (since $|f(z)| \leq 1/(R^4 - 1) \to 0$ on $\Gamma_R$):

$$I = 2\pi i \cdot \left(-\frac{i}{2\sqrt{2}}\right) = \frac{2\pi i \cdot i}{-2\sqrt{2}} = \frac{\pi}{\sqrt{2}} = \frac{\pi\sqrt{2}}{2}$$

**Example 2: An oscillatory integral via Jordan's lemma.**

Evaluate

$$I = \int_{-\infty}^{\infty} \frac{x \sin x}{x^2 + a^2} \, dx, \quad a > 0$$

Write this as the imaginary part of $\int_{-\infty}^{\infty} x e^{ix}/(x^2 + a^2) \, dx$. Set $f(z) = z e^{iz}/(z^2 + a^2) = z e^{iz}/((z-ia)(z+ia))$. The only pole in the upper half-plane is $z = ia$ (a simple pole). Jordan's lemma applies since $|z/(z^2 + a^2)| \to 0$ uniformly on $\Gamma_R$.

$$\text{Res}(f, ia) = \lim_{z \to ia} (z - ia) \cdot \frac{z e^{iz}}{(z-ia)(z+ia)} = \frac{ia \cdot e^{i(ia)}}{2ia} = \frac{e^{-a}}{2}$$

Thus $\int_{-\infty}^{\infty} \frac{x e^{ix}}{x^2 + a^2} \, dx = 2\pi i \cdot \frac{e^{-a}}{2} = \pi i e^{-a}$, and taking the imaginary part:

$$I = \pi e^{-a}$$

**Example 3: A branch cut integral via the keyhole contour.**

Evaluate

$$I = \int_0^{\infty} \frac{x^{\alpha - 1}}{1 + x} \, dx, \quad 0 < \alpha < 1$$

This is a standard Beta function integral equal to $\pi / \sin(\pi \alpha)$, but proving it via residues reveals the keyhole technique. Define $z^{\alpha-1} = e^{(\alpha-1)\log z}$ using the principal branch $\log z = \ln|z| + i\arg z$ with $\arg z \in [0, 2\pi)$. The branch cut lies along the positive real axis. The keyhole contour $\gamma$ consists of: a segment $L^+$ just above the positive real axis from $\varepsilon$ to $R$; a large circle $C_R$ of radius $R$ traversed counterclockwise; a segment $L^-$ just below the positive real axis from $R$ to $\varepsilon$; and a small circle $C_\varepsilon$ of radius $\varepsilon$ traversed clockwise.

On $L^+$: $z = x$ with $\arg z = 0$, so $z^{\alpha - 1} = x^{\alpha-1}$. On $L^-$: $z = x e^{2\pi i}$ with $\arg z = 2\pi$, so $z^{\alpha - 1} = x^{\alpha - 1} e^{2\pi i(\alpha-1)}$. The integrals over $C_R$ and $C_\varepsilon$ vanish as $R \to \infty$ and $\varepsilon \to 0$ (verified by estimating $|z^{\alpha-1}/(1+z)|$ on each arc and using $0 < \alpha < 1$). The contour encloses one singularity, the simple pole at $z = -1 = e^{i\pi}$:

$$\text{Res}\left(\frac{z^{\alpha-1}}{1+z}, -1\right) = e^{i\pi(\alpha-1)} = -e^{i\pi\alpha}$$

The residue theorem gives

$$\int_0^\infty \frac{x^{\alpha-1}}{1+x}dx + e^{2\pi i(\alpha-1)} \int_\infty^0 \frac{x^{\alpha-1}}{1+x} dx = 2\pi i \cdot (-e^{i\pi\alpha})$$

The second integral flips orientation:

$$I \left(1 - e^{2\pi i(\alpha - 1)}\right) = -2\pi i e^{i\pi\alpha}$$

Since $e^{2\pi i(\alpha - 1)} = e^{2\pi i\alpha}$:

$$I \left(1 - e^{2\pi i\alpha}\right) = -2\pi i e^{i\pi\alpha}$$

Dividing:

$$I = \frac{-2\pi i e^{i\pi\alpha}}{1 - e^{2\pi i\alpha}} = \frac{2\pi i e^{i\pi\alpha}}{e^{2\pi i\alpha} - 1} = \frac{2\pi i}{e^{i\pi\alpha} - e^{-i\pi\alpha}} = \frac{2\pi i}{2i \sin(\pi\alpha)} = \frac{\pi}{\sin(\pi\alpha)}$$

**Example 4: A trigonometric integral via unit circle parametrization.**

Evaluate

$$I = \int_0^{2\pi} \frac{d\theta}{a + b\cos\theta}, \quad a > |b| > 0$$

Substitute $z = e^{i\theta}$, so $d\theta = dz/(iz)$ and $\cos\theta = (z + z^{-1})/2$. The integral becomes

$$I = \oint_{|z|=1} \frac{1}{a + b(z + z^{-1})/2} \cdot \frac{dz}{iz} = \oint_{|z|=1} \frac{2 \, dz}{i(2az + bz^2 + b)} = \oint_{|z|=1} \frac{2 \, dz}{ib(z^2 + 2(a/b)z + 1)}$$

The roots of $z^2 + 2(a/b)z + 1 = 0$ are $z_\pm = -(a/b) \pm \sqrt{(a/b)^2 - 1}$. Since $a > |b|$, both roots are real and satisfy $z_+ z_- = 1$, so one root lies inside and one outside the unit circle. Specifically, $|z_-| = (a/b) + \sqrt{(a/b)^2 - 1} > 1$ and $|z_+| = 1/|z_-| < 1$. The residue at $z_+$ is

$$\text{Res} = \frac{2/(ib)}{2z_+ + 2(a/b)} = \frac{2/(ib)}{2(z_+ - z_-)} = \frac{1}{ib(z_+ - z_-)}$$

The difference $z_+ - z_- = -2\sqrt{(a/b)^2 - 1} = -2\sqrt{a^2 - b^2}/b$, so

$$\text{Res} = \frac{1}{ib \cdot (-2\sqrt{a^2-b^2}/b)} = \frac{-1}{2i\sqrt{a^2-b^2}}$$

Applying the residue theorem:

$$I = 2\pi i \cdot \frac{-1}{2i\sqrt{a^2-b^2}} = \frac{2\pi}{\sqrt{a^2 - b^2}}$$

### Failure Modes and Edge Cases

Several pathologies arise in practice that require careful treatment.

**Poles on the contour of integration.** When the integrand has a simple pole on the real axis (or on the contour itself), the standard integral is interpreted as a Cauchy principal value and the contour must be indented with a small semicircle of radius $\varepsilon$ around the pole. For a simple pole at $z_0$ on the real axis, the indented semicircular arc $\gamma_\varepsilon$ of radius $\varepsilon$ traversed counterclockwise through angle $\pi$ contributes

$$\lim_{\varepsilon \to 0} \int_{\gamma_\varepsilon} f(z) \, dz = \pi i \cdot \text{Res}(f, z_0)$$

a factor of $\pi i$ rather than $2\pi i$, since only a half-winding passes around the pole. This is the **indentation lemma**, and its failure to account for the factor of $1/2$ is a common computational error.

**Logarithmic branch cut alignment.** When using the keyhole contour, the branch cut of $\log z$ must be chosen to avoid all singularities of the integrand. If $f(z)$ has poles on the positive real axis, the branch cut should be rotated (e.g., placed on the negative real axis using $\arg z \in (-\pi, \pi]$), and the keyhole wraps around the negative axis instead. Misaligning the branch cut with singularities produces contradictions in the residue count.

**Insufficient decay at infinity.** Jordan's lemma requires $|f(z)| \to 0$ uniformly on $\Gamma_R$. For rational $R(z)$, this demands $\deg q \geq \deg p + 2$ for the absolute integral $\int R(x) \, dx$ and $\deg q \geq \deg p + 1$ for oscillatory integrals $\int R(x) e^{i\lambda x} \, dx$. When only $\deg q = \deg p + 1$, the residue theorem still applies but convergence of the real integral must be verified separately, typically as a principal value.

**Multiple singularities inside the contour.** It is entirely correct and often necessary to include multiple poles inside a single contour. The residue theorem sums all contributions linearly, and the principal value of each residue must be computed at its respective pole without confusion between them. A common error when poles cluster near the real axis is to conflate the residue computation at $z_0$ with the nearby behavior at an adjacent pole $z_1$; each must be computed by the appropriate formula using only the local behavior at that point.

**Essential singularities inside contours.** The residue theorem applies equally to essential singularities: the residue $a_{-1}$ exists and is well-defined regardless of the singularity type, and the theorem makes no distinction. However, computing $a_{-1}$ at an essential singularity requires extracting the coefficient of $(z-z_0)^{-1}$ from the full Laurent expansion, which cannot be done by the simple pole formulas. For $e^{1/z}$ at $z = 0$, the expansion $\sum_{n=0}^{\infty} 1/(n! z^n)$ gives $\text{Res}(e^{1/z}, 0) = a_{-1} = 1/1! = 1$.

The deepest invariant running through all of these computations is that residues are, at their core, topological. The winding number $n(\gamma, z_j)$ is a topological invariant of the homotopy class of $\gamma$ in $\mathbb{C} \setminus \{z_1, \ldots, z_k\}$, and the residue theorem states that the contour integral depends only on this topological datum together with the local analytic datum at each singularity. This is a shadow of the broader de Rham and sheaf-cohomological perspective on complex integration, in which the residue theorem is an instance of Stokes' theorem applied to the sheaf of holomorphic differential forms — a vantage point that opens directly into several complex variables and algebraic geometry. For now, however, the practitioner's toolkit assembled in this lesson — Laurent expansion, singularity classification, residue computation, and contour design — constitutes a self-contained engine capable of evaluating vast classes of integrals that resist every real-variable technique.
