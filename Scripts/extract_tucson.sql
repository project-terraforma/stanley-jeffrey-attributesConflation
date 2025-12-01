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
    -- TUCSON BOUNDING BOX
    bbox.xmin >= -111.08
    AND bbox.xmax <= -110.72
    AND bbox.ymin >= 32.10
    AND bbox.ymax <= 32.35
    
    -- SECONDARY FILTER
    AND ST_Within(
      geometry,
      ST_GeomFromText(
        'POLYGON((-111.08 32.10, -110.72 32.10, -110.72 32.35, -111.08 32.35, -111.08 32.10))'
      )
    )
  -- Removed LIMIT so you get the full evaluation set
)
TO 'data/interim/omf_tucson.geojson'
WITH (FORMAT GDAL, DRIVER 'GeoJSON');