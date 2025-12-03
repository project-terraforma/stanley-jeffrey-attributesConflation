import pandas as pd
import json
from rapidfuzz import fuzz

# --- CONFIG ---
PREDICTED_FILE = 'data/final_golden_records.json'
GROUND_TRUTH_FILE = 'data/yelp_ground_truth.csv'

def main():
    print("--- Phase 5: Conflation Evaluation ---")

    # 1. Load Your Predictions
    print(f"Loading predictions from {PREDICTED_FILE}...")
    try:
        df_pred = pd.read_json(PREDICTED_FILE, lines=True)
    except ValueError:
        print("❌ Error: Could not read predictions JSON.")
        return
        
    # Safeguard: Ensure columns exist
    if 'place_id' not in df_pred.columns:
        print("❌ Error: 'place_id' column missing in predictions.")
        return

    df_pred = df_pred[['place_id', 'primary_name', 'primary_address']]

    # 2. Load Ground Truth
    print(f"Loading ground truth from {GROUND_TRUTH_FILE}...")
    try:
        df_gt = pd.read_csv(GROUND_TRUTH_FILE)
    except FileNotFoundError:
        print("❌ Error: Ground truth file missing. Run 'build_yelp_ground_truth.py' first!")
        return

    # 3. Merge
    merged = pd.merge(df_gt, df_pred, on='place_id', how='inner')
    
    print(f"Comparing {len(merged)} clusters against Ground Truth...")

    # --- CRITICAL CHECK ---
    if len(merged) == 0:
        print("\n❌ STOPPING: No matches found.")
        print("   Reason: Your 'place_id's don't match between files.")
        print("   Solution: You must re-run the WHOLE pipeline in order so IDs stay consistent:")
        print("     1. python assign_place_ids.py")
        print("     2. python build_yelp_ground_truth.py")
        print("     3. python conflate_attributes.py")
        print("     4. python eval_conflation.py")
        return
    # ----------------------

    # 4. Grading Logic (FIXED)
    def grade_row(row):
        gt_name = str(row['true_name'])
        pred_name = str(row['primary_name'])
        
        # Exact Match
        exact = (gt_name.strip() == pred_name.strip())
        
        # Fuzzy Score
        score = fuzz.ratio(gt_name, pred_name)
        
        # RETURN WITH LABELS so pandas knows where to put them
        return pd.Series([exact, score], index=['exact_match', 'fuzzy_score'])

    # Apply the grading
    grades = merged.apply(grade_row, axis=1)
    
    # Join the grades back to the original dataframe
    merged = pd.concat([merged, grades], axis=1)

    # 5. Calculate Metrics
    exact_accuracy = merged['exact_match'].mean()
    fuzzy_accuracy = (merged['fuzzy_score'] >= 90).mean()

    print("\nResults:")
    print(f"✅ Exact String Match Accuracy: {exact_accuracy:.2%}")
    print(f"✅ Fuzzy Match Accuracy (>90%): {fuzzy_accuracy:.2%}")
    
    if exact_accuracy < 0.99:
        print("\n⚠️  Note: Accuracy is below 100%. Check normalization.")

    print("\nSample Comparisons:")
    print(merged[['true_name', 'primary_name', 'fuzzy_score']].head(5))

if __name__ == "__main__":
    main()