import pandas as pd
import json

# ===========================
# CONFIG
# ===========================
INPUT_FILE = "VALID_MATCHES_FUZZY.csv"
OUTPUT_GOLD_FILE = "RULE_GOLDEN_DATASET.csv"
OUTPUT_REVIEW_FILE = "LOW_SCORE_FOR_REVIEW.csv"

# Minimum match score to automatically accept a record
MIN_MATCH_SCORE = 75  # adjust as needed

# Columns mapping: OMF -> Golden truth
GOLD_COLS = {
    "omf_place_id": "place_id",
    "omf_name": "truth_name",
    "omf_address": "truth_address",
    "omf_phone": "truth_phone",
    "omf_categories": "truth_categories",
    "omf_website": "truth_website"
}

# ===========================
# LOAD DATA
# ===========================
df = pd.read_csv(INPUT_FILE)

# ===========================
# FILTER BY MATCH SCORE
# ===========================
accepted = df[df["match_score"] >= MIN_MATCH_SCORE].copy()
manual_review = df[df["match_score"] < MIN_MATCH_SCORE].copy()

print(f"Total records: {len(df)}")
print(f"Accepted (>= {MIN_MATCH_SCORE}): {len(accepted)}")
print(f"For manual review (< {MIN_MATCH_SCORE}): {len(manual_review)}")

# ===========================
# SELECT & RENAME COLUMNS
# ===========================
gold_df = accepted[list(GOLD_COLS.keys())].rename(columns=GOLD_COLS)

# Remove duplicates based on place_id (keep first)
gold_df = gold_df.drop_duplicates(subset=["place_id"])

# ===========================
# SAVE FILES
# ===========================
gold_df.to_csv(OUTPUT_GOLD_FILE, index=False)
print(f"Golden dataset saved: {OUTPUT_GOLD_FILE}")

if len(manual_review) > 0:
    manual_review.to_csv(OUTPUT_REVIEW_FILE, index=False)
    print(f"Records below threshold saved for review: {OUTPUT_REVIEW_FILE}")

