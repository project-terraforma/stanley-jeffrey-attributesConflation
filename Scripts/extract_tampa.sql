-- 1. Setup
INSTALL spatial; LOAD spatial;
INSTALL httpfs; LOAD httpfs;
SET s3_region='us-west-2';

-- 2. Execution
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
    -- TAMPA BOUNDING BOX
    bbox.xmin >= -82.58
    AND bbox.xmax <= -82.38
    AND bbox.ymin >= 27.88
    AND bbox.ymax <= 28.12
    
    -- SECONDARY FILTER
    AND ST_Within(
      geometry,
      ST_GeomFromText(
        'POLYGON((-82.58 27.88, -82.38 27.88, -82.38 28.12, -82.58 28.12, -82.58 27.88))'
      )
    )
  -- Removed LIMIT so you get the full evaluation set
)
TO 'data/interim/omf_tampa.geojson'
WITH (FORMAT GDAL, DRIVER 'GeoJSON');