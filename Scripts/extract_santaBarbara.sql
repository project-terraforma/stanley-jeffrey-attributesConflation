-- 1. Install/Load required extensions for S3 and GeoJSON
INSTALL spatial;
LOAD spatial;
INSTALL httpfs;
LOAD httpfs;

-- 2. Configure S3 Region (Overture is in us-west-2)
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
      'POLYGON((-119.85 34.38, -119.64 34.38, -119.64 34.48, -119.85 34.48, -119.85 34.38))'
    )
  )
)
TO 'data/interim/omf_santa_barbara.geojson'
WITH (FORMAT GDAL, DRIVER 'GeoJSON');