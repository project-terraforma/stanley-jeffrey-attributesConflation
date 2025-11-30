import pandas as pd
import numpy as np
from math import radians, cos, sin, asin, sqrt
import jellyfish # pip install jellyfish

# --- CONFIG ---
INPUT_FILE = 'data/normalized_p_sb_data.json'
OUTPUT_FILE = 'data/training_pairs_labeled_old.json'

# --- HELPER: HAVERSINE DISTANCE ---
def haversine(lon1, lat1, lon2, lat2):
    """
    Calculate the great circle distance between two points 
    on the earth (specified in decimal degrees) in METERS.
    """
    # Vectorized version for Pandas
    lon1, lat1, lon2, lat2 = map(np.radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1 
    dlat = lat2 - lat1 
    a = np.sin(dlat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2)**2
    c = 2 * np.arcsin(np.sqrt(a)) 
    r = 6371000 # Radius of earth in meters
    return c * r

# --- 1. LOAD AND SPLIT DATA ---
print("Loading data...")
df = pd.read_json(INPUT_FILE, lines=True)

# We want to match YELP (Anchor) -> OMF/OSM (Candidates)
df_yelp = df[df['source'] == 'yelp'].copy()
df_other = df[df['source'].isin(['omf', 'osm'])].copy()

print(f"Anchors (Yelp): {len(df_yelp)}")
print(f"Candidates (OMF/OSM): {len(df_other)}")

# --- 2. BLOCKING (Candidate Generation) ---
# We only compare records if they are in the same City AND start with same letter.
# This reduces 14 billion pairs to a few hundred thousand.

print("Generating candidate pairs (Blocking)...")

# 1. Use strict Name Blocking (First 3 letters)
# "Starbucks" -> "sta"
# "Subway" -> "sub"
# They will NOT match, which saves millions of pairs.
df_yelp['block_key'] = df_yelp['city'] + "_" + df_yelp['name_norm'].str[0:3]
df_other['block_key'] = df_other['city'] + "_" + df_other['name_norm'].str[0:3]

# Inner Join on the blocking key
pairs = pd.merge(
    df_yelp, 
    df_other, 
    on='block_key', 
    suffixes=('_left', '_right')
)

print(f"Initial Candidate Pairs (from Blocking): {len(pairs)}")

# --- 3. OPTIMIZED FEATURE ENGINEERING ---

# A. CALCULATE DISTANCE FIRST (Vectorized Math = Instant)
print("Calculating geographic distances...")
pairs['geo_distance'] = haversine(
    pairs['lon_left'], pairs['lat_left'],
    pairs['lon_right'], pairs['lat_right']
)

# B. FILTER IMMEDIATELY (The Speed Boost)
# If they are more than 1000 meters (1km) apart, they are definitely NOT the same place.
# We drop them NOW so we don't waste time checking their names.
print("Filtering pairs > 1000m away...")
pairs = pairs[pairs['geo_distance'] < 1000].copy()

print(f"Pairs remaining after Distance Filter: {len(pairs)}")

# C. CALCULATE STRING SIMILARITY (Only on the close pairs)
# Now we use Jellyfish, but only on the small subset of data.
print("Calculating name similarity (Jellyfish)...")
pairs['name_score'] = pairs.apply(
    lambda x: jellyfish.jaro_winkler_similarity(
        str(x['name_norm_left']), 
        str(x['name_norm_right'])
    ), axis=1
)

# --- 4. AUTOMATIC LABELING (The 'Silver Standard') ---
# Since we don't have human labels, we create them using strict rules.

print("Applying weak supervision labels...")

def get_label(row):
    dist = row['geo_distance']
    score = row['name_score']
    
    # CASE 1: High Confidence Match (Positive)
    # Very close (within 30m) AND very similar name (>0.85)
    if dist < 30 and score > 0.85:
        return 1
        
    # CASE 2: High Confidence Non-Match (Negative)
    # Far away (>500m) OR totally different name (<0.5)
    if dist > 500 or score < 0.5:
        return 0
        
    # CASE 3: Ambiguous (Hard Negatives / Hard Positives)
    # These are the ones the AI actually needs to learn, but for now
    # we mark them as -1 to exclude from initial training or review manually.
    return -1

pairs['label'] = pairs.apply(get_label, axis=1)

# Filter out the ambiguous ones for the clean training set
training_set = pairs[pairs['label'] != -1].copy()

# --- 5. CLEAN UP AND EXPORT ---
final_cols = [
    'id_left', 'source_left', 'name_norm_left', 'lat_left', 'lon_left',
    'id_right', 'source_right', 'name_norm_right', 'lat_right', 'lon_right',
    'geo_distance', 'name_score', 'label'
]

training_set = training_set[final_cols]

print(f"Generated {len(training_set)} labeled pairs.")
print(f"Positives: {len(training_set[training_set['label']==1])}")
print(f"Negatives: {len(training_set[training_set['label']==0])}")

print(f"Exporting to JSON...")
training_set.to_json(OUTPUT_FILE, orient='records', lines=True)
print(f"Saved to {OUTPUT_FILE}")