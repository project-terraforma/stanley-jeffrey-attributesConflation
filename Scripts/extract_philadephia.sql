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
    -- PRIMARY OPTIMIZATION: Filter using the 'bbox' struct first.
    -- This enables Parquet "Predicate Pushdown" (skips file downloads).
    bbox.xmin >= -75.28 
    AND bbox.xmax <= -74.96
    AND bbox.ymin >= 39.87 
    AND bbox.ymax <= 40.14
    
    -- SECONDARY FILTER: Precise geometry check.
    AND ST_Within(
      geometry,
      ST_GeomFromText(
        'POLYGON((-75.28 39.87, -74.96 39.87, -74.96 40.14, -75.28 40.14, -75.28 39.87))'
      )
    )
)
TO 'data/interim/omf_philadelphia.geojson'
WITH (FORMAT GDAL, DRIVER 'GeoJSON');