-- 1. Setup
INSTALL spatial; LOAD spatial;
INSTALL httpfs; LOAD httpfs;
SET s3_region='us-west-2';

-- 2. Extraction
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
    -- CORRECTED COLUMN NAMES: xmin, xmax, ymin, ymax
    bbox.xmin >= -119.85 AND bbox.xmax <= -119.64
    AND bbox.ymin >= 34.38 AND bbox.ymax <= 34.48
    
    -- Geometry filter
    AND ST_Within(
      geometry,
      ST_GeomFromText('POLYGON((-119.85 34.38, -119.64 34.38, -119.64 34.48, -119.85 34.48, -119.85 34.38))')
    )
)
TO 'data/interim/omf_santa_barbara.geojson'
WITH (FORMAT GDAL, DRIVER 'GeoJSON');