import pandas as pd
import json
from pathlib import Path
from datetime import datetime


BASE_DIR = Path(__file__).resolve().parent.parent  # go up one folder
INPUT = "VALID_MATCHES.csv"
OUTPUT = Path(__file__).resolve().parent / f"RULE_GOLDEN_DATASET_TEMPLATE.csv"

df = pd.read_csv(INPUT)

# Normalize provider names
df["omf_source"] = (
    df["omf_source"]
    .str.lower()
    .str.replace(" ", "_")
    .str.replace("microsoft_structured", "microsoft")
    .str.replace("msft", "microsoft")
    .str.replace("foursquare_structured", "foursquare")
)

providers = sorted(df["omf_source"].unique())

rows = []

# Build golden rows
for pid, group in df.groupby("omf_place_id"):

    y = group.iloc[0]

    entry = {
        "place_id": pid,

        # Yelp fields
        "yelp_business_id": y["yelp_business_id"],
        "yelp_name": y["yelp_name"],
        "yelp_address": y["yelp_address"],
        "yelp_phone": y["yelp_phone"],
        "yelp_categories": y["yelp_categories"],

        "match_score": y["match_score"],

        # Truth columns — manually filled later
        "truth_name_source": "",
        "truth_name": "",
        "truth_phone_source": "",
        "truth_phone": "",
        "truth_website_source": "",
        "truth_website": "",
        "truth_address_source": "",
        "truth_address": "",
        "truth_categories_source": "",
        "truth_categories": "",
        "best_source": ""
    }


    # Provider-specific fields
    for _, r in group.iterrows():
        src = r["omf_source"]

        entry[f"{src}_name"] = r["omf_name"]
        entry[f"{src}_address"] = r["omf_address"]
        entry[f"{src}_phone"] = r["omf_phone"]
        entry[f"{src}_categories"] = r["omf_categories"]
        entry[f"{src}_website"] = r["omf_website"]
        entry[f"{src}_socials"] = r["omf_socials"]

    rows.append(entry)


# Ensure consistent column order
provider_cols = []
for p in providers:
    provider_cols += [
        f"{p}_name",
        f"{p}_address",
        f"{p}_phone",
        f"{p}_categories",
        f"{p}_website",
        f"{p}_socials",
    ]

final_cols = (
    [
        "place_id",
        "yelp_business_id",
        "yelp_name",
        "yelp_address",
        "yelp_phone",
        "yelp_categories",
        "match_score",
    ]
    + provider_cols
    + [
        "truth_name_source",
        "truth_name",
        "truth_phone_source",
        "truth_phone",
        "truth_website_source",
        "truth_website",
        "truth_address_source",
        "truth_address",
        "truth_categories_source",
        "truth_categories",
        "best_source",
    ]
)

out = pd.DataFrame(rows)
out = out.reindex(columns=final_cols)

out.to_csv(OUTPUT, index=False)
print(f"Wrote {OUTPUT} with {len(out)} rows.")
