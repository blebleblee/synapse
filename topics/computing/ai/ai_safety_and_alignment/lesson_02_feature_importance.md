# Lesson 2: Feature Importance and Sensitivity Analysis in AI Safety

## 1. First-Principles Foundations

### Why Interpretability Is a Safety Property

Feature importance and sensitivity analysis are not merely diagnostic conveniences—they are foundational safety properties. A model that produces correct outputs for inscrutable reasons is not safer than one that produces wrong outputs; it is dangerous in a different and often harder-to-detect way. When a system cannot be audited, biases cannot be found, failure modes cannot be predicted, and trust cannot be justified.

The core thesis is this: **a model is aligned only insofar as we can verify what it is responding to**. If a fraud-detection model is secretly using postal code as a proxy for race, permutation importance will expose it. If an autonomous vehicle's steering network is responding to irrelevant sensor artifacts, Sobol indices will localize them. The analytical tools in this lesson are, in a very direct sense, alignment verification tools.

### Information-Theoretic Grounding

Feature importance can be formalized through mutual information. For a feature $X_i$ and model output $Y$, the mutual information is:

$$
I(X_i; Y) = \sum_{x \in \mathcal{X}} \sum_{y \in \mathcal{Y}} p(x, y) \log \frac{p(x, y)}{p(x)\,p(y)}
$$

For continuous variables this becomes:

$$
I(X_i; Y) = \int_{\mathcal{X}} \int_{\mathcal{Y}} p(x, y) \log \frac{p(x, y)}{p(x)\,p(y)}\, dy\, dx
$$

$I(X_i; Y) = 0$ if and only if $X_i$ and $Y$ are statistically independent. This establishes a principled lower bound: a feature with zero mutual information contributes nothing to prediction and can be safely dropped. Crucially, mutual information is **invariant under invertible transformations** of either variable, which makes it more reliable than correlation-based measures that assume linearity.

The conditional mutual information $I(X_i; Y \mid X_{\setminus i})$ quantifies the *unique* contribution of $X_i$ after accounting for all other features—the quantity permutation importance approximates empirically without requiring density estimation.

### Variance Decomposition: The ANOVA Functional Decomposition

The theoretical backbone of Sobol analysis is the **Hoeffding-Sobol (ANOVA) decomposition**. For a square-integrable function $f : [0,1]^d \to \mathbb{R}$ of independent uniform inputs $X = (X_1, \ldots, X_d)$:

$$
f(X) = f_0 + \sum_i f_i(X_i) + \sum_{i < j} f_{ij}(X_i, X_j) + \cdots + f_{1,2,\ldots,d}(X_1, \ldots, X_d)
$$

where $f_0 = \mathbb{E}[f(X)]$, and each term integrates to zero over any of its arguments. This decomposition is **unique** under the constraint that all constituent functions are orthogonal with respect to the uniform measure. Squaring and integrating yields the variance decomposition:

$$
\mathrm{Var}(Y) = \sum_i V_i + \sum_{i<j} V_{ij} + \cdots + V_{1,\ldots,d}
$$

where $V_i = \mathrm{Var}(\mathbb{E}[Y \mid X_i])$ and $V_{ij} = \mathrm{Var}(\mathbb{E}[Y \mid X_i, X_j]) - V_i - V_j$. This is not an approximation—it is exact for independent inputs.

The independence assumption is critical. When features are correlated, the decomposition is no longer unique and Sobol indices can assign importance to features that are not causally relevant. This is a known, non-trivial failure mode discussed in Section 4.

---

## 2. Core Methods: Architecture and Mechanics

### 2.1 Permutation Feature Importance (PFI)

PFI was introduced by Breiman (2001) in the context of Random Forests and later generalized by Fisher, Rudin, and Dominici (2019) as model-agnostic "Model Reliance." The mechanism is conceptually clean: a feature is important if the model *relies* on it, and we detect reliance by breaking the feature's signal.

**Algorithm:**

```text
Given: trained model f, validation set D = {(x^(n), y^(n))}, metric L
Baseline: s_0 = L(f, D)
For each feature j in {1, ..., d}:
    For k in {1, ..., K}:
        D_k^j = D with column j randomly permuted
        s_k^j = L(f, D_k^j)
    Importance(j) = mean_k(s_k^j - s_0)   # positive = performance drop
```

The permutation breaks the joint distribution $p(X_j, Y)$ while preserving the marginal $p(X_j)$, so the model still receives plausible values for feature $j$—just values that carry no information about $y$. The resulting drop in $L$ measures how much the model was relying on that signal.

**Architectural consequences:**

- PFI measures reliance on marginal information. It does *not* detect features that are important only in combination with others (interaction effects). A feature that is useless alone but essential in concert with another will show low PFI.
- PFI on the training set measures memorization; PFI on a held-out validation set measures generalization. Use the validation set.
- For correlated features, PFI produces misleading results: shuffling $X_j$ creates out-of-distribution (OOD) samples that expose the model to inputs it was never trained on, inflating apparent importance for correlated partners.

**Production-grade Python implementation with confidence intervals:**

```python
import numpy as np
from sklearn.base import is_classifier
from sklearn.metrics import check_scoring
from typing import Callable, Optional
import pandas as pd
from dataclasses import dataclass, field


@dataclass
class PFIResult:
    feature_names: list[str]
    importances_mean: np.ndarray
    importances_std: np.ndarray
    importances_raw: np.ndarray  # shape: (n_features, n_repeats)

    def as_dataframe(self) -> pd.DataFrame:
        return pd.DataFrame(
            {
                "feature": self.feature_names,
                "importance_mean": self.importances_mean,
                "importance_std": self.importances_std,
            }
        ).sort_values("importance_mean", ascending=False).reset_index(drop=True)


def permutation_feature_importance(
    model,
    X: np.ndarray,
    y: np.ndarray,
    scoring: str | Callable = "neg_mean_squared_error",
    n_repeats: int = 30,
    random_state: Optional[int] = 42,
    feature_names: Optional[list[str]] = None,
    n_jobs: int = 1,
) -> PFIResult:
    """
    Model-agnostic permutation feature importance with confidence intervals.

    Parameters
    ----------
    model      : Fitted estimator with a predict (or predict_proba) method.
    X          : Validation features, shape (n_samples, n_features).
    y          : Validation targets, shape (n_samples,).
    scoring    : sklearn-compatible scorer name or callable.
    n_repeats  : Number of shuffles per feature; 30 is typically sufficient.
    random_state : Seed for reproducibility.
    feature_names : Optional list of feature names for labeling.
    n_jobs     : Parallel workers (-1 = all cores). Requires joblib.

    Returns
    -------
    PFIResult dataclass with per-feature importance distributions.
    """
    rng = np.random.default_rng(random_state)
    scorer = check_scoring(model, scoring=scoring)

    n_features = X.shape[1]
    if feature_names is None:
        feature_names = [f"feature_{i}" for i in range(n_features)]

    baseline_score = scorer(model, X, y)

    def _permute_one_feature(j: int) -> np.ndarray:
        scores = np.empty(n_repeats)
        X_permuted = X.copy()
        for k in range(n_repeats):
            X_permuted[:, j] = rng.permutation(X[:, j])
            scores[k] = scorer(model, X_permuted, y)
        return baseline_score - scores  # positive = importance

    if n_jobs != 1:
        from joblib import Parallel, delayed
        raw = np.array(
            Parallel(n_jobs=n_jobs)(
                delayed(_permute_one_feature)(j) for j in range(n_features)
            )
        )
    else:
        raw = np.array([_permute_one_feature(j) for j in range(n_features)])

    return PFIResult(
        feature_names=feature_names,
        importances_mean=raw.mean(axis=1),
        importances_std=raw.std(axis=1),
        importances_raw=raw,
    )


# --- Usage example ---
if __name__ == "__main__":
    from sklearn.datasets import make_regression
    from sklearn.ensemble import GradientBoostingRegressor
    from sklearn.model_selection import train_test_split

    X, y = make_regression(n_samples=2000, n_features=15, n_informative=5,
                            noise=0.1, random_state=0)
    X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2,
                                                       random_state=0)

    model = GradientBoostingRegressor(n_estimators=200, random_state=0)
    model.fit(X_train, y_train)

    result = permutation_feature_importance(
        model, X_val, y_val,
        scoring="neg_mean_squared_error",
        n_repeats=30,
        n_jobs=-1,
    )
    print(result.as_dataframe().head(10))
```

### 2.2 Sobol Sensitivity Indices

Sobol indices are the gold standard for **global** sensitivity analysis.

They decompose the variance of a model's output into contributions from individual features (first-order indices) and interactions (higher-order indices), providing a complete variance-based attribution framework. Unlike permutation importance, which measures predictive degradation, Sobol indices quantify what fraction of output variance is *driven* by each input's uncertainty. This distinction is critical in AI safety: permutation importance tells you which features the model relies on for prediction accuracy, while Sobol indices reveal which input uncertainties propagate most strongly to output uncertainty—essential for robustness analysis, adversarial defense, and understanding failure modes under distribution shift. Computing Sobol indices requires evaluating the model across a structured sample of the input space (typically via quasi-Monte Carlo or polynomial chaos methods), making them computationally expensive but uniquely interpretable. For safety-critical AI systems, the investment is justified: Sobol first-order indices identify which features dominate output variance independently, while total-order indices capture all effects including interactions, exposing hidden dependencies that could be exploited or lead to emergent risks.

Both permutation feature importance and Sobol sensitivity analysis serve complementary roles in the AI safety practitioner's diagnostic arsenal. Permutation importance is fast, model-agnostic, and reveals which features the model *uses* for decisions—ideal for debugging, feature selection, and explaining model behavior to stakeholders. Sobol indices are rigorous, variance-decomposing, and reveal which input uncertainties *matter* for output uncertainty—essential for risk quantification, robustness certification, and aligning model behavior with safety constraints under distributional uncertainty. Together, they provide a layered understanding: permutation importance for operational debugging and interpretability, Sobol indices for formal verification and uncertainty quantification in high-stakes deployment. Practitioners should default to permutation importance for iterative development and model auditing, escalating to Sobol analysis when formal safety cases, regulatory compliance, or adversarial robustness guarantees are required.

## Summary & Verification Matrix

| **Invariant / Mechanism** | **Mathematical Form** | **Diagnostic Criterion** | **Safety Implication** |
|---------------------------|----------------------|-------------------------|------------------------|
| **Permutation Importance Definition** | \( \text{PFI}_j = \mathbb{E}[\mathcal{L}(f, X^{(j)}, y)] - \mathcal{L}(f, X, y) \) where \( X^{(j)} \) has feature \( j \) permuted | Positive value indicates feature \( j \) contributes to predictive performance; near-zero suggests redundancy or irrelevance | Identifies which features the model depends on; negative values signal overfitting or feature interactions that stabilize predictions when disrupted |
| **Permutation vs. SHAP Trade-off** | PFI: \( O(n \cdot k \cdot r) \) for \( r \) repeats; SHAP: \( O(2^d) \) or approximations | PFI variance decreases as \( 1/\sqrt{r} \); SHAP provides additive feature attributions with theoretical guarantees | PFI is model-agnostic and scalable for auditing; SHAP provides local explanations but may be intractable for high-dimensional safety-critical systems |
| **Sobol First-Order Index** | \( S_i = \frac{\mathbb{V}_{x_i}[\mathbb{E}_{x_{\sim i}}[f(x) \mid x_i]]}{\mathbb{V}[f(x)]} \) | \( S_i \in [0,1] \); \( \sum_i S_i \leq 1 \) with equality only if no interactions exist | Quantifies fraction of output variance driven solely by feature \( i \); low \( S_i \) for safety-critical features indicates potential failure under adversarial perturbation |
| **Sobol Total-Order Index** | \( S_T^i = 1 - \frac{\mathbb{V}_{x_{\sim i}}[\mathbb{E}_{x_i}[f(x) \mid x_{\sim i}]]}{\mathbb{V}[f(x)]} \) | \( S_T^i \geq S_i \); gap \( S_T^i - S_i \) measures interaction strength | Captures all variance contributions including interactions; large \( S_T^i - S_i \) exposes hidden feature dependencies that could enable exploitation or emergent risk |
| **Variance Decomposition Completeness** | \( \sum_{i} S_i + \sum_{i<j} S_{ij} + \cdots = 1 \) (Sobol theorem) | Check via Monte Carlo estimation convergence; residual error should decrease as \( O(N^{-1/2}) \) | Verifies that all output uncertainty is accounted for; unexplained variance indicates model stochasticity or incomplete input space coverage |
| **Computational Complexity Constraint** | Sobol: \( N(d+2) \) model evaluations for first-order; quasi-Monte Carlo reduces constant | PFI completes in seconds; Sobol may require \( 10^4 \)–\( 10^6 \) evaluations for convergence | PFI enables rapid iteration during development; Sobol is reserved for final safety certification, regulatory submission, or formal robustness proofs in deployment-critical contexts |
