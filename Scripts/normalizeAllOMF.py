import sys
from pathlib import Path

# Add project root to sys.path so we can import src modules
sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.data_preprocessing.normalize_omf import normalize_omf_geojson

# List of city OMF files
omf_files = [
    'data/raw/omf_phoenix.geojson',
    'data/raw/omf_las_vegas.geojson',
    'data/raw/omf_pittsburgh.geojson',
    'data/raw/omf_madison.geojson'
]

output_dir = Path('data/interim')
output_dir.mkdir(parents=True, exist_ok=True)

for file in omf_files:
    city_name = Path(file).stem.replace('omf_', '')
    output_file = output_dir / f'omf_{city_name}_normalized.geojson'
    print(f"Normalizing {file} → {output_file}")
    normalize_omf_geojson(file, str(output_file))

print("All OMF files normalized successfully.")

