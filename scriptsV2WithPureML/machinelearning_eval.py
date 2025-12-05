import pandas as pd
import ast
import json
from rapidfuzz import fuzz

GOLD = "ML_GOLDEN_DATASET.csv"
PRED = "ML_BEST_ATTRIBUTES.csv"

try:
    df_g = pd.read_csv(GOLD)
    df_p = pd.read_csv(PRED)
    # merge on place_id
    df = df_g.merge(df_p, on="place_id", how="inner")
except FileNotFoundError:
    print("Error: Input CSV files not found. Run ml_golden.py and ml_based_conflation.py first.")
    exit()

# --------------------------------------------------------
# ATTRIBUTE → (truth_column, predicted_column)
# --------------------------------------------------------
ATTRS = {
    "name":       ("truth_name", "best_name"),
    "phone":      ("truth_phone", "best_phone"),
    "address":    ("truth_address", "best_address"),
    "website":    ("truth_website", "best_website"),
    "category":   ("truth_categories", "best_category")
}

# --------------------------------------------------------
# NORMALIZATION HELPERS
# --------------------------------------------------------
def clean_phone(p):
    if pd.isna(p): return ""
    digits = "".join([d for d in str(p) if d.isdigit()])
    return digits[-10:]  # last 10 digits (US phones)

def clean_name(n):
    if pd.isna(n): return ""
    n = str(n).lower()
    n = "".join(c if c.isalnum() or c==" " else " " for c in n)
    return " ".join(n.split())

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
        if isinstance(obj, dict):
            return obj.get("primary","").lower()
    except:
        return str(c).lower()
    return str(c).lower()

def clean_address(a):
    if pd.isna(a): return ""
    try:
        obj = json.loads(a)
        if isinstance(obj, dict):
            a = " ".join([
                obj.get("freeform",""),
                obj.get("locality",""),
                obj.get("region",""),
                obj.get("postcode",""),
                obj.get("country","")
            ])
        elif isinstance(obj, list):
            parts = []
            for block in obj:
                if isinstance(block, dict):
                    parts.append(block.get("freeform",""))
                    parts.append(block.get("locality",""))
                    parts.append(block.get("region",""))
                    parts.append(block.get("postcode",""))
                    parts.append(block.get("country",""))
            a = " ".join(parts)
    except:
        pass

    a = str(a).lower()
    a = "".join(c if c.isalnum() or c==" " else " " for c in a)
    a = " ".join(a.split())
    return a

# Dispatcher
def normalize(val, field):
    if field == "phone": return clean_phone(val)
    if field == "address": return clean_address(val)
    if field == "website": return clean_website(val)
    if field == "category": return clean_category(val)
    return clean_name(val)

# --------------------------------------------------------
# EVALUATION METRICS
# --------------------------------------------------------
print(f"\n{'ATTRIBUTE':<12} | {'ACCURACY':<10} | {'PRECISION':<10} | {'RECALL':<10} | {'F1 SCORE':<10}")
print("-" * 65)

metrics_list = []

for field, (truth_col, pred_col) in ATTRS.items():
    
    tp = 0              # True Positives (Match)
    pred_count = 0      # Total Non-Empty Predictions (TP + FP)
    truth_count = 0     # Total Non-Empty Truths (TP + FN)
    intersect_count = 0 # Count where BOTH exist (for pure accuracy)
    intersect_correct = 0

    for _, row in df.iterrows():
        t_raw = row.get(truth_col, "")
        p_raw = row.get(pred_col, "")

        # Check existence (non-empty strings)
        has_truth = pd.notna(t_raw) and str(t_raw).strip() != ""
        has_pred = pd.notna(p_raw) and str(p_raw).strip() != ""

        if has_truth: truth_count += 1
        if has_pred: pred_count += 1

        # Logic: Only check match if both exist
        if has_truth and has_pred:
            intersect_count += 1
            
            t_n = normalize(t_raw, field)
            p_n = normalize(p_raw, field)

            # Match Condition: Exact OR Fuzzy >= 90
            if t_n == p_n or fuzz.ratio(t_n, p_n) >= 90:
                tp += 1
                intersect_correct += 1

    # Metrics Calculation
    # 1. Accuracy (Intersection Match Rate)
    accuracy = (intersect_correct / intersect_count * 100) if intersect_count > 0 else 0.0

    # 2. Precision (TP / Total Preds)
    precision = (tp / pred_count * 100) if pred_count > 0 else 0.0

    # 3. Recall (TP / Total Truths)
    recall = (tp / truth_count * 100) if truth_count > 0 else 0.0

    # 4. F1 Score (2 * (P*R)/(P+R))
    if (precision + recall) > 0:
        f1 = 2 * (precision * recall) / (precision + recall)
    else:
        f1 = 0.0

    print(f"{field:<12} | {accuracy:6.2f}%    | {precision:6.2f}%    | {recall:6.2f}%    | {f1:6.2f}%")
    
    # Store for overall average
    metrics_list.append({
        "acc": accuracy, "prec": precision, "rec": recall, "f1": f1
    })

# Overall Averages
avg_acc = sum(m["acc"] for m in metrics_list) / len(metrics_list)
avg_prec = sum(m["prec"] for m in metrics_list) / len(metrics_list)
avg_rec = sum(m["rec"] for m in metrics_list) / len(metrics_list)
avg_f1 = sum(m["f1"] for m in metrics_list) / len(metrics_list)

print("-" * 65)
print(f"{'OVERALL':<12} | {avg_acc:6.2f}%    | {avg_prec:6.2f}%    | {avg_rec:6.2f}%    | {avg_f1:6.2f}%")
print("\n")
