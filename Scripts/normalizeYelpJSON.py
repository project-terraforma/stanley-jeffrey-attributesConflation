from pathlib import Path
import pandas as pd
import numpy as np
from unidecode import unidecode

def clean_text(x):
    if pd.isnull(x) or str(x).strip() == "":
        return np.nan
    return unidecode(str(x).strip().lower())

def normalize_yelp_json(input_file):
    df = pd.read_json(input_file, lines=True)

    key_fields = [
        "business_id", "name", "address", "city", "state",
        "postal_code", "latitude", "longitude","categories"
    ]
    df = df[key_fields]

    text_columns = ["name", "address", "city", "state"]
    for col in text_columns:
        df[col] = df[col].apply(clean_text)

    df.dropna(subset=["name", "address"], inplace=True)
    df['categories'] = df['categories'].apply(
        lambda x: [clean_text(c) for c in x.split(',')] if pd.notnull(x) else []
    )

    return df

if __name__ == "__main__":
    input_file = '../data/raw/yelp_academic_dataset_business.json'
    output_file = '../data/interim/normalized_yelp.csv'

    normalized_df = normalize_yelp_json(input_file)

    normalized_df.to_csv(output_file, index=False)
    print(f"Normalization complete. Data saved to {output_file}")

