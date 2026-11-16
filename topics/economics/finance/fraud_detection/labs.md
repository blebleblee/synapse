# Operational Verification Labs: Fraud Detection

## Objective & Operational Lab Setup

Fraud detection constitutes one of the most critical operational risk management functions within modern financial institutions, credit card networks, insurance underwriters, and digital payment platforms. The economic cost of fraud extends beyond direct monetary losses to encompass reputational damage, regulatory penalties, increased compliance overhead, and the erosion of consumer trust that fundamentally undermines market efficiency. This laboratory guide equips the practitioner with the statistical, econometric, and machine learning techniques required to design, calibrate, and operationally validate fraud detection systems that balance Type I errors (false positives that inconvenience legitimate customers) against Type II errors (false negatives that allow fraudulent transactions to succeed).

The operational environment for fraud detection analytics combines retrospective data analysis with real-time scoring systems. Practitioners must master the tension between model accuracy and computational latency, between explainability for regulatory compliance and predictive power, and between static rule-based systems and adaptive learning architectures. The economic framework underpinning fraud detection draws from information asymmetry theory, where fraudsters possess private information about their intentions that must be inferred from observable transaction patterns, and from optimal stopping problems, where the institution must decide in milliseconds whether to authorize, decline, or flag a transaction for manual review.

The laboratory setup requires a computational environment capable of handling large transaction datasets, performing logistic regression and ensemble learning methods, and simulating the operational dynamics of a fraud detection pipeline. We employ Python with the scientific computing stack (NumPy, Pandas, Scikit-learn, Matplotlib) as the primary analytical platform, complemented by Excel for exploratory data analysis and financial metric calculation. The practitioner will work with synthetic transaction data that mimics real-world patterns including temporal dynamics, geographic clustering, merchant category distributions, and the highly imbalanced class distribution characteristic of fraud (typically 0.1% to 2% of transactions).

Begin by establishing the Python environment. Install the required packages using pip in a virtual environment to maintain reproducibility. Execute the following commands in your terminal to create an isolated workspace and install dependencies:

```bash
python3 -m venv fraud_detection_lab
source fraud_detection_lab/bin/activate
pip install numpy pandas scikit-learn matplotlib seaborn imbalanced-learn xgboost openpyxl jupyter
```

The imbalanced-learn library provides resampling techniques critical for handling the severe class imbalance inherent in fraud detection, where legitimate transactions outnumber fraudulent ones by ratios of 100:1 or greater. The xgboost package implements gradient boosting decision trees, which have proven highly effective in capturing the non-linear interaction effects between transaction features that signal fraudulent behavior.

Create a project directory structure that separates raw data, processed features, trained models, and evaluation outputs. This organizational discipline ensures reproducibility and facilitates the transition from laboratory experimentation to production deployment:

```bash
mkdir -p fraud_labs/{data,models,outputs,notebooks}
cd fraud_labs
```

The data directory will house both the raw transaction logs and the engineered feature sets. The models directory stores serialized trained classifiers and their associated metadata. The outputs directory contains evaluation reports, confusion matrices, ROC curves, and cost-benefit analyses that translate model performance into economic terms. The notebooks directory provides a workspace for exploratory data analysis and iterative model development.

We begin with synthetic data generation that captures the key statistical properties of real payment card transactions. The following Python script generates 100,000 transactions with realistic feature distributions and a 1.5% fraud rate. Save this as `data/generate_transactions.py`:

```python
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

np.random.seed(42)

n_transactions = 100000
fraud_rate = 0.015

transaction_ids = [f"TXN{str(i).zfill(8)}" for i in range(n_transactions)]

timestamps = [datetime(2024, 1, 1) + timedelta(
    seconds=int(x)) for x in np.random.exponential(
    scale=30, size=n_transactions).cumsum()]

amounts = np.concatenate([
    np.random.gamma(shape=2, scale=25, size=int(n_transactions * 0.7)),
    np.random.gamma(shape=1.5, scale=100, size=int(n_transactions * 0.2)),
    np.random.gamma(shape=1, scale=500, size=int(n_transactions * 0.1))
])
np.random.shuffle(amounts)
amounts = np.round(amounts, 2)

merchant_categories = np.random.choice(
    ['GROCERY', 'RESTAURANT', 'GAS_STATION', 'RETAIL', 'ONLINE', 
     'TRAVEL', 'ENTERTAINMENT', 'HEALTHCARE', 'UTILITIES'],
    size=n_transactions,
    p=[0.25, 0.18, 0.12, 0.15, 0.12, 0.06, 0.05, 0.04, 0.03]
)

countries = np.random.choice(
    ['US', 'CA', 'GB', 'FR', 'DE', 'JP', 'AU', 'BR', 'IN', 'MX'],
    size=n_transactions,
    p=[0.65, 0.10, 0.08, 0.05, 0.04, 0.03, 0.02, 0.01, 0.01, 0.01]
)

card_present = np.random.choice([True, False], size=n_transactions, p=[0.55, 0.45])

customer_ids = np.random.choice(range(1, 25001), size=n_transactions)

is_fraud = np.random.choice([0, 1], size=n_transactions, 
                            p=[1 - fraud_rate, fraud_rate])

fraud_indices = np.where(is_fraud == 1)[0]
amounts[fraud_indices] = amounts[fraud_indices] * np.random.uniform(1.5, 4.0, 
                                                                     size=len(fraud_indices))
amounts[fraud_indices] = np.round(amounts[fraud_indices], 2)

for idx in fraud_indices[:int(len(fraud_indices) * 0.4)]:
    merchant_categories[idx] = np.random.choice(['ONLINE', 'TRAVEL', 'ENTERTAINMENT'])

for idx in fraud_indices[:int(len(fraud_indices) * 0.3)]:
    countries[idx] = np.random.choice(['BR', 'MX', 'IN', 'RU', 'CN'])

for idx in fraud_indices[:int(len(fraud_indices) * 0.6)]:
    card_present[idx] = False

df = pd.DataFrame({
    'transaction_id': transaction_ids,
    'timestamp': timestamps,
    'amount': amounts,
    'merchant_category': merchant_categories,
    'country': countries,
    'card_present': card_present,
    'customer_id': customer_ids,
    'is_fraud': is_fraud
})

df = df.sort_values('timestamp').reset_index(drop=True)

df.to_csv('data/transactions_raw.csv', index=False)
print(f"Generated {n_transactions} transactions")
print(f"Fraud rate: {df['is_fraud'].mean():.4f}")
print(f"Date range: {df['timestamp'].min()} to {df['timestamp'].max()}")
print(f"\nAmount statistics:")
print(df.groupby('is_fraud')['amount'].describe())
```

Execute this script to generate the raw transaction dataset. The synthetic data incorporates realistic economic patterns including temporal clustering (transactions arrive according to a Poisson process with exponential inter-arrival times), amount distributions that follow gamma distributions with different parameters for everyday purchases versus large transactions, and merchant category preferences that reflect consumer spending patterns. Crucially, the fraud cases exhibit statistically distinct characteristics: elevated transaction amounts, higher prevalence of card-not-present transactions, geographic anomalies, and concentration in high-risk merchant categories. These patterns mirror real-world fraud behavior where criminals exploit stolen card credentials for immediate high-value purchases before detection and card cancellation.

## Exercise 1: Foundational Practical Implementation

The foundational fraud detection system employs logistic regression as the primary classification algorithm. Despite the proliferation of sophisticated machine learning techniques, logistic regression remains operationally valuable because it produces interpretable coefficients that satisfy regulatory explainability requirements, converges rapidly on large datasets, and provides calibrated probability scores that map naturally to risk thresholds. The economic interpretation of logistic regression coefficients as log-odds ratios allows risk managers to communicate model behavior to compliance officers, auditors, and executive stakeholders who lack technical machine learning expertise.

Feature engineering constitutes the most economically impactful component of fraud detection system development. Raw transaction attributes such as amount, merchant category, and timestamp contain limited discriminatory power in isolation. The practitioner must construct derived features that capture deviations from established customer behavior patterns, temporal anomalies, geographic inconsistencies, and velocity indicators that measure the frequency and concentration of recent transactions. These engineered features transform the fraud detection problem from a classification task on raw attributes to a behavioral anomaly detection framework grounded in the economic principle that fraudsters exhibit systematically different transaction patterns than legitimate cardholders.

Create a feature engineering pipeline that computes customer-level aggregates, temporal features, and velocity indicators. Save the following as `data/feature_engineering.py`:

```python
import numpy as np
import pandas as pd
from datetime import timedelta

def engineer_features(df):
    df = df.copy()
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df.sort_values(['customer_id', 'timestamp']).reset_index(drop=True)
    
    df['hour'] = df['timestamp'].dt.hour
    df['day_of_week'] = df['timestamp'].dt.dayofweek
    df['is_weekend'] = (df['day_of_week'] >= 5).astype(int)
    df['is_night'] = ((df['hour'] >= 22) | (df['hour'] <= 6)).astype(int)
    
    customer_stats = df.groupby('customer_id').agg({
        'amount': ['mean', 'std', 'median', 'count'],
        'card_present': 'mean'
    }).reset_index()
    
    customer_stats.columns = ['customer_id', 'customer_avg_amount', 
                              'customer_std_amount', 'customer_median_amount',
                              'customer_txn_count', 'customer_card_present_rate']
    
    df = df.merge(customer_stats, on='customer_id', how='left')
    
    df['amount_vs_avg'] = (df['amount'] - df['customer_avg_amount']) / (
        df['customer_std_amount'] + 1e-5)
    
    df['amount_vs_median'] = df['amount'] / (df['customer_median_amount'] + 1e-5)
    
    df['time_since_last'] = df.groupby('customer_id')['timestamp'].diff().dt.total_seconds()
    df['time_since_last'] = df['time_since_last'].fillna(86400)
    
    df['log_time_since_last'] = np.log1p(df['time_since_last'])
    
    velocity_windows = [3600, 86400, 604800]
    
    for window in velocity_windows:
        window_name = f"velocity_{window}s"
        df[window_name] = 0
        
        for customer_id in df['customer_id'].unique():
            customer_mask = df['customer_id'] == customer_id
            customer_df = df[customer_mask].copy()
            
            for idx in customer_df.index:
                current_time = df.loc[idx, 'timestamp']
                window_start = current_time - timedelta(seconds=window)
                
                recent_mask = (df['customer_id'] == customer_id) & \
                              (df['timestamp'] >= window_start) & \
                              (df['timestamp'] < current_time)
                
                df.loc[idx, window_name] = recent_mask.sum()
    
    country_risk = df.groupby('country')['is_fraud'].mean().to_dict()
    df['country_risk_score'] = df['country'].map(country_risk)
    
    category_risk = df.groupby('merchant_category')['is_fraud'].mean().to_dict()
    df['category_risk_score'] = df['merchant_category'].map(category_risk)
    
    return df

df_raw = pd.read_csv('data/transactions_raw.csv')
print(f"Loaded {len(df_raw)} transactions")

df_features = engineer_features(df_raw)

print(f"\nEngineered features shape: {df_features.shape}")
print(f"Feature columns: {df_features.columns.tolist()}")

df_features.to_csv('data/transactions_features.csv', index=False)
print("\nFeature engineering complete")
print(f"Fraud rate: {df_features['is_fraud'].mean():.4f}")
```

Execute this feature engineering script. The pipeline constructs temporal features that capture circadian patterns in transaction timing, recognizing that fraudulent transactions exhibit distinct time-of-day and day-of-week distributions compared to legitimate spending. The customer-level aggregate statistics establish a behavioral baseline for each cardholder, enabling the calculation of amount deviation metrics that quantify how abnormal the current transaction is relative to historical patterns. The velocity features count recent transactions within sliding time windows, detecting rapid-fire transaction sequences that signal account takeover or card testing behavior. The country and merchant category risk scores encode empirical fraud rates as features, allowing the model to learn that certain geographic regions and merchant types carry elevated fraud risk.

The economic intuition underlying these engineered features derives from information asymmetry theory and revealed preference. Legitimate cardholders exhibit consistent behavioral patterns that reflect stable preferences, budget constraints, and routine spending habits. Fraudsters, by contrast, seek to maximize the value extracted before detection, leading to large transactions, unusual timing, geographic inconsistencies relative to the cardholder's established patterns, and concentration in liquid, easily monetized merchant categories. The velocity features operationalize the economic concept of time discounting: fraudsters exhibit extreme present-bias and attempt to extract maximum value in minimal time.

Now construct the training pipeline with careful attention to temporal validation structure. In fraud detection, data leakage represents a severe operational risk. If the model trains on information from the future or if customer-level statistics incorporate fraudulent transactions from the validation period, the laboratory performance metrics will overstate real-world effectiveness. Implement a strict temporal train-test split where the model trains on historical data and validates on subsequent transactions, mimicking production deployment where the model must predict fraud risk on future, unseen events.

Create the model training script as `models/train_logistic.py`:

```python
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (classification_report, confusion_matrix, 
                             roc_auc_score, roc_curve, precision_recall_curve,
                             average_precision_score)
from imblearn.over_sampling import SMOTE
import matplotlib.pyplot as plt
import seaborn as sns
import pickle

df = pd.read_csv('data/transactions_features.csv')
df['timestamp'] = pd.to_datetime(df['timestamp'])

df = df.sort_values('timestamp').reset_index(drop=True)

split_date = df['timestamp'].quantile(0.8)
train_df = df[df['timestamp'] < split_date].copy()
test_df = df[df['timestamp'] >= split_date].copy()

print(f"Training set: {len(train_df)} transactions ({train_df['is_fraud'].sum()} fraud)")
print(f"Test set: {len(test_df)} transactions ({test_df['is_fraud'].sum()} fraud)")
print(f"Training period: {train_df['timestamp'].min()} to {train_df['timestamp'].max()}")
print(f"Test period: {test_df['timestamp'].min()} to {test_df['timestamp'].max()}")

feature_cols = [
    'amount', 'hour', 'day_of_week', 'is_weekend', 'is_night',
    'customer_avg_amount', 'customer_std_amount', 'customer_txn_count',
    'customer_card_present_rate', 'amount_vs_avg', 'amount_vs_median',
    'log_time_since_last', 'velocity_3600s', 'velocity_86400s', 'velocity_604800s',
    'country_risk_score', 'category_risk_score'
]

categorical_cols = ['merchant_category', 'country']

label_encoders = {}
for col in categorical_cols:
    le = LabelEncoder()
    train_df[f'{col}_encoded'] = le.fit_transform(train_df[col])
    test_df[f'{col}_encoded'] = test_df[col].map(
        dict(zip(le.classes_, le.transform(le.classes_)))
    ).fillna(-1).astype(int)
    label_encoders[col] = le
    feature_cols.append(f'{col}_encoded')

train_df['card_present'] = train_df['card_present'].astype(int)
test_df['card_present'] = test_df['card_present'].astype(int)
feature_cols.append('card_present')

X_train = train_df[feature_cols].fillna(0)
y_train = train_df['is_fraud']

X_test = test_df[feature_cols].fillna(0)
y_test = test_df['is_fraud']

scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

print(f"\nOriginal training class distribution:")
print(f"Legitimate: {(y_train == 0).sum()} ({(y_train == 0).mean():.4f})")
print(f"Fraud: {(y_train == 1).sum()} ({(y_train == 1).mean():.4f})")

smote = SMOTE(sampling_strategy=0.3, random_state=42)
X_train_resampled, y_train_resampled = smote.fit_resample(X_train_scaled, y_train)

print(f"\nResampled training class distribution:")
print(f"Legitimate: {(y_train_resampled == 0).sum()} ({(y_train_resampled == 0).mean():.4f})")
print(f"Fraud: {(y_train_resampled == 1).sum()} ({(y_train_resampled == 1).mean():.4f})")

model = LogisticRegression(
    penalty='l2',
    C=0.1,
    class_weight=None,
    solver='lbfgs',
    max_iter=1000,
    random_state=42
)

model.fit(X_train_resampled, y_train_resampled)

y_train_pred_proba = model.predict_proba(X_train_scaled)[:, 1]
y_test_pred_proba = model.predict_proba(X_test_scaled)[:, 1]

train_auc = roc_auc_score(y_train, y_train_pred_proba)
test_auc = roc_auc_score(y_test, y_test_pred_proba)

train_ap = average_precision_score(y_train, y_train_pred_proba)
test_ap = average_precision_score(y_test, y_test_pred_proba)

print(f"\n=== Model Performance ===")
print(f"Training AUC-ROC: {train_auc:.4f}")
print(f"Test AUC-ROC: {test_auc:.4f}")
print(f"Training Average Precision: {train_ap:.4f}")
print(f"Test Average Precision: {test_ap:.4f}")

thresholds = [0.3, 0.5, 0.7, 0.9]

for threshold in thresholds:
    y_test_pred = (y_test_pred_proba >= threshold).astype(int)
    
    cm = confusion_matrix(y_test, y_test_pred)
    tn, fp, fn, tp = cm.ravel()
    
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    fpr = fp / (fp + tn) if (fp + tn) > 0 else 0
    
    print(f"\n--- Threshold: {threshold} ---")
    print(f"Precision: {precision:.4f}")
    print(f"Recall: {recall:.4f}")
    print(f"False Positive Rate: {fpr:.4f}")
    print(f"Confusion Matrix:")
    print(f"  TN: {tn:6d}  FP: {fp:6d}")
    print(f"  FN: {fn:6d}  TP: {tp:6d}")

feature_importance = pd.DataFrame({
    'feature': feature_cols,
    'coefficient': model.coef_[0]
}).sort_values('coefficient', key=abs, ascending=False)

print(f"\n=== Top 10 Feature Coefficients ===")
print(feature_importance.head(10).to_string(index=False))

with open('models/logistic_model.pkl', 'wb') as f:
    pickle.dump(model, f)

with open('models/scaler.pkl', 'wb') as f:
    pickle.dump(scaler, f)

with open('models/label_encoders.pkl', 'wb') as f:
    pickle.dump(label_encoders, f)

metadata = {
    'feature_cols': feature_cols,
    'train_auc': train_auc,
    'test_auc': test_auc,
    'train_ap': train_ap,
    'test_ap': test_ap,
    'train_size': len(train_df),
    'test_size': len(test_df)
}

with open('models/model_metadata.pkl', 'wb') as f:
    pickle.dump(metadata, f)

fig, axes = plt.subplots(1, 2, figsize=(14, 5))

fpr, tpr, _ = roc_curve(y_test, y_test_pred_proba)
axes[0].plot(fpr, tpr, label=f'Logistic Regression (AUC={test_auc:.3f})', linewidth=2)
axes[0].plot([0, 1], [0, 1], 'k--', label='Random Classifier', linewidth=1)
axes[0].set_xlabel('False Positive Rate', fontsize=11)
axes[0].set_ylabel('True Positive Rate', fontsize=11)
axes[0].set_title('ROC Curve - Test Set', fontsize=12, fontweight='bold')
axes[0].legend(fontsize=10)
axes[0].grid(alpha=0.3)

precision, recall, _ = precision_recall_curve(y_test, y_test_pred_proba)
axes[1].plot(recall, precision, label=f'Logistic Regression (AP={test_ap:.3f})', linewidth=2)
axes[1].axhline(y=y_test.mean(), color='k', linestyle='--', 
                label=f'Baseline (Fraud Rate={y_test.mean():.3f})', linewidth=1)
axes[1].set_xlabel('Recall', fontsize=11)
axes[1].set_ylabel('Precision', fontsize=11)
axes[1].set_title('Precision-Recall Curve - Test Set', fontsize=12, fontweight='bold')
axes[1].legend(fontsize=10)
axes[1].grid(alpha=0.3)

plt.tight_layout()
plt.savefig('outputs/logistic_performance.png', dpi=300, bbox_inches='tight')
print("\nPerformance plots saved to outputs/logistic_performance.png")

fig, ax = plt.subplots(figsize=(10, 8))
top_features = feature_importance.head(15)
colors = ['red' if x < 0 else 'green' for x in top_features['coefficient']]
ax.barh(range(len(top_features)), top_features['coefficient'], color=colors, alpha=0.7)
ax.set_yticks(range(len(top_features)))
ax.set_yticklabels(top_features['feature'])
ax.set_xlabel('Coefficient (Log-Odds Ratio)', fontsize=11)
ax.set_title('Top 15 Feature Coefficients - Logistic Regression', fontsize=12, fontweight='bold')
ax.axvline(x=0, color='black', linestyle='-', linewidth=0.8)
ax.grid(axis='x', alpha=0.3)
plt.tight_layout()
plt.savefig('outputs/feature_importance.png', dpi=300, bbox_inches='tight')
print("Feature importance plot saved to outputs/feature_importance.png")
```

Execute this training script. The temporal train-test split preserves the chronological ordering of transactions, ensuring that the model never sees future data during training. This validation structure mirrors production deployment where the model must generalize to subsequent time periods with potentially evolving fraud patterns. The SMOTE resampling technique addresses the extreme class imbalance by synthesizing artificial minority class examples in feature space, preventing the model from collapsing to a trivial classifier that predicts all transactions as legitimate. The resampling ratio of 0.3 (fraudulent transactions comprise 30% of the resampled training set) balances the competing objectives of providing sufficient fraud examples for learning while avoiding over-representation that degrades precision.

The threshold analysis reveals the fundamental economic tradeoff in fraud detection system design. Lowering the classification threshold increases recall (the model catches more fraudulent transactions) at the cost of elevated false positives (legitimate transactions incorrectly flagged for review). The optimal threshold depends on the relative economic costs of false positives versus false negatives. A false positive imposes customer friction costs: delayed transaction approval, potential purchase abandonment, customer service overhead, and reputational damage. A false negative permits fraud losses, chargeback processing costs, and exposure to regulatory sanctions. Financial institutions typically calibrate thresholds to achieve 60-80% fraud recall while maintaining false positive rates below 1-3%.

The feature coefficients provide economic interpretability. Positive coefficients indicate features associated with elevated fraud risk. The velocity features (counts of recent transactions) exhibit positive coefficients because fraudsters engage in rapid-fire transaction sequences. The amount deviation metrics carry positive coefficients as fraudulent transactions systematically deviate from cardholder norms. The country and category risk scores encode empirical fraud rate patterns learned from historical data. Negative coefficients correspond to protective factors: card-present transactions reduce fraud risk because physical card possession provides authentication.

## Exercise 2: Parameter Variation & Empirical Analysis

The logistic regression baseline establishes a benchmark for model performance and interpretability, but gradient boosting decision trees (GBDT) frequently achieve superior predictive accuracy in fraud detection applications. GBDT methods construct ensembles of weak decision trees that sequentially correct the errors of previous trees, capturing complex non-linear interactions between features that logistic regression's linear decision boundary cannot represent. The economic intuition is that fraud patterns involve conditional logic and threshold effects: a transaction is only suspicious if the amount exceeds the customer's historical maximum AND the merchant category is high-risk AND the time since last transaction is less than one hour. GBDT naturally learns these conjunctive rules through hierarchical tree splits.

Implement an XGBoost classifier to assess the performance gain from non-linear modeling. XGBoost incorporates regularization terms that penalize model complexity, reducing overfitting risk relative to standard gradient boosting. The regularization parameters $\lambda$ (L2 penalty on leaf weights) and $\alpha$ (L1 penalty on leaf weights) control the bias-variance tradeoff, with higher values producing simpler models that generalize better to unseen data but potentially sacrifice training set performance.

Create the XGBoost training script as `models/train_xgboost.py`:

```python
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import (classification_report, confusion_matrix, 
                             roc_auc_score, roc_curve, precision_recall_curve,
                             average_precision_score)
import xgboost as xgb
import matplotlib.pyplot as plt
import seaborn as sns
import pickle

df = pd.read_csv('data/transactions_features.csv')
df['timestamp'] = pd.to_datetime(df['timestamp'])
df = df.sort_values('timestamp').reset_index(drop=True)

split_date = df['timestamp'].quantile(0.8)
train_df = df[df['timestamp'] < split_date].copy()
test_df = df[df['timestamp'] >= split_date].copy()

print(f"Training set: {len(train_df)} transactions ({train_df['is_fraud'].sum()} fraud)")
print(f"Test set: {len(test_df)} transactions ({test_df['is_fraud'].sum()} fraud)")

feature_cols = [
    'amount', 'hour', 'day_of_week', 'is_weekend', 'is_night',
    'customer_avg_amount', 'customer_std_amount', 'customer_txn_count',
    'customer_card_present_rate', 'amount_vs_avg', 'amount_vs_median',
    'log_time_since_last', 'velocity_3600s', 'velocity_86400s', 'velocity_604800s',
    'country_risk_score', 'category_risk_score'
]

categorical_cols = ['merchant_category', 'country']

label_encoders = {}
for col in categorical_cols:
    le = LabelEncoder()
    train_df[f'{col}_encoded'] = le.fit_transform(train_df[col])
    test_df[f'{col}_encoded'] = test_df[col].map(
        dict(zip(le.classes_, le.transform(le.classes_)))
    ).fillna(-1).astype(int)
    label_encoders[col] = le
    feature_cols.append(f'{col}_encoded')

train_df['card_present'] = train_df['card_present'].astype(int)
test_df['card_present'] = test_df['card_present'].astype(int)
feature_cols.append('card_present')

X_train = train_df[feature_cols].fillna(0)
y_train = train_df['is_fraud']

X_test = test_df[feature_cols].fillna(0)
y_test = test_df['is_fraud']

fraud_weight = len(y_train) / (2 * y_train.sum())
print(f"\nClass weight for fraud: {fraud_weight:.2f}")

model = xgb.XGBClassifier(
    n_estimators=200,
    max_depth=6,
    learning_rate=0.1,
    subsample=0.8,
    colsample_bytree=0.8,
    gamma=1.0,
    reg_alpha=0.1,
    reg_lambda=1.0,
    scale_pos_weight=fraud_weight,
    eval_metric='aucpr',
    random_state=42,
    use_label_encoder=False
)

eval_set = [(X_train, y_train), (X_test, y_test)]

model.fit(
    X_train, y_train,
    eval_set=eval_set,
    verbose=False
)

y_train_pred_proba = model.predict_proba(X_train)[:, 1]
y_test_pred_proba = model.predict_proba(X_test)[:, 1]

train_auc = roc_auc_score(y_train, y_train_pred_proba)
test_auc = roc_auc_score(y_test, y_test_pred_proba)

train_ap = average_precision_score(y_train, y_train_pred_proba)
test_ap = average_precision_score(y_test, y_test_pred_proba)

print(f"\n=== XGBoost Model Performance ===")
print(f"Training AUC-ROC: {train_auc:.4f}")
print(f"Test AUC-ROC: {test_auc:.4f}")
print(f"Training Average Precision: {train_ap:.4f}")
print(f"Test Average Precision: {test_ap:.4f}")

thresholds = [0.3, 0.5, 0.7, 0.9]

for threshold in thresholds:
    y_test_pred = (y_test_pred_proba >= threshold).astype(int)
    
    cm = confusion_matrix(y_test, y_test_pred)
    tn, fp, fn, tp = cm.ravel()
    
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    fpr = fp / (fp + tn) if (fp + tn) > 0 else 0
    
    print(f"\n--- Threshold: {threshold} ---")
    print(f"Precision: {precision:.4f}")
    print(f"Recall: {recall:.4f}")
    print(f"False Positive Rate: {fpr:.4f}")
    print(f"Confusion Matrix:")
    print(f"  TN: {tn:6d}  FP: {fp:6d}")
    print(f"  FN: {fn:6d}  TP: {tp:6d}")

feature_importance = pd.DataFrame({
    'feature': feature_cols,
    'importance': model.feature_importances_
}).sort_values('importance', ascending=False)

print(f"\n=== Top 10 Feature Importances ===")
print(feature_importance.head(10).to_string(index=False))

with open('models/xgboost_model.pkl', 'wb') as f:
    pickle.dump(model, f)

metadata = {
    'feature_cols': feature_cols,
    'train_auc': train_auc,
    'test_auc': test_auc,
    'train_ap': train_ap,
    'test_ap': test_ap,
    'train_size': len(train_df),
    'test_size': len(test_df)
}

with open('models/xgboost_metadata.pkl', 'wb') as f:
    pickle.dump(metadata, f)

fig, axes = plt.subplots(1, 2, figsize=(14, 5))

fpr, tpr, _ = roc_curve(y_test, y_test_pred_proba)
axes[0].plot(fpr, tpr, label=f'XGBoost (AUC={test_auc:.3f})', linewidth=2, color='darkgreen')
axes[0].plot([0, 1], [0, 1], 'k--', label='Random Classifier', linewidth=1)
axes[0].set_xlabel('False Positive Rate', fontsize=11)
axes[0].set_ylabel('True Positive Rate', fontsize=11)
axes[0].set_title('ROC Curve - Test Set (XGBoost)', fontsize=12, fontweight='bold')
axes[0].legend(fontsize=10)
axes[0].grid(alpha=0.3)

precision, recall, _ = precision_recall_curve(y_test, y_test_pred_proba)
axes[1].plot(recall, precision, label=f'XGBoost (AP={test_ap:.3f})', linewidth=2, color='darkgreen')
axes[1].axhline(y=y_test.mean(), color='k', linestyle='--', 
                label=f'Baseline (Fraud Rate={y_test.mean():.3f})', linewidth=1)
axes[1].set_xlabel('Recall', fontsize=11)
axes[1].set_ylabel('Precision', fontsize=11)
axes[1].set_title('Precision-Recall Curve - Test Set (XGBoost)', fontsize=12, fontweight='bold')
axes[1].legend(fontsize=10)
axes[1].grid(alpha=0.3)

plt.tight_layout()
plt.savefig('outputs/xgboost_performance.png', dpi=300, bbox_inches='tight')
print("\nXGBoost performance plots saved to outputs/xgboost_performance.png")

fig, ax = plt.subplots(figsize=(10, 8))
top_features = feature_importance.head(15)
ax.barh(range(len(top_features)), top_features['importance'], color='darkgreen', alpha=0.7)
ax.set_yticks(range(len(top_features)))
ax.set_yticklabels(top_features['feature'])
ax.set_xlabel('Feature Importance (Gain)', fontsize=11)
ax.set_title('Top 15 Feature Importances - XGBoost', fontsize=12, fontweight='bold')
ax.grid(axis='x', alpha=0.3)
plt.tight_layout()
plt.savefig('outputs/xgboost_feature_importance.png', dpi=300, bbox_inches='tight')
print("XGBoost feature importance plot saved to outputs/xgboost_feature_importance.png")
```

Execute this XGBoost training script and compare the AUC-ROC and Average Precision metrics to the logistic regression baseline. Typical performance gains range from 2-5 percentage points in AUC-ROC and 5-10 percentage points in Average Precision. The Precision-Recall curve proves more informative than ROC for imbalanced classification problems because it focuses on the minority class performance and does not give credit for correctly classifying the abundant negative examples.

The XGBoost feature importance rankings differ from logistic regression coefficients because the GBDT framework measures importance through total gain (the cumulative reduction in loss function from splits on each feature) rather than marginal effects holding other features constant. Interaction features that provide minimal marginal predictive power in isolation may rank highly if they prove informative when combined with other features through sequential tree splits. This property makes GBDT particularly effective for fraud detection where risk depends on conjunctions of conditions rather than additive feature contributions.

Now implement a comprehensive cost-benefit analysis that translates model performance metrics into economic terms. The confusion matrix provides counts of true positives, false positives, true negatives, and false negatives, but financial executives require dollar-denominated metrics: total fraud losses prevented, false positive costs, net economic value, and return on investment. The cost-benefit framework makes explicit the economic tradeoffs embedded in threshold selection and enables data-driven calibration of the fraud detection system to maximize institutional profitability rather than optimizing abstract statistical metrics.

Create the economic analysis script as `outputs/cost_benefit_analysis.py`:

```python
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import pickle
from sklearn.metrics import confusion_matrix

df = pd.read_csv('data/transactions_features.csv')
df['timestamp'] = pd.to_datetime(df['timestamp'])
df = df.sort_values('timestamp').reset_index(drop=True)

split_date = df['timestamp'].quantile(0.8)
test_df = df[df['timestamp'] >= split_date].copy()

feature_cols = [
    'amount', 'hour', 'day_of_week', 'is_weekend', 'is_night',
    'customer_avg_amount', 'customer_std_amount', 'customer_txn_count',
    'customer_card_present_rate', 'amount_vs_avg', 'amount_vs_median',
    'log_time_since_last', 'velocity_3600s', 'velocity_86400s', 'velocity_604800s',
    'country_risk_score', 'category_risk_score', 'merchant_category_encoded',
    'country_encoded', 'card_present'
]

X_test = test_df[feature_cols].fillna(0)
y_test = test_df['is_fraud']
amounts_test = test_df['amount'].values

with open('models/xgboost_model.pkl', 'rb') as f:
    model = pickle.load(f)

y_test_pred_proba = model.predict_proba(X_test)[:, 1]

avg_fraud_amount = test_df[test_df['is_fraud'] == 1]['amount'].mean()
median_fraud_amount = test_df[test_df['is_fraud'] == 1]['amount'].median()

print(f"Average fraud transaction amount: ${avg_fraud_amount:.2f}")
print(f"Median fraud transaction amount: ${median_fraud_amount:.2f}")

FRAUD_LOSS_RATE = 1.0
MANUAL_REVIEW_COST = 15.0
CUSTOMER_FRICTION_COST = 8.0
CHARGEBACK_FEE = 25.0

thresholds = np.arange(0.1, 1.0, 0.05)

results = []

for threshold in thresholds:
    y_pred = (y_test_pred_proba >= threshold).astype(int)
    
    cm = confusion_matrix(y_test, y_pred)
    tn, fp, fn, tp = cm.ravel()
    
    fraud_amounts_caught = amounts_test[(y_test == 1) & (y_pred == 1)]
    fraud_amounts_missed = amounts_test[(y_test == 1) & (y_pred == 0)]
    
    fraud_losses_prevented = fraud_amounts_caught.sum() * FRAUD_LOSS_RATE
    fraud_losses_incurred = fraud_amounts_missed.sum() * FRAUD_LOSS_RATE
    
    manual_review_costs = (tp + fp) * MANUAL_REVIEW_COST
    
    customer_friction_costs = fp * CUSTOMER_FRICTION_COST
    
    chargeback_costs = fn * CHARGEBACK_FEE
    
    total_costs = manual_review_costs + customer_friction_costs + chargeback_costs + fraud_losses_incurred
    
    net_value = fraud_losses_prevented - (manual_review_costs + customer_friction_costs + chargeback_costs)
    
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    fpr = fp / (fp + tn) if (fp + tn) > 0 else 0
    
    results.append({
        'threshold': threshold,
        'tp': tp,
        'fp': fp,
        'tn': tn,
        'fn': fn,
        'precision': precision,
        'recall': recall,
        'fpr': fpr,
        'fraud_prevented': fraud_losses_prevented,
        'fraud_incurred': fraud_losses_incurred,
        'review_costs': manual_review_costs,
        'friction_costs': customer_friction_costs,
        'chargeback_costs': chargeback_costs,
        'total_costs': total_costs,
        'net_value': net_value
    })

results_df = pd.DataFrame(results)

optimal_idx = results_df['net_value'].idxmax()
optimal_row = results_df.loc[optimal_idx]

print(f"\n=== Economic Optimal Threshold ===")
print(f"Threshold: {optimal_row['threshold']:.2f}")
print(f"Precision: {optimal_row['precision']:.4f}")
print(f"Recall: {optimal_row['recall']:.4f}")
print(f"False Positive Rate: {optimal_row['fpr']:.4f}")
print(f"\nEconomic Metrics:")
print(f"Fraud Prevented: ${optimal_row['fraud_prevented']:,.2f}")
print(f"Fraud Incurred: ${optimal_row['fraud_incurred']:,.2f}")
print(f"Manual Review Costs: ${optimal_row['review_costs']:,.2f}")
print(f"Customer Friction Costs: ${optimal_row['friction_costs']:,.2f}")
print(f"Chargeback Costs: ${optimal_row['chargeback_costs']:,.2f}")
print(f"Total Costs: ${optimal_row['total_costs']:,.2f}")
print(f"Net Economic Value: ${optimal_row['net_value']:,.2f}")

baseline_fraud_loss = test_df[test_df['is_fraud'] == 1]['amount'].sum() * FRAUD_LOSS_RATE
baseline_chargeback = test_df['is_fraud'].sum() * CHARGEBACK_FEE
baseline_total_cost = baseline_fraud_loss + baseline_chargeback

roi = (optimal_row['net_value'] / baseline_total_cost) * 100 if baseline_total_cost > 0 else 0

print(f"\n=== Baseline Scenario (No Fraud Detection) ===")
print(f"Total Fraud Losses: ${baseline_fraud_loss:,.2f}")
print(f"Total Chargeback Fees: ${baseline_chargeback:,.2f}")
print(f"Total Baseline Cost: ${baseline_total_cost:,.2f}")
print(f"\nROI of Fraud Detection System: {roi:.2f}%")

results_df.to_csv('outputs/cost_benefit_analysis.csv', index=False)
print("\nCost-benefit analysis saved to outputs/cost_benefit_analysis.csv")

fig, axes = plt.subplots(2, 2, figsize=(14, 10))

ax = axes[0, 0]
ax.plot(results_df['threshold'], results_df['net_value'], linewidth=2, color='darkblue')
ax.axvline(x=optimal_row['threshold'], color='red', linestyle='--', linewidth=1.5, 
           label=f"Optimal: {optimal_row['threshold']:.2f}")
ax.set_xlabel('Classification Threshold', fontsize=11)
ax.set_ylabel('Net Economic Value ($)', fontsize=11)
ax.set_title('Net Economic Value vs. Threshold', fontsize=12, fontweight='bold')
ax.legend(fontsize=10)
ax.grid(alpha=0.3)

ax = axes[0, 1]
ax.plot(results_df['threshold'], results_df['recall'], linewidth=2, label='Recall (TPR)', color='green')
ax.plot(results_df['threshold'], results_df['precision'], linewidth=2, label='Precision', color='blue')
ax.plot(results_df['threshold'], results_df['fpr'], linewidth=2, label='FPR', color='red')
ax.axvline(x=optimal_row['threshold'], color='black', linestyle='--', linewidth=1.5, alpha=0.5)
ax.set_xlabel('Classification Threshold', fontsize=11)
ax.set_ylabel('Rate', fontsize=11)
ax.set_title('Performance Metrics vs. Threshold', fontsize=12, fontweight='bold')
ax.legend(fontsize=10)
ax.grid(alpha=0.3)

ax = axes[1, 0]
cost_components = ['review_costs', 'friction_costs', 'chargeback_costs', 'fraud_incurred']
cost_labels = ['Manual Review', 'Customer Friction', 'Chargebacks', 'Fraud Incurred']
for cost_col, label in zip(cost_components, cost_labels):
    ax.plot(results_df['threshold'], results_df[cost_col], linewidth=2, label=label)
ax.axvline(x=optimal_row['threshold'], color='black', linestyle='--', linewidth=1.5, alpha=0.5)
ax.set_xlabel('Classification Threshold', fontsize=11)
ax.set_ylabel('Cost ($)', fontsize=11)
ax.set_title('Cost Components vs. Threshold', fontsize=12, fontweight='bold')
ax.legend(fontsize=10)
ax.grid(alpha=0.3)

ax = axes[1, 1]
optimal_costs = [
    optimal_row['review_costs'],
    optimal_row['friction_costs'],
    optimal_row['chargeback_costs'],
    optimal_row['fraud_incurred']
]
colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']
ax.pie(optimal_costs, labels=cost_labels, autopct='%1.1f%%', colors=colors, startangle=90)
ax.set_title(f'Cost Breakdown at Optimal Threshold ({optimal_row["threshold"]:.2f})', 
             fontsize=12, fontweight='bold')

plt.tight_layout()
plt.savefig('outputs/cost_benefit_plots.png', dpi=300, bbox_inches='tight')
print("Cost-benefit plots saved to outputs/cost_benefit_plots.png")
```

Execute this cost-benefit analysis script. The economic optimal threshold differs from thresholds that maximize statistical metrics like F1-score or Youden's J-statistic because it incorporates the asymmetric costs of different error types and the monetary value of prevented fraud. The optimal threshold typically falls in the 0.3 to 0.5 range for most financial institutions, balancing fraud capture rates with acceptable false positive volumes.

The cost parameters warrant careful calibration to institutional specifics. Manual review costs include analyst labor, quality assurance overhead, and system infrastructure for flagged transaction queues. Customer friction costs reflect the expected loss from declined legitimate transactions that would have completed absent intervention, incorporating both immediate lost revenue and long-term customer attrition effects. Chargeback fees cover processing costs and penalty assessments from card networks. The fraud loss rate accounts for recovery rates through investigation and insurance. Sensitivity analysis on these cost parameters reveals which operational improvements deliver maximum economic impact: reducing manual review costs through automation, minimizing customer friction through adaptive authentication, or improving fraud recovery processes.

## Exercise 3: Stress Testing, Boundary Failure & Recovery Protocol

Production fraud detection systems must maintain performance under distribution shift, adversarial attacks, and operational failures. Fraudsters adapt their behavior in response to detection systems, leading to temporal drift where the statistical properties of fraudulent transactions evolve over time. New fraud schemes emerge (synthetic identity fraud, account takeover, card-not-present abuse) that exhibit different feature patterns than historical training data. The system must detect these changes and trigger model retraining or feature engineering updates before performance degradation becomes severe.

Implement a temporal stability analysis that tracks model performance across time windows to detect drift. The analysis computes rolling metrics on sequential test batches, identifying periods where AUC-ROC or Average Precision decline significantly relative to validation performance. This monitoring framework operationalizes the statistical process control principles that manufacturing quality systems employ to detect production line degradation.

Create the temporal stability analysis script as `outputs/temporal_stability.py`:

```python
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import pickle
from sklearn.metrics import roc_auc_score, average_precision_score, confusion_matrix

df = pd.read_csv('data/transactions_features.csv')
df['timestamp'] = pd.to_datetime(df['timestamp'])
df = df.sort_values('timestamp').reset_index(drop=True)

split_date = df['timestamp'].quantile(0.8)
test_df = df[df['timestamp'] >= split_date].copy()

feature_cols = [
    'amount', 'hour', 'day_of_week', 'is_weekend', 'is_night',
    'customer_avg_amount', 'customer_std_amount', 'customer_txn_count',
    'customer_card_present_rate', 'amount_vs_avg', 'amount_vs_median',
    'log_time_since_last', 'velocity_3600s', 'velocity_86400s', 'velocity_604800s',
    'country_risk_score', 'category_risk_score', 'merchant_category_encoded',
    'country_encoded', 'card_present'
]

X_test = test_df[feature_cols].fillna(0)
y_test = test_df['is_fraud']

with open('models/xgboost_model.pkl', 'rb') as f:
    model = pickle.load(f)

y_test_pred_proba = model.predict_proba(X_test)[:, 1]

test_df['fraud_score'] = y_test_pred_proba

test_df['week'] = ((test_df['timestamp'] - test_df['timestamp'].min()).dt.total_seconds() / 
                   (7 * 86400)).astype(int)

weekly_metrics = []

for week in sorted(test_df['week'].unique()):
    week_df = test_df[test_df['week'] == week]
    
    if len(week_df) < 100 or week_df['is_fraud'].sum() < 5:
        continue
    
    y_true = week_df['is_fraud']
    y_scores = week_df['fraud_score']
    
    auc = roc_auc_score(y_true, y_scores)
    ap = average_precision_score(y_true, y_scores)
    
    fraud_rate = y_true.mean()
    avg_fraud_score = y_scores[y_true == 1].mean()
    avg_legit_score = y_scores[y_true == 0].mean()
    
    y_pred = (y_scores >= 0.5).astype(int)
    cm = confusion_matrix(y_true, y_pred)
    tn, fp, fn, tp = cm.ravel()
    
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    
    weekly_metrics.append({
        'week': week,
        'n_transactions': len(week_df),
        'fraud_rate': fraud_rate,
        'auc': auc,
        'ap': ap,
        'precision': precision,
        'recall': recall,
        'avg_fraud_score': avg_fraud_score,
        'avg_legit_score': avg_legit_score
    })

weekly_df = pd.DataFrame(weekly_metrics)

overall_auc = roc_auc_score(test_df['is_fraud'], test_df['fraud_score'])
overall_ap = average_precision_score(test_df['is_fraud'], test_df['fraud_score'])

auc_std = weekly_df['auc'].std()
ap_std = weekly_df['ap'].std()

drift_threshold_auc = overall_auc - 2 * auc_std
drift_threshold_ap = overall_ap - 2 * ap_std

drifted_weeks_auc = weekly_df[weekly_df['auc'] < drift_threshold_auc]
drifted_weeks_ap = weekly_df[weekly_df['ap'] < drift_threshold_ap]

print("=== Temporal Stability Analysis ===")
print(f"\nOverall Test Set Performance:")
print(f"AUC-ROC: {overall_auc:.4f}")
print(f"Average Precision: {overall_ap:.4f}")

print(f"\nWeekly Performance Statistics:")
print(f"AUC-ROC: {weekly_df['auc'].mean():.4f} ± {auc_std:.4f}")
print(f"Average Precision: {weekly_df['ap'].mean():.4f} ± {ap_std:.4f}")

print(f"\nDrift Detection (2-sigma threshold):")
print(f"AUC-ROC drift threshold: {drift_threshold_auc:.4f}")
print(f"Average Precision drift threshold: {drift_threshold_ap:.4f}")

if len(drifted_weeks_auc) > 0:
    print(f"\nWeeks with AUC-ROC drift detected: {len(drifted_weeks_auc)}")
    print(drifted_weeks_auc[['week', 'auc', 'ap', 'fraud_rate']].to_string(index=False))

if len(drifted_weeks_ap) > 0:
    print(f"\nWeeks with Average Precision drift detected: {len(drifted_weeks_ap)}")
    print(drifted_weeks_ap[['week', 'auc', 'ap', 'fraud_rate']].to_string(index=False))

weekly_df.to_csv('outputs/temporal_stability.csv', index=False)
print("\nTemporal stability analysis saved to outputs/temporal_stability.csv")

fig, axes = plt.subplots(2, 2, figsize=(14, 10))

ax = axes[0, 0]
ax.plot(weekly_df['week'], weekly_df['auc'], marker='o', linewidth=2, markersize=6, color='darkblue')
ax.axhline(y=overall_auc, color='green', linestyle='--', linewidth=1.5, label=f'Overall: {overall_auc:.3f}')
ax.axhline(y=drift_threshold_auc, color='red', linestyle='--', linewidth=1.5, 
           label=f'Drift Threshold: {drift_threshold_auc:.3f}')
ax.set_xlabel('Week', fontsize=11)
ax.set_ylabel('AUC-ROC', fontsize=11)
ax.set_title('AUC-ROC Over Time', fontsize=12, fontweight='bold')
ax.legend(fontsize=10)
ax.grid(alpha=0.3)

ax = axes[0, 1]
ax.plot(weekly_df['week'], weekly_df['ap'], marker='o', linewidth=2, markersize=6, color='darkgreen')
ax.axhline(y=overall_ap, color='green', linestyle='--', linewidth=1.5, label=f'Overall: {overall_ap:.3f}')
ax.axhline(y=drift_threshold_ap, color='red', linestyle='--', linewidth=1.5, 
           label=f'Drift Threshold: {drift_threshold_ap:.3f}')
ax.set_xlabel('Week', fontsize=11)
ax.set_ylabel('Average Precision', fontsize=11)
ax.set_title('Average Precision Over Time', fontsize=12, fontweight='bold')
ax.legend(fontsize=10)
ax.grid(alpha=0.3)

ax = axes[1, 0]
ax.plot(weekly_df['week'], weekly_df['precision'], marker='o', linewidth=2, 
        markersize=6, label='Precision', color='blue')
ax.plot(weekly_df['week'], weekly_df['recall'], marker='s', linewidth=2, 
        markersize=6, label='Recall', color='orange')
ax.set_xlabel('Week', fontsize=11)
ax.set_ylabel('Rate', fontsize=11)
ax.set_title('Precision and Recall Over Time (Threshold=0.5)', fontsize=12, fontweight='bold')
ax.legend(fontsize=10)
ax.grid(alpha=0.3)

ax = axes[1, 1]
ax.plot(weekly_df['week'], weekly_df['avg_fraud_score'], marker='o', linewidth=2, 
        markersize=6, label='Fraud Transactions', color='red')
ax.plot(weekly_df['week'], weekly_df['avg_legit_score'], marker='s', linewidth=2, 
        markersize=6, label='Legitimate Transactions', color='green')
ax.set_xlabel('Week', fontsize=11)
ax.set_ylabel('Average Fraud Score', fontsize=11)
ax.set_title('Average Fraud Scores by Class Over Time', fontsize=12, fontweight='bold')
ax.legend(fontsize=10)
ax.grid(alpha=0.3)

plt.tight_layout()
plt.savefig('outputs/temporal_stability_plots.png', dpi=300, bbox_inches='tight')
print("Temporal stability plots saved to outputs/temporal_stability_plots.png")
```

Execute this temporal stability analysis. Performance degradation manifests as declining AUC-ROC or Average Precision in later time windows, indicating that the model's learned patterns no longer generalize to current fraud behavior. The drift detection mechanism flags weeks where performance falls below two standard deviations from the mean, triggering alerts for model retraining or feature engineering review. The average fraud score trends reveal whether fraudulent transactions are becoming more difficult to distinguish from legitimate ones (converging average scores) or whether the separation is maintained.

Now implement an adversarial robustness test that simulates fraudsters adapting to evade detection. Adversarial attacks in fraud detection typically involve manipulating transaction features to reduce fraud scores while maintaining fraudulent intent. Attackers cannot control all features (timestamp, customer history) but can strategically select transaction amounts, merchant categories, and timing to minimize detection probability. The robustness test applies small perturbations to fraudulent transactions and measures the resulting change in fraud scores, identifying vulnerable features that adversaries could exploit.

Create the adversarial robustness analysis script as `outputs/adversarial_robustness.py`:

```python
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import pickle
from sklearn.metrics import roc_auc_score

df = pd.read_csv('data/transactions_features.csv')
df['timestamp'] = pd.to_datetime(df['timestamp'])
df = df.sort_values('timestamp').reset_index(drop=True)

split_date = df['timestamp'].quantile(0.8)
test_df = df[df['timestamp'] >= split_date].copy()

fraud_df = test_df[test_df['is_fraud'] == 1].copy()

feature_cols = [
    'amount', 'hour', 'day_of_week', 'is_weekend', 'is_night',
    'customer_avg_amount', 'customer_std_amount', 'customer_txn_count',
    'customer_card_present_rate', 'amount_vs_avg', 'amount_vs_median',
    'log_time_since_last', 'velocity_3600s', 'velocity_86400s', 'velocity_604800s',
    'country_risk_score', 'category_risk_score', 'merchant_category_encoded',
    'country_encoded', 'card_present'
]

X_fraud = fraud_df[feature_cols].fillna(0)

with open('models/xgboost_model.pkl', 'rb') as f:
    model = pickle.load(f)

baseline_scores = model.predict_proba(X_fraud)[:, 1]

print("=== Adversarial Robustness Analysis ===")
print(f"Baseline fraud scores: mean={baseline_scores.mean():.4f}, std={baseline_scores.std():.4f}")

manipulable_features = ['amount', 'hour', 'is_weekend', 'is_night']

perturbation_results = []

for feature in manipulable_features:
    X_perturbed = X_fraud.copy()
    
    if feature == 'amount':
        X_perturbed[feature] = X_fraud[feature] * 0.7
        X_perturbed['amount_vs_avg'] = (X_perturbed['amount'] - X_fraud['customer_avg_amount']) / (
            X_fraud['customer_std_amount'] + 1e-5)
        X_perturbed['amount_vs_median'] = X_perturbed['amount'] / (X_fraud['customer_median_amount'] + 1e-5)
        perturbation_desc = "Reduce amount by 30%"
    
    elif feature == 'hour':
        X_perturbed[feature] = 14
        X_perturbed['is_night'] = 0
        perturbation_desc = "Shift to afternoon (hour=14)"
    
    elif feature == 'is_weekend':
        X_perturbed[feature] = 0
        perturbation_desc = "Change to weekday"
    
    elif feature == 'is_night':
        X_perturbed[feature] = 0
        X_perturbed['hour'] = 14
        perturbation_desc = "Change to daytime"
    
    perturbed_scores = model.predict_proba(X_perturbed)[:, 1]
    
    score_change = perturbed_scores - baseline_scores
    mean_change = score_change.mean()
    evasion_rate = (perturbed_scores < 0.5).sum() / len(perturbed_scores)
    
    perturbation_results.append({
        'feature': feature,
        'perturbation': perturbation_desc,
        'mean_score_change': mean_change,
        'evasion_rate': evasion_rate,
        'baseline_detection_rate': (baseline_scores >= 0.5).mean(),
        'perturbed_detection_rate': (perturbed_scores >= 0.5).mean()
    })
    
    print(f"\n--- Feature: {feature} ---")
    print(f"Perturbation: {perturbation_desc}")
    print(f"Mean score change: {mean_change:.4f}")
    print(f"Baseline detection rate: {(baseline_scores >= 0.5).mean():.4f}")
    print(f"Perturbed detection rate: {(perturbed_scores >= 0.5).mean():.4f}")
    print(f"Evasion rate: {evasion_rate:.4f}")

results_df = pd.DataFrame(perturbation_results)
results_df.to_csv('outputs/adversarial_robustness.csv', index=False)
print("\nAdversarial robustness analysis saved to outputs/adversarial_robustness.csv")

most_vulnerable = results_df.loc[results_df['mean_score_change'].idxmin()]

print(f"\n=== Most Vulnerable Feature ===")
print(f"Feature: {most_vulnerable['feature']}")
print(f"Perturbation: {most_vulnerable['perturbation']}")
print(f"Score reduction: {-most_vulnerable['mean_score_change']:.4f}")
print(f"Detection rate drop: {most_vulnerable['baseline_detection_rate'] - most_vulnerable['perturbed_detection_rate']:.4f}")

fig, axes = plt.subplots(1, 2, figsize=(14, 5))

ax = axes[0]
colors = ['red' if x < 0 else 'green' for x in results_df['mean_score_change']]
ax.barh(results_df['feature'], results_df['mean_score_change'], color=colors, alpha=0.7)
ax.set_xlabel('Mean Fraud Score Change', fontsize=11)
ax.set_title('Adversarial Score Changes by Feature Perturbation', fontsize=12, fontweight='bold')
ax.axvline(x=0, color='black', linestyle='-', linewidth=0.8)
ax.grid(axis='x', alpha=0.3)

ax = axes[1]
x = np.arange(len(results_df))
width = 0.35
ax.bar(x - width/2, results_df['baseline_detection_rate'], width, label='Baseline', color='blue', alpha=0.7)
ax.bar(x + width/2, results_df['perturbed_detection_rate'], width, label='Perturbed', color='orange', alpha=0.7)
ax.set_xlabel('Feature Perturbation', fontsize=11)
ax.set_ylabel('Detection Rate (Threshold=0.5)', fontsize=11)
ax.set_title('Detection Rate: Baseline vs. Perturbed', fontsize=12, fontweight='bold')
ax.set_xticks(x)
ax.set_xticklabels(results_df['feature'], rotation=45, ha='right')
ax.legend(fontsize=10)
ax.grid(axis='y', alpha=0.3)

plt.tight_layout()
plt.savefig('outputs/adversarial_robustness_plots.png', dpi=300, bbox_inches='tight')
print("Adversarial robustness plots saved to outputs/adversarial_robustness_plots.png")
```

Execute this adversarial robustness analysis. Features that exhibit large negative score changes under small perturbations represent vulnerabilities that sophisticated fraudsters could exploit. Amount manipulation typically reduces fraud scores most significantly because fraudsters can strategically choose transaction values closer to customer norms. The evasion rate quantifies the percentage of fraudulent transactions that would evade detection (score below threshold) after perturbation. Production fraud detection systems must incorporate robustness constraints during training, such as adversarial training that augments the dataset with perturbed examples, or architectural modifications like gradient masking that reduce the sensitivity of fraud scores to small input changes.

## Operational Reference Guide & Diagnostic Checklist

The operational deployment of fraud detection systems requires continuous monitoring, periodic retraining, and integration with downstream decisioning logic that determines transaction outcomes. The practitioner must establish production pipelines that score transactions in real-time (sub-100ms latency requirements), maintain model performance through data drift, and provide audit trails for regulatory compliance. This reference guide consolidates the operational procedures, diagnostic checks, and remediation protocols necessary for production fraud detection systems.

**Model Retraining Schedule:** Establish a cadence for model retraining that balances performance maintenance with operational overhead. Weekly retraining on rolling 90-day windows captures recent fraud pattern evolution while maintaining sufficient historical data for stable learning. More frequent retraining (daily) proves necessary during periods of rapid fraud scheme emergence or seasonal spending pattern shifts. Implement automated retraining pipelines that trigger on performance degradation alerts from temporal stability monitoring rather than fixed schedules alone.

**Feature Engineering Updates:** Monitor feature importance rankings and correlation structures to identify staleness. If a historically important feature's contribution declines precipitously, investigate whether fraud patterns have shifted or whether data quality issues have degraded feature informativeness. Add new features to capture emerging fraud patterns: for example, if account takeover fraud increases, engineer device fingerprinting features and IP geolocation consistency checks. Remove deprecated features that no longer provide signal to reduce model complexity and computational overhead.

**Threshold Calibration:** Revisit classification thresholds quarterly or when cost parameters change. Fraud rates, transaction volumes, and operational costs exhibit seasonal variation that shifts the economic optimum. Recalibrate thresholds using the cost-benefit framework with updated cost parameters reflecting current manual review efficiency, customer friction impacts, and fraud loss recovery rates. Implement dynamic thresholding that adjusts based on real-time risk indicators: higher thresholds during low-fraud periods to reduce false positives, lower thresholds during high-risk periods (holiday shopping, data breach announcements affecting the institution).

**Data Quality Monitoring:** Implement upstream validation checks on transaction data before scoring. Missing values in critical features (amount, merchant category, timestamp) indicate data pipeline failures that would degrade predictions. Outliers in feature distributions may signal data corruption or genuine anomalies requiring investigation. Monitor feature distributions in production scoring versus training data distributions to detect schema changes or data pipeline bugs before they impact performance.

**Model Explainability for Compliance:** Regulatory frameworks (GDPR, Fair Credit Reporting Act, Equal Credit Opportunity Act) require explainability for automated decisions affecting consumers. Maintain audit logs that record for each declined transaction: the fraud score, the top five contributing features and their values, and the classification threshold applied. Implement local explanation techniques (SHAP values, LIME) that decompose individual predictions into feature contributions, enabling customer service representatives to communicate decline reasons to affected cardholders.

**False Positive Analysis and Mitigation:** Establish processes for analyzing false positive patterns. If specific customer segments (high-spending travelers, small business owners) experience disproportionate false positive rates, tune thresholds or engineer segment-specific models. Implement customer feedback loops where declined cardholders can verify transaction legitimacy, feeding this information into model retraining to reduce future false positives for similar cases.

**Fraud Taxonomy Tracking:** Maintain classification of confirmed fraud cases by fraud type (card-not-present, account takeover, synthetic identity, friendly fraud). Track model performance by fraud type to identify systematic weaknesses. If the model exhibits low recall on synthetic identity fraud, engineer features specific to that pattern (new account age, rapid credit line exhaustion) and potentially train separate specialist models for high-impact fraud types.

**Disaster Recovery and Fallback Protocols:** Define fallback decision logic for model scoring failures or latency violations. Simple rule-based systems (decline all transactions above amount thresholds in high-risk merchant categories) provide graceful degradation when machine learning infrastructure fails. Maintain secondary models trained on reduced feature sets that can operate with degraded data availability. Establish monitoring that alerts on scoring latency violations or prediction service errors before they impact customer experience.

**A/B Testing for Model Improvements:** Deploy model updates through controlled A/B tests that measure impact on both fraud capture rates and false positive volumes before full rollout. Randomly assign transaction flows to champion (current production model) versus challenger (proposed update) and compare economic metrics over evaluation periods. This testing framework prevents regressions and quantifies the value of model improvements in production conditions rather than relying solely on offline validation metrics.

**Integration with Authentication Systems:** Coordinate fraud detection with step-up authentication that challenges high-risk transactions with additional verification (one-time passwords, biometric confirmation) rather than outright decline. This reduces false positive friction by allowing legitimate high-risk transactions to complete with additional authentication burden rather than blocking them entirely. Define risk score thresholds for automatic approval, step-up authentication, and automatic decline that optimize the tradeoff between fraud losses, authentication costs, and customer experience.

The practitioner now possesses a complete operational framework for designing, deploying, and maintaining production fraud detection systems that translate statistical predictions into economically optimal business decisions. The integration of machine learning classification with cost-benefit analysis, temporal stability monitoring, and adversarial robustness testing equips financial institutions to combat fraud effectively while minimizing the operational costs and customer friction that would otherwise erode the economic value of fraud prevention.
