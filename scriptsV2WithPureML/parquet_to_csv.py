import pandas as pd

df = pd.read_parquet("project_b_samples_2k.parquet")
df.to_csv("project_b_samples_2k.csv", index=False)

