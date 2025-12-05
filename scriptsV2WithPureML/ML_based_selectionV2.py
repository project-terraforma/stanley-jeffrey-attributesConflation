#!/usr/bin/env python3
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, accuracy_score

# Paths
TRAIN_FEATURES_FILE = "../data/processed/ML_TRAIN_FEATURES_name.csv"
OUT_FILE = "../data/processed/ml_predictions_v2.csv"

# --------------------------------------------------------------
# Load data
# --------------------------------------------------------------
print("Loading data...")
df = pd.read_csv(TRAIN_FEATURES_FILE)

# Print label counts
print("\nLabel counts before balancing:")
print(df['label'].value_counts())

# --------------------------------------------------------------
# Upsample smaller classes for perfect balance
# --------------------------------------------------------------
min_count = df['label'].value_counts().min()
print(f"\nDownsampling / Upsampling all classes to {min_count} rows for balance...")

balanced_df = pd.concat([
    df[df['label'] == lbl].sample(n=min_count, replace=True, random_state=42)
    for lbl in df['label'].unique()
])

print("\nLabel counts after balancing:")
print(balanced_df['label'].value_counts())

# --------------------------------------------------------------
# Split features / target
# --------------------------------------------------------------
feature_cols = [c for c in balanced_df.columns if c != 'label']

# Keep only numeric columns
X = balanced_df[feature_cols].select_dtypes(include=np.number)
y = balanced_df['label']

# --------------------------------------------------------------
# Train RandomForest
# --------------------------------------------------------------
clf = RandomForestClassifier(
    n_estimators=200,
    max_depth=None,
    random_state=42,
    n_jobs=-1
)

clf.fit(X, y)

# --------------------------------------------------------------
# Predict on training set (for inspection)
# --------------------------------------------------------------
y_pred = clf.predict(X)

acc = accuracy_score(y, y_pred)
print(f"\n=========================================")
print("   ML ATTRIBUTE SELECTION (NAME+ADDR+CAT+COORD)")
print("=========================================")
print(f"Accuracy: {acc*100:.2f}%\n")
print("Classification Report:")
print(classification_report(y, y_pred))

# --------------------------------------------------------------
# Feature importances
# --------------------------------------------------------------
importances = pd.Series(clf.feature_importances_, index=X.columns).sort_values(ascending=False)
print("\nFeature Importance:")
print(importances)

# --------------------------------------------------------------
# Save predictions
# --------------------------------------------------------------
balanced_df['pred_label'] = y_pred
balanced_df.to_csv(OUT_FILE, index=False)
print(f"\nML predictions saved to {OUT_FILE}")

