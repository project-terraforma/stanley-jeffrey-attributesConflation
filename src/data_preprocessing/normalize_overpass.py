import geopandas as gpd
import pandas as pd
import numpy as np
from unidecode import unidecode

def clean_text(x):
    if pd.isnull(x) or str(x).strip() == "":
        return np.nan
    return unidecode(str(x).strip().lower())

def extract_category(props):
    keys = ["amenity", "shop", "office", "tourism", "craft", "service"]
    
    cats = []
    for k in keys:
        if k in props and props[k]:
            cats.append(clean_text(props[k]))
    return cats

def extract_address(props):
    if "addr:full" in props:
        return clean_text(props["addr:full"])
    
    parts = []
    for key in ["addr:housenumber", "addr:street", "addr:city", "addr:state"]:
        if key in props:
            parts.append(str(props[key]))
    if parts:
        return clean_text(" ".join(parts))
    
    return np.nan

def normalize_overpass_geojson(input_file: str, output_file: str):
    gdf = gpd.read_file(input_file)

    # OSM stores metadata in a "properties" dict
    props = gdf["properties"]

    gdf["id"] = props.apply(lambda p: f"{p.get('@type', 'osm')}_{p.get('@id')}")
    gdf["name"] = props.apply(lambda p: clean_text(p.get("name")))
    gdf["address"] = props.apply(extract_address)
    gdf["category"] = props.apply(extract_category)

    # Keep minimal schema
    gdf = gdf[["id", "name", "address", "category", "geometry"]]

    # Drop rows missing required fields
    gdf.dropna(subset=["name", "geometry"], inplace=True)

    gdf.to_file(output_file, driver='GeoJSON')
    print(f"Normalized Overpass data saved to {output_file}")

    return gdf

