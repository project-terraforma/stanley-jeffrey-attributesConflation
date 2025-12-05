INSTALL spatial;
LOAD spatial;

-- optional for S3 access
INSTALL httpfs;
LOAD httpfs;
SET s3_region='us-west-2';

COPY (
  SELECT
      id,
      names.primary AS name,
      categories.primary AS category,
      addresses[1].freeform AS address,
      'Edmonton' AS city,   -- force city

      ARRAY_TO_STRING(phones, '|') AS phones,
      ARRAY_TO_STRING(websites, '|') AS websites,
      ARRAY_TO_STRING(emails, '|') AS emails,
      ARRAY_TO_STRING(socials, '|') AS socials,
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
TO '../../data/raw/omf_edmonton_full.csv'
WITH (HEADER, DELIMITER ',');

