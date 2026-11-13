```markdown
# Lesson 1: Fundamentals of AI

## 1. First-Principles Intuition & Invariants

Artificial intelligence is, at its mathematical core, a family of function approximation techniques. Given a dataset of input-output pairs $\{(x_i, y_i)\}_{i=1}^N$, the goal is to find a function $f_\theta$ parameterized by $\theta$ such that $f_\theta(x) \approx y$ for unseen inputs $x$. Everything else — neural architectures, training algorithms, regularization schemes — is engineering scaffolding built on top of this single idea.

The problem is fundamentally ill-posed: infinitely many functions can fit any finite dataset exactly. This is Vapnik's insight from statistical learning theory. The resolution is *inductive bias*: assumptions baked into the architecture or optimization procedure that prefer certain function classes. A convolutional network assumes spatial locality and translation invariance. A Transformer assumes that pairwise attention over a sequence is sufficient to capture dependencies. The choice of inductive bias is the most consequential design decision an ML engineer makes, and it is rarely discussed with the rigor it deserves.

### The Three Invariants of Statistical Learning

**1. The Bias-Variance Decomposition**

For any estimator $\hat{f}$, the expected generalization error on unseen data decomposes as:

$$\mathbb{E}[(y - \hat{f}(x))^2] = \underbrace{(\mathbb{E}[\hat{f}(x)] - f(x))^2}_{\text{Bias}^2} + \underbrace{\mathbb{E}[(\hat{f}(x) - \mathbb{E}[\hat{f}(x)])^2]}_{\text{Variance}} + \underbrace{\sigma^2}_{\text{Irreducible Noise}}$$

Bias measures systematic error from wrong assumptions in the model family. Variance measures sensitivity to fluctuations in the training set. Irreducible noise is a property of the data-generating process itself. Classic regularization methods (L1/L2 weight decay, dropout, early stopping) trade bias for variance reduction. Modern overparameterized networks (billions of parameters) violate the classical bias-variance intuition through *double descent*: error first rises, then falls again as model capacity increases past interpolation threshold.

**2. The No Free Lunch Theorem**

Wolpert and Macready (1997) proved that averaged over all possible problem distributions, every optimization algorithm performs identically. No algorithm is universally superior. In practice this means every architectural or optimization choice that improves performance on one distribution must degrade it on another. This is not a theoretical curiosity — it is why transfer learning requires careful consideration of domain shift and why a ResNet trained on ImageNet does not trivially generalize to medical imaging.

**3. The Manifold Hypothesis**

Real-world high-dimensional data (images, text, audio) does not occupy its ambient space uniformly. It concentrates on or near a low-dimensional manifold embedded in that space. A 256×256 RGB image lives in $\mathbb{R}^{196608}$, but the manifold of "natural photographs" has effective dimensionality estimated in the hundreds. Deep learning succeeds largely because its hierarchical feature extraction machinery discovers and exploits this manifold structure. This explains why random pixel noise, which lies far from the natural image manifold, is immediately catastrophic for a classifier — and why adversarial examples, which are imperceptibly small perturbations that cross manifold boundaries, are so effective.

### Learning Paradigms: A Precise Taxonomy

The supervised/unsupervised dichotomy is a pedagogical simplification. A more precise taxonomy:

| Paradigm | Supervision Signal | Canonical Algorithm | Formal Objective |
|---|---|---|---|
| Supervised | Full label $y_i$ per example | SGD on cross-entropy | $\min_\theta \mathbb{E}_{(x,y)}[\mathcal{L}(f_\theta(x), y)]$ |
| Unsupervised | None | Variational Autoencoder, k-means | $\min_\theta -\mathbb{E}_x[\log p_\theta(x)]$ |
| Self-supervised | Label derived from data itself | BERT, SimCLR | Masked token prediction, contrastive loss |
| Reinforcement | Scalar reward $r_t$ from environment | PPO, Q-learning | $\max_\pi \mathbb{E}[\sum_t \gamma^t r_t]$ |
| Semi-supervised | Labels for subset, unlabeled remainder | Label propagation | Consistency regularization |
| Few-shot | $k$ labeled examples per class | MAML, Prototypical Nets | Meta-learning across task distributions |

Self-supervised learning deserves particular emphasis because it underlies every large language model (LLM) in production today, including GPT-4. The pretraining objective — predict the next token given all previous tokens — is a form of self-supervision where the label is derived directly from the data sequence itself, requiring no human annotation.

---

## 2. Core Architecture & Mechanics

### Neural Networks from First Principles

A feedforward neural network is a composition of affine transformations interleaved with nonlinear activation functions:

$$f_\theta(x) = W_L \cdot \sigma(W_{L-1} \cdot \sigma(\cdots \sigma(W_1 x + b_1) \cdots) + b_{L-1}) + b_L$$

where $\sigma$ is an elementwise nonlinearity such as ReLU ($\sigma(z) = \max(0, z)$), and $\theta = \{W_l, b_l\}_{l=1}^L$ are the learnable parameters. Without the nonlinearity, any depth of composition collapses to a single linear transformation — the Universal Approximation Theorem (Hornik, 1989; Cybenko, 1989) guarantees that a single hidden layer with sufficient width can approximate any continuous function on a compact domain, but
