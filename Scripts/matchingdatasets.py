#!/usr/bin/env python3
"""
matchingdatasets_fast.py

Optimized matching pipeline:
- Chunked processing (default 5k Yelp rows / chunk)
- Spatial nearest join -> local bbox candidate selection -> RapidFuzz on local set
- Intermediate chunk saves to ../data/interim to be resumable
"""

import math
import os
from pathlib import Path
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
from unidecode import unidecode
from rapidfuzz import process, fuzz
from geopandas.tools import sjoin_nearest
import warnings
import time

warnings.filterwarnings('ignore', 'GeoSeries.notna', UserWarning)

# ----------------------------
# CONFIG
# ----------------------------
YELP_JSON = "../data/raw/yelp_academic_dataset_business.json"
OMF_GEOJSON = "../data/interim/omf_all_merged.geojson"
OVERPASS_GEOJSON = "../data/interim/overpass_all_merged.geojson"
OUT_DIR = Path("../data/interim")
OUT_DIR.mkdir(parents=True, exist_ok=True)

CHUNK_SIZE = 5000                # Yelp rows per chunk (tune: 2000-10000)
MAX_DISTANCE_METERS = 100        # spatial window for candidate selection
FUZZY_SCORE_THRESHOLD = 80       # keep fuzzy matches >= this
SAVE_EVERY_CHUNK = True

# Filenames for chunk results
OMF_CHUNK_PREFIX = OUT_DIR / "yelp_omf_chunk"
OVERPASS_CHUNK_PREFIX = OUT_DIR / "yelp_overpass_chunk"
FINAL_OMF_OUT = OUT_DIR / "yelp_omf_matched.geojson"
FINAL_OVERPASS_OUT = OUT_DIR / "yelp_overpass_matched.geojson"

# ----------------------------
# Helpers
# ----------------------------
def clean_text(x):
    if pd.isnull(x) or str(x).strip() == "":
        return None
    return unidecode(str(x).strip().lower())

def ensure_cols(gdf, required):
    for c in required:
        if c not in gdf.columns:
            gdf[c] = None
    return gdf

# ----------------------------
# Load & preprocess inputs
# ----------------------------
print("Loading Yelp (CSV/JSON) and target GeoJSONs...")

# Yelp: load JSON lines -> DataFrame -> clean -> GeoDataFrame
yelp_df = pd.read_json(YELP_JSON, lines=True)
yelp_df = yelp_df[[
    "business_id", "name", "address", "city", "state", "postal_code",
    "latitude", "longitude", "categories"
]]

# text clean
for col in ["name", "address", "city", "state"]:
    yelp_df[col] = yelp_df[col].apply(clean_text)

# drop rows without location or name
yelp_df = yelp_df.dropna(subset=["latitude", "longitude", "name"]).reset_index(drop=True)

yelp_gdf = gpd.GeoDataFrame(
    yelp_df,
    geometry=gpd.points_from_xy(yelp_df.longitude, yelp_df.latitude),
    crs="EPSG:4326"
)

# Targets
omf_gdf = gpd.read_file(OMF_GEOJSON)
overpass_gdf = gpd.read_file(OVERPASS_GEOJSON)

# Ensure standardized columns
omf_gdf = ensure_cols(omf_gdf, ["id", "name", "address", "geometry"])
overpass_gdf = ensure_cols(overpass_gdf, ["id", "name", "address", "geometry"])

# Drop rows with missing geometry or name in target sets
omf_gdf = omf_gdf.dropna(subset=["geometry"]).reset_index(drop=True)
overpass_gdf = overpass_gdf.dropna(subset=["geometry"]).reset_index(drop=True)

print(f"Yelp rows: {len(yelp_gdf):,}, OMF rows: {len(omf_gdf):,}, Overpass rows: {len(overpass_gdf):,}")

# Project everything to metric CRS once (EPSG:3857)
yelp_proj = yelp_gdf.to_crs(epsg=3857).copy()
omf_proj = omf_gdf.to_crs(epsg=3857).copy()
overpass_proj = overpass_gdf.to_crs(epsg=3857).copy()

# Build cleaned name columns for fuzzy matching
omf_proj["name_clean"] = omf_proj["name"].apply(clean_text)
overpass_proj["name_clean"] = overpass_proj["name"].apply(clean_text)
yelp_proj["name_clean"] = yelp_proj["name"].apply(clean_text)

# Build spatial indices for target sets
omf_index = omf_proj.sindex
overpass_index = overpass_proj.sindex

# ----------------------------
# Core matching logic per chunk
# ----------------------------
def process_chunk(yelp_chunk, target_proj, target_index, target_name_col="name_clean"):
    """
    yelp_chunk: GeoDataFrame in metric CRS (epsg:3857)
    target_proj: target GeoDataFrame in metric CRS
    target_index: spatial index of target_proj
    Returns matched_gdf (yelp_chunk with appended match info)
    """
    # 1) sjoin_nearest to get initial candidate index_right and distance (fast)
    joined = sjoin_nearest(
        yelp_chunk, target_proj,
        how="left",
        max_distance=MAX_DISTANCE_METERS,
        distance_col="distance_m"
    )
    # rename source/target name columns if present
    # after join, Yelp name is usually name_left; target name becomes name_right
    # to be safe, detect
    if "name_left" in joined.columns:
        source_name_col = "name_left"
    elif "name" in joined.columns:
        source_name_col = "name"
    else:
        source_name_col = "name_clean"

    # We'll produce these columns
    matched_candidate_ids = []
    matched_candidate_names = []
    matched_scores = []
    matched_distances = []

    # For each row, query spatial index via bounding box -> precise distance filter -> fuzzy match limited set
    for idx, row in joined.iterrows():
        src_geom = row.geometry
        src_name = row[source_name_col] if source_name_col in row else row.get("name_clean")
        matched_distances.append(row.get("distance_m", None))

        if pd.isnull(src_name) or src_geom is None:
            matched_candidate_ids.append(None)
            matched_candidate_names.append(None)
            matched_scores.append(None)
            continue

        # bbox query: buffer by max distance (meters)
        buf = src_geom.buffer(MAX_DISTANCE_METERS)
        minx, miny, maxx, maxy = buf.bounds

        # intersection with sindex -> candidate indices
        candidate_idx = list(target_index.intersection((minx, miny, maxx, maxy)))
        if not candidate_idx:
            matched_candidate_ids.append(None)
            matched_candidate_names.append(None)
            matched_scores.append(None)
            continue

        # subset and precise distance filter
        candidates = target_proj.iloc[candidate_idx].copy()
        # compute exact distance in meters and filter
        candidates["dist2src"] = candidates.geometry.distance(src_geom)
        candidates = candidates[candidates["dist2src"] <= MAX_DISTANCE_METERS]

        if candidates.empty:
            matched_candidate_ids.append(None)
            matched_candidate_names.append(None)
            matched_scores.append(None)
            continue

        # prepare small list of candidate names
        candidate_names = candidates[target_name_col].fillna("").tolist()
        # run RapidFuzz on small list
        res = process.extractOne(src_name, candidate_names, scorer=fuzz.WRatio)
        # res may be None or a tuple (match, score, idx) depending on library version
        match_str, score = (None, None)
        if res:
            # handle different return shapes
            if isinstance(res, tuple):
                # (match, score, idx) or (match, score)
                if len(res) >= 2:
                    match_str, score = res[0], res[1]
            else:
                # object with attributes
                try:
                    match_str = res.value
                    score = res.score
                except Exception:
                    match_str, score = None, None

        if score is not None and score >= FUZZY_SCORE_THRESHOLD:
            # find the matched candidate row to get its id
            # we match by name string — there could be duplicates; pick first
            cand_row = candidates[candidates[target_name_col] == match_str]
            if not cand_row.empty:
                matched_candidate_ids.append(cand_row.iloc[0].get("id"))
                matched_candidate_names.append(match_str)
                matched_scores.append(int(score))
            else:
                # fallback: use first candidate
                matched_candidate_ids.append(candidates.iloc[0].get("id"))
                matched_candidate_names.append(match_str)
                matched_scores.append(int(score))
        else:
            matched_candidate_ids.append(None)
            matched_candidate_names.append(None)
            matched_scores.append(None)

    # attach results
    joined["matched_id"] = matched_candidate_ids
    joined["matched_name"] = matched_candidate_names
    joined["matched_name_score"] = matched_scores
    joined["distance_m_final"] = matched_distances

    return joined

# ----------------------------
# High-level chunk loop (for OMF and Overpass separately)
# ----------------------------
def run_matching_all_chunks(yelp_proj, target_proj, target_index, chunk_prefix):
    n = len(yelp_proj)
    n_chunks = math.ceil(n / CHUNK_SIZE)
    chunk_files = []

    for i in range(n_chunks):
        start = i * CHUNK_SIZE
        end = min((i + 1) * CHUNK_SIZE, n)
        print(f"\nProcessing chunk {i+1}/{n_chunks}: rows {start}..{end-1} (size {end-start})")
        yelp_chunk = yelp_proj.iloc[start:end].copy()

        t0 = time.time()
        matched_chunk = process_chunk(yelp_chunk, target_proj, target_index)
        t1 = time.time()
        print(f"Chunk processed in {t1-t0:.1f}s")

        # write chunk to disk (GeoJSON)
        chunk_file = Path(f"{chunk_prefix}_{i+1}.geojson")
        matched_chunk.to_file(chunk_file, driver="GeoJSON")
        print(f"Saved chunk to {chunk_file} ({chunk_file.stat().st_size/1024/1024:.2f} MB)")
        chunk_files.append(chunk_file)

    # concatenate all chunk files into one GeoDataFrame
    print("Concatenating chunk files...")
    gdfs = [gpd.read_file(str(p)) for p in chunk_files]
    all_matched = gpd.GeoDataFrame(pd.concat(gdfs, ignore_index=True), crs=gdfs[0].crs)
    # save final
    return all_matched, chunk_files

# ----------------------------
# Run pipeline
# ----------------------------
if __name__ == "__main__":
    # OMF matching
    print("\n=== MATCHING: Yelp -> OMF ===")
    omf_matched_gdf, omf_chunks = run_matching_all_chunks(yelp_proj, omf_proj, omf_index, OMF_CHUNK_PREFIX)
    omf_matched_gdf.to_file(FINAL_OMF_OUT, driver="GeoJSON")
    print(f"Final OMF matched saved to {FINAL_OMF_OUT} ({FINAL_OMF_OUT.stat().st_size/1024/1024:.2f} MB)")

    # Overpass matching
    print("\n=== MATCHING: Yelp -> Overpass ===")
    overpass_matched_gdf, overpass_chunks = run_matching_all_chunks(yelp_proj, overpass_proj, overpass_index, OVERPASS_CHUNK_PREFIX)
    overpass_matched_gdf.to_file(FINAL_OVERPASS_OUT, driver="GeoJSON")
    print(f"Final Overpass matched saved to {FINAL_OVERPASS_OUT} ({FINAL_OVERPASS_OUT.stat().st_size/1024/1024:.2f} MB)")

    print("\nAll matching complete.")

