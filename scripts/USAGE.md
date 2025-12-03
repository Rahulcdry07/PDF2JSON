# DSR Rate Matching Scripts - Usage Guide

This guide explains how to use the DSR matching scripts with your own files.

## Overview

The DSR matching system consists of four main scripts:

1. **input_file_converter.py** - Converts input files to structured format ⭐ RECOMMENDED FIRST STEP
2. **convert_to_structured_json.py** - Converts PDF-extracted JSON to structured format
3. **create_alternative_formats.py** - Creates CSV and SQLite database from structured JSON
4. **match_dsr_rates_sqlite.py** - Matches your items with DSR rates from the database

## Recommended Workflow

### Step 0: Convert Your Input File (IMPORTANT!)

Before matching, convert your input file to structured format for better accuracy:

```bash
cd scripts

# Convert input file to structured format
python3 input_file_converter.py -i ../examples/input_files/Lko_Office_Repair_revise.json

# This creates: Lko_Office_Repair_revise_structured.json
```

**Why convert input files?**
- ✅ More reliable extraction (100% vs ~70% with unstructured)
- ✅ Consistent format matching reference files
- ✅ Easier to debug and verify
- ✅ Better performance
- ✅ Cleaner code, fewer edge cases

### Quick Start

```bash
cd scripts

# Step 0: Convert input file to structured format (RECOMMENDED)
python3 input_file_converter.py -i /path/to/your/input.json

# Step 1: Convert PDF JSON to structured format (for reference files)
python3 convert_to_structured_json.py

# Step 2: Create SQLite database
python3 create_alternative_formats.py

# Step 3: Match DSR codes (use structured input)
python3 match_dsr_rates_sqlite.py -i /path/to/your/input_structured.json
```

### With Your Own Files

```bash
cd scripts

# Step 0: Convert your input file
python3 input_file_converter.py \
  -i /path/to/your/input_items.json \
  -o /path/to/your/input_items_structured.json

# Step 1: Convert your DSR volumes to structured format (any number of volumes)
python3 convert_to_structured_json.py \
  -v /path/to/your/DSR_Vol_1.json /path/to/your/DSR_Vol_2.json /path/to/your/DSR_Vol_3.json \
  -o /path/to/output/directory

# Step 2: Create database from your structured files (any number of volumes)
python3 create_alternative_formats.py \
  -v /path/to/output/DSR_Vol_1_structured.json \
     /path/to/output/DSR_Vol_2_structured.json \
     /path/to/output/DSR_Vol_3_structured.json \
  -o /path/to/output/directory

# Step 3: Match your items (use structured input)
python3 match_dsr_rates_sqlite.py \
  -i /path/to/your/input_items_structured.json \
  -d /path/to/output/DSR_combined.db \
  -o /path/to/results \
  -t 0.3
```

## Script Details

### 0. input_file_converter.py ⭐ NEW

Converts input files (e.g., Lko_Office_Repair_revise.json) to structured format.

**Usage:**
```bash
python3 input_file_converter.py [OPTIONS]
```

**Options:**
- `-i, --input` - Path to input JSON file (required)
- `-o, --output` - Output file path (default: `<input>_structured.json`)

**Output:**
- Structured JSON with consistent format:
  ```json
  {
    "metadata": {
      "source_file": "input.json",
      "total_items": 19,
      "type": "input_items"
    },
    "items": [
      {
        "item_number": 1,
        "code": "DSR-2023-15.12.2",
        "clean_code": "15.12.2",
        "description": "...",
        "unit": "nos",
        "quantity": 10.0,
        "keywords": [...]
      }
    ]
  }
  ```

**Examples:**
```bash
# Convert with default output name
python3 input_file_converter.py -i ../examples/input_files/Lko_Office_Repair_revise.json

# Specify custom output
python3 input_file_converter.py -i input.json -o structured_input.json
```

### 1. convert_to_structured_json.py

Converts unstructured PDF JSON to structured format with explicit fields.

**Usage:**
```bash
python3 convert_to_structured_json.py [OPTIONS]
```

**Options:**
- `-v, --volumes` - Path(s) to DSR volume JSON files (can specify any number of files)
- `-o, --output-dir` - Output directory (default: same as first input file directory)

**Output:**
- `<filename>_structured.json` - Structured JSON with explicit fields (one per input volume)
- `<filename>_structured.index.json` - Index file for quick lookups (one per input volume)

**Examples:**
```bash
# Convert 2 volumes
python3 convert_to_structured_json.py \
  -v ../data/DSR_Volume_1.json ../data/DSR_Volume_2.json \
  -o ../data/structured

# Convert 5 volumes
python3 convert_to_structured_json.py \
### 2. create_alternative_formats.py

Creates CSV and SQLite database from structured JSON files. Combines all volumes into single database files.

**Usage:**
```bash
python3 create_alternative_formats.py [OPTIONS]
```

**Options:**
- `-v, --volumes` - Path(s) to structured DSR JSON files (can specify any number of files)
- `-o, --output-dir` - Output directory (default: same as first input file directory)
- `--skip-demo` - Skip demonstration queries

**Output:**
- `DSR_combined.csv` - CSV export combining all volumes
- `DSR_combined.db` - SQLite database with all volumes

**Examples:**
```bash
# Create database from 2 volumes
python3 create_alternative_formats.py \
  -v ../data/structured/DSR_Vol_1_Civil_structured.json \
     ../data/structured/DSR_Vol_2_Civil_structured.json \
  -o ../data/database \
  --skip-demo

# Create database from 5 volumes
python3 create_alternative_formats.py \
  -v vol1_structured.json vol2_structured.json vol3_structured.json \
     vol4_structured.json vol5_structured.json \
  -o ./database
```v1 ../data/structured/DSR_Vol_1_Civil_structured.json \
  -v2 ../data/structured/DSR_Vol_2_Civil_structured.json \
  -o ../data/database \
  --skip-demo
```

### 3. match_dsr_rates_sqlite.py

Matches your items with DSR rates from the SQLite database.

**Usage:**
```bash
python3 match_dsr_rates_sqlite.py [OPTIONS]
```

**Options:**
- `-i, --input` - Path to input JSON file with DSR items (default: ../examples/input_files/Lko_Office_Repair_revise.json)
- `-d, --database` - Path to SQLite DSR database (default: ../reference_files/DSR_combined.db)
- `-o, --output` - Output directory for results (default: ../examples/output_reports)
- `-t, --threshold` - Similarity threshold for matching (default: 0.3)

**Output:**
- `<input_filename>_matched_rates.json` - Matched results with rates and amounts

**Example:**
```bash
python3 match_dsr_rates_sqlite.py \
  -i ../projects/project1/items.json \
  -d ../data/database/DSR_combined.db \
  -o ../projects/project1/results \
  -t 0.4
```

## Input File Format

Your input JSON file should have DSR items in the following format:

```json
{
  "items": [
    {
      "description": "Item description here",
      "quantity": 10.5,
      "unit": "sqm"
    }
  ]
}
```

The script will automatically extract DSR codes from the descriptions.

## Output Format

The matched results JSON will contain:

```json
{
  "project": "DSR Rate Matching from your_file.json",
  "source_files": {
    "items": "/path/to/input.json",
    "rates_database": "/path/to/DSR_combined.db"
  },
  "summary": {
    "total_items": 14,
    "exact_matches": 7,
    "code_match_description_mismatch": 5,
    "not_found": 2,
    "total_estimated_amount": 3540921.89
  },
  "matched_items": [
    {
      "dsr_code": "DSR-2023-15.38",
      "description": "...",
      "quantity": 25.92,
      "unit": "Cum",
      "rate": 75.8,
      "amount": 1964.74,
      "match_type": "exact_with_description_match",
## Tips

1. **Multiple Volumes**: You can provide any number of DSR volume files. The scripts will:
   - Process each volume independently in the conversion step
   - Combine all volumes into a single database in the database creation step
   - Use the combined database for matching

2. **Similarity Threshold**: Adjust the `-t` parameter (0.0 to 1.0) to control matching strictness:
   - Higher values (0.5-0.8): More strict, only high-quality matches
   - Lower values (0.2-0.4): More lenient, accepts partial matches

3. **Database Creation**: The SQLite database only needs to be created once. Reuse it for multiple matching operations.

4. **Performance**: SQLite matching is 50-100x faster than JSON parsing for large datasets.

5. **File Paths**: Use absolute paths or paths relative to the scripts directory.

6. **Volume Naming**: Volumes are automatically named as "Volume 1", "Volume 2", etc. based on the order you provide them.

2. **Database Creation**: The SQLite database only needs to be created once. Reuse it for multiple matching operations.

3. **Performance**: SQLite matching is 50-100x faster than JSON parsing for large datasets.

4. **File Paths**: Use absolute paths or paths relative to the scripts directory.

## Getting Help

Use the `--help` flag with any script to see all available options:

```bash
python3 match_dsr_rates_sqlite.py --help
python3 convert_to_structured_json.py --help
python3 create_alternative_formats.py --help
```

## Troubleshooting

**Error: Input file not found**
- Check that your file path is correct
- Use absolute paths if relative paths don't work

**Error: Database file not found**
- Run `create_alternative_formats.py` first to create the database

**Error: No DSR codes found**
- Verify your input JSON format matches the expected structure
- Check that DSR codes in descriptions follow the pattern: DSR-2023-XX.XX.X

**Low match rates**
- Try adjusting the similarity threshold (`-t` parameter)
- Check that your reference DSR volumes contain the required codes
- Review the descriptions in your input file for accuracy
