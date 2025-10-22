'''
1. Summary of Normalization Steps
Step	Action
1	Keep only key fields
2	Load JSON into DataFrame
3	Lowercase, trim text
4	Split categories into lists
5	Remove duplicates

6	Drop rows with missing critical fields (dropped all rows with null values)
________________________________________________________________________________
7	Validate ZIP codes & coordinates
8	Optional: normalize addresses & remove accents
9	Save clean CSV

2. Gather data from different sources and conflate so entries refer to same place


Step 1: Identify Key Fields

From the Yelp JSON, keep only the attributes you care about:

business_id → unique identifier
name → business name
address → street address
city → city name
state → 2-letter state
postal_code → ZIP code
latitude & longitude → geolocation
stars → rating
review_count → number of reviews
categories → business categories

'''

import pandas as pd
import json
import numpy as np
from unidecode import unidecode
from pathlib import Path
import re


def clean_text(x):
    if pd.isnull(x) or str(x).strip() == "":
        return np.nan
    return unidecode(str(x).strip().lower())




def normalize_yelp_json(input_file):
    df = pd.read_json(input_file, lines=True)

    key_fields = [
        "business_id", "name", "address", "city", "state",
        "postal_code", "categories"
    ]
    #select only the key fields we highlighted
    df = df[key_fields]
    #cleaning the data from these fields
    text_columns = ["name", "address", "city", "state"]
    for col in text_columns:

        df[col] = df[col].apply(clean_text)



    df.dropna(subset=["name", "address"], inplace=True)
    df['categories'] = df['categories'].apply(
        lambda x: [clean_text(c) for c in x.split(',')] if pd.notnull(x) else []
    )
    
    return df

print(normalize_yelp_json('/Users/stanleyshen/stanley-jeffrey-attributesConflation/data/sample_data.json'))