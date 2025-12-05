#!/usr/bin/env python3
"""
ml_eval.py
Evaluate ML output (ML_BEST_ATTRIBUTES.csv) against ground truth (yelp_ground_truth.csv)
Outputs accuracy and classification metrics.
"""
import pandas as pd
from sklearn.metrics import accuracy_score, classification_report
from pathlib import Path
import numpy as np

GT = "../data/processed/yelp_ground_truth.csv"
PRED = "../data/processed/ML_BEST_ATTRIBUTES.csv"

gt = pd.read_csv(GT, dtype=str)
pred = pd.read_csv(PRED, dtype=str)

cmp = gt.merge(pred, on="place_id", how="left")
cmp['best_name_pred'] = cmp['best_name_pred'].fillna("")

cmp['name_match'] = (cmp['best_name_pred'] == cmp['name_true'])
acc = cmp['name_match'].mean()
print(f"Name exact-match accuracy: {acc*100:.2f}%")

def label_from_pred(row):
    if row['best_name_pred'] == row['name_true']:
        return 1
    return 0

cmp['correct_label'] = cmp.apply(label_from_pred, axis=1)
print(f"Correct predictions: {cmp['correct_label'].sum():,} / {len(cmp):,}")

