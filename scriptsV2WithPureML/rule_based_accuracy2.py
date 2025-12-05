#!/usr/bin/env python3
import pandas as pd
from pathlib import Path

# ---------------------------
# Paths
# ---------------------------
RULE_OUTPUT = "../data/processed/yelp_conflated_middle.csv"  # output from your rule-based script
GOLDEN_TRUTH = "../data/processed/RULE_GOLDEN_DATASET_TEMPLATE.csv"  # labeled ground truth

# ---------------------------
# Load datasets
# ---------------------------
rule_df = pd.read_csv(RULE_OUTPUT)
gold_df = pd.read_csv(GOLDEN_TRUTH)

# Merge on place_id
df = rule_df.merge(gold_df, on="place_id", suffixes=("_pred", "_true"))

# ---------------------------
# Evaluation metrics
# ---------------------------
def accuracy(pred_col, true_col):
    """Simple accuracy: proportion of exact matches"""
    matches = df[pred_col] == df[true_col]
    return matches.mean()

# Name accuracy
name_acc = accuracy("best_name", "best_name_true")

# Address accuracy
address_acc = accuracy("best_address", "best_address_true")

# Optional: coordinate deviation (median distance in meters)
import numpy as np

def haversine(lat1, lon1, lat2, lon2):
    """Distance in meters between two lat/lon points"""
    R = 6371000  # radius of Earth in meters
    phi1 = np.radians(lat1)
    phi2 = np.radians(lat2)
    dphi = np.radians(lat2 - lat1)
    dlambda = np.radians(lon2 - lon1)
    a = np.sin(dphi/2.0)**2 + np.cos(phi1) * np.cos(phi2) * np.sin(dlambda/2.0)**2
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1-a))
    return R * c

df["coord_error_m"] = haversine(df["latitude_median"], df["longitude_median"],
                                df["latitude_true"], df["longitude_true"])
median_coord_error = df["coord_error_m"].median()

# ---------------------------
# Print results
# ---------------------------
print("Rule-based evaluation results:")
print(f"Name accuracy: {name_acc:.2%}")
print(f"Address accuracy: {address_acc:.2%}")
print(f"Median coordinate error: {median_coord_error:.1f} meters")

