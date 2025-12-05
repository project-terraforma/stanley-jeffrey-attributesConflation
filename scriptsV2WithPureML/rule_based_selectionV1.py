#!/usr/bin/env python3
import pandas as pd
from pathlib import Path
from rapidfuzz import fuzz

TRIPLET_FILE = "../data/processed/yelp_triplet_matches_with_gaps.csv"
OUTPUT_FILE = "../data/processed/yelp_conflated.csv"

Path("../data/processed").mkdir(exist_ok=True)

df = pd.read_csv(TRIPLET_FILE)

def pick_best_name(row):
    """
    Rule-based selection for 'name':
    1. Pick the attribute with the highest fuzzy match score (omf_score or overpass_score)
    2. Tie-break: prefer OMF > Overpass > Yelp
    3. Fallback: use Yelp name
    """
    scores = {
        'omf': row.get('omf_score', 0) if pd.notnull(row.get('omf_score')) else 0,
        'overpass': row.get('overpass_score', 0) if pd.notnull(row.get('overpass_score')) else 0
    }
    if scores['omf'] >= scores['overpass'] and pd.notnull(row.get('omf_name')):
        return row['omf_name']
    elif scores['overpass'] > scores['omf'] and pd.notnull(row.get('overpass_name')):
        return row['overpass_name']
    else:
        return row['name']  # fallback to Yelp

def pick_best_address(row):
    """
    Rule-based selection for 'address':
    1. Use OMF if available
    2. Otherwise, use Overpass
    3. Otherwise, fallback to Yelp
    """
    if pd.notnull(row.get('omf_id')) and pd.notnull(row.get('omf_name')):
        return row['address']
    elif pd.notnull(row.get('overpass_id')) and pd.notnull(row.get('overpass_name')):
        return row['address']
    else:
        return row['address']

df['best_name'] = df.apply(pick_best_name, axis=1)
df['best_address'] = df.apply(pick_best_address, axis=1)

median_coords = df.groupby('place_id')[['latitude','longitude']].median().reset_index()
df = df.merge(median_coords, on='place_id', suffixes=('','_median'))

conflated_df = df[['place_id', 'best_name', 'best_address', 'latitude_median', 'longitude_median']].drop_duplicates('place_id')

conflated_df.to_csv(OUTPUT_FILE, index=False)
print(f"Rule-based conflated dataset saved to {OUTPUT_FILE} ({len(conflated_df):,} rows)")



'''

#!/usr/bin/env python3
import pandas as pd
from pathlib import Path
from rapidfuzz import fuzz

# ---------------------------
# Paths
# ---------------------------
TRIPLET_FILE = "../data/processed/yelp_triplet_matches_with_gaps.csv"
OUTPUT_FILE = "../data/processed/yelp_conflated_middle.csv"

Path("../data/processed").mkdir(exist_ok=True)

# ---------------------------
# Load data
# ---------------------------
df = pd.read_csv(TRIPLET_FILE)

# ---------------------------
# Helper functions
# ---------------------------
def normalize_text(text):
    """Lowercase, strip, remove extra spaces."""
    if pd.isnull(text):
        return ""
    return " ".join(str(text).lower().strip().split())

# ---------------------------
# Name selection
# ---------------------------
def pick_best_name(row):
    """
    Picks best name based on fuzzy match scores and source priority.
    Rule:
      1. Use highest score (omf_score vs overpass_score)
      2. Tie-break: OMF > Overpass > Yelp
      3. Fallback: Yelp name
    """
    scores = {
        "omf": row.get("omf_score", 0) if pd.notnull(row.get("omf_score")) else 0,
        "overpass": row.get("overpass_score", 0) if pd.notnull(row.get("overpass_score")) else 0,
    }

    if scores["omf"] >= scores["overpass"] and pd.notnull(row.get("omf_name")):
        return normalize_text(row["omf_name"])
    elif scores["overpass"] > scores["omf"] and pd.notnull(row.get("overpass_name")):
        return normalize_text(row["overpass_name"])
    else:
        return normalize_text(row["name"])  # fallback to Yelp

# ---------------------------
# Address selection
# ---------------------------
def pick_best_address(row):
    """
    Picks best address based on source availability.
    Rule:
      1. Use OMF if available
      2. Else Overpass
      3. Else Yelp
    """
    if pd.notnull(row.get("omf_id")):
        return normalize_text(row.get("address", ""))
    elif pd.notnull(row.get("overpass_id")):
        return normalize_text(row.get("address", ""))
    else:
        return normalize_text(row.get("address", ""))

# ---------------------------
# Apply rules
# ---------------------------
df["best_name"] = df.apply(pick_best_name, axis=1)
df["best_address"] = df.apply(pick_best_address, axis=1)

# ---------------------------
# Consolidate coordinates
# ---------------------------
median_coords = df.groupby("place_id")[["latitude", "longitude"]].median().reset_index()
df = df.merge(median_coords, on="place_id", suffixes=("", "_median"))

# ---------------------------
# Final conflated dataset
# ---------------------------
conflated_df = df[["place_id", "best_name", "best_address", "latitude_median", "longitude_median"]].drop_duplicates("place_id")

conflated_df.to_csv(OUTPUT_FILE, index=False)
print(f"Middle-ground rule-based conflated dataset saved to {OUTPUT_FILE} ({len(conflated_df):,} rows)")
'''
