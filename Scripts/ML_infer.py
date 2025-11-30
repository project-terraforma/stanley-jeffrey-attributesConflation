import pandas as pd
import joblib
import os

# --- CONFIG ---
# We run inference on the generated pairs file
INPUT_FILE = 'data/training_pairs_labeled.json'
MODEL_FILE = 'models/entity_matching_model.pkl'
OUTPUT_FILE = 'data/processed/ml_predictions.csv'

def main():
    print("--- Phase 4: ML Inference ---")

    # 1. Load Model
    if not os.path.exists(MODEL_FILE):
        print(f"❌ Error: Model {MODEL_FILE} not found. Run ML_train.py first.")
        return
    print(f"Loading model from {MODEL_FILE}...")
    model = joblib.load(MODEL_FILE)

    # 2. Load Data
    print(f"Loading data from {INPUT_FILE}...")
    df = pd.read_json(INPUT_FILE, lines=True)
    
    # 3. Predict
    # UPDATE: We must use the EXACT same features the model was trained on
    feature_cols = ['geo_distance', 'name_score', 'address_score']
    
    # Check if address_score exists (just in case)
    if 'address_score' not in df.columns:
        print("⚠️ Warning: 'address_score' missing. Filling with 0 (may affect accuracy).")
        df['address_score'] = 0
        
    X = df[feature_cols]

    print("Running predictions...")
    
    # "predict" gives 0 or 1
    df['ml_prediction'] = model.predict(X)
    
    # "predict_proba" gives the CONFIDENCE (0.0 to 1.0)
    # This is the "Magic Number" for your final conflation logic
    df['ml_confidence'] = model.predict_proba(X)[:, 1]

    # 4. Filter and Sort
    # Sort by confidence so the best matches are at the top
    matches = df.copy() 
    matches = matches.sort_values(by='ml_confidence', ascending=False)

    # 5. Export
    print(f"Found {len(matches)} pairs processed.")
    
# UPDATE THIS LIST in ML_inference.py
    out_cols = [
        'ml_confidence', 
        'ml_prediction',
        'id_left', 'source_left', 'name_norm_left', 'address_left',   # <--- Added id_left
        'id_right', 'source_right', 'name_norm_right', 'address_right', # <--- Added id_right
        'geo_distance', 'name_score', 'address_score'
    ]
    
    # Only keep columns that actually exist in the dataframe
    final_out_cols = [c for c in out_cols if c in matches.columns]
    
    matches[final_out_cols].to_csv(OUTPUT_FILE, index=False)
    print(f"✅ Results saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()