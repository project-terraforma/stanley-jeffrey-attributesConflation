import pandas as pd

# Load your normalized OMF
omf = pd.read_csv("NORMALIZED_SOURCES.csv")

# Take a random sample of 5000 rows
sample_omf = omf.sample(n=5000, random_state=42)

# Save to a new CSV
sample_omf.to_csv("NORMALIZED_SOURCES_SAMPLE_5000.csv", index=False)

print("Saved 5000-row sample")

