Rule Based Selection Metric:

| Attribute  | Accuracy | Precision | Recall  | F1 Score |
| :---       | :---     | :---      | :---    | :---     |
| **Name** | 76.47%   | 78.50%    | 74.20%  | 76.29%   |
| **Phone** | 94.12%   | 96.00%    | 92.30%  | 94.11%   |
| **Address** | 100.00%  | 100.00%   | 100.00% | 100.00%  |
| **Categories** | 64.71%   | 68.75%    | 61.10%  | 64.70%   |
| **Website** | 64.71%   | 66.00%    | 63.50%  | 64.72%   |
| ---------- | -------- | --------- | ------- | -------- |
| **OVERALL** | **80.10%** | **81.85%** | **78.22%** | **79.96%** |



Hybrid model:

See model on branch: https://github.com/project-terraforma/stanley-jeffrey-attributesConflation/tree/after-normalization1

Scripts to run order:
1. duckdb -f extract_philadephia.sql
2. duckdb -f extract_santaBarbara.sql 
3. python src/data_preprocessing/new_normalize_philly_sb.py
4. <img width="364" height="294" alt="Screenshot 2025-12-02 at 5 54 23 PM" src="https://github.com/user-attachments/assets/495ca72b-f444-42d5-8fa8-7852c7d60f69" />
   <img width="1158" height="32" alt="Screenshot 2025-12-02 at 5 58 15 PM" src="https://github.com/user-attachments/assets/44acfc73-140a-41db-9b3d-7402dbf1bab2" />
5. python src/data_preprocessing/new_generate_training_pairs.py
6. <img width="601" height="248" alt="Screenshot 2025-12-02 at 5 55 08 PM" src="https://github.com/user-attachments/assets/80f8baf3-1560-4220-b0f7-e406f5a6a5bd" />
   <img width="1578" height="29" alt="image" src="https://github.com/user-attachments/assets/89e41668-8cb0-4a59-b88c-8feea5979120" />
7. python Scripts/ML_train.py
8. <img width="482" height="383" alt="Screenshot 2025-12-02 at 5 55 34 PM" src="https://github.com/user-attachments/assets/48e34cb1-a081-43ec-9dab-3032d4fe41d4" />
9. python Scripts/ML_infer.py
10. <img width="429" height="93" alt="image" src="https://github.com/user-attachments/assets/e7313fa6-386a-4dbe-a6ca-3a5a826ab2db" />
    <img width="1195" height="72" alt="image" src="https://github.com/user-attachments/assets/9423972e-e166-484a-9d32-7819e26d586e" />
    <img width="1499" height="273" alt="image" src="https://github.com/user-attachments/assets/5ab11ba8-53da-4baa-a55d-d4d27f8b5cdf" />
    <img width="1458" height="75" alt="image" src="https://github.com/user-attachments/assets/11526630-2d2e-4129-b450-2198da5d6a44" />
11. python Scripts/assign_place_ids.py
12. <img width="625" height="113" alt="image" src="https://github.com/user-attachments/assets/4403a271-1e37-4e63-8e62-b85f81a23c11" />
    <img width="426" height="97" alt="image" src="https://github.com/user-attachments/assets/ac6ab752-edc0-4e66-9e95-521165132597" />
    <img width="515" height="669" alt="image" src="https://github.com/user-attachments/assets/733c1de4-4c62-40f3-8b03-a13c38b9efe9" />
13. <img width="560" height="77" alt="Screenshot 2025-12-02 at 5 56 17 PM" src="https://github.com/user-attachments/assets/b5e5ab2d-fc44-4ded-8af8-f0f1ddcddb91" />
14. python Scripts/build_yelp_ground_truth.py
15. <img width="559" height="121" alt="image" src="https://github.com/user-attachments/assets/10bedafc-0999-4828-9658-9ae50884727a" />
16. python Scripts/conflate_attributes.py
17. <img width="1463" height="45" alt="image" src="https://github.com/user-attachments/assets/79477f7d-9486-4e4e-bab8-66ac790eb318" />
18. python Scripts/eval_conflation.py
19. <img width="687" height="264" alt="Screenshot 2025-12-02 at 5 56 40 PM" src="https://github.com/user-attachments/assets/60eef15d-d108-49e7-9dcc-1d449bb18618" />



Machine Learning Selection:

| ATTRIBUTE  | ACCURACY | PRECISION | RECALL | F1 SCORE |
| :---       | :---     | :---      | :---   | :---     |
| **name** | 78.00%   | 81.25%    | 75.50% | 78.27%   |
| **phone** | 88.00%   | 91.60%    | 84.60% | 87.96%   |
| **address** | 100.00%  | 100.00%   | 100.00%| 100.00%  |
| **website** | 85.00%   | 82.90%    | 87.20% | 84.99%   |
| **category** | 72.00%   | 75.00%    | 69.20% | 71.98%   |
| ----------------- | ---------- | ---------- | ---------- | ---------- |
| **OVERALL** | **84.60%** | **86.15%** | **83.30%** | **84.64%** |
