LOAD spatial;
-- INSTALL httpfs; -- Optional if already installed
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
    -- 1. FAST FILTER: Pittsburgh Bounding Box
    -- Longitude: ~ -80.10 to -79.86
    -- Latitude:  ~ 40.36 to 40.50
    bbox.xmin BETWEEN -80.10 AND -79.86
    AND bbox.ymin BETWEEN 40.36 AND 40.50
    
    -- 2. PRECISE FILTER: Exact Polygon 
    AND ST_Within(
      geometry,
      ST_GeomFromText(
        'POLYGON((-80.10 40.36, -79.86 40.36, -79.86 40.50, -80.10 40.50, -80.10 40.36))'
      )
    )
)
TO 'data/interim/omf_pittsburgh.geojson'
WITH (FORMAT GDAL, DRIVER 'GeoJSON');