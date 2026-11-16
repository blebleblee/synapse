# Lesson 5: Multivariate Methods

## 1. First-Principles Intuition & Invariants

Statistics lives in high dimensions. The moment a problem involves more than one measured quantity per observation, the analyst steps into a space where univariate intuitions fail quietly and without warning. Means become centroid vectors, variances become covariance matrices, and the question of "how different are these groups?" demands not a $t$-statistic but a geometric comparison of ellipsoidal clouds in $\mathbb{R}^p$. Multivariate methods are the rigorous machinery for navigating that space, and understanding them from first principles requires anchoring every technique to the structure it exploits.

### The Multivariate Normal Distribution

The foundation is the multivariate normal. A random vector $\mathbf{X} = (X_1, X_2, \ldots, X_p)^\top$ follows a $p$-dimensional multivariate normal distribution if every linear combination $\mathbf{a}^\top \mathbf{X}$ for $\mathbf{a} \in \mathbb{R}^p$ is itself a univariate normal. This characterization is not circular — it is the definitive property that makes the multivariate normal closed under linear transformation, a critical algebraic invariant.

The density is defined for a non-degenerate distribution ($\det(\boldsymbol{\Sigma}) > 0$) as:

$$f(\mathbf{x}) = \frac{1}{(2\pi)^{p/2} |\boldsymbol{\Sigma}|^{1/2}} \exp\!\left(-\frac{1}{2}(\mathbf{x} - \boldsymbol{\mu})^\top \boldsymbol{\Sigma}^{-1} (\mathbf{x} - \boldsymbol{\mu})\right)$$

where $\boldsymbol{\mu} \in \mathbb{R}^p$ is the mean vector and $\boldsymbol{\Sigma} \in \mathbb{R}^{p \times p}$ is the covariance matrix, which must be symmetric and positive semi-definite. The argument of the exponential, $(\mathbf{x} - \boldsymbol{\mu})^\top \boldsymbol{\Sigma}^{-1} (\mathbf{x} - \boldsymbol{\mu})$, is the **Mahalanobis distance squared**, denoted $D^2$. It measures how far $\mathbf{x}$ is from $\boldsymbol{\mu}$ in units adjusted for the variance and correlation structure of the distribution. Where Euclidean distance treats all coordinate directions equally, Mahalanobis distance stretches and rotates the space so that the covariance ellipsoid becomes a sphere, making the geometry of inference coordinate-free.

The covariance matrix $\boldsymbol{\Sigma}$ encodes two separate phenomena simultaneously: the marginal variances $\sigma_{ii} = \text{Var}(X_i)$ along its diagonal, and the pairwise covariances $\sigma_{ij} = \text{Cov}(X_i, X_j)$ off it. The correlation matrix $\mathbf{R}$, obtained by standardizing $\boldsymbol{\Sigma}$, isolates the dependency structure from the scaling. Positive semi-definiteness of $\boldsymbol{\Sigma}$ is not a convenience assumption — it reflects that no linear combination of the variables can have negative variance, a physical necessity. When $\boldsymbol{\Sigma}$ is only positive semi-definite and not positive definite, the distribution is degenerate: the probability mass lies on a lower-dimensional affine subspace, and the density in $\mathbb{R}^p$ does not exist.

The spectral decomposition of $\boldsymbol{\Sigma}$ is central to nearly every multivariate method. Because $\boldsymbol{\Sigma}$ is real symmetric, the spectral theorem guarantees:

$$\boldsymbol{\Sigma} = \mathbf{P} \boldsymbol{\Lambda} \mathbf{P}^\top$$

where $\mathbf{P}$ is the orthogonal matrix of eigenvectors and $\boldsymbol{\Lambda} = \text{diag}(\lambda_1, \lambda_2, \ldots, \lambda_p)$ contains the eigenvalues in non-increasing order. These eigenvectors are the principal axes of the density ellipsoid, and the eigenvalues are the squared radii along those axes. This decomposition is not incidental to PCA — it *is* PCA, as we will develop precisely below.

A critical distributional result governs inference: if $\mathbf{X}_1, \mathbf{X}_2, \ldots, \mathbf{X}_n \overset{\text{iid}}{\sim} \mathcal{N}_p(\boldsymbol{\mu}, \boldsymbol{\Sigma})$, then the sample mean vector $\bar{\mathbf{X}} = \frac{1}{n}\sum_{i=1}^n \mathbf{X}_i$ satisfies:

$$\bar{\mathbf{X}} \sim \mathcal{N}_p\!\left(\boldsymbol{\mu},\, \frac{1}{n}\boldsymbol{\Sigma}\right)$$

and the sample covariance matrix $\mathbf{S} = \frac{1}{n-1}\sum_{i=1}^n (\mathbf{X}_i - \bar{\mathbf{X}})(\mathbf{X}_i - \bar{\mathbf{X}})^\top$ follows a Wishart distribution $\mathcal{W}_p(n-1, \boldsymbol{\Sigma})$, the multivariate generalization of the chi-squared distribution. The Wishart distribution is the probability law on symmetric positive definite matrices induced by summing outer products of multivariate normal vectors, and its degrees of freedom count the rank of the scatter matrix.

### Hotelling's $T^2$: The Multivariate $t$-Test

When comparing a sample mean vector $\bar{\mathbf{X}}$ to a hypothesized value $\boldsymbol{\mu}_0$, or comparing the mean vectors of two groups, the natural extension of the Student $t$-statistic is **Hotelling's $T^2$**, introduced by Harold Hotelling in 1931. The one-sample statistic is:

$$T^2 = n(\bar{\mathbf{X}} - \boldsymbol{\mu}_0)^\top \mathbf{S}^{-1} (\bar{\mathbf{X}} - \boldsymbol{\mu}_0)$$

This is precisely the Mahalanobis distance from the sample mean to the null vector, scaled by sample size and estimated by $\mathbf{S}$. The key distributional result is that under $H_0: \boldsymbol{\mu} = \boldsymbol{\mu}_0$ and normality:

$$\frac{n - p}{p(n-1)} T^2 \sim F(p,\, n - p)$$

The proof of this transformation from $T^2$ to an $F$-distribution runs through the independence of $\bar{\mathbf{X}}$ and $\mathbf{S}$ (itself a consequence of the Cochran decomposition in the multivariate setting) and the relationship between the Wishart and multivariate beta distributions. The two-sample Hotelling statistic for comparing $\boldsymbol{\mu}_1$ and $\boldsymbol{\mu}_2$ using pooled covariance $\mathbf{S}_p$ is:

$$T^2 = \frac{n_1 n_2}{n_1 + n_2}(\bar{\mathbf{X}}_1 - \bar{\mathbf{X}}_2)^\top \mathbf{S}_p^{-1} (\bar{\mathbf{X}}_1 - \bar{\mathbf{X}}_2)$$

which follows the same $F$-transformation with $n_1 + n_2 - 2$ total degrees of freedom for $\mathbf{S}_p$. The simultaneous confidence region for $\boldsymbol{\mu}$ is the Mahalanobis ellipsoid:

$$\left\{\boldsymbol{\mu} : n(\bar{\mathbf{X}} - \boldsymbol{\mu})^\top \mathbf{S}^{-1}(\bar{\mathbf{X}} - \boldsymbol{\mu}) \leq \frac{p(n-1)}{n-p} F_{\alpha}(p, n-p)\right\}$$

This ellipsoid is the correct simultaneous inference region: unlike $p$ separate univariate confidence intervals, it controls the joint probability that every component falls within its band, respecting the correlation structure encoded in $\mathbf{S}$.

### MANOVA: Extending ANOVA to Multiple Response Variables

**Multivariate Analysis of Variance (MANOVA)** addresses the question that ANOVA cannot: given $g$ groups and $p$ response variables measured simultaneously, do the groups differ in their mean vectors? The setup mirrors one-way ANOVA. For group $k$ containing $n_k$ observations, the total scatter is decomposed as:

$$\mathbf{T} = \mathbf{B} + \mathbf{W}$$

where $\mathbf{T} = \sum_{k=1}^g \sum_{i=1}^{n_k} (\mathbf{X}_{ki} - \bar{\mathbf{X}})(\mathbf{X}_{ki} - \bar{\mathbf{X}})^\top$ is the total scatter matrix, $\mathbf{B} = \sum_{k=1}^g n_k (\bar{\mathbf{X}}_k - \bar{\mathbf{X}})(\bar{\mathbf{X}}_k - \bar{\mathbf{X}})^\top$ is the between-group scatter, and $\mathbf{W} = \sum_{k=1}^g \sum_{i=1}^{n_k} (\mathbf{X}_{ki} - \bar{\mathbf{X}}_k)(\mathbf{X}_{ki} - \bar{\mathbf{X}}_k)^\top$ is the within-group scatter (the pooled covariance estimator up to a constant). The multivariate $F$-ratio analog is the matrix $\mathbf{W}^{-1}\mathbf{B}$, whose eigenvalues drive the four classical test statistics.

**Wilks' $\Lambda$** is the most commonly reported:

$$\Lambda = \frac{|\mathbf{W}|}{|\mathbf{B} + \mathbf{W}|} = \frac{|\mathbf{W}|}{|\mathbf{T}|}$$

It is the ratio of the determinant of the within-group scatter to the total scatter. Because determinants measure volume, $\Lambda$ quantifies what fraction of total multivariate dispersion is unexplained by group membership. Small $\Lambda$ (near zero) indicates that between-group differences dominate, mirroring how small $p$-values correspond to large $F$-statistics in univariate ANOVA. The other three test statistics — **Pillai's trace** $V = \text{tr}(\mathbf{B}(\mathbf{B}+\mathbf{W})^{-1})$, **Lawley-Hotelling trace** $U = \text{tr}(\mathbf{W}^{-1}\mathbf{B})$, and **Roy's largest root** $\theta = \lambda_{\max}(\mathbf{W}^{-1}\mathbf{B})$ — each weight the eigenvalues of $\mathbf{W}^{-1}\mathbf{B}$ differently. Pillai's trace sums the canonical correlations and is the most robust to violations of normality and covariance homogeneity. Roy's largest root optimizes power along the single linear combination most discriminating between groups, making it powerful when that direction concentrates all group separation.

### Principal Component Analysis: The Spectral Decomposition as Data Compression

**Principal Component Analysis (PCA)** is the unsupervised technique for finding the orthogonal directions of maximum variance in a multivariate dataset. Its theoretical justification is an optimization problem: find the unit vector $\mathbf{a}_1 \in \mathbb{R}^p$ that maximizes $\text{Var}(\mathbf{a}_1^\top \mathbf{X}) = \mathbf{a}_1^\top \boldsymbol{\Sigma} \mathbf{a}_1$ subject to $\|\mathbf{a}_1\| = 1$.

Using a Lagrange multiplier $\lambda$, the stationarity condition is:

$$\frac{\partial}{\partial \mathbf{a}_1}\!\left(\mathbf{a}_1^\top \boldsymbol{\Sigma} \mathbf{a}_1 - \lambda(\mathbf{a}_1^\top \mathbf{a}_1 - 1)\right) = 2\boldsymbol{\Sigma}\mathbf{a}_1 - 2\lambda \mathbf{a}_1 = \mathbf{0}$$

This is precisely the eigenequation $\boldsymbol{\Sigma}\mathbf{a}_1 = \lambda \mathbf{a}_1$. Substituting back, $\mathbf{a}_1^\top \boldsymbol{\Sigma} \mathbf{a}_1 = \lambda \mathbf{a}_1^\top \mathbf{a}_1 = \lambda$, so the variance of the projection equals the eigenvalue. The maximum variance direction is therefore the eigenvector corresponding to $\lambda_1$, the largest eigenvalue of $\boldsymbol{\Sigma}$. The second principal component $\mathbf{a}_2$ maximizes variance subject to both unit norm and orthogonality to $\mathbf{a}_1$; the same argument yields the eigenvector for $\lambda_2$. Continuing inductively, the $k$-th principal component is the $k$-th eigenvector, and the variance it captures is $\lambda_k$.

The proportion of total variance explained by the first $m$ components is:

$$\frac{\sum_{k=1}^m \lambda_k}{\sum_{k=1}^p \lambda_k} = \frac{\sum_{k=1}^m \lambda_k}{\text{tr}(\boldsymbol{\Sigma})}$$

In practice, $\boldsymbol{\Sigma}$ is replaced by the sample covariance $\mathbf{S}$, and the eigendecomposition is computed numerically via the **singular value decomposition (SVD)** of the centered data matrix $\mathbf{X}_c \in \mathbb{R}^{n \times p}$:

$$\mathbf{X}_c = \mathbf{U} \mathbf{D} \mathbf{V}^\top$$

where $\mathbf{U} \in \mathbb{R}^{n \times p}$ has orthonormal columns, $\mathbf{D} = \text{diag}(d_1, \ldots, d_p)$ contains singular values, and $\mathbf{V} \in \mathbb{R}^{p \times p}$ is orthogonal. The relationship to the eigendecomposition of $\mathbf{S}$ is:

$$\mathbf{S} = \frac{1}{n-1}\mathbf{X}_c^\top \mathbf{X}_c = \mathbf{V} \frac{\mathbf{D}^2}{n-1} \mathbf{V}^\top$$

so the right singular vectors in $\mathbf{V}$ are the principal component loadings, and $\lambda_k = d_k^2/(n-1)$. Using SVD rather than explicit eigendecomposition of $\mathbf{S}$ is numerically superior: forming $\mathbf{X}_c^\top \mathbf{X}_c$ squares the condition number, amplifying floating-point error, while the SVD algorithm operates directly on the data matrix.

A critical choice is whether to perform PCA on the covariance matrix $\mathbf{S}$ or the correlation matrix $\mathbf{R}$. When variables are measured in different units or on vastly different scales, $\mathbf{S}$-based PCA will have its first component dominated by the highest-variance variable regardless of its scientific relevance. Standardizing to unit variance (standardized PCA on $\mathbf{R}$) removes this scale artifact, but it also treats all variables as equally important a priori. This is not a universal improvement — if the variance differences are physically meaningful, standardization destroys signal.

### Factor Analysis: Modeling Latent Structure

Where PCA is a rotation of observed variance, **factor analysis** posits a generative model for the covariance structure. The common factor model assumes that each observed variable is a linear combination of a small number $m$ of unobserved **common factors** plus a variable-specific error:

$$\mathbf{X} - \boldsymbol{\mu} = \boldsymbol{\Lambda} \mathbf{F} + \boldsymbol{\epsilon}$$

where $\boldsymbol{\Lambda} \in \mathbb{R}^{p \times m}$ is the matrix of **factor loadings**, $\mathbf{F} \sim \mathcal{N}_m(\mathbf{0}, \mathbf{I})$ contains the $m$ common factors (assumed orthonormal), and $\boldsymbol{\epsilon} \sim \mathcal{N}_p(\mathbf{0}, \boldsymbol{\Psi})$ with $\boldsymbol{\Psi} = \text{diag}(\psi_1, \ldots, \psi_p)$ captures unique variance for each variable. The model implies the covariance structure:

$$\boldsymbol{\Sigma} = \boldsymbol{\Lambda}\boldsymbol{\Lambda}^\top + \boldsymbol{\Psi}$$

The term $\boldsymbol{\Lambda}\boldsymbol{\Lambda}^\top$ contains the **communalities** $h_i^2 = \sum_{k=1}^m \lambda_{ik}^2$ along its diagonal, measuring how much of variable $i$'s variance is shared with the common factors. The uniquenesses $\psi_i = 1 - h_i^2$ (when working with the correlation matrix) capture what remains unexplained.

Factor analysis is fundamentally indeterminate: if $\boldsymbol{\Lambda}$ satisfies the model, then so does $\boldsymbol{\Lambda}\mathbf{Q}$ for any orthogonal matrix $\mathbf{Q}$, since $(\boldsymbol{\Lambda}\mathbf{Q})(\boldsymbol{\Lambda}\mathbf{Q})^\top = \boldsymbol{\Lambda}\boldsymbol{\Lambda}^\top$. This **rotational indeterminacy** is not a bug — it is the degree of freedom that factor analysis exploits to find interpretable solutions. The **varimax** rotation maximizes the variance of squared loadings within each factor:

$$V = \frac{1}{p}\sum_{k=1}^m \left[\sum_{i=1}^p \tilde{\lambda}_{ik}^4 - \frac{1}{p}\left(\sum_{i=1}^p \tilde{\lambda}_{ik}^2\right)^2\right]$$

where $\tilde{\lambda}_{ik}$ are loadings scaled by communalities. Maximizing $V$ drives each loading toward either zero or its extreme, producing the **simple structure** criterion of Thurstone: each variable loads highly on few factors and each factor is defined by a distinct cluster of variables. Estimation of $\boldsymbol{\Lambda}$ proceeds by maximum likelihood (yielding a likelihood ratio test for the number of factors), by principal factor analysis (using communality estimates in place of diagonal ones), or by iterative principal axis factoring.

### Canonical Correlation Analysis

**Canonical Correlation Analysis (CCA)**, developed by Hotelling in 1936, asks: what are the linear combinations of two variable sets $\mathbf{X} \in \mathbb{R}^p$ and $\mathbf{Y} \in \mathbb{R}^q$ that have maximum correlation? Let the joint covariance structure be:

$$\text{Cov}\!\begin{pmatrix}\mathbf{X} \\ \mathbf{Y}\end{pmatrix} = \begin{pmatrix}\boldsymbol{\Sigma}_{XX} & \boldsymbol{\Sigma}_{XY} \\ \boldsymbol{\Sigma}_{YX} & \boldsymbol{\Sigma}_{YY}\end{pmatrix}$$

We seek vectors $\mathbf{a} \in \mathbb{R}^p$ and $\mathbf{b} \in \mathbb{R}^q$ maximizing $\text{Cor}(\mathbf{a}^\top \mathbf{X}, \mathbf{b}^\top \mathbf{Y})$. Setting up the Lagrangian and taking derivatives leads to the generalized eigenvalue problem:

$$\boldsymbol{\Sigma}_{XX}^{-1}\boldsymbol{\Sigma}_{XY}\boldsymbol{\Sigma}_{YY}^{-1}\boldsymbol{\Sigma}_{YX}\mathbf{a} = \rho^2 \mathbf{a}$$

The eigenvalues $\rho_1^2 \geq \rho_2^2 \geq \cdots \geq \rho_s^2$ where $s = \min(p, q)$ are the squared **canonical correlations**, and the corresponding eigenvectors yield the canonical variates. The first pair $(\mathbf{a}_1^\top \mathbf{X},\, \mathbf{b}_1^\top \mathbf{Y})$ has maximum correlation $\rho_1$. Subsequent pairs are uncorrelated with all previous pairs and have the next highest correlation.

Notice that CCA generalizes multiple regression: when $q = 1$, the single canonical correlation equals the multiple correlation coefficient $R$ between $\mathbf{Y}$ and $\mathbf{X}$, and the canonical variate in $\mathbf{X}$ is exactly the fitted value direction. CCA is also the common framework underlying many multivariate techniques — PCA is CCA between $\mathbf{X}$ and itself, and linear discriminant analysis is a special case of CCA between continuous predictors and a binary group indicator, as the connection to Fisher's discriminant makes precise.

### Linear Discriminant Analysis

**Linear Discriminant Analysis (LDA)** finds the linear combination of variables that maximally separates predefined groups, in Fisher's formulation: maximize the ratio of between-group variance to within-group variance of the projected scores. For the two-group case, this is equivalent to finding $\mathbf{a}$ maximizing:

$$\frac{\mathbf{a}^\top \mathbf{B} \mathbf{a}}{\mathbf{a}^\top \mathbf{W} \mathbf{a}}$$

The solution is $\mathbf{a} \propto \mathbf{W}^{-1}(\bar{\mathbf{X}}_1 - \bar{\mathbf{X}}_2)$, the pooled-covariance-adjusted mean difference. For $g > 2$ groups, the discriminant directions are the eigenvectors of $\mathbf{W}^{-1}\mathbf{B}$ corresponding to its $\min(g-1, p)$ nonzero eigenvalues — the same matrix at the heart of MANOVA. LDA as a classifier assigns an observation $\mathbf{x}$ to the group $k$ minimizing:

$$(\mathbf{x} - \bar{\mathbf{X}}_k)^\top \mathbf{S}_p^{-1} (\mathbf{x} - \bar{\mathbf{X}}_k) - 2\log \pi_k$$

where $\pi_k$ is the prior probability of group $k$. When $\pi_k$ are equal, this reduces to nearest centroid in Mahalanobis distance. The assumption of equal covariance matrices $\boldsymbol{\Sigma}_1 = \boldsymbol{\Sigma}_2 = \cdots = \boldsymbol{\Sigma}_g$ is what makes the discriminant function linear. When this assumption fails, **quadratic discriminant analysis (QDA)** uses group-specific covariance matrices $\mathbf{S}_k$, producing quadratic decision boundaries at the cost of estimating $p(p+1)/2$ additional parameters per group.

### Cluster Analysis: Unsupervised Group Discovery

Where discriminant analysis assigns observations to known groups, **cluster analysis** discovers group structure from data alone. The two dominant paradigms are hierarchical clustering and $k$-means partitioning.

Hierarchical agglomerative clustering begins with each observation in its own cluster and merges the two closest clusters at each step, building a **dendrogram** that records the merge sequence and distances. The choice of **linkage criterion** determines cluster geometry: single linkage uses the minimum inter-cluster distance, producing elongated, chaining clusters; complete linkage uses the maximum, producing compact, roughly spherical clusters; average linkage (UPGMA) uses the mean pairwise distance; and Ward's linkage minimizes the total within-cluster sum of squares increment at each merge, formally equivalent to applying Hotelling's criterion to cluster scatter matrices. Ward's method is equivalent to hierarchical clustering under a Euclidean variance criterion and tends to produce balanced, interpretable dendrograms for Gaussian cluster shapes.

The $k$-means algorithm partitions $n$ observations into $k$ clusters $C_1, \ldots, C_k$ by minimizing total within-cluster variance:

$$\text{TWCV} = \sum_{j=1}^k \sum_{\mathbf{x}_i \in C_j} \|\mathbf{x}_i - \bar{\mathbf{x}}_j\|^2$$

The Lloyd algorithm alternates between assignment and update steps. Crucially, this objective function is the trace of the within-cluster scatter matrix $\mathbf{W}_k$:

$$\text{TWCV} = \text{tr}(\mathbf{W}_k)$$

so $k$-means implicitly assumes spherical, equal-volume clusters. The algorithm converges to a local minimum; initialization via $k$-means++ selects initial centroids proportional to squared distance from already-chosen centroids, dramatically improving convergence to good solutions.

**Gaussian mixture models (GMM)** generalize $k$-means by modeling the data as a mixture of $k$ multivariate normals with general covariance structures, estimated via the **EM algorithm**. The E-step computes posterior probabilities $r_{ik} = P(\text{component } k \mid \mathbf{x}_i)$ using the current parameters; the M-step updates means, covariances, and mixing weights using soft-weighted sufficient statistics. GMMs recover the geometry $k$-means assumes away: each component has its own $\boldsymbol{\mu}_k$ and $\boldsymbol{\Sigma}_k$, permitting ellipsoidal clusters of different orientations and sizes.

### Covariance Structure Modeling: Structural Equation Models

**Structural Equation Modeling (SEM)** unifies factor analysis and path analysis under a single framework for testing theoretically motivated covariance structures. The fundamental equation is:

$$\boldsymbol{\Sigma}(\boldsymbol{\theta}) = \boldsymbol{\Lambda}(\mathbf{I} - \mathbf{B})^{-1}\boldsymbol{\Psi}(\mathbf{I} - \mathbf{B})^{-\top}\boldsymbol{\Lambda}^\top + \boldsymbol{\Theta}_\epsilon$$

where $\mathbf{B}$ is the matrix of path coefficients among latent variables (with zero diagonal), $\boldsymbol{\Psi}$ is the latent variable covariance matrix, $\boldsymbol{\Lambda}$ maps latent to observed variables, and $\boldsymbol{\Theta}_\epsilon$ is the unique variance matrix. Estimation by maximum likelihood minimizes the discrepancy function:

$$F_{ML} = \log|\boldsymbol{\Sigma}(\boldsymbol{\theta})| + \text{tr}(\mathbf{S}\boldsymbol{\Sigma}(\boldsymbol{\theta})^{-1}) - \log|\mathbf{S}| - p$$

which is zero when $\boldsymbol{\Sigma}(\boldsymbol{\theta}) = \mathbf{S}$ exactly. At the solution $\hat{\boldsymbol{\theta}}$, the statistic $(n-1)F_{ML}(\hat{\boldsymbol{\theta}})$ is asymptotically $\chi^2$ with $\frac{1}{2}p(p+1) - q$ degrees of freedom, where $q$ is the number of free parameters, providing a likelihood ratio test of model fit. The **identification problem** — whether the data uniquely determine $\boldsymbol{\theta}$ — requires that the number of free parameters not exceed $\frac{1}{2}p(p+1)$, the number of unique covariance elements, with additional structural constraints needed to fix the scale of latent variables.

---

## 2. Core Architecture & Mechanics

The practitioner must internalize the mechanical architecture through which these methods flow: from raw data matrix to inference. The following diagram captures the main computation pipeline.

```
┌────────────────────────────────────────────────────────────────────┐
│                     Raw Data Matrix  X (n×p)                       │
└───────────────────────────────┬────────────────────────────────────┘
                                │
                    Center: X_c = X - 1μ̂ᵀ
                                │
            ┌───────────────────┼──────────────────────┐
            │                   │                      │
     Scatter/SVD           Covariance S          Group Labels
     X_c = UDVᵀ        S = Xcᵀ Xc / (n-1)        (if known)
            │                   │                      │
     ┌──────┴──────┐     ┌──────┴──────┐     ┌────────┴───────┐
     │     PCA     │     │   Factor    │     │  MANOVA / LDA  │
     │  scores=UD  │     │  Analysis   │     │  B, W matrices │
     │ loadings=V  │     │  Λ, Ψ estim │     │  W⁻¹B eigens   │
     └──────┬──────┘     └──────┬──────┘     └────────┬───────┘
            │                   │                      │
     Dimensionality     Latent Structure         Discriminant
     Reduction          Rotation (varimax)       Functions / Groups
            │                   │                      │
            └───────────────────┴──────────────────────┘
                                │
                        Reduced Representation
                        (scores, factors, discriminants)
                                │
                    ┌───────────┴────────────┐
                    │                        │
             Clustering              Canonical Correlation
             (k-means, GMM,          (CCA: Σ_XX⁻¹ Σ_XY Σ_YY⁻¹ Σ_YX)
              hierarchical)
                    │                        │
             Cluster Labels          Canonical Variates
                                     and Correlations ρ₁,...,ρₛ
```

### The Covariance Matrix as the Load-Bearing Structure

Every multivariate method is a function of $\mathbf{S}$ (or its inverse). Computing $\mathbf{S}$ reliably is therefore the primary numerical task. With $n$ observations and $p$ variables, $\mathbf{S}$ is positive definite only when $n > p$. When $p \geq n$ — the **high-dimensional regime** increasingly relevant in modern statistical applications — $\mathbf{S}$ is rank-deficient, its inverse does not exist, and standard methods break down. This is not merely a numerical annoyance: $\mathbf{S}$ has only $n-1$ degrees of freedom distributed across $p(p+1)/2$ entries, so when $p$ is comparable to $n$, the sample eigenvalues are severely dispersed relative to the population eigenvalues by the **Marchenko-Pastur law**, which characterizes the limiting spectral distribution of large Wishart matrices.

The computational mechanics of the main algorithms are as follows.

**PCA via SVD.** Given the centered data matrix $\mathbf{X}_c \in \mathbb{R}^{n \times p}$, compute the thin SVD $\mathbf{X}_c = \mathbf{U}_r \mathbf{D}_r \mathbf{V}_r^\top$ retaining only the top $r$ singular values, where $r \ll \min(n,p)$. The score matrix is $\mathbf{T} = \mathbf{U}_r \mathbf{D}_r \in \mathbb{R}^{n \times r}$ and the loading matrix is $\mathbf{V}_r \in \mathbb{R}^{p \times r}$. The reconstruction of a data point from its first $r$ components is:

$$\hat{\mathbf{x}}_i = \bar{\mathbf{x}} + \mathbf{V}_r \mathbf{V}_r^\top (\mathbf{x}_i - \bar{\mathbf{x}})$$

The residual $\mathbf{x}_i - \hat{\mathbf{x}}_i$ lies in the orthogonal complement of the principal subspace. The mean squared reconstruction error across the dataset equals $\sum_{k=r+1}^p \lambda_k$, the sum of discarded eigenvalues — a clean identity that quantifies information loss.

**Hotelling's $T^2$ computation.** For computational stability, do not compute $\mathbf{S}^{-1}$ explicitly. Instead, compute the Cholesky decomposition $\mathbf{S} = \mathbf{L}\mathbf{L}^\top$ and solve for $\mathbf{z} = \mathbf{L}^{-1}(\bar{\mathbf{X}} - \boldsymbol{\mu}_0)$ by forward substitution. Then $T^2 = n \|\mathbf{z}\|^2$. This avoids squaring the condition number of $\mathbf{S}$ and is numerically stable as long as $\mathbf{S}$ is well-conditioned.

**EM for Gaussian Mixture Models.** Let $\boldsymbol{\theta} = \{(\pi_k, \boldsymbol{\mu}_k, \boldsymbol{\Sigma}_k)\}_{k=1}^K$ be the current parameters. The E-step computes responsibilities:

$$r_{ik} = \frac{\pi_k \, \mathcal{N}(\mathbf{x}_i \mid \boldsymbol{\mu}_k, \boldsymbol{\Sigma}_k)}{\sum_{j=1}^K \pi_j \, \mathcal{N}(\mathbf{x}_i \mid \boldsymbol{\mu}_j, \boldsymbol{\Sigma}_j)}$$

The M-step sets:

$$\pi_k^{\text{new}} = \frac{N_k}{n}, \quad \boldsymbol{\mu}_k^{\text{new}} = \frac{1}{N_k}\sum_{i=1}^n r_{ik}\mathbf{x}_i, \quad \boldsymbol{\Sigma}_k^{\text{new}} = \frac{1}{N_k}\sum_{i=1}^n r_{ik}(\mathbf{x}_i - \boldsymbol{\mu}_k^{\text{new}})(\mathbf{x}_i - \boldsymbol{\mu}_k^{\text{new}})^\top$$

where $N_k = \sum_i r_{ik}$ is the effective count for component $k$. The log-likelihood $\sum_i \log \sum_k \pi_k \mathcal{N}(\mathbf{x}_i \mid \boldsymbol{\mu}_k, \boldsymbol{\Sigma}_k)$ is guaranteed non-decreasing at each iteration by Jensen's inequality, and convergence to a local maximum is assured. The critical implementation detail is computing the Gaussian density in log-space using the log-determinant and solving via Cholesky to prevent numerical underflow for large $p$.

**CCA via SVD.** The raw eigenvalue formulation $\boldsymbol{\Sigma}_{XX}^{-1}\boldsymbol{\Sigma}_{XY}\boldsymbol{\Sigma}_{YY}^{-1}\boldsymbol{\Sigma}_{YX}$ is numerically poor because it involves two matrix inversions. The stable algorithm computes Cholesky factors $\mathbf{S}_{XX} = \mathbf{L}_X \mathbf{L}_X^\top$ and $\mathbf{S}_{YY} = \mathbf{L}_Y \mathbf{L}_Y^\top$, forms the matrix $\mathbf{K} = \mathbf{L}_X^{-1} \mathbf{S}_{XY} \mathbf{L}_Y^{-\top}$, and computes its SVD $\mathbf{K} = \mathbf{U}_K \mathbf{D}_K \mathbf{V}_K^\top$. The canonical correlations are the singular values $\rho_k = d_k$, and the canonical weight vectors are $\mathbf{a}_k = \mathbf{L}_X^{-\top}\mathbf{u}_k$ and $\mathbf{b}_k = \mathbf{L}_Y^{-\top}\mathbf{v}_k$.

### Ward's Linkage as Variance Minimization

Ward's hierarchical clustering merges clusters $C_i$ and $C_j$ to minimize the increment in total within-cluster sum of squares. The merge cost can be computed without recomputing scatter matrices using the **Lance-Williams update formula**:

$$d(C_i \cup C_j,\, C_k) = \frac{n_i + n_k}{n_i + n_j + n_k} d(C_i, C_k) + \frac{n_j + n_k}{n_i + n_j + n_k} d(C_j, C_k) - \frac{n_k}{n_i + n_j + n_k} d(C_i, C_j)$$

This recursive formula computes all inter-cluster distances dynamically in $O(n^2)$ space and $O(n^2 \log n)$ time using a priority queue, without ever storing the full $n \times n$ distance matrix in memory simultaneously.

---

## 3. High-Performance Optimization & Failure Modes

Knowing the theory and the mechanics is insufficient without understanding where these methods break, how to detect failure, and what structural remedies exist. Each multivariate technique carries specific vulnerability patterns that follow directly from the mathematical assumptions on which it rests.

### Rank Deficiency and the High-Dimensional Trap

The single most catastrophic failure in applied multivariate analysis is inverting a sample covariance matrix that is singular or near-singular. This happens whenever $p \geq n$, but it also happens subtly when $p < n$ but predictors are highly collinear. The symptom is an ill-conditioned $\mathbf{S}$ with condition number $\kappa(\mathbf{S}) = \lambda_1 / \lambda_p \gg 1$, causing $\mathbf{S}^{-1}$ to amplify small estimation errors in the low-variance directions by a factor of $\kappa$.

The **regularized (shrinkage) estimator** of Ledoit and Wolf provides a principled remedy. It shrinks $\mathbf{S}$ toward a structured target $\mathbf{T}$ (commonly $\frac{\text{tr}(\mathbf{S})}{p}\mathbf{I}$):

$$\hat{\boldsymbol{\Sigma}}_{LW} = (1 - \alpha)\mathbf{S} + \alpha \mathbf{T}$$

The optimal shrinkage intensity $\alpha^*$ minimizes the expected Frobenius loss $\mathbb{E}\|\hat{\boldsymbol{\Sigma}} - \boldsymbol{\Sigma}\|_F^2$ and has a closed-form estimate from the data alone, making it a practical drop-in replacement for $\mathbf{S}$ in Hotelling's $T^2$, LDA, and MANOVA. The Ledoit-Wolf estimator is always positive definite for $\alpha \in (0,1]$, resolving the singularity problem while introducing controllable bias. For LDA specifically, **regularized discriminant analysis (RDA)** interpolates between LDA and QDA:

$$\hat{\boldsymbol{\Sigma}}_k(\alpha, \gamma) = \alpha \mathbf{S}_k + (1-\alpha)\mathbf{S}_p, \quad \hat{\boldsymbol{\Sigma}}_k(\alpha, \gamma, \gamma) = (1-\gamma)\hat{\boldsymbol{\Sigma}}_k(\alpha) + \gamma \frac{\text{tr}(\hat{\boldsymbol{\Sigma}}_k(\alpha))}{p}\mathbf{I}$$

with $(\alpha, \gamma)$ tuned by cross-validation.

### Determining the Number of Components or Factors

Both PCA and factor analysis require selecting a dimensionality $m$ or $r$. This selection has genuine consequences for downstream inference and should be treated as a statistical decision, not a heuristic one.

For PCA, the **scree plot** graphs $\lambda_k$ against $k$. The "elbow" heuristic — retaining components before the eigenvalue curve flattens — lacks formal justification and is unreliable in practice. A better approach is the **parallel analysis** procedure of Horn (1965): simulate many datasets of the same dimensions $n \times p$ under a null model of no correlation (i.e., $\boldsymbol{\Sigma} = \mathbf{I}$), compute the expected eigenvalues from these simulations, and retain only the components whose observed eigenvalues exceed the simulated 95th percentile. This controls for the inflation of sample eigenvalues due to chance variation. Alternatively, cross-validation on reconstruction error — holding out blocks of entries in $\mathbf{X}$ and predicting them from the PCA model — provides a direct empirical measure of predictive dimensionality.

For factor analysis, the chi-squared test from maximum likelihood estimation has known defects: it always rejects for large $n$ regardless of practical fit, and it cannot handle non-normality. The **Root Mean Square Error of Approximation (RMSEA)** corrects for model complexity:

$$\text{RMSEA} = \sqrt{\max\!\left(\frac{\chi^2 - df}{df(n-1)}, 0\right)}$$

Values below 0.05 indicate close fit, below 0.08 adequate fit, and above 0.10 poor fit. The **BIC criterion** $\chi^2 - df \cdot \log(n)$ additionally penalizes model complexity, providing a consistent selector for $m$.

For Gaussian mixture models, BIC consistently selects the correct number of components $K$ under mild regularity conditions. Explicitly, the penalized log-likelihood is $2\ell(\hat{\boldsymbol{\theta}}) - q_K \log n$ where $q_K = K - 1 + Kp + Kp(p+1)/2$ counts free parameters (mixing weights, means, and unique covariance entries). The model with maximum BIC is chosen. Note that the likelihood ratio test cannot be applied directly to compare $K$ and $K+1$ component models because the boundary of the parameter space is degenerate under the null, invalidating the standard $\chi^2$ asymptotics. BIC and the **integrated completed likelihood (ICL)** criterion are therefore the standard tools.

### Violation of the Equal Covariance Assumption

MANOVA and LDA both assume homogeneity of covariance matrices across groups: $\boldsymbol{\Sigma}_1 = \cdots = \boldsymbol{\Sigma}_g = \boldsymbol{\Sigma}$. This can be tested with **Box's M test**, which computes a generalized likelihood ratio comparing $\mathbf{S}_k$ to the pooled $\mathbf{S}_p$:

$$M = (n - g)\log|\mathbf{S}_p| - \sum_{k=1}^g (n_k - 1)\log|\mathbf{S}_k|$$

Under $H_0$ of equal covariance matrices and multivariate normality, an approximation to $M$ follows a chi-squared distribution. Box's M is notoriously sensitive to non-normality, however, frequently rejecting when the true departure is from normality rather than covariance heterogeneity. A practical strategy is to treat Box's M rejection with skepticism unless accompanied by visual evidence (e.g., dramatically different scatter plot shapes across groups), and to use Pillai's trace in MANOVA — which is the most robust among the four test statistics to covariance heterogeneity — when homogeneity is in doubt.

### Multivariate Outliers and Non-Normality

A multivariate outlier need not appear extreme in any univariate projection. It manifests as a point with large Mahalanobis distance $D^2(\mathbf{x}_i) = (\mathbf{x}_i - \bar{\mathbf{x}})^\top \mathbf{S}^{-1}(\mathbf{x}_i - \bar{\mathbf{x}})$. Under multivariate normality, $D^2 \sim \chi^2(p)$ approximately, so the chi-squared Q-Q plot of ordered $D^2$ values against $\chi^2(p)$ quantiles provides a diagnostic for both normality and outliers. Points that deviate from the line at large quantiles are multivariate outliers; systematic curvature throughout indicates non-normality.

The fundamental problem is that $\bar{\mathbf{x}}$ and $\mathbf{S}$ themselves are contaminated by the outliers being detected — a masking effect. The **Minimum Covariance Determinant (MCD)** estimator resolves this by finding the subset of $h = \lfloor (n + p + 1)/2 \rfloor$ observations whose sample covariance has minimum determinant, providing robust location and scatter estimates $\hat{\boldsymbol{\mu}}_{MCD}$ and $\hat{\boldsymbol{\Sigma}}_{MCD}$ that are not distorted by outliers. The robust Mahalanobis distance computed from these estimates follows a scaled $F$-distribution under normality, providing a formal outlier detection threshold.

Non-normality itself can be tested via Mardia's multivariate skewness and kurtosis measures. Mardia's multivariate skewness is:

$$\hat{\beta}_{1,p} = \frac{1}{n^2}\sum_{i=1}^n \sum_{j=1}^n \left[(\mathbf{x}_i - \bar{\mathbf{x}})^\top \mathbf{S}^{-1}(\mathbf{x}_j - \bar{\mathbf{x}})\right]^3$$

Under multivariate normality, $\frac{n}{6}\hat{\beta}_{1,p} \overset{d}{\to} \chi^2\!\left(\frac{p(p+1)(p+2)}{6}\right)$. Mardia's kurtosis is $\hat{\beta}_{2,p} = \frac{1}{n}\sum_{i=1}^n D_i^4$, which under normality is approximately normal with mean $p(p+2)$ and variance $\frac{8p(p+2)}{n}$.

### The Curse of Dimensionality in Clustering

$K$-means and hierarchical clustering depend on distance functions that become meaningless as $p$ grows. In high dimensions, the ratio of maximum to minimum inter-point Euclidean distance converges to one as $p \to \infty$ under mild moment conditions — formally, for i.i.d. components:

$$\frac{\max_{i \neq j} \|\mathbf{x}_i - \mathbf{x}_j\|^2 - \min_{i \neq j} \|\mathbf{x}_i - \mathbf{x}_j\|^2}{\min_{i \neq j} \|\mathbf{x}_i - \mathbf{x}_j\|^2} \to 0 \text{ as } p \to \infty$$

This concentration of distances is the technical mechanism by which nearest-neighbor structure collapses in high dimensions. The practical mitigation is to perform dimensionality reduction (PCA, factor analysis, or autoencoders) prior to clustering, restricting analysis to the meaningful low-dimensional manifold. For GMM, the number of parameters in $\boldsymbol{\Sigma}_k$ grows quadratically in $p$, motivating parsimonious covariance structures: diagonal, spherical, or tied covariance models that share structure across components.

### Scaling, Preprocessing, and Workflow Discipline

The practitioner's workflow must handle preprocessing with the same rigor as the statistical methods themselves. All multivariate inference requires that the scatter matrix $\mathbf{S}$ be estimable, which demands the sample size relation $n > p + 1$ at minimum and preferably $n > 5p$ for stable eigenvalue estimation. Measurement scale matters: PCA on $\mathbf{S}$ gives different results than PCA on $\mathbf{R}$, and the choice must be justified by whether variance differences across variables are scientifically meaningful.

Missing data breaks the symmetry of the covariance estimator. Complete-case analysis discards entire observations with any missing entry, which is unbiased only under missing-completely-at-random (MCAR) but wastes data. Full-information maximum likelihood (FIML) and multiple imputation preserve all observations and are consistent under the weaker missing-at-random (MAR) assumption. For FIML in the SEM context, the likelihood is modified to sum over the observed pattern of each individual:

$$\ell_{FIML} = -\frac{1}{2}\sum_{i=1}^n \left[\log|\boldsymbol{\Sigma}_{o_i}| + (\mathbf{x}_{o_i} - \boldsymbol{\mu}_{o_i})^\top \boldsymbol{\Sigma}_{o_i}^{-1}(\mathbf{x}_{o_i} - \boldsymbol{\mu}_{o_i})\right]$$

where the subscript $o_i$ denotes the observed components for subject $i$. FIML uses all available data simultaneously, is asymptotically equivalent to full-data ML, and is the gold standard for missing data in multivariate normal models.

The overarching principle governing sound multivariate analysis is this: every method, from PCA to SEM, is ultimately a model imposed on the sample covariance matrix. The fidelity of that model to the true population structure determines the validity of conclusions. Eigenvalues are statistics, not features of the world. Clusters are imposed structures, not discovered objects, unless the model that generates them is explicitly specified and validated. And discriminant functions are optimal only when their assumptions — normality, homogeneity, linearity — are approximately met in the population from which the data arose. Maintaining this critical stance while executing the mechanics fluently is what separates statistical analysis from numerical theater.
