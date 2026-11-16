# Lesson 6: Analytic Continuation, Riemann Surfaces, and Advanced Structure Theorems

## 1. First-Principles Intuition & Invariants

### The Problem of Multi-Valued Functions and the Limits of a Single Disk

One of the most striking revelations in the development of nineteenth-century analysis is that a holomorphic function defined on a small open disk does not merely *live* in that disk — it reaches outward, propagating its values across the entire connected complex plane (or some natural domain thereof) with an inexorable rigidity that has no analogue in real analysis. A smooth real function can be freely modified outside any compact set while remaining smooth everywhere; a holomorphic function permits no such local surgery. If you know its values on any disk, you know them on every domain to which it can be analytically continued. This rigidity is both the source of the theory's extraordinary power and the origin of its subtlest difficulties.

The difficulty appears immediately when you try to extend familiar functions globally. Consider the complex logarithm. On the right half-plane $\{z : \operatorname{Re}(z) > 0\}$, the function $\log z = \ln|z| + i\arg(z)$ is perfectly well-defined and holomorphic when we restrict $\arg(z) \in (-\pi/2, \pi/2)$. But the moment you attempt to continue this function around the origin — traversing a closed loop that encircles $z = 0$ — you return to your starting point with a value that has shifted by $2\pi i$. The function is not single-valued on $\mathbb{C} \setminus \{0\}$. The complex square root $z^{1/2}$, the inverse trigonometric functions, and the algebraic functions defined by equations like $w^2 = z^3 - z$ all exhibit the same pathology: continuation along a closed loop can return a different branch.

The classical response to this situation, prior to Riemann, was to regard multi-valuedness as a defect to be quarantined — to fix a branch cut, declare the function single-valued on a slit plane, and move on. Riemann's insight, articulated in his 1851 doctoral dissertation, was diametrically opposed: multi-valuedness is not a defect but a signal that the function's natural domain of definition is not the complex plane at all, but a more elaborate geometric object. That object is a **Riemann surface**, and once you work on it, every multi-valued function becomes genuinely single-valued. The apparent pathology dissolves because the topology of the surface accounts for it.

Before we can appreciate Riemann surfaces fully, we must understand the precise analytic mechanism that creates multi-valuedness: analytic continuation along paths, and the conditions under which that continuation is or is not path-independent.

### Analytic Continuation: The Mechanism of Propagation

**Definition (Analytic Continuation Along a Path).** Let $\gamma : [0,1] \to \mathbb{C}$ be a path, and suppose $(f_0, D_0)$ is a function element — a holomorphic function $f_0$ defined on an open disk $D_0$ centered at $\gamma(0)$. A *continuation of $(f_0, D_0)$ along $\gamma$* is a family of function elements $\{(f_t, D_t)\}_{t \in [0,1]}$ such that:

$\gamma(t) \in D_t$ for all $t$, the radii vary continuously with $t$, and whenever $D_s \cap D_t \neq \emptyset$ for $s$ near $t$, we have $f_s \equiv f_t$ on that intersection.

The key point is that each $f_t$ is a holomorphic function on its disk, and adjacent disks in the chain agree on overlaps. The continuation is therefore locally unambiguous at every step. The global question — whether two different paths from $\gamma(0)$ to $\gamma(1)$ produce the same germ at the endpoint — is entirely a question about topology.

**Theorem (Uniqueness of Analytic Continuation Along a Path).** If a continuation of $(f_0, D_0)$ along $\gamma$ exists, it is unique.

*Proof.* Suppose $\{(f_t, D_t)\}$ and $\{(g_t, E_t)\}$ are two continuations of the same function element along $\gamma$. Define $S = \{t \in [0,1] : f_t \equiv g_t \text{ on } D_t \cap E_t\}$. Since $f_0 = g_0$ on $D_0 \cap E_0$, we have $0 \in S$. The set $S$ is open: if $f_s \equiv g_s$ near $\gamma(s)$, then by the overlap condition, the agreement propagates to a neighborhood of $s$ in $[0,1]$. The set $S$ is also closed: if $t_n \to t$ with $t_n \in S$, then $f_{t_n}$ and $g_{t_n}$ agree on disks around $\gamma(t_n)$, and by the continuity of the construction and the identity theorem, $f_t \equiv g_t$ near $\gamma(t)$. Since $[0,1]$ is connected and $S$ is both open and closed in $[0,1]$ with $0 \in S$, we conclude $S = [0,1]$. $\blacksquare$

The theorem guarantees that the continuation process itself is unambiguous, but it says nothing about path-independence. Two different paths from $p$ to $q$ may yield different germs at $q$. This phenomenon — analytically equivalent to the failure of a differential to be exact — is captured by the monodromy theorem.

### The Monodromy Theorem

**Theorem (Monodromy Theorem).** Let $\Omega \subset \mathbb{C}$ be an open set, and let $(f_0, D_0)$ be a function element at $p \in \Omega$ that can be analytically continued along every path in $\Omega$ starting at $p$. If $\gamma_0$ and $\gamma_1$ are two paths in $\Omega$ from $p$ to $q$ that are homotopic relative to their endpoints (i.e., there exists a continuous deformation $H : [0,1]^2 \to \Omega$ with $H(s,0) = \gamma_0(s)$, $H(s,1) = \gamma_1(s)$, $H(0,t) = p$, $H(1,t) = q$ for all $t$), then the analytic continuation of $(f_0, D_0)$ along $\gamma_0$ and along $\gamma_1$ produces the same germ at $q$.

The proof proceeds by applying the uniqueness theorem to the entire homotopy family simultaneously. For each fixed deformation parameter $t \in [0,1]$, the path $s \mapsto H(s,t)$ admits a unique continuation. One then shows that the resulting germ at $q$ varies continuously (and by discreteness of the germ structure, is therefore constant) in $t$.

The corollary is immediate and fundamental: if $\Omega$ is simply connected, then every two paths from $p$ to $q$ are homotopic in $\Omega$, so analytic continuation is path-independent. A function element that continues analytically along every path in a simply connected domain $\Omega$ extends to a globally single-valued holomorphic function on $\Omega$.

This tells us precisely what goes wrong with $\log z$ on $\mathbb{C} \setminus \{0\}$: that domain is not simply connected. Its fundamental group $\pi_1(\mathbb{C} \setminus \{0\}) \cong \mathbb{Z}$ is generated by a loop that winds once around the origin, and that generator acts on the germ of $\log z$ by shifting it by $2\pi i$. The monodromy of the logarithm is the homomorphism $\pi_1(\mathbb{C} \setminus \{0\}) \to \mathbb{Z}$ sending the generator to $1$ — an exact encoding of the topological obstruction in algebraic terms.

### Riemann Surfaces: Resolving Multi-Valuedness Geometrically

Riemann's resolution constructs, for any multi-valued holomorphic function, a surface on which the function is genuinely single-valued. The modern formulation makes this precise through the concept of a one-dimensional complex manifold.

**Definition (Riemann Surface).** A Riemann surface is a connected one-dimensional complex manifold: a Hausdorff topological space $X$ equipped with an atlas of charts $\{(U_\alpha, \phi_\alpha)\}$, where each $\phi_\alpha : U_\alpha \to \mathbb{C}$ is a homeomorphism onto an open subset of $\mathbb{C}$, and all transition maps $\phi_\beta \circ \phi_\alpha^{-1}$ are holomorphic wherever defined.

The simplest examples include the complex plane $\mathbb{C}$ itself, the Riemann sphere $\hat{\mathbb{C}} = \mathbb{C} \cup \{\infty\}$ (with two charts, one omitting $\infty$ and one omitting $0$, with transition map $z \mapsto 1/z$), and any open subset of $\mathbb{C}$. The more interesting examples arise from the analytic continuation process itself.

**The Universal Analytic Continuation Surface.** Given a function element $(f_0, D_0)$, one defines a surface by taking the set of all germs $[f]_p$ obtainable by continuation along all paths from $D_0$, topologized so that a neighborhood of $[f]_p$ consists of all germs of $f$ at points near $p$. This construction, the *Riemann surface of the function element*, is the maximal domain on which the function is well-defined and single-valued. The projection $[f]_p \mapsto p$ is a local homeomorphism from this surface to $\mathbb{C}$.

For $w = \log z$, the resulting Riemann surface is an infinite-sheeted covering of $\mathbb{C} \setminus \{0\}$, homeomorphic to a helix projecting down onto a circle. For $w = z^{1/2}$, the surface has two sheets meeting at $z = 0$: one constructs it concretely by taking two copies of $\mathbb{C}$ slit along the negative real axis and joining them along the slit with opposite orientations. The resulting surface is homeomorphic to $\mathbb{C}$ itself, and $w = z^{1/2}$ is a well-defined holomorphic function on it.

For algebraic functions defined by $P(z, w) = 0$ where $P$ is a polynomial, the Riemann surface is a compact surface (after adding finitely many points at infinity) whose genus $g$ is computable from the degree of $P$ via the Riemann-Hurwitz formula. For the elliptic curve $w^2 = (z - e_1)(z - e_2)(z - e_3)(z - e_4)$ with distinct roots $e_1, e_2, e_3, e_4$, the resulting Riemann surface has genus $g = 1$ and is topologically a torus — the natural domain of the doubly periodic Weierstrass $\wp$-function.

The Riemann sphere $\hat{\mathbb{C}}$ serves as the natural compactification for meromorphic functions on $\mathbb{C}$, turning poles into well-defined points rather than singularities. Every meromorphic function on a compact Riemann surface is a holomorphic map to $\hat{\mathbb{C}}$, and the degree of such a map — the generic number of preimages of any value — is a topological invariant encoding deep algebraic information.

---

## 2. Core Architecture & Mechanics

### The Argument Principle: Zeros, Poles, and Winding Numbers

Having established the geometric context for multi-valued functions, we now develop the analytic machinery that counts zeros and poles. The argument principle is the fundamental tool, connecting local algebraic data (the orders of zeros and poles) to global topological data (winding numbers of image curves).

**Theorem (Argument Principle).** Let $f$ be meromorphic in an open set containing a simple closed positively oriented contour $\gamma$ and its interior $D$, with no zeros or poles on $\gamma$ itself. Then

$$\frac{1}{2\pi i} \oint_\gamma \frac{f'(z)}{f(z)}\, dz = Z - P$$

where $Z$ is the number of zeros of $f$ in $D$ counted with multiplicity, and $P$ is the number of poles counted with multiplicity.

*Proof.* The logarithmic derivative $f'/f$ is meromorphic in $D$. At a zero $z_0$ of order $m$, write $f(z) = (z - z_0)^m g(z)$ where $g$ is holomorphic and nonvanishing near $z_0$. Then

$$\frac{f'(z)}{f(z)} = \frac{m}{z - z_0} + \frac{g'(z)}{g(z)}.$$

The function $g'/g$ is holomorphic near $z_0$, so $f'/f$ has a simple pole at $z_0$ with residue $m$. At a pole $z_0$ of order $p$, write $f(z) = (z - z_0)^{-p} h(z)$ with $h$ holomorphic and nonvanishing, giving

$$\frac{f'(z)}{f(z)} = \frac{-p}{z - z_0} + \frac{h'(z)}{h(z)},$$

so $f'/f$ has a simple pole at $z_0$ with residue $-p$. Applying the residue theorem to $\oint_\gamma f'/f\, dz$ and summing over all zeros and poles in $D$ yields $2\pi i(Z - P)$. $\blacksquare$

The geometric interpretation is equally instructive. As $z$ traverses $\gamma$, the image $f(z)$ traverses a closed curve $\Gamma$ in $\mathbb{C} \setminus \{0\}$. The integral $\frac{1}{2\pi i}\oint_\gamma f'/f\, dz$ is exactly the winding number $n(\Gamma, 0)$ of $\Gamma$ around the origin. Zeros of $f$ contribute positive winding and poles contribute negative winding, with the total winding number recording the signed count $Z - P$. This is the argument principle in its geometric form: the total variation of $\arg f(z)$ as $z$ traverses $\gamma$ equals $2\pi(Z - P)$.

### Rouché's Theorem: Deforming Zeros Under Perturbation

Rouché's theorem is the argument principle's most immediately applicable corollary. It provides a quantitative stability result: if one holomorphic function dominates another on a contour, the total zero count inside the contour is preserved under their combination.

**Theorem (Rouché).** Let $f$ and $g$ be holomorphic on an open set containing the closed disk $\overline{D}$ bounded by a simple closed contour $\gamma$. If $|g(z)| < |f(z)|$ for all $z \in \gamma$, then $f$ and $f + g$ have the same number of zeros inside $\gamma$.

*Proof.* Define the one-parameter family $h_t(z) = f(z) + tg(z)$ for $t \in [0,1]$. On $\gamma$, we have $|h_t(z)| \geq |f(z)| - t|g(z)| > 0$ since $|g(z)| < |f(z)|$. Therefore $h_t$ has no zeros on $\gamma$ for any $t \in [0,1]$. The number of zeros of $h_t$ inside $\gamma$, given by

$$N(t) = \frac{1}{2\pi i} \oint_\gamma \frac{h_t'(z)}{h_t(z)}\, dz,$$

is a continuous function of $t$ (the integrand varies continuously in $t$ since $h_t$ is nonvanishing on $\gamma$). Since $N(t)$ is integer-valued and continuous, it is constant. Thus $N(0) = N(1)$, i.e., $f$ and $f + g$ have the same zero count. $\blacksquare$

As an application, we prove the **Fundamental Theorem of Algebra** via Rouché. Let $p(z) = z^n + a_{n-1}z^{n-1} + \cdots + a_0$. On the circle $|z| = R$ for sufficiently large $R$, take $f(z) = z^n$ and $g(z) = a_{n-1}z^{n-1} + \cdots + a_0$. Then

$$|g(z)| \leq |a_{n-1}|R^{n-1} + \cdots + |a_0| < R^n = |f(z)|$$

for $R$ large enough. By Rouché, $p(z) = f(z) + g(z)$ has the same number of zeros inside $|z| = R$ as $f(z) = z^n$, which has exactly $n$ zeros at the origin. So $p$ has exactly $n$ zeros in $\mathbb{C}$. $\blacksquare$

Rouché's theorem also yields a clean proof of the **Open Mapping Theorem**: if $f$ is non-constant holomorphic at $z_0$, then $f$ maps every sufficiently small neighborhood of $z_0$ onto an open set. Indeed, write $f(z) - f(z_0) = (z-z_0)^m g(z)$ with $g(z_0) \neq 0$ and $m \geq 1$. For any $w_0$ close to $f(z_0)$, the function $(f(z) - w_0) = (f(z) - f(z_0)) + (f(z_0) - w_0)$ satisfies Rouché's condition on a small circle around $z_0$, confirming that $w_0$ is achieved as a value.

### The Structure of Continuation: A Diagram of Chain Relationships

The following diagram depicts the relationship between local function elements and their global propagation via chains of overlapping disks.

```
        γ(0)=p                              γ(1)=q
          │                                   │
    (f₀, D₀)──overlap──(f₁, D₁)──overlap──(f₂, D₂)── ··· ──(fₙ, Dₙ)
          │                │                  │                   │
       germ at p        germ propagated     germ propagated    germ at q
                          along γ            along γ

  Homotopy invariance:
  
       γ₀ ─────────────────────────────► q
       │  ╲                              ▲
       │   H(s,t)  (homotopy in Ω)       │
       │        ╲                        │
       p ─────────────────────────────► q
       γ₁
  
  If Ω simply connected ⟹ [γ₀] = [γ₁] in π₁(Ω) ⟹ same germ at q.
  If Ω = ℂ∖{0}:  π₁ ≅ ℤ,  loop generator acts on log-germ by z ↦ z + 2πi.
```

The chain of overlapping disks forms the analytic continuation. The monodromy action of $\pi_1(\Omega)$ on the fiber of germs above any basepoint encodes all the multi-valuedness of the function.

### Weierstrass Factorization: Prescribing Zeros on $\mathbb{C}$

The classical factorization theorem for polynomials — that a degree-$n$ polynomial with roots $a_1, \ldots, a_n$ factors as $c\prod(z - a_k)$ — has a profound generalization to entire functions. The key difficulty is convergence: an infinite product $\prod(1 - z/a_k)$ need not converge without convergence factors.

**Weierstrass Elementary Factors.** Define, for $p \geq 0$:
$$E_0(z) = 1 - z, \qquad E_p(z) = (1-z)\exp\!\left(z + \frac{z^2}{2} + \cdots + \frac{z^p}{p}\right) \text{ for } p \geq 1.$$

Each $E_p$ is entire, with a single zero at $z = 1$, and satisfies the crucial estimate: for $|z| \leq 1$,
$$|1 - E_p(z)| \leq |z|^{p+1}.$$

*Proof of estimate.* Write $\log E_p(z) = \log(1-z) + z + z^2/2 + \cdots + z^p/p$. Using the Taylor series $\log(1-z) = -\sum_{k=1}^\infty z^k/k$, we get $\log E_p(z) = -\sum_{k=p+1}^\infty z^k/k$. Therefore $|\log E_p(z)| \leq \sum_{k=p+1}^\infty |z|^k/k \leq |z|^{p+1}/(1-|z|)$ for $|z| < 1$. Since $|1 - E_p(z)| \leq |e^{\log E_p(z)} - 1| \leq |\log E_p(z)| e^{|\log E_p(z)|}$ and for $|z| \leq 1/2$ this gives $|1 - E_p(z)| \leq C|z|^{p+1}$, the estimate holds. $\blacksquare$

**Theorem (Weierstrass Factorization Theorem).** Let $\{a_n\}$ be a sequence of nonzero complex numbers with $|a_n| \to \infty$. Then there exist nonneg integers $p_n$ such that the product

$$\prod_{n=1}^\infty E_{p_n}\!\left(\frac{z}{a_n}\right)$$

converges uniformly on compact sets to an entire function whose zero set is exactly $\{a_n\}$ with the prescribed multiplicities. In particular, if $p_n = n-1$ always works (which it does when $\sum |a_n|^{-n} < \infty$), one may take all $p_n$ equal.

For the general case: if $f$ is any entire function with zeros at $\{a_n\}$ (with $a_n \neq 0$ for all $n$) and a zero of order $m$ at the origin, then

$$f(z) = z^m e^{g(z)} \prod_{n=1}^\infty E_{p_n}\!\left(\frac{z}{a_n}\right)$$

for some entire function $g(z)$ and appropriate $p_n$.

*Proof of convergence.* Fix a compact set $K \subset \mathbb{C}$, and choose $R$ such that $K \subset \overline{D}(0, R)$. For all but finitely many $n$, we have $|a_n| > 2R$, so $|z/a_n| \leq 1/2$ for $z \in K$. For these $n$, the estimate $|1 - E_{p_n}(z/a_n)| \leq |z/a_n|^{p_n+1}$ implies

$$\sum_n \left|1 - E_{p_n}\!\left(\frac{z}{a_n}\right)\right| \leq \sum_n \left(\frac{R}{|a_n|}\right)^{p_n+1}.$$

Choosing $p_n = n - 1$ gives terms $(R/|a_n|)^n$, which form a convergent series since $|a_n| \geq 2R$ for large $n$ ensures the ratio is at most $1/2^n$. By the standard criterion that $\sum |1 - u_n| < \infty$ implies $\prod u_n$ converges absolutely and uniformly, the product converges uniformly on $K$. $\blacksquare$

As a canonical example, the Weierstrass factorization of $\sin(\pi z)$ uses the zero set $\{0, \pm 1, \pm 2, \ldots\}$. Since the zeros $\pm n$ satisfy $\sum 1/n^2 < \infty$, one can take all $p_n = 1$, yielding

$$\sin(\pi z) = \pi z \prod_{n=1}^\infty \left(1 - \frac{z^2}{n^2}\right),$$

which is Euler's product formula. The logarithmic derivative of this identity gives the partial fraction expansion

$$\pi \cot(\pi z) = \frac{1}{z} + \sum_{n=1}^\infty \left(\frac{1}{z-n} + \frac{1}{z+n}\right),$$

which is itself an instance of the Mittag-Leffler theorem.

### The Mittag-Leffler Theorem: Prescribing Poles on $\mathbb{C}$

Weierstrass prescribes zeros. Mittag-Leffler prescribes the principal parts at poles, the complementary algebraic datum.

**Theorem (Mittag-Leffler).** Let $\{a_n\}$ be a sequence of distinct complex numbers with $|a_n| \to \infty$, and for each $n$ let $p_n(z)$ be a polynomial without constant term (the prescribed principal part at $a_n$). Then there exists a meromorphic function $f$ on $\mathbb{C}$ whose only poles are the $a_n$, with principal part $p_n(1/(z - a_n))$ at each $a_n$. The general such function is

$$f(z) = \sum_{n=1}^\infty \left[p_n\!\left(\frac{1}{z - a_n}\right) - q_n(z)\right] + g(z),$$

where $q_n$ are polynomials chosen so that the sum converges, and $g$ is any entire function.

*Proof of convergence.* For each $n$, the function $p_n(1/(z-a_n))$ is holomorphic on $D(0, |a_n|)$, so it has a Taylor expansion around the origin. Set $q_n(z)$ to be the partial sum of that Taylor expansion up to degree $N_n$, chosen so that

$$\left|p_n\!\left(\frac{1}{z-a_n}\right) - q_n(z)\right| \leq \frac{1}{2^n}$$

for $|z| \leq |a_n|/2$. Then on any compact set $K$, all but finitely many terms satisfy this bound, and the series converges uniformly on $K$ to a meromorphic function with the prescribed poles. $\blacksquare$

The Mittag-Leffler theorem and the Weierstrass factorization theorem together provide a complete function-theoretic toolkit: one can prescribe poles and principal parts freely (Mittag-Leffler), prescribe zeros freely (Weierstrass), and encode both prescriptions into a single meromorphic function via their combination. This is the analytic counterpart of the Chinese Remainder Theorem for polynomials: local data at isolated points can be freely specified, and the global function assembles them.

---

## 3. High-Performance Optimization & Failure Modes

### Working Practitioners' Toolkit: Applying the Theorems

Understanding these theorems abstractly is one thing; deploying them in computation requires recognizing which theorem is called for and setting up the conditions correctly. We examine the most common points of failure.

**Applying Rouché correctly** requires that $|g(z)| < |f(z)|$ holds strictly on the entire contour — equality at even a single point invalidates the conclusion. When estimating on a circle $|z| = R$, the standard tactic is to split the polynomial $p(z)$ into its dominant term $f$ and the remainder $g$, then bound $|g|$ by a sum of absolute values using the triangle inequality and compare with $|f| = R^n$. The estimate is sharp: if $p(z) = z^n - R^n$ and $\gamma = \{|z| = R\}$, then $|p(z)| = 0$ at points where $z^n = R^n$, so the zeros are on the contour, not inside it. Rouché does not apply.

A subtler failure mode arises when applying Rouché to determine zero locations for functions like $f(z) = e^z - 3z^2$ in a region such as $|z| \leq 1$. The natural split is $f = -3z^2$ and $g = e^z$. On $|z| = 1$, $|{-3z^2}| = 3$ and $|e^z| \leq e^{|\operatorname{Re}(z)|} \leq e < 3$. So Rouché applies: $f + g = e^z - 3z^2$ has the same number of zeros as $-3z^2$ inside $|z| = 1$, namely $2$.

**Applying the argument principle** to count zeros numerically requires evaluating the winding number

$$Z - P = \frac{1}{2\pi} \Delta_\gamma \arg f$$

where $\Delta_\gamma \arg f$ denotes the total change in argument of $f(z)$ as $z$ traverses $\gamma$. In practice, one parametrizes $\gamma(t)$ and tracks $\arg f(\gamma(t))$ carefully to avoid branch cuts in the argument function. The standard computational mistake is to naively compute $\arg f(\gamma(t))$ using a function like $\text{atan2}$ that returns values in $(-\pi, \pi]$ and then sum differences — this introduces spurious jumps of $\pm 2\pi$ at branch cut crossings. The correct method tracks the argument continuously by adding $\pm 2\pi$ whenever a jump occurs, accumulating the total variation.

### Infinite Products: Convergence, Estimation, and Canonical Genus

A subtle issue in the Weierstrass theorem concerns the choice of $p_n$. The theorem guarantees existence for some sequence $p_n$, but the resulting entire function depends on this choice through the exponential factor $e^{g(z)}$. When the zeros satisfy a growth condition $\sum_{n=1}^\infty |a_n|^{-(p+1)} < \infty$ for some fixed integer $p$, one may take all $p_n = p$ uniformly; the resulting product is called the **canonical product of genus $p$**, and the entire function (with $g$ a polynomial of degree at most $p$) has genus at most $\max(p, \deg g)$.

For the Gamma function, the standard definition via Weierstrass is

$$\frac{1}{\Gamma(z)} = z e^{\gamma z} \prod_{n=1}^\infty \left(1 + \frac{z}{n}\right)e^{-z/n},$$

where $\gamma = \lim_{n\to\infty}(1 + 1/2 + \cdots + 1/n - \ln n)$ is the Euler-Mascheroni constant. The zeros of $1/\Gamma(z)$ are at $z = 0, -1, -2, \ldots$, confirming that $\Gamma(z)$ is entire-free of zeros (it has poles at the nonpositive integers). The convergence of this product uses $p_n = 1$ throughout, with the factor $e^{-z/n}$ providing cancellation for the sum $\sum 1/n$, which diverges without it.

**Common failure in Mittag-Leffler applications.** The theorem guarantees that the correcting polynomials $q_n$ can always be chosen to enforce convergence, but it does not prescribe them uniquely. In a concrete computation — say, deriving the partial fraction expansion of $\pi\csc^2(\pi z)$ — one must verify that the natural expansion already converges without correction (which it does, since $1/(z-n)^2 \to 0$ uniformly on compact sets away from the poles). The Mittag-Leffler structure is then:

$$\pi^2 \csc^2(\pi z) = \sum_{n=-\infty}^{\infty} \frac{1}{(z-n)^2},$$

where the doubly infinite sum converges absolutely on compact sets away from the integers. Differentiating the cotangent expansion once and using termwise differentiation (justified by uniform convergence on compacta) gives this identity directly.

### The Riemann Zeta Function: Where the Structural Theorems Converge

No treatment of these analytic tools is complete without acknowledging their convergence in the theory of the Riemann zeta function $\zeta(s)$. This is not a detour — the zeta function is the arena in which analytic continuation, the structure of zeros, Weierstrass products, and functional equations interact with the deepest open problem in mathematics.

For $\operatorname{Re}(s) > 1$, the zeta function is defined by the absolutely convergent Dirichlet series

$$\zeta(s) = \sum_{n=1}^\infty \frac{1}{n^s} = \prod_{p \text{ prime}} \frac{1}{1 - p^{-s}},$$

where the Euler product expansion follows from the unique factorization of integers and the absolute convergence of $\sum n^{-s}$.

**Analytic Continuation of $\zeta(s)$.** The function $\zeta(s)$ as defined above is holomorphic for $\operatorname{Re}(s) > 1$. It extends to a meromorphic function on all of $\mathbb{C}$ with a single simple pole at $s = 1$ with residue $1$. One standard method uses the integral representation

$$\zeta(s) = \frac{1}{\Gamma(s)} \int_0^\infty \frac{t^{s-1}}{e^t - 1}\, dt$$

for $\operatorname{Re}(s) > 1$. The right-hand side can be continued meromorphically by the Hankel contour method, deforming the integration path to avoid the singularity at $t = 0$. The analytic continuation is an instance of Schwarz reflection combined with the monodromy theorem: the continuation exists and is path-independent because the domain of continuation is simply connected away from the poles.

**The Functional Equation and Completed Zeta Function.** Define the completed zeta function

$$\xi(s) = \frac{1}{2}s(s-1)\pi^{-s/2}\Gamma(s/2)\zeta(s).$$

Riemann proved that $\xi(s) = \xi(1-s)$, a functional equation relating values at $s$ and $1-s$ across the critical line $\operatorname{Re}(s) = 1/2$. This symmetry, combined with the analytic continuation, implies that $\zeta(s)$ has zeros at the negative even integers $s = -2, -4, -6, \ldots$ (called the trivial zeros, arising from the poles of $\Gamma(s/2)$) and potentially infinitely many zeros in the critical strip $0 \leq \operatorname{Re}(s) \leq 1$.

**The Weierstrass Product for $\xi$.** Since $\xi(s)$ is an entire function of order $1$, the Weierstrass factorization theorem applies with genus $1$. The nontrivial zeros $\{\rho\}$ of $\zeta(s)$ — which are the zeros of $\xi(s)$ — satisfy $\sum_\rho |\rho|^{-1-\epsilon} < \infty$ for any $\epsilon > 0$, so the canonical product of genus $1$ converges:

$$\xi(s) = \xi(0) \prod_\rho \left(1 - \frac{s}{\rho}\right)e^{s/\rho},$$

where the product runs over all nontrivial zeros. This Weierstrass product, combined with the functional equation $\xi(s) = \xi(1-s)$, implies that the zeros come in pairs $(\rho, 1-\rho)$. The logarithmic derivative of this product yields explicit formulas relating the distribution of primes to the locations of the zeros $\rho$ — the explicit formula of Riemann and von Mangoldt.

**The Riemann Hypothesis** states that all nontrivial zeros satisfy $\operatorname{Re}(\rho) = 1/2$. Equivalently, all zeros of $\xi(s)$ lie on the line $\operatorname{Re}(s) = 1/2$. The argument principle provides the standard method for counting zeros in the critical strip: by applying it to the rectangular contour with vertices at $-\epsilon, 2+\epsilon, 2+\epsilon+iT, -\epsilon+iT$ and using the functional equation, one establishes the **Riemann-von Mangoldt formula**

$$N(T) = \frac{T}{2\pi}\log\frac{T}{2\pi} - \frac{T}{2\pi} + \frac{7}{8} + O\!\left(\frac{\log T}{T}\right)$$

where $N(T)$ counts the number of nontrivial zeros $\rho = \beta + i\gamma$ with $0 < \gamma \leq T$. This formula is entirely a consequence of the argument principle applied to $\xi(s)$ and refined using Stirling's approximation for $\Gamma$. It confirms that the zeros are numerous and that the Weierstrass product is non-degenerate, while the precise location of each zero within the strip $0 < \operatorname{Re}(s) < 1$ remains the governing mystery of analytic number theory.

The arc from function elements and overlapping disks to the Weierstrass product representation of the completed zeta function is not a digression from complex analysis into number theory — it is complex analysis carrying out its own deepest internal logic. Every tool developed in this lesson (analytic continuation along paths, the monodromy theorem to establish single-valuedness of the continuation, the argument principle to count zeros, Rouché to establish zero-free regions, and the Weierstrass factorization to encode the zero set in a product) is deployed in the proof and investigation of the Riemann hypothesis. The hypothesis itself is a statement about the zeros of an entire function, and the entire machinery of this lesson is what gives that statement its precise mathematical content.
