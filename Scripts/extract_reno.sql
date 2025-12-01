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
    -- RENO BOUNDING BOX (Optimization)
    bbox.xmin >= -120.05
    AND bbox.xmax <= -119.70
    AND bbox.ymin >= 39.45
    AND bbox.ymax <= 39.65
    
    -- SECONDARY FILTER (Precise Polygon)
    AND ST_Within(
      geometry,
      ST_GeomFromText(
        -- Order: Bottom-Left -> Bottom-Right -> Top-Right -> Top-Left -> Bottom-Left
        'POLYGON((-120.05 39.45, -119.70 39.45, -119.70 39.65, -120.05 39.65, -120.05 39.45))'
      )
    )
  -- Note: I removed LIMIT 5000 so you get ALL Reno data for your eval set
)
TO 'data/interim/omf_reno.geojson'
WITH (FORMAT GDAL, DRIVER 'GeoJSON');