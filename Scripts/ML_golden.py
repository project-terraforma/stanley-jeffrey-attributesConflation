#!/usr/bin/env python3
"""
ml_golden.py
Create a golden dataset (one row per place_id) using Yelp as ground-truth.
Output: ../data/processed/ML_GOLDEN_DATASET_TEMPLATE.csv
"""
import pandas as pd
from pathlib import Path

TRIPLET = "../data/processed/yelp_triplet_matches.csv"
GROUND_TRUTH = "../data/processed/yelp_ground_truth.csv"
OUT = "../data/processed/ML_GOLDEN_DATASET_TEMPLATE.csv"

Path("../data/processed").mkdir(exist_ok=True)

print("Loading triplet and ground truth...")
trip = pd.read_csv(TRIPLET, dtype=str)
gt = pd.read_csv(GROUND_TRUTH, dtype=str)

gold = gt.drop_duplicates(subset=["place_id"]).copy()

counts = trip.groupby("place_id").size().reset_index(name="n_candidates")
gold = gold.merge(counts, on="place_id", how="left")

gold.to_csv(OUT, index=False)
print(f"Golden dataset saved to {OUT} ({len(gold):,} place_ids)")

