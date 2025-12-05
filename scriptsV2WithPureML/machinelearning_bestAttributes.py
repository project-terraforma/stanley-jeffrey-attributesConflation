import pandas as pd
import os, warnings
from pathlib import Path
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import LabelEncoder
from joblib import dump, load

warnings.filterwarnings("ignore")
BASE = Path(__file__).resolve().parent.parent
ATTRS = ["name", "phone", "address", "website", "categories"]
PROVIDERS = ["foursquare", "meta", "microsoft"]

# --- HELPERS ---
def clean(x): return str(x).lower().strip() if pd.notna(x) else ""
def clean_src(s):
    s = clean(s)
    return "microsoft" if "msft" in s else "foursquare" if "four" in s else "meta" if "meta" in s else s

def get_features(row, attr, is_train=False):
    """Builds numerical feature vector for a specific attribute."""
    f = {}
    truth = clean(row.get(f"truth_{attr}")) if is_train else None
    for p in PROVIDERS:
        val = clean(row.get(f"{p}_{attr}"))
        f[f"{p}_present"] = 1 if val else 0
        # Train: overlap with Truth. Inference: length proxy (richness).
        f[f"{p}_sim"] = len(set(val.split()) & set(truth.split())) if is_train else len(val.split())
        f[f"{p}_exact"] = 1 if is_train and val == truth else 0
    return f

# --- CORE LOGIC ---
def train():
    print("=== Training Models ===")
    try:
        df = pd.read_csv("ML_GOLDEN_DATASET.csv")
    except FileNotFoundError:
        print("Error: ML_GOLDEN_DATASET_TEMPLATE.csv not found.")
        return

    os.makedirs("models", exist_ok=True)
    
    for attr in ATTRS:
        # Check if columns exist before training
        if f"truth_{attr}_source" not in df.columns:
            print(f"Skipping {attr}: Column 'truth_{attr}_source' missing.")
            continue

        # Filter rows where we actually have a truth source label
        valid_rows = df[df[f"truth_{attr}_source"].notna() & (df[f"truth_{attr}_source"] != "")]
        if valid_rows.empty: continue
            
        X = pd.DataFrame([get_features(r, attr, True) for _, r in valid_rows.iterrows()])
        y = valid_rows[f"truth_{attr}_source"].apply(clean).values
        
        if len(set(y)) < 2:
             print(f"  {attr}: Not enough classes to train (needs >1 source type). Skipping.")
             continue

        le = LabelEncoder()
        y_enc = le.fit_transform(y)
        
        # Competiton: LogReg vs Random Forest
        models = [LogisticRegression(), RandomForestClassifier(n_estimators=100, random_state=42)]
        best = max(models, key=lambda m: m.fit(X, y_enc).score(X, y_enc))
        
        dump({"model": best, "le": le}, f"models/{attr}_model.joblib")
        print(f"  {attr}: Trained {best.__class__.__name__}")

def infer():
    print("\n=== Running Inference ===")
    
    # 1. Load and Fix Raw Data
    csv_path = "NORMALIZED_SOURCES.csv"
    if not csv_path.exists():
        csv_path = "NORMALIZED_SOURCES.csv" # try local directory
        if not os.path.exists(csv_path):
             print(f"Error: {csv_path} not found.")
             return

    raw = pd.read_csv(csv_path)
    
    # --- ROBUSTNESS FIX ---
    # Map common variations of column names
    col_map = {"addr": "address", "category": "categories", "web": "website"}
    raw = raw.rename(columns=col_map)
    
    # Ensure all expected ATTRS exist in the DataFrame
    for attr in ATTRS:
        if attr not in raw.columns:
            print(f"Warning: Column '{attr}' missing in input CSV. Filling with empty strings.")
            raw[attr] = ""
    # ----------------------

    raw["src"] = raw["source"].apply(clean_src)
    
    # Pivot creates columns like ('name', 'meta'), ('phone', 'microsoft')
    wide = raw.pivot_table(index="place_id", columns="src", values=ATTRS, aggfunc="first")
    
    # Flatten MultiIndex columns: e.g. ('address', 'meta') -> 'meta_address'
    # Note: pivot_table columns are (Attribute, Source)
    wide.columns = [f"{col[1]}_{col[0]}" for col in wide.columns] 
    wide = wide.reset_index()

    results = []
    for _, row in wide.iterrows():
        res = {"place_id": row["place_id"]}
        votes = []
        
        for attr in ATTRS:
            try:
                # Load Model & Predict
                model_path = f"models/{attr}_model.joblib"
                if not os.path.exists(model_path): continue

                bundle = load(model_path)
                feats = pd.DataFrame([get_features(row, attr, False)]) # Build features from wide row
                pred_src = bundle["le"].inverse_transform(bundle["model"].predict(feats))[0]
                
                # Pick Value (Fallback to first available if prediction is empty)
                val = row.get(f"{pred_src}_{attr}")
                if pd.isna(val) or val == "":
                    for p in PROVIDERS:
                        v = row.get(f"{p}_{attr}")
                        if pd.notna(v) and v != "": val = v; break
                
                res[f"best_{attr}"] = val
                res[f"{attr}_source"] = pred_src
                votes.append(pred_src)
            except Exception as e: 
                # print(f"Error predicting {attr}: {e}")
                pass
            
        if votes: res["best_source"] = max(set(votes), key=votes.count)
        results.append(res)

    out = pd.DataFrame(results)
    
    # --- COMPATIBILITY FIX ---
    # The evaluation script expects 'best_category' (singular), but we generated 'best_categories' (plural).
    # We rename it here to ensure the grading script finds the column.
    rename_map = {
        "best_categories": "best_category",
        "categories_source": "category_source"
    }
    out = out.rename(columns=rename_map)
    # -------------------------
    
    out.to_csv("ML_BEST_ATTRIBUTES.csv", index=False)
    print(f"Done. Wrote {len(out)} rows to ML_BEST_ATTRIBUTES.csv")

if __name__ == "__main__":
    train()
    infer()
