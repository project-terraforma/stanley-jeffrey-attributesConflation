import pandas as pd

# Replace 'path/to/your/file.parquet' with the actual path to your Parquet file
df = pd.read_parquet("/Users/stanleyshen/Downloads/project_b_samples_2k.parquet")


pd.set_option('display.max_colwidth', None)

# Display the first few rows
print(df.head(10))
# Display the first few rows of the DataFrame
