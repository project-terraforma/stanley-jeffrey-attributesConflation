-- extract_boise.sql
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
    bbox.xmin BETWEEN -116.35 AND -116.15
    AND bbox.ymin BETWEEN 43.50 AND 43.70
    AND ST_Within(
      geometry,
      ST_GeomFromText('POLYGON((-116.35 43.50, -116.15 43.50, -116.15 43.70, -116.35 43.70, -116.35 43.50))')
    )
)
TO '../data/raw/omf_boise.geojson'
WITH (FORMAT GDAL, DRIVER 'GeoJSON');

