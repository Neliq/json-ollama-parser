import csv
import json
import random

import sys

def inspect_dataset():
    csv.field_size_limit(sys.maxsize)
    filepath = 'archive/amazon-products.csv'
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        reader = csv.DictReader(f)
        all_rows = list(reader)
        
    print(f"Total rows: {len(all_rows)}")
    samples = random.sample(all_rows, 5)
    
    for i, row in enumerate(samples):
        print(f"\n--- Sample {i+1} ---")
        print(f"Title: {row.get('title')}")
        print(f"Brand: {row.get('brand')}")
        print(f"Categories: {row.get('categories')}")
        print(f"Dimensions: {row.get('product_dimensions')}")
        print(f"Weight: {row.get('item_weight')}")
        print(f"Features: {str(row.get('features'))[:200]}...")
        # print(f"Variations: {row.get('variations')[:200]}...") # Truncate
        print(f"Root BS Category: {row.get('root_bs_category')}")

if __name__ == "__main__":
    inspect_dataset()
