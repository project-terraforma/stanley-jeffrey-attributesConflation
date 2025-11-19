INSTALL spatial;
LOAD spatial;

COPY (
  SELECT
    id,
    names.primary AS name,
    categories.primary AS category,
    addresses[1].freeform AS address,  -- flatten first address
    geometry
  FROM read_parquet(
     's3://overturemaps-us-west-2/release/2025-10-22.0/theme=places/type=place/*',
     hive_partitioning=1
  )
  WHERE ST_Within(
    geometry,
    ST_GeomFromText(
      'POLYGON((-115.35 35.85, -114.95 35.85, -114.95 36.35, -115.35 36.35, -115.35 35.85))'
    )
  )
)
TO 'data/interim/omf_las_vegas.geojson'
WITH (FORMAT GDAL, DRIVER 'GeoJSON');

