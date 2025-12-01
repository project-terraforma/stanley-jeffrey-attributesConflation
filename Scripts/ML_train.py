import pandas as pd
import numpy as np
import joblib
import os
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, accuracy_score, confusion_matrix

# --- CONFIG ---
# 1. TRAIN on the Hard/Manual Philly/SB data you just generated
TRAIN_FILE = 'data/training_pairs_labeled_temp.json' 

# 2. TEST on your small, high-quality "Stress Test"
# CHANGE THIS TO YOUR CSV FILENAME
TEST_FILE = 'data/real_test.csv' 

MODEL_OUTPUT = 'models/entity_matching_model.pkl'

# --- MAIN ---
def main():
    print("--- Phase 3: ML Training (Train on Hard Pairs -> Test on Real Manual Data) ---")
    
    # 1. Load Training Data
    print(f"Loading TRAINING data from {TRAIN_FILE}...")
    if not os.path.exists(TRAIN_FILE):
        print(f"❌ Error: Training file not found at {TRAIN_FILE}")
        return
    df_train = pd.read_json(TRAIN_FILE, lines=True)
    print(f"Loaded {len(df_train)} training pairs.")

    # 2. Load Evaluation Data (YOUR CSV)
    print(f"Loading TEST data from {TEST_FILE}...")
    if not os.path.exists(TEST_FILE):
        print(f"❌ Error: Test file not found at {TEST_FILE}")
        print("   -> Go create 'real_test.csv' with 20 manual rows!")
        return
    
    # LOAD CSV (Because you made it in Excel)
    df_test = pd.read_csv(TEST_FILE)

    # 3. Clean Labels
    # Ensure labels are numbers and valid (0 or 1)
    df_test = df_test.dropna(subset=['label'])
    df_test['label'] = pd.to_numeric(df_test['label'], errors='coerce')
    df_test = df_test[df_test['label'].isin([0, 1])]
    
    print(f"Loaded {len(df_test)} VALID manual test pairs.")

    if len(df_test) == 0:
        print("❌ Error: No valid labels found in real_test.csv.")
        return

    # 4. Align Features (Ensure columns match)
    feature_cols = ['geo_distance', 'name_score', 'address_score']
    
    # Check if 'address_score' is missing (common if you made CSV manually)
    # If missing, we can calculate it on the fly or fill with 0 temporarily
    if 'address_score' not in df_test.columns:
        print("⚠️ Warning: 'address_score' missing in CSV. Filling with 0.5 (Neutral).")
        # In a real scenario, you'd want to calculate this properly!
        df_test['address_score'] = 0.5 

    X_train = df_train[feature_cols]
    y_train = df_train['label']

    X_test  = df_test[feature_cols]
    y_test  = df_test['label']

    print(f"\nTraining on {len(X_train)} samples...")
    print(f"Testing on  {len(X_test)} samples (Your Manual Stress Test)...")

    # 5. Train Model
    print("Training Random Forest Classifier...")
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)

    # 6. Evaluate
    print("\nEvaluating model on YOUR MANUAL DATA...")
    y_pred = model.predict(X_test)
    
    acc = accuracy_score(y_test, y_pred)
    print(f"\n✅ TRUE REAL-WORLD ACCURACY: {acc:.4f}")
    
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred))
    
    print("Confusion Matrix:")
    print(confusion_matrix(y_test, y_pred))

if __name__ == "__main__":
    main()

# import pandas as pd
# import numpy as np
# import joblib
# import os
# from sklearn.ensemble import RandomForestClassifier
# from sklearn.metrics import classification_report, accuracy_score, confusion_matrix

# # --- CONFIG ---
# TRAIN_FILE = 'data/training_pairs_labeled_temp.json' 

# # UPDATE THIS PATH to your new JSON test file
# TEST_FILE = 'data/eval_training_pairs_labeled.json' 

# MODEL_OUTPUT = 'models/entity_matching_model.pkl'

# # --- MAIN ---
# def main():
#     print("--- Phase 3: ML Training (Train on Base -> Test on New Cities) ---")
    
#     # 1. Load Training Data
#     print(f"Loading TRAINING data from {TRAIN_FILE}...")
#     if not os.path.exists(TRAIN_FILE):
#         print(f"❌ Error: Training file not found at {TRAIN_FILE}")
#         return
#     df_train = pd.read_json(TRAIN_FILE, lines=True)
#     print(f"Loaded {len(df_train)} training pairs.")

#     # 2. Load Evaluation Data (JSON)
#     print(f"Loading TEST data from {TEST_FILE}...")
#     if not os.path.exists(TEST_FILE):
#         print(f"❌ Error: Test file not found at {TEST_FILE}")
#         return
    
#     # --- CHANGED: Read JSON instead of CSV ---
#     try:
#         # Try JSON Lines first (standard for this project)
#         df_test = pd.read_json(TEST_FILE, lines=True)
#     except ValueError:
#         # Fallback to standard JSON array if lines=True fails
#         df_test = pd.read_json(TEST_FILE)
    
#     # 3. Validate Labels
#     # We need to ensure the 'label' column exists and isn't empty (NaN)
#     if 'label' not in df_test.columns:
#         print("❌ Error: 'label' column missing in test JSON.")
#         print("   (Did you forget to grade the candidates?)")
#         return

#     # Filter for valid labels (0 or 1)
#     df_test = df_test.dropna(subset=['label'])
#     df_test = df_test[df_test['label'].isin([0, 1])]
    
#     print(f"Loaded {len(df_test)} valid graded test pairs.")

#     if len(df_test) == 0:
#         print("❌ Error: No valid labels found (rows with label 0 or 1).")
#         return

#     # 4. Align Features
#     feature_cols = ['geo_distance', 'name_score', 'address_score']
    
#     # Ensure test file has the columns we need
#     for col in feature_cols:
#         if col not in df_test.columns:
#             print(f"❌ Error: Test JSON is missing column '{col}'")
#             return

#     X_train = df_train[feature_cols]
#     y_train = df_train['label']

#     X_test  = df_test[feature_cols]
#     y_test  = df_test['label']

#     print(f"\nTraining on {len(X_train)} samples (Philly/SB)...")
#     print(f"Testing on  {len(X_test)} samples (New Cities)...")

#     # 5. Train Model
#     print("Training Random Forest Classifier...")
#     model = RandomForestClassifier(n_estimators=100, random_state=42)
#     model.fit(X_train, y_train)

#     # 6. Evaluate
#     print("\nEvaluating model on New Cities...")
#     y_pred = model.predict(X_test)
    
#     acc = accuracy_score(y_test, y_pred)
#     print(f"\n✅ Accuracy on Unseen Cities: {acc:.4f}")
    
#     print("\nClassification Report:")
#     print(classification_report(y_test, y_pred))
    
#     print("Confusion Matrix:")
#     print(confusion_matrix(y_test, y_pred))

#     # 7. Save Model
#     print(f"\nSaving model to {MODEL_OUTPUT}...")
#     joblib.dump(model, MODEL_OUTPUT)
#     print("Done.")

# if __name__ == "__main__":
#     main()