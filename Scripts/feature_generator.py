#!/usr/bin/env python3
"""
feature_generator.py
Generates training and inference feature CSVs for an attribute (name, address, phone...).
Outputs:
  ../data/processed/ML_TRAIN_FEATURES_<attr>.csv
  ../data/processed/ML_INFER_FEATURES_<attr>.csv

Currently implements 'name' features. Extend for other attributes similarly.
"""
import pandas as pd
import numpy as np
from rapidfuzz import fuzz
from pathlib import Path

TRIPLET = "../data/processed/yelp_triplet_matches.csv"
GROUND_TRUTH = "../data/processed/yelp_ground_truth.csv"
OUT_DIR = Path("../data/processed")
OUT_DIR.mkdir(parents=True, exist_ok=True)

def safe_fuzz(a, b):
    if pd.isna(a) or pd.isna(b):
        return 0
    return fuzz.token_set_ratio(str(a), str(b))

def category_overlap(a, b):
    # inputs: comma-separated strings or lists
    if pd.isna(a) or pd.isna(b):
        return 0
    try:
        sa = set([x.strip() for x in str(a).split(",") if x.strip()])
        sb = set([x.strip() for x in str(b).split(",") if x.strip()])
        if not sa or not sb:
            return 0
        return len(sa & sb) / max(1, len(sa | sb))
    except Exception:
        return 0

print("Loading data...")
trip = pd.read_csv(TRIPLET, dtype=str)
gt = pd.read_csv(GROUND_TRUTH, dtype=str)

# merge ground truth so each candidate row has name_true/address_true
df = trip.merge(gt, on="place_id", how="left", suffixes=("", "_gt"))

# compute candidate fields (normalize column names you have)
# Our triplet likely has: name (Yelp), omf_name, overpass_name, omf_score, overpass_score, omf_distance, overpass_distance
# Fill NaNs for safe numeric operations
df['omf_score'] = pd.to_numeric(df.get('omf_score'), errors='coerce').fillna(0)
df['overpass_score'] = pd.to_numeric(df.get('overpass_score'), errors='coerce').fillna(0)
df['omf_distance'] = pd.to_numeric(df.get('omf_distance'), errors='coerce').fillna(99999)
df['overpass_distance'] = pd.to_numeric(df.get('overpass_distance'), errors='coerce').fillna(99999)

# FEATURE ENGINEERING for name attribute
print("Computing features for name...")
df['yelp_name_sim_to_true'] = df.apply(lambda r: safe_fuzz(r.get('name'), r.get('name_true')), axis=1)
df['omf_name_sim_to_true'] = df.apply(lambda r: safe_fuzz(r.get('omf_name'), r.get('name_true')), axis=1)
df['overpass_name_sim_to_true'] = df.apply(lambda r: safe_fuzz(r.get('overpass_name'), r.get('name_true')), axis=1)

# Candidate presence flags
df['has_omf'] = df['omf_name'].notna().astype(int)
df['has_overpass'] = df['overpass_name'].notna().astype(int)

# Category overlap between Yelp and OMF/Overpass
df['cat_overlap_omf'] = df.apply(lambda r: category_overlap(r.get('categories'), r.get('category') or r.get('omf_category')), axis=1)
df['cat_overlap_overpass'] = df.apply(lambda r: category_overlap(r.get('categories'), r.get('category_right') or r.get('overpass_category')), axis=1)

# Compose feature set
feature_cols = [
    'omf_score', 'overpass_score',
    'omf_distance', 'overpass_distance',
    'yelp_name_sim_to_true','omf_name_sim_to_true','overpass_name_sim_to_true',
    'has_omf','has_overpass',
    'cat_overlap_omf','cat_overlap_overpass'
]

features = df[['place_id','business_id'] + feature_cols + ['omf_name','overpass_name','name','name_true']].copy()

# LABEL creation for training: 0=Yelp,1=OMF,2=Overpass (we only label rows that match truth exactly)
def label_name_row(r):
    if pd.notna(r['name_true']) and r.get('name') == r['name_true']:
        return 0
    if pd.notna(r['name_true']) and pd.notna(r['omf_name']) and r.get('omf_name') == r['name_true']:
        return 1
    if pd.notna(r['name_true']) and pd.notna(r['overpass_name']) and r.get('overpass_name') == r['name_true']:
        return 2
    return np.nan  # unknown / no exact match

features['label'] = features.apply(label_name_row, axis=1)

# TRAIN FEATURES: rows with label not null
train_df = features[features['label'].notna()].copy()
train_out = OUT_DIR / "ML_TRAIN_FEATURES_name.csv"
train_df.to_csv(train_out, index=False)
print(f"Saved train features: {train_out} ({len(train_df):,} rows)")

# INFER FEATURES: all rows (we keep label if present)
infer_out = OUT_DIR / "ML_INFER_FEATURES_name.csv"
features.to_csv(infer_out, index=False)
print(f"Saved infer features: {infer_out} ({len(features):,} rows)")

print("Feature generation complete.")

