# Ollama JSON Parser: AI Product Description Extractor

A robust, local AI tool that parses plain text product descriptions into structured JSON data. Optimized for **12GB VRAM** using `mistral-nemo` (12B) and a **Hybrid Prompting** architecture.

## 🚀 Features

- **Dynamic Schema Generation**: Automatically builds a JSON schema (`schema.json`) by analyzing your product dataset CSV.
- **Hybrid Prompting**:
  - **Strict Enums**: Forces the model to choose from valid lists for top-level keys like `category`.
  - **Open Extraction**: Allows free-text extraction for brands, subcategories, and colors, validated via post-processing.
- **Fuzzy Matching Validation**: uses Python's `difflib` to validate and normalize extracted values against thousands of known schema entries (Brand, Color, Subcategory).
- **100% Local**: Runs entirely on your machine using Ollama.

## 🛠️ Prerequisites

1.  **Ollama**: Install from [ollama.com](https://ollama.com/).
2.  **Pull the Model**:
    ```bash
    ollama pull mistral-nemo
    ```
3.  **Python 3.8+**

## 📦 Installation

1.  Clone the repository.
2.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

## 🏃 Usage

### 1. Generate Schema (Optional)

If you have a new dataset (`archive/amazon-products.csv`), regenerate the schema to capture new brands, categories, and colors.

```bash
python generate_schema.py
```

_This scans the CSV and updates `schema.json` with top 1000 brands, valid colors, and categories._

### 2. Run Interactive Parser

Test the parser with your own inputs.

```bash
python parser.py
```

**Example Input:**

> "Heavy duty 10ft orange extension cord. Brand: PowerMax. Weight: 2lbs."

**Example Output:**

```json
{
  "category": "tools & home improvement",
  "subcategory": "electrical cords",
  "brand": "PowerMax",
  "color": "orange",
  "material": null,
  "size": "10ft",
  "dimensions": null,
  "weight": "2lbs",
  "features": ["Heavy duty"]
}
```

### 3. Run Verification

Measure accuracy against the dataset.

```bash
python test_parser.py
```

_This extracts 50 random samples from the CSV, runs the parser, and compares the output against Ground Truth data._

## 📂 Project Structure

- `parser.py`: Main inference script. Handles prompting and `validate_and_normalize` logic.
- `generate_schema.py`: Analysis script. Uses `Counter` and whitelist filtering to build the schema.
- `schema.json`: The taxonomy definition. Referenced by the parser.
- `test_parser.py`: Automated verification script with Ground Truth extraction logic.
- `archive/`: Directory for input CSV datasets.

## ⚙️ Configuration

- **Model**: Change `MODEL_NAME` in `parser.py` to use a different Ollama model (e.g., `llama3.1`).
- **Schema Limits**: Adjust `top_n` in `generate_schema.py` to capture more or fewer brands/colors.
