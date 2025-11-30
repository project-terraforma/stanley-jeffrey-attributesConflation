# stanley-jeffrey-attributesConflation

## Overview
Our project aims to develop an automated decision logic for **attribute conflation**, selecting the most accurate and up-to-date attributes when multiple data sources represent the same real-world place.  
This process supports the broader **Overture initiative** to unify place data from multiple providers into clean, high-quality records.

---

## Repo Structure


```text
.
├── scripts/
│   ├── rule_based_selectionV1.py
│   ├── ML_based_selectionV1.py
│   ├── place_id_matches.py
│   ├── generate_ground_truth_dataset.py
│   ├── feature_generator.py
│   ├── ML_train.py
│   ├── ML_infer.py
│   ├── ML_eval.py
│   └── extract_*.sql
├── src/
│   ├── data_preprocessing/
│   ├── matching/
│   ├── conflation/
│   └── utils/
├── data/
│   ├── raw/
│   ├── interim/
│   └── processed/
├── models/
├── notebooks/
├── tests/
├── requirements.txt
├── environment.yml
├── README.md
└── LICENSE
```

### Summary of workflow:

- Raw data is in data/raw (original JSON/GeoJSON from sources).
- Normalization happens in src/data_preprocessing → produces cleaned datasets in data/interim.
- Triplet matching is performed by scripts in scripts/, producing yelp_triplet_matches.csv.
- **Attribute conflation:**
- Rule-based in rule_based_selectionV1.py, evaluated with rule_based_accuracy.py.
- ML-based in ML_train.py, ML_infer.py, ML_eval.py, producing ml_predictions.csv.
- SQL scripts in scripts/extract_data/ are used to pull city-specific datasets.
- Final processed datasets (ground truth, conflated, ML predictions) live in data/processed/.

## Project Roadmap

### Phase 1 – Data Preparation
- **Gather data:** Collect place data from multiple sources (Overture, Yelp, Google, etc.) to produce Raw JSON/CSV files.
- **Normalization:** Clean text, standardize casing, remove duplicates, and validate ZIP codes & coordinates to produce Clean DataFrames per source.

### Phase 2 – Entity Matching / Place ID Assignment
- **Blocking / Candidate generation:** Use city, ZIP, or proximity to reduce comparisons and generate candidate record pairs.
- **Matching logic:** Use fuzzy name/address, category, and optional lat/lon proximity to assign a unified `place_id`.
- **Evaluate matches:** Spot-check and compute precision/recall against known matches, producing a Matched dataset with `place_id`.

### Phase 3 – Attribute Conflation
- **Group by `place_id`:** Combine all source records for each place to create a Grouped dataset.
- **Decide attribute logic:** Implement rule-based or ML-based selection for name, address, etc., to define a unified "golden record".
- **Implement conflation algorithm:** Apply logic or a trained model to produce a Conflated dataset.
- **Evaluate accuracy:** Compare to Yelp ground truth to generate metrics and reports.

### Phase 4 – Results & Reporting
- **Performance evaluation:** Quantify accuracy, precision, and recall of rule vs. ML selection.
- **Recommendations:** Suggest a scaling strategy and create a summary report or slide deck.
- **Final deliverables:** Clean labeled dataset, code notebooks, and an evaluation report for the full POC.

---

## Challenges
- **Data availability and coverage:** Some datasets do not cover all geographic areas, limiting evaluation scope.
- **Overpass API limitations:** Encountered query timeouts for large OSM data batches; mitigated by narrowing geographic scopes and using Python tools.
- **Pending sponsor feedback:** Awaiting confirmation from the OMF team regarding OKR alignment and data priorities.

---

## OKRs

### Objective 1: Build a high-quality labeled dataset for attribute conflation
**Key Results:**
- Collect and preprocess ≥2000 pre-matched place records from ≥3 distinct data sources.
- Label ≥90% (≥1800) of collected records with verified ground-truth attributes using Yelp Academic Dataset.
- Achieve ≥95% data consistency across the final labeled dataset via automated field validation.
- Ensure ≤2% missing or invalid attribute values (≤40 records) after final cleaning.
- Complete dataset preprocessing and labeling within 6 weeks of project start.

### Objective 2: Develop and compare algorithms for optimal attribute selection
**Key Results:**
- Implement 2 algorithms: one rule-based and one machine learning model.
- Achieve ≥80% validation accuracy on attribute prediction using a 70/15/15 train/validation/test split.
- Identify and document the top 3 most impactful features or rules contributing to ≥60% of total model importance.
- Limit model inference time to ≤200 ms per record on 2000 records.
- Conduct ≥5 cross-validation folds for reliable performance estimation.

### Objective 3: Evaluate performance and recommend a scalable solution
**Key Results:**
- Evaluate model performance using precision, recall, and F1-score on a test set of 1,500 records.
- Demonstrate ≥17% relative improvement in F1-score of the best-performing model compared to the baseline rule-based approach.
- Conduct 1 live presentation demonstrating algorithm performance and recommending next steps for Overture Places deployment.
- Provide ≥3 recommendations for scaling the solution to datasets exceeding 1 million records.

---

