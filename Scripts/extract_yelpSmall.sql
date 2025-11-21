COPY (
    SELECT 
        business_id,
        name,
        address,
        city,
        state,
        postal_code,
        latitude,  
        longitude,  
        categories
    FROM read_json_auto('yelp_academic_dataset_business.json')
    WHERE city IN ('Philadelphia', 'Santa Barbara', 'Montecito', 'Goleta', 'Carpinteria') 
) 
TO 'data/interim/yelp_philadephia_santabarbara.json'
WITH (FORMAT JSON);