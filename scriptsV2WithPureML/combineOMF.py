import pandas as pd
from pathlib import Path

# Folder containing all your files
DATA_DIR = Path("../data/raw")

# Grab all files that start with "omf_" and end with ".csv"
omf_files = list(DATA_DIR.glob("omf_*_full.csv"))

print("Found files:", omf_files)

dfs = []

for f in omf_files:
    df = pd.read_csv(f)
    df["source_file"] = f.name  # optional: track where each row came from
    dfs.append(df)

# Combine all into one big DataFrame
combined = pd.concat(dfs, ignore_index=True)

# Save combined file
combined.to_csv("OMF_ALL_COMBINED.csv", index=False)

print("Combined dataset saved as OMF_ALL_COMBINED.csv")

