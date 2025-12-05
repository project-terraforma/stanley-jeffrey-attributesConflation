import geopandas as gpd
from pathlib import Path
import pandas as pd

# Paths
interim_dir = Path('../data/interim')

# ------------------------
# Merge all OMF datasets
# ------------------------
omf_files = list(interim_dir.glob('omf_*_normalized.geojson'))
omf_gdfs = [gpd.read_file(f) for f in omf_files]
omf_all = gpd.GeoDataFrame(pd.concat(omf_gdfs, ignore_index=True))

# Optional: standardize CRS
omf_all = omf_all.to_crs(epsg=4326)

# Save merged OMF dataset
omf_all.to_file(interim_dir / 'omf_all_merged.geojson', driver='GeoJSON')
print(f"Merged {len(omf_files)} OMF files → omf_all_merged.geojson")

# ------------------------
# Merge all Overpass datasets
# ------------------------
overpass_files = list(interim_dir.glob('overpass_*_normalized.geojson'))
overpass_gdfs = [gpd.read_file(f) for f in overpass_files]
overpass_all = gpd.GeoDataFrame(pd.concat(overpass_gdfs, ignore_index=True))

# Optional: standardize CRS
overpass_all = overpass_all.to_crs(epsg=4326)

# Save merged Overpass dataset
overpass_all.to_file(interim_dir / 'overpass_all_merged.geojson', driver='GeoJSON')
print(f"Merged {len(overpass_files)} Overpass files → overpass_all_merged.geojson")

