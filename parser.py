import ollama
import json
import os
import sys
import difflib


MODEL_NAME = "mistral"
SCHEMA_FILE = "schema.json"

def load_schema(filepath):
    """Loads the schema from a JSON file."""
    if not os.path.exists(filepath):
        print(f"Error: Schema file '{filepath}' not found.")
        sys.exit(1)
    
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON schema: {e}")
        sys.exit(1)

def construct_prompt(schema):
    """Constructs the system prompt based on the schema."""
    properties = schema.get("properties", {})
    inference_rules = schema.get("inference_rules", [])
    
    # Separate Category from others for Hybrid Prompting
    category_values = []
    if "category" in properties and properties["category"].get("type") == "enum":
        category_values = properties["category"].get("values", [])
    
    fields_desc = []
    
    for key, output_def in properties.items():
        prop_type = output_def.get("type")
        description = output_def.get("description", "")
        
        # Special handling for Category (Strict Enum)
        if key == "category":
            fields_desc.append(f"- {key}: String (Choose from list below) - {description}")
        elif prop_type == "enum":
            # Other Enums (Brand, Subcategory): Open Extraction
            fields_desc.append(f"- {key}: String (Extract from text) - {description}")
        elif prop_type == 'array':
            fields_desc.append(f"- {key}: List of strings - {description}")
        else:
            fields_desc.append(f"- {key}: String - {description}")

    fields_str = "\n".join(fields_desc)
    rules_str = "\n".join([f"- {rule}" for rule in inference_rules])
    
    # Inject Category List
    cat_list_str = "\n".join([f"- {c}" for c in category_values])
    
    prompt = f"""
You are a helpful assistant that parses product descriptions into a JSON structure.
You MUST output ONLY valid JSON.
You must extract the following properties from the input text.

Fields to Extract:
{fields_str}

Valid Categories (Choose exactly one for 'category'):
{cat_list_str}

Rules:
1. Return JSON only.
2. For 'category', you MUST infer and choose the best fit from the 'Valid Categories' list above.
3. For ALL OTHER fields (brand, subcategory, etc.), extract the EXACT text found in the description. Do not guess.
4. If a property is not found, return null (or empty list for arrays).
5. 'features' should be a list of short strings highlighting key product features.

Inference Rules:
{rules_str}

Example Input: "Bright, big orange and black fedora made with quality polyester. Brand: HatMaster. Dimensions: 10x10x5 inches. Weight: 0.5 lbs. Features: Waterproof, sun protection."
Example Output:
{{
  "category": "clothing, shoes & jewelry",
  "subcategory": "hats",
  "brand": "HatMaster",
  "color": "orange", 
  "material": "polyester",
  "size": "xl",
  "dimensions": "10x10x5 inches",
  "weight": "0.5 lbs",
  "features": ["Waterproof", "sun protection"]
}}
"""
    return prompt

def validate_and_normalize(result, schema):
    """Normalizes extracted values against schema enums using fuzzy matching."""
    if not result:
        return result
        
    properties = schema.get("properties", {})
    
    for key, value in result.items():
        if key not in properties:
             continue
             
        prop_def = properties[key]
        if prop_def.get("type") == "enum" and value:
            valid_values = prop_def.get("values", [])
            
            # Helper to match single value
            def match_val(v):
                if not v: return None
                v = str(v).lower().strip()
                if v in valid_values:
                    return v # Exact match
                # Fuzzy match
                matches = difflib.get_close_matches(v, valid_values, n=1, cutoff=0.6)
                if matches:
                    return matches[0]
                return v # Return original value if no match found (soft validation)
            
            # Handle list vs string
            if isinstance(value, list):
                new_list = []
                for item in value:
                     matched = match_val(item)
                     if matched: new_list.append(matched)
                # Ensure unique
                result[key] = list(set(new_list)) if new_list else None
            else:
                result[key] = match_val(value)
                
    return result

def parse_description(description, system_prompt, schema):
    """
    Sends the description to Ollama and returns the parsed JSON.
    """
    try:
        response = ollama.chat(
            model=MODEL_NAME,
            messages=[
                {
                    'role': 'system',
                    'content': system_prompt,
                },
                {
                    'role': 'user',
                    'content': description,
                },
            ],
            format='json',
        )
        content = response['message']['content']
        raw_result = json.loads(content)
        
        # Post-process validation
        return validate_and_normalize(raw_result, schema)

    except Exception as e:
        print(f"Error communicating with Ollama: {e}")
        return None

def main():
    print("Ollama JSON Parser")
    print("------------------")
    print(f"Using model: {MODEL_NAME}")
    
    schema = load_schema(SCHEMA_FILE)
    system_prompt = construct_prompt(schema)
    # print("DEBUG: System Prompt:\n", system_prompt) # Uncomment for debugging

    while True:
        try:
            user_input = input("\nEnter product description (or 'quit' to exit): ").strip()
            if user_input.lower() in ['quit', 'exit']:
                break
            
            if not user_input:
                continue

            print("Parsing...")
            result = parse_description(user_input, system_prompt, schema)
            
            if result:
                print(json.dumps(result, indent=2))
            else:
                print("Failed to parse input.")
                
        except KeyboardInterrupt:
            print("\nExiting...")
            break

if __name__ == "__main__":
    main()
