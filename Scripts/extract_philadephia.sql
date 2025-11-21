-- 1. Install/Load required extensions for S3 and GeoJSON
INSTALL spatial;
LOAD spatial;
INSTALL httpfs;
LOAD httpfs;

-- 2. Configure S3 Region (Required for Overture bucket)
SET s3_region='us-west-2';

-- 3. Execute the extraction
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
  WHERE ST_Within(
    geometry,
    ST_GeomFromText(
      -- Bounding Box for Philadelphia, PA
      -- (West: -75.28, East: -74.96, South: 39.87, North: 40.14)
      'POLYGON((-75.28 39.87, -74.96 39.87, -74.96 40.14, -75.28 40.14, -75.28 39.87))'
    )
  )
)
TO 'data/interim/omf_philadelphia.geojson'
WITH (FORMAT GDAL, DRIVER 'GeoJSON');
