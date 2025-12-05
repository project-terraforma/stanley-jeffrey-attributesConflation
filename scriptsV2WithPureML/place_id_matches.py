#!/usr/bin/env python3
import pandas as pd
import geopandas as gpd
from pathlib import Path

# Paths
YELP_OMF_FILE = "../data/interim/yelp_omf_matched.geojson"
YELP_OVERPASS_FILE = "../data/interim/yelp_overpass_matched.geojson"
OUT_FILE = "../data/processed/yelp_triplet_matches.csv"

# Ensure output folder exists
Path("../data/processed").mkdir(exist_ok=True)

# --------------------------------------------------------------
# Load matched datasets
# --------------------------------------------------------------
yelp_omf = gpd.read_file(YELP_OMF_FILE)
yelp_overpass = gpd.read_file(YELP_OVERPASS_FILE)

print("Loaded Yelp→OMF columns:", yelp_omf.columns)
print("Loaded Yelp→Overpass columns:", yelp_overpass.columns)

# --------------------------------------------------------------
# Select + rename columns for OMF matches
# --------------------------------------------------------------
yelp_omf = yelp_omf[[
    "business_id",
    "name_left",
    "address_left",
    "latitude",
    "longitude",
    "matched_id",
    "matched_name",
    "matched_name_score",
    "distance_m_final",
    "categories",
    "category"
]].rename(columns={
    "name_left": "name",
    "address_left": "address",
    "matched_id": "omf_id",
    "matched_name": "omf_name",
    "matched_name_score": "omf_score",
    "distance_m_final": "omf_distance",
    "categories": "category",
    "category": "omf_category"
})

# --------------------------------------------------------------
# Select + rename columns for Overpass matches
# --------------------------------------------------------------
yelp_overpass = yelp_overpass[[
    "business_id",
    "matched_id",
    "matched_name",
    "matched_name_score",
    "distance_m_final",
    "category"
]].rename(columns={
    "matched_id": "overpass_id",
    "matched_name": "overpass_name",
    "matched_name_score": "overpass_score",
    "distance_m_final": "overpass_distance",
    "category": "overpass_category"
})

# --------------------------------------------------------------
# Merge OMF + Overpass into triplets (KEEP ALL YELP ROWS)
# --------------------------------------------------------------
triplet_df = pd.merge(yelp_omf, yelp_overpass, on="business_id", how="outer")

# --------------------------------------------------------------
# DO NOT REMOVE YELP-ONLY ROWS (critical)
# --------------------------------------------------------------
# triplet_df = triplet_df[...]  <-- REMOVED

# --------------------------------------------------------------
# Assign unified place_id
# --------------------------------------------------------------
def assign_place_id(row):
    if pd.notnull(row["omf_id"]):
        return f"P_{row['omf_id']}"
    elif pd.notnull(row["overpass_id"]):
        return f"P_{row['overpass_id']}"
    else:
        return f"P_{row['business_id']}"

triplet_df["place_id"] = triplet_df.apply(assign_place_id, axis=1)

# --------------------------------------------------------------
# Reorder columns
# --------------------------------------------------------------
triplet_df = triplet_df[[
    "place_id", "business_id",
    "name", "address", "category", "latitude", "longitude",
    "omf_id", "omf_name", "omf_category", "omf_score", "omf_distance",
    "overpass_id", "overpass_name", "overpass_category", "overpass_score", "overpass_distance"
]]

# --------------------------------------------------------------
# Save
# --------------------------------------------------------------
triplet_df.to_csv(OUT_FILE, index=False)
print(f"\nTriplet table saved: {OUT_FILE}")
print(f"Total rows: {len(triplet_df):,}")
print("Finished!")

