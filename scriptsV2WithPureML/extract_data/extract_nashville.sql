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
      'Nashville' AS city,   -- force city
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
    bbox.xmin BETWEEN -86.95 AND -86.55
    AND bbox.ymin BETWEEN 36.00 AND 36.35
    AND ST_Within(
      geometry,
      ST_GeomFromText('POLYGON((-86.95 36.00, -86.55 36.00, -86.55 36.35, -86.95 36.35, -86.95 36.00))')
    )
)
TO '../../data/raw/omf_nashville_full.csv'
WITH (HEADER, DELIMITER ',');

