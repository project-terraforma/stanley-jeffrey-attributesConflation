#!/usr/bin/env python3
"""
Minimal assign_place_ids.py

Inputs (preferred):
 - data/processed/ml_predictions.csv

Fallback inputs:
 - data/training_pairs_labeled.json
 - data/training_pairs_labeled_temp.json

Outputs:
 - data/meta_lookup.csv
 - data/place_id_map.csv
 - data/place_clusters.json
"""
import os, json, uuid
import pandas as pd
from collections import defaultdict

# --- CONFIG ---
PRED_CSV = "data/processed/ml_predictions.csv"
TRAIN_JSONS = ["data/training_pairs_labeled.json", "data/training_pairs_labeled_temp.json"]
META_OUT = "data/meta_lookup.csv"
MAP_OUT = "data/place_id_map.csv"
CLUSTERS_OUT = "data/place_clusters.json"
THRESHOLD = 0.80   # confidence threshold to accept ml edges

# Minimal DSU (Union-Find) with path compression
class DSU:
    def __init__(self):
        self.p = {}
    def make(self, x):
        if x not in self.p:
            self.p[x] = x
    def find(self, x):
        if self.p[x] != x:
            self.p[x] = self.find(self.p[x])
        return self.p[x]
    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra == rb: return
        self.p[rb] = ra

def load_input():
    # prefer ml predictions
    if os.path.exists(PRED_CSV):
        return pd.read_csv(PRED_CSV)
    # fallback train json lines with label==1
    for j in TRAIN_JSONS:
        if os.path.exists(j):
            df = pd.read_json(j, lines=True)
            # ensure id_left/id_right exist
            if 'id_left' in df.columns and 'id_right' in df.columns:
                return df
    raise FileNotFoundError("No input predictions or training pairs found.")
# def load_input():
#     # Prefer training pairs files first (rule-based / labels), then ml predictions
#     for j in TRAIN_JSONS:
#         if os.path.exists(j):
#             df = pd.read_json(j, lines=True)
#             if 'id_left' in df.columns and 'id_right' in df.columns:
#                 print(f"Using training pairs from {j} as input (rule-based path).")
#                 return df

#     # If no training pairs found, fall back to ML predictions if available
#     if os.path.exists(PRED_CSV):
#         print(f"No training pairs found — falling back to ML predictions: {PRED_CSV}")
#         return pd.read_csv(PRED_CSV)

#     raise FileNotFoundError("No input predictions or training pairs found.")

def build_meta(df):
    meta = {}
    for side in ("left","right"):
        idc = f"id_{side}"
        src = f"source_{side}"
        name = f"name_norm_{side}"
        addr = f"address_{side}"
        cols = [c for c in (idc, src, name, addr) if c in df.columns]
        for _, r in df[cols].drop_duplicates().iterrows():
            pid = r[idc]
            if pd.isna(pid): continue
            if pid not in meta:
                meta[pid] = {
                    "id": pid,
                    "source": r.get(src) if src in r else None,
                    "name": r.get(name) if name in r else None,
                    "address": r.get(addr) if addr in r else None
                }
            else:
                if not meta[pid].get("name") and name in r:
                    meta[pid]["name"] = r.get(name)
                if not meta[pid].get("address") and addr in r:
                    meta[pid]["address"] = r.get(addr)
                if not meta[pid].get("source") and src in r:
                    meta[pid]["source"] = r.get(src)
    return meta

def main():
    print("Loading predictions / pairs...")
    df = load_input()
    print(f"Loaded {len(df)} rows.")

    # Build meta lookup from data we have
    meta = build_meta(df)

    # Determine accepted edges:
    # prefer ml_prediction + ml_confidence >= THRESHOLD
    if 'ml_prediction' in df.columns and 'ml_confidence' in df.columns:
        edges = df[(df['ml_prediction'] == 1) & (df['ml_confidence'] >= THRESHOLD)].copy()
    # else fallback to label==1 in training json
    elif 'label' in df.columns:
        edges = df[df['label'] == 1].copy()
    else:
        # If nothing else, assume every row is an edge
        edges = df.copy()

    print(f"{len(edges)} accepted edges for clustering (threshold={THRESHOLD}).")

    # build all ids (so singletons are included)
    all_ids = set()
    if 'id_left' in df.columns:
        all_ids.update(df['id_left'].dropna().unique().tolist())
    if 'id_right' in df.columns:
        all_ids.update(df['id_right'].dropna().unique().tolist())

    # DSU init
    dsu = DSU()
    for pid in all_ids:
        dsu.make(pid)

    # union accepted edges
    for _, r in edges.iterrows():
        a = r.get('id_left')
        b = r.get('id_right')
        if pd.isna(a) or pd.isna(b): continue
        # make nodes if unseen
        if a not in dsu.p: dsu.make(a)
        if b not in dsu.p: dsu.make(b)
        dsu.union(a, b)

    # build clusters
    groups = defaultdict(list)
    for pid in all_ids:
        groups[dsu.find(pid)].append(pid)

    # convert to stable place_ids and produce outputs
    clusters = []
    id_to_place = {}
    for root, members in groups.items():
        place_id = "place_" + uuid.uuid4().hex[:12]
        sub = edges[(edges['id_left'].isin(members)) & (edges['id_right'].isin(members))]
        avg_conf = float(sub['ml_confidence'].mean()) if ('ml_confidence' in sub.columns and len(sub)>0) else None
        sources = list({meta[m]['source'] for m in members if m in meta and meta[m].get('source')})
        clusters.append({
            "place_id": place_id,
            "members": members,
            "size": len(members),
            "avg_confidence": avg_conf,
            "sources": sources
        })
        for m in members:
            id_to_place[m] = place_id

    # Write outputs
    os.makedirs(os.path.dirname(META_OUT) or ".", exist_ok=True)
    print(f"Writing {META_OUT}, {MAP_OUT}, {CLUSTERS_OUT} ...")
    pd.DataFrame.from_dict(meta, orient='index').to_csv(META_OUT, index=False)
    pd.DataFrame(list(id_to_place.items()), columns=['id','place_id']).to_csv(MAP_OUT, index=False)
    with open(CLUSTERS_OUT, 'w') as f:
        json.dump(clusters, f, indent=2)

    print(f"Done. {len(clusters)} clusters (includes singletons).")

if __name__ == "__main__":
    main()
