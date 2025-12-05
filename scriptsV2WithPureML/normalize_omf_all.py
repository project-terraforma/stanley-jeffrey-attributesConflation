import pandas as pd
import json
import re

INPUT = "NORMALIZED_SOURCES_SAMPLE_200.csv"
OUTPUT = "NORMALIZED_SOURCES.csv"

def clean_text(x):
    if not x: return ""
    x = str(x).lower()
    x = re.sub(r"[^a-z0-9 ]", " ", x)
    return re.sub(r"\s+", " ", x).strip()

def clean_phone(p):
    if not p: return ""
    p = re.sub(r"\D", "", str(p))
    return p[-10:] if len(p) >= 10 else p

def to_json_list(x):
    """Wrap string in a JSON array, or empty array if missing"""
    if pd.isna(x) or x == "":
        return json.dumps([])
    return json.dumps([x])

def parse_address(addr_str):
    # Split your address string roughly into street/city/state/postal if possible
    # Here we just use full address as street and leave others blank
    full = clean_text(addr_str)
    return full, full, "", "", "", ""

df = pd.read_csv(INPUT)

normalized = []
for _, row in df.iterrows():
    full_addr, street, city, state, postal, country = parse_address(row["address"])
    normalized.append({
        "place_id": row["id"],
        "source": row["source_file"] if "source_file" in row else "omf",
        "name": clean_text(row["name"]),
        "phone": clean_phone(row["phones"]),
        "addr": full_addr,
        "street": street,
        "city": city,
        "state": state,
        "postal": postal,
        "country": country,
        "categories": to_json_list(row.get("category", "")),
        "website": to_json_list(row.get("websites", "")),
        "socials": to_json_list(row.get("socials", "")),
    })

pd.DataFrame(normalized).to_csv(OUTPUT, index=False)
print(f"Wrote {OUTPUT} ({len(normalized)} records)")

