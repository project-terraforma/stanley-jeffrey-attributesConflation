import json
import pandas as pd
import re

# ======================================================
# CLEANING HELPERS
# ======================================================

def clean_text(x):
    if not x:
        return ""
    x = str(x).lower()
    x = re.sub(r"[^a-z0-9 ]", " ", x)
    x = re.sub(r"\s+", " ", x).strip()
    return x

def clean_phone(p):
    if not p:
        return ""
    p = re.sub(r"\D", "", str(p))
    return p[-10:] if len(p) >= 10 else p

# ======================================================
# LOAD + NORMALIZE YELP BUSINESS DATASET
# ======================================================

def load_and_normalize_yelp(path):
    """
    Loads Yelp dataset and outputs the same normalized fields used by the validation script.
    """
    rows = []

    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            try:
                obj = json.loads(line)
            except:
                continue

            # Raw fields
            business_id = obj.get("business_id", "")
            raw_name = obj.get("name", "")
            raw_phone = obj.get("phone", "")
            raw_categories = obj.get("categories", "")

            # Address parts
            street = clean_text(obj.get("address", ""))
            city   = clean_text(obj.get("city", ""))
            state  = clean_text(obj.get("state", ""))
            postal = clean_text(obj.get("postal_code", ""))

            full_addr = clean_text(f"{street} {city} {state} {postal}")

            rows.append({
                "business_id": business_id,
                "name": clean_text(raw_name),
                "phone": clean_phone(raw_phone),
                "categories": clean_text(str(raw_categories)),
                "street": street,
                "city": city,
                "state": state,
                "postal": postal,
                "addr": full_addr,
            })

    return pd.DataFrame(rows)


# ======================================================
# MAIN
# ======================================================

if __name__ == "__main__":
    yelp_df = load_and_normalize_yelp("../data/raw/yelp_academic_dataset_business.json")

    print("Loaded Yelp rows:", len(yelp_df))
    yelp_df.to_csv("YELP_NORMALIZED.csv", index=False)
    print("Saved YELP_NORMALIZED.csv")

