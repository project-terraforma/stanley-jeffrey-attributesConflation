import pandas as pd
import geopandas as gpd
from shapely import wkt
from pathlib import Path

# List of all raw CSV files
csv_files = [
    '../data/raw/omf_boise_full.csv',
    '../data/raw/omf_edmonton_full.csv',
    '../data/raw/omf_indianapolis_full.csv',
#    '../data/raw/omf_las_vegas_full.csv',
 #   '../data/raw/omf_madison_full.csv',
    '../data/raw/omf_nashville_full.csv',
    '../data/raw/omf_neworleans_full.csv',
    '../data/raw/omf_philadelphia_full.csv',
  #  '../data/raw/omf_phoenix_full.csv',
    '../data/raw/omf_pittsburgh_full.csv',
   # '../data/raw/omf_reno_full.csv',
    '../data/raw/omf_santabarbara_full.csv',
    '../data/raw/omf_stlouis_full.csv',
    '../data/raw/omf_tampa_full.csv',
    '../data/raw/omf_tucson_full.csv'
]

# Output directory for GeoJSON
output_dir = Path('../data/raw_geojson')
output_dir.mkdir(parents=True, exist_ok=True)

for csv_file in csv_files:
    df = pd.read_csv(csv_file)

    # Convert WKT 'POINT (lon lat)' strings to shapely geometries
    df['geometry'] = df['geometry'].apply(wkt.loads)

    # Create a GeoDataFrame
    gdf = gpd.GeoDataFrame(df, geometry='geometry', crs="EPSG:4326")

    # Output GeoJSON file
    output_file = output_dir / (Path(csv_file).stem.replace('_full', '') + '.geojson')
    gdf.to_file(output_file, driver='GeoJSON')

    print(f"Converted {csv_file} → {output_file}")

print("All CSVs converted to GeoJSON successfully.")

