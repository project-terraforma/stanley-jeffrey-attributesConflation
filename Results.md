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
10. <img width="401" height="72" alt="Screenshot 2025-12-02 at 5 55 56 PM" src="https://github.com/user-attachments/assets/cc1719d4-bf9f-4871-a16d-4d6cd451b461" />
11. python Scripts/assign_place_ids.py
12. <img width="560" height="77" alt="Screenshot 2025-12-02 at 5 56 17 PM" src="https://github.com/user-attachments/assets/b5e5ab2d-fc44-4ded-8af8-f0f1ddcddb91" />
13. python Scripts/build_yelp_ground_truth.py
14. python Scripts/conflate_attributes.py
15. python Scripts/eval_conflation.py
16. <img width="687" height="264" alt="Screenshot 2025-12-02 at 5 56 40 PM" src="https://github.com/user-attachments/assets/60eef15d-d108-49e7-9dcc-1d449bb18618" />
