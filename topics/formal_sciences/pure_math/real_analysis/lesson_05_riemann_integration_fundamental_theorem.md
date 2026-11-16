# Lesson 5: Riemann Integration — Darboux Sums, Integrability, Fundamental Theorem

## 1. First-Principles Intuition & Invariants

The problem of quadrature—measuring the area enclosed between a curve and the axis—is among the oldest in mathematics. Archimedes attacked it with his method of exhaustion, inscribing and circumscribing polygons around curvilinear regions and arguing that the gap could be driven below any threshold. This geometric instinct persisted through Newton and Leibniz, who discovered the profound connection between differentiation and accumulation that we now call the Fundamental Theorem of Calculus. Yet the logical foundations of the integral remained geometric and intuitive until the nineteenth century, when Cauchy began the arithmetization of analysis and Riemann gave the first rigorous, purely algebraic definition of the integral for a broad class of functions. Darboux subsequently reformulated Riemann's construction using upper and lower sums, yielding a cleaner framework that separates the definition of integrability from the mechanics of evaluation. We develop that framework here.

The architectural idea is deceptively simple. Given a bounded function $f:[a,b]\to\mathbb{R}$, we partition the interval $[a,b]$ into finitely many subintervals. On each subinterval we approximate $f$ from above by its supremum and from below by its infimum, forming two families of rectangular approximations to the area. The function is integrable precisely when the gap between the overestimate and the underestimate can be made arbitrarily small by choosing sufficiently fine partitions. The integral is then the unique number trapped between every lower sum and every upper sum.

A **partition** $P$ of $[a,b]$ is a finite ordered set of points $P=\{x_0,x_1,\dots,x_n\}$ with $a=x_0<x_1<\cdots<x_n=b$. The **norm** (or **mesh**) of $P$ is the length of its longest subinterval:

$$\|P\|=\max_{1\le i\le n}(x_i-x_{i-1}).$$

A partition $Q$ is a **refinement** of $P$, written $Q\supseteq P$, if every point of $P$ belongs to $Q$. Given a bounded function $f$ and a partition $P$, on each subinterval $[x_{i-1},x_i]$ we set:

$$M_i(f)=\sup\{f(x):x\in[x_{i-1},x_i]\},\qquad m_i(f)=\inf\{f(x):x\in[x_{i-1},x_i]\},$$

and $\Delta x_i=x_i-x_{i-1}$. The **upper** and **lower Darboux sums** are:

$$U(P,f)=\sum_{i=1}^{n}M_i(f)\,\Delta x_i,\qquad L(P,f)=\sum_{i=1}^{n}m_i(f)\,\Delta x_i.$$

Geometrically, $U(P,f)$ is the total area of the outer rectangles that overestimate the region beneath $f$, and $L(P,f)$ is the total area of the inner rectangles that underestimate it. Since $m_i(f)\le M_i(f)$ for every $i$, we always have $L(P,f)\le U(P,f)$.

The first structural observation is that refinement improves the approximation: adding points to a partition can only decrease upper sums and increase lower sums.

**Lemma (Refinement).** *If $Q\supseteq P$, then $L(P,f)\le L(Q,f)\le U(Q,f)\le U(P,f)$.*

*Proof.* It suffices to prove the result when $Q$ is obtained from $P$ by adding a single point $z\in(x_{k-1},x_k)$; the general case follows by induction. All terms of the upper sum are unchanged except the $k$-th, which becomes:

$$M_k'\,(z-x_{k-1})+M_k''\,(x_k-z),$$

where $M_k'=\sup\{f(x):x\in[x_{k-1},z]\}$ and $M_k''=\sup\{f(x):x\in[z,x_k]\}$. Since $[x_{k-1},z]\subseteq[x_{k-1},x_k]$, we have $M_k'\le M_k$, and similarly $M_k''\le M_k$. Therefore:

$$M_k'(z-x_{k-1})+M_k''(x_k-z)\le M_k(z-x_{k-1})+M_k(x_k-z)=M_k\,\Delta x_k,$$

which gives $U(Q,f)\le U(P,f)$. The argument for $L(P,f)\le L(Q,f)$ is identical with infima replacing suprema. $\blacksquare$

This immediately yields a cross-partition inequality of fundamental importance: no lower sum can exceed any upper sum, even when the two sums arise from different partitions.

**Lemma.** *For any partitions $P$ and $Q$, $L(P,f)\le U(Q,f)$.*

*Proof.* The common refinement $P\cup Q$ satisfies $L(P,f)\le L(P\cup Q,f)\le U(P\cup Q,f)\le U(Q,f)$ by two applications of the refinement lemma. $\blacksquare$

This inequality tells us that the set of all lower sums is bounded above (by any upper sum) and the set of all upper sums is bounded below (by any lower sum). This motivates the definitions of the **upper and lower Darboux integrals**:

$$\overline{\int_a^b}f=\inf_{P}\,U(P,f),\qquad \underline{\int_a^b}f=\sup_{P}\,L(P,f).$$

By the cross-partition inequality, $\underline{\int_a^b}f\le\overline{\int_a^b}f$ always holds. When equality holds, we say $f$ is **Riemann integrable** on $[a,b]$, and the common value is denoted $\int_a^b f$.

This definition, while conceptually clean, requires computing suprema and infima over all partitions—a formidable task in practice. The **Darboux Integrability Criterion** provides a single, checkable condition:

**Theorem (Darboux's Criterion).** *A bounded function $f:[a,b]\to\mathbb{R}$ is Riemann integrable if and only if for every $\varepsilon>0$ there exists a partition $P$ such that*

$$U(P,f)-L(P,f)<\varepsilon.$$

*Proof.* $(\Rightarrow)$ Suppose $f$ is integrable with $\int_a^b f=I$. For any $\varepsilon>0$, there exist partitions $P_1$ and $P_2$ such that $U(P_1,f)<I+\varepsilon/2$ and $L(P_2,f)>I-\varepsilon/2$. Let $P=P_1\cup P_2$. By the refinement lemma, $L(P_2,f)\le L(P,f)\le U(P,f)\le U(P_1,f)$, so:

$$U(P,f)-L(P,f)\le U(P_1,f)-L(P_2,f)<\left(I+\frac{\varepsilon}{2}\right)-\left(I-\frac{\varepsilon}{2}\right)=\varepsilon.$$

$(\Leftarrow)$ Suppose for every $\varepsilon>0$ there exists $P$ with $U(P,f)-L(P,f)<\varepsilon$. Since $L(P,f)\le\underline{\int_a^b}f\le\overline{\int_a^b}f\le U(P,f)$, we have:

$$0\le\overline{\int_a^b}f-\underline{\int_a^b}f\le U(P,f)-L(P,f)<\varepsilon.$$

As $\varepsilon$ is arbitrary, the upper and lower integrals coincide, so $f$ is integrable. $\blacksquare$

The quantity $U(P,f)-L(P,f)=\sum_{i=1}^n(M_i-m_i)\,\Delta x_i$ measures the total oscillation of $f$ weighted by interval lengths across the partition. Darboux's criterion says that $f$ is integrable precisely when this total oscillation can be made arbitrarily small—when, in a quantifiable sense, $f$ is nearly constant on the subintervals of a sufficiently fine partition.

Darboux's formulation is equivalent to Riemann's original definition via tagged partitions. A **tagged partition** consists of a partition $P=\{x_0,\dots,x_n\}$ together with sample points (tags) $t_i\in[x_{i-1},x_i]$, and the associated **Riemann sum** is $S(P,f,\{t_i\})=\sum_{i=1}^n f(t_i)\,\Delta x_i$. Since $m_i\le f(t_i)\le M_i$ for every tag, every Riemann sum is squeezed: $L(P,f)\le S(P,f,\{t_i\})\le U(P,f)$. The equivalence rests on the following theorem, which ensures that Darboux integrability forces all Riemann sums with sufficiently fine mesh to converge to the integral, regardless of tag choice.

**Theorem (Equivalence of Riemann and Darboux Integrability).** *Let $f:[a,b]\to\mathbb{R}$ be bounded. The following are equivalent:*

1. *$f$ is Darboux integrable with $\int_a^b f=I$.*
2. *For every $\varepsilon>0$ there exists $\delta>0$ such that for every partition $P$ with $\|P\|<\delta$ and every choice of tags, $|S(P,f,\{t_i\})-I|<\varepsilon$.*

*Proof.* We prove $(1)\Rightarrow(2)$; the converse follows since Riemann sums are squeezed by Darboux sums. Suppose $f$ is integrable with integral $I$. By Darboux's criterion, for $\varepsilon>0$ there exists a partition $P_0=\{y_0,\dots,y_m\}$ with $U(P_0,f)-L(P_0,f)<\varepsilon/2$. Let $M=\sup_{[a,b]}|f|$ and let $N=m-1$ be the number of interior points of $P_0$. If $M=0$ or $N=0$, the result is trivial; otherwise, set $\delta=\varepsilon/(8MN)$.

Let $P$ be any partition with $\|P\|<\delta$, and set $Q=P\cup P_0$. By the refinement lemma, $U(Q,f)-L(Q,f)\le U(P_0,f)-L(P_0,f)<\varepsilon/2$. We now bound the gap $U(P,f)-U(Q,f)$. Going from $P$ to $Q$ adds the $N$ interior points of $P_0$. Each added point $z$ falls in some subinterval $[x_{i-1},x_i]$ of $P$ with $\Delta x_i<\delta$. As computed in the refinement lemma, the decrease in the upper sum from splitting this interval is:

$$(M_i-M_i')(z-x_{i-1})+(M_i-M_i'')(x_i-z)\le 2M\,\Delta x_i<2M\delta.$$

Summing over all $N$ added points: $U(P,f)-U(Q,f)<2MN\delta$. Similarly, $L(Q,f)-L(P,f)<2MN\delta$. Therefore:

$$U(P,f)-L(P,f)=\bigl[U(P,f)-U(Q,f)\bigr]+\bigl[U(Q,f)-L(Q,f)\bigr]+\bigl[L(Q,f)-L(P,f)\bigr]$$

$$<2MN\delta+\frac{\varepsilon}{2}+2MN\delta=4MN\delta+\frac{\varepsilon}{2}=\frac{\varepsilon}{2}+\frac{\varepsilon}{2}=\varepsilon.$$

Since $L(P,f)\le S(P,f,\{t_i\})\le U(P,f)$ and $L(P,f)\le I\le U(P,f)$ for any tags, we conclude $|S(P,f,\{t_i\})-I|\le U(P,f)-L(P,f)<\varepsilon$. $\blacksquare$

This theorem is the linchpin connecting the Darboux framework (technically convenient for proving integrability) with the Riemann framework (computationally natural for evaluating integrals as limits of sums). We move freely between the two throughout this lesson.

A conceptually powerful reformulation uses the notion of **oscillation**. For a bounded function $f$ on an interval $I$, the oscillation is $\omega(f,I)=\sup_I f-\inf_I f$. At a point $x$, the oscillation of $f$ is $\omega_f(x)=\inf_{\delta>0}\omega\bigl(f,(x-\delta,x+\delta)\bigr)$. The function $f$ is continuous at $x$ if and only if $\omega_f(x)=0$, and the discontinuity set decomposes as $D_f=\{x:\omega_f(x)>0\}=\bigcup_{n=1}^\infty\{x:\omega_f(x)\ge 1/n\}$. Darboux's criterion can be restated: $f$ is integrable if and only if for every $\varepsilon>0$ there exists a partition $P$ with $\sum_{i=1}^n\omega\bigl(f,[x_{i-1},x_i]\bigr)\,\Delta x_i<\varepsilon$. This decomposition of the discontinuity set into a countable union of controlled-oscillation sets is the key to Lebesgue's complete characterization of integrability, which we prove in the next section.

```
┌─────────────────────────────────────────────────────────────┐
│            Darboux Integrability Framework                   │
│                                                             │
│  Partition P = {x₀, x₁, ..., xₙ}                            │
│                                                             │
│  U(P,f) = Σ Mᵢ Δxᵢ  ←── overestimate (outer rectangles)    │
│                                                             │
│  L(P,f) = Σ mᵢ Δxᵢ  ←── underestimate (inner rectangles)    │
│                                                             │
│  Gap: U(P,f) - L(P,f) = Σ (Mᵢ - mᵢ) Δxᵢ = total oscillation │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Darboux Criterion:                                   │   │
│  │  f integrable ⟺ ∀ε>0 ∃P: U(P,f) - L(P,f) < ε      │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  Refinement P ⊆ Q:                                          │
│    L(P,f) ≤ L(Q,f) ≤ U(Q,f) ≤ U(P,f)                       │
│                                                             │
│  Any two partitions P, Q:                                    │
│    L(P,f) ≤ U(Q,f)                                         │
│                                                             │
│  Lower integral:  ∫̲f = sup_P L(P,f)                        │
│  Upper integral:  ∫̄f = inf_P U(P,f)                        │
│  f integrable ⟺ ∫̲f = ∫̄f = ∫f                             │
└─────────────────────────────────────────────────────────────┘
```

## 2. Core Architecture & Mechanics

### 2.1 Classes of Integrable Functions

With the Darboux criterion in hand, we can identify broad classes of integrable functions by constructing explicit partitions that drive the total oscillation to zero. The two most important classes—continuous and monotone functions—follow from distinct but equally instructive arguments, each illuminating a different mechanism by which oscillation can be controlled.

**Theorem (Continuous functions are integrable).** *If $f$ is continuous on $[a,b]$, then $f$ is Riemann integrable on $[a,b]$.*

*Proof.* Since $[a,b]$ is compact and $f$ is continuous, $f$ is bounded by the Extreme Value Theorem and uniformly continuous by the Heine–Borel theorem. Given $\varepsilon>0$, uniform continuity provides $\delta>0$ such that $|x-y|<\delta$ implies $|f(x)-f(y)|<\varepsilon/(b-a)$ for all $x,y\in[a,b]$. Choose any partition $P$ with $\|P\|<\delta$. On each subinterval $[x_{i-1},x_i]$, the Extreme Value Theorem guarantees that $f$ attains its supremum $M_i$ at some $s_i\in[x_{i-1},x_i]$ and its infimum $m_i$ at some $t_i\in[x_{i-1},x_i]$. Since $|s_i-t_i|\le\Delta x_i<\delta$, uniform continuity gives $M_i-m_i=f(s_i)-f(t_i)<\varepsilon/(b-a)$. Therefore:

$$U(P,f)-L(P,f)=\sum_{i=1}^n(M_i-m_i)\,\Delta x_i<\frac{\varepsilon}{b-a}\sum_{i=1}^n\Delta x_i=\varepsilon.$$

By Darboux's criterion, $f$ is integrable. $\blacksquare$

The mechanism is clear: uniform continuity forces $f$ to vary by less than any prescribed threshold on sufficiently short intervals, so a partition with small enough mesh controls oscillation on every subinterval simultaneously.

**Theorem (Monotone functions are integrable).** *If $f$ is monotone on $[a,b]$, then $f$ is Riemann integrable on $[a,b]$.*

*Proof.* We treat the case where $f$ is increasing; the decreasing case follows by applying the result to $-f$. Since $f$ is increasing, $f(a)\le f(x)\le f(b)$ for all $x\in[a,b]$, so $f$ is bounded. Given $\varepsilon>0$, choose $n$ large enough that $(f(b)-f(a))(b-a)/n<\varepsilon$. Let $P$ be the uniform partition with $\Delta x_i=(b-a)/n$ for all $i$. Since $f$ is increasing, $M_i=f(x_i)$ and $m_i=f(x_{i-1})$, so $M_i-m_i=f(x_i)-f(x_{i-1})$. The total oscillation is:

$$U(P,f)-L(P,f)=\sum_{i=1}^n\bigl(f(x_i)-f(x_{i-1})\bigr)\,\frac{b-a}{n}=\frac{b-a}{n}\bigl(f(b)-f(a)\bigr)<\varepsilon,$$

where the sum telescopes to $f(b)-f(a)$. By Darboux's criterion, $f$ is integrable. $\blacksquare$

The contrast with the continuous case is instructive. A monotone function can have jump discontinuities—potentially many—but the total variation $f(b)-f(a)$ is fixed. The telescoping sum distributes this variation across $n$ equal subintervals, and the per-interval contribution $(f(b)-f(a))/n$ vanishes as $n\to\infty$, regardless of where the jumps occur.

These two classes cover most functions encountered in practice, but they do not exhaust the integrable functions. A function can have infinitely many discontinuities and still be integrable, provided those discontinuities are sparse in a precise sense. This brings us to Lebesgue's complete characterization.

**Definition.** A set $A\subseteq\mathbb{R}$ has **(Lebesgue) measure zero** if for every $\varepsilon>0$, there exists a countable collection of open intervals $\{(a_k,b_k)\}_{k=1}^\infty$ such that $A\subseteq\bigcup_{k=1}^\infty(a_k,b_k)$ and $\sum_{k=1}^\infty(b_k-a_k)<\varepsilon$.

Any countable set has measure zero: cover the $k$-th point with an interval of length $\varepsilon/2^k$. The Cantor set, despite being uncountable, also has measure zero. A countable union of measure-zero sets has measure zero, as the coverings can be combined with geometrically decaying lengths.

**Theorem (Lebesgue's Integrability Criterion).** *A bounded function $f:[a,b]\to\mathbb{R}$ is Riemann integrable if and only if the set of points at which $f$ is discontinuous has measure zero.*

*Proof.* $(\Rightarrow)$ Suppose $f$ is integrable. For each $n\in\mathbb{N}$, define $D_n=\{x\in[a,b]:\omega_f(x)\ge 1/n\}$. The discontinuity set is $D_f=\bigcup_{n=1}^\infty D_n$. We show each $D_n$ has measure zero; since countable unions of measure-zero sets have measure zero, this suffices.

Fix $n$ and let $\varepsilon>0$. By Darboux's criterion, there exists a partition $P=\{x_0,\dots,x_N\}$ with $U(P,f)-L(P,f)<\varepsilon/(2n)$. Let $\mathcal{S}$ be the set of indices $i$ for which $D_n\cap(x_{i-1},x_i)\ne\varnothing$. For each $i\in\mathcal{S}$, the oscillation of $f$ on $[x_{i-1},x_i]$ is at least $1/n$ (since $\omega_f(x)\ge 1/n$ for some interior point $x$, and the oscillation on the larger interval dominates). Therefore:

$$\frac{1}{n}\sum_{i\in\mathcal{S}}\Delta x_i\le\sum_{i\in\mathcal{S}}(M_i-m_i)\,\Delta x_i\le\sum_{i=1}^N(M_i-m_i)\,\Delta x_i<\frac{\varepsilon}{2n}.$$

This gives $\sum_{i\in\mathcal{S}}\Delta x_i<\varepsilon/2$. The points of $D_n$ lying in the interiors of subintervals indexed by $\mathcal{S}$ are covered by these subintervals, whose total length is less than $\varepsilon/2$. The remaining points of $D_n$ lie at the partition points $\{x_0,\dots,x_N\}$; cover each by an open interval of length $\varepsilon/(2(N+1))$, contributing total length at most $\varepsilon/2$. The total covering length is less than $\varepsilon$, so $D_n$ has measure zero.

$(\Leftarrow)$ Suppose $D_f$ has measure zero. Let $\varepsilon>0$ and let $M=\sup_{[a,b]}|f|$. If $M=0$, then $f\equiv 0$ is trivially integrable, so assume $M>0$. Set $\alpha=\varepsilon/(2(b-a))$ and $\eta=\varepsilon/(4M)$.

The set $D_\alpha=\{x\in[a,b]:\omega_f(x)\ge\alpha\}$ is a subset of $D_f$, hence has measure zero. There exist finitely many open intervals $G_1,\dots,G_p$ covering $D_\alpha$ with total length $\sum|G_j|<\eta$. (We use finitely many by extracting a finite subcover from the countable one, adjusting the total length bound.)

Let $G=\bigcup_{j=1}^p G_j$ and $K=[a,b]\setminus G$. The set $K$ is closed and bounded, hence compact. At every point $x\in K$, we have $\omega_f(x)<\alpha$, so there exists $\delta_x>0$ with $\omega\bigl(f,(x-\delta_x,x+\delta_x)\cap[a,b]\bigr)<\alpha$. The open intervals $\{(x-\delta_x,x+\delta_x)\}_{x\in K}$ cover $K$; by the Lebesgue number lemma, there exists $\lambda>0$ such that any subset of $K$ with diameter less than $\lambda$ is contained in some $(x_0-\delta_{x_0},x_0+\delta_{x_0})$.

Construct a partition $P$ as follows. Include all endpoints of the connected components of $G\cap[a,b]$ (which is a finite union of open intervals, since $G$ is a finite union of open intervals). Include $a$ and $b$. Then subdivide each closed-interval component of $K$ into subintervals of length less than $\lambda$. Each subinterval of the resulting partition $P$ falls into one of two categories:

**Type 1:** The subinterval is contained in $G\cap[a,b]$. Its oscillation satisfies $M_i-m_i\le 2M$, and the total length of all such subintervals is at most $|G\cap[a,b]|\le\sum|G_j|<\eta$.

**Type 2:** The subinterval is contained in $K$ with length less than $\lambda$. By the Lebesgue number property, it lies inside some $(x_0-\delta_{x_0},x_0+\delta_{x_0})$, so $\omega(f,[x_{i-1},x_i])<\alpha$, meaning $M_i-m_i<\alpha$. The total length of all such subintervals is at most $b-a$.

Combining:

$$U(P,f)-L(P,f)\le 2M\cdot\eta+\alpha\cdot(b-a)=2M\cdot\frac{\varepsilon}{4M}+\frac{\varepsilon}{2(b-a)}\cdot(b-a)=\frac{\varepsilon}{2}+\frac{\varepsilon}{2}=\varepsilon.$$

By Darboux's criterion, $f$ is integrable. $\blacksquare$

Lebesgue's criterion is a remarkable result: it reduces the analytic question of integrability to the topological question of how large the discontinuity set is. A function may be discontinuous at every rational point (a dense set) and still be integrable, because the rationals are countable and hence have measure zero. The classical example is **Thomae's function**:

$$t(x)=\begin{cases}1/q&\text{if }x=p/q\text{ in lowest terms with }q>0,\\0&\text{if }x\notin\mathbb{Q}.\end{cases}$$

This function is continuous at every irrational and discontinuous at every rational. Since $\mathbb{Q}\cap[0,1]$ is countable (hence measure zero), Lebesgue's criterion guarantees that $t$ is Riemann integrable on $[0,1]$. Moreover, since $t\ge 0$ and $t$ equals $0$ at every irrational, for any partition $P$ we have $L(P,t)=0$ (every subinterval contains irrationals where $t=0$), so $\int_0^1 t=0$. This is a function with a dense set of discontinuities that is nonetheless integrable—a striking illustration of the power of Lebesgue's characterization.

### 2.2 Properties of the Integral

The Riemann integral satisfies a collection of algebraic and order properties that make it a practical computational tool. We prove the most important ones here, each from first principles using the Darboux framework.

**Theorem (Linearity).** *If $f$ and $g$ are Riemann integrable on $[a,b]$ and $\alpha,\beta\in\mathbb{R}$, then $\alpha f+\beta g$ is Riemann integrable and*

$$\int_a^b(\alpha f+\beta g)=\alpha\int_a^b f+\beta\int_a^b g.$$

*Proof.* We prove the two parts separately.

**Scalar multiplication.** For $\alpha>0$ and any partition $P$, $U(P,\alpha f)=\alpha\,U(P,f)$ and $L(P,\alpha f)=\alpha\,L(P,f)$, since $\sup(\alpha f)=\alpha\sup f$ and $\inf(\alpha f)=\alpha\inf f$ for $\alpha>0$. Thus $U(P,\alpha f)-L(P,\alpha f)=\alpha\bigl(U(P,f)-L(P,f)\bigr)$, which can be made arbitrarily small, proving integrability, and $\int\alpha f=\alpha\int f$. For $\alpha<0$, multiplication by $\alpha$ reverses order, so $U(P,\alpha f)=\alpha\,L(P,f)$ and $L(P,\alpha f)=\alpha\,U(P,f)$. Then $U(P,\alpha f)-L(P,\alpha f)=|\alpha|\bigl(U(P,f)-L(P,f)\bigr)$, again proving integrability, and $\int\alpha f=\alpha\int f$ (the upper and lower integrals swap, but the common value is $\alpha$ times the original). The case $\alpha=0$ is trivial.

**Addition.** For any partition $P$ and subinterval $I_i=[x_{i-1},x_i]$, the inequality $\inf_{I_i}(f+g)\ge\inf_{I_i}f+\inf_{I_i}g$ gives $L(P,f)+L(P,g)\le L(P,f+g)$, and $\sup_{I_i}(f+g)\le\sup_{I_i}f+\sup_{I_i}g$ gives $U(P,f+g)\le U(P,f)+U(P,g)$. Therefore:

$$U(P,f+g)-L(P,f+g)\le\bigl[U(P,f)-L(P,f)\bigr]+\bigl[U(P,g)-L(P,g)\bigr].$$

Given $\varepsilon>0$, choose $P_1$ with $U(P_1,f)-L(P_1,f)<\varepsilon/2$ and $P_2$ with $U(P_2,g)-L(P_2,g)<\varepsilon/2$. For $P=P_1\cup P_2$, the refinement lemma gives $U(P,f+g)-L(P,f+g)<\varepsilon$, proving integrability. For the value: both $\int(f+g)$ and $\int f+\int g$ lie between $L(P,f)+L(P,g)$ and $U(P,f)+U(P,g)$ for every $P$. Since the gap $U(P,f)+U(P,g)-L(P,f)-L(P,g)\to 0$, they must be equal. $\blacksquare$

**Theorem (Monotonicity).** *If $f$ and $g$ are integrable on $[a,b]$ and $f(x)\le g(x)$ for all $x\in[a,b]$, then $\int_a^b f\le\int_a^b g$.*

*Proof.* For any partition $P$, $m_i(f)\le m_i(g)$ and $M_i(f)\le M_i(g)$ on every subinterval, so $L(P,f)\le L(P,g)$ and $U(P,f)\le U(P,g)$. Taking suprema over $P$ gives $\int f\le\int g$. $\blacksquare$

**Theorem (Absolute integrability).** *If $f$ is integrable on $[a,b]$, then $|f|$ is integrable and $\left|\int_a^b f\right|\le\int_a^b|f|$.*

*Proof.* For any interval $I$ and any $x,y\in I$, the reverse triangle inequality gives $||f(x)|-|f(y)||\le|f(x)-f(y)|$. Taking the supremum over $x,y\in I$ yields $\omega(|f|,I)\le\omega(f,I)$, so $U(P,|f|)-L(P,|f|)\le U(P,f)-L(P,f)$ for every partition $P$. Since $f$ is integrable, the right side can be made arbitrarily small, so $|f|$ is integrable. The inequality follows from $-|f|\le f\le|f|$ and monotonicity: $-\int|f|\le\int f\le\int|f|$, hence $\left|\int f\right|\le\int|f|$. $\blacksquare$

**Theorem (Product of integrable functions).** *If $f$ and $g$ are integrable on $[a,b]$, then $fg$ is integrable.*

*Proof.* We first show that $f^2$ is integrable whenever $f$ is integrable and bounded by $M$. For any $x,y$ in a subinterval $I$: $|f(x)^2-f(y)^2|=|f(x)-f(y)|\cdot|f(x)+f(y)|\le 2M|f(x)-f(y)|$. Taking suprema: $\omega(f^2,I)\le 2M\,\omega(f,I)$, so $U(P,f^2)-L(P,f^2)\le 2M\bigl(U(P,f)-L(P,f)\bigr)\to 0$. Now the identity $fg=\tfrac{1}{2}\bigl[(f+g)^2-f^2-g^2\bigr]$ expresses $fg$ as a linear combination of squares of integrable functions (using linearity to handle $f+g$), so $fg$ is integrable. $\blacksquare$

**Theorem (Additivity over intervals).** *If $f$ is integrable on $[a,b]$ and $c\in(a,b)$, then $f$ is integrable on $[a,c]$ and $[c,b]$, and $\int_a^b f=\int_a^c f+\int_c^b f$.*

*Proof.* Given $\varepsilon>0$, there exists a partition $P$ of $[a,b]$ with $U(P,f)-L(P,f)<\varepsilon$. Refine to $Q=P\cup\{c\}$; then $U(Q,f)-L(Q,f)<\varepsilon$ by the refinement lemma. The restriction of $Q$ to $[a,c]$ gives a partition $P_1$ of $[a,c]$, and $U(P_1,f)-L(P_1,f)$ is a partial sum of the non-negative terms in $U(Q,f)-L(Q,f)$, hence $<\varepsilon$. So $f$ is integrable on $[a,c]$; similarly on $[c,b]$. For the value, $U(Q,f)=U(P_1,f)+U(P_2,f)$ and $L(Q,f)=L(P_1,f)+L(P_2,f)$, where $P_2=Q|_{[c,b]}$. Taking limits as $\varepsilon\to 0$ gives $\int_a^b f=\int_a^c f+\int_c^b f$. $\blacksquare$

**Theorem (Mean Value Theorem for Integrals).** *If $f$ is continuous on $[a,b]$, there exists $c\in[a,b]$ with $\int_a^b f=f(c)(b-a)$.*

*Proof.* By the Extreme Value Theorem, $f$ attains its minimum $m$ and maximum $M$ on $[a,b]$. Then $m(b-a)\le\int_a^b f\le M(b-a)$, so $m\le\frac{1}{b-a}\int_a^b f\le M$. By the Intermediate Value Theorem, there exists $c\in[a,b]$ with $f(c)=\frac{1}{b-a}\int_a^b f$. $\blacksquare$

### 2.3 The Fundamental Theorem of Calculus

The Fundamental Theorem of Calculus establishes the deep connection between differentiation and integration that gives calculus its power. It comes in two parts, each with distinct hypotheses and distinct conclusions, and both require careful proof.

**Theorem (FTC, Part I).** *Let $f$ be Riemann integrable on $[a,b]$. Define $F(x)=\int_a^x f(t)\,dt$ for $x\in[a,b]$ (with $F(a)=0$). Then:*

*(a) $F$ is Lipschitz continuous on $[a,b]$.*

*(b) If $f$ is continuous at $c\in[a,b]$, then $F$ is differentiable at $c$ with $F'(c)=f(c)$.*

*Proof of (a).* Since $f$ is integrable, it is bounded: $|f|\le M$ for some $M\ge 0$. By additivity, for $a\le x<y\le b$:

$$|F(y)-F(x)|=\left|\int_x^y f(t)\,dt\right|\le\int_x^y|f(t)|\,dt\le M(y-x),$$

where the first inequality uses absolute integrability and monotonicity. This is the Lipschitz condition.

*Proof of (b).* Suppose $f$ is continuous at $c$. For $h\neq 0$ with $c+h\in[a,b]$:

$$\frac{F(c+h)-F(c)}{h}-f(c)=\frac{1}{h}\int_c^{c+h}f(t)\,dt-f(c)=\frac{1}{h}\int_c^{c+h}\bigl[f(t)-f(c)\bigr]\,dt,$$

where we used $\frac{1}{h}\int_c^{c+h}f(c)\,dt=\frac{f(c)\cdot h}{h}=f(c)$, the integral of a constant over an interval of length $h$. Given $\varepsilon>0$, continuity of $f$ at $c$ provides $\delta>0$ such that $|t-c|<\delta$ implies $|f(t)-f(c)|<\varepsilon$.

For $0<h<\delta$: every $t\in[c,c+h]$ satisfies $|t-c|\le h<\delta$, so:

$$\left|\frac{F(c+h)-F(c)}{h}-f(c)\right|\le\frac{1}{h}\int_c^{c+h}|f(t)-f(c)|\,dt\le\frac{1}{h}\cdot\varepsilon\cdot h=\varepsilon.$$

For $-\delta<h<0$: every $t\in[c+h,c]$ satisfies $|t-c|\le|h|<\delta$, and reversing the integration limits:

$$\frac{F(c+h)-F(c)}{h}-f(c)=\frac{-1}{|h|}\int_{c+h}^{c}\bigl[f(t)-f(c)\bigr]\,dt,$$

$$\left|\frac{F(c+h)-F(c)}{h}-f(c)\right|\le\frac{1}{|h|}\int_{c+h}^{c}|f(t)-f(c)|\,dt\le\frac{1}{|h|}\cdot\varepsilon\cdot|h|=\varepsilon.$$

In both cases, $|F'(c)-f(c)|<\varepsilon$ for $|h|<\delta$, proving $F'(c)=f(c)$. $\blacksquare$

When $f$ is continuous on all of $[a,b]$, FTC Part I tells us that $F(x)=\int_a^x f$ is an antiderivative of $f$. This is a powerful existence result: every continuous function has an antiderivative, constructed explicitly by integration.

**Theorem (FTC, Part II).** *Let $F:[a,b]\to\mathbb{R}$ be differentiable on $[a,b]$ with $F'=f$ Riemann integrable on $[a,b]$. Then:*

$$\int_a^b f(x)\,dx=F(b)-F(a).$$

*Proof.* Let $P=\{x_0,x_1,\dots,x_n\}$ be any partition of $[a,b]$. Since $F$ is continuous on $[x_{i-1},x_i]$ and differentiable on $(x_{i-1},x_i)$, the Mean Value Theorem provides $t_i\in(x_{i-1},x_i)$ with:

$$F(x_i)-F(x_{i-1})=F'(t_i)(x_i-x_{i-1})=f(t_i)\,\Delta x_i.$$

Summing telescopes the left side:

$$F(b)-F(a)=\sum_{i=1}^n\bigl[F(x_i)-F(x_{i-1})\bigr]=\sum_{i=1}^n f(t_i)\,\Delta x_i=S(P,f,\{t_i\}).$$

The right side is a Riemann sum. By the Equivalence Theorem of Section 1, since $f$ is integrable, for any $\varepsilon>0$ there exists $\delta>0$ such that $|S(P,f,\{t_i\})-\int_a^b f|<\varepsilon$ for all partitions with $\|P\|<\delta$ and all tag choices. Choosing such a $P$:

$$\left|F(b)-F(a)-\int_a^b f\right|<\varepsilon.$$

Since the left side is independent of $\varepsilon$ and $\varepsilon$ is arbitrary, $\int_a^b f=F(b)-F(a)$. $\blacksquare$

The hypothesis that $F'=f$ is Riemann integrable is essential. A derivative need not be Riemann integrable—we exhibit a counterexample in Section 3. When the hypothesis holds, FTC Part II provides the familiar evaluation formula $\int_a^b f=F(b)-F(a)$, reducing the computation of integrals to the search for antiderivatives.

Two important techniques follow as direct corollaries of the Fundamental Theorem.

**Integration by Parts.** *If $u$ and $v$ are differentiable on $[a,b]$ with $u'$ and $v'$ Riemann integrable, then:*

$$\int_a^b u(x)\,v'(x)\,dx=\bigl[u(x)v(x)\bigr]_a^b-\int_a^b u'(x)\,v(x)\,dx.$$

*Proof.* By the product rule, $(uv)'=u'v+uv'$. Since $u',v'$ are integrable and $u,v$ are continuous (being differentiable), the products $u'v$ and $uv'$ are integrable (products of integrable and continuous functions are integrable, as continuous functions are integrable and the product theorem applies). By FTC Part II, $\int_a^b(uv)'=uv\big|_a^b$. By linearity, $\int_a^b(u'v+uv')=\int_a^b u'v+\int_a^b uv'$. Equating and rearranging gives the formula. $\blacksquare$

**Substitution.** *If $g:[a,b]\to\mathbb{R}$ is continuously differentiable and $f$ is continuous on $g([a,b])$, then:*

$$\int_{g(a)}^{g(b)}f(x)\,dx=\int_a^b f\bigl(g(t)\bigr)\,g'(t)\,dt.$$

*Proof.* Define $F(x)=\int_{g(a)}^x f(s)\,ds$. By FTC Part I, $F'=f$. By the chain rule, $\frac{d}{dt}F\bigl(g(t)\bigr)=f\bigl(g(t)\bigr)\,g'(t)$, which is continuous (hence integrable). By FTC Part II: $\int_a^b f(g(t))g'(t)\,dt=F(g(b))-F(g(a))=\int_{g(a)}^{g(b)}f(s)\,ds$. $\blacksquare$

### 2.4 Improper Integrals

The Riemann integral is defined only for bounded functions on bounded intervals. Many important functions and domains fall outside this scope: the Gaussian $e^{-x^2}$ on $[0,\infty)$, or $1/\sqrt{x}$ on $(0,1]$. We extend the integral to such cases by taking limits, defining **improper integrals** of two types.

**Type 1: Infinite intervals.** If $f$ is integrable on $[a,b]$ for every $b>a$, we define:

$$\int_a^\infty f=\lim_{b\to\infty}\int_a^b f,$$

provided the limit exists and is finite. Similarly, $\int_{-\infty}^b f=\lim_{a\to-\infty}\int_a^b f$. The two-sided integral $\int_{-\infty}^\infty f$ is defined as $\int_{-\infty}^c f+\int_c^\infty f$ for any $c$, and requires both one-sided integrals to converge independently.

**Type 2: Unbounded functions.** If $f$ is integrable on $[a+\varepsilon,b]$ for every $\varepsilon>0$ but unbounded near $a$, we define $\int_a^b f=\lim_{\varepsilon\to 0^+}\int_{a+\varepsilon}^b f$. The definition is analogous for singularities at $b$ or at an interior point $c$ (where the integral splits into two independent limits).

The most fundamental convergence test is the **$p$-test**, which classifies the convergence of power-function integrals.

**Theorem ($p$-test).** *The integral $\int_1^\infty x^{-p}\,dx$ converges if and only if $p>1$, and $\int_0^1 x^{-p}\,dx$ converges if and only if $p<1$.*

*Proof.* For $\int_1^\infty x^{-p}\,dx$ with $p\neq 1$:

$$\int_1^b x^{-p}\,dx=\frac{x^{1-p}}{1-p}\bigg|_1^b=\frac{b^{1-p}-1}{1-p}.$$

If $p>1$, then $1-p<0$ and $b^{1-p}\to 0$, so the integral converges to $\frac{1}{p-1}$. If $p<1$, then $1-p>0$ and $b^{1-p}\to\infty$, so the integral diverges. For $p=1$: $\int_1^b x^{-1}\,dx=\ln b\to\infty$.

For $\int_0^1 x^{-p}\,dx$ with $p\neq 1$:

$$\int_\varepsilon^1 x^{-p}\,dx=\frac{1-\varepsilon^{1-p}}{1-p}.$$

If $p<1$, then $1-p>0$ and $\varepsilon^{1-p}\to 0$, so the integral converges to $\frac{1}{1-p}$. If $p>1$, then $1-p<0$ and $\varepsilon^{1-p}\to\infty$, so the integral diverges. For $p=1$: $\int_\varepsilon^1 x^{-1}\,dx=-\ln\varepsilon\to\infty$. $\blacksquare$

The borderline case $p=1$ diverges in both settings—a manifestation of the harmonic series' divergence.

**Theorem (Comparison Test).** *If $0\le f(x)\le g(x)$ for all $x\ge a$ and $\int_a^\infty g$ converges, then $\int_a^\infty f$ converges. If $\int_a^\infty f$ diverges, then $\int_a^\infty g$ diverges.*

*Proof.* Define $F(b)=\int_a^b f$ and $G(b)=\int_a^b g$. Since $f,g\ge 0$, both $F$ and $G$ are increasing functions of $b$. Since $\int_a^\infty g$ converges, $G$ is bounded above by $\int_a^\infty g$. The inequality $f\le g$ gives $F(b)\le G(b)\le\int_a^\infty g$ for all $b$, so $F$ is increasing and bounded, hence $\lim_{b\to\infty}F(b)$ exists and is finite. $\blacksquare$

**Theorem (Absolute convergence implies convergence).** *If $\int_a^\infty|f|$ converges, then $\int_a^\infty f$ converges, and $\left|\int_a^\infty f\right|\le\int_a^\infty|f|$.*

*Proof.* Since $0\le f+|f|\le 2|f|$, the comparison test gives convergence of $\int_a^\infty(f+|f|)$. Then $\int_a^\infty f=\int_a^\infty(f+|f|)-\int_a^\infty|f|$ is the difference of two convergent integrals. The inequality follows from $\left|\int_a^b f\right|\le\int_a^b|f|$ for finite $b$ (proved earlier) and taking $b\to\infty$. $\blacksquare$

The converse fails: $\int_1^\infty\frac{\sin x}{x}\,dx$ converges (by the Dirichlet test below) but $\int_1^\infty\frac{|\sin x|}{x}\,dx$ diverges (since $|\sin x|\ge\sin^2 x=\frac{1-\cos 2x}{2}$, and $\int_1^\infty\frac{1}{2x}\,dx$ diverges while $\int_1^\infty\frac{\cos 2x}{2x}\,dx$ converges by the same Dirichlet test, so the difference diverges).

**Theorem (Dirichlet's Test).** *Let $f$ be continuous on $[a,\infty)$ with a bounded antiderivative $F(b)=\int_a^b f$ (i.e., $|F(b)|\le K$ for all $b\ge a$). Let $g$ be continuously differentiable, decreasing, and tending to $0$ as $x\to\infty$. Then $\int_a^\infty f(x)\,g(x)\,dx$ converges.*

*Proof.* By integration by parts, for $b>a$:

$$\int_a^b f(x)\,g(x)\,dx=F(b)\,g(b)-F(a)\,g(a)+\int_a^b F(x)\bigl(-g'(x)\bigr)\,dx.$$

As $b\to\infty$: $F(b)g(b)\to 0$ since $|F(b)|\le K$ and $g(b)\to 0$. The integral $\int_a^\infty F(x)(-g'(x))\,dx$ converges absolutely, since $|F(x)(-g'(x))|\le K(-g'(x))$ and $\int_a^\infty(-g'(x))\,dx=g(a)-\lim_{x\to\infty}g(x)=g(a)<\infty$ (using $g$ decreasing and $g\ge 0$). Therefore:

$$\int_a^\infty f(x)\,g(x)\,dx=-F(a)\,g(a)+\int_a^\infty F(x)\bigl(-g'(x)\bigr)\,dx,$$

which is a sum of finite quantities. $\blacksquare$

Applying this with $f(x)=\sin x$ (whose antiderivative $-\cos x$ is bounded) and $g(x)=1/x$ (decreasing to $0$), we confirm that $\int_1^\infty\frac{\sin x}{x}\,dx$ converges—a conditionally convergent improper integral that is not absolutely convergent.

## 3. High-Performance Optimization & Failure Modes

### 3.1 Numerical Integration: From Darboux Sums to Quadrature Rules

The Darboux framework provides not only a theoretical foundation but also a practical route to numerical computation. Every quadrature rule can be understood as a specific choice of Riemann sum, and the error bounds follow directly from controlling oscillation.

The **trapezoidal rule** approximates the integral by replacing $f$ with linear interpolation on each subinterval of a uniform partition with $n$ subintervals of width $h=(b-a)/n$:

$$T_n=\frac{h}{2}\sum_{i=0}^{n-1}\bigl[f(x_i)+f(x_{i+1})\bigr]=\frac{h}{2}\left[f(x_0)+2f(x_1)+\cdots+2f(x_{n-1})+f(x_n)\right].$$

Each term $\frac{h}{2}[f(x_i)+f(x_{i+1})]$ is the area of the trapezoid on $[x_i,x_{i+1}]$, which equals the average of the upper and lower Darboux rectangle areas when $f$ is linear. For a general $f\in C^2[a,b]$, the error is:

$$\left|T_n-\int_a^b f\right|\le\frac{(b-a)^3}{12n^2}\max_{[a,b]}|f''|.$$

*Proof of error bound.* On each subinterval $[x_{i-1},x_i]$ of width $h$, the local error is:

$$E_i=\int_{x_{i-1}}^{x_i}f(x)\,dx-\frac{h}{2}\bigl[f(x_{i-1})+f(x_i)\bigr].$$

Define $K(x)=\frac{1}{2}(x-x_{i-1})(x_i-x)$, which is non-negative on $[x_{i-1},x_i]$ and vanishes at the endpoints. Integrate by parts twice (or use the Peano kernel theorem): the error formula for linear interpolation gives $E_i=\int_{x_{i-1}}^{x_i}K(x)\,f''(x)\,dx$ up to sign. Taking absolute values:

$$|E_i|\le\max_{[x_{i-1},x_i]}|f''|\int_{x_{i-1}}^{x_i}K(x)\,dx=\max|f''|\cdot\frac{h^3}{12}.$$

(The integral $\int_0^h\frac{1}{2}t(h-t)\,dt=\frac{h^3}{12}$ is computed by elementary calculus.) Summing over $n$ subintervals:

$$|E|\le n\cdot\frac{M_2\,h^3}{12}=\frac{M_2(b-a)h^2}{12}=\frac{M_2(b-a)^3}{12n^2},$$

where $M_2=\max_{[a,b]}|f''|$. $\blacksquare$

The trapezoidal rule achieves $O(n^{-2})$ convergence—doubling the number of points reduces the error by a factor of four. **Simpson's rule** improves this dramatically by replacing linear interpolation with quadratic interpolation on pairs of subintervals:

$$S_n=\frac{h}{3}\left[f(x_0)+4f(x_1)+2f(x_2)+4f(x_3)+\cdots+4f(x_{n-1})+f(x_n)\right],$$

where $n$ must be even. For $f\in C^4[a,b]$, the error satisfies:

$$\left|S_n-\int_a^b f\right|\le\frac{(b-a)^5}{180\,n^4}\max_{[a,b]}|f^{(4)}|.$$

The proof proceeds analogously, using the Peano kernel for quadratic interpolation: the kernel $K(x)=\frac{1}{24}(x-x_{i-1})(x_{i-1/2}-x)^2(x_i-x)$ (where $x_{i-1/2}$ is the midpoint) integrates to $h^5/180$ in absolute value. Simpson's rule achieves $O(n^{-4})$ convergence—doubling the number of points reduces the error by a factor of sixteen. For smooth functions, this is a dramatic improvement at essentially no additional computational cost.

### 3.2 Failure: The Dirichlet Function and Non-Integrability

The most instructive failure of Riemann integrability is the **Dirichlet function**:

$$\mathbf{1}_{\mathbb{Q}}(x)=\begin{cases}1&\text{if }x\in\mathbb{Q},\\0&\text{if }x\notin\mathbb{Q}.\end{cases}$$

For any partition $P$ of $[a,b]$, every subinterval $[x_{i-1},x_i]$ contains both rational and irrational points (by the density of $\mathbb{Q}$ and $\mathbb{R}\setminus\mathbb{Q}$ in $\mathbb{R}$). Therefore $M_i=1$ and $m_i=0$ for every $i$, giving:

$$U(P,\mathbf{1}_{\mathbb{Q}})=\sum_{i=1}^n 1\cdot\Delta x_i=b-a,\qquad L(P,\mathbf{1}_{\mathbb{Q}})=\sum_{i=1}^n 0\cdot\Delta x_i=0,$$

for every partition $P$. The upper integral is $b-a$ and the lower integral is $0$; they never coincide, so $\mathbf{1}_{\mathbb{Q}}$ is not Riemann integrable. The function is discontinuous at every point of $[a,b]$, and $[a,b]$ does not have measure zero (it has Lebesgue measure $b-a>0$), consistent with Lebesgue's criterion.

This example illustrates a fundamental limitation of the Riemann integral: it cannot handle functions that oscillate too wildly on every interval. The Lebesgue integral, developed later, extends the class of integrable functions to include $\mathbf{1}_{\mathbb{Q}}$ (with Lebesgue integral $0$, since $\mathbb{Q}$ has Lebesgue measure zero), but the Riemann theory cannot reach this far.

### 3.3 Failure: When the Fundamental Theorem Does Not Apply

FTC Part II requires the derivative $F'=f$ to be Riemann integrable. This hypothesis is not automatic: a derivative can exist everywhere yet fail to be Riemann integrable.

**Unbounded derivative.** Consider $f(x)=x^2\sin(1/x^2)$ for $x\neq 0$, with $f(0)=0$. Then $f$ is differentiable everywhere on $[0,1]$, with:

$$f'(x)=2x\sin(1/x^2)-\frac{2}{x}\cos(1/x^2)\quad(x\neq 0),\qquad f'(0)=0.$$

The term $\frac{2}{x}\cos(1/x^2)$ is unbounded near $x=0$, so $f'$ is not bounded on $[0,1]$ and hence not Riemann integrable. FTC Part II cannot be applied, even though $f$ is differentiable everywhere. The integral $\int_0^1 f'$ does not exist in the Riemann sense, so the formula $\int_0^1 f'=f(1)-f(0)$ is not merely unproved—it is meaningless within the Riemann theory.

**Bounded but non-integrable derivative (Volterra's construction).** Volterra constructed a function $F$ differentiable on $[0,1]$ with $F'$ bounded but discontinuous on a set of positive measure (a "fat Cantor set"). Since the discontinuity set of $F'$ has positive Lebesgue measure, $F'$ is not Riemann integrable by Lebesgue's criterion. This is a deeper failure: the derivative exists and is bounded, but its oscillations on the fat Cantor set are too severe for the Riemann integral to handle. The construction proceeds by modifying the Cantor set to have positive measure (removing middle intervals of decreasing proportions so that the total removed length is less than 1), then placing scaled copies of $x^2\sin(1/x)$ on each removed interval. The resulting function is differentiable everywhere, but its derivative oscillates discontinuously at every point of the fat Cantor set.

These examples show that the hypotheses of FTC Part II are not redundant. The formula $\int_a^b F'=F(b)-F(a)$ holds when $F'$ is integrable, but integrability of a derivative is a genuine restriction—one that the Lebesgue theory relaxes (every bounded derivative is Lebesgue integrable, and FTC holds in a more general sense).

### 3.4 Failure: Improper Integral Divergence

Improper integrals can fail to converge in instructive ways.

**Divergence to infinity.** The integral $\int_1^\infty\frac{1}{x}\,dx=\lim_{b\to\infty}\ln b=\infty$ diverges, as does $\int_0^1\frac{1}{x}\,dx=\lim_{\varepsilon\to 0^+}(-\ln\varepsilon)=\infty$. These are the borderline $p=1$ cases of the $p$-test.

**Oscillatory divergence.** The integral $\int_0^\infty\cos(x^2)\,dx$ actually converges (by a substitution $u=x^2$ and Dirichlet's test), but $\int_0^\infty\cos x\,dx$ diverges: $\int_0^b\cos x\,dx=\sin b$, which has no limit as $b\to\infty$. The integrand does not decay, so the positive and negative areas fail to settle to a finite value.

**Conditional convergence.** The integral $\int_1^\infty\frac{\sin x}{x}\,dx$ converges (by Dirichlet's test) but not absolutely: $\int_1^\infty\frac{|\sin x|}{x}\,dx$ diverges. The divergence of the absolute integral follows from $|\sin x|\ge\sin^2 x=\frac{1-\cos 2x}{2}$, which gives $\int_1^\infty\frac{|\sin x|}{x}\,dx\ge\frac{1}{2}\int_1^\infty\frac{1}{x}\,dx-\frac{1}{2}\int_1^\infty\frac{\cos 2x}{x}\,dx$. The first integral diverges (harmonic), the second converges (Dirichlet test with $f=\cos 2x$, $g=1/x$), so the difference diverges. This mirrors the behavior of the alternating harmonic series $\sum(-1)^n/n$, which converges but not absolutely.

**Dependence on definition for two-sided integrals.** The integral $\int_{-\infty}^\infty\sin x\,dx$ diverges under the standard definition (both $\int_{-\infty}^0$ and $\int_0^\infty$ must converge independently), but the symmetric limit $\lim_{R\to\infty}\int_{-R}^R\sin x\,dx=\lim_{R\to\infty}0=0$ exists. This **Cauchy principal value** is a weaker notion of convergence that can assign a finite value to integrals that diverge in the standard sense. The two notions agree for absolutely convergent integrals but can differ for conditionally convergent ones.

### 3.5 The Integrability Landscape

The following table summarizes the complete classification of Riemann integrability for bounded functions on $[a,b]$, organized by the structure of the discontinuity set:

| Class | Discontinuity set | Integrable? | Key mechanism |
|---|---|---|---|
| Continuous | $\varnothing$ | Yes | Uniform continuity controls oscillation |
| Monotone | At most countable | Yes | Total variation telescopes across partition |
| Bounded, finitely many discontinuities | Finite set | Yes | Discontinuities isolated in small subintervals |
| Thomae's function | $\mathbb{Q}\cap[a,b]$ (countable) | Yes | Measure zero by Lebesgue's criterion |
| Bounded, $D_f$ measure zero | Measure zero | Yes | Lebesgue's criterion ($\Leftarrow$) |
| Dirichlet function | $[a,b]$ (positive measure) | No | Oscillation maximal on every subinterval |
| Volterra's derivative | Fat Cantor set (positive measure) | No | Oscillation on positive-measure set |

The Riemann integral thus occupies a middle ground: it handles all continuous and monotone functions, and many functions with infinitely many discontinuities, but it fails for functions whose discontinuities are too densely distributed. The passage to the Lebesgue integral, which we develop in subsequent lessons, removes this limitation by decomposing the domain according to level sets rather than partitions, at the cost of greater measure-theoretic machinery.

The Fundamental Theorem of Calculus completes the architecture: integration and differentiation are inverse operations, provided the derivative is integrable. This condition, automatic for continuous functions but not for all derivatives, is the precise boundary within which the classical calculus of Newton and Leibniz operates without leaving the Riemann framework.
