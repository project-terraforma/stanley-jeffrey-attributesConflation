#!/usr/bin/env python3
import pandas as pd
from pathlib import Path

CONFLATED_FILE = "../data/processed/yelp_conflated.csv"      # rule-based output
GROUND_TRUTH_FILE = "../data/processed/yelp_ground_truth.csv"  # correct names/addresses

conflated_df = pd.read_csv(CONFLATED_FILE)
ground_truth_df = pd.read_csv(GROUND_TRUTH_FILE)

merged = conflated_df.merge(ground_truth_df, on='place_id', how='inner')

merged['name_correct'] = merged['best_name'] == merged['name']
merged['address_correct'] = merged['best_address'] == merged['address']

name_accuracy = merged['name_correct'].mean() * 100
address_accuracy = merged['address_correct'].mean() * 100
overall_accuracy = ((merged['name_correct'] & merged['address_correct']).mean()) * 100

print(f"Rule-based Name Accuracy: {name_accuracy:.2f}%")
print(f"Rule-based Address Accuracy: {address_accuracy:.2f}%")
print(f"Rule-based Overall Accuracy (name & address correct): {overall_accuracy:.2f}%")

