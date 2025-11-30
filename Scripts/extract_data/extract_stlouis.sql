-- extract_st_louis.sql
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
    bbox.xmin BETWEEN -90.40 AND -90.10
    AND bbox.ymin BETWEEN 38.50 AND 38.75
    AND ST_Within(
      geometry,
      ST_GeomFromText('POLYGON((-90.40 38.50, -90.10 38.50, -90.10 38.75, -90.40 38.75, -90.40 38.50))')
    )
)
TO '../data/raw/omf_st_louis.geojson'
WITH (FORMAT GDAL, DRIVER 'GeoJSON');

