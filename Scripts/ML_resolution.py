import pandas as pd
import networkx as nx
import uuid

# --- CONFIG ---
INPUT_PAIRS_FILE = 'data/processed/ml_predictions.csv'
OUTPUT_FILE = 'data/final_golden_records.json'

# CONFIDENCE THRESHOLD
# The AI predicts 0.0 to 1.0. We only trust high-confidence matches.
# 0.5 is standard. 0.8 is strict (safer).
THRESHOLD = 0.5

def main():
    print("--- Phase 5: Entity Resolution ---")
    
    # 1. Load the Predictions
    print(f"Loading predictions from {INPUT_PAIRS_FILE}...")
    df = pd.read_csv(INPUT_PAIRS_FILE)
    
    # 2. Filter by Confidence & Prediction
    # We keep pairs where the AI predicted 1 (Match) AND confidence is high
    matches = df[(df['ml_prediction'] == 1) & (df['ml_confidence'] >= THRESHOLD)].copy()
    print(f"Found {len(matches)} valid matches to merge.")

    # 3. Build the Graph
    # NetworkX connects A->B and B->C, realizing A-B-C are all the same place.
    print("Building graph of connected entities...")
    G = nx.Graph()
    
    # Add edges (connections) for every matched pair
    for idx, row in matches.iterrows():
        G.add_edge(row['id_left'], row['id_right'])
        
    # 4. Find Clusters (Connected Components)
    clusters = list(nx.connected_components(G))
    print(f"Found {len(clusters)} clusters of duplicates.")

    # 5. Generate Golden Records ("Survivorship")
    print("Merging data into Golden Records...")
    
    # We create a lookup dictionary to get metadata (Name, Address) back from IDs
    meta_lookup = {}
    
    def save_info(row, suffix):
        pid = row[f'id_{suffix}']
        # Only save if we haven't seen this ID yet (or if we want to overwrite)
        if pid not in meta_lookup:
            meta_lookup[pid] = {
                'source': row[f'source_{suffix}'],
                'name': row[f'name_norm_{suffix}'],
                'address': str(row[f'address_{suffix}']) if pd.notna(row[f'address_{suffix}']) else None
            }
            
    # Scan the matches one last time to fill our lookup table
    for idx, row in matches.iterrows():
        save_info(row, 'left')
        save_info(row, 'right')

    golden_records = []
    
    for cluster in clusters:
        cluster_ids = list(cluster)
        
        # LOGIC: Who survives? 
        # We prioritize Yelp data > OMF data > OSM data
        best_name = None
        best_address = None
        best_source_rank = 999 # Lower is better
        
        sources_found = []
        
        # Helper ranker
        source_priority = {'yelp': 1, 'omf': 2, 'osm': 3}
        
        for pid in cluster_ids:
            if pid not in meta_lookup: continue
            
            info = meta_lookup[pid]
            src = info['source']
            sources_found.append(src)
            
            rank = source_priority.get(src, 10)
            
            # If this source is higher priority than what we have, take its data
            if rank < best_source_rank:
                best_source_rank = rank
                best_name = info['name']
                best_address = info['address']
            
            # Tie-breaker: If rank is equal, but we don't have an address yet, take this one
            elif rank == best_source_rank and best_address is None and info['address']:
                best_address = info['address']

        # Create the Master Record
        golden_record = {
            'golden_id': str(uuid.uuid4()), # Unique ID for the new merged place
            'primary_name': best_name,
            'primary_address': best_address,
            'source_count': len(cluster_ids),
            'sources': list(set(sources_found)),
            'child_ids': cluster_ids
        }
        
        golden_records.append(golden_record)

    # 6. Export
    final_df = pd.DataFrame(golden_records)
    
    # Optional: Sort by most sources found (most verified places at top)
    final_df = final_df.sort_values(by='source_count', ascending=False)
    
    print(f"Generated {len(final_df)} unique Golden Records.")
    
    final_df.to_json(OUTPUT_FILE, orient='records', lines=True)
    print(f"✅ Saved clean map to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()