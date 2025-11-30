import pandas as pd
import json
import re
import os

# --- 1. CONFIGURATION ---
# Paths are relative to the project root (stanley-jeffrey-attributesConflation)
FILES = {
    'yelp': 'data/yelp_philly_sb.json',
    
    'omf': [
        {'path': 'data/raw/omf_santa_barbara.geojson', 'city': 'Santa Barbara'},
        {'path': 'data/raw/omf_philadelphia.geojson', 'city': 'Philadelphia'}
    ],
    
    'osm': [
        {'path': 'data/raw/overpass_santaBarbara.geojson', 'city': 'Santa Barbara'},
        {'path': 'data/raw/overpass_philadelphia.geojson', 'city': 'Philadelphia'} 
    ]
}

OUTPUT_FILE = 'data/interim/normalized_p_sb_data.json'

# --- 2. HELPER FUNCTIONS ---

def clean_text(text):
    """
    Standardizes text: lowercase, removes special chars, strips whitespace.
    Example: "Starbucks Coffee #123!" -> "starbucks coffee 123"
    """
    if text is None or not isinstance(text, str):
        return ""
    # Remove punctuation/special chars (keep alphanumeric and spaces)
    text = re.sub(r'[^\w\s]', '', text) 
    # Collapse multiple spaces into one
    text = re.sub(r'\s+', ' ', text)
    return text.lower().strip()

def load_yelp(filepath):
    """Loads Yelp JSON (created by DuckDB)."""
    if not os.path.exists(filepath):
        print(f"⚠️ Warning: Yelp file not found at {filepath}")
        return pd.DataFrame()
    
    print(f"Loading Yelp: {filepath}...")
    # DuckDB exports are usually line-delimited or standard JSON. 
    # lines=True works for line-delimited. If it fails, try lines=False.
    try:
        df = pd.read_json(filepath, lines=True)
    except ValueError:
        df = pd.read_json(filepath)

    df['source'] = 'yelp'
    # Rename columns to match Golden Schema
    df = df.rename(columns={
        'business_id': 'id', 
        'categories': 'category_raw',
        'latitude': 'lat',
        'longitude': 'lon'
    })
    return df

def load_omf(file_info):
    """Loads Overture Maps GeoJSON."""
    filepath = file_info['path']
    city_label = file_info['city']
    
    if not os.path.exists(filepath):
        print(f"⚠️ Warning: OMF file not found at {filepath}")
        return pd.DataFrame()

    print(f"Loading OMF: {filepath}...")
    with open(filepath, 'r') as f:
        data = json.load(f)

    rows = []
    for feature in data.get('features', []):
        props = feature.get('properties', {})
        geom = feature.get('geometry', {})
        
        # Overture geometry is usually [lon, lat]
        coords = geom.get('coordinates', [None, None])
        
        rows.append({
            'id': props.get('id'),
            'source': 'omf',
            'name': props.get('name'),
            'address': props.get('address'),
            'city': city_label, # Use the explicit city label we defined
            'lat': coords[1],
            'lon': coords[0],
            'category_raw': props.get('category')
        })
    return pd.DataFrame(rows)

def load_osm(file_info):
    filepath = file_info['path']
    city_label = file_info['city']

    if not os.path.exists(filepath):
        print(f"⚠️ Warning: OSM file not found at {filepath}")
        return pd.DataFrame()

    print(f"Loading OSM: {filepath}...")
    
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
    except Exception as e:
        print(f"❌ Error reading JSON: {e}")
        return pd.DataFrame()

    rows = []
    
    # --- DETECT FORMAT ---
    if isinstance(data, dict) and 'features' in data:
        print(f"   -> Detected GeoJSON format ({len(data['features'])} features).")
        source_list = data['features']
        is_geojson = True
    elif isinstance(data, dict) and 'elements' in data:
        print(f"   -> Detected Overpass API format ({len(data['elements'])} elements).")
        source_list = data['elements']
        is_geojson = False
    elif isinstance(data, list):
        print(f"   -> Detected List format ({len(data)} items).")
        source_list = data
        is_geojson = False
    else:
        print("❌ Unknown JSON format. Could not find 'features' or 'elements'.")
        return pd.DataFrame()

    # --- EXTRACT DATA ---
    for item in source_list:
        # 1. Get Tags/Properties
        if is_geojson:
            tags = item.get('properties', {})
            osm_id = item.get('id') or tags.get('@id')
        else:
            tags = item.get('tags', {})
            osm_id = item.get('id')

        # 2. Filter (Must have a name)
        name = tags.get('name')
        if not name:
            continue
            
        # 3. Construct Address
        addr_parts = [tags.get('addr:housenumber'), tags.get('addr:street')]
        addr_str = " ".join([p for p in addr_parts if p])

        # 4. Get Category
        cat = tags.get('amenity') or tags.get('shop') or tags.get('tourism') or tags.get('building') or 'unknown'
        
        # 5. Get Coordinates
        lat, lon = None, None
        
        if is_geojson:
            geom = item.get('geometry', {})
            coords = geom.get('coordinates')
            geom_type = geom.get('type')
            
            if geom_type == 'Point' and coords:
                lon, lat = coords[0], coords[1]
            elif geom_type == 'Polygon' and coords:
                lon, lat = coords[0][0][0], coords[0][0][1]
        else:
            lat = item.get('lat') or item.get('center', {}).get('lat')
            lon = item.get('lon') or item.get('center', {}).get('lon')

        # --- [NEW CODE STARTS HERE] ---
        # 6. FILTER OUT BAD TYPES
        # If we couldn't find coordinates (e.g. LineStrings), skip it.
        if lat is None or lon is None:
            continue
            
        # If the category looks like a train route, boundary, or highway, skip it.
        if tags.get('route') or tags.get('boundary') or tags.get('highway'):
            continue
        # --- [NEW CODE ENDS HERE] ---

        rows.append({
            'id': f"osm_{osm_id}",
            'source': 'osm',
            'name': name,
            'address': addr_str,
            'city': city_label,
            'lat': lat,
            'lon': lon,
            'category_raw': cat
        })

    print(f"   -> Successfully extracted {len(rows)} POIs.")
    return pd.DataFrame(rows)

# --- 3. MAIN EXECUTION ---

def main():
    dfs = []

    # 1. Load Yelp
    dfs.append(load_yelp(FILES['yelp']))

    # 2. Load all OMF files
    for omf_file in FILES['omf']:
        dfs.append(load_omf(omf_file))

    # 3. Load all OSM files
    for osm_file in FILES['osm']:
        dfs.append(load_osm(osm_file))

    # 4. Merge
    print("Merging datasets...")
    if not dfs:
        print("❌ Error: No data loaded.")
        return
        
    df_all = pd.concat(dfs, ignore_index=True)
    print(f"Total Raw Records: {len(df_all)}")

    # 5. Normalize Columns
    print("Normalizing text columns...")
    df_all['name_norm'] = df_all['name'].apply(clean_text)
    df_all['address_norm'] = df_all['address'].apply(clean_text)

    # Fill NaNs for cleaner JSON
    df_all['category_raw'] = df_all['category_raw'].fillna('unknown')
    df_all['city'] = df_all['city'].fillna('')
    df_all['address_norm'] = df_all['address_norm'].fillna('')

    # 6. Select Final Schema
    final_cols = ['id', 'source', 'name_norm', 'address_norm', 'lat', 'lon', 'category_raw', 'city']
    
    # Ensure all columns exist (adds them as empty if missing)
    for col in final_cols:
        if col not in df_all.columns:
            df_all[col] = None
            
    df_final = df_all[final_cols]

    # 7. Export to NDJSON (Line-Delimited)
    print(f"Exporting to {OUTPUT_FILE}...")
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    
    df_final.to_json(OUTPUT_FILE, orient='records', lines=True)
    
    print("✅ Success! Preview of data:")
    print(df_final[['source', 'name_norm', 'city']].head(5))

if __name__ == "__main__":
    main()