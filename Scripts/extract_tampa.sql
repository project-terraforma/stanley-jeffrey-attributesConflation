-- extract_tampa.sql
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
    bbox.xmin BETWEEN -82.60 AND -82.30
    AND bbox.ymin BETWEEN 27.80 AND 28.10
    AND ST_Within(
      geometry,
      ST_GeomFromText('POLYGON((-82.60 27.80, -82.30 27.80, -82.30 28.10, -82.60 28.10, -82.60 27.80))')
    )
)
TO '../data/raw/omf_tampa.geojson'
WITH (FORMAT GDAL, DRIVER 'GeoJSON');

