import pandas as pd
import json
from rapidfuzz import fuzz
from sklearn.metrics import precision_score, recall_score, f1_score

# ======================================================
# CONFIGURATION
# ======================================================
GOLD_FILE = "RULE_GOLDEN_DATASET.csv"
PRED_FILE = "RULE_BEST_ATTRIBUTES.csv"

ATTRS = {
    "name":       ("truth_name", "best_name"),
    "phone":      ("truth_phone", "best_phone"),
    "address":    ("truth_address", "best_address"),
    "categories": ("truth_categories", "best_category"),
    "website":    ("truth_website", "best_website"),
}

# ======================================================
# NORMALIZATION HELPERS
# ======================================================
def clean_phone(p):
    if pd.isna(p): return ""
    digits = "".join([d for d in str(p) if d.isdigit()])
    return digits[-10:]

def clean_address(a):
    if pd.isna(a): 
        return ""
    
    # If it's a JSON string (from best_address)
    if str(a).strip().startswith("[") and str(a).strip().endswith("]"):
        try:
            obj = json.loads(a)
            if isinstance(obj, list) and len(obj) > 0:
                a = obj[0].get("freeform", "")
        except json.JSONDecodeError:
            a = str(a)
    else:
        a = str(a)
    
    # Normalize text
    a = a.lower()
    a = a.replace(".", "").replace(",", "")
    a = a.replace("street", "st").replace("road", "rd").replace("avenue", "ave")
    a = a.replace("boulevard", "blvd").replace("drive", "dr").replace("lane", "ln")
    a = a.replace("court", "ct").replace("place", "pl").replace("square", "sq")
    
    # Remove extra numeric suffixes like secondary zip codes
    parts = a.split()
    new_parts = []
    for part in parts:
        if len(part) == 5 and part.isdigit():
            new_parts.append(part)
            break
        new_parts.append(part)
    return " ".join(new_parts)

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
        pass
    return str(c).lower()

def clean_name(n):
    if pd.isna(n): return ""
    n = str(n).lower()
    n = "".join(c if c.isalnum() or c==" " else " " for c in n)
    return " ".join(n.split())

def normalize(v, field):
    if field=="phone": return clean_phone(v)
    if field=="address": return clean_address(v)
    if field=="website": return clean_website(v)
    if field=="categories": return clean_category(v)
    return clean_name(v)

# ======================================================
# MAIN EVALUATION
# ======================================================
def run_eval():
    try:
        gold = pd.read_csv(GOLD_FILE)
        pred = pd.read_csv(PRED_FILE)
    except FileNotFoundError:
        print("Error: Could not find input CSV files.")
        return

    # Merge on place_id
    df = gold.merge(pred, on="place_id", how="inner")
    
    overall_metrics = {"accuracy": [], "precision": [], "recall": [], "f1": []}

    for field, (truth_col, pred_col) in ATTRS.items():
        y_true = []
        y_pred = []

        for _, row in df.iterrows():
            truth = row.get(truth_col, "")
            pred_val = row.get(pred_col, "")

            # Skip if truth is missing
            if pd.isna(truth) or str(truth).strip() == "":
                continue

            # Normalize
            t = normalize(truth, field)
            p = normalize(pred_val, field)

            y_true.append(1)  # Truth exists
            if t == p or fuzz.ratio(t, p) >= 90:
                y_pred.append(1)
            else:
                y_pred.append(0)

        if y_true:
            accuracy = sum(y_pred)/len(y_pred)
            precision = precision_score(y_true, y_pred, zero_division=0)
            recall = recall_score(y_true, y_pred, zero_division=0)
            f1 = f1_score(y_true, y_pred, zero_division=0)

            overall_metrics["accuracy"].append(accuracy)
            overall_metrics["precision"].append(precision)
            overall_metrics["recall"].append(recall)
            overall_metrics["f1"].append(f1)

            print(f"{field}: Accuracy={accuracy*100:.2f}%, Precision={precision*100:.2f}%, Recall={recall*100:.2f}%, F1={f1*100:.2f}%")
        else:
            print(f"{field}: No valid truth data found.")

    # Print overall averages
    if overall_metrics["accuracy"]:
        print("\nOverall Average Metrics:")
        print(f"Accuracy:  {sum(overall_metrics['accuracy'])/len(overall_metrics['accuracy'])*100:.2f}%")
        print(f"Precision: {sum(overall_metrics['precision'])/len(overall_metrics['precision'])*100:.2f}%")
        print(f"Recall:    {sum(overall_metrics['recall'])/len(overall_metrics['recall'])*100:.2f}%")
        print(f"F1 Score:  {sum(overall_metrics['f1'])/len(overall_metrics['f1'])*100:.2f}%")
    else:
        print("No valid truth data found for any attribute.")

if __name__ == "__main__":
    run_eval()

