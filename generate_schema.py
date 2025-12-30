import csv
import json
import re
import os
import sys
import ast
from collections import Counter

# File paths
AMAZON_CSV = 'archive/amazon-products.csv'
OUTPUT_SCHEMA = 'schema.json'

def load_csv_data(filepath):
    """Loads CSV data into a list of dictionaries."""
    data = []
    if not os.path.exists(filepath):
        print(f"Warning: {filepath} not found.")
        return data
    
    # Increase field size limit for large descriptions
    csv.field_size_limit(sys.maxsize)
    
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append(row)
    return data

def parse_json_field(field_text):
    """Parses a text field that might contain JSON or python literals."""
    if not field_text or field_text == 'null':
        return None
    try:
        # Try JSON first
        return json.loads(field_text.replace("'", '"')) # simple fix for single quotes
    except json.JSONDecodeError:
        try:
             # Try AST literal eval for python-like lists
             return ast.literal_eval(field_text)
        except:
             return None

def extract_categories_and_subcategories(data_list, min_count=5):
    """Extracts top and leaf categories."""
    categories = []
    subcategories = []
    
    for row in data_list:
        cat_raw = row.get('categories')
        parsed = parse_json_field(cat_raw)
        
        if parsed and isinstance(parsed, list) and len(parsed) > 0:
            # Top level
            if parsed[0]:
                categories.append(parsed[0].strip().lower())
            # Leaf (Subcategory)
            if len(parsed) > 1:
                subcategories.append(parsed[-1].strip().lower())
        elif row.get('root_bs_category'):
             categories.append(row.get('root_bs_category').strip().lower())
             
    # Filter by frequency
    cat_counts = Counter(categories)
    valid_categories = [cat for cat, count in cat_counts.items() if count >= min_count]
    
    sub_counts = Counter(subcategories)
    valid_subcategories = [sub for sub, count in sub_counts.most_common(999)] # Limit subcategories
    
    return sorted(list(set(valid_categories))), sorted(list(set(valid_subcategories)))

def extract_brands(data_list, top_n=999):
    """Extracts top brands."""
    brands = []
    for row in data_list:
        b = row.get('brand')
        if b:
            brands.append(b.strip()) # Keep original case for brands? Or Title Case?
            
    counts = Counter(brands)
    # top_n most common brands
    return sorted([item[0] for item in counts.most_common(top_n)])

def extract_colors_from_variations(data_list, top_n=999):
    """Extracts common colors from 'variations' names."""
    colors = []
    
    # Extensive list of valid known colors and modifiers
    valid_color_tokens = {
        'beige', 'black', 'blue', 'brown', 'burgundy', 'camel', 'charcoal', 'cobalt', 'copper', 
        'coral', 'cream', 'crimson', 'cyan', 'dark', 'gold', 'gray', 'green', 'grey', 'indigo', 
        'ivory', 'khaki', 'lavender', 'light', 'lilac', 'magenta', 'maroon', 'matte', 'metallic', 
        'mint', 'multicolor', 'mustard', 'navy', 'nude', 'olive', 'orange', 'peach', 'pink', 
        'plum', 'purple', 'red', 'rose', 'royal', 'ruby', 'rust', 'sage', 'salmon', 'sand', 
        'silver', 'sky', 'tan', 'taupe', 'teal', 'turquoise', 'violet', 'white', 'yellow', 
        'amber', 'aqua', 'azure', 'bronze', 'chocolate', 'coffee', 'emerald', 'fuchsia', 
        'garnet', 'hazel', 'jade', 'lime', 'mocha', 'pearl', 'platinum', 'sapphire', 'scarlet', 
        'sienna', 'slate', 'smoke', 'steel', 'titanium', 'topaz', 'vanilla', 'zinc', 'champagne',
        'clear', 'crystal', 'transparent'
    }
    
    # Exclude misleading tokens that might look like colors or are common garbage
    stop_words = {'large', 'medium', 'small', 'size', 'pack', 'set', 'pair', 'x-large', 
                  'xx-large', 'small/medium', 'large/x-large', 'mens', 'womens', 'kids', 
                  'baby', 'toddler', 'in', 'oz', 'lb', 'kg', 'ml', 'bluetooth', 'wifi', 
                  'usb', 'battery', 'power', 'kit', 'replacement', 'compatible'}

    for row in data_list:
        vars_raw = row.get('variations')
        parsed = parse_json_field(vars_raw)
        
        if parsed and isinstance(parsed, list):
            for v in parsed:
                if isinstance(v, dict) and 'name' in v:
                    name = v['name']
                    if not name: continue
                    
                    # Normalize
                    clean_name = name.lower().strip()
                    
                    # 1. Reject if strictly numeric (already done, but verify)
                    if re.search(r'\d', clean_name):
                        continue
                        
                    # 2. Tokenize
                    # Replace special chars with space to split e.g. "blue/green", "black-white"
                    tokens = re.split(r'[\s/\-,&]+', clean_name)
                    
                    # 3. Filter tokens
                    valid_tokens = []
                    is_valid_entry = False
                    
                    for t in tokens:
                        if t in stop_words:
                            continue # explicitly skip known bad words
                        if t in valid_color_tokens:
                            valid_tokens.append(t)
                            is_valid_entry = True
                    
                    # 4. Reconstruct
                    # Only add if we found at least one valid color token
                    if is_valid_entry:
                        # Logic: "Blue Large" -> "blue"
                        # "Dark Blue" -> "dark blue"
                        # "Black and White" -> "black white" (acceptable simplified form)
                        # "Bluetooth" -> (filtered out)
                        final_color = " ".join(valid_tokens)
                        if final_color:
                            colors.append(final_color)
    
    counts = Counter(colors)
    return sorted([item[0] for item in counts.most_common(top_n)])

def extract_materials(data_list, top_n=999):
    """Extracts materials using regex from descriptions."""
    materials = []
    
    known_materials = [
        'cotton', 'polyester', 'wool', 'leather', 'silk', 'nylon', 'spandex', 
        'denim', 'linen', 'viscose', 'rayon', 'acrylic', 'cashmere', 'suede',
        'metal', 'plastic', 'wood', 'glass', 'ceramic', 'rubber', 'latex', 'silicone',
        'canvas', 'chiffon', 'velvet', 'fleece', 'jersey', 'lace', 'satin', 'bamboo'
    ]
    
    for row in data_list:
        desc = (row.get('description') or '') + " " + (row.get('features') or '') + " " + (row.get('product_details') or '')
        desc = desc.lower()
        
        for material in known_materials:
            if material in desc:
                materials.append(material)
    
    counts = Counter(materials)
    return sorted([item[0] for item in counts.most_common(top_n)])

def extract_sizes(data_list):
    return ['xs', 's', 'm', 'l', 'xl', 'xxl', 'xxxl']

def main():
    print("Loading dataset...")
    data = load_csv_data(AMAZON_CSV)
    
    if not data:
        print("No data found!")
        return

    print("Extracting schema properties...")
    categories, subcategories = extract_categories_and_subcategories(data)
    brands = extract_brands(data, top_n=999)
    colors = extract_colors_from_variations(data)
    materials = extract_materials(data)
    sizes = extract_sizes(data)
    
    # Construct schema structure
    # Now using detailed definitions
    schema = {
        "properties": {
            "category": {
                "type": "enum",
                "description": "The main category of the product",
                "values": categories
            },
            "subcategory": {
                "type": "enum",
                "description": "The specific subcategory",
                "values": subcategories
            },
            "brand": {
                "type": "enum",
                "description": "The brand manufacturer",
                "values": brands
            },
            "color": {
                "type": "enum",
                "description": "Primary color(s)",
                "values": colors
            },
            "material": {
                "type": "enum",
                "description": "Primary material(s)",
                "values": materials
            },
            "size": {
                "type": "enum",
                "description": "Size if applicable",
                "values": sizes
            },
            "dimensions": {
                "type": "string",
                "description": "Product dimensions (e.g., '10x10x5 inches')"
            },
            "weight": {
                "type": "string",
                "description": "Product weight (e.g., '2 lbs')"
            },
            "features": {
                "type": "array",
                "description": "List of key features or highlights",
                "items": { "type": "string" }
            }
        },
        "inference_rules": [
            "If a mapped property is not a perfect match, choose the closest valid option for enums.",
            "For 'dimensions' and 'weight', extract the exact text if found.",
            "For 'features', extract a list of 3-5 main features.",
            "Map 'big' or 'large' to 'l', 'small' to 's'."
        ]
    }
    
    print(f"Categories found: {len(categories)}")
    print(f"Subcategories found: {len(subcategories)}")
    print(f"Brands found: {len(brands)}")
    print(f"Colors found: {len(colors)}")
    print(f"Materials found: {len(materials)}")
    
    print(f"Writing schema to {OUTPUT_SCHEMA}...")
    with open(OUTPUT_SCHEMA, 'w') as f:
        json.dump(schema, f, indent=2)
    print("Done.")

if __name__ == "__main__":
    main()
