# Lesson 3: Existence, Uniqueness, Dependence — The Foundational Theorems

## 1. First-Principles Intuition & Invariants

The fundamental question in the theory of ordinary differential equations is deceptively simple: given an initial value problem of the form $\frac{dy}{dt} = f(t, y)$ with $y(t_0) = y_0$, does a solution exist? If so, is it unique? And how does this solution behave as we perturb the initial condition or modify the vector field $f$ itself? These questions strike at the heart of mathematical modeling, for without existence we have posed a meaningless problem, without uniqueness we cannot predict future behavior, and without continuous dependence we cannot trust numerical approximations or experimental measurements contaminated by inevitable noise.

The classical approach to existence and uniqueness in ordinary differential equations rests upon the Picard-Lindelöf theorem, a constructive result that simultaneously proves existence through an explicit iterative scheme and establishes uniqueness through a contraction mapping argument. The theorem demands a Lipschitz condition on the vector field $f$ with respect to the state variable $y$, a regularity hypothesis that ensures solutions cannot bifurcate or exhibit pathological branching behavior. This condition, while seemingly technical, encodes the intuition that nearby initial conditions should yield nearby trajectories, at least locally in time.

Before we can appreciate the power of the Picard iteration scheme, we must internalize the integral equation reformulation of the initial value problem. The differential equation $y'(t) = f(t, y(t))$ with $y(t_0) = y_0$ is equivalent to the integral equation

$$y(t) = y_0 + \int_{t_0}^{t} f(s, y(s)) \, ds.$$

This reformulation trades the problem of differentiation for one of integration, converting a rate-of-change specification into a cumulative displacement formulation. The advantage is profound: integration is a smoothing operation, while differentiation amplifies irregularities. By working in the space of continuous functions and iterating the integral operator, we construct solutions through successive approximations, each one more refined than the last.

The Lipschitz condition on $f$ takes the form $|f(t, y_1) - f(t, y_2)| \le L |y_1 - y_2|$ for all $(t, y_1)$ and $(t, y_2)$ in some domain. This constant $L$ measures the maximal rate at which the vector field's output can change relative to changes in the state variable. When $L$ is finite, the integral operator becomes a contraction on an appropriately chosen complete metric space, and the Banach fixed point theorem guarantees the existence of a unique fixed point—precisely the solution we seek.

The theory of maximal intervals of existence extends these local results to global behavior. A solution can be extended forward in time until it either escapes to infinity, reaches the boundary of the domain where $f$ is defined, or encounters a finite-time singularity. The Gronwall inequality serves as the master estimation tool throughout, allowing us to control the growth of solutions and their differences through differential inequalities. This inequality, elegant in its simplicity, asserts that if $u(t) \le a + \int_{t_0}^{t} b(s) u(s) \, ds$ with $a \ge 0$ and $b(s) \ge 0$, then $u(t) \le a \exp\left(\int_{t_0}^{t} b(s) \, ds\right)$. It transforms an integral inequality into an explicit exponential bound, the fundamental currency of quantitative analysis in differential equations.

Continuous dependence theorems assert that solutions depend continuously on initial data and parameters. If we perturb $y_0$ by a small amount $\delta$, the resulting solution $y(t)$ changes by at most $O(\delta)$ on any compact time interval where solutions exist. This stability property legitimizes numerical computation and physical measurement: the unavoidable errors in specifying initial conditions do not catastrophically amplify, at least not immediately. The proof again relies on Gronwall's inequality, applied to the difference between two solutions.

These foundational results—existence, uniqueness, maximal intervals, continuous dependence—form the bedrock upon which all subsequent theory rests. Without them, the study of differential equations would be a catalog of examples rather than a coherent mathematical discipline. We now proceed to construct these theorems from first principles, providing complete proofs with every algebraic transition justified.

## 2. Core Architecture & Mechanics

The Picard iteration scheme constructs a sequence of functions $\{y_n(t)\}_{n=0}^{\infty}$ that converges uniformly to the unique solution of the initial value problem. We begin with the crude approximation $y_0(t) = y_0$, the constant function equal to the initial condition. Each subsequent iterate is defined by applying the integral operator:

$$y_{n+1}(t) = y_0 + \int_{t_0}^{t} f(s, y_n(s)) \, ds.$$

This recursive definition generates an improving sequence of approximations. The zeroth iterate ignores the dynamics entirely; the first iterate $y_1(t) = y_0 + \int_{t_0}^{t} f(s, y_0) \, ds$ incorporates the initial slope information; the second iterate corrects this by using the slope information from the first iterate; and so on. The process resembles successive refinement in numerical analysis, but here we prove convergence in the uniform norm.

To establish the Picard-Lindelöf theorem rigorously, we work in a rectangular domain $R = \{(t, y) : |t - t_0| \le a, |y - y_0| \le b\}$ where $f$ is continuous and satisfies the Lipschitz condition $|f(t, y_1) - f(t, y_2)| \le L |y_1 - y_2|$ for all $(t, y_1), (t, y_2) \in R$. Since $f$ is continuous on the compact set $R$, it is bounded: $|f(t, y)| \le M$ for all $(t, y) \in R$. We restrict attention to the interval $|t - t_0| \le \alpha$ where $\alpha = \min\{a, b/M\}$. This choice ensures that if $|y(s) - y_0| \le b$ for all $s$ between $t_0$ and $t$, then the integral $\int_{t_0}^{t} |f(s, y(s))| \, ds \le M |t - t_0| \le M \alpha \le b$, keeping the trajectory within the vertical strip.

We now prove that the Picard iterates remain well-defined and stay within the region where $f$ is defined. For $y_0(t) = y_0$, we have $|y_0(t) - y_0| = 0 \le b$ trivially. Suppose $|y_n(s) - y_0| \le b$ for all $|s - t_0| \le \alpha$. Then

$$|y_{n+1}(t) - y_0| = \left| \int_{t_0}^{t} f(s, y_n(s)) \, ds \right| \le \int_{t_0}^{t} |f(s, y_n(s))| \, ds \le M |t - t_0| \le M \alpha \le b,$$

establishing by induction that all iterates remain in the domain $R$.

The heart of the proof lies in showing that the sequence $\{y_n(t)\}$ is Cauchy in the space $C([t_0 - \alpha, t_0 + \alpha])$ equipped with the supremum norm $\|y\| = \sup_{|t - t_0| \le \alpha} |y(t)|$. We estimate the difference between consecutive iterates. For the first step,

$$|y_1(t) - y_0(t)| = \left| \int_{t_0}^{t} f(s, y_0) \, ds \right| \le M |t - t_0|.$$

For the second step, using the Lipschitz condition,

$$|y_2(t) - y_1(t)| = \left| \int_{t_0}^{t} [f(s, y_1(s)) - f(s, y_0(s))] \, ds \right| \le \int_{t_0}^{t} L |y_1(s) - y_0(s)| \, ds.$$

Substituting the previous bound,

$$|y_2(t) - y_1(t)| \le \int_{t_0}^{t} L M |s - t_0| \, ds = L M \frac{|t - t_0|^2}{2}.$$

Continuing inductively, we claim that

$$|y_{n+1}(t) - y_n(t)| \le M \frac{(L |t - t_0|)^n}{n!}.$$

The base case $n = 0$ was verified above. Assuming the bound for step $n$, we compute

$$|y_{n+2}(t) - y_{n+1}(t)| = \left| \int_{t_0}^{t} [f(s, y_{n+1}(s)) - f(s, y_n(s))] \, ds \right|$$
$$\le \int_{t_0}^{t} L |y_{n+1}(s) - y_n(s)| \, ds \le \int_{t_0}^{t} L M \frac{(L |s - t_0|)^n}{n!} \, ds.$$

For $t \ge t_0$, we have

$$\int_{t_0}^{t} L M \frac{(L (s - t_0))^n}{n!} \, ds = L M \left[ \frac{(L (s - t_0))^{n+1}}{(n+1)! L} \right]_{s=t_0}^{s=t} = M \frac{(L (t - t_0))^{n+1}}{(n+1)!},$$

completing the induction. A symmetric argument handles $t < t_0$.

Now observe that for any $|t - t_0| \le \alpha$, the series $\sum_{n=0}^{\infty} |y_{n+1}(t) - y_n(t)|$ is dominated by the convergent series $\sum_{n=0}^{\infty} M \frac{(L \alpha)^n}{n!} = M e^{L \alpha}$. By the Weierstrass M-test, the series converges uniformly on $|t - t_0| \le \alpha$. Therefore, the sequence of partial sums $y_n(t) = y_0 + \sum_{k=0}^{n-1} [y_{k+1}(t) - y_k(t)]$ converges uniformly to a limit function $y(t)$.

The limit function $y(t)$ is continuous since it is the uniform limit of continuous functions. Moreover, we can pass the limit through the integral to verify that $y(t)$ satisfies the integral equation:

$$y(t) = \lim_{n \to \infty} y_n(t) = y_0 + \lim_{n \to \infty} \int_{t_0}^{t} f(s, y_{n-1}(s)) \, ds.$$

The uniform convergence of $y_n$ to $y$ and the continuity of $f$ imply that $f(s, y_n(s)) \to f(s, y(s))$ uniformly in $s$, allowing us to interchange limit and integral:

$$y(t) = y_0 + \int_{t_0}^{t} f(s, y(s)) \, ds.$$

Differentiating both sides using the fundamental theorem of calculus, $y'(t) = f(t, y(t))$, and clearly $y(t_0) = y_0$. We have constructed a solution.

Uniqueness follows from a contraction argument. Suppose $y(t)$ and $z(t)$ are two solutions on $|t - t_0| \le \alpha$ with the same initial condition. Then

$$|y(t) - z(t)| = \left| \int_{t_0}^{t} [f(s, y(s)) - f(s, z(s))] \, ds \right| \le \int_{t_0}^{t} L |y(s) - z(s)| \, ds.$$

Define $u(t) = |y(t) - z(t)|$. For $t \ge t_0$, we have $u(t) \le \int_{t_0}^{t} L u(s) \, ds$. Gronwall's inequality, which we prove shortly, then implies $u(t) \le 0 \cdot e^{L(t - t_0)} = 0$. Hence $y(t) = z(t)$ for all $t \ge t_0$. A symmetric argument covers $t < t_0$.

Gronwall's inequality is the workhorse of differential equation estimates. In its differential form, if $u'(t) \le b(t) u(t)$ with $u(t_0) = u_0 \ge 0$ and $b(t)$ continuous, then $u(t) \le u_0 \exp\left(\int_{t_0}^{t} b(s) \, ds\right)$. To prove this, define $v(t) = u(t) \exp\left(-\int_{t_0}^{t} b(s) \, ds\right)$. Then

$$v'(t) = u'(t) e^{-\int_{t_0}^{t} b(s) \, ds} - u(t) b(t) e^{-\int_{t_0}^{t} b(s) \, ds} \le b(t) u(t) e^{-\int_{t_0}^{t} b(s) \, ds} - u(t) b(t) e^{-\int_{t_0}^{t} b(s) \, ds} = 0.$$

Hence $v(t)$ is nonincreasing, so $v(t) \le v(t_0) = u_0$. Multiplying by the exponential factor yields the desired bound.

The integral form of Gronwall's inequality, which we used in the uniqueness proof, states that if $u(t) \le a + \int_{t_0}^{t} b(s) u(s) \, ds$ with $a \ge 0$ and $b(s) \ge 0$, then $u(t) \le a \exp\left(\int_{t_0}^{t} b(s) \, ds\right)$. To prove this, define $w(t) = \int_{t_0}^{t} b(s) u(s) \, ds$. Then $w'(t) = b(t) u(t) \le b(t) (a + w(t))$, so $(w(t) + a) / (w(t) + a) \cdot w'(t) \le b(t)$, which integrates to $\log(w(t) + a) - \log(a) \le \int_{t_0}^{t} b(s) \, ds$. Exponentiating, $w(t) + a \le a \exp\left(\int_{t_0}^{t} b(s) \, ds\right)$, and since $u(t) \le a + w(t)$, the conclusion follows.

The theory of maximal intervals of existence addresses the question: how far can a solution be extended? Given an initial value problem on a domain $D \subseteq \mathbb{R} \times \mathbb{R}^n$, the solution defines a maximal interval of existence $(t_-, t_+)$ containing $t_0$. The solution cannot be extended beyond this interval, meaning that as $t \to t_+$, either $|y(t)| \to \infty$ or $(t, y(t))$ approaches the boundary of $D$. The key result is that if $D = \mathbb{R} \times \mathbb{R}^n$ and $f$ is globally Lipschitz in $y$ and satisfies a linear growth condition $|f(t, y)| \le C(1 + |y|)$, then the solution exists for all time.

To see this, suppose the maximal interval is $(t_-, t_+)$ with $t_+ < \infty$. The integral equation yields $|y(t)| \le |y_0| + \int_{t_0}^{t} |f(s, y(s))| \, ds \le |y_0| + \int_{t_0}^{t} C(1 + |y(s)|) \, ds$. Applying Gronwall's inequality with $a = |y_0| + C(t - t_0)$ and constant $b = C$, we obtain $|y(t)| \le [|y_0| + C(t - t_0)] e^{C(t - t_0)}$, a finite bound for $t < t_+$. This contradicts the assumption that $|y(t)| \to \infty$ as $t \to t_+$, and since $(t, y(t))$ cannot escape the domain $\mathbb{R} \times \mathbb{R}^n$, we conclude $t_+ = \infty$.

Continuous dependence on initial data asserts that if $y(t)$ and $z(t)$ are solutions with initial conditions $y(t_0) = y_0$ and $z(t_0) = z_0$, then $|y(t) - z(t)| \le |y_0 - z_0| e^{L|t - t_0|}$ on any interval where both solutions exist and the Lipschitz constant is $L$. The proof is immediate from Gronwall: $|y(t) - z(t)| \le |y_0 - z_0| + \int_{t_0}^{t} L |y(s) - z(s)| \, ds$, so Gronwall's inequality directly yields the exponential bound. This estimate quantifies the intuition that small perturbations in initial data lead to small perturbations in solutions, at least on bounded time intervals. The exponential factor reflects the amplification due to the dynamics, growing without bound as $|t - t_0| \to \infty$ in general.

Continuous dependence on parameters extends this result to families of differential equations $y' = f(t, y, \lambda)$ where $\lambda \in \mathbb{R}^p$ is a parameter vector. If $f$ is Lipschitz in $(y, \lambda)$ jointly, then solutions depend continuously on $\lambda$ as well. The proof follows the same Gronwall-based strategy: $|y(t, \lambda) - y(t, \mu)| \le \int_{t_0}^{t} |f(s, y(s, \lambda), \lambda) - f(s, y(s, \mu), \mu)| \, ds$, and applying Lipschitz continuity in both arguments yields the exponential bound $|y(t, \lambda) - y(t, \mu)| \le C |\lambda - \mu| e^{L|t - t_0|}$ for an appropriate constant $C$.

## 3. High-Performance Optimization & Failure Modes

The Picard iteration scheme, while theoretically elegant, converges slowly in practice when the Lipschitz constant $L$ is large. The convergence rate is governed by the series $\sum_{n=0}^{\infty} M \frac{(L\alpha)^n}{n!}$, which requires many terms when $L\alpha$ is not small. In numerical work, practitioners instead use Runge-Kutta methods or multistep schemes that achieve higher-order convergence. However, the Picard iteration provides a constructive proof of existence and serves as the foundation for more sophisticated iteration schemes in the theory of partial differential equations, such as the Banach-Caccioppoli contraction principle applied to abstract function spaces.

The Lipschitz condition, while sufficient for uniqueness, is not necessary. The weaker Osgood condition $\int_0^{\epsilon} \frac{d\xi}{\omega(\xi)} = \infty$ where $|f(t, y_1) - f(t, y_2)| \le \omega(|y_1 - y_2|)$ and $\omega$ is continuous, increasing, and $\omega(0) = 0$, also guarantees uniqueness. The Osgood theorem covers equations like $y' = \sqrt{|y|}$ where the right-hand side fails to be Lipschitz at $y = 0$ (since $|\sqrt{|y_1|} - \sqrt{|y_2|}| / |y_1 - y_2| \to \infty$ as $y_1, y_2 \to 0$), yet the Osgood integral diverges: $\int_0^{\epsilon} \frac{d\xi}{\sqrt{\xi}} = 2\sqrt{\epsilon} \to 0$ as $\epsilon \to 0$. Wait, this integral converges, not diverges. Let me reconsider. Actually, for $\omega(\xi) = \sqrt{\xi}$, we have $\int_0^{\epsilon} \frac{d\xi}{\sqrt{\xi}} = 2\sqrt{\epsilon}$, which approaches zero as $\epsilon \to 0$, so the integral does not diverge to infinity. The correct statement is that for $\omega(\xi) = \xi^{\alpha}$ with $\alpha < 1$, the Osgood integral $\int_0^{\epsilon} \frac{d\xi}{\xi^{\alpha}} = \frac{\epsilon^{1-\alpha}}{1-\alpha}$, which diverges to infinity as $\epsilon \to 0$ only if $\alpha \ge 1$. For $\alpha = 1/2$, the integral converges, and in fact uniqueness can fail. A counterexample is $y' = 2\sqrt{|y|}$ with $y(0) = 0$, which admits both the trivial solution $y(t) = 0$ and the solution $y(t) = t^2$ for $t \ge 0$ (and $y(t) = -t^2$ for $t \le 0$). The precise Osgood condition requires that the integral diverges, which occurs when $\omega$ grows at least as fast as linearly near zero.

A common failure mode in applying existence theorems is neglecting the local nature of the result. The Picard-Lindelöf theorem guarantees existence on an interval $|t - t_0| \le \alpha$ where $\alpha = \min\{a, b/M\}$, which can be arbitrarily small if the vector field $f$ has large magnitude $M$ or the domain has small vertical extent $b$. The example $y' = y^2$ with $y(0) = 1$ illustrates finite-time blowup: the solution $y(t) = 1/(1 - t)$ exists only for $t < 1$ despite the vector field being smooth everywhere. The Picard-Lindelöf theorem correctly predicts local existence near $t = 0$, but global existence requires additional hypotheses such as the linear growth condition.

Another subtlety arises in systems with state-dependent discontinuities. The equation $y' = \text{sgn}(y)$ where $\text{sgn}$ is the sign function fails to satisfy the Lipschitz condition at $y = 0$. Starting from $y(0) = 0$, the differential equation does not uniquely determine the solution: the system could remain at $y = 0$ (since $\text{sgn}(0)$ is often defined as zero), or it could jump to positive or negative values. This non-uniqueness reflects the failure of the Lipschitz hypothesis. In applications such as dry friction or control systems with switching, one must carefully specify the behavior at discontinuities, often invoking set-valued differential inclusions or Filippov solutions.

The continuous dependence estimates, while reassuring, carry an exponential factor $e^{L|t - t_0|}$ that can become astronomically large on long time intervals. For chaotic systems with positive Lyapunov exponents, nearby trajectories separate exponentially fast, and the exponential dependence in the Picard-Lindelöf theorem reflects this sensitivity. In practice, this means that numerical simulations of chaotic systems are reliable only over a finite prediction horizon, beyond which accumulated roundoff errors overwhelm the computation. The shadowing lemma from dynamical systems theory provides a partial remedy: even though the computed trajectory diverges from the exact solution, it may shadow a nearby exact trajectory with slightly perturbed initial conditions.

The Gronwall inequality admits numerous generalizations and refinements. The discrete Gronwall inequality states that if $u_n \le a + \sum_{k=0}^{n-1} b_k u_k$ with $a, b_k, u_k \ge 0$, then $u_n \le a \prod_{k=0}^{n-1} (1 + b_k)$. In the continuous setting with time-varying coefficients, if $u(t) \le a(t) + \int_{t_0}^{t} b(s) u(s) \, ds$ where $a(t)$ is differentiable and $a'(t) \le b(t) a(t)$, then $u(t) \le a(t) \exp\left(\int_{t_0}^{t} b(s) \, ds\right)$. These variants arise in the analysis of perturbed systems and stability theory.

A practical optimization in applying existence theorems is to choose the domain $R$ carefully to maximize the interval of existence $\alpha$. Since $\alpha = \min\{a, b/M\}$, one seeks to balance the horizontal and vertical extents against the bound $M = \sup_{R} |f|$. Enlarging $a$ or $b$ may increase $M$ if $f$ grows rapidly, potentially decreasing $\alpha$. In some cases, an optimal choice of rectangular domain can be computed explicitly. For example, consider $y' = y^2$ with $y(0) = 1$. We have $M = \sup_{|y - 1| \le b} y^2 \le (1 + b)^2$, so $\alpha = \min\{a, b/(1+b)^2\}$. The function $g(b) = b/(1+b)^2$ achieves its maximum at $b = 1$, yielding $g(1) = 1/4$. Thus, choosing $b = 1$ and any $a \ge 1/4$ gives $\alpha = 1/4$. This agrees with the exact solution's blowup time: starting from $y(0) = 1$, the solution $y(t) = 1/(1-t)$ reaches $y(1/4) = 4/3$, within the domain $|y - 1| \le 1$.

The maximal interval of existence can be characterized using continuation arguments. Suppose we have established existence on $[t_0, t_1)$. If $\sup_{t \in [t_0, t_1)} |y(t)| < \infty$ and $(t_1, \lim_{t \to t_1^-} y(t))$ lies in the interior of the domain $D$, then the Picard-Lindelöf theorem applies anew, extending the solution past $t_1$. Repeating this process, the solution extends until $(t, y(t))$ escapes every compact subset of $D$ or $|y(t)| \to \infty$. The maximal interval $(t_-, t_+)$ is therefore the largest interval on which the solution cannot be continued.

In summary, the Picard-Lindelöf theorem and its associated machinery—Gronwall's inequality, continuous dependence, and maximal existence intervals—provide the rigorous foundation for the qualitative and quantitative theory of ordinary differential equations. Every subsequent result, from stability theory to bifurcation analysis to numerical methods, rests upon these foundational estimates. The constructive nature of the Picard iteration and the explicit exponential bounds from Gronwall make these results not merely existence theorems but practical tools for analysis and computation. The failure modes—violation of Lipschitz continuity, finite-time blowup, exponential separation of trajectories—delineate the boundaries of applicability and guide the search for appropriate hypotheses in more general settings.
