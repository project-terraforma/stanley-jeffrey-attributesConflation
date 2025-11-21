import pandas as pd
import json
import re
import os

# --- 1. CONFIGURATION ---
# Update these paths to match your actual filenames
FILES = {
    'yelp': '../../data/yelp_philly_sb.json',
    
    # List all your Overture GeoJSONs here
    'omf': [
        {'path': '../../data/raw/omf_santa_barbara.geojson', 'city': 'Santa Barbara'},
        {'path': '../../data/raw/omf_philadelphia.geojson', 'city': 'Philadelphia'}
    ],
    
    # List all your Overpass JSONs here
    'osm': [
        {'path': '../../data/raw/overpass_santaBarbara.geojson', 'city': 'Santa Barbara'},
        {'path': '../../data/raw/overpass_philadelphia.geojson', 'city': 'Philadelphia'} # Uncomment if you have this
    ]
}

OUTPUT_FILE = '../../data/training_data_normalized.json'

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
    
    # CASE 1: GeoJSON FeatureCollection (The likely fix)
    if isinstance(data, dict) and 'features' in data:
        print(f"   -> Detected GeoJSON format ({len(data['features'])} features).")
        source_list = data['features']
        is_geojson = True
        
    # CASE 2: Standard Overpass API
    elif isinstance(data, dict) and 'elements' in data:
        print(f"   -> Detected Overpass API format ({len(data['elements'])} elements).")
        source_list = data['elements']
        is_geojson = False
        
    # CASE 3: DuckDB List Export
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
            # GeoJSON IDs are often in 'id' or properties['@id']
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
            # GeoJSON stores coords in geometry -> coordinates
            geom = item.get('geometry', {})
            coords = geom.get('coordinates')
            geom_type = geom.get('type')
            
            if geom_type == 'Point' and coords:
                lon, lat = coords[0], coords[1]
            elif geom_type == 'Polygon' and coords:
                # Take the first point of the polygon as a rough center
                lon, lat = coords[0][0][0], coords[0][0][1]
        else:
            # Standard OSM Format
            lat = item.get('lat') or item.get('center', {}).get('lat')
            lon = item.get('lon') or item.get('center', {}).get('lon')

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