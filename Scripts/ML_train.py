import pandas as pd
import numpy as np
import joblib
import os
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, accuracy_score, confusion_matrix

# --- CONFIG ---
INPUT_FILE = 'data/training_pairs_labeled.json'
MODEL_OUTPUT = 'models/entity_matching_model.pkl'

# --- MAIN ---
def main():
    print("--- Phase 3: ML Training ---")
    
    # 1. Load Data
    print(f"Loading data from {INPUT_FILE}...")
    if not os.path.exists(INPUT_FILE):
        print(f"❌ Error: File not found at {INPUT_FILE}")
        return

    df = pd.read_json(INPUT_FILE, lines=True)
    print(f"Loaded {len(df)} pairs.")

    # 2. Prepare Features (X) and Target (y)
    # UPDATE: We added 'address_score' to the features list!
    feature_cols = ['geo_distance', 'name_score', 'address_score']
    
    # Check if address_score exists (sanity check)
    if 'address_score' not in df.columns:
        print("⚠️ Warning: 'address_score' not found in data. Using only distance and name.")
        feature_cols = ['geo_distance', 'name_score']

    X = df[feature_cols]
    y = df['label']

    print(f"Features used: {feature_cols}")

    # 3. Split Data (80% Train, 20% Test)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    print(f"Training set: {len(X_train)} samples")
    print(f"Test set:     {len(X_test)} samples")

    # 4. Train Model (Random Forest)
    print("Training Random Forest Classifier...")
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)

    # 5. Evaluate
    print("Evaluating model...")
    y_pred = model.predict(X_test)
    
    acc = accuracy_score(y_test, y_pred)
    print(f"\n✅ Model Accuracy: {acc:.4f}")
    
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred))
    
    print("Confusion Matrix:")
    print(confusion_matrix(y_test, y_pred))

    # 6. Feature Importance
    print("\nFeature Importance:")
    importances = model.feature_importances_
    for name, importance in zip(feature_cols, importances):
        print(f"  {name}: {importance:.4f}")

    # 7. Save Model
    print(f"\nSaving model to {MODEL_OUTPUT}...")
    joblib.dump(model, MODEL_OUTPUT)
    print("Done.")

if __name__ == "__main__":
    main()