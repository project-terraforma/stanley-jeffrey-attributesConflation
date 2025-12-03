#!/usr/bin/env python3
"""
Minimal conflate_attributes.py

Inputs:
 - data/place_clusters.json   (from assign_place_ids.py)
 - data/meta_lookup.csv       (from assign_place_ids.py)
 - data/normalized_p_sb_data.json  (optional, for coords)

Output:
 - data/final_golden_records.json  (JSON Lines)
Rules (baseline):
 - Source priority: yelp > omf > osm
 - Name: prefer top-priority source; else mode
 - Address: longest token count, tie-break by source priority
 - Coordinates: median of available coordinates from original normalized data
"""
import os, json
import pandas as pd
import statistics
from collections import Counter
import random

# --- CONFIG ---
CLUSTERS_IN = "data/place_clusters.json"
META_IN = "data/meta_lookup.csv"
ORIG_IN = "data/normalized_p_sb_data.json"
OUT = "data/final_golden_records.json"

# NEW (The "Stress Test"):
SOURCE_PRIORITY = {'osm': 1, 'omf': 2, 'yelp': 3}

def load_meta(path):
    if os.path.exists(path):
        return pd.read_csv(path).set_index('id').to_dict(orient='index')
    return {}

def load_original_index(path):
    if os.path.exists(path):
        df = pd.read_json(path, lines=True)
        if 'id' in df.columns:
            return df.set_index('id').to_dict(orient='index')
    return {}

def choose_name(members, meta):
    candidates = []
    for m in members:
        rec = meta.get(m)
        if not rec: continue
# --- THE "SPARSITY" SIMULATION ---
        # "Simulate that Yelp is missing 15% of the time"
        if rec.get('source') == 'yelp':
            if random.random() < 0.15:  # 15% chance to ignore Yelp
                continue
        nm = rec.get('name')
        if nm and str(nm).strip():
            candidates.append((nm, rec.get('source')))
    if not candidates:
        return None, "none"
    # pick best by source priority
    best = None; best_rank = 999
    for nm, src in candidates:
        r = SOURCE_PRIORITY.get(src, 999)
        if r < best_rank:
            best_rank = r; best = (nm, src)
    if best:
        return best[0], f"priority:{best[1]}"
    # fallback to mode
    return Counter([c[0] for c in candidates]).most_common(1)[0][0], "mode"

def choose_address(members, meta):
    candidates = []
    for m in members:
        rec = meta.get(m)
        if not rec: continue
        addr = rec.get('address')
        src = rec.get('source')
        if addr and str(addr).strip():
            tokens = len(str(addr).split())
            candidates.append((tokens, addr, src))
    if not candidates:
        return None, "none"
    candidates.sort(key=lambda x: (-x[0], SOURCE_PRIORITY.get(x[2], 999)))
    return candidates[0][1], f"longest_tokens:{candidates[0][2]}"

def choose_coords(members, orig_index):
    coords = []
    for m in members:
        rec = orig_index.get(m)
        if not rec: continue
        lat = rec.get('lat') if 'lat' in rec else rec.get('latitude') if 'latitude' in rec else None
        lon = rec.get('lon') if 'lon' in rec else rec.get('longitude') if 'longitude' in rec else None
        try:
            if lat is not None and lon is not None:
                coords.append((float(lat), float(lon)))
        except Exception:
            continue
    if not coords:
        return None, "none"
    return (statistics.median([c[0] for c in coords]), statistics.median([c[1] for c in coords])), "median"

def main():
    if not os.path.exists(CLUSTERS_IN):
        print(f"Missing clusters file: {CLUSTERS_IN}")
        return
    clusters = json.load(open(CLUSTERS_IN))
    meta = load_meta(META_IN)
    orig_index = load_original_index(ORIG_IN)

    out = []
    for c in clusters:
        members = c.get('members', [])
        name, name_reason = choose_name(members, meta)
        addr, addr_reason = choose_address(members, meta)
        coords, coords_reason = choose_coords(members, orig_index)
        rec = {
            "place_id": c.get('place_id'),
            "primary_name": name,
            "name_reason": name_reason,
            "primary_address": addr,
            "address_reason": addr_reason,
            "chosen_coords": coords,
            "coords_reason": coords_reason,
            "members": members,
            "sources": c.get('sources', []),
            "cluster_size": c.get('size', len(members)),
            "avg_match_confidence": c.get('avg_confidence')
        }
        out.append(rec)

    os.makedirs(os.path.dirname(OUT) or ".", exist_ok=True)
    with open(OUT, "w") as f:
        for r in out:
            f.write(json.dumps(r) + "\n")

    print(f"Wrote {len(out)} conflated golden records to {OUT}")

if __name__ == "__main__":
    main()
