# Lesson 5: Stochastic Global Optimization

## 1. First-Principles Intuition & Invariants

The curse of dimensionality transforms optimization from an elegant mathematical exercise into a computational battlefield. When the objective function $f: \mathbb{R}^n \to \mathbb{R}$ lives in a space where $n$ exceeds even modest values like $n = 100$, deterministic grid search becomes computationally infeasible: exhaustively sampling just 10 points per dimension yields $10^{100}$ function evaluations, a number that dwarfs the estimated atom count in the observable universe. Even when the function possesses smooth gradients amenable to Newton-Raphson or quasi-Newton descent, the presence of multiple local minima, saddle points with nearly-zero eigenvalues, and rugged plateau regions can trap deterministic algorithms in suboptimal basins for arbitrarily long durations.

Stochastic global optimization emerges as the principled response to this computational catastrophe. Rather than attempting exhaustive enumeration or relying on the fiction of unimodal convexity, stochastic methods inject controlled randomness into the search process, enabling escape from local minima while maintaining statistical guarantees of convergence to global optima—or at minimum, high-quality approximate solutions with bounded suboptimality. The fundamental trade-off crystallizes immediately: we surrender the deterministic convergence certificates of convex optimization in exchange for practical tractability on high-dimensional, non-convex, multimodal landscapes that model real phenomena in machine learning, operations research, molecular chemistry, and financial portfolio allocation.

The landscape of stochastic optimization divides naturally into three paradigms, each grounded in distinct mathematical principles. First-order stochastic gradient methods replace exact gradients $\nabla f(x)$ with noisy unbiased estimators $g(x)$, exploiting the law of large numbers to guarantee that the accumulated noise averages to zero over sufficiently many iterations. Variance reduction techniques—SVRG (Stochastic Variance Reduced Gradient) and SAGA (a variance-reduced generalization)—tighten convergence rates from sublinear $O(1/\sqrt{T})$ to linear $O(\rho^T)$ for strongly convex functions by maintaining auxiliary gradient tables that subtract out systematic bias from stochastic samples.

Metaheuristic search algorithms abandon gradient information entirely, instead modeling optimization as evolution, thermodynamics, or collective behavior. Simulated annealing maps the optimization problem onto statistical mechanics, interpreting the objective function as an energy landscape and applying the Metropolis-Hastings acceptance criterion with a temperature schedule $T(t)$ that asymptotically approaches zero. The Boltzmann distribution $\pi(x) \propto \exp(-f(x)/T)$ guarantees that given sufficient cooling time governed by logarithmic schedules $T(t) = c / \log(1+t)$, the algorithm converges in distribution to the global minimum with probability one—a theoretical guarantee purchased at the cost of impractically slow cooling rates in finite-time budgets.

Genetic algorithms encode candidate solutions as chromosomes in a finite alphabet $\Sigma^n$, applying crossover and mutation operators that respect the schema theorem: high-fitness building blocks (schemata) receive exponentially increasing trials across generations. The implicit parallelism of genetic algorithms processes approximately $O(n^3)$ schemata per generation despite evaluating only a polynomial-sized population, though this Holland hypothesis remains rigorously proven only for simplified fitness landscapes without epistatic interactions between loci.

Particle swarm optimization transposes the optimization problem into kinematic phase space, modeling each candidate solution as a particle with position $x_i(t) \in \mathbb{R}^n$ and velocity $v_i(t) \in \mathbb{R}^n$. The update equations blend inertia, cognitive attraction toward personal best positions, and social attraction toward the global swarm best, inducing collective exploration patterns that exhibit emergent properties analogous to bird flocking and fish schooling. Unlike genetic algorithms, particle swarms maintain continuous real-valued representations and exploit gradient-free local search through velocity momentum.

Bayesian optimization occupies the apex of sample-efficient global optimization for expensive black-box functions $f: \mathcal{X} \to \mathbb{R}$ where each evaluation requires substantial computational or experimental cost (computational fluid dynamics simulations, hyperparameter training runs, physical chemistry experiments). The algorithm maintains a probabilistic surrogate model—typically a Gaussian process $\mathcal{GP}(\mu, k)$ with mean function $\mu(x)$ and kernel $k(x, x')$—that provides both a predictive mean $\hat{f}(x)$ and uncertainty quantification $\sigma(x)$ at every unevaluated point. An acquisition function $\alpha(x)$ such as Expected Improvement, Upper Confidence Bound, or Knowledge Gradient balances exploitation of regions with high predicted values against exploration of regions with high uncertainty, converting the intractable global optimization problem into a sequence of tractable acquisition function optimizations.

The unifying mathematical invariant across all stochastic optimization methods emerges from martingale convergence theory and stochastic approximation. For iterative stochastic algorithms of the form $x_{t+1} = x_t - \alpha_t g_t$ where $g_t$ represents a noisy gradient or search direction, convergence demands that the step sizes $\{\alpha_t\}$ satisfy the Robbins-Monro conditions: $\sum_{t=1}^\infty \alpha_t = \infty$ to ensure sufficient exploration and $\sum_{t=1}^\infty \alpha_t^2 < \infty$ to guarantee that accumulated noise remains bounded. Under additional technical conditions—unbiased gradient estimates $\mathbb{E}[g_t | \mathcal{F}_t] = \nabla f(x_t)$, bounded variance $\mathbb{E}[\|g_t - \nabla f(x_t)\|^2 | \mathcal{F}_t] \le \sigma^2$, and Lipschitz smoothness of $f$—the iterates $x_t$ converge almost surely to stationary points where $\nabla f(x^*) = 0$.

The formal statement requires measure-theoretic precision. Let $(\Omega, \mathcal{F}, \mathbb{P})$ denote the underlying probability space and $\{\mathcal{F}_t\}$ the natural filtration encoding the history of random choices. The sequence $\{x_t\}$ forms a stochastic process adapted to $\mathcal{F}_t$. Define the Lyapunov function $V(x) = f(x) - f^* \ge 0$ where $f^*$ denotes the global minimum value. Under the Robbins-Monro conditions and smoothness assumptions, we establish the supermartingale convergence result:

$$\mathbb{E}[V(x_{t+1}) | \mathcal{F}_t] \le V(x_t) - \alpha_t \|\nabla f(x_t)\|^2 + \frac{L \alpha_t^2 \sigma^2}{2}$$

where $L$ denotes the Lipschitz constant of $\nabla f$. Summing this telescoping inequality from $t=0$ to $T-1$ and applying the tower property of conditional expectation yields:

$$\sum_{t=0}^{T-1} \alpha_t \mathbb{E}[\|\nabla f(x_t)\|^2] \le V(x_0) - \mathbb{E}[V(x_T)] + \frac{L \sigma^2}{2} \sum_{t=0}^{T-1} \alpha_t^2 < \infty$$

Since $\sum_{t=0}^\infty \alpha_t = \infty$ and the left-hand side remains bounded, we conclude that $\liminf_{t \to \infty} \mathbb{E}[\|\nabla f(x_t)\|^2] = 0$, establishing convergence to stationary points in expectation. Almost sure convergence requires additional measurability arguments from martingale theory, specifically the Doob martingale convergence theorem applied to the supermartingale $V(x_t) - \frac{L \sigma^2}{2} \sum_{s=0}^{t-1} \alpha_s^2$.

This abstract framework unifies the convergence analysis across disparate stochastic methods, though the constants $L$ and $\sigma$ vary dramatically by algorithm class. Variance-reduced methods achieve $\sigma^2 = O(1/n)$ where $n$ denotes the number of training samples, gradient-free metaheuristics incur $\sigma^2 = O(n)$ due to finite-difference gradient estimation in dimension $n$, and Bayesian optimization sidesteps gradient estimation entirely by operating in acquisition function space.


## 2. Core Architecture & Mechanics

### Stochastic Gradient Descent and Minibatch Sampling

Classical stochastic gradient descent addresses the empirical risk minimization problem ubiquitous in statistical learning. Given a training dataset $\{(x_i, y_i)\}_{i=1}^n$ and a parameterized hypothesis class $h_\theta: \mathcal{X} \to \mathcal{Y}$, we seek parameters $\theta^* \in \mathbb{R}^d$ minimizing the average loss:

$$f(\theta) = \frac{1}{n} \sum_{i=1}^n \ell(h_\theta(x_i), y_i)$$

where $\ell: \mathcal{Y} \times \mathcal{Y} \to \mathbb{R}_+$ measures prediction error. The full-batch gradient $\nabla f(\theta) = \frac{1}{n} \sum_{i=1}^n \nabla_\theta \ell(h_\theta(x_i), y_i)$ requires $O(nd)$ arithmetic operations per iteration, rendering gradient descent intractable when $n$ reaches millions or billions of samples in modern deep learning applications.

Stochastic gradient descent samples a single index $i_t \sim \text{Uniform}\{1, \ldots, n\}$ uniformly at random and forms the unbiased gradient estimator:

$$g_t = \nabla_\theta \ell(h_\theta(x_{i_t}), y_{i_t})$$

The unbiasedness follows immediately from linearity of expectation: $\mathbb{E}_{i_t}[g_t] = \frac{1}{n} \sum_{i=1}^n \nabla_\theta \ell(h_\theta(x_i), y_i) = \nabla f(\theta)$. However, the variance grows as the number of samples increases. If we denote $g_i = \nabla_\theta \ell(h_\theta(x_i), y_i)$, then:

$$\text{Var}(g_t) = \mathbb{E}[\|g_t - \nabla f(\theta)\|^2] = \frac{1}{n} \sum_{i=1}^n \|g_i - \nabla f(\theta)\|^2$$

This variance directly controls the second term in the supermartingale bound, limiting convergence rates to $O(1/\sqrt{T})$ for non-strongly convex objectives.

Minibatch SGD interpolates between full-batch and single-sample extremes by sampling a batch $\mathcal{B}_t \subset \{1, \ldots, n\}$ of size $b$ and computing:

$$g_t = \frac{1}{b} \sum_{i \in \mathcal{B}_t} \nabla_\theta \ell(h_\theta(x_i), y_i)$$

The variance reduction scales inversely with batch size: $\text{Var}(g_t) = \sigma^2 / b$ where $\sigma^2$ denotes the single-sample variance. The optimal batch size balances variance reduction against computational cost. On modern GPU hardware with massively parallel arithmetic units, small batch sizes underutilize computational resources, while excessively large batches approach full-batch gradient descent, eliminating the exploration benefits of stochasticity. Empirical practice in deep learning typically selects $b \in \{32, 64, 128, 256\}$ based on memory bandwidth constraints and parallelism factors.

The learning rate schedule $\{\alpha_t\}$ critically determines convergence behavior. Constant step sizes $\alpha_t = \alpha$ violate the Robbins-Monro condition $\sum \alpha_t^2 < \infty$, causing iterates to oscillate indefinitely within a ball of radius $O(\alpha \sigma)$ around stationary points rather than converging. Practitioners employ several principled schedules:

The polynomial decay schedule $\alpha_t = \alpha_0 / (1 + t)^\gamma$ with $\gamma \in (0.5, 1]$ satisfies Robbins-Monro conditions and achieves convergence rate $O(1/t^{1-\gamma})$ for strongly convex functions. The exponential decay schedule $\alpha_t = \alpha_0 \exp(-\lambda t)$ decreases more aggressively, reaching machine precision neighborhoods faster but risking premature convergence to suboptimal stationary points in non-convex landscapes.

Step-decay or piecewise-constant schedules multiply the learning rate by a factor $\rho \in (0, 1)$ every $k$ epochs: $\alpha_t = \alpha_0 \rho^{\lfloor t/k \rfloor}$. These schedules dominate modern deep learning practice despite violating theoretical convergence conditions, justified by empirical observation that discrete step reductions enable escape from flat regions and saddle points through sudden injections of exploration.

Momentum acceleration augments SGD with exponential moving averages of past gradients, effectively treating optimization as overdamped Langevin dynamics in a viscous medium. The Polyak momentum update maintains a velocity vector $v_t \in \mathbb{R}^d$:

$$v_{t+1} = \beta v_t + g_t$$
$$\theta_{t+1} = \theta_t - \alpha_t v_{t+1}$$

where $\beta \in [0, 1)$ controls the momentum decay rate. The velocity accumulates gradient history with exponentially decaying weights $\{\beta^k\}_{k=0}^\infty$, accelerating convergence in directions of consistent gradient and dampening oscillations in directions of high curvature.

Nesterov accelerated gradient refines momentum by evaluating the gradient at the lookahead position $\theta_t - \beta v_t$ rather than the current position $\theta_t$:

$$v_{t+1} = \beta v_t + \nabla f(\theta_t - \beta v_t)$$
$$\theta_{t+1} = \theta_t - \alpha v_{t+1}$$

This seemingly minor modification yields provable acceleration for convex objectives, achieving convergence rate $O(1/t^2)$ compared to $O(1/t)$ for standard gradient descent. The intuition appeals to physics: by evaluating the gradient at the anticipated future position, Nesterov momentum implements a form of predictive control that prevents overshooting minima.

### Variance Reduction: SVRG and SAGA

Variance-reduced gradient methods achieve the sample complexity of full-batch gradient descent while maintaining the per-iteration cost of stochastic gradient descent—a seemingly impossible feat made possible through careful gradient table bookkeeping. The key insight recognizes that the high variance in stochastic gradients stems from the randomness of sampling, which can be reduced by subtracting a correction term that removes systematic bias.

Stochastic Variance Reduced Gradient (SVRG) operates in epochs indexed by $s = 0, 1, 2, \ldots$. At the beginning of epoch $s$, the algorithm computes the full-batch gradient $\tilde{\mu}_s = \frac{1}{n} \sum_{i=1}^n \nabla_\theta \ell(h_{\tilde{\theta}_s}(x_i), y_i)$ at a snapshot parameter $\tilde{\theta}_s$ and stores it. During the epoch, SVRG performs $m$ inner iterations with the variance-reduced gradient estimator:

$$g_t = \nabla_\theta \ell(h_{\theta_t}(x_{i_t}), y_{i_t}) - \nabla_\theta \ell(h_{\tilde{\theta}_s}(x_{i_t}), y_{i_t}) + \tilde{\mu}_s$$

The correction term $\nabla_\theta \ell(h_{\tilde{\theta}_s}(x_{i_t}), y_{i_t}) - \tilde{\mu}_s$ has expectation zero by construction, canceling the variance introduced by sampling. The variance of $g_t$ satisfies:

$$\mathbb{E}[\|g_t - \nabla f(\theta_t)\|^2] \le 2L^2 \|\theta_t - \tilde{\theta}_s\|^2$$

where $L$ denotes the Lipschitz constant of individual gradients $\nabla_\theta \ell$. This variance bound depends quadratically on the distance to the snapshot parameter rather than on any intrinsic noise level, vanishing as $\theta_t$ approaches $\tilde{\theta}_s$. For strongly convex functions with condition number $\kappa = L/\mu$, SVRG achieves linear convergence rate $\mathbb{E}[f(\theta_T) - f^*] \le \rho^T (f(\theta_0) - f^*)$ with $\rho = 1/(2\kappa)$, provided the epoch length $m$ and step size $\alpha$ satisfy $\alpha \le 1/(10L)$ and $m \ge 10\kappa$.

The epoch structure imposes a computational pattern that alternates between full-gradient computation and stochastic inner iterations. Let $T_{\text{epoch}}$ denote the wall-clock time for one epoch. The full-gradient computation requires $O(nd)$ operations, while $m$ inner iterations each require $O(d)$ operations. The total cost per epoch is $O((n+m)d)$. For linear convergence, we require $m = \Theta(\kappa)$, yielding per-epoch cost $O((n + \kappa)d)$. When $\kappa \ll n$, SVRG achieves dramatic speedups over full-batch gradient descent, which requires $O(\kappa nd)$ total operations to reach $\epsilon$ accuracy.

SAGA (a variance-reduced generalization whose acronym playfully references the long saga of variance reduction research) eliminates the epoch structure entirely through a gradient table mechanism. The algorithm maintains an $n \times d$ table $\phi_i \in \mathbb{R}^d$ storing the most recently computed gradient for each training sample. At iteration $t$, SAGA samples index $i_t$, computes the current gradient $g_{i_t} = \nabla_\theta \ell(h_{\theta_t}(x_{i_t}), y_{i_t})$, and forms the variance-reduced estimator:

$$v_t = g_{i_t} - \phi_{i_t} + \frac{1}{n} \sum_{j=1}^n \phi_j$$

The table is then updated: $\phi_{i_t} \gets g_{i_t}$. The average gradient $\bar{\phi}_t = \frac{1}{n} \sum_{j=1}^n \phi_j$ can be maintained incrementally using the update $\bar{\phi}_{t+1} = \bar{\phi}_t + \frac{1}{n}(g_{i_t} - \phi_{i_t})$, reducing the per-iteration cost from $O(nd)$ to $O(d)$ after paying the initial $O(nd)$ table initialization cost.

SAGA achieves the same linear convergence rate as SVRG without requiring epoch boundaries or full-gradient computations, at the cost of maintaining the gradient table in memory—a space complexity of $O(nd)$ that becomes prohibitive when $n$ exceeds millions of samples or $d$ exceeds billions of parameters. The convergence analysis appeals to the observation that as $\theta_t$ approaches the optimum $\theta^*$, the gradients $g_i$ stored in the table also approach their optimal values $\nabla_\theta \ell(h_{\theta^*}(x_i), y_i)$, causing the table average $\bar{\phi}_t$ to converge to the true full-gradient $\nabla f(\theta^*)$.

The variance of the SAGA estimator admits the bound:

$$\mathbb{E}[\|v_t - \nabla f(\theta_t)\|^2] \le \frac{2L^2}{n} \sum_{i=1}^n \|\theta_t - \theta_t^{(i)}\|^2$$

where $\theta_t^{(i)}$ denotes the parameter value at which $\phi_i$ was last computed. This bound reveals that SAGA's variance decreases as the table entries become more current, establishing an implicit coupling between parameter convergence and table freshness.

Both SVRG and SAGA extend to non-strongly convex objectives with convergence rate $O(1/T)$—faster than SGD's $O(1/\sqrt{T})$ but slower than the linear rate for strongly convex functions. The practical impact on deep learning remains contested: while variance reduction delivers substantial speedups on convex objectives like logistic regression and linear SVMs, neural network training often benefits more from the implicit regularization induced by SGD's sustained noise, which prevents overfitting by maintaining exploration throughout training.

### Simulated Annealing and the Metropolis-Hastings Criterion

Simulated annealing transposes optimization into the language of statistical mechanics and thermodynamics, modeling the search for global minima as the physical process of annealing—heating a material to high temperature and slowly cooling it to minimize internal energy through crystalline ordering. The analogy maps the objective function $f: \mathcal{X} \to \mathbb{R}$ to an energy function $E(x)$, candidate solutions $x \in \mathcal{X}$ to atomic configurations, and the optimization process to thermal equilibration at progressively decreasing temperatures.

At fixed temperature $T > 0$, the Boltzmann-Gibbs distribution assigns probability:

$$\pi_T(x) = \frac{1}{Z(T)} \exp\left(-\frac{f(x)}{T}\right)$$

where $Z(T) = \sum_{x \in \mathcal{X}} \exp(-f(x)/T)$ denotes the partition function (for discrete spaces) or $Z(T) = \int_{\mathcal{X}} \exp(-f(x)/T) \, dx$ for continuous spaces. The temperature parameter controls exploration: at high temperatures $T \to \infty$, the distribution flattens to uniform $\pi_T(x) \approx 1/|\mathcal{X}|$, assigning equal probability to all configurations regardless of objective value. As temperature approaches zero $T \to 0^+$, the distribution concentrates exponentially on global minima: $\pi_T(x) \to \mathbb{1}_{x \in \arg\min f}(x) / |\arg\min f|$.

The Metropolis-Hastings algorithm generates samples from $\pi_T$ through a Markov chain with stationary distribution $\pi_T$. Given current state $x_t$, the algorithm proposes a candidate $x'$ from a symmetric proposal distribution $q(x' | x_t)$ satisfying $q(x' | x) = q(x | x')$ (typically a Gaussian random walk $x' = x_t + \mathcal{N}(0, \sigma^2 I)$ for continuous spaces). The candidate is accepted with probability:

$$\alpha(x_t, x') = \min\left\{1, \exp\left(-\frac{f(x') - f(x_t)}{T}\right)\right\}$$

If accepted, set $x_{t+1} = x'$; otherwise, set $x_{t+1} = x_t$. This acceptance criterion implements detailed balance: the probability flux from state $x$ to state $x'$ equals the reverse flux from $x'$ to $x$, guaranteeing that $\pi_T$ remains stationary under the Markov chain dynamics.

The acceptance rule admits a simple interpretation: improvements $f(x') < f(x_t)$ are always accepted ($\alpha = 1$), while deteriorations $f(x') > f(x_t)$ are accepted with probability $\exp(-(f(x') - f(x_t))/T)$, allowing occasional uphill moves that prevent entrapment in local minima. The acceptance probability for deteriorations decays exponentially with the magnitude of worsening $\Delta f = f(x') - f(x_t)$ and decreases as temperature cools.

Simulated annealing embeds this Metropolis-Hastings sampler within a cooling schedule $T(t)$ that gradually reduces temperature over iterations. The classical convergence theorem, due to Hajek, establishes that logarithmic cooling $T(t) = c / \log(1 + t)$ guarantees convergence to global minima with probability one, provided the constant $c$ exceeds a threshold determined by the depth of the deepest local minimum trap:

$$c \ge \max_{x \in \mathcal{L}} \min_{\text{path } x \to \mathcal{G}} \max_{y \in \text{path}} (f(y) - f(x))$$

where $\mathcal{L}$ denotes the set of local minima and $\mathcal{G}$ denotes the set of global minima. This constant $c$ measures the height of the tallest barrier that must be surmounted to escape from any local minimum to reach a global minimum—a quantity that is generically intractable to compute for arbitrary objective functions.

The logarithmic cooling schedule purchases theoretical convergence guarantees at the cost of impractical convergence times. To achieve error probability $\epsilon$, logarithmic cooling requires $T = \Omega(\exp(c/\epsilon))$ iterations—exponential in the inverse error tolerance. Practical implementations employ much more aggressive cooling schedules such as geometric cooling $T(t) = T_0 \rho^t$ with $\rho \in (0.8, 0.99)$ or linear cooling $T(t) = T_0 - \gamma t$, sacrificing provable global convergence for acceptable finite-time performance.

The proposal distribution $q(x' | x)$ critically impacts exploration efficiency. Gaussian random walks with fixed variance $\sigma^2$ face a dilemma: small variance $\sigma^2 \to 0$ yields high acceptance rates but slow mixing due to local diffusion, while large variance $\sigma^2 \to \infty$ enables long-distance jumps but incurs low acceptance rates that waste computation. Adaptive proposal mechanisms adjust $\sigma^2(t)$ during the search to maintain target acceptance rates around $0.23$ for high-dimensional spaces (a value derived from optimal scaling theory in Markov chain Monte Carlo).

Simulated annealing excels on combinatorial optimization problems with discrete solution spaces—traveling salesman tours, graph colorings, VLSI circuit placement—where gradient information is unavailable and the discrete topology precludes gradient-free finite-difference estimation. The algorithm's ability to accept occasional deteriorations enables escape from local minima that trap hill-climbing heuristics, while the cooling schedule ensures ultimate convergence to high-quality solutions.

### Genetic Algorithms and the Schema Theorem

Genetic algorithms model optimization as Darwinian evolution, encoding candidate solutions as finite strings (chromosomes) in an alphabet $\Sigma$ and applying biologically-inspired operators—selection, crossover, mutation—to iteratively improve population fitness. The algorithm maintains a population $\mathcal{P}_t = \{x_1^{(t)}, \ldots, x_N^{(t)}\}$ of $N$ individuals $x_i \in \Sigma^n$ and iterates through generations $t = 0, 1, 2, \ldots$ according to the following cycle.

Selection samples individuals for reproduction with probability proportional to fitness $f(x_i)$. Fitness-proportionate selection implements a discrete probability distribution $p_i = f(x_i) / \sum_{j=1}^N f(x_j)$, ensuring that high-fitness individuals contribute more offspring to the next generation. Tournament selection randomly samples $k$ individuals and selects the fittest among them, providing a tunable selection pressure controlled by tournament size $k$. Rank-based selection sorts individuals by fitness and assigns selection probabilities based on rank rather than raw fitness values, preventing premature convergence when a single superfit individual dominates the population.

Crossover exchanges genetic material between two parent chromosomes $x, y \in \Sigma^n$ to produce offspring. Single-point crossover selects a random cut position $c \sim \text{Uniform}\{1, \ldots, n-1\}$ and forms offspring by concatenating the prefix of one parent with the suffix of the other:

$$x' = x[1:c] \oplus y[c+1:n]$$
$$y' = y[1:c] \oplus x[c+1:n]$$

where $\oplus$ denotes concatenation. Two-point crossover generalizes this by selecting two cut positions $c_1 < c_2$ and swapping the segment between them. Uniform crossover treats each locus independently, selecting offspring alleles from parents with equal probability: $x'[i] \in \{x[i], y[i]\}$ with probability $1/2$ each.

Mutation introduces variation by randomly perturbing alleles with small probability $p_m \ll 1$. For binary alphabets $\Sigma = \{0, 1\}$, mutation flips each bit independently with probability $p_m$. For real-valued chromosomes $x \in \mathbb{R}^n$, mutation adds Gaussian noise: $x'[i] = x[i] + \mathcal{N}(0, \sigma_m^2)$. The mutation rate balances exploration against exploitation: excessive mutation $p_m \to 1$ reduces the algorithm to random search, while insufficient mutation $p_m \to 0$ risks population convergence to local optima with insufficient genetic diversity to escape.

The schema theorem, proven by John Holland, provides a theoretical foundation for genetic algorithm convergence by analyzing the dynamics of schemata—hyperplane partitions of the solution space defined by fixed allele values at a subset of loci. A schema $H$ is represented as a string over the extended alphabet $\Sigma \cup \{*\}$ where $*$ denotes a wildcard matching any allele. For example, the binary schema $H = 1*0**1$ matches all 6-bit strings beginning with $1$, containing $0$ in the third position, and ending with $1$.

The defining length $\delta(H)$ measures the distance between the first and last fixed positions in $H$, while the order $o(H)$ counts the number of fixed positions. Single-point crossover disrupts schema $H$ with probability approximately $\delta(H) / (n-1)$: if the crossover point falls within the defining length, the schema may be broken. Mutation disrupts $H$ with probability approximately $1 - (1 - p_m)^{o(H)} \approx o(H) p_m$ for small $p_m$.

Let $m(H, t)$ denote the number of individuals matching schema $H$ in generation $t$, and let $\bar{f}(H, t)$ denote the average fitness of those individuals. The schema theorem states that under fitness-proportionate selection, single-point crossover with rate $p_c$, and bitwise mutation with rate $p_m$:

$$\mathbb{E}[m(H, t+1)] \ge m(H, t) \cdot \frac{\bar{f}(H, t)}{\bar{f}(t)} \cdot \left(1 - p_c \frac{\delta(H)}{n-1} - o(H) p_m\right)$$

where $\bar{f}(t)$ denotes the population average fitness. Schemata with above-average fitness $\bar{f}(H, t) > \bar{f}(t)$, short defining length $\delta(H) \ll n$, and low order $o(H) \ll n$ receive exponentially increasing trials in successive generations. These short, low-order, high-fitness schemata constitute building blocks that genetic algorithms implicitly assemble into complete high-fitness solutions.

The implicit parallelism hypothesis asserts that despite evaluating only $N$ individuals per generation, the genetic algorithm processes information about approximately $N^3$ schemata through their implicit representation in the population. This claim relies on the observation that each individual $x \in \Sigma^n$ participates in $2^n$ binary schemata (one for each subset of positions), and selection acts on schema averages aggregated across the population.

Critics note that the schema theorem provides only a lower bound on expected schema counts and assumes fitness-proportionate selection, which practitioners rarely use due to scaling issues. Moreover, the building block hypothesis fails for deceptive fitness landscapes where low-order schemata mislead the search toward local optima. The Royal Road functions, introduced by Mitchell and Holland, provide tractable test problems where building blocks compose hierarchically, though real optimization landscapes rarely exhibit such convenient structure.

### Particle Swarm Optimization

Particle swarm optimization models the search process as collective motion of a swarm of particles traversing the solution space $\mathcal{X} \subseteq \mathbb{R}^n$. Each particle $i \in \{1, \ldots, N\}$ maintains position $x_i(t) \in \mathbb{R}^n$ and velocity $v_i(t) \in \mathbb{R}^n$ that evolve according to kinematic update equations blending inertia, cognitive attraction, and social attraction.

At each iteration $t$, each particle remembers its personal best position $p_i = \arg\min_{\tau \le t} f(x_i(\tau))$ and has access to the global best position $g = \arg\min_{i,\tau \le t} f(x_i(\tau))$ achieved by any particle. The velocity update combines three components:

$$v_i(t+1) = \omega v_i(t) + c_1 r_1 \odot (p_i - x_i(t)) + c_2 r_2 \odot (g - x_i(t))$$

where $\omega \in [0, 1]$ is the inertia weight, $c_1, c_2 > 0$ are cognitive and social acceleration coefficients, $r_1, r_2 \sim \text{Uniform}(0, 1)^n$ are random vectors with independent uniform components, and $\odot$ denotes componentwise multiplication. The position updates via:

$$x_i(t+1) = x_i(t) + v_i(t+1)$$

The inertia term $\omega v_i(t)$ prevents abrupt velocity changes, maintaining search momentum and enabling particles to overshoot local minima. The cognitive term $c_1 r_1 \odot (p_i - x_i(t))$ attracts the particle toward its personal best, exploiting the particle's individual search history. The social term $c_2 r_2 \odot (g - x_i(t))$ attracts the particle toward the global best, enabling information sharing across the swarm.

The random vectors $r_1, r_2$ inject stochasticity that prevents premature convergence and enables exploration of diverse search directions. The componentwise multiplication ensures that each dimension receives independent random scaling, allowing the swarm to navigate axis-aligned valleys and ridges.

The parameter selection $(\omega, c_1, c_2)$ controls the balance between exploration and exploitation. The original formulation by Kennedy and Eberhart used $\omega = 1$, $c_1 = c_2 = 2$, yielding explosive dynamics that could send particles far from the current best positions. Later analysis by Clerc and Kennedy derived the constriction coefficient $\chi$ ensuring convergence to stable fixed points:

$$\chi = \frac{2}{|2 - \varphi - \sqrt{\varphi^2 - 4\varphi}|}$$

where $\varphi = c_1 + c_2 > 4$. Typical values are $\varphi = 4.1$, yielding $\chi \approx 0.729$. The constricted velocity update scales the entire expression by $\chi$:

$$v_i(t+1) = \chi \left[\omega v_i(t) + c_1 r_1 \odot (p_i - x_i(t)) + c_2 r_2 \odot (g - x_i(t))\right]$$

The stability analysis treats the stochastic update as a deterministic difference equation with expected values $\mathbb{E}[r_1] = \mathbb{E}[r_2] = 0.5 \cdot \mathbf{1}$, yielding the deterministic skeleton:

$$v_i(t+1) = \omega v_i(t) + 0.5 c_1 (p_i - x_i(t)) + 0.5 c_2 (g - x_i(t))$$
$$x_i(t+1) = x_i(t) + v_i(t+1)$$

Writing $u_i(t) = x_i(t) - g$ and combining equations yields a second-order difference equation for the deviation from the global best:

$$u_i(t+2) = (1 + \omega - 0.5 c_1 - 0.5 c_2) u_i(t+1) - \omega u_i(t) + 0.5 c_1 (p_i - g)$$

Stability requires the characteristic polynomial $\lambda^2 - (1 + \omega - 0.5 c_1 - 0.5 c_2) \lambda + \omega = 0$ to have roots inside the unit circle, imposing constraints on $(\omega, c_1, c_2)$ that the constriction coefficient $\chi$ satisfies.

Topology variants generalize the global best $g$ to neighborhood bests, enabling more gradual information diffusion across the swarm. The ring topology connects particles in a circular graph, with each particle attracted only to the best position within its local neighborhood of radius $k$. The von Neumann topology arranges particles on a 2D grid with each particle influenced by its four cardinal neighbors. These topologies trade convergence speed for population diversity: global topology induces rapid convergence but risks premature consensus on suboptimal regions, while local topologies maintain diverse subswarms exploring different basins.

Particle swarm optimization excels on continuous, moderate-dimensional problems $n \lesssim 100$ with multimodal landscapes. The collective dynamics exhibit emergent exploration patterns that balance individual particle exploitation with swarm-wide information sharing. However, the lack of gradient information renders PSO inefficient on high-dimensional convex problems where gradient-based methods dominate, and the position-based update rules struggle on discrete combinatorial spaces where genetic algorithms and simulated annealing prove more natural.

### Bayesian Optimization and Gaussian Process Surrogates

Bayesian optimization addresses the expensive black-box optimization problem: minimize $f: \mathcal{X} \to \mathbb{R}$ subject to a stringent budget $T$ on the number of function evaluations, where each evaluation $f(x)$ requires substantial computational or experimental cost (hours for computational fluid dynamics simulations, days for hyperparameter training of large neural networks, weeks for physical chemistry experiments). The algorithm proceeds sequentially: at iteration $t$, given observations $\mathcal{D}_t = \{(x_i, y_i)\}_{i=1}^t$ where $y_i = f(x_i) + \epsilon_i$ with noise $\epsilon_i \sim \mathcal{N}(0, \sigma_n^2)$, select the next query point $x_{t+1}$ to maximize information gain about the global optimum.

Bayesian optimization maintains a probabilistic surrogate model $p(f | \mathcal{D}_t)$ encoding beliefs about the unknown function $f$. The Gaussian process prior $f \sim \mathcal{GP}(\mu_0, k)$ specifies a mean function $\mu_0: \mathcal{X} \to \mathbb{R}$ and positive-definite kernel (covariance function) $k: \mathcal{X} \times \mathcal{X} \to \mathbb{R}$. The kernel encodes smoothness assumptions: the widely-used squared exponential (RBF) kernel:

$$k(x, x') = \sigma_f^2 \exp\left(-\frac{\|x - x'\|^2}{2\ell^2}\right)$$

generates infinitely differentiable sample paths with correlation length scale $\ell$ and marginal variance $\sigma_f^2$. The Matérn kernel family:

$$k_\nu(x, x') = \sigma_f^2 \frac{2^{1-\nu}}{\Gamma(\nu)} \left(\sqrt{2\nu} \frac{\|x - x'\|}{\ell}\right)^\nu K_\nu\left(\sqrt{2\nu} \frac{\|x - x'\|}{\ell}\right)$$

interpolates between different smoothness levels controlled by $\nu$: $\nu = 1/2$ yields the Ornstein-Uhlenbeck process (once mean-square differentiable), $\nu = 3/2$ yields once differentiable paths, and $\nu \to \infty$ recovers the squared exponential kernel.

Given observations $\mathcal{D}_t$, the posterior distribution $p(f | \mathcal{D}_t)$ remains a Gaussian process with updated mean $\mu_t(x)$ and covariance $k_t(x, x')$. Let $\mathbf{K}$ denote the $t \times t$ Gram matrix with entries $K_{ij} = k(x_i, x_j) + \sigma_n^2 \delta_{ij}$, let $\mathbf{k}(x)$ denote the $t$-dimensional vector with entries $k_i(x) = k(x_i, x)$, and let $\mathbf{y} = (y_1, \ldots, y_t)^\top$. The posterior mean and variance at arbitrary input $x \in \mathcal{X}$ are:

$$\mu_t(x) = \mu_0(x) + \mathbf{k}(x)^\top \mathbf{K}^{-1} (\mathbf{y} - \mu_0(\mathbf{x}))$$
$$\sigma_t^2(x) = k(x, x) - \mathbf{k}(x)^\top \mathbf{K}^{-1} \mathbf{k}(x)$$

The posterior mean $\mu_t(x)$ interpolates the observations when $\sigma_n = 0$ (noiseless case) and provides a smooth regression fit when $\sigma_n > 0$. The posterior variance $\sigma_t^2(x)$ quantifies epistemic uncertainty: $\sigma_t^2(x) \to 0$ at observed points $x \in \{x_1, \ldots, x_t\}$ and increases with distance from observations.

The acquisition function $\alpha: \mathcal{X} \to \mathbb{R}$ converts the posterior distribution into a selection criterion for the next query point $x_{t+1} = \arg\max_{x \in \mathcal{X}} \alpha(x; \mathcal{D}_t)$. Expected Improvement (EI) quantifies the expected amount by which querying $x$ improves upon the current best observation $y^+ = \min_{i \le t} y_i$:

$$\alpha_{\text{EI}}(x) = \mathbb{E}[\max\{y^+ - f(x), 0\} | \mathcal{D}_t]$$

Under the Gaussian process posterior, $f(x) | \mathcal{D}_t \sim \mathcal{N}(\mu_t(x), \sigma_t^2(x))$, enabling closed-form evaluation:

$$\alpha_{\text{EI}}(x) = \begin{cases}
(y^+ - \mu_t(x)) \Phi(Z) + \sigma_t(x) \phi(Z) & \text{if } \sigma_t(x) > 0 \\
0 & \text{if } \sigma_t(x) = 0
\end{cases}$$

where $Z = (y^+ - \mu_t(x)) / \sigma_t(x)$, $\Phi$ denotes the standard normal CDF, and $\phi$ denotes the standard normal PDF. Expected Improvement balances exploitation (large negative $\mu_t(x)$ predicts low objective values) against exploration (large $\sigma_t(x)$ indicates high uncertainty).

Upper Confidence Bound (UCB) acquisition adds a multiple of the posterior standard deviation to the posterior mean:

$$\alpha_{\text{UCB}}(x) = -\mu_t(x) + \beta_t^{1/2} \sigma_t(x)$$

where $\beta_t = 2 \log(t^{n/2 + 2} \pi^2 / (3\delta))$ for high-probability regret bounds with confidence parameter $\delta$. The negative sign accounts for minimization: UCB favors regions with low predicted values or high uncertainty. Larger $\beta_t$ increases exploration emphasis.

Knowledge Gradient measures the expected improvement in the posterior minimum after observing $x$:

$$\alpha_{\text{KG}}(x) = \mathbb{E}[\min_{x' \in \mathcal{X}} \mu_{t+1}(x') - \min_{x' \in \mathcal{X}} \mu_t(x') | \mathcal{D}_t, x_{t+1} = x]$$

This acquisition function requires nested optimization (optimizing $\mu_{t+1}$ over $\mathcal{X}$ for each candidate $x$), rendering it computationally expensive but provably optimal under certain problem classes.

Bayesian optimization achieves sublinear Bayesian simple regret $r_T = \mathbb{E}[f(x_{t^*}) - f(x^*)]$ where $x_{t^*}$ denotes the best-observed point after $T$ iterations and $x^*$ denotes the global optimum. Under smoothness assumptions encoded by the kernel's reproducing kernel Hilbert space (RKHS), UCB achieves regret bound:

$$r_T \le C \sqrt{\frac{\log T}{T}} \cdot \|f\|_{\mathcal{H}}$$

where $\mathcal{H}$ denotes the RKHS associated with kernel $k$ and $C$ depends on the kernel parameters. This $O(1/\sqrt{T})$ rate matches the minimax lower bound for black-box optimization under RKHS smoothness assumptions.

The computational bottleneck lies in solving the acquisition function optimization $x_{t+1} = \arg\max_x \alpha(x)$, which itself constitutes a non-convex global optimization problem. Multi-start local optimization samples $M$ random initial points and runs gradient-based optimization (BFGS, L-BFGS) from each, selecting the best result. Evolutionary strategies and random search provide gradient-free alternatives when acquisition function gradients are unavailable.

Hyperparameter learning adapts the kernel parameters $\theta = (\sigma_f, \ell, \sigma_n)$ by maximizing the marginal likelihood (evidence):

$$\log p(\mathbf{y} | \mathbf{X}, \theta) = -\frac{1}{2} \mathbf{y}^\top \mathbf{K}^{-1} \mathbf{y} - \frac{1}{2} \log|\mathbf{K}| - \frac{t}{2} \log(2\pi)$$

Gradient-based optimization with respect to $\theta$ adapts the model to observed data, though this introduces non-convexity and potential overfitting when $t$ is small.

Bayesian optimization excels on low-to-moderate dimensional problems $n \lesssim 20$ with expensive function evaluations and budgets $T \in [50, 500]$. Applications include hyperparameter tuning for machine learning models, protein structure optimization, material science design, and robotics controller synthesis. The method struggles with high dimensions $n \gg 20$ due to the exponential scaling of Gaussian process inference and the curse of dimensionality affecting acquisition function optimization.


## 3. High-Performance Optimization & Failure Modes

### Minibatch Size Selection and Gradient Noise Calibration

The minibatch size $b$ critically determines both computational throughput and statistical efficiency in stochastic gradient descent. Modern GPU architectures achieve peak FLOP/s utilization when arithmetic intensity (FLOP per byte of memory traffic) matches the hardware's operational intensity threshold. For matrix-matrix multiplication executing backpropagation through dense layers, arithmetic intensity scales as $O(b)$ while memory bandwidth requirements scale as $O(d)$, causing small batch sizes to become memory-bandwidth bound rather than compute-bound.

The roofline model quantifies this trade-off by plotting achieved FLOP/s against arithmetic intensity, revealing performance ceilings imposed by either peak compute throughput or memory bandwidth. For NVIDIA A100 GPUs with peak compute 19.5 TFLOP/s (FP32) and memory bandwidth 1.6 TB/s, the operational intensity threshold sits at $19.5 / 1.6 \approx 12$ FLOP/byte. Training batches must perform at least 12 floating-point operations per byte transferred to saturate compute resources.

Gradient noise scale diagnostics quantify the effective batch size beyond which increasing $b$ yields diminishing returns. Define the gradient signal-to-noise ratio:

$$\text{SNR} = \frac{\|\mathbb{E}[g_t]\|^2}{\mathbb{E}[\|g_t - \mathbb{E}[g_t]\|^2]} = \frac{\|\nabla f(\theta_t)\|^2}{\text{Var}(g_t)}$$

and the simple gradient noise scale $B_{\text{simple}} = \text{SNR}$. The noise scale $B_{\text{simple}}$ estimates the batch size at which gradient variance equals gradient magnitude squared. For batch size $b \ll B_{\text{simple}}$, gradient noise dominates signal, while for $b \gg B_{\text{simple}}$, additional samples provide marginal variance reduction.

McCandlish et al. establish that training time $t_{\text{train}}(b)$ to reach fixed validation loss scales as:

$$t_{\text{train}}(b) \approx t_0 \left(1 + \frac{B_{\text{noise}}}{b}\right)$$

where $B_{\text{noise}}$ denotes the critical batch size (related to but distinct from $B_{\text{simple}}$) and $t_0$ denotes the asymptotic training time as $b \to \infty$. This relationship reveals that doubling batch size from $b = B_{\text{noise}}/4$ to $b = B_{\text{noise}}/2$ halves training time, but doubling from $b = 4B_{\text{noise}}$ to $b = 8B_{\text{noise}}$ yields only marginal speedup.

The learning rate $\alpha$ must scale proportionally with batch size to maintain fixed expected parameter update magnitude. The linear scaling rule $\alpha(b) = \alpha_{\text{base}} \cdot (b / b_{\text{base}})$ preserves the expected parameter change $\mathbb{E}[\Delta \theta] = -\alpha \nabla f(\theta)$, though higher-order effects (curvature interactions, gradient staleness) cause this rule to break down for very large batches $b \gg B_{\text{noise}}$.

Warmup schedules gradually increase learning rate from near-zero to target value over initial iterations to prevent instability when initializing with large batch sizes. The linear warmup schedule increases $\alpha_t = (\alpha_{\text{target}} / t_{\text{warmup}}) \cdot \min\{t, t_{\text{warmup}}\}$ over $t_{\text{warmup}}$ steps before transitioning to standard decay schedules. Warmup prevents explosive gradient norm growth that can occur when large learning rates amplify small gradient estimation errors during early training when parameters remain far from stationary points.

### Adaptive Learning Rates and Diagonal Preconditioning

Adaptive learning rate methods construct per-parameter learning rates by accumulating gradient statistics across iterations, implementing diagonal preconditioning that accelerates convergence in poorly-conditioned directions. AdaGrad maintains sum-of-squared-gradients $s_i(t) = \sum_{\tau=1}^t g_i^2(\tau)$ for each parameter $i$ and adapts the learning rate:

$$\theta_i(t+1) = \theta_i(t) - \frac{\alpha}{\sqrt{s_i(t)} + \epsilon} g_i(t)$$

where $\epsilon \approx 10^{-8}$ provides numerical stability. Parameters with large accumulated gradient squares $s_i(t)$ receive smaller effective learning rates $\alpha / \sqrt{s_i(t)}$, while parameters with consistently small gradients receive larger effective rates. This adaptation automatically handles features appearing at different frequencies in data: rare features receive large updates when they appear, while common features receive small updates to prevent overshooting.

AdaGrad's monotonically increasing accumulators $s_i(t)$ cause learning rates to decay toward zero, eventually halting learning prematurely. RMSprop replaces the sum with an exponential moving average:

$$s_i(t) = \rho s_i(t-1) + (1-\rho) g_i^2(t)$$

with decay rate $\rho \in (0.9, 0.999)$. The exponential weighting emphasizes recent gradients, allowing the algorithm to adapt to non-stationary objectives and recover from suboptimal parameter regions.

Adam (Adaptive Moment Estimation) combines RMSprop's squared-gradient moving average with momentum's gradient moving average:

$$m_i(t) = \beta_1 m_i(t-1) + (1-\beta_1) g_i(t)$$
$$v_i(t) = \beta_2 v_i(t-1) + (1-\beta_2) g_i^2(t)$$

The algorithm applies bias correction to account for zero initialization:

$$\hat{m}_i(t) = m_i(t) / (1 - \beta_1^t)$$
$$\hat{v}_i(t) = v_i(t) / (1 - \beta_2^t)$$

and updates parameters:

$$\theta_i(t+1) = \theta_i(t) - \frac{\alpha}{\sqrt{\hat{v}_i(t)} + \epsilon} \hat{m}_i(t)$$

Standard hyperparameter values are $\beta_1 = 0.9$, $\beta_2 = 0.999$, $\alpha = 0.001$, and $\epsilon = 10^{-8}$. Adam dominates deep learning optimization practice due to its robustness across architectures and minimal hyperparameter tuning requirements.

The convergence analysis of adaptive methods reveals subtle pathologies. Reddi et al. demonstrate that Adam can fail to converge to optimal solutions on simple convex problems due to the exponential moving average's short memory. The pathological example constructs an objective where gradients alternate between large positive and large negative values with period longer than the effective memory window $1/(1-\beta_2) \approx 1000$ steps, causing $v_i(t)$ to underestimate true gradient variance and inflate effective learning rates.

AMSGrad corrects this issue by maintaining the maximum squared gradient seen so far:

$$\hat{v}_i(t) = \max\{\hat{v}_i(t-1), v_i(t)\}$$

guaranteeing that effective learning rates decrease monotonically. However, empirical evaluations show minimal practical difference between Adam and AMSGrad on realistic deep learning benchmarks, suggesting the pathological example represents an edge case rather than a widespread failure mode.

### Temperature Schedules and Acceptance Rates in Simulated Annealing

The cooling schedule $T(t)$ fundamentally determines simulated annealing's exploration-exploitation balance. The logarithmic schedule $T(t) = c / \log(1+t)$ provides asymptotic convergence guarantees but cools so slowly that reaching low temperatures requires impractically many iterations. For fixed computational budget $T_{\text{max}}$ iterations, logarithmic cooling may terminate at temperature $T(T_{\text{max}}) = c / \log(1 + T_{\text{max}})$ that remains too high to concentrate probability mass on global minima.

Geometric cooling $T(t) = T_0 \rho^t$ with $\rho \in (0.9, 0.99)$ aggressively reduces temperature exponentially, reaching low temperatures $T \approx 0$ in $O(\log(1/T))$ iterations. The temperature at iteration $t$ satisfies $T(t) = T_0 \rho^t$, so $t = \log(T/T_0) / \log(\rho)$. For $T_0 = 100$, $T = 10^{-3}$, and $\rho = 0.95$, we require $t \approx \log(10^{-5}) / \log(0.95) \approx 225$ iterations—orders of magnitude faster than logarithmic cooling.

The initial temperature $T_0$ should be chosen such that initial acceptance rates for uphill moves remain high (typically $80\%$ or higher), enabling thorough exploration of the solution space before exploitation begins. The acceptance probability for a deterioration of magnitude $\Delta f$ is $\exp(-\Delta f / T_0)$, so $T_0 \approx \langle\Delta f\rangle / \log(1/p_{\text{accept}})$ where $\langle\Delta f\rangle$ denotes the typical objective change between neighbors and $p_{\text{accept}}$ denotes the target acceptance rate. Adaptive initialization performs a short pilot run at high temperature to estimate $\langle\Delta f\rangle$ from sample transitions.

The final temperature $T_f$ controls solution quality: lower final temperatures produce better solutions at the cost of requiring more iterations to cool. Adaptive cooling schedules adjust $\rho(t)$ based on acceptance rates observed during search. If acceptance rates remain too high (indicating the system has equilibrated at the current temperature), the cooling rate accelerates; if acceptance rates drop precipitously (indicating insufficient equilibration time), cooling slows.

Reheating strategies periodically increase temperature to escape local minima that trap the search. When no improvement occurs for $k_{\text{stagnation}}$ consecutive iterations, the algorithm increases temperature by a fixed multiple or resets to the initial temperature, injecting renewed exploration. Reheating transforms simulated annealing into a multi-restart procedure that explores multiple basins of attraction.

The Metropolis-Hastings acceptance criterion assumes symmetric proposals $q(x' | x) = q(x | x')$. Asymmetric proposals such as Gaussian random walks with temperature-dependent variance $\sigma^2(T)$ require the generalized acceptance probability:

$$\alpha(x, x') = \min\left\{1, \frac{q(x | x')}{q(x' | x)} \exp\left(-\frac{f(x') - f(x)}{T}\right)\right\}$$

to maintain detailed balance. Adaptive proposal mechanisms adjust $\sigma^2(T) \propto T$ to maintain approximately constant acceptance rates as temperature cools, preventing the proposal distribution from becoming too broad (causing excessive rejections) or too narrow (limiting exploration).

### Crossover and Mutation Operators in Genetic Algorithms

The interplay between crossover and mutation determines genetic algorithm exploration efficiency. Crossover exploits building blocks by recombining high-fitness schemata from different individuals, while mutation introduces novel genetic material absent from the current population. High crossover rates $p_c \approx 0.9$ with low mutation rates $p_m \approx 1/n$ emphasize exploitation of existing building blocks, while low crossover rates with high mutation rates emphasize exploration through random perturbation.

Problem structure dictates appropriate operator choices. For additively separable objectives $f(x) = \sum_{i=1}^n f_i(x_i)$ where loci contribute independently, mutation alone suffices since no epistatic interactions require crossover to assemble. For hierarchically decomposable problems where fitness depends on interactions within small groups of loci (building blocks), crossover enables parallel assembly of high-fitness building blocks into complete solutions.

Deceptive problems deliberately mislead genetic algorithms by constructing fitness landscapes where low-order building blocks point toward suboptimal regions while the global optimum requires combinations of low-fitness building blocks. The four-bit fully deceptive function assigns fitness based on Hamming distance to the all-ones string:

$$f(x) = \begin{cases}
4 & \text{if } \|x\|_1 = 4 \\
3 - \|x\|_1 & \text{otherwise}
\end{cases}$$

Every proper subschema of $1111$ has higher average fitness than $1111$ itself, causing selection to drive the population toward $0000$. Deceptive functions demonstrate that the building block hypothesis fails for adversarially constructed landscapes.

Linkage learning techniques automatically identify groups of interacting loci (building blocks) and preserve them during crossover. The linkage tree genetic algorithm (LTGA) constructs a hierarchical clustering of loci based on pairwise mutual information, then performs crossover that respects this clustering by transferring entire linked clusters atomically. The Bayesian optimization algorithm (BOA) learns a Bayesian network representing probabilistic dependencies among loci and samples new individuals from this distribution.

Gray coding transforms binary representations to reduce the impact of Hamming cliffs—adjacent integers whose binary representations differ in many bit positions. The standard binary encoding of integers 7 and 8 is $0111$ and $1000$, differing in all four bits despite numerical proximity. Gray code ensures adjacent integers differ in exactly one bit: $7 \to 0100$, $8 \to 1100$. This encoding prevents crossover from generating offspring with arbitrarily distant fitness values when splitting parent chromosomes encoding numerically close solutions.

### Swarm Diversity and Convergence Monitoring

Particle swarm optimization risks premature convergence when all particles cluster near the global best position $g$, eliminating exploration of alternative basins. The swarm diversity at iteration $t$ quantifies the average distance between particles and the swarm centroid $\bar{x}(t) = \frac{1}{N} \sum_{i=1}^N x_i(t)$:

$$D(t) = \frac{1}{N} \sum_{i=1}^N \|x_i(t) - \bar{x}(t)\|$$

Declining diversity $D(t) \to 0$ signals impending convergence. Adaptive inertia weight strategies increase $\omega$ when diversity drops below a threshold, injecting momentum that disperses particles and renews exploration.

Repulsive particles introduce artificial repulsion between nearby particles to maintain minimum inter-particle distances. The modified velocity update adds a repulsion term:

$$v_i(t+1) = \omega v_i(t) + c_1 r_1 \odot (p_i - x_i(t)) + c_2 r_2 \odot (g - x_i(t)) + c_3 \sum_{j \ne i} \frac{x_i(t) - x_j(t)}{\|x_i(t) - x_j(t)\|^3}$$

where $c_3 > 0$ controls repulsion strength. The inverse-cube repulsion mimics electrostatic forces, preventing particle collapse while preserving attraction to promising regions.

Niching techniques partition the swarm into subswarms exploring different basins of attraction. After each iteration, particles within distance $r_{\text{niche}}$ of each other form a niche. Each niche maintains its own local best position rather than sharing a global best, preventing domination by a single basin. The number of niches provides an estimate of the number of distinct local optima discovered.

Velocity clamping prevents explosive velocity growth that can send particles far from promising regions. The clamped velocity enforces componentwise bounds:

$$v_i(t+1)[j] = \begin{cases}
v_{\max} & \text{if } v_i(t+1)[j] > v_{\max} \\
-v_{\max} & \text{if } v_i(t+1)[j] < -v_{\max} \\
v_i(t+1)[j] & \text{otherwise}
\end{cases}$$

where $v_{\max} = \rho (\text{ub}_j - \text{lb}_j)$ with $\rho \in [0.1, 0.5]$ and $[\text{lb}_j, \text{ub}_j]$ denotes the domain bounds for dimension $j$. Velocity clamping trades convergence speed for stability, particularly important during early iterations when particles possess little information about promising regions.

### Gaussian Process Scaling and Sparse Approximations

Exact Gaussian process inference requires solving the linear system $\mathbf{K} \boldsymbol{\alpha} = \mathbf{y}$ for the weights $\boldsymbol{\alpha}$ and computing the log-determinant $\log|\mathbf{K}|$, both requiring $O(t^3)$ arithmetic operations for $t$ observations. The cubic scaling renders exact inference intractable beyond $t \approx 10{,}000$ observations.

Sparse Gaussian process approximations reduce complexity by selecting $m \ll t$ inducing points $\mathbf{Z} = \{z_1, \ldots, z_m\}$ and conditioning predictions on function values $\mathbf{u} = f(\mathbf{Z})$ at these inducing points rather than all observations. The Subset of Regressors (SoR) approximation uses the posterior:

$$p(f(x) | \mathbf{X}, \mathbf{y}, \mathbf{Z}) \approx \int p(f(x) | \mathbf{u}) p(\mathbf{u} | \mathbf{X}, \mathbf{y}, \mathbf{Z}) \, d\mathbf{u}$$

where $p(\mathbf{u} | \mathbf{X}, \mathbf{y}, \mathbf{Z})$ denotes the Gaussian process posterior conditioned on inducing points. The inducing point posterior requires inverting only the $m \times m$ matrix $\mathbf{K}_{ZZ}$, reducing complexity to $O(m^2 t)$ for training and $O(m^2)$ for prediction.

The Fully Independent Training Conditional (FITC) approximation improves on SoR by accounting for uncertainty in the inducing point representation. FITC replaces the prior covariance with:

$$\text{Cov}[f(x), f(x')] \approx k(x, x') - \mathbf{k}_Z(x)^\top \mathbf{K}_{ZZ}^{-1} \mathbf{k}_Z(x')$$

where $\mathbf{k}_Z(x) = (k(z_1, x), \ldots, k(z_m, x))^\top$. This low-rank plus diagonal structure $\mathbf{K} \approx \mathbf{K}_{XZ} \mathbf{K}_{ZZ}^{-1} \mathbf{K}_{ZX} + \text{diag}(\boldsymbol{\lambda})$ enables $O(m^2 t)$ inference via Woodbury matrix inversion.

Inducing point selection critically impacts approximation quality. Uniform grid placement in $\mathcal{X}$ works for low dimensions $n \le 3$ but scales exponentially. Greedy forward selection iteratively adds inducing points maximizing posterior variance reduction, ensuring coverage of high-uncertainty regions. Variational inference optimizes inducing point locations $\mathbf{Z}$ jointly with kernel hyperparameters by minimizing the KL divergence between the approximate and exact posteriors.

Trust region constraints prevent Bayesian optimization from querying pathological points where the Gaussian process posterior overestimates function values due to extrapolation beyond observed regions. The constrained acquisition maximizes $\alpha(x)$ subject to $\|x - x_{\text{best}}\| \le \delta$ where $x_{\text{best}}$ denotes the current best observation and $\delta$ controls exploration radius. As more observations accumulate and the posterior uncertainty shrinks, $\delta$ can be gradually increased.

Multi-fidelity Bayesian optimization exploits cheap approximate function evaluations $f_{\text{approx}}(x)$ (coarse computational meshes, early-stopping neural network training) alongside expensive exact evaluations $f(x)$. The algorithm models $f$ and $f_{\text{approx}}$ jointly via a multi-output Gaussian process with cross-covariance kernel, enabling transfer of information from cheap to expensive evaluations. The acquisition function balances querying high-fidelity versus low-fidelity approximations based on cost-adjusted expected improvement.

### Failure Modes and Diagnostic Strategies

Stochastic gradient descent exhibits several characteristic failure modes that require problem-specific diagnosis and mitigation. Exploding gradients occur when backpropagation through recurrent architectures or very deep feedforward networks causes gradient norms $\|\nabla_\theta f(\theta_t)\|$ to grow exponentially with depth. Gradient clipping caps gradient norms at a threshold: $g_t \gets g_t \cdot \min\{1, \tau / \|g_t\|\}$ where $\tau \approx 1.0$ prevents parameter updates from overshooting reasonable regions. Layer normalization and careful weight initialization (Xavier, He initialization) architecturally prevent gradient explosion by maintaining approximately unit variance of activations and gradients across layers.

Vanishing gradients manifest in the opposite extreme: gradients shrink exponentially with depth, preventing learning in early layers. Residual connections $h(x) = x + f(x)$ maintain gradient flow by providing direct paths from output to input that bypass intermediate layers, enabling training of networks with hundreds of layers.

Loss plateaus with near-zero gradients can represent either wide local minima (desirable for generalization), saddle points (escapable via stochastic noise), or flat regions of the loss surface (requiring learning rate increases or architectural changes). Computing Hessian eigenvalues via Lanczos iteration distinguishes these cases: positive-definite Hessians indicate local minima, indefinite Hessians with negative eigenvalues indicate saddle points, and nearly-singular Hessians indicate flat regions.

Poor generalization despite low training loss signals overfitting addressable via regularization (weight decay $\mathcal{R}(\theta) = \frac{\lambda}{2} \|\theta\|^2$, dropout), early stopping based on validation loss, or data augmentation. The double descent phenomenon complicates this picture: modern overparameterized networks often exhibit a second descent regime where increasing capacity beyond interpolation threshold paradoxically improves generalization, suggesting classical bias-variance trade-offs require revision.

Simulated annealing's primary failure mode is inadequate equilibration time at each temperature, causing the Markov chain to fail to reach the Boltzmann distribution before cooling proceeds. Monitoring acceptance rates provides equilibration diagnostics: acceptance rates declining below $10\%$ indicate insufficient temperature, while rates exceeding $80\%$ indicate wasted computation at unnecessarily high temperatures. Adaptive equilibration extends iteration counts at each temperature until acceptance rates stabilize.

Genetic algorithms suffer from loss of diversity when selection pressure eliminates genetic variation before crossover explores building block combinations. The population converges prematurely to a single dominant genotype, terminating search. Diversity-preserving mechanisms include fitness sharing (reducing fitness of individuals in crowded regions of genotype space), crowding (replacing parents with offspring only when offspring are more similar), and island models (maintaining multiple isolated populations with periodic migration).

Particle swarm optimization's characteristic failure is stagnation near local optima due to insufficient exploration momentum. All particles cluster around the global best position $g$ with near-zero velocities, eliminating gradient-free search. Restarting particles at random positions when diversity drops below threshold reinitializes exploration, though this discards accumulated search information. Guaranteed convergence PSO modifies the velocity update to ensure asymptotic convergence to stationary points by incorporating decreasing random perturbations.

Bayesian optimization degrades when the Gaussian process model misspecifies the true function class, causing acquisition functions to target regions that appear promising under the model but are actually suboptimal. Kernel misspecification (using squared exponential kernel for non-smooth functions) induces systematic bias in posterior means. Model diagnostics include leave-one-out cross-validation (evaluating predictive likelihood on held-out observations) and posterior predictive checks (comparing observed data to samples from the posterior predictive distribution). Mixture kernels $k = w_1 k_1 + w_2 k_2$ combining different length scales and smoothness assumptions provide robustness against misspecification.

The tension between theoretical convergence guarantees and practical finite-time performance pervades stochastic global optimization. Logarithmic cooling guarantees simulated annealing convergence but requires infeasible runtimes. Robbins-Monro conditions guarantee stochastic gradient convergence but dictate decaying learning rates that slow convergence on non-convex losses. Bayesian optimization provides sample-efficient global search but scales poorly beyond $20$-dimensional spaces. Navigating these trade-offs demands problem-specific calibration: exploit convexity and gradient information when available via variance-reduced methods, resort to metaheuristics when gradients are intractable or discrete structure precludes first-order methods, and deploy Bayesian optimization for expensive black-box objectives where sample efficiency justifies computational overhead.
