#!/usr/bin/env python3
"""
ml_train.py
Train a model for the name attribute and save it.
Outputs:
 - models/random_forest_name.pkl
 - ../data/processed/ML_BEST_ATTRIBUTES.csv   (feature importances)
"""
import pandas as pd
from pathlib import Path
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import classification_report, accuracy_score
import joblib
import numpy as np

TRAIN_FILE = "../data/processed/ML_TRAIN_FEATURES_name.csv"
MODEL_DIR = Path("../models")
MODEL_DIR.mkdir(parents=True, exist_ok=True)
MODEL_OUT = MODEL_DIR / "random_forest_name.pkl"
OUT_IMP = "../data/processed/ML_BEST_ATTRIBUTES.csv"

print("Loading training features...")
df = pd.read_csv(TRAIN_FILE)

df = df[df['label'].notna()].copy()
y = df['label'].astype(int)
feature_cols = [c for c in df.columns if c not in ['place_id','business_id','omf_name','overpass_name','name','name_true','label']]

X = df[feature_cols].fillna(0).values

print("Splitting train/test...")
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

print("Training RandomForest...")
model = RandomForestClassifier(n_estimators=300, random_state=42, class_weight='balanced', n_jobs=-1)
model.fit(X_train, y_train)

print("Testing...")
y_pred = model.predict(X_test)
print("Accuracy:", accuracy_score(y_test, y_pred))
print(classification_report(y_test, y_pred, digits=4))

importances = model.feature_importances_
fi = pd.DataFrame({
    "feature": feature_cols,
    "importance": importances
}).sort_values("importance", ascending=False)

fi.to_csv(OUT_IMP, index=False)
print(f"Saved feature importances to {OUT_IMP}")

joblib.dump(model, MODEL_OUT)
print(f"Saved model to {MODEL_OUT}")

