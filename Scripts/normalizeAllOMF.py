import sys
from pathlib import Path

# Add project root so imports work
sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.data_preprocessing.normalize_omf import normalize_omf_geojson

# List of all OMF raw files (relative to the scripts/ directory)
omf_files = [
    '../data/raw/omf_boise.geojson',
    '../data/raw/omf_edmonton.geojson',
    '../data/raw/omf_indianapolis.geojson',
    '../data/raw/omf_las_vegas.geojson',
    '../data/raw/omf_madison.geojson',
    '../data/raw/omf_nashville.geojson',
    '../data/raw/omf_new_orleans.geojson',
    '../data/raw/omf_philadelphia.geojson',
    '../data/raw/omf_phoenix.geojson',
    '../data/raw/omf_pittsburgh.geojson',
    '../data/raw/omf_reno.geojson',
    '../data/raw/omf_santa_barbara.geojson',
    '../data/raw/omf_st_louis.geojson',
    '../data/raw/omf_tampa.geojson',
    '../data/raw/omf_tucson.geojson'
]

# Output directory (also relative to scripts/)
output_dir = Path('../data/interim')
output_dir.mkdir(parents=True, exist_ok=True)

for file in omf_files:
    city_name = Path(file).stem.replace('omf_', '')
    output_file = output_dir / f'omf_{city_name}_normalized.geojson'
    print(f"Normalizing {file} → {output_file}")
    normalize_omf_geojson(file, str(output_file))

print("All OMF files normalized successfully.")

