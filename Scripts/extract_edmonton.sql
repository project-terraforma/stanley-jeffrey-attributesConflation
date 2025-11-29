-- extract_edmonton.sql
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
    bbox.xmin BETWEEN -113.75 AND -113.25
    AND bbox.ymin BETWEEN 53.40 AND 53.70
    AND ST_Within(
      geometry,
      ST_GeomFromText('POLYGON((-113.75 53.40, -113.25 53.40, -113.25 53.70, -113.75 53.70, -113.75 53.40))')
    )
)
TO '../data/raw/omf_edmonton.geojson'
WITH (FORMAT GDAL, DRIVER 'GeoJSON');

