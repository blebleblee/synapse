# Lesson 3: Linear Models & Regression

## 1. First-Principles Intuition & Invariants

The central ambition of linear regression is deceptively simple: given a collection of observations, find the linear function that best explains the variation in one quantity as a function of others. Yet embedded within this ambition lies one of the most consequential structures in all of applied mathematics—a bridge between geometric intuition, probabilistic inference, and computational linear algebra that has shaped statistics, econometrics, machine learning, and signal processing for three centuries.

The story begins with Legendre and Gauss, both of whom independently developed the method of least squares around 1805–1809. Gauss, characteristically, went further: he showed that if the errors corrupting one's measurements are normally distributed, then the least squares estimator is not merely convenient but optimal in a precise sense. This insight crystallized into what we now call the Gauss-Markov theorem, a result whose invariants govern every regression model you will ever fit.

### The Geometric Invariant: Projection onto a Subspace

Consider $n$ observations of a response variable arranged into a vector $\mathbf{y} \in \mathbb{R}^n$, and $p$ predictor variables forming a matrix $\mathbf{X} \in \mathbb{R}^{n \times p}$ (with the first column typically a vector of ones, encoding the intercept). The linear model asserts that $\mathbf{y}$ lies near a $p$-dimensional affine subspace of $\mathbb{R}^n$, the column space of $\mathbf{X}$, denoted $\text{col}(\mathbf{X})$.

The least squares problem asks: which point $\hat{\mathbf{y}} \in \text{col}(\mathbf{X})$ is closest to $\mathbf{y}$ in the Euclidean sense? The answer is the orthogonal projection of $\mathbf{y}$ onto $\text{col}(\mathbf{X})$. This is not merely an analogy; it is the precise geometric content of the method. The residual vector $\mathbf{e} = \mathbf{y} - \hat{\mathbf{y}}$ must be orthogonal to every column of $\mathbf{X}$, which is exactly the condition $\mathbf{X}^\top \mathbf{e} = \mathbf{0}$, or equivalently:

$$\mathbf{X}^\top (\mathbf{y} - \mathbf{X}\hat{\boldsymbol{\beta}}) = \mathbf{0}$$

This equation is the **normal equation**, and when $\mathbf{X}^\top \mathbf{X}$ is invertible, it yields the unique solution:

$$\hat{\boldsymbol{\beta}} = (\mathbf{X}^\top \mathbf{X})^{-1} \mathbf{X}^\top \mathbf{y}$$

The matrix $\mathbf{H} = \mathbf{X}(\mathbf{X}^\top \mathbf{X})^{-1} \mathbf{X}^\top$ is called the **hat matrix** because it maps $\mathbf{y}$ to its fitted values $\hat{\mathbf{y}} = \mathbf{H}\mathbf{y}$. It is an orthogonal projection operator: $\mathbf{H}^2 = \mathbf{H}$ and $\mathbf{H}^\top = \mathbf{H}$. Its complement $\mathbf{M} = \mathbf{I} - \mathbf{H}$ projects onto the orthogonal complement of $\text{col}(\mathbf{X})$, annihilating any component of $\mathbf{y}$ that the model can explain. These two operators partition $\mathbb{R}^n$ into the signal and the noise.

### The Probabilistic Invariant: The Classical Linear Model

The geometric derivation is distribution-free; least squares requires no probabilistic assumptions. To perform inference—to construct confidence intervals, test hypotheses, and assess significance—one must impose structure on the errors. The **classical linear model** (CLM) encodes five assumptions. The model is:

$$\mathbf{y} = \mathbf{X}\boldsymbol{\beta} + \boldsymbol{\varepsilon}$$

where $\boldsymbol{\varepsilon}$ is a random vector satisfying: $\mathbb{E}[\boldsymbol{\varepsilon}] = \mathbf{0}$ (zero mean), $\text{Var}(\boldsymbol{\varepsilon}) = \sigma^2 \mathbf{I}$ (homoscedasticity and uncorrelated errors), and $\mathbf{X}$ has full column rank $p$ (no exact multicollinearity). These are the Gauss-Markov assumptions. If additionally $\boldsymbol{\varepsilon} \sim \mathcal{N}(\mathbf{0}, \sigma^2 \mathbf{I})$, one obtains the normal linear model, which licenses exact $t$- and $F$-statistics in finite samples.

### The Gauss-Markov Theorem: Optimality of Least Squares

The Gauss-Markov theorem is the theoretical bedrock upon which the entire edifice of linear regression rests. It asserts that under the Gauss-Markov assumptions, the OLS estimator $\hat{\boldsymbol{\beta}}$ is the **Best Linear Unbiased Estimator** (BLUE): among all estimators of $\boldsymbol{\beta}$ that are (a) linear in $\mathbf{y}$ and (b) unbiased, it has the smallest variance for every linear combination $\mathbf{c}^\top \boldsymbol{\beta}$.

**Proof.** Let $\tilde{\boldsymbol{\beta}} = \mathbf{C}\mathbf{y}$ be any linear unbiased estimator of $\boldsymbol{\beta}$. Unbiasedness requires $\mathbb{E}[\mathbf{C}\mathbf{y}] = \boldsymbol{\beta}$ for all $\boldsymbol{\beta}$, which forces $\mathbf{C}\mathbf{X} = \mathbf{I}_p$. Write $\mathbf{C} = (\mathbf{X}^\top \mathbf{X})^{-1}\mathbf{X}^\top + \mathbf{D}$ where $\mathbf{D} = \mathbf{C} - (\mathbf{X}^\top \mathbf{X})^{-1}\mathbf{X}^\top$. The unbiasedness constraint $\mathbf{C}\mathbf{X} = \mathbf{I}_p$ then implies $\mathbf{D}\mathbf{X} = \mathbf{0}$. The variance of $\tilde{\boldsymbol{\beta}}$ is:

$$\text{Var}(\tilde{\boldsymbol{\beta}}) = \sigma^2 \mathbf{C}\mathbf{C}^\top = \sigma^2 \left[(\mathbf{X}^\top \mathbf{X})^{-1} + \mathbf{D}\mathbf{D}^\top\right]$$

The cross terms vanish because $\mathbf{D}\mathbf{X} = \mathbf{0}$ implies $(\mathbf{X}^\top \mathbf{X})^{-1}\mathbf{X}^\top \mathbf{D}^\top = \mathbf{0}$. Since $\mathbf{D}\mathbf{D}^\top$ is positive semidefinite, we conclude:

$$\text{Var}(\tilde{\boldsymbol{\beta}}) - \text{Var}(\hat{\boldsymbol{\beta}}) = \sigma^2 \mathbf{D}\mathbf{D}^\top \succeq \mathbf{0}$$

This completes the proof. The OLS estimator achieves the minimum variance among all linear unbiased competitors, and equality holds if and only if $\mathbf{D} = \mathbf{0}$, i.e., $\tilde{\boldsymbol{\beta}} = \hat{\boldsymbol{\beta}}$. $\blacksquare$

The critical invariant to internalize is what Gauss-Markov does *not* say: it does not claim OLS is optimal among all estimators, nor among biased estimators. Ridge regression, LASSO, and James-Stein estimators can all dominate OLS in mean squared error by accepting bias in exchange for reduced variance. Gauss-Markov is a theorem about the linear unbiased class, and that class is exactly where classical regression lives.

### ANOVA Decomposition and the Coefficient of Determination

A fundamental algebraic identity, itself a consequence of the projection geometry, decomposes total variation in $\mathbf{y}$ into explained and unexplained parts. When the model includes an intercept, one can show:

$$\underbrace{\sum_{i=1}^n (y_i - \bar{y})^2}_{\text{SST}} = \underbrace{\sum_{i=1}^n (\hat{y}_i - \bar{y})^2}_{\text{SSR}} + \underbrace{\sum_{i=1}^n (y_i - \hat{y}_i)^2}_{\text{SSE}}$$

This is the **ANOVA decomposition**, also written $\text{SST} = \text{SSR} + \text{SSE}$. The identity holds because $\hat{\mathbf{y}}$ and $\mathbf{e}$ are orthogonal by construction. The **coefficient of determination** is:

$$R^2 = \frac{\text{SSR}}{\text{SST}} = 1 - \frac{\text{SSE}}{\text{SST}}$$

$R^2$ measures the proportion of total variance explained by the fitted model. It increases monotonically with the number of predictors, which motivates the **adjusted** $R^2$:

$$\bar{R}^2 = 1 - \frac{\text{SSE}/(n-p)}{\text{SST}/(n-1)} = 1 - (1 - R^2)\frac{n-1}{n-p}$$

This penalizes model complexity by using the degrees-of-freedom-adjusted mean squares rather than raw sums. The $F$-statistic for the overall significance of the regression is:

$$F = \frac{\text{SSR}/(p-1)}{\text{SSE}/(n-p)} \sim F_{p-1,\, n-p}$$

under the null hypothesis $H_0: \beta_1 = \cdots = \beta_{p-1} = 0$. The distributional result follows from the fact that $\text{SSR}/\sigma^2 \sim \chi^2_{p-1}$ and $\text{SSE}/\sigma^2 \sim \chi^2_{n-p}$, and these two chi-squared variates are independent—a consequence of the orthogonality of the projection operators $\mathbf{H}$ and $\mathbf{M} = \mathbf{I} - \mathbf{H}$.

---

## 2. Core Architecture & Mechanics

### The Numerical Pipeline: From Data Matrix to Inference

Understanding regression computationally requires understanding how the normal equation $\hat{\boldsymbol{\beta}} = (\mathbf{X}^\top \mathbf{X})^{-1} \mathbf{X}^\top \mathbf{y}$ is actually evaluated in practice. A naive practitioner might form $\mathbf{X}^\top \mathbf{X}$ explicitly and then invert it—this is numerically disastrous. The condition number of $\mathbf{X}^\top \mathbf{X}$ is the square of the condition number of $\mathbf{X}$, so any mild ill-conditioning in the design matrix is catastrophically amplified. All serious numerical implementations use orthogonal decomposition instead.

The **QR decomposition** of $\mathbf{X}$ writes $\mathbf{X} = \mathbf{Q}\mathbf{R}$, where $\mathbf{Q} \in \mathbb{R}^{n \times p}$ has orthonormal columns ($\mathbf{Q}^\top \mathbf{Q} = \mathbf{I}_p$) and $\mathbf{R} \in \mathbb{R}^{p \times p}$ is upper triangular with positive diagonal entries (assuming $\mathbf{X}$ has full column rank). Substituting into the normal equation:

$$(\mathbf{X}^\top \mathbf{X})^{-1} \mathbf{X}^\top \mathbf{y} = (\mathbf{R}^\top \mathbf{Q}^\top \mathbf{Q} \mathbf{R})^{-1} \mathbf{R}^\top \mathbf{Q}^\top \mathbf{y} = \mathbf{R}^{-1} \mathbf{Q}^\top \mathbf{y}$$

This reduces to solving the upper triangular system $\mathbf{R}\hat{\boldsymbol{\beta}} = \mathbf{Q}^\top \mathbf{y}$ by back substitution—numerically stable and $O(np^2)$ in cost. The fitted values become $\hat{\mathbf{y}} = \mathbf{Q}\mathbf{Q}^\top \mathbf{y}$, making the hat matrix $\mathbf{H} = \mathbf{Q}\mathbf{Q}^\top$ transparently a projection onto the column space of $\mathbf{Q}$ (which equals that of $\mathbf{X}$).

For near-rank-deficient or rank-deficient problems, the **singular value decomposition** $\mathbf{X} = \mathbf{U}\mathbf{\Sigma}\mathbf{V}^\top$ provides the most complete picture. The Moore-Penrose pseudoinverse $\mathbf{X}^+ = \mathbf{V}\mathbf{\Sigma}^+\mathbf{U}^\top$ yields the minimum-norm least squares solution $\hat{\boldsymbol{\beta}} = \mathbf{X}^+\mathbf{y}$, where $\mathbf{\Sigma}^+$ replaces each nonzero singular value $\sigma_i$ by $1/\sigma_i$ and leaves zeros as zeros. The singular values also directly reveal multicollinearity: if $\sigma_p \approx 0$, the design matrix is nearly rank-deficient, and the corresponding linear combination of predictors is nearly unidentifiable from the data.

The computational signal path for a complete regression analysis can be summarized as follows:

```
Raw Data Matrix X ∈ ℝ^{n×p}
        │
        ▼
  Column centering / scaling
  (standardization for interpretability,
   or orthogonal polynomials for numerical stability)
        │
        ▼
  QR Decomposition: X = QR
  ┌─────────────────────────┐
  │  Q: n×p orthonormal     │
  │  R: p×p upper triangular│
  └─────────────────────────┘
        │
        ▼
  Solve R β̂ = Q^T y   (back substitution, O(p²))
        │
        ▼
  Compute ŷ = QQ^T y, residuals e = y - ŷ
        │
        ▼
  Estimate σ² = ||e||² / (n - p)
        │
        ▼
  Covariance: Var(β̂) = σ² (X^T X)^{-1} = σ² (R^T R)^{-1}
        │
        ▼
  Inference: t-statistics, F-tests, confidence intervals
        │
        ▼
  Diagnostics: leverage h_ii, Cook's distance, VIF
```

### Estimation of $\sigma^2$ and Its Role in Inference

The error variance $\sigma^2$ is unknown and must be estimated from the residuals. The natural estimator is:

$$\hat{\sigma}^2 = \frac{\mathbf{e}^\top \mathbf{e}}{n - p} = \frac{\text{SSE}}{n-p}$$

The denominator $n - p$ is the residual degrees of freedom, the dimension of the orthogonal complement of $\text{col}(\mathbf{X})$ in $\mathbb{R}^n$. To see why this denominator yields an unbiased estimator, note that $\mathbb{E}[\text{SSE}] = \mathbb{E}[\mathbf{y}^\top \mathbf{M} \mathbf{y}]$. Since $\mathbf{M}\mathbf{X} = \mathbf{0}$:

$$\mathbb{E}[\mathbf{y}^\top \mathbf{M} \mathbf{y}] = \mathbb{E}[\boldsymbol{\varepsilon}^\top \mathbf{M} \boldsymbol{\varepsilon}] = \sigma^2 \text{tr}(\mathbf{M}) = \sigma^2(n - p)$$

The last step uses the cyclic trace identity and the fact that $\mathbf{M}$ is a projection of rank $n - p$. Thus $\mathbb{E}[\hat{\sigma}^2] = \sigma^2$, confirming unbiasedness.

The standard error of the $j$-th coefficient estimate is $\text{SE}(\hat{\beta}_j) = \hat{\sigma}\sqrt{[(\mathbf{X}^\top \mathbf{X})^{-1}]_{jj}}$, and under normality:

$$t_j = \frac{\hat{\beta}_j - \beta_j}{\text{SE}(\hat{\beta}_j)} \sim t_{n-p}$$

which provides the basis for individual coefficient tests and confidence intervals.

### Residual Analysis: Diagnosing Model Adequacy

Residuals are not merely the difference between fitted and observed values; they are the primary diagnostic instrument for assessing whether the CLM assumptions hold. The raw residuals $e_i = y_i - \hat{y}_i$ are, however, not identically distributed even when the errors $\varepsilon_i$ are. The variance of the $i$-th residual is $\text{Var}(e_i) = \sigma^2(1 - h_{ii})$, where $h_{ii} = [\mathbf{H}]_{ii}$ is the **leverage** of observation $i$—its diagonal element in the hat matrix. Points with high leverage sit far from the centroid of the predictor space and exert disproportionate influence on the fitted hyperplane.

This heterogeneity motivates **internally studentized residuals**:

$$r_i = \frac{e_i}{\hat{\sigma}\sqrt{1 - h_{ii}}}$$

and **externally studentized residuals** (also called deleted residuals or $t$-residuals):

$$t_i = \frac{e_i}{\hat{\sigma}_{(i)}\sqrt{1 - h_{ii}}}$$

where $\hat{\sigma}_{(i)}$ is the error standard deviation estimated with observation $i$ deleted. By a Sherman-Morrison-Woodbury identity, $\hat{\sigma}_{(i)}^2(n-p-1) = \hat{\sigma}^2(n-p) - e_i^2/(1-h_{ii})$, so the deletion need not be computed by literally refitting the model. Under the normal linear model, $t_i \sim t_{n-p-1}$, enabling formal outlier tests.

**Cook's distance** combines leverage and residual magnitude into a single influence measure:

$$D_i = \frac{(\hat{\boldsymbol{\beta}} - \hat{\boldsymbol{\beta}}_{(i)})^\top \mathbf{X}^\top \mathbf{X} (\hat{\boldsymbol{\beta}} - \hat{\boldsymbol{\beta}}_{(i)})}{p\hat{\sigma}^2} = \frac{r_i^2}{p} \cdot \frac{h_{ii}}{1 - h_{ii}}$$

The second equality is an algebraic identity that makes Cook's distance computable without deletion. Values of $D_i$ exceeding 4/n or 1 (depending on the convention) warrant close inspection. The factored form reveals the two routes to influence: an observation can be influential by having a large standardized residual ($r_i^2$ large), by having high leverage ($h_{ii}$ close to 1), or both.

### Multicollinearity: Diagnosis and Geometric Meaning

When two or more columns of $\mathbf{X}$ are approximately linearly dependent, the matrix $\mathbf{X}^\top \mathbf{X}$ becomes nearly singular, the OLS estimator has enormous variance, and coefficient estimates become unstable—small perturbations to the data or the model produce wildly different $\hat{\boldsymbol{\beta}}$ values. This pathology is **multicollinearity**, and it deserves precise mathematical characterization rather than intuitive description.

The severity of multicollinearity for predicting $\beta_j$ is measured by the **Variance Inflation Factor**:

$$\text{VIF}_j = \frac{1}{1 - R_j^2}$$

where $R_j^2$ is the coefficient of determination from regressing the $j$-th predictor on all remaining predictors. The geometric reading is direct: $1 - R_j^2$ is the squared sine of the angle between the $j$-th column of $\mathbf{X}$ and the subspace spanned by the other columns. When $R_j^2 \to 1$, the $j$-th predictor is nearly in the span of the others, the angle approaches zero, and the variance of $\hat{\beta}_j$ is inflated by the factor $\text{VIF}_j \to \infty$.

The connection to the singular value decomposition is illuminating: if $\mathbf{X} = \mathbf{U}\mathbf{\Sigma}\mathbf{V}^\top$, then the variance of the OLS estimator is $\text{Var}(\hat{\boldsymbol{\beta}}) = \sigma^2 \mathbf{V} \mathbf{\Sigma}^{-2} \mathbf{V}^\top$, so a small singular value $\sigma_k$ produces an enormous variance in the direction of the corresponding right singular vector $\mathbf{v}_k$. The **condition number** $\kappa = \sigma_1 / \sigma_p$ quantifies the overall degree of ill-conditioning; values above 30 indicate moderate multicollinearity, and above 100, severe.

---

## 3. High-Performance Optimization & Failure Modes

### Weighted Least Squares: When Homoscedasticity Fails

The Gauss-Markov theorem assumes $\text{Var}(\boldsymbol{\varepsilon}) = \sigma^2 \mathbf{I}$. When this fails—when different observations have different error variances or correlated errors—OLS remains unbiased but is no longer BLUE. The generalized least squares (GLS) framework handles this by accounting for the covariance structure of the errors.

Suppose $\text{Var}(\boldsymbol{\varepsilon}) = \sigma^2 \mathbf{\Omega}$ where $\mathbf{\Omega}$ is a known positive definite matrix. Since $\mathbf{\Omega}$ is positive definite, it admits a Cholesky decomposition $\mathbf{\Omega} = \mathbf{L}\mathbf{L}^\top$. Premultiplying the model by $\mathbf{L}^{-1}$ yields:

$$\mathbf{L}^{-1}\mathbf{y} = \mathbf{L}^{-1}\mathbf{X}\boldsymbol{\beta} + \mathbf{L}^{-1}\boldsymbol{\varepsilon}$$

The transformed errors $\mathbf{L}^{-1}\boldsymbol{\varepsilon}$ satisfy $\text{Var}(\mathbf{L}^{-1}\boldsymbol{\varepsilon}) = \sigma^2 \mathbf{I}$, so OLS applied to the transformed model yields the GLS estimator:

$$\hat{\boldsymbol{\beta}}_{\text{GLS}} = (\mathbf{X}^\top \mathbf{\Omega}^{-1} \mathbf{X})^{-1} \mathbf{X}^\top \mathbf{\Omega}^{-1} \mathbf{y}$$

which is BLUE within the larger class of linear models with error covariance $\sigma^2 \mathbf{\Omega}$.

The practically important special case is **weighted least squares** (WLS), where $\mathbf{\Omega} = \text{diag}(w_1^{-1}, \ldots, w_n^{-1})$ and each $w_i$ is a known positive weight. The WLS criterion minimizes:

$$Q(\boldsymbol{\beta}) = \sum_{i=1}^n w_i (y_i - \mathbf{x}_i^\top \boldsymbol{\beta})^2 = (\mathbf{y} - \mathbf{X}\boldsymbol{\beta})^\top \mathbf{W} (\mathbf{y} - \mathbf{X}\boldsymbol{\beta})$$

where $\mathbf{W} = \text{diag}(w_1, \ldots, w_n)$. The WLS normal equations are $\mathbf{X}^\top \mathbf{W} \mathbf{X} \hat{\boldsymbol{\beta}} = \mathbf{X}^\top \mathbf{W} \mathbf{y}$, with solution:

$$\hat{\boldsymbol{\beta}}_{\text{WLS}} = (\mathbf{X}^\top \mathbf{W} \mathbf{X})^{-1} \mathbf{X}^\top \mathbf{W} \mathbf{y}$$

Weights are determined by the error structure of the application. If group $i$ is the mean of $n_i$ replicate measurements with common variance $\sigma^2$, then $w_i = n_i$. If the variance of observation $i$ is proportional to some known function $v(\mu_i)$ of its mean (a pattern characteristic of exponential family distributions), then $w_i = 1/v(\mu_i)$.

### Ridge Regression and the Bias-Variance Tradeoff

When multicollinearity is severe, one abandons the unbiasedness requirement and accepts controlled bias in exchange for substantially reduced variance. **Ridge regression** (Tikhonov regularization) modifies the OLS criterion by adding a quadratic penalty on the coefficient vector:

$$Q_\lambda(\boldsymbol{\beta}) = \|\mathbf{y} - \mathbf{X}\boldsymbol{\beta}\|^2 + \lambda \|\boldsymbol{\beta}\|^2, \quad \lambda > 0$$

The ridge estimator is:

$$\hat{\boldsymbol{\beta}}_\lambda = (\mathbf{X}^\top \mathbf{X} + \lambda \mathbf{I})^{-1} \mathbf{X}^\top \mathbf{y}$$

The addition of $\lambda \mathbf{I}$ to the singular (or nearly singular) $\mathbf{X}^\top \mathbf{X}$ guarantees invertibility regardless of the design. In the SVD representation $\mathbf{X} = \mathbf{U}\mathbf{\Sigma}\mathbf{V}^\top$:

$$\hat{\boldsymbol{\beta}}_\lambda = \sum_{k=1}^p \frac{\sigma_k}{\sigma_k^2 + \lambda} \mathbf{v}_k \mathbf{u}_k^\top \mathbf{y}$$

contrasted with the OLS estimator $\hat{\boldsymbol{\beta}} = \sum_{k=1}^p \sigma_k^{-1} \mathbf{v}_k \mathbf{u}_k^\top \mathbf{y}$. Ridge shrinks each principal component's contribution by the factor $\sigma_k^2/(\sigma_k^2 + \lambda)$, applying the most shrinkage to the directions corresponding to small singular values—precisely the directions that OLS estimates most unreliably. The mean squared error of the ridge estimator is:

$$\text{MSE}(\hat{\boldsymbol{\beta}}_\lambda) = \underbrace{\sigma^2 \sum_{k=1}^p \frac{\sigma_k^2}{(\sigma_k^2+\lambda)^2}}_{\text{variance}} + \underbrace{\lambda^2 \sum_{k=1}^p \frac{(\mathbf{v}_k^\top \boldsymbol{\beta})^2}{(\sigma_k^2+\lambda)^2}}_{\text{bias}^2}$$

For small $\lambda$, the derivative of MSE with respect to $\lambda$ at $\lambda = 0$ is negative when $\sigma^2 \sum_k \sigma_k^{-4} > \|\boldsymbol{\beta}\|^2 / \sigma^4$, confirming that there always exists a small positive $\lambda$ for which ridge dominates OLS in MSE. This provides the theoretical basis for regularization—Gauss-Markov's conclusion that OLS is BLUE is not contradicted, because ridge is biased.

### Generalized Linear Models: Extending the Linear Predictor

Classical linear regression makes two structural choices simultaneously: a Gaussian error distribution, and an identity link between the linear predictor $\eta_i = \mathbf{x}_i^\top \boldsymbol{\beta}$ and the conditional mean $\mu_i = \mathbb{E}[y_i \mid \mathbf{x}_i]$. **Generalized linear models** (GLMs), introduced by Nelder and Wedderburn (1972), decouple these choices, allowing the response distribution to be any member of the exponential family and the relationship between $\mu_i$ and $\eta_i$ to be mediated by a **link function** $g$:

$$g(\mu_i) = \eta_i = \mathbf{x}_i^\top \boldsymbol{\beta}$$

The exponential family parameterization writes the probability mass or density function as:

$$f(y_i; \theta_i, \phi) = \exp\!\left(\frac{y_i \theta_i - b(\theta_i)}{a(\phi)} + c(y_i, \phi)\right)$$

where $\theta_i$ is the natural (canonical) parameter, $\phi$ is the dispersion parameter, and $b(\cdot)$, $a(\cdot)$, $c(\cdot)$ are known functions specific to the distribution. The mean and variance of $y_i$ are $\mathbb{E}[y_i] = b'(\theta_i)$ and $\text{Var}(y_i) = a(\phi) b''(\theta_i)$, so the variance function $V(\mu) = b''(\theta(\mu))$ completely characterizes the mean-variance relationship for each exponential family member.

The **canonical link** function is $g = (b')^{-1}$, which sets $\theta_i = \eta_i$. For the Gaussian, the canonical link is the identity; for the Bernoulli, it is the logit; for the Poisson, it is the logarithm. Using the canonical link produces the simplest score equations and is often (though not always) the most interpretable choice.

### Logistic Regression: Binary Response

When the response $y_i \in \{0, 1\}$, the natural model assumes $y_i \sim \text{Bernoulli}(\pi_i)$ with $\pi_i = \mathbb{P}(y_i = 1 \mid \mathbf{x}_i)$. Logistic regression applies the logit link:

$$\log\frac{\pi_i}{1 - \pi_i} = \mathbf{x}_i^\top \boldsymbol{\beta}$$

Inverting: $\pi_i = \sigma(\mathbf{x}_i^\top \boldsymbol{\beta})$ where $\sigma(z) = (1 + e^{-z})^{-1}$ is the logistic sigmoid. The log-likelihood is:

$$\ell(\boldsymbol{\beta}) = \sum_{i=1}^n \left[y_i \mathbf{x}_i^\top \boldsymbol{\beta} - \log(1 + e^{\mathbf{x}_i^\top \boldsymbol{\beta}})\right]$$

The score equation $\nabla \ell = \mathbf{X}^\top (\mathbf{y} - \boldsymbol{\pi}) = \mathbf{0}$ has no closed-form solution, but the Hessian $\nabla^2 \ell = -\mathbf{X}^\top \mathbf{W} \mathbf{X}$ where $\mathbf{W} = \text{diag}(\pi_i(1-\pi_i))$ is negative semidefinite everywhere, so $\ell$ is concave and Newton-Raphson converges globally whenever the maximum exists. The Newton step takes the form:

$$\boldsymbol{\beta}^{(t+1)} = \boldsymbol{\beta}^{(t)} + (\mathbf{X}^\top \mathbf{W}^{(t)} \mathbf{X})^{-1} \mathbf{X}^\top (\mathbf{y} - \boldsymbol{\pi}^{(t)})$$

which can be rewritten as a WLS step on a working response vector $\mathbf{z}^{(t)} = \mathbf{X}\boldsymbol{\beta}^{(t)} + (\mathbf{W}^{(t)})^{-1}(\mathbf{y} - \boldsymbol{\pi}^{(t)})$. This reformulation—**Iteratively Reweighted Least Squares** (IRLS)—holds for all GLMs and reveals that every GLM can be fit by a sequence of WLS problems, converging to the MLE.

Coefficient $\beta_j$ has the interpretation that a one-unit increase in $x_j$, holding others fixed, multiplies the odds $\pi_i/(1-\pi_i)$ by $e^{\beta_j}$. This is the **odds ratio** interpretation, and it is exact (not approximate) within the logistic model.

The maximum likelihood estimator fails to exist (is infinite) when the data are **perfectly separated**: there exists a hyperplane $\mathbf{x}^\top \boldsymbol{\beta} = 0$ that perfectly classifies all training observations. The IRLS algorithm signals this failure through exploding coefficient estimates and working weight matrices approaching zero. Detection requires inspecting the data geometrically, and the solution is either to impose regularization ($\ell_2$ or Firth's penalized likelihood) or to acknowledge that the data support arbitrarily strong claims about the boundary.

### Poisson Regression: Count Data

For count responses $y_i \in \{0, 1, 2, \ldots\}$, the natural model is $y_i \sim \text{Poisson}(\mu_i)$, with the log link:

$$\log(\mu_i) = \mathbf{x}_i^\top \boldsymbol{\beta}$$

ensuring that fitted means $\hat{\mu}_i = \exp(\mathbf{x}_i^\top \hat{\boldsymbol{\beta}})$ remain positive. The log-likelihood is:

$$\ell(\boldsymbol{\beta}) = \sum_{i=1}^n \left[y_i \mathbf{x}_i^\top \boldsymbol{\beta} - e^{\mathbf{x}_i^\top \boldsymbol{\beta}} - \log(y_i!)\right]$$

The score equation $\mathbf{X}^\top (\mathbf{y} - \boldsymbol{\mu}) = \mathbf{0}$ again yields no closed form, but IRLS with weights $w_i = \mu_i$ converges to the MLE. The Poisson model constrains $\text{Var}(y_i) = \mathbb{E}[y_i] = \mu_i$—the equidispersion assumption. Real count data frequently exhibit **overdispersion**: $\text{Var}(y_i) > \mu_i$, arising from unobserved heterogeneity, clustering, or excess zeros. The standard diagnostic is Pearson's $\chi^2$ statistic divided by its degrees of freedom:

$$\hat{\phi} = \frac{\sum_{i=1}^n (y_i - \hat{\mu}_i)^2 / \hat{\mu}_i}{n - p}$$

If $\hat{\phi} \gg 1$, the Poisson model is misspecified. Remedies include the **negative binomial regression** model (which introduces a free variance parameter $\phi$), **quasi-Poisson** (which uses Poisson estimating equations but scales standard errors by $\sqrt{\hat{\phi}}$), and zero-inflated models when the excess variation is concentrated at zero.

An important extension arises when observations represent counts over different exposure periods or areas. If observation $i$ is a count over exposure $t_i$, the natural model is $\log(\mu_i/t_i) = \mathbf{x}_i^\top \boldsymbol{\beta}$, equivalently $\log(\mu_i) = \mathbf{x}_i^\top \boldsymbol{\beta} + \log(t_i)$. The term $\log(t_i)$ is an **offset**—a known component of the linear predictor whose coefficient is fixed at 1—and it correctly normalizes the rate before modeling.

### Model Selection and the Information-Theoretic Framework

Classical hypothesis testing (likelihood ratio tests, $F$-tests for nested models) answers the question of whether a reduced model fits significantly worse than a larger one. It does not directly address the question of choosing among non-nested models or of trading off fit against complexity. For this, information-theoretic criteria provide a principled framework.

The **Akaike Information Criterion** is:

$$\text{AIC} = -2\ell(\hat{\boldsymbol{\beta}}) + 2p$$

where $\ell(\hat{\boldsymbol{\beta}})$ is the maximized log-likelihood and $p$ is the number of estimated parameters. The AIC estimates, up to an additive constant, the expected Kullback-Leibler divergence from the true data-generating process to the fitted model. The penalty $2p$ corrects for the upward bias in the maximized log-likelihood as an estimator of generalization. The small-sample corrected version **AICc** adds a further term $2p(p+1)/(n-p-1)$, which becomes negligible as $n/p \to \infty$.

The **Bayesian Information Criterion** is:

$$\text{BIC} = -2\ell(\hat{\boldsymbol{\beta}}) + p\log n$$

The larger penalty $p \log n$ (which exceeds $2p$ for $n > e^2 \approx 7.4$) reflects BIC's derivation as an approximation to the log marginal likelihood under a default prior, and it enforces stronger parsimony as $n$ grows. BIC is consistent for model selection under regularity conditions—as $n \to \infty$, it selects the true model with probability one if the true model is in the candidate set—whereas AIC is not consistent but minimizes asymptotic prediction error.

The practitioner's invariant: AIC is preferable when predictive accuracy is the goal; BIC is preferable when identifying the true model structure is the goal. Neither should be treated as a hypothesis test. The difference $\Delta\text{AIC} = \text{AIC}_k - \text{AIC}_{\min}$ of less than 2 indicates models with comparable empirical support; differences above 10 indicate essentially no support for the worse model. These thresholds derive from Akaike weights $w_k = \exp(-\Delta\text{AIC}_k/2) / \sum_j \exp(-\Delta\text{AIC}_j/2)$, which are interpretable as posterior probabilities over the model set under a flat prior, providing a natural framework for multi-model inference and model averaging.
