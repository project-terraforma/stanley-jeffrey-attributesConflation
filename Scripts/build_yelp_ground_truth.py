#!/usr/bin/env python3
"""
build_yelp_ground_truth.py

Automatically generates yelp_ground_truth.csv from clusters that
contain at least one Yelp source record.

Inputs:
 - data/meta_lookup.csv
 - data/place_clusters.json

Output:
 - data/yelp_ground_truth.csv
"""

import json
import pandas as pd

META = "data/meta_lookup.csv"
CLUSTERS = "data/place_clusters.json"
OUT = "data/yelp_ground_truth.csv"

def main():
    meta = pd.read_csv(META)
    meta_map = meta.set_index("id").to_dict(orient="index")

    with open(CLUSTERS) as f:
        clusters = json.load(f)

    rows = []

    for c in clusters:
        place_id = c["place_id"]
        members = c["members"]

        # find Yelp record inside the cluster
        yelp_records = [
            meta_map[m]
            for m in members
            if m in meta_map and meta_map[m].get("source") == "yelp"
        ]

        if len(yelp_records) == 0:
            continue  # skip clusters without Yelp

        # assume Yelp record is ground truth (you can later refine)
        gt = yelp_records[0]

        rows.append({
            "place_id": place_id,
            "true_name": gt.get("name"),
            "true_address": gt.get("address")
        })

    df = pd.DataFrame(rows)
    df.to_csv(OUT, index=False)

    print(f"Generated {len(df)} rows → {OUT}")


if __name__ == "__main__":
    main()
