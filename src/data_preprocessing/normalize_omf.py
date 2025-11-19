import geopandas as gpd
import pandas as pd
import numpy as np
from unidecode import unidecode

def clean_text(x):
    if pd.isnull(x) or str(x).strip() == "":
        return np.nan
    return unidecode(str(x).strip().lower())

def normalize_omf_geojson(input_file: str, output_file: str):
    gdf = gpd.read_file(input_file)
    
    # Use correct column names
    key_fields = ['id', 'name', 'address', 'category', 'geometry']
    gdf = gdf[key_fields]

    text_columns = ['name', 'address', 'category']
    for col in text_columns:
        gdf[col] = gdf[col].apply(clean_text)

    gdf.dropna(subset=['name', 'geometry'], inplace=True)

    # Convert category to list (even if it’s a single string)
    def normalize_category(cat):
        if pd.isnull(cat):
            return []
        if isinstance(cat, list):
            return [clean_text(c) for c in cat]
        return [clean_text(c) for c in str(cat).split(',')]

    gdf['category'] = gdf['category'].apply(normalize_category)

    gdf.to_file(output_file, driver='GeoJSON')
    print(f"Normalized OMF data saved to {output_file}")
    return gdf

# Example usage:
# normalize_omf_geojson('data/raw/omf_phoenix.geojson', 'data/interim/omf_phoenix_normalized.geojson')

