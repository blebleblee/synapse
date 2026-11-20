# Operational Verification Labs: Scikit Learn

## Objective & Environment Setup

Scikit-learn remains the cornerstone library for classical machine learning in production environments, offering a mature ecosystem of estimators, transformers, and pipeline abstractions that enforce reproducible model development. While deep learning frameworks dominate attention in contemporary discourse, the overwhelming majority of deployed ML systems in enterprise settings rely on gradient-boosted trees, regularized linear models, and ensemble methods—all domains where scikit-learn excels. This laboratory guide focuses on operational verification: the discipline of ensuring that your scikit-learn pipelines produce correct, robust, and performant predictions under real-world conditions. You will construct complete training harnesses, implement cross-validation strategies that prevent data leakage, benchmark hyperparameter search across multiple estimators, and stress-test models against adversarial inputs and distribution shift.

The verification methodology follows a three-phase protocol. First, you implement a complete end-to-end pipeline from raw data ingestion through feature engineering to model persistence, validating correctness at each stage. Second, you conduct rigorous hyperparameter optimization using grid search and randomized search, measuring not only accuracy metrics but also training time, memory consumption, and prediction latency. Third, you subject trained models to pathological inputs—missing values, outliers, categorical cardinality explosions, and covariate shift—documenting failure modes and implementing defensive mitigations. This approach mirrors production ML engineering practices where model correctness and operational resilience matter more than marginal accuracy gains on clean benchmark datasets.

Your working environment requires Python 3.11 or later with a curated dependency stack. Create an isolated virtual environment to prevent version conflicts and install the core scientific computing stack. Execute `python -m venv scikit_lab_env` followed by `source scikit_lab_env/bin/activate` on Unix systems or `scikit_lab_env\Scripts\activate` on Windows. Install dependencies with exact version pinning: `pip install scikit-learn==1.4.0 numpy==1.26.3 pandas==2.1.4 polars==0.20.3 matplotlib==3.8.2 seaborn==0.13.1 joblib==1.3.2`. Polars provides a faster alternative to pandas for data preprocessing, while joblib enables parallel hyperparameter search and model serialization. Verify your installation by importing scikit-learn and checking its version: `python -c "import sklearn; print(sklearn.__version__)"` should output `1.4.0`.

The laboratory dataset comes from the UCI Adult Income dataset, a classification task predicting whether individuals earn above fifty thousand dollars annually based on demographic and employment features. This dataset contains a realistic mixture of numerical and categorical features, missing values, class imbalance, and non-linear decision boundaries—ideal for verifying pipeline robustness. Download the raw data files: `wget https://archive.ics.uci.edu/ml/machine-learning-databases/adult/adult.data` and `wget https://archive.ics.uci.edu/ml/machine-learning-databases/adult/adult.test`. The training set contains 32,561 samples while the test set holds 16,281 samples. Each row encodes fifteen features including age, work class, education level, marital status, occupation, relationship, race, sex, capital gain, capital loss, hours per week, and native country, with the target variable indicating income bracket.

Create a project directory structure that separates data, source code, trained models, and evaluation artifacts. Execute `mkdir -p scikit_lab/{data,src,models,results}` and navigate to the root directory. Place the downloaded dataset files in `scikit_lab/data/`. Your source code will live in `scikit_lab/src/`, serialized models persist to `scikit_lab/models/`, and evaluation metrics save to `scikit_lab/results/`. This separation enforces reproducibility and simplifies version control integration. All subsequent code examples assume execution from the `scikit_lab/src/` directory with relative paths adjusted accordingly.

## Exercise 1: Hands-On Implementation & Pipeline Execution

Construct a complete data preprocessing and model training pipeline that transforms raw CSV data into a persisted classifier. Begin by implementing a robust data loading function that handles the Adult dataset's quirks: leading whitespace in categorical values, missing values encoded as question marks, and inconsistent column naming between train and test files. Create a new file `src/data_loader.py` and implement the following data ingestion logic. The loader must parse the CSV format without headers, assign canonical column names, strip whitespace from string values, replace missing value sentinels with NumPy NaN, and cast the binary target to integer labels.

```python
import polars as pl
import numpy as np
from pathlib import Path
from typing import Tuple

COLUMN_NAMES = [
    'age', 'workclass', 'fnlwgt', 'education', 'education_num',
    'marital_status', 'occupation', 'relationship', 'race', 'sex',
    'capital_gain', 'capital_loss', 'hours_per_week', 'native_country', 'income'
]

CATEGORICAL_FEATURES = [
    'workclass', 'education', 'marital_status', 'occupation',
    'relationship', 'race', 'sex', 'native_country'
]

NUMERICAL_FEATURES = [
    'age', 'fnlwgt', 'education_num', 'capital_gain',
    'capital_loss', 'hours_per_week'
]

def load_adult_data(filepath: Path, is_test: bool = False) -> pl.DataFrame:
    """Load and preprocess Adult Income dataset from raw CSV.
    
    Args:
        filepath: Path to the data file (adult.data or adult.test)
        is_test: Whether this is the test set (has extra period in target)
    
    Returns:
        Polars DataFrame with standardized columns and missing value handling
    """
    df = pl.read_csv(
        filepath,
        has_header=False,
        new_columns=COLUMN_NAMES,
        null_values=['?', ' ?'],
        truncate_ragged_lines=True
    )
    
    # Strip whitespace from all string columns
    for col in df.columns:
        if df[col].dtype == pl.Utf8:
            df = df.with_columns(pl.col(col).str.strip_chars().alias(col))
    
    # Test set has trailing period in income column
    if is_test:
        df = df.with_columns(
            pl.col('income').str.replace('.', '').alias('income')
        )
    
    # Encode binary target: '>50K' -> 1, '<=50K' -> 0
    df = df.with_columns(
        (pl.col('income') == '>50K').cast(pl.Int32).alias('income')
    )
    
    return df

def prepare_train_test_split() -> Tuple[pl.DataFrame, pl.DataFrame]:
    """Load both train and test sets with consistent preprocessing."""
    data_dir = Path('../data')
    
    train_df = load_adult_data(data_dir / 'adult.data', is_test=False)
    test_df = load_adult_data(data_dir / 'adult.test', is_test=True)
    
    print(f"Training samples: {len(train_df)}")
    print(f"Test samples: {len(test_df)}")
    print(f"Feature columns: {len(COLUMN_NAMES) - 1}")
    print(f"Numerical features: {len(NUMERICAL_FEATURES)}")
    print(f"Categorical features: {len(CATEGORICAL_FEATURES)}")
    
    return train_df, test_df
```

The data loader exploits Polars for efficient CSV parsing with explicit null value handling. The `null_values` parameter catches both the raw question mark sentinel and its whitespace-padded variant. Polars string methods provide vectorized whitespace stripping without explicit iteration. The binary target encoding uses boolean comparison followed by integer casting, avoiding fragile string matching logic. The loader prints diagnostic statistics to verify data dimensions before pipeline execution begins.

Now implement the feature engineering pipeline using scikit-learn's `ColumnTransformer` and `Pipeline` abstractions. These classes enforce correct train-test transformation sequences by fitting preprocessing steps only on training data while applying the learned transformations to test data. Missing values must be imputed before encoding, numerical features require scaling to prevent distance-based algorithms from being dominated by high-magnitude variables, and categorical features need encoding strategies that handle unseen categories in production. Create `src/feature_pipeline.py` with the complete preprocessing specification.

```python
import numpy as np
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from data_loader import NUMERICAL_FEATURES, CATEGORICAL_FEATURES

class DataFrameSelector(BaseEstimator, TransformerMixin):
    """Select specific columns from a Polars or Pandas DataFrame."""
    
    def __init__(self, column_names):
        self.column_names = column_names
    
    def fit(self, X, y=None):
        return self
    
    def transform(self, X):
        return X[self.column_names].to_numpy()

def build_preprocessing_pipeline() -> ColumnTransformer:
    """Construct complete feature engineering pipeline.
    
    Numerical features:
        1. Impute missing values with median (robust to outliers)
        2. Standardize to zero mean and unit variance
    
    Categorical features:
        1. Impute missing values with constant 'missing' marker
        2. One-hot encode with automatic unknown category handling
    
    Returns:
        Fitted ColumnTransformer ready for fit_transform on training data
    """
    
    # Numerical preprocessing: median imputation + standardization
    numerical_pipeline = Pipeline([
        ('selector', DataFrameSelector(NUMERICAL_FEATURES)),
        ('imputer', SimpleImputer(strategy='median', add_indicator=False)),
        ('scaler', StandardScaler())
    ])
    
    # Categorical preprocessing: constant imputation + one-hot encoding
    # handle_unknown='ignore' prevents errors on unseen categories
    # sparse_output=False for compatibility with downstream estimators
    categorical_pipeline = Pipeline([
        ('selector', DataFrameSelector(CATEGORICAL_FEATURES)),
        ('imputer', SimpleImputer(strategy='constant', fill_value='missing')),
        ('encoder', OneHotEncoder(
            handle_unknown='ignore',
            sparse_output=False,
            drop='first'  # Drop first category to avoid multicollinearity
        ))
    ])
    
    # Combine pipelines with ColumnTransformer
    preprocessor = ColumnTransformer(
        transformers=[
            ('num', numerical_pipeline, NUMERICAL_FEATURES),
            ('cat', categorical_pipeline, CATEGORICAL_FEATURES)
        ],
        remainder='drop',  # Drop columns not in either feature list
        n_jobs=-1  # Parallelize transformations across cores
    )
    
    return preprocessor

def create_full_pipeline(estimator):
    """Wrap estimator with preprocessing in a unified Pipeline.
    
    Args:
        estimator: Any scikit-learn compatible estimator
    
    Returns:
        Pipeline that handles raw DataFrames end-to-end
    """
    return Pipeline([
        ('preprocessor', build_preprocessing_pipeline()),
        ('classifier', estimator)
    ])
```

The `DataFrameSelector` transformer bridges the gap between Polars DataFrames and scikit-learn's NumPy expectations. By implementing the `BaseEstimator` and `TransformerMixin` interfaces, it becomes a first-class pipeline component that respects fit-transform semantics. The numerical preprocessing pipeline chains median imputation with z-score standardization. Median imputation resists outlier contamination better than mean imputation, crucial for features like capital gain where most values are zero but some are extremely large. Standardization centers each feature at zero mean with unit standard deviation, ensuring that gradient-based optimizers and distance metrics treat all numerical features equally.

The categorical preprocessing pipeline uses constant imputation to create an explicit 'missing' category rather than dropping rows with null values, preserving more training data. The `OneHotEncoder` with `handle_unknown='ignore'` gracefully handles production scenarios where new categorical values appear in inference data—unseen categories produce all-zero encodings rather than raising exceptions. Setting `drop='first'` removes one category per feature to avoid perfect multicollinearity in linear models, where including all indicator variables would make the design matrix rank-deficient. The `ColumnTransformer` executes numerical and categorical pipelines in parallel using all available CPU cores via `n_jobs=-1`, then concatenates results into a single feature matrix.

Now implement the complete training harness that loads data, fits the pipeline, evaluates performance metrics, and persists the trained model. Create `src/train_baseline.py` as your first complete operational verification script. This harness must compute classification metrics on both training and test sets to detect overfitting, generate a confusion matrix for error analysis, measure prediction latency for deployment sizing, and serialize the complete pipeline for production serving.

```python
import time
import joblib
import numpy as np
from pathlib import Path
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, confusion_matrix, classification_report
)
from data_loader import prepare_train_test_split
from feature_pipeline import create_full_pipeline

def evaluate_classifier(y_true, y_pred, y_pred_proba, dataset_name):
    """Compute comprehensive classification metrics.
    
    Args:
        y_true: Ground truth labels
        y_pred: Predicted class labels
        y_pred_proba: Predicted class probabilities for positive class
        dataset_name: 'Train' or 'Test' for logging
    """
    print(f"\n{'='*60}")
    print(f"{dataset_name} Set Evaluation")
    print(f"{'='*60}")
    
    # Basic classification metrics
    accuracy = accuracy_score(y_true, y_pred)
    precision = precision_score(y_true, y_pred, zero_division=0)
    recall = recall_score(y_true, y_pred, zero_division=0)
    f1 = f1_score(y_true, y_pred, zero_division=0)
    
    # ROC-AUC requires probability estimates
    try:
        roc_auc = roc_auc_score(y_true, y_pred_proba)
    except ValueError:
        roc_auc = np.nan
    
    print(f"Accuracy:  {accuracy:.4f}")
    print(f"Precision: {precision:.4f}")
    print(f"Recall:    {recall:.4f}")
    print(f"F1 Score:  {f1:.4f}")
    print(f"ROC-AUC:   {roc_auc:.4f}")
    
    # Confusion matrix for error analysis
    cm = confusion_matrix(y_true, y_pred)
    print(f"\nConfusion Matrix:")
    print(f"                 Predicted Negative  Predicted Positive")
    print(f"Actual Negative  {cm[0,0]:>18}  {cm[0,1]:>18}")
    print(f"Actual Positive  {cm[1,0]:>18}  {cm[1,1]:>18}")
    
    # False positive and false negative rates
    fpr = cm[0,1] / (cm[0,0] + cm[0,1]) if (cm[0,0] + cm[0,1]) > 0 else 0
    fnr = cm[1,0] / (cm[1,0] + cm[1,1]) if (cm[1,0] + cm[1,1]) > 0 else 0
    print(f"\nFalse Positive Rate: {fpr:.4f}")
    print(f"False Negative Rate: {fnr:.4f}")
    
    return {
        'accuracy': accuracy,
        'precision': precision,
        'recall': recall,
        'f1': f1,
        'roc_auc': roc_auc
    }

def train_baseline_model():
    """Train baseline Random Forest classifier with full pipeline."""
    
    # Load data
    print("Loading Adult Income dataset...")
    train_df, test_df = prepare_train_test_split()
    
    # Separate features and targets
    X_train = train_df.drop('income')
    y_train = train_df['income'].to_numpy()
    X_test = test_df.drop('income')
    y_test = test_df['income'].to_numpy()
    
    # Class distribution analysis
    train_positive_rate = np.mean(y_train)
    test_positive_rate = np.mean(y_test)
    print(f"\nClass balance:")
    print(f"Training set positive class: {train_positive_rate:.2%}")
    print(f"Test set positive class: {test_positive_rate:.2%}")
    
    # Initialize baseline classifier
    # Random Forest with 100 trees, balanced class weights, and fixed seed
    rf_classifier = RandomForestClassifier(
        n_estimators=100,
        max_depth=20,
        min_samples_split=10,
        min_samples_leaf=4,
        max_features='sqrt',
        class_weight='balanced',
        n_jobs=-1,
        random_state=42,
        verbose=1
    )
    
    # Create full pipeline with preprocessing
    pipeline = create_full_pipeline(rf_classifier)
    
    # Train model
    print("\nTraining Random Forest pipeline...")
    train_start = time.time()
    pipeline.fit(X_train, y_train)
    train_time = time.time() - train_start
    print(f"Training completed in {train_time:.2f} seconds")
    
    # Training set predictions
    print("\nGenerating training set predictions...")
    y_train_pred = pipeline.predict(X_train)
    y_train_proba = pipeline.predict_proba(X_train)[:, 1]
    train_metrics = evaluate_classifier(
        y_train, y_train_pred, y_train_proba, 'Train'
    )
    
    # Test set predictions with latency measurement
    print("\nGenerating test set predictions...")
    predict_start = time.time()
    y_test_pred = pipeline.predict(X_test)
    predict_time = time.time() - predict_start
    y_test_proba = pipeline.predict_proba(X_test)[:, 1]
    
    test_metrics = evaluate_classifier(
        y_test, y_test_pred, y_test_proba, 'Test'
    )
    
    # Prediction latency analysis
    avg_latency_ms = (predict_time / len(X_test)) * 1000
    print(f"\nPrediction latency: {predict_time:.3f}s total, "
          f"{avg_latency_ms:.3f}ms per sample")
    
    # Check for overfitting
    train_test_gap = train_metrics['accuracy'] - test_metrics['accuracy']
    print(f"\nTrain-Test Accuracy Gap: {train_test_gap:.4f}")
    if train_test_gap > 0.05:
        print("WARNING: Significant overfitting detected (>5% gap)")
    
    # Persist model
    model_dir = Path('../models')
    model_dir.mkdir(exist_ok=True)
    model_path = model_dir / 'baseline_rf_pipeline.joblib'
    
    print(f"\nSerializing model to {model_path}...")
    joblib.dump(pipeline, model_path, compress=3)
    
    # Verify serialization
    loaded_pipeline = joblib.load(model_path)
    verification_pred = loaded_pipeline.predict(X_test[:10])
    assert np.array_equal(verification_pred, y_test_pred[:10]), \
        "Model serialization verification failed!"
    
    print("\nBaseline training complete. Model persisted successfully.")
    
    return pipeline, train_metrics, test_metrics

if __name__ == '__main__':
    train_baseline_model()
```

Execute the training script from the source directory: `python train_baseline.py`. The harness first analyzes class balance, revealing that approximately twenty-four percent of samples belong to the positive class (income above fifty thousand). This imbalance motivates the `class_weight='balanced'` parameter in the Random Forest, which automatically adjusts sample weights to penalize misclassification of minority class examples more heavily. The balanced weighting prevents the model from achieving high accuracy by simply predicting the majority class for all samples.

The Random Forest hyperparameters represent a reasonable starting point for operational verification. Setting `n_estimators=100` builds an ensemble of one hundred decision trees, each trained on a bootstrap sample of the data. The `max_depth=20` constraint prevents individual trees from overfitting by memorizing training data, while `min_samples_split=10` and `min_samples_leaf=4` enforce that internal nodes and leaf nodes contain sufficient samples before splitting. The `max_features='sqrt'` parameter decorrelates trees by considering only the square root of total features at each split, trading individual tree accuracy for ensemble diversity. Setting `random_state=42` ensures reproducible results across runs, critical for debugging and version control.

Training completes in approximately thirty to forty seconds on modern hardware, producing a model with eighty-five to eighty-seven percent test accuracy. The confusion matrix reveals that the model predicts the negative class (income below fifty thousand) more reliably than the positive class, consistent with class imbalance. The false negative rate typically exceeds the false positive rate, meaning the model fails to identify high earners more often than it incorrectly flags low earners. This asymmetry has real-world implications: in credit lending applications, false negatives deny loans to qualified applicants, while false positives extend credit to risky borrowers.

Prediction latency averages around fifty microseconds per sample on a typical CPU, meeting real-time serving requirements for most applications. The serialized model consumes approximately fifty megabytes on disk due to the one hundred decision trees, each storing split conditions and leaf values. The `compress=3` parameter applies modest zlib compression to reduce storage footprint without significantly increasing deserialization time. The verification step confirms that loading the persisted model produces identical predictions, validating that the serialization captured all pipeline state including fitted preprocessing transformers.

## Exercise 2: Hyperparameter Tuning & Empirical Benchmarking

Systematic hyperparameter optimization separates production ML engineering from ad-hoc experimentation. While the baseline Random Forest achieved reasonable performance, you must empirically verify whether alternative algorithms or tuned hyperparameters improve accuracy, reduce latency, or better calibrate probability estimates. This exercise implements exhaustive grid search over multiple classifier architectures and conducts rigorous benchmarking that measures not only predictive performance but also computational cost and resource consumption.

Begin by implementing a comprehensive hyperparameter search harness that evaluates three distinct classifier families: Random Forests, Gradient Boosting Machines, and Logistic Regression with elastic net regularization. Each algorithm offers different tradeoffs between interpretability, training time, prediction latency, and accuracy. Random Forests parallelize trivially across cores and provide feature importances but lack probability calibration. Gradient boosting builds trees sequentially, achieving higher accuracy at the cost of longer training times and difficulty parallelizing. Logistic regression trains nearly instantaneously and produces well-calibrated probabilities but struggles with non-linear decision boundaries unless feature engineering creates interaction terms.

Create `src/hyperparameter_search.py` implementing stratified k-fold cross-validation with exhaustive grid search. Stratified splitting preserves class distribution across folds, ensuring each fold contains approximately the same proportion of positive and negative examples. This prevents some folds from containing disproportionately easy or hard examples, reducing variance in cross-validation estimates.

```python
import json
import time
import joblib
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GridSearchCV, StratifiedKFold
from sklearn.metrics import make_scorer, f1_score
from data_loader import prepare_train_test_split
from feature_pipeline import create_full_pipeline

def build_search_spaces():
    """Define hyperparameter search spaces for each classifier family.
    
    Returns:
        Dictionary mapping classifier names to (estimator, param_grid) tuples
    """
    
    # Random Forest search space
    rf_estimator = RandomForestClassifier(
        class_weight='balanced',
        n_jobs=4,  # Limit parallelism to leave cores for cross-validation
        random_state=42
    )
    rf_params = {
        'classifier__n_estimators': [50, 100, 200],
        'classifier__max_depth': [10, 20, 30, None],
        'classifier__min_samples_split': [5, 10, 20],
        'classifier__min_samples_leaf': [2, 4, 8],
        'classifier__max_features': ['sqrt', 'log2']
    }
    
    # Gradient Boosting search space
    gb_estimator = GradientBoostingClassifier(
        random_state=42,
        subsample=0.8,
        validation_fraction=0.1,
        n_iter_no_change=10,
        tol=1e-4
    )
    gb_params = {
        'classifier__n_estimators': [100, 200, 300],
        'classifier__learning_rate': [0.01, 0.05, 0.1],
        'classifier__max_depth': [3, 5, 7],
        'classifier__min_samples_split': [10, 20],
        'classifier__min_samples_leaf': [4, 8],
        'classifier__max_features': ['sqrt', 'log2']
    }
    
    # Logistic Regression with elastic net search space
    lr_estimator = LogisticRegression(
        penalty='elasticnet',
        solver='saga',
        max_iter=1000,
        class_weight='balanced',
        random_state=42,
        n_jobs=-1
    )
    lr_params = {
        'classifier__C': [0.001, 0.01, 0.1, 1.0, 10.0],
        'classifier__l1_ratio': [0.0, 0.25, 0.5, 0.75, 1.0]
    }
    
    return {
        'random_forest': (rf_estimator, rf_params),
        'gradient_boosting': (gb_estimator, gb_params),
        'logistic_regression': (lr_estimator, lr_params)
    }

def run_hyperparameter_search():
    """Execute exhaustive grid search with cross-validation for all classifiers."""
    
    print("Loading Adult Income dataset...")
    train_df, test_df = prepare_train_test_split()
    
    X_train = train_df.drop('income')
    y_train = train_df['income'].to_numpy()
    X_test = test_df.drop('income')
    y_test = test_df['income'].to_numpy()
    
    # Configure stratified k-fold cross-validation
    cv_splitter = StratifiedKFold(
        n_splits=5,
        shuffle=True,
        random_state=42
    )
    
    # Use F1 score as optimization metric (balances precision and recall)
    f1_scorer = make_scorer(f1_score)
    
    search_spaces = build_search_spaces()
    results_summary = []
    
    for classifier_name, (base_estimator, param_grid) in search_spaces.items():
        print(f"\n{'='*70}")
        print(f"Hyperparameter Search: {classifier_name.replace('_', ' ').title()}")
        print(f"{'='*70}")
        
        # Wrap estimator in preprocessing pipeline
        pipeline = create_full_pipeline(base_estimator)
        
        # Calculate total number of configurations
        param_counts = [len(values) for values in param_grid.values()]
        total_configs = np.prod(param_counts)
        total_fits = total_configs * cv_splitter.n_splits
        
        print(f"Parameter grid size: {total_configs} configurations")
        print(f"Cross-validation folds: {cv_splitter.n_splits}")
        print(f"Total model fits: {total_fits}")
        
        # Initialize grid search
        grid_search = GridSearchCV(
            estimator=pipeline,
            param_grid=param_grid,
            scoring=f1_scorer,
            cv=cv_splitter,
            n_jobs=-1,  # Parallelize across configurations
            verbose=2,
            return_train_score=True,
            error_score='raise'
        )
        
        # Execute search
        search_start = time.time()
        grid_search.fit(X_train, y_train)
        search_time = time.time() - search_start
        
        print(f"\nSearch completed in {search_time:.1f} seconds")
        print(f"Average time per configuration: {search_time/total_configs:.2f}s")
        
        # Extract best model and evaluate
        best_pipeline = grid_search.best_estimator_
        best_params = grid_search.best_params_
        best_cv_score = grid_search.best_score_
        
        print(f"\nBest cross-validation F1 score: {best_cv_score:.4f}")
        print(f"Best hyperparameters:")
        for param_name, param_value in best_params.items():
            clean_name = param_name.replace('classifier__', '')
            print(f"  {clean_name}: {param_value}")
        
        # Test set evaluation
        print(f"\nEvaluating on held-out test set...")
        predict_start = time.time()
        y_test_pred = best_pipeline.predict(X_test)
        predict_time = time.time() - predict_start
        
        from sklearn.metrics import accuracy_score, precision_score, recall_score
        
        test_accuracy = accuracy_score(y_test, y_test_pred)
        test_precision = precision_score(y_test, y_test_pred, zero_division=0)
        test_recall = recall_score(y_test, y_test_pred, zero_division=0)
        test_f1 = f1_score(y_test, y_test_pred, zero_division=0)
        
        avg_latency_ms = (predict_time / len(X_test)) * 1000
        
        print(f"Test Accuracy:  {test_accuracy:.4f}")
        print(f"Test Precision: {test_precision:.4f}")
        print(f"Test Recall:    {test_recall:.4f}")
        print(f"Test F1 Score:  {test_f1:.4f}")
        print(f"Prediction latency: {avg_latency_ms:.3f}ms per sample")
        
        # Record results
        results_summary.append({
            'classifier': classifier_name,
            'cv_f1_score': best_cv_score,
            'test_accuracy': test_accuracy,
            'test_precision': test_precision,
            'test_recall': test_recall,
            'test_f1_score': test_f1,
            'search_time_seconds': search_time,
            'prediction_latency_ms': avg_latency_ms,
            'best_params': best_params
        })
        
        # Persist best model
        model_dir = Path('../models')
        model_path = model_dir / f'tuned_{classifier_name}.joblib'
        joblib.dump(best_pipeline, model_path, compress=3)
        print(f"\nBest model saved to {model_path}")
    
    # Generate comparative summary
    print(f"\n{'='*70}")
    print("Hyperparameter Search Summary")
    print(f"{'='*70}\n")
    
    results_df = pd.DataFrame(results_summary)
    
    # Sort by test F1 score descending
    results_df = results_df.sort_values('test_f1_score', ascending=False)
    
    print(results_df[['classifier', 'test_accuracy', 'test_f1_score', 
                      'prediction_latency_ms', 'search_time_seconds']].to_string(index=False))
    
    # Save detailed results
    results_dir = Path('../results')
    results_dir.mkdir(exist_ok=True)
    results_path = results_dir / 'hyperparameter_search_results.json'
    
    with open(results_path, 'w') as f:
        json.dump(results_summary, f, indent=2, default=str)
    
    print(f"\nDetailed results saved to {results_path}")
    
    # Identify best model
    best_result = results_summary[0]
    print(f"\nBest performing model: {best_result['classifier']}")
    print(f"Test F1 Score: {best_result['test_f1_score']:.4f}")
    print(f"Test Accuracy: {best_result['test_accuracy']:.4f}")
    
    return results_df

if __name__ == '__main__':
    run_hyperparameter_search()
```

Execute the hyperparameter search: `python hyperparameter_search.py`. This process will consume thirty to sixty minutes depending on hardware, fitting hundreds of models across five cross-validation folds. The Random Forest search explores three hundred twenty-four configurations (3 × 4 × 3 × 3 × 2), requiring 1,620 total model fits. Gradient boosting examines two hundred sixteen configurations for 1,080 fits. Logistic regression sweeps twenty-five configurations for 125 fits, completing fastest due to the algorithm's computational efficiency.

The search harness parallelizes across configurations using `n_jobs=-1` in `GridSearchCV`, allowing scikit-learn to distribute work across all available CPU cores. However, Random Forest and Logistic Regression internally parallelize their training as well via their own `n_jobs` parameters. To prevent over-subscription—where more threads than physical cores compete for CPU resources—the Random Forest estimator limits internal parallelism to four cores with `n_jobs=4`. This nested parallelism strategy maximizes throughput: cross-validation distributes configurations across cores, while each configuration's training uses moderate internal parallelism.

The cross-validation strategy uses F1 score as the optimization metric rather than accuracy. F1 score, the harmonic mean of precision and recall, better captures model performance on imbalanced datasets because it requires both metrics to be high. A classifier that simply predicts the majority class achieves seventy-six percent accuracy but zero F1 score for the minority class. Optimizing F1 forces the search to find hyperparameters that balance true positive rate against false positive rate, appropriate for applications where both types of errors carry cost.

Gradient boosting typically achieves the highest F1 scores, often reaching 0.70 to 0.72 on the test set with optimal hyperparameters. The best configuration usually involves moderate tree depth (five to seven), low learning rate (0.05 to 0.1), and high tree count (two hundred to three hundred). The `subsample=0.8` parameter implements stochastic gradient boosting by training each tree on a random eighty percent subset of training data, reducing overfitting through bootstrap aggregation. The early stopping parameters (`validation_fraction=0.1`, `n_iter_no_change=10`, `tol=1e-4`) halt training when validation loss stops improving, preventing the model from overfitting to training data while reducing unnecessary computation.

Random Forest achieves competitive performance with slightly lower F1 scores around 0.68 to 0.70. The optimal configuration typically uses more trees (one hundred to two hundred), deeper depth (twenty to thirty layers or unlimited), and moderate node constraints. Random Forests benefit from deeper trees that capture complex interactions, whereas gradient boosting prefers shallow stumps that incrementally refine predictions. The prediction latency for Random Forest remains low, around fifty to one hundred microseconds per sample, because trees evaluate in parallel and each tree requires only logarithmic decision steps.

Logistic regression delivers the fastest training and prediction times but lower accuracy, typically achieving F1 scores around 0.62 to 0.65. The optimal regularization strength usually falls in the moderate range (C between 0.1 and 1.0), while the L1/L2 ratio explores the elastic net spectrum. Pure L1 regularization (l1_ratio=1.0) performs feature selection by shrinking coefficients to exactly zero, useful for interpretability but potentially discarding informative features. Pure L2 regularization (l1_ratio=0.0) shrinks all coefficients toward zero without eliminating any, maintaining all features while penalizing large weights. The elastic net (l1_ratio between 0.0 and 1.0) combines both behaviors, offering a middle ground that balances feature selection against coefficient shrinkage.

The prediction latency differences reveal algorithmic complexity tradeoffs. Logistic regression requires only a single matrix-vector multiplication, yielding prediction times under ten microseconds per sample. Random Forest evaluates one hundred independent trees in parallel, taking fifty to one hundred microseconds. Gradient boosting evaluates trees sequentially with early stopping, consuming one hundred fifty to three hundred microseconds per sample despite having similar tree counts to Random Forest. For latency-sensitive applications requiring sub-millisecond response times, these differences matter when serving thousands of concurrent requests.

Now implement a specialized benchmarking harness that measures training time, memory consumption, and prediction throughput under controlled conditions. Create `src/benchmark_estimators.py` to profile computational resource usage across classifier families. This script measures peak memory allocation during training, computes predictions per second for batch and single-sample inference, and characterizes how performance scales with training set size.

```python
import time
import psutil
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from data_loader import prepare_train_test_split
from feature_pipeline import create_full_pipeline

def measure_memory_usage(func):
    """Decorator to measure peak memory consumption during function execution."""
    def wrapper(*args, **kwargs):
        process = psutil.Process()
        mem_before = process.memory_info().rss / 1024 / 1024  # MB
        
        result = func(*args, **kwargs)
        
        mem_after = process.memory_info().rss / 1024 / 1024  # MB
        peak_mem = mem_after - mem_before
        
        return result, peak_mem
    
    return wrapper

def benchmark_classifier(classifier_name, estimator, X_train, y_train, X_test, y_test):
    """Comprehensive performance benchmarking for a single classifier.
    
    Measures:
        - Training time and memory consumption
        - Batch prediction throughput
        - Single-sample prediction latency
        - Model serialization size
    """
    print(f"\n{'='*70}")
    print(f"Benchmarking: {classifier_name}")
    print(f"{'='*70}")
    
    # Create pipeline
    pipeline = create_full_pipeline(estimator)
    
    # Training benchmark with memory profiling
    @measure_memory_usage
    def train_with_memory():
        return pipeline.fit(X_train, y_train)
    
    print("Training model...")
    train_start = time.time()
    trained_pipeline, train_memory_mb = train_with_memory()
    train_time = time.time() - train_start
    
    print(f"Training time: {train_time:.2f}s")
    print(f"Training memory delta: {train_memory_mb:.1f} MB")
    
    # Batch prediction throughput
    print("\nMeasuring batch prediction throughput...")
    batch_trials = 5
    batch_times = []
    
    for _ in range(batch_trials):
        start = time.time()
        _ = trained_pipeline.predict(X_test)
        batch_times.append(time.time() - start)
    
    avg_batch_time = np.mean(batch_times)
    std_batch_time = np.std(batch_times)
    samples_per_second = len(X_test) / avg_batch_time
    
    print(f"Batch prediction time: {avg_batch_time:.4f}s ± {std_batch_time:.4f}s")
    print(f"Throughput: {samples_per_second:.0f} samples/second")
    
    # Single-sample latency
    print("\nMeasuring single-sample latency...")
    single_trials = 1000
    single_times = []
    
    # Use first sample for repeated prediction
    single_sample = X_test[:1]
    
    for _ in range(single_trials):
        start = time.perf_counter()
        _ = trained_pipeline.predict(single_sample)
        single_times.append(time.perf_counter() - start)
    
    single_times = np.array(single_times) * 1000  # Convert to milliseconds
    p50_latency = np.percentile(single_times, 50)
    p95_latency = np.percentile(single_times, 95)
    p99_latency = np.percentile(single_times, 99)
    
    print(f"Single-sample latency (P50): {p50_latency:.3f}ms")
    print(f"Single-sample latency (P95): {p95_latency:.3f}ms")
    print(f"Single-sample latency (P99): {p99_latency:.3f}ms")
    
    # Model serialization size
    print("\nMeasuring serialization size...")
    import joblib
    import io
    
    buffer = io.BytesIO()
    joblib.dump(trained_pipeline, buffer, compress=3)
    model_size_mb = len(buffer.getvalue()) / 1024 / 1024
    
    print(f"Serialized model size: {model_size_mb:.2f} MB")
    
    # Test set accuracy
    y_test_pred = trained_pipeline.predict(X_test)
    from sklearn.metrics import accuracy_score, f1_score
    
    test_accuracy = accuracy_score(y_test, y_test_pred)
    test_f1 = f1_score(y_test, y_test_pred, zero_division=0)
    
    print(f"\nTest Accuracy: {test_accuracy:.4f}")
    print(f"Test F1 Score: {test_f1:.4f}")
    
    return {
        'classifier': classifier_name,
        'train_time_seconds': train_time,
        'train_memory_mb': train_memory_mb,
        'batch_predict_time_seconds': avg_batch_time,
        'throughput_samples_per_sec': samples_per_second,
        'p50_latency_ms': p50_latency,
        'p95_latency_ms': p95_latency,
        'p99_latency_ms': p99_latency,
        'model_size_mb': model_size_mb,
        'test_accuracy': test_accuracy,
        'test_f1_score': test_f1
    }

def run_benchmarks():
    """Execute comprehensive benchmarks across all classifier families."""
    
    print("Loading Adult Income dataset...")
    train_df, test_df = prepare_train_test_split()
    
    X_train = train_df.drop('income')
    y_train = train_df['income'].to_numpy()
    X_test = test_df.drop('income')
    y_test = test_df['income'].to_numpy()
    
    # Define benchmark estimators with reasonable hyperparameters
    estimators = {
        'Random Forest': RandomForestClassifier(
            n_estimators=100,
            max_depth=20,
            min_samples_split=10,
            min_samples_leaf=4,
            class_weight='balanced',
            n_jobs=-1,
            random_state=42
        ),
        'Gradient Boosting': GradientBoostingClassifier(
            n_estimators=200,
            learning_rate=0.1,
            max_depth=5,
            min_samples_split=10,
            min_samples_leaf=4,
            subsample=0.8,
            random_state=42
        ),
        'Logistic Regression': LogisticRegression(
            penalty='elasticnet',
            C=1.0,
            l1_ratio=0.5,
            solver='saga',
            max_iter=1000,
            class_weight='balanced',
            n_jobs=-1,
            random_state=42
        )
    }
    
    benchmark_results = []
    
    for classifier_name, estimator in estimators.items():
        result = benchmark_classifier(
            classifier_name, estimator,
            X_train, y_train, X_test, y_test
        )
        benchmark_results.append(result)
    
    # Generate comparative summary
    print(f"\n{'='*70}")
    print("Benchmark Summary")
    print(f"{'='*70}\n")
    
    results_df = pd.DataFrame(benchmark_results)
    
    # Display key metrics
    display_cols = [
        'classifier', 'train_time_seconds', 'model_size_mb',
        'p50_latency_ms', 'throughput_samples_per_sec',
        'test_f1_score'
    ]
    
    print(results_df[display_cols].to_string(index=False))
    
    # Save detailed results
    results_dir = Path('../results')
    results_dir.mkdir(exist_ok=True)
    results_path = results_dir / 'benchmark_results.csv'
    
    results_df.to_csv(results_path, index=False)
    print(f"\nDetailed results saved to {results_path}")
    
    # Performance-efficiency frontier analysis
    print("\nPerformance-Efficiency Analysis:")
    for _, row in results_df.iterrows():
        efficiency_score = (row['test_f1_score'] * row['throughput_samples_per_sec']) / row['model_size_mb']
        print(f"{row['classifier']}: Efficiency Score = {efficiency_score:.2f}")
    
    return results_df

if __name__ == '__main__':
    run_benchmarks()
```

Execute the benchmark suite: `python benchmark_estimators.py`. The memory profiling reveals that gradient boosting consumes the most training memory, often exceeding five hundred megabytes, because it maintains gradient and hessian matrices for the entire dataset during tree construction. Random Forest memory usage scales with the number of trees and maximum depth but remains more modest, typically under three hundred megabytes, because each tree trains independently on bootstrap samples. Logistic regression uses minimal memory, under one hundred megabytes, since it only maintains coefficient vectors and gradient accumulators.

The throughput measurements expose the prediction performance hierarchy. Logistic regression achieves tens of thousands of samples per second in batch mode because the entire model collapses to a single matrix multiply that BLAS libraries optimize aggressively. Random Forest delivers several thousand samples per second by evaluating all trees in parallel, with performance scaling roughly proportionally to available CPU cores. Gradient boosting lags behind at hundreds to low thousands of samples per second because trees execute sequentially and the implementation lacks the same level of vectorization.

Single-sample latency tells a different story relevant for real-time serving. The P50 latency (median) provides the typical-case performance, while P95 and P99 latencies capture tail behavior important for service-level objectives. Logistic regression maintains sub-millisecond latency at all percentiles, making it suitable for latency-critical applications. Random Forest latency increases at higher percentiles due to operating system scheduling jitter and cache effects when hundreds of tree evaluations execute. Gradient boosting shows the highest latency variability because early stopping means prediction time depends on how quickly the ensemble converges for each sample.

Model serialization size matters for deployment scenarios with memory constraints or cold-start latency requirements. Logistic regression models compress to under one megabyte, containing only coefficient vectors and feature preprocessing state. Random Forest models range from ten to one hundred megabytes depending on tree count and depth, storing full decision tree structures. Gradient boosting models occupy similar space to Random Forests but grow more slowly with tree count because individual trees are shallow.

The efficiency score computed at the end synthesizes multiple dimensions: predictive performance (F1), inference speed (throughput), and deployment cost (model size). This composite metric helps identify Pareto-optimal solutions on the performance-efficiency frontier. Logistic regression often achieves the highest efficiency score despite lower raw accuracy because its minimal resource consumption compensates for reduced predictive power. Gradient boosting maximizes raw performance at the cost of efficiency. Random Forest occupies a middle ground, offering strong accuracy with reasonable resource usage.

## Exercise 3: Stress Testing, Edge Cases & Failure Mitigation

Production ML systems encounter pathological inputs that never appear in clean benchmark datasets: missing values across all features, categorical cardinality explosions from adversarial input, extreme outliers that break scaling assumptions, and distributional shift where test data comes from a fundamentally different population than training data. This exercise systematically probes model failure modes and implements defensive mitigations that prevent silent prediction degradation.

Begin by constructing a suite of adversarial test cases that stress each component of the preprocessing and modeling pipeline. Create `src/adversarial_tests.py` implementing systematic edge case generation. These tests must verify correct handling of: all-missing samples that contain no informative features, unseen categorical values that never appeared in training data, extreme numerical outliers multiple standard deviations beyond training range, and class-imbalanced batches containing only majority or minority class examples.

```python
import numpy as np
import polars as pl
import joblib
from pathlib import Path
from data_loader import NUMERICAL_FEATURES, CATEGORICAL_FEATURES, COLUMN_NAMES

def generate_all_missing_sample():
    """Create sample with missing values in all features."""
    sample = {col: None for col in COLUMN_NAMES[:-1]}  # Exclude target
    return pl.DataFrame([sample])

def generate_unseen_categorical_sample(train_df):
    """Create sample with entirely new categorical values."""
    sample = train_df[0].to_dicts()[0]
    
    # Replace all categorical features with novel values
    for cat_feat in CATEGORICAL_FEATURES:
        sample[cat_feat] = f'UNSEEN_{cat_feat.upper()}_VALUE'
    
    # Remove target
    sample.pop('income', None)
    
    return pl.DataFrame([sample])

def generate_extreme_outlier_sample(train_df):
    """Create sample with extreme outliers in numerical features."""
    sample = train_df[0].to_dicts()[0]
    
    # Set numerical features to extreme values (10x max observed)
    for num_feat in NUMERICAL_FEATURES:
        max_val = train_df[num_feat].max()
        sample[num_feat] = float(max_val * 10)
    
    # Remove target
    sample.pop('income', None)
    
    return pl.DataFrame([sample])

def generate_zero_variance_batch(train_df, size=100):
    """Create batch where all samples are identical."""
    # Use the median sample as template
    medians = {}
    for num_feat in NUMERICAL_FEATURES:
        medians[num_feat] = float(train_df[num_feat].median())
    
    # Use most common category for categorical features
    modes = {}
    for cat_feat in CATEGORICAL_FEATURES:
        modes[cat_feat] = train_df[cat_feat].mode()[0]
    
    # Combine into single sample
    sample = {**medians, **modes}
    
    # Replicate to create batch
    batch = pl.DataFrame([sample] * size)
    
    return batch

def generate_mixed_quality_batch(train_df, size=100):
    """Create batch with mixture of normal and adversarial samples."""
    samples = []
    
    # 70% normal samples from training distribution
    normal_indices = np.random.choice(len(train_df), size=int(0.7 * size))
    normal_samples = train_df[normal_indices].drop('income').to_dicts()
    samples.extend(normal_samples)
    
    # 10% all-missing samples
    missing_samples = [
        {col: None for col in COLUMN_NAMES[:-1]}
        for _ in range(int(0.1 * size))
    ]
    samples.extend(missing_samples)
    
    # 10% extreme outliers
    outlier_base = train_df[0].to_dicts()[0]
    outlier_base.pop('income', None)
    outlier_samples = []
    for _ in range(int(0.1 * size)):
        outlier = outlier_base.copy()
        for num_feat in NUMERICAL_FEATURES:
            max_val = train_df[num_feat].max()
            outlier[num_feat] = float(max_val * np.random.uniform(5, 20))
        outlier_samples.append(outlier)
    samples.extend(outlier_samples)
    
    # 10% unseen categoricals
    unseen_base = train_df[0].to_dicts()[0]
    unseen_base.pop('income', None)
    unseen_samples = []
    for _ in range(int(0.1 * size)):
        unseen = unseen_base.copy()
        for cat_feat in CATEGORICAL_FEATURES:
            unseen[cat_feat] = f'ADVERSARIAL_{cat_feat}_{np.random.randint(1000)}'
        unseen_samples.append(unseen)
    samples.extend(unseen_samples)
    
    return pl.DataFrame(samples)

def test_model_robustness(model_path, train_df):
    """Execute comprehensive adversarial testing suite."""
    
    print(f"Loading model from {model_path}...")
    pipeline = joblib.load(model_path)
    
    print("\n" + "="*70)
    print("Adversarial Robustness Testing")
    print("="*70)
    
    # Test 1: All-missing sample
    print("\nTest 1: All-missing features")
    all_missing = generate_all_missing_sample()
    try:
        pred = pipeline.predict(all_missing)
        proba = pipeline.predict_proba(all_missing)
        print(f"  Prediction: {pred[0]}")
        print(f"  Confidence: {proba[0].max():.4f}")
        print("  ✓ Handled successfully")
    except Exception as e:
        print(f"  ✗ FAILED: {str(e)}")
    
    # Test 2: Unseen categorical values
    print("\nTest 2: Unseen categorical values")
    unseen_cat = generate_unseen_categorical_sample(train_df)
    try:
        pred = pipeline.predict(unseen_cat)
        proba = pipeline.predict_proba(unseen_cat)
        print(f"  Prediction: {pred[0]}")
        print(f"  Confidence: {proba[0].max():.4f}")
        print("  ✓ Handled successfully")
    except Exception as e:
        print(f"  ✗ FAILED: {str(e)}")
    
    # Test 3: Extreme numerical outliers
    print("\nTest 3: Extreme numerical outliers")
    outliers = generate_extreme_outlier_sample(train_df)
    try:
        pred = pipeline.predict(outliers)
        proba = pipeline.predict_proba(outliers)
        print(f"  Prediction: {pred[0]}")
        print(f"  Confidence: {proba[0].max():.4f}")
        print("  ✓ Handled successfully")
    except Exception as e:
        print(f"  ✗ FAILED: {str(e)}")
    
    # Test 4: Zero-variance batch
    print("\nTest 4: Zero-variance batch (all identical samples)")
    zero_var = generate_zero_variance_batch(train_df, size=100)
    try:
        preds = pipeline.predict(zero_var)
        probas = pipeline.predict_proba(zero_var)
        unique_preds = np.unique(preds)
        prob_std = probas.std(axis=0)
        print(f"  Unique predictions: {len(unique_preds)}")
        print(f"  Prediction variance: {preds.var():.6f}")
        print(f"  Probability std dev: {prob_std.mean():.6f}")
        print("  ✓ Handled successfully")
    except Exception as e:
        print(f"  ✗ FAILED: {str(e)}")
    
    # Test 5: Mixed quality batch
    print("\nTest 5: Mixed quality batch (70% normal, 30% adversarial)")
    mixed_batch = generate_mixed_quality_batch(train_df, size=200)
    try:
        preds = pipeline.predict(mixed_batch)
        probas = pipeline.predict_proba(mixed_batch)
        
        # Analyze prediction distribution
        pred_dist = np.bincount(preds)
        print(f"  Prediction distribution: {pred_dist}")
        
        # Check for NaN outputs
        if np.any(np.isnan(probas)):
            print(f"  ✗ WARNING: NaN values in probability outputs")
        else:
            print(f"  ✓ No NaN outputs")
        
        # Check probability calibration
        max_probas = probas.max(axis=1)
        print(f"  Mean confidence: {max_probas.mean():.4f}")
        print(f"  Min confidence: {max_probas.min():.4f}")
        print(f"  Max confidence: {max_probas.max():.4f}")
        
        print("  ✓ Batch processed successfully")
    except Exception as e:
        print(f"  ✗ FAILED: {str(e)}")
    
    # Test 6: Prediction consistency
    print("\nTest 6: Prediction consistency (same input, multiple calls)")
    test_sample = train_df[:1].drop('income')
    preds_multiple = []
    for _ in range(10):
        pred = pipeline.predict(test_sample)
        preds_multiple.append(pred[0])
    
    if len(set(preds_multiple)) == 1:
        print(f"  ✓ Consistent predictions: {preds_multiple[0]}")
    else:
        print(f"  ✗ WARNING: Inconsistent predictions: {set(preds_multiple)}")
    
    print("\n" + "="*70)
    print("Robustness Testing Complete")
    print("="*70)

if __name__ == '__main__':
    from data_loader import prepare_train_test_split
    
    train_df, _ = prepare_train_test_split()
    
    # Test the baseline model
    model_path = Path('../models/baseline_rf_pipeline.joblib')
    if model_path.exists():
        test_model_robustness(model_path, train_df)
    else:
        print(f"Model not found at {model_path}")
        print("Run train_baseline.py first to create the model")
```

Execute the adversarial test suite: `python adversarial_tests.py`. The well-constructed pipeline with proper imputation and `handle_unknown='ignore'` in the one-hot encoder should pass all tests without raising exceptions. The all-missing sample receives imputed values (medians for numerical features, constant 'missing' for categorical features) and produces a valid prediction, though with potentially high uncertainty. The unseen categorical sample maps novel category values to all-zero indicator vectors, effectively treating them as neutral evidence, and produces predictions based only on numerical features and seen categorical patterns.

Extreme outliers stress the numerical preprocessing pipeline. StandardScaler transforms outliers linearly, so a value ten times the maximum training value becomes approximately ten standard deviations above the mean after scaling. Tree-based models (Random Forest and Gradient Boosting) handle scaled outliers gracefully because decision trees only care about relative ordering, not absolute magnitude—an extreme outlier simply falls into the rightmost bin. Logistic regression applies the linear predictor to the scaled extreme value, potentially producing very large logit values that translate to probabilities near zero or one after the sigmoid transformation. If coefficients for outlier-prone features are large, predictions may become overconfident.

The zero-variance batch reveals prediction stability. All identical samples should produce identical predictions and probabilities, confirming determinism in the inference pipeline. Any variance in outputs indicates non-determinism from floating-point arithmetic instability, parallel processing race conditions, or stochastic components in the model. Random Forest with a fixed random seed is deterministic, but if you accidentally omitted `random_state=42`, different trees would break ties differently across runs, causing prediction instability.

The mixed quality batch simulates production traffic where normal requests are contaminated with malformed inputs from API misuse, data pipeline bugs, or adversarial manipulation. The pipeline should process the entire batch without failing, producing predictions for all samples even if confidence is low for adversarial examples. Analyzing the confidence distribution reveals whether the model appropriately expresses uncertainty: well-calibrated models should output lower confidence for out-of-distribution samples.

Now implement distributional shift analysis by training on a subset of the data defined by one feature value and testing on samples with a different value. This simulates common production scenarios where training data comes from one geographic region, time period, or demographic group while production traffic includes others. Create `src/distribution_shift.py` to quantify performance degradation under covariate shift.

```python
import numpy as np
import joblib
from pathlib import Path
from sklearn.metrics import accuracy_score, f1_score, classification_report
from data_loader import prepare_train_test_split
from feature_pipeline import create_full_pipeline
from sklearn.ensemble import RandomForestClassifier

def analyze_distribution_shift():
    """Quantify model performance under covariate shift."""
    
    print("Loading full dataset...")
    train_df, test_df = prepare_train_test_split()
    
    # Define shift scenario: train on young workers, test on older workers
    age_threshold = 40
    
    print(f"\nDistribution Shift Scenario:")
    print(f"Training: age <= {age_threshold}")
    print(f"Testing: age > {age_threshold}")
    
    # Split training data by age
    train_young = train_df.filter(train_df['age'] <= age_threshold)
    train_old = train_df.filter(train_df['age'] > age_threshold)
    
    # Split test data by age
    test_young = test_df.filter(test_df['age'] <= age_threshold)
    test_old = test_df.filter(test_df['age'] > age_threshold)
    
    print(f"\nData splits:")
    print(f"  Train young: {len(train_young)} samples")
    print(f"  Train old: {len(train_old)} samples")
    print(f"  Test young: {len(test_young)} samples")
    print(f"  Test old: {len(test_old)} samples")
    
    # Analyze class distribution shifts
    train_young_pos_rate = train_young['income'].mean()
    train_old_pos_rate = train_old['income'].mean()
    test_young_pos_rate = test_young['income'].mean()
    test_old_pos_rate = test_old['income'].mean()
    
    print(f"\nClass distribution (positive rate):")
    print(f"  Train young: {train_young_pos_rate:.2%}")
    print(f"  Train old: {train_old_pos_rate:.2%}")
    print(f"  Test young: {test_young_pos_rate:.2%}")
    print(f"  Test old: {test_old_pos_rate:.2%}")
    
    # Train model on young workers only
    print("\nTraining model on young workers only...")
    X_train_young = train_young.drop('income')
    y_train_young = train_young['income'].to_numpy()
    
    classifier = RandomForestClassifier(
        n_estimators=100,
        max_depth=20,
        min_samples_split=10,
        min_samples_leaf=4,
        class_weight='balanced',
        n_jobs=-1,
        random_state=42
    )
    
    pipeline = create_full_pipeline(classifier)
    pipeline.fit(X_train_young, y_train_young)
    
    # Evaluate on in-distribution test set (young workers)
    print("\n" + "="*70)
    print("In-Distribution Performance (age <= 40)")
    print("="*70)
    
    X_test_young = test_young.drop('income')
    y_test_young = test_young['income'].to_numpy()
    
    y_pred_young = pipeline.predict(X_test_young)
    
    accuracy_young = accuracy_score(y_test_young, y_pred_young)
    f1_young = f1_score(y_test_young, y_pred_young, zero_division=0)
    
    print(f"\nAccuracy: {accuracy_young:.4f}")
    print(f"F1 Score: {f1_young:.4f}")
    print("\nClassification Report:")
    print(classification_report(y_test_young, y_pred_young, zero_division=0))
    
    # Evaluate on out-of-distribution test set (old workers)
    print("\n" + "="*70)
    print("Out-of-Distribution Performance (age > 40)")
    print("="*70)
    
    X_test_old = test_old.drop('income')
    y_test_old = test_old['income'].to_numpy()
    
    y_pred_old = pipeline.predict(X_test_old)
    
    accuracy_old = accuracy_score(y_test_old, y_pred_old)
    f1_old = f1_score(y_test_old, y_pred_old, zero_division=0)
    
    print(f"\nAccuracy: {accuracy_old:.4f}")
    print(f"F1 Score: {f1_old:.4f}")
    print("\nClassification Report:")
    print(classification_report(y_test_old, y_pred_old, zero_division=0))
    
    # Quantify performance degradation
    print("\n" + "="*70)
    print("Distribution Shift Impact")
    print("="*70)
    
    accuracy_drop = accuracy_young - accuracy_old
    f1_drop = f1_young - f1_old
    
    print(f"\nAccuracy degradation: {accuracy_drop:.4f} ({accuracy_drop/accuracy_young:.1%})")
    print(f"F1 score degradation: {f1_drop:.4f} ({f1_drop/f1_young:.1%})")
    
    if accuracy_drop > 0.05:
        print("\n⚠ WARNING: Significant performance degradation under distribution shift")
        print("  Consider training on more diverse data or implementing domain adaptation")
    else:
        print("\n✓ Model shows reasonable robustness to age-based distribution shift")
    
    # Train on combined data for comparison
    print("\n" + "="*70)
    print("Training on Combined Data (all ages)")
    print("="*70)
    
    X_train_full = train_df.drop('income')
    y_train_full = train_df['income'].to_numpy()
    
    pipeline_full = create_full_pipeline(classifier)
    pipeline_full.fit(X_train_full, y_train_full)
    
    # Evaluate combined model on old workers
    y_pred_old_full = pipeline_full.predict(X_test_old)
    accuracy_old_full = accuracy_score(y_test_old, y_pred_old_full)
    f1_old_full = f1_score(y_test_old, y_pred_old_full, zero_division=0)
    
    print(f"\nPerformance on old workers (age > 40):")
    print(f"  Trained on young only: Accuracy={accuracy_old:.4f}, F1={f1_old:.4f}")
    print(f"  Trained on all ages:   Accuracy={accuracy_old_full:.4f}, F1={f1_old_full:.4f}")
    
    improvement = accuracy_old_full - accuracy_old
    print(f"\nImprovement from diverse training: {improvement:.4f} ({improvement/accuracy_old:.1%})")

if __name__ == '__main__':
    analyze_distribution_shift()
```

Execute the distribution shift analysis: `python distribution_shift.py`. Training exclusively on workers aged forty or younger produces a model that underperforms on older workers by five to fifteen percentage points in accuracy. The degradation occurs because age correlates with other income predictors: older workers have more education, longer work history, and different occupational distributions. A model trained only on young workers learns spurious correlations that fail to generalize.

The class distribution analysis reveals part of the problem. Older workers have higher positive class rates (above fifty thousand income) than younger workers, approximately thirty-five percent versus fifteen percent. Training on young workers biases the model toward predicting the negative class more frequently because that is the overwhelming majority in the training set. When applied to older workers where the positive class is more common, the model's decision threshold is miscalibrated, producing excessive false negatives.

Training on the full age range improves performance on older workers by five to ten percentage points, demonstrating that diverse training data improves robustness to distribution shift. The model trained on all ages learns that age itself is predictive and adjusts decision boundaries accordingly. However, even the full-data model may degrade on entirely new age ranges (very young workers under twenty-five or elderly workers over sixty-five) if those groups were underrepresented in training data.

Implement calibration analysis to assess whether predicted probabilities accurately reflect true positive rates. Well-calibrated models output probabilities that match empirical frequencies: samples with predicted probability 0.7 should be positive seventy percent of the time. Create `src/calibration_analysis.py` implementing reliability diagrams and calibration metrics.

```python
import numpy as np
import matplotlib.pyplot as plt
import joblib
from pathlib import Path
from sklearn.calibration import calibration_curve
from sklearn.metrics import brier_score_loss, log_loss
from data_loader import prepare_train_test_split

def analyze_calibration(model_path, output_dir):
    """Comprehensive probability calibration analysis."""
    
    print(f"Loading model from {model_path}...")
    pipeline = joblib.load(model_path)
    
    print("Loading test data...")
    _, test_df = prepare_train_test_split()
    
    X_test = test_df.drop('income')
    y_test = test_df['income'].to_numpy()
    
    # Generate probability predictions
    print("Computing probability predictions...")
    y_pred_proba = pipeline.predict_proba(X_test)[:, 1]
    
    # Calibration metrics
    print("\n" + "="*70)
    print("Calibration Metrics")
    print("="*70)
    
    # Brier score (mean squared error of probabilities)
    brier = brier_score_loss(y_test, y_pred_proba)
    print(f"\nBrier Score: {brier:.4f} (lower is better)")
    
    # Log loss (cross-entropy)
    logloss = log_loss(y_test, y_pred_proba)
    print(f"Log Loss: {logloss:.4f} (lower is better)")
    
    # Expected Calibration Error (ECE)
    n_bins = 10
    prob_true, prob_pred = calibration_curve(
        y_test, y_pred_proba, n_bins=n_bins, strategy='uniform'
    )
    
    ece = np.mean(np.abs(prob_true - prob_pred))
    print(f"Expected Calibration Error (ECE): {ece:.4f} (lower is better)")
    
    # Reliability diagram
    print("\nGenerating reliability diagram...")
    
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    
    # Subplot 1: Calibration curve
    ax1 = axes[0]
    ax1.plot([0, 1], [0, 1], 'k--', label='Perfect calibration')
    ax1.plot(prob_pred, prob_true, 's-', label='Model calibration')
    ax1.set_xlabel('Predicted Probability', fontsize=12)
    ax1.set_ylabel('Empirical Frequency', fontsize=12)
    ax1.set_title('Reliability Diagram', fontsize=14)
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Subplot 2: Probability distribution
    ax2 = axes[1]
    ax2.hist(y_pred_proba[y_test == 0], bins=30, alpha=0.6, 
             label='Negative class', color='blue', density=True)
    ax2.hist(y_pred_proba[y_test == 1], bins=30, alpha=0.6, 
             label='Positive class', color='red', density=True)
    ax2.set_xlabel('Predicted Probability', fontsize=12)
    ax2.set_ylabel('Density', fontsize=12)
    ax2.set_title('Probability Distribution by True Class', fontsize=14)
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    output_path = output_dir / 'calibration_analysis.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"Reliability diagram saved to {output_path}")
    
    # Confidence distribution analysis
    print("\n" + "="*70)
    print("Confidence Distribution")
    print("="*70)
    
    # Analyze prediction confidence
    confidence = np.maximum(y_pred_proba, 1 - y_pred_proba)
    
    print(f"\nMean confidence: {confidence.mean():.4f}")
    print(f"Median confidence: {np.median(confidence):.4f}")
    print(f"Std dev confidence: {confidence.std():.4f}")
    
    # Low confidence samples (ambiguous predictions)
    low_conf_threshold = 0.6
    low_conf_mask = confidence < low_conf_threshold
    n_low_conf = low_conf_mask.sum()
    
    print(f"\nSamples with confidence < {low_conf_threshold}: "
          f"{n_low_conf} ({n_low_conf/len(y_test):.1%})")
    
    # High confidence errors (overconfident mistakes)
    high_conf_threshold = 0.9
    y_pred = (y_pred_proba > 0.5).astype(int)
    errors = (y_pred != y_test)
    high_conf_errors = errors & (confidence > high_conf_threshold)
    
    print(f"High-confidence errors (confidence > {high_conf_threshold}): "
          f"{high_conf_errors.sum()} ({high_conf_errors.sum()/errors.sum():.1%} of errors)")
    
    if high_conf_errors.sum() > 0.1 * errors.sum():
        print("\n⚠ WARNING: Model is overconfident on many errors")
        print("  Consider applying probability calibration (Platt scaling or isotonic regression)")
    
    plt.close()
    
    return {
        'brier_score': brier,
        'log_loss': logloss,
        'ece': ece,
        'mean_confidence': confidence.mean(),
        'low_confidence_rate': n_low_conf / len(y_test),
        'high_confidence_error_rate': high_conf_errors.sum() / errors.sum()
    }

if __name__ == '__main__':
    model_path = Path('../models/baseline_rf_pipeline.joblib')
    output_dir = Path('../results')
    output_dir.mkdir(exist_ok=True)
    
    if model_path.exists():
        analyze_calibration(model_path, output_dir)
    else:
        print(f"Model not found at {model_path}")
        print("Run train_baseline.py first")
```

Execute calibration analysis: `python calibration_analysis.py`. Random Forest classifiers typically exhibit poor calibration out of the box because the ensemble averaging pushes probabilities toward zero and one. The reliability diagram shows the calibration curve deviating from the diagonal, often underestimating probabilities in the middle range (predicting 0.4 when true frequency is 0.6) and overestimating at extremes (predicting 0.9 when true frequency is 0.7).

The Expected Calibration Error (ECE) quantifies miscalibration by computing the mean absolute difference between predicted probabilities and empirical frequencies across bins. ECE above 0.1 indicates substantial miscalibration requiring correction. Brier score combines calibration and discrimination: it decreases when predictions are both accurate and well-calibrated. Log loss penalizes overconfident incorrect predictions more heavily than Brier score, making it sensitive to extreme probability estimates.

The probability distribution histogram reveals separation between classes. Well-discriminating models show minimal overlap: negative class predictions cluster near zero while positive class predictions cluster near one. Poorly discriminating models show substantial overlap with both classes spread across the full probability range. The overlap region contains ambiguous samples where the model lacks confidence and may benefit from human review in production systems.

High-confidence errors represent the most dangerous failure mode. These are samples where the model predicts incorrectly with high probability, providing no signal to downstream systems that the prediction may be wrong. If more than ten percent of errors occur with high confidence, consider applying calibration methods. Platt scaling fits a logistic regression on top of model outputs to recalibrate probabilities. Isotonic regression fits a non-parametric monotonic function, more flexible but requiring more calibration data.

## ML Diagnostic Cheat Sheet & Verification Checklist

This section consolidates diagnostic commands, debugging procedures, and operational checklists for maintaining scikit-learn pipelines in production. Use these references when investigating model degradation, validating new training runs, or troubleshooting prediction anomalies.

**Data Quality Verification Commands:**

Verify dataset loading and preprocessing correctness before training. These commands catch data parsing errors, missing value handling bugs, and feature engineering mistakes that silently degrade model performance.

```python
# Inspect raw data structure and identify missing values
import polars as pl
df = pl.read_csv('data/adult.data')
print(df.describe())  # Summary statistics reveal outliers and null counts
print(df.null_count())  # Explicit null count per column

# Verify categorical cardinality (detect cardinality explosion)
for col in df.columns:
    if df[col].dtype == pl.Utf8:
        unique_count = df[col].n_unique()
        print(f"{col}: {unique_count} unique values")
        if unique_count > 100:
            print(f"  WARNING: High cardinality in {col}")

# Check feature correlation (detect multicollinearity)
import numpy as np
numerical_cols = ['age', 'education_num', 'hours_per_week', 'capital_gain']
corr_matrix = df[numerical_cols].to_pandas().corr()
high_corr = np.where(np.abs(corr_matrix) > 0.9)
for i, j in zip(*high_corr):
    if i < j:
        print(f"High correlation: {numerical_cols[i]} <-> {numerical_cols[j]}: {corr_matrix.iloc[i,j]:.3f}")
```

**Pipeline Debugging Workflow:**

Isolate pipeline failures by testing each transformer independently. This bisection approach identifies which component introduced NaN values, raised exceptions, or produced incorrect output shapes.

```python
# Manually step through pipeline components
from sklearn.pipeline import Pipeline

# Load pipeline
import joblib
pipeline = joblib.load('models/baseline_rf_pipeline.joblib')

# Extract individual transformers
preprocessor = pipeline.named_steps['preprocessor']
classifier = pipeline.named_steps['classifier']

# Test preprocessing in isolation
X_test = test_df.drop('income')
X_transformed = preprocessor.transform(X_test)

# Verify output shape and check for NaNs
print(f"Transformed shape: {X_transformed.shape}")
print(f"Contains NaN: {np.any(np.isnan(X_transformed))}")
print(f"Contains Inf: {np.any(np.isinf(X_transformed))}")

# If NaNs present, identify source transformer
if np.any(np.isnan(X_transformed)):
    # Get feature names from transformers
    num_features = preprocessor.transformers_[0][2]
    cat_features = preprocessor.transformers_[1][2]
    
    # Test numerical pipeline separately
    num_transformer = preprocessor.transformers_[0][1]
    X_num = X_test[num_features]
    X_num_transformed = num_transformer.transform(X_num)
    print(f"Numerical NaNs: {np.any(np.isnan(X_num_transformed))}")
    
    # Test categorical pipeline separately
    cat_transformer = preprocessor.transformers_[1][1]
    X_cat = X_test[cat_features]
    X_cat_transformed = cat_transformer.transform(X_cat)
    print(f"Categorical NaNs: {np.any(np.isnan(X_cat_transformed))}")
```

**Model Performance Monitoring:**

Track prediction distributions and performance metrics over time to detect model drift. Save these statistics for each batch of predictions in production and compare against training set distributions.

```python
# Compute prediction distribution statistics
y_pred_proba = pipeline.predict_proba(X_test)[:, 1]

stats = {
    'mean_probability': float(np.mean(y_pred_proba)),
    'std_probability': float(np.std(y_pred_proba)),
    'median_probability': float(np.median(y_pred_proba)),
    'min_probability': float(np.min(y_pred_proba)),
    'max_probability': float(np.max(y_pred_proba)),
    'positive_rate': float(np.mean(y_pred_proba > 0.5))
}

# Compare against training baseline
import json
baseline_path = 'results/training_baseline_stats.json'
if Path(baseline_path).exists():
    with open(baseline_path, 'r') as f:
        baseline = json.load(f)
    
    # Detect distribution shifts
    mean_shift = abs(stats['mean_probability'] - baseline['mean_probability'])
    pos_rate_shift = abs(stats['positive_rate'] - baseline['positive_rate'])
    
    if mean_shift > 0.1:
        print(f"WARNING: Mean probability shifted by {mean_shift:.3f}")
    if pos_rate_shift > 0.05:
        print(f"WARNING: Positive rate shifted by {pos_rate_shift:.1%}")
```

**Feature Importance Analysis:**

Extract feature importances from tree-based models to understand which variables drive predictions. Unexpected importance patterns may indicate data leakage or spurious correlations.

```python
# Extract feature importances from Random Forest
classifier = pipeline.named_steps['classifier']

# Get feature names from preprocessor
preprocessor = pipeline.named_steps['preprocessor']

# Numerical features (standardized)
num_feature_names = preprocessor.transformers_[0][2]

# Categorical features (one-hot encoded)
cat_encoder = preprocessor.transformers_[1][1].named_steps['encoder']
cat_feature_names_in = preprocessor.transformers_[1][2]
cat_feature_names_out = cat_encoder.get_feature_names_out(cat_feature_names_in)

# Combine all feature names
all_feature_names = list(num_feature_names) + list(cat_feature_names_out)

# Get importances
importances = classifier.feature_importances_

# Sort by importance
importance_df = pd.DataFrame({
    'feature': all_feature_names,
    'importance': importances
}).sort_values('importance', ascending=False)

print("\nTop 20 Most Important Features:")
print(importance_df.head(20).to_string(index=False))

# Visualize top features
import matplotlib.pyplot as plt
top_n = 15
top_features = importance_df.head(top_n)

plt.figure(figsize=(10, 6))
plt.barh(range(top_n), top_features['importance'])
plt.yticks(range(top_n), top_features['feature'])
plt.xlabel('Feature Importance')
plt.title('Top 15 Most Important Features')
plt.gca().invert_yaxis()
plt.tight_layout()
plt.savefig('results/feature_importance.png', dpi=300)
print("\nFeature importance plot saved to results/feature_importance.png")
```

**Hyperparameter Sensitivity Analysis:**

Quantify how sensitive model performance is to each hyperparameter. This identifies which parameters require careful tuning versus which can use default values.

```python
# Test sensitivity to n_estimators
from sklearn.model_selection import cross_val_score

n_estimators_values = [10, 50, 100, 200, 500]
scores = []

for n_est in n_estimators_values:
    clf = RandomForestClassifier(
        n_estimators=n_est,
        max_depth=20,
        class_weight='balanced',
        random_state=42,
        n_jobs=-1
    )
    pipeline_temp = create_full_pipeline(clf)
    cv_scores = cross_val_score(
        pipeline_temp, X_train, y_train,
        cv=3, scoring='f1', n_jobs=-1
    )
    mean_score = cv_scores.mean()
    scores.append(mean_score)
    print(f"n_estimators={n_est:3d}: F1={mean_score:.4f} ± {cv_scores.std():.4f}")

# Compute sensitivity (score change per parameter change)
sensitivity = np.diff(scores) / np.diff(n_estimators_values)
print(f"\nMean sensitivity: {np.mean(np.abs(sensitivity)):.6f} F1 per tree")
```

**Operational Verification Checklist:**

Use this checklist before deploying a new model version to production. Each item prevents a common category of production failure.

```text
□ Data Loading
  □ CSV files parse without errors
  □ Column names match expected schema
  □ Missing value sentinels are correctly identified
  □ Data types are appropriate (numerical vs categorical)

□ Preprocessing Pipeline
  □ Numerical features are imputed before scaling
  □ Categorical features handle unseen values gracefully
  □ Feature counts match expected dimensions after encoding
  □ Transformed data contains no NaN or Inf values

□ Model Training
  □ Cross-validation scores are stable across folds (std < 0.05)
  □ Training set performance is not perfect (check for data leakage)
  □ Test set performance is within 5% of cross-validation performance
  □ Class balance is accounted for (balanced weights or stratified sampling)

□ Prediction Quality
  □ Predictions are deterministic (same input → same output)
  □ Probability estimates sum to 1.0 for each sample
  □ No predictions yield NaN or Inf
  □ Prediction latency meets SLA requirements (<100ms typical)

□ Robustness
  □ Model handles all-missing-value samples without crashing
  □ Unseen categorical values do not raise exceptions
  □ Extreme numerical outliers produce valid predictions
  □ Batch predictions match individual predictions (no batching artifacts)

□ Calibration
  □ Expected Calibration Error (ECE) < 0.1
  □ Reliability diagram shows reasonable alignment with diagonal
  □ High-confidence errors are less than 10% of total errors

□ Serialization
  □ Model serializes and deserializes without errors
  □ Loaded model produces identical predictions to original
  □ Serialized file size is reasonable for deployment (<100MB typical)
  □ Model version and metadata are tracked

□ Monitoring
  □ Feature distributions are logged for drift detection
  □ Prediction distributions are tracked over time
  □ Performance metrics are computed on recent batches
  □ Alerting is configured for anomalies
```

**Common Failure Modes and Resolutions:**

This troubleshooting guide maps symptoms to root causes and remediation steps. Use it when production predictions behave unexpectedly.

**Symptom:** Predictions return all zeros or all ones.
**Diagnosis:** Class imbalance overwhelmed the model, or decision threshold is miscalibrated.
**Resolution:** Enable `class_weight='balanced'` in the classifier. If using custom thresholds, recalibrate using validation set to balance precision and recall.

**Symptom:** `ValueError: Input contains NaN, infinity or a value too large for dtype('float64')`.
**Diagnosis:** Preprocessing pipeline failed to impute missing values, or scaling produced numerical overflow.
**Resolution:** Verify imputer is placed before scaler in pipeline. Check for extreme outliers (>1e10) that cause overflow; consider clipping or log transformation.

**Symptom:** `KeyError` or `ValueError` about unseen categorical values.
**Diagnosis:** OneHotEncoder not configured to handle unknown categories.
**Resolution:** Set `handle_unknown='ignore'` in OneHotEncoder. Verify this parameter persists after serialization.

**Symptom:** Predictions are non-deterministic across runs.
**Diagnosis:** Missing `random_state` parameter in classifier or stochastic preprocessing step.
**Resolution:** Set `random_state=42` in all estimators. For Random Forest, also ensure `n_jobs` is consistent or set to 1 for maximum reproducibility.

**Symptom:** Training succeeds but test predictions are significantly worse.
**Diagnosis:** Data leakage during preprocessing, or fitting imputer/scaler on test data.
**Resolution:** Ensure preprocessing is wrapped in Pipeline and only `fit` is called on training data. Never call `fit_transform` on test data—use `transform` only.

**Symptom:** Memory consumption exceeds available RAM during training.
**Diagnosis:** Dataset too large for in-memory processing, or model creates excessive copies.
**Resolution:** Use `n_jobs=1` to reduce parallel memory overhead. Consider partial fitting with `warm_start=True` or switch to online learning algorithms (SGDClassifier).

**Symptom:** Prediction latency exceeds service-level objectives.
**Diagnosis:** Model complexity too high for real-time requirements, or inefficient serialization format.
**Resolution:** Reduce tree count in Random Forest, decrease max depth, or switch to faster algorithm (Logistic Regression). Use `compress=0` in joblib.dump for faster deserialization at cost of larger files.

This laboratory guide has taken you through the complete operational verification workflow for scikit-learn classifiers: building robust preprocessing pipelines, conducting rigorous hyperparameter searches, benchmarking computational performance, and stress-testing against adversarial inputs and distribution shift. The verification discipline separates production ML engineering from academic experimentation. Models that pass these tests will serve reliably in real-world systems, handling edge cases gracefully and maintaining performance as data distributions evolve. The diagnostic cheat sheet and verification checklist provide operational references for maintaining model health over time. Return to these materials when investigating production incidents or validating new model versions before deployment.
