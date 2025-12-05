import json
import pandas as pd
from rapidfuzz import fuzz
import re

# ============================
# HELPERS
# ============================

def clean_text(x):
    if not x:
        return ""
    x = str(x).lower()
    x = re.sub(r"[^a-z0-9 ]", " ", x)
    return re.sub(r"\s+", " ", x).strip()

def clean_phone(p):
    if not p:
        return ""
    p = re.sub(r"\D", "", str(p))
    return p[-10:] if len(p) >= 10 else p

def to_json_list(x):
    if pd.isna(x) or x == "":
        return json.dumps([])
    return json.dumps([x])

# ============================
# LOAD DATA
# ============================


def load_omf(path):
    df = pd.read_csv(path)
    df.columns = df.columns.str.strip().str.lower()  # normalize headers

    rows = []
    for _, r in df.iterrows():
        rows.append({
            "place_id": r.get("id", ""),          # safer access
            "name": clean_text(r.get("name", "")),
            "addr": clean_text(r.get("address", "")),
            "phone": clean_phone(r.get("phones", "")),
            "categories": to_json_list(r.get("category", "")),
            "website": to_json_list(r.get("websites", "")),
            "socials": to_json_list(r.get("socials", "")),
            "source": r.get("source_file", "omf"),
            "city": clean_text(r.get("city", ""))   # <-- ADD THIS

        })
    return pd.DataFrame(rows)


def load_yelp(path):
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            try:
                obj = json.loads(line)
            except:
                continue
            rows.append({
                "business_id": obj.get("business_id"),
                "name": clean_text(obj.get("name")),
                "addr": clean_text(obj.get("address", "")),
                "phone": clean_phone(obj.get("phone")),
                "categories": clean_text(str(obj.get("categories", ""))),
                "city": clean_text(obj.get("city", ""))  # <-- include city here
            })
    return pd.DataFrame(rows)

'''
# ============================
# FUZZY MATCHING
# ============================

def calculate_score(omf_row, yelp_row):
    # Weighted fuzzy match: 65% name, 35% address
    name_score = fuzz.token_sort_ratio(omf_row["name"], yelp_row["name"])
    addr_score = fuzz.token_sort_ratio(omf_row["addr"], yelp_row["addr"])
    return 0.65 * name_score + 0.35 * addr_score

def match_omf_yelp(omf_df, yelp_df, min_matchable=55, min_valid=75):
    valid_rows = []
    matchable_count = 0
    valid_count = 0

    print("Matching OMF to Yelp (fuzzy)...")

    yelp_records = yelp_df.to_dict("records")  # no city filter

    for _, omf in omf_df.iterrows():
        best_score = 0
        best_yelp = None

        for yelp in yelp_records:
            score = calculate_score(omf, yelp)
            if score > best_score:
                best_score = score
                best_yelp = yelp
                if best_score == 100:
                    break

        if best_score >= min_matchable:
            matchable_count += 1
        if best_score >= min_valid and best_yelp:
            valid_count += 1
            valid_rows.append({
                "omf_place_id": omf["place_id"],
                "omf_name": omf["name"],
                "omf_address": omf["addr"],
                "omf_phone": omf["phone"],
                "omf_categories": omf["categories"],
                "omf_website": omf["website"],
                "omf_socials": omf["socials"],
                "omf_source": omf["source"],
                "yelp_business_id": best_yelp["business_id"],
                "yelp_name": best_yelp["name"],
                "yelp_address": best_yelp["addr"],
                "yelp_phone": best_yelp["phone"],
                "yelp_categories": best_yelp["categories"],
                "match_score": best_score
            })

    return len(omf_df), matchable_count, valid_count, valid_rows
'''

# ======================================================
# MATCHING LOGIC WITH CITY FILTER
# ======================================================

def calculate_score(omf_row, yelp_row):
    # Phone match takes priority
    if omf_row["phone"] and yelp_row["phone"] and omf_row["phone"] == yelp_row["phone"]:
        return 100
    # Fuzzy match name & address
    ns = fuzz.token_sort_ratio(omf_row["name"], yelp_row["name"])
    ad = fuzz.token_sort_ratio(omf_row["addr"], yelp_row["addr"])
    return (0.65 * ns) + (0.35 * ad)

def validate(omf_df, yelp_df):
    matchable = 0
    valid = 0
    valid_rows = []

    # Group Yelp by city for fast lookup
    print("Indexing Yelp data by city...")
    yelp_lookup = {}
    for city, group in yelp_df.groupby("city"):
        if city:
            yelp_lookup[city] = group.to_dict('records')

    print("Matching OMF records...")
    for _, omf in omf_df.iterrows():
        city = omf["city"]
        if not city or city not in yelp_lookup:
            continue  # skip if city missing or no Yelp records

        candidates = yelp_lookup[city]
        best_score = 0
        best_record = None
        '''
        for y in candidates:
            score = calculate_score(omf, y)
            if score > best_score:
                best_score = score
                best_record = y
                if best_score == 100:  # perfect match, stop early
                    break
'''
        for y in candidates:
            score = calculate_score(omf, y)
            if score > best_score:
                best_score = score
                best_record = y
                print(f"OMF: {omf['name']} / {omf['addr']}")
                print(f"Yelp: {y['name']} / {y['addr']}")
                print(f"Score: {score}")
                if best_score == 100:
                    break

        if best_score >= 55:
            matchable += 1

        if best_score >= 75 and best_record:  # threshold for "valid" match
            valid += 1
            valid_rows.append({
                "omf_place_id": omf["place_id"],
                "omf_source": omf["source"],
                "omf_name": omf["name"],
                "omf_address": omf["addr"],
                "omf_phone": omf["phone"],
                "omf_categories": omf["categories"],
                "omf_website": omf["website"],
                "omf_socials": omf["socials"],

                "yelp_business_id": best_record["business_id"],
                "yelp_name": best_record["name"],
                "yelp_address": best_record["addr"],
                "yelp_phone": best_record["phone"],
                "yelp_categories": best_record["categories"],

                "match_score": best_score
            })

    return len(omf_df), matchable, valid, valid_rows

# ============================
# MAIN
# ============================

if __name__ == "__main__":
    omf = load_omf("NORMALIZED_SOURCES_SAMPLE_5000.csv")  # or full CSV
    yelp = load_yelp("../data/raw/yelp_academic_dataset_business.json")

    total, matchable, valid, valid_rows = validate(omf, yelp)

    print("\n=== MATCHING SUMMARY ===")
    print(f"Total OMF: {total}")
    print(f"Matchable (score >= 55): {matchable}")
    print(f"Valid (score >= 75): {valid}")
    if matchable > 0:
        print(f"Coverage: {(valid / matchable) * 100:.2f}%")

    pd.DataFrame(valid_rows).to_csv("VALID_MATCHES_FUZZY.csv", index=False)
    print("Wrote VALID_MATCHES_FUZZY.csv")

