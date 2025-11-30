-- extract_reno.sql
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
    bbox.xmin BETWEEN -119.90 AND -119.65
    AND bbox.ymin BETWEEN 39.40 AND 39.60
    AND ST_Within(
      geometry,
      ST_GeomFromText('POLYGON((-119.90 39.40, -119.65 39.40, -119.65 39.60, -119.90 39.60, -119.90 39.40))')
    )
)
TO '../data/raw/omf_reno.geojson'
WITH (FORMAT GDAL, DRIVER 'GeoJSON');

