import pandas as pd

triplet_df = pd.read_csv("../data/processed/yelp_triplet_matches_with_gaps.csv")

ground_truth = triplet_df[['place_id', 'name', 'address']].drop_duplicates()

ground_truth.to_csv("../data/processed/yelp_ground_truth.csv", index=False)

print(f"Ground-truth dataset created: {len(ground_truth):,} place_ids")

