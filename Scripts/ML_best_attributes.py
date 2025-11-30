#!/usr/bin/env python3
"""
ml_best_attributes.py
Read ML_BEST_ATTRIBUTES.csv and output the top-K selected features.
"""
import pandas as pd
from pathlib import Path

IMP_FILE = "../data/processed/ML_BEST_ATTRIBUTES.csv"
OUT = "../data/processed/ML_BEST_ATTRIBUTES_TOPK.csv"
K = 8

df = pd.read_csv(IMP_FILE)
topk = df.sort_values("importance", ascending=False).head(K)
topk.to_csv(OUT, index=False)
print(f"Top {K} features written to {OUT}")

