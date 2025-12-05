import pandas as pd

# Load your golden dataset
gold = pd.read_csv("RULE_GOLDEN_DATASET.csv")

# Pick columns for evaluation (truth)
gold_eval = gold.rename(columns={
    "omf_name": "truth_name",
    "omf_address": "truth_address",
    "omf_phone": "truth_phone",
    "omf_categories": "truth_categories",
    "omf_website": "truth_website"
})

# Keep place_id for merging later
gold_eval = gold_eval[["place_id", "truth_name", "truth_address", "truth_phone", "truth_categories", "truth_website"]]

gold_eval = gold_eval.rename(columns={"omf_place_id": "place_id"})

# Save template CSV
gold_eval.to_csv("RULE_GOLDEN_DATASET_TEMPLATE.csv", index=False)
print("Golden evaluation template saved!")

