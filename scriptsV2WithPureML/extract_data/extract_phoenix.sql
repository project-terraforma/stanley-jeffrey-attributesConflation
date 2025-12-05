INSTALL spatial;
LOAD spatial;

COPY (
  SELECT
    id,
    names.primary AS name,
    categories.primary AS category,
    addresses[1].freeform AS address,   -- flatten address for GeoJSON
    geometry
  FROM read_parquet(
     's3://overturemaps-us-west-2/release/2025-10-22.0/theme=places/type=place/*',
     hive_partitioning=1
  )
  WHERE ST_Within(
    geometry,
    ST_GeomFromText(
      'POLYGON((-112.3 33.1, -111.9 33.1, -111.9 33.7, -112.3 33.7, -112.3 33.1))'
    )
  )
)
TO 'data/interim/omf_phoenix.geojson'
WITH (FORMAT GDAL, DRIVER 'GeoJSON');

