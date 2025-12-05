#!/usr/bin/env python3
import pandas as pd
import numpy as np
from pathlib import Path
from rapidfuzz import fuzz

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report

TRIPLET_FILE = "../data/processed/yelp_triplet_matches.csv"
GROUND_TRUTH_FILE = "../data/processed/yelp_ground_truth.csv"
OUTPUT_FILE = "../data/processed/ml_predictions.csv"

Path("../data/processed").mkdir(exist_ok=True)

df = pd.read_csv(TRIPLET_FILE)
gt = pd.read_csv(GROUND_TRUTH_FILE)

df = df.merge(gt, on="place_id", how="left")


def safe_fuzz(a, b):
    if pd.isna(a) or pd.isna(b): 
        return 0
    return fuzz.token_set_ratio(str(a), str(b))

df['yelp_sim'] = df.apply(lambda r: safe_fuzz(r['name'], r['name_true']), axis=1)
df['omf_sim'] = df.apply(lambda r: safe_fuzz(r['omf_name'], r['name_true']), axis=1)
df['overpass_sim'] = df.apply(lambda r: safe_fuzz(r['overpass_name'], r['name_true']), axis=1)

df = df.fillna({
    'omf_score': 0,
    'overpass_score': 0,
    'omf_distance': 9999,
    'overpass_distance': 9999,
    'omf_sim': 0,
    'overpass_sim': 0,
    'yelp_sim': 0
})

def label_row(row):
    if row['name'] == row['name_true']:
        return 0  # Yelp
    if row['omf_name'] == row['name_true']:
        return 1  # OMF
    if row['overpass_name'] == row['name_true']:
        return 2  # Overpass
    return 0  # default to Yelp if no exact match

df['label'] = df.apply(label_row, axis=1)

feature_cols = [
    'omf_score', 'overpass_score',
    'omf_distance', 'overpass_distance',
    'yelp_sim', 'omf_sim', 'overpass_sim'
]

X = df[feature_cols]
y = df['label']

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

model = RandomForestClassifier(
    n_estimators=200,
    random_state=42,
    class_weight="balanced"
)
model.fit(X_train, y_train)

y_pred = model.predict(X_test)

print("=========================================")
print("   MACHINE LEARNING ATTRIBUTE SELECTION")
print("=========================================")
print(f"Accuracy: {accuracy_score(y_test, y_pred)*100:.2f}%")
print("\nClassification Report:")
print(classification_report(y_test, y_pred, target_names=['Yelp','OMF','Overpass']))

print("Feature Importance:")
for name, importance in sorted(
        zip(feature_cols, model.feature_importances_),
        key=lambda x: x[1],
        reverse=True):
    print(f"{name}: {importance:.4f}")

df['best_source_pred'] = model.predict(df[feature_cols])

def pick_name(row):
    if row['best_source_pred'] == 0:
        return row['name']
    elif row['best_source_pred'] == 1:
        return row['omf_name']
    else:
        return row['overpass_name']

df['best_name_pred'] = df.apply(pick_name, axis=1)

final = df[['place_id', 'best_name_pred']].drop_duplicates('place_id')

final.to_csv(OUTPUT_FILE, index=False)
print(f"\nML predictions saved to {OUTPUT_FILE}")


