-- extract_new_orleans.sql
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
    bbox.xmin BETWEEN -90.20 AND -89.85
    AND bbox.ymin BETWEEN 29.85 AND 30.15
    AND ST_Within(
      geometry,
      ST_GeomFromText('POLYGON((-90.20 29.85, -89.85 29.85, -89.85 30.15, -90.20 30.15, -90.20 29.85))')
    )
)
TO '../data/raw/omf_new_orleans.geojson'
WITH (FORMAT GDAL, DRIVER 'GeoJSON');

