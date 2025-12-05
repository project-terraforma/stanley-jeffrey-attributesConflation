import pandas as pd
from rapidfuzz import fuzz
import json

# =========================
# CONFIG
# =========================
GOLD_FILE = "RULE_GOLDEN_DATASET.csv"      # Golden dataset
PRED_FILE = "RULE_BEST_ATTRIBUTES.csv"    # Predictions
ATTRS = {
    "name":       ("truth_name", "best_name"),
    "phone":      ("truth_phone", "best_phone"),
    "address":    ("truth_address", "best_address"),
    "categories": ("truth_categories", "best_category"),
    "website":    ("truth_website", "best_website"),
}

# =========================
# NORMALIZATION HELPERS
# =========================
def clean_phone(p):
    if pd.isna(p): return ""
    digits = "".join([d for d in str(p) if d.isdigit()])
    return digits[-10:]

def clean_text(t):
    if pd.isna(t): return ""
    t = str(t).lower()
    t = "".join(c if c.isalnum() or c==" " else " " for c in t)
    return " ".join(t.split())

def clean_website(w):
    if pd.isna(w): return ""
    w = str(w).lower()
    for prefix in ["https://", "http://", "www."]:
        w = w.replace(prefix, "")
    return w.split("/")[0]

def clean_category(c):
    if pd.isna(c): return ""
    try:
        obj = json.loads(c)
        if isinstance(obj, list):
            return " ".join([str(x).lower() for x in obj])
        if isinstance(obj, dict):
            return obj.get("primary","").lower()
    except:
        return str(c).lower()
    return str(c).lower()

def normalize(value, field):
    if field == "phone": 
        return clean_phone(value)
    if field == "address": 
        # Skip extra cleaning since addresses are already normalized
        return str(value)
    if field == "website": 
        return clean_website(value)
    if field == "categories": 
        return clean_category(value)
    return clean_text(value)

# =========================
# MAIN EVALUATION
# =========================
gold = pd.read_csv(GOLD_FILE)
pred = pd.read_csv(PRED_FILE)

merged = gold.merge(pred, on="place_id", how="inner")

field_scores = {}
for field, (truth_col, pred_col) in ATTRS.items():
    correct = 0
    total = 0
    for _, r in merged.iterrows():
        t = normalize(r[truth_col], field)
        p = normalize(r.get(pred_col, ""), field)

        # Debug output for address
        if field == "address":
            print(f"Truth   : '{t}'")
            print(f"Pred    : '{p}'")
            print(f"Fuzzy % : {fuzz.ratio(t, p)}")
            print("-" * 40)

        if t == "" or p == "":
            continue

        total += 1
        if t == p or fuzz.ratio(t, p) >= 90:
            correct += 1

    score = (correct / total * 100) if total > 0 else 0
    field_scores[field] = score

# Optionally remove address from overall accuracy
# overall = sum([v for k,v in field_scores.items() if k != "address"]) / (len(field_scores)-1)
overall = sum(field_scores.values()) / len(field_scores) if field_scores else 0

print("\n=== ACCURACY RESULTS ===")
for f, s in field_scores.items():
    print(f"{f:12s}: {s:.2f}%")
print(f"Overall Accuracy: {overall:.2f}%")

