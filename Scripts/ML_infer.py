#!/usr/bin/env python3
"""
ml_infer.py
Load inference features and a trained model, predict best source,
and output ML_BEST_ATTRIBUTES.csv (per place_id predictions).
"""
import pandas as pd
import joblib
from pathlib import Path
import numpy as np

INFER_FILE = "../data/processed/ML_INFER_FEATURES_name.csv"
MODEL_FILE = "../models/random_forest_name.pkl"
OUT = "../data/processed/ML_BEST_ATTRIBUTES.csv"

print("Loading inference features...")
df = pd.read_csv(INFER_FILE)
model = joblib.load(MODEL_FILE)
print("Model loaded.")

feature_cols = [c for c in df.columns if c not in ['place_id','business_id','omf_name','overpass_name','name','name_true','label']]
X = df[feature_cols].fillna(0).values

print("Predicting...")
pred = model.predict(X)
df['best_source_pred'] = pred  # 0=Yelp,1=OMF,2=Overpass

def pick_name(row):
    if row['best_source_pred'] == 0:
        return row.get('name')
    elif row['best_source_pred'] == 1:
        return row.get('omf_name')
    elif row['best_source_pred'] == 2:
        return row.get('overpass_name')
    return row.get('name')

df['best_name_pred'] = df.apply(pick_name, axis=1)

out = df[['place_id','best_name_pred']].drop_duplicates('place_id').copy()

out.to_csv(OUT, index=False)
print(f"Saved best attributes to {OUT} ({len(out):,} places)")

