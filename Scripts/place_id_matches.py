#!/usr/bin/env python3
import pandas as pd
import geopandas as gpd
from pathlib import Path

# Paths to matched datasets
YELP_OMF_FILE = "../data/interim/yelp_omf_matched.geojson"
YELP_OVERPASS_FILE = "../data/interim/yelp_overpass_matched.geojson"
OUT_FILE = "../data/processed/yelp_triplet_matches_with_gaps.csv"

Path("../data/processed").mkdir(exist_ok=True)

# Load matched data
yelp_omf = gpd.read_file(YELP_OMF_FILE)
yelp_overpass = gpd.read_file(YELP_OVERPASS_FILE)

# Inspect columns to know which ones to pick
print("Yelp->OMF columns:", yelp_omf.columns)
print("Yelp->Overpass columns:", yelp_overpass.columns)

# Select relevant columns and rename for consistency
yelp_omf = yelp_omf[[
    "business_id", "name_left", "address_left", "latitude", "longitude",
    "matched_id", "matched_name", "matched_name_score", "distance_m_final"
]].rename(columns={
    "name_left": "name",
    "address_left": "address",
    "matched_id": "omf_id",
    "matched_name": "omf_name",
    "matched_name_score": "omf_score",
    "distance_m_final": "omf_distance"
})

yelp_overpass = yelp_overpass[[
    "business_id", "matched_id", "matched_name", "matched_name_score", "distance_m_final"
]].rename(columns={
    "matched_id": "overpass_id",
    "matched_name": "overpass_name",
    "matched_name_score": "overpass_score",
    "distance_m_final": "overpass_distance"
})

# Merge Yelp->OMF and Yelp->Overpass on Yelp business_id
triplet_df = pd.merge(yelp_omf, yelp_overpass, on="business_id", how="outer")

# Optional: create a unified place_id (grouping by matched OMF or Overpass id)
def assign_place_id(row):
    if pd.notnull(row["omf_id"]):
        return f"P_{row['omf_id']}"
    elif pd.notnull(row["overpass_id"]):
        return f"P_{row['overpass_id']}"
    else:
        return f"P_{row['business_id']}"

triplet_df["place_id"] = triplet_df.apply(assign_place_id, axis=1)

# Reorder columns
triplet_df = triplet_df[[
    "place_id", "business_id", "name", "address", "latitude", "longitude",
    "omf_id", "omf_name", "omf_score", "omf_distance",
    "overpass_id", "overpass_name", "overpass_score", "overpass_distance"
]]

# --- NEW: Insert blank row between unique place_ids ---
triplet_df = triplet_df.sort_values("place_id").reset_index(drop=True)
rows_with_gaps = []
prev_place = None
for _, row in triplet_df.iterrows():
    current_place = row["place_id"]
    if prev_place is not None and current_place != prev_place:
        # Add empty row
        rows_with_gaps.append([None] * len(triplet_df.columns))
    rows_with_gaps.append(row.tolist())
    prev_place = current_place

triplet_df_with_gaps = pd.DataFrame(rows_with_gaps, columns=triplet_df.columns)

# Save to CSV
triplet_df_with_gaps.to_csv(OUT_FILE, index=False)
print(f"Triplet table with gaps saved to {OUT_FILE} ({len(triplet_df_with_gaps):,} rows)")

