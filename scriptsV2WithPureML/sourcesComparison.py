import json
import pandas as pd
from rapidfuzz import fuzz
import re

# ======================================================
# CLEANING HELPERS
# ======================================================

def clean_text(x):
    if not x: return ""
    x = str(x).lower()
    x = re.sub(r"[^a-z0-9 ]", " ", x)
    return re.sub(r"\s+", " ", x).strip()

def clean_phone(p):
    if not p: return ""
    p = re.sub(r"\D", "", str(p))
    return p[-10:] if len(p) >= 10 else p

def safe_json(val):
    """Helper to safely parse JSON or return empty list"""
    if pd.isna(val) or val == "": return []
    try: return json.loads(val)
    except: return []

def parse_address(addr_list):
    if not addr_list: return "", "", "", "", "", ""
    a = addr_list[0]
    street  = clean_text(a.get("freeform", ""))
    city    = clean_text(a.get("locality", ""))
    state   = clean_text(a.get("region", ""))
    postal  = clean_text(a.get("postcode", ""))
    country = clean_text(a.get("country", ""))
    full = clean_text(f"{street} {city} {state} {postal}")
    return full, street, city, state, postal, country

def extract_domain(urls):
    if not urls: return ""
    try:
        u = urls[0].lower().replace("https://", "").replace("http://", "").replace("www.", "")
        return u.split("/")[0]
    except: return ""

# ======================================================
# DATA LOADING
# ======================================================

def load_omf(path):
    df = pd.read_csv(path)
    rows = []
    for _, r in df.iterrows():
        cats = safe_json(r.get("categories"))
        websites = safe_json(r.get("website"))
        socials = safe_json(r.get("socials"))
        addr_list = safe_json(r.get("address"))
        
        full_addr, street, city, state, postal, country = parse_address(addr_list)

        rows.append({
            "place_id": r["place_id"],
            "source": r["source"],
            "name": clean_text(r["name"]),
            "phone": clean_phone(r.get("phone")),
            "domain": extract_domain(websites),
            "addr": full_addr,
            "street": street, "city": city, "state": state, "postal": postal, "country": country,
            # KEEP RAW JSON STRINGS FOR OUTPUT
            "categories": json.dumps(cats),
            "website": json.dumps(websites),
            "socials": json.dumps(socials),
        })
    return pd.DataFrame(rows)

def load_yelp(path):
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            try: obj = json.loads(line)
            except: continue
            
            street = clean_text(obj.get("address", ""))
            city = clean_text(obj.get("city", ""))
            state = clean_text(obj.get("state", ""))
            postal = clean_text(obj.get("postal_code", ""))
            
            rows.append({
                "business_id": obj.get("business_id"),
                "name": clean_text(obj.get("name")),
                "phone": clean_phone(obj.get("phone")),
                "categories": clean_text(str(obj.get("categories", ""))),
                "street": street, "city": city, "state": state, "postal": postal,
                "addr": clean_text(f"{street} {city} {state} {postal}")
            })
    return pd.DataFrame(rows)

# ======================================================
# MATCHING LOGIC
# ======================================================

def calculate_score(omf_row, yelp_row):
    # 1. Phone Match (The Golden Rule)
    if omf_row["phone"] and yelp_row["phone"] and omf_row["phone"] == yelp_row["phone"]:
        return 100
    
    # 2. Fuzzy Text Match
    ns = fuzz.token_sort_ratio(omf_row["name"], yelp_row["name"])
    ad = fuzz.token_sort_ratio(omf_row["addr"], yelp_row["addr"])
    return (0.65 * ns) + (0.35 * ad)

def validate(omf_df, yelp_df):
    matchable = 0
    valid = 0
    valid_rows = []

    # OPTIMIZATION: Group Yelp by City into a dictionary for O(1) lookup
    print("Indexing Yelp data by city...")
    yelp_lookup = {}
    for city, group in yelp_df.groupby("city"):
        if city: yelp_lookup[city] = group.to_dict('records')

    print("Matching OMF records...")
    for _, omf in omf_df.iterrows():
        # Fast lookup
        candidates = yelp_lookup.get(omf["city"], [])
        if not candidates: continue

        best_score = 0
        best_record = None

        for y in candidates:
            score = calculate_score(omf, y)
            if score > best_score:
                best_score = score
                best_record = y
                if best_score == 100: break # Stop early if perfect match

        if best_score >= 55: matchable += 1
        
        # Threshold for "Valid" match
        if best_score >= 75 and best_record:
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

# ======================================================
# MAIN EXECUTION
# ======================================================

if __name__ == "__main__":
    omf = load_omf("NORMALIZED_SOURCES.csv")
    yelp = load_yelp("../data/raw/yelp_academic_dataset_business.json")

    total, matchable, valid, valid_rows = validate(omf, yelp)

    print("\n=== VALIDATION SUMMARY ===")
    print(f"Total OMF: {total}")
    print(f"Matchable: {matchable}")
    print(f"Valid: {valid}")
    if matchable > 0:
        print(f"Coverage: {(valid / matchable) * 100:.2f}%")

    pd.DataFrame(valid_rows).to_csv("VALID_MATCHES.csv", index=False)
    print("\nWrote VALID_MATCHES.csv")
