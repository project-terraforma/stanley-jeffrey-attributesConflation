'''
Summary of Normalization Steps
Step	Action
1	Keep only key fields
2	Load JSON into DataFrame
3	Lowercase, trim text
4	Split categories into lists
5	Remove duplicates
6	Drop rows with missing critical fields
7	Validate ZIP codes & coordinates
8	Optional: normalize addresses & remove accents
9	Save clean CSV


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

pd.set_option('display.max_columns', None)
pd.set_option('display.max_colwidth', None)

def clean_text(x):
    if pd.isnull(x):
        return np.nan
    return unidecode(str(x).strip().lower())


def normalize_yelp_json(input_file):
    df = pd.read_json(input_file, lines=True)
    print("Before cleaning", df)

    key_fields = [
        "business_id", "name", "address", "city", "state",
        "postal_code", "categories"
    ]
    #select only the key fields we highlighted
    df = df[key_fields]
    #cleaning the data from these fields
    text_columns = ["name", "address", "city", "state", "categories"]
    for col in text_columns:
        df[col] = df[col].apply(clean_text)
    
    print("After", df)

normalize_yelp_json('/Users/stanleyshen/stanley-jeffrey-attributesConflation/data/sample_data.json')