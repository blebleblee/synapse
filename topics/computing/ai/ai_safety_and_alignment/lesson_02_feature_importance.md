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

```
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

Sobol indices are the gold standard for **global** sensitivity analysis. They answer the question: across the full input distribution, how much of the output variance is attributable to each input or interaction?

**First-order index:**

$$
S_i = \frac{V_i}{\mathrm{Var}(Y)} = \frac{\mathrm{Var}\bigl(\mathbb{E}[Y \mid X_i]\bigr)}{\mathrm{Var}(Y)}
$$

$S_i$ captures the main effect of $X_i$ alone—the variance reduction achievable by learning $X_i$ perfectly
