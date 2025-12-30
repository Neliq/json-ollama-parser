import parser
import json
import sys
import os
import csv
import random
import ast
import re

# Ensure we can import parser from current directory
sys.path.append('.')

DATASET_FILE = 'archive/amazon-products.csv'
SAMPLE_SIZE = 50

def normalize(text):
    if not text:
        return ""
    if isinstance(text, list):
         return str(text).strip().lower()
    return str(text).strip().lower()

def normalize_output_list(output):
    """Handles both string and list output."""
    if not output:
        return []
    if isinstance(output, list):
        return [normalize(c) for c in output if c]
    return [normalize(output)]

def parse_json_field(field_text):
    """Parses a text field that might contain JSON or python literals."""
    if not field_text or field_text == 'null':
        return None
    try:
        return json.loads(field_text.replace("'", '"')) 
    except:
        try:
             return ast.literal_eval(field_text)
        except:
             return None

def main():
    print(f"Loading dataset from {DATASET_FILE}...")
    if not os.path.exists(DATASET_FILE):
        print("Error: Dataset file not found.")
        sys.exit(1)

    # Increase field size limit
    csv.field_size_limit(sys.maxsize)

    data = []
    with open(DATASET_FILE, 'r', encoding='utf-8', errors='ignore') as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append(row)
    
    if not data:
        print("Error: Dataset is empty.")
        sys.exit(1)

    print(f"Loaded {len(data)} records. Selecting {SAMPLE_SIZE} random samples...")
    # Filter for rows that have at least some category info to be fail
    valid_data = [d for d in data if d.get('categories') and d.get('categories') != 'null']
    if len(valid_data) < SAMPLE_SIZE:
        samples = valid_data
    else:
        samples = random.sample(valid_data, SAMPLE_SIZE)

    # Load schema once
    print("Loading schema...")
    schema = parser.load_schema(parser.SCHEMA_FILE)
    system_prompt = parser.construct_prompt(schema)

    correct_categories = 0
    correct_colors = 0
    correct_brands = 0
    correct_subcategories = 0
    found_dimensions = 0
    total_samples = len(samples)

    print("\n--- Starting Verification ---")

    for i, row in enumerate(samples):
        print(f"\nSample {i+1}/{total_samples}:")
        
        # Prepare input
        # Amazon has title, description, features
        description = (row.get('title') or '') + " " + (row.get('description') or '')
        description = description.strip()
        # Truncate if too long to save context window and time
        if len(description) > 1000:
            description = description[:1000] + "..."
            
        if not description:
            print("Skipping empty description.")
            continue
            
        # Ground Truth - Category
        cat_raw = row.get('categories')
        parsed_cat = parse_json_field(cat_raw)
        gt_category = ""
        gt_subcategory = "" # New variable for leaf
        
        if parsed_cat and isinstance(parsed_cat, list) and len(parsed_cat) > 0:
            # Schema 'category' matches the ROOT (index 0)
            gt_category = normalize(parsed_cat[0])
            # Schema 'subcategory' matches the LEAF (last index) (if different)
            if len(parsed_cat) > 1:
                gt_subcategory = normalize(parsed_cat[-1])
            else:
                 gt_subcategory = gt_category
                 
        elif row.get('root_bs_category'):
            gt_category = normalize(row.get('root_bs_category'))
            gt_subcategory = gt_category # fallback

        # Ground Truth - Color (from variations)
        vars_raw = row.get('variations')
        parsed_vars = parse_json_field(vars_raw)
        gt_colors = []
        if parsed_vars and isinstance(parsed_vars, list):
             for v in parsed_vars:
                 if isinstance(v, dict) and 'name' in v:
                     name = v['name']
                     if name:
                         gt_colors.append(normalize(name))

        # Ground Truth - New Fields
        gt_brand = normalize(row.get('brand'))
        gt_dimensions = row.get('product_dimensions')
        gt_weight = row.get('item_weight')
        gt_features_raw = parse_json_field(row.get('features'))
        
        print(f"Ground Truth -> Category: '{gt_category}', Subcategory: '{gt_category}', Brand: '{gt_brand}'")
        
        # Prediction
        result = parser.parse_description(description, system_prompt, schema)
        
        if not result:
            print("FAILURE: Parser returned Error/None")
            continue

        pred_category = ""
        pred_cat_list = normalize_output_list(result.get('category'))
        if pred_cat_list:
            pred_category = pred_cat_list[0]

        pred_subcategory = normalize(result.get("subcategory"))
        pred_brand = normalize(result.get("brand"))
        pred_dimensions = result.get("dimensions")
        pred_weight = result.get("weight")
        pred_features = result.get("features")
        pred_colors = normalize_output_list(result.get('color'))
        
        print(f"Prediction   -> Cat: '{pred_category}', Sub: '{pred_subcategory}', Brand: '{pred_brand}', Dim: {pred_dimensions}, Wgt: {pred_weight}")
        
        # Verification Logic
        
        # 1. Category (Broad Match)
        cat_match = (pred_category == gt_category)
        if cat_match: correct_categories += 1
        
        # 2. Subcategory (Fuzzy Match)
        # Check against pure GT subcategory
        sub_match = False
        if gt_subcategory and pred_subcategory:
            if pred_subcategory in gt_subcategory or gt_subcategory in pred_subcategory:
                sub_match = True
        
        # 3. Brand (Fuzzy Match)
        brand_match = False
        if gt_brand and pred_brand:
            if pred_brand in gt_brand or gt_brand in pred_brand:
                brand_match = True
        elif not gt_brand and not pred_brand:
            brand_match = True
            
        # 4. Color (Intersection)
        col_match = False
        if not gt_colors and not pred_colors:
             col_match = True
        elif gt_colors and pred_colors:
             for p in pred_colors:
                 for g in gt_colors:
                     if p in g or g in p:
                         col_match = True
                         break
                 if col_match: break

        if col_match: correct_colors += 1
        if brand_match: correct_brands += 1
        if sub_match: correct_subcategories += 1
        
        print(f"Matches -> Cat: {cat_match}, Sub: {sub_match}, Brand: {brand_match}, Color: {col_match}")
        
        # Simple existence check for extensive fields
        has_dims_pred = bool(pred_dimensions)
        has_dims_gt = bool(gt_dimensions)
        if has_dims_pred and has_dims_gt: found_dimensions += 1
        print(f"Dimensions Found: {has_dims_pred} (GT: {has_dims_gt})")

        
    # We will just print per-line status rather than global stats for all new fields to avoid clutter,
    # but let's accumulate Brand accuracy.
    # ...


    print("\n--- Results ---")
    print(f"Category Accuracy:    {correct_categories}/{total_samples} ({correct_categories/total_samples*100:.1f}%)")
    print(f"Subcategory Accuracy: {correct_subcategories}/{total_samples} ({correct_subcategories/total_samples*100:.1f}%)")
    print(f"Brand Accuracy:       {correct_brands}/{total_samples} ({correct_brands/total_samples*100:.1f}%)")
    print(f"Color Accuracy:       {correct_colors}/{total_samples} ({correct_colors/total_samples*100:.1f}%)")
    print(f"Dimensions Found:     {found_dimensions}/{total_samples} (where GT existed)")

if __name__ == "__main__":
    main()
