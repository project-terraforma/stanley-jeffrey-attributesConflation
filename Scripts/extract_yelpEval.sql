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
    WHERE city IN ('Tucson', 'Tampa', 'Reno') 
    LIMIT 5000
) 
TO 'data/interim/yelp_eval_cities.json'
WITH (FORMAT JSON);