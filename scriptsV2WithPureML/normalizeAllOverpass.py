import sys
from pathlib import Path
import pandas as pd
import numpy as np
from unidecode import unidecode
import geopandas as gpd

def clean_text(x):
    if pd.isnull(x) or str(x).strip() == "":
        return np.nan
    return unidecode(str(x).strip().lower())

def get_id(row):
    if isinstance(row, dict) and "@id" in row:
        return row["@id"]
    return None

def get_name(row):
    if isinstance(row, dict) and "name" in row:
        return clean_text(row["name"])
    return None

def get_address(row):
    if isinstance(row, dict):
        if "addr:full" in row and row["addr:full"]:
            return clean_text(row["addr:full"])
        parts = []
        for key in ["addr:housenumber", "addr:street", "addr:city", "addr:state", "addr:postcode"]:
            if key in row and row[key]:
                parts.append(str(row[key]))
        if parts:
            return clean_text(", ".join(parts))
    return np.nan

def get_category(row):
    cats = []
    keys = ["amenity", "shop", "office", "tourism", "craft", "service", "building", "brand"]
    if isinstance(row, dict):
        for k in keys:
            if row.get(k):
                cats.append(clean_text(row[k]))
    return cats
'''
def normalize_overpass_geojson(input_file: str, output_file: str):
    gdf = gpd.read_file(input_file)

    # Extract properties: if GeoPandas flattened them, use columns; else use dict
    if "properties" in gdf.columns:
        props = gdf["properties"]
    else:
        props = gdf.apply(lambda row: row.to_dict(), axis=1)

    # Create normalized columns
    gdf["id"] = props.apply(get_id)
    gdf["name"] = props.apply(get_name)
    gdf["address"] = props.apply(get_address)
    gdf["category"] = props.apply(get_category)

    # Keep only standard columns
    gdf = gdf[["id", "name", "address", "category", "geometry"]]

    # Drop rows missing required fields
    gdf.dropna(subset=["name", "geometry"], inplace=True)

    # Save
    gdf.to_file(output_file, driver="GeoJSON")
    print(f"Normalized Overpass data saved to {output_file}")
    return gdf
'''
import geopandas as gpd

def normalize_overpass_geojson(input_file: str, output_file: str):
    # Read GeoJSON normally (ignore_invalid won't work)
    gdf = gpd.read_file(input_file)

    # Filter out invalid geometries
    gdf = gdf[gdf.geometry.notna()]  # Remove nulls
    gdf = gdf[gdf.geometry.is_valid | gdf.geometry.is_empty]  # Keep only valid or empty

    # Extract properties safely
    if "properties" in gdf.columns:
        props = gdf["properties"]
    else:
        props = gdf.apply(lambda row: row.to_dict(), axis=1)

    # Normalization logic
    gdf["id"] = props.apply(get_id)
    gdf["name"] = props.apply(get_name)
    gdf["address"] = props.apply(get_address)
    gdf["category"] = props.apply(get_category)

    gdf = gdf[["id", "name", "address", "category", "geometry"]]
    gdf.dropna(subset=["name", "geometry"], inplace=True)

    gdf.to_file(output_file, driver="GeoJSON")
    print(f"Normalized Overpass data saved to {output_file}")
    return gdf


if __name__ == "__main__":
    # List of all 15 Overpass city files
    overpass_files = [
        '../data/raw/overpass_boise_full.geojson',
        '../data/raw/overpass_edmonton_full.geojson',
        '../data/raw/overpass_indianapolis_full.geojson',
        '../data/raw/overpass_nashville_full.geojson',
        '../data/raw/overpass_neworleans_full.geojson',
        '../data/raw/overpass_philadelphia_full.geojson',
        '../data/raw/overpass_pittsburgh_full.geojson',
#        '../data/raw/overpass_santabarbara.geojson',
        '../data/raw/overpass_stlouis_full.geojson',
        '../data/raw/overpass_tampa_full.geojson',
        '../data/raw/overpass_tucson_full.geojson'
    ]

    output_dir = Path('../data/interim')
    output_dir.mkdir(parents=True, exist_ok=True)

    for file in overpass_files:
        city_name = Path(file).stem.replace('overpass_', '')
        output_file = output_dir / f'overpass_{city_name}_normalized.geojson'
        print(f"Normalizing {file} → {output_file}")
        normalize_overpass_geojson(file, str(output_file))

    print("All Overpass files normalized successfully.")

