LOAD spatial;
INSTALL httpfs; -- Ensure this is installed
LOAD httpfs;
SET s3_region='us-west-2';

COPY (
  SELECT
    id,
    names.primary AS name,
    categories.primary AS category,
    addresses[1].freeform AS address,
    geometry
  FROM read_parquet(
     's3://overturemaps-us-west-2/release/2025-10-22.0/theme=places/type=place/*',
     hive_partitioning=1
  )
  WHERE 
    -- 1. THE FAST FILTER: Rough bounding box using numeric columns
    -- This prevents downloading data for the rest of the world.
    bbox.xmin BETWEEN -89.50 AND -89.30
    AND bbox.ymin BETWEEN 43.00 AND 43.18
    
    -- 2. THE PRECISE FILTER: Exact polygon shape
    -- Now this only runs on the tiny subset of data that passed the filter above.
    AND ST_Within(
      geometry,
      ST_GeomFromText(
        'POLYGON((-89.50 43.00, -89.30 43.00, -89.30 43.18, -89.50 43.18, -89.50 43.00))'
      )
    )
)
TO 'data/interim/omf_madison.geojson'
WITH (FORMAT GDAL, DRIVER 'GeoJSON');
