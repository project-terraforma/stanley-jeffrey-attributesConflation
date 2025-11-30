-- extract_santa_barbara.sql
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
    bbox.xmin BETWEEN -119.80 AND -119.60
    AND bbox.ymin BETWEEN 34.38 AND 34.48
    AND ST_Within(
      geometry,
      ST_GeomFromText('POLYGON((-119.80 34.38, -119.60 34.38, -119.60 34.48, -119.80 34.48, -119.80 34.38))')
    )
)
TO '../data/raw/omf_santa_barbara.geojson'
WITH (FORMAT GDAL, DRIVER 'GeoJSON');

