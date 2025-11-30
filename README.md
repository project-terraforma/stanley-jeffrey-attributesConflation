# stanley-jeffrey-attributesConflation

Overview
Our project aims to develop an automated decision logic for attribute conflation, selecting the most accurate and up-to-date attributes when multiple data sources represent the same real-world place. This process supports the broader Overture initiative to unify place data from multiple providers into clean, high-quality records.


Project Roadmap Summary
Phase 1 – Data Preparation
Gather data: Collect place data from multiple sources (Overture, Yelp, Google, etc.) to produce Raw JSON/CSV files.
Normalization: Clean text, standardize casing, remove duplicates, and validate ZIPs & coordinates to produce Clean DataFrames per source.
Phase 2 – Entity Matching / Place ID Assignment
Blocking / candidate generation: Use city, ZIP, or proximity to reduce comparisons and generate Candidate record pairs.
Matching logic: Use fuzzy name/address, category, and optional lat/lon proximity to get a Unified place_id assigned.
Evaluate matches: Spot-check and compute precision/recall against known matches, resulting in a Matched dataset with place_id.
Phase 3 – Attribute Conflation
Group by place_id: Combine all source records for each place to create a Grouped dataset.
Decide attribute logic: Implement rule-based or ML-based selection for name, address, etc., to define a Unified "golden record" per place.
Implement conflation algorithm: Apply logic or a trained model to produce a Conflated dataset.
Evaluate accuracy: Compare to Yelp ground truth to generate Metrics + report.
Phase 4 – Results & Reporting
Performance evaluation: Quantify the accuracy, precision, and recall of rule vs. ML selection.
Recommendations: Suggest a scaling strategy to create a written summary or slide deck.
Final deliverables: Clean labeled dataset, code notebooks, and an evaluation report for the Full POC package.


Challenges We Faced:
Data availability and coverage: Some datasets do not cover all geographic areas, which limits how broadly we can evaluate our approach.
Overpass API limitations: We’ve encountered Overpass query timeouts while downloading large batches of OpenStreetMap data. We are resolving this by narrowing geographic scopes and using Python tools
Pending sponsor feedback: We’re still waiting on confirmation from the OMF team regarding our OKR alignment and data priorities.



Updated OKRs
Objective 1: Build a high-quality labeled dataset for attribute conflation
Key Results:
Collect and preprocess ≥2000 pre-matched place records from at least 3 distinct data sources.


Label ≥90% (≥1800) of collected records with verified ground-truth attributes using the Yelp Academic Dataset.


Achieve ≥95% data consistency across the final labeled dataset via automated field validation checks.


Ensure ≤2% missing or invalid attribute values (≤40 records) after final data cleaning.


Complete dataset preprocessing and labeling within 6 weeks of project start.


Objective 2: Develop and compare algorithms for optimal attribute selection
Key Results:
Implement 2 algorithms: one rule-based system and one machine learning model.


Achieve ≥80% validation accuracy on attribute prediction using a 70/15/15 train/validation/test split.


Identify and document the top 3 most impactful features or rules contributing to ≥60% of total model importance.


Limit model inference time to ≤200 milliseconds per record on a dataset of 2000 records.


Conduct ≥5 cross-validation folds for reliable performance estimation.


Objective 3: Evaluate performance and recommend a scalable solution
Key Results:
Evaluate model performance using precision, recall, and F1-score on a test set of 1,500 records.


Demonstrate a ≥17% relative improvement in F1-score of the best-performing model compared to the baseline rule-based approach.


Conduct 1 live presentation demonstrating algorithm performance and recommending next steps for Overture Places deployment.


Provide ≥3 next-step recommendations for scaling the solution to datasets exceeding 1 million records.



