import pandas as pd
import numpy as np
from rapidfuzz import fuzz
import duckdb
import os

# --- CONFIG ---
INPUT_FILE = 'data/normalized_p_sb_data.json'
OUTPUT_FILE = 'data/training_pairs_labeled.json'

# INPUT: Your accumulated wisdom (The file you edit/append to)
MANUAL_LABELS_INPUT = 'data/processed/manual_labels.csv'

# OUTPUT: New questions for next time (The file the script creates)
UNCERTAIN_OUTPUT = 'data/processed/active_learning_candidates.csv'

# --- HELPER: HAVERSINE DISTANCE ---
def haversine(lon1, lat1, lon2, lat2):
    # Vectorized version for Pandas
    lon1, lat1, lon2, lat2 = map(np.radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1 
    dlat = lat2 - lat1 
    a = np.sin(dlat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2)**2
    c = 2 * np.arcsin(np.sqrt(a)) 
    r = 6371000 # Radius of earth in meters
    return c * r

# --- 1. LOAD DATA ---
print("Loading data...")
df = pd.read_json(INPUT_FILE, lines=True)

df_yelp = df[df['source'] == 'yelp'].copy()
df_other = df[df['source'].isin(['omf', 'osm'])].copy()

print(f"Anchors (Yelp): {len(df_yelp)}")
print(f"Candidates (OMF/OSM): {len(df_other)}")

# --- 2. BLOCKING (DuckDB) ---
print("Generating candidate pairs (DuckDB Spatial Join)...")

con = duckdb.connect()

query = """
SELECT 
    y.id AS id_left, 
    y.source AS source_left,
    y.name_norm AS name_norm_left, 
    y.address_norm AS address_left,   
    y.lat AS lat_left, 
    y.lon AS lon_left,
    
    o.id AS id_right, 
    o.source AS source_right,
    o.name_norm AS name_norm_right, 
    o.address_norm AS address_right,  
    o.lat AS lat_right, 
    o.lon AS lon_right
FROM df_yelp y, df_other o
WHERE 
    y.lat BETWEEN (o.lat - 0.003) AND (o.lat + 0.003)
    AND 
    y.lon BETWEEN (o.lon - 0.003) AND (o.lon + 0.003)
"""

pairs = con.execute(query).df()
print(f"Initial Candidate Pairs: {len(pairs)}")

# --- 3. FEATURE ENGINEERING ---
print("Calculating features...")
pairs['geo_distance'] = haversine(
    pairs['lon_left'], pairs['lat_left'],
    pairs['lon_right'], pairs['lat_right']
)

# Hard Filter (Speed optimization)
pairs = pairs[pairs['geo_distance'] < 1000].copy()

# Name Score
pairs['name_score'] = pairs.apply(
    lambda x: fuzz.ratio(str(x['name_norm_left']), str(x['name_norm_right'])) / 100.0, 
    axis=1
)

# Address Score
pairs['address_left'] = pairs['address_left'].fillna('')
pairs['address_right'] = pairs['address_right'].fillna('')
pairs['address_score'] = pairs.apply(
    lambda x: fuzz.token_sort_ratio(str(x['address_left']), str(x['address_right'])) / 100.0, 
    axis=1
)

# --- 4. AUTO-LABELING ---
print("Applying weak supervision labels...")

def get_label(row):
    dist = row['geo_distance']
    score = row['name_score']
    
    # Strict Auto-Positive
    if dist < 50 and score > 0.85:
        return 1
    # Strict Auto-Negative
    if dist > 300 or score < 0.4:
        return 0
    # Ambiguous
    return -1

pairs['label'] = pairs.apply(get_label, axis=1)

# --- 5. MERGE MANUAL LABELS (VECTORIZED & FAST) ---
if os.path.exists(MANUAL_LABELS_INPUT):
    print(f"Loading manual overrides from {MANUAL_LABELS_INPUT}...")
    manual_df = pd.read_csv(MANUAL_LABELS_INPUT)
    
    # 1. Keep only definite decisions (0 or 1)
    manual_decisions = manual_df[manual_df['label'].isin([0, 1])].copy()
    
    # 2. Rename for join
    manual_decisions = manual_decisions[['id_left', 'id_right', 'label']].rename(
        columns={'label': 'manual_label'}
    )
    
    # 3. Merge (Left Join) - Efficiently matches rows
    pairs = pairs.merge(manual_decisions, on=['id_left', 'id_right'], how='left')
    
    # 4. Apply Overrides
    # If manual_label exists, use it. Else keep original label.
    pairs['label'] = pairs['manual_label'].combine_first(pairs['label'])
    
    # 5. Drop helper col
    pairs = pairs.drop(columns=['manual_label'])
    
    print(f"Merged {len(manual_decisions)} manual overrides.")
else:
    print("No manual labels file found yet. Using auto-labels only.")

# --- 6. EXPORT UNCERTAIN PAIRS ---
# Export whatever is LEFT as -1 (excluding what you just fixed)
uncertain_pairs = pairs[pairs['label'] == -1].copy()

if len(uncertain_pairs) > 0:
    uncertain_pairs.to_csv(UNCERTAIN_OUTPUT, index=False)
    print(f"⚠️  Saved {len(uncertain_pairs)} NEW ambiguous pairs to {UNCERTAIN_OUTPUT}")
    print("    (Action: Copy labeled rows from this file -> manual_labels.csv)")

# --- 7. FINAL DATASET & BALANCING ---
training_set = pairs[pairs['label'] != -1].copy()

print("Balancing dataset...")
df_pos = training_set[training_set['label'] == 1]
df_neg = training_set[training_set['label'] == 0]

# Sample 5x as many negatives as positives
n_pos = len(df_pos)
n_neg_keep = n_pos * 5 

if len(df_neg) > n_neg_keep:
    df_neg = df_neg.sample(n=n_neg_keep, random_state=42)

training_set = pd.concat([df_pos, df_neg])
training_set = training_set.sample(frac=1, random_state=42).reset_index(drop=True)

# --- 8. EXPORT TRAINING DATA ---
final_cols = [
    'id_left', 'source_left', 'name_norm_left', 'address_left',
    'lat_left', 'lon_left',
    'id_right', 'source_right', 'name_norm_right', 'address_right',
    'lat_right', 'lon_right',
    'geo_distance', 'name_score', 'address_score', 'label'
]

# Safeguard
use_cols = [c for c in final_cols if c in training_set.columns]
training_set = training_set[use_cols]

print(f"Generated {len(training_set)} labeled pairs.")
print(f"Positives: {len(training_set[training_set['label']==1])}")
print(f"Negatives: {len(training_set[training_set['label']==0])}")

print(f"Exporting training data to {OUTPUT_FILE}...")
training_set.to_json(OUTPUT_FILE, orient='records', lines=True)
print("Done.")