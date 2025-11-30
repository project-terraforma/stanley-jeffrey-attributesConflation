-- extract_philadelphia.sql
LOAD spatial;
INSTALL httpfs;
LOAD httpfs;
SET s3_region='us-west-2';

COPY (
  SELECT id,
         names.primary AS name,
         categories.primary AS category,
         addresses[1].freeform AS address,
         geometry
  FROM read_parquet(
      's3://overturemaps-us-west-2/release/2025-10-22.0/theme=places/type=place/*',
      hive_partitioning=1
  )
  WHERE 
    bbox.xmin BETWEEN -75.30 AND -74.95
    AND bbox.ymin BETWEEN 39.85 AND 40.15
    AND ST_Within(
      geometry,
      ST_GeomFromText('POLYGON((-75.30 39.85, -74.95 39.85, -74.95 40.15, -75.30 40.15, -75.30 39.85))')
    )
)
TO '../data/raw/omf_philadelphia.geojson'
WITH (FORMAT GDAL, DRIVER 'GeoJSON');

