# DSR Matching Scripts - Usage Examples

## Example 0: Using Structured Input Files ⭐ RECOMMENDED

Convert your input file to structured format first for best results:

```bash
cd scripts

# Step 0: Convert input file to structured format
python3 input_file_converter.py \
  -i ../examples/input_files/Lko_Office_Repair_revise.json

# Output: Lko_Office_Repair_revise_structured.json
# This gives you:
# - 100% extraction accuracy (vs ~70% with unstructured)
# - Consistent format matching reference files
# - Easier debugging and verification
# - Better performance

# Then match with structured input
python3 match_dsr_rates_sqlite.py \
  -i ../examples/input_files/Lko_Office_Repair_revise_structured.json
```

**Why use structured input?**
- ✅ All 19 items extracted correctly (vs 14 items with unstructured)
- ✅ No pattern matching edge cases
- ✅ Consistent field names (code, description, quantity, unit)
- ✅ Same format as reference files
- ✅ Faster processing

## Example 1: Processing 2 Volumes (Default)

This is the most common scenario with two DSR volumes.

```bash
cd scripts

# Step 1: Convert both volumes
python3 convert_to_structured_json.py

# Step 2: Create combined database
python3 create_alternative_formats.py

# Step 3: Convert input file (RECOMMENDED)
python3 input_file_converter.py -i input.json

# Step 4: Match items
python3 match_dsr_rates_sqlite.py -i input_structured.json
```

**Output:**
- 2,234 total DSR codes extracted
- Combined database with both volumes
- Matched items with rates and amounts

## Example 2: Processing 3+ Volumes

When you have multiple DSR volumes from different years or regions:

```bash
cd scripts

# Step 1: Convert all volumes
python3 convert_to_structured_json.py \
  -v ../data/DSR_2023_Vol_1.json \
     ../data/DSR_2023_Vol_2.json \
     ../data/DSR_2024_Vol_1.json \
     ../data/DSR_2024_Vol_2.json \
  -o ../data/structured

# Step 2: Create combined database from all volumes
python3 create_alternative_formats.py \
  -v ../data/structured/DSR_2023_Vol_1_structured.json \
     ../data/structured/DSR_2023_Vol_2_structured.json \
     ../data/structured/DSR_2024_Vol_1_structured.json \
     ../data/structured/DSR_2024_Vol_2_structured.json \
  -o ../data/database

# Step 3: Convert input file
python3 input_file_converter.py \
  -i ../projects/project1/items.json

# Step 4: Match against combined database
python3 match_dsr_rates_sqlite.py \
  -i ../projects/project1/items_structured.json \
  -d ../data/database/DSR_combined.db \
  -o ../projects/project1/results
```

## Example 3: Regional DSR Files

Processing DSR files from different regions:

```bash
# Convert regional DSR files
python3 convert_to_structured_json.py \
  -v ../data/UP_DSR_Civil.json \
     ../data/Delhi_DSR_Civil.json \
     ../data/Haryana_DSR_Civil.json \
  -o ../data/regional

# Create combined database
python3 create_alternative_formats.py \
  -v ../data/regional/UP_DSR_Civil_structured.json \
     ../data/regional/Delhi_DSR_Civil_structured.json \
     ../data/regional/Haryana_DSR_Civil_structured.json \
  -o ../data/regional

# Match with specific threshold
python3 match_dsr_rates_sqlite.py \
  -i project_items.json \
  -d ../data/regional/DSR_combined.db \
  -t 0.4
```

## Example 4: Incremental Updates

Adding new DSR volumes to existing database:

```bash
# First time: Create initial database with 2 volumes
python3 convert_to_structured_json.py \
  -v vol1.json vol2.json \
  -o ./structured

python3 create_alternative_formats.py \
  -v ./structured/vol1_structured.json \
     ./structured/vol2_structured.json \
  -o ./database

# Later: Add new volume (vol3)
# Step 1: Convert the new volume
python3 convert_to_structured_json.py \
  -v vol3.json \
  -o ./structured

# Step 2: Recreate database with all 3 volumes
python3 create_alternative_formats.py \
  -v ./structured/vol1_structured.json \
     ./structured/vol2_structured.json \
     ./structured/vol3_structured.json \
  -o ./database \
  --skip-demo
```

## Example 5: Custom Similarity Threshold

Adjusting matching sensitivity:

```bash
# Strict matching (only high-quality matches)
python3 match_dsr_rates_sqlite.py \
  -i items.json \
  -d database/DSR_combined.db \
  -t 0.7

# Lenient matching (accepts partial matches)
python3 match_dsr_rates_sqlite.py \
  -i items.json \
  -d database/DSR_combined.db \
  -t 0.2

# Default balanced matching
python3 match_dsr_rates_sqlite.py \
  -i items.json \
  -d database/DSR_combined.db \
  -t 0.3
```

## Example 6: Batch Processing Multiple Projects

Processing multiple project files against the same database:

```bash
# Create database once
python3 convert_to_structured_json.py
python3 create_alternative_formats.py

# Match multiple projects
for project in project1 project2 project3; do
  python3 match_dsr_rates_sqlite.py \
    -i "../projects/${project}/items.json" \
    -d ../examples/reference_files/DSR_combined.db \
    -o "../projects/${project}/results"
done
```

## Example 7: Working with Different Output Directories

Organizing outputs by project:

```bash
# Project structure:
# /projects/
#   - office_repair/
#   - school_construction/
#   - hospital_renovation/

# Convert DSR volumes once
python3 convert_to_structured_json.py \
  -v ../reference/DSR_Vol_1.json ../reference/DSR_Vol_2.json \
  -o ../reference/structured

# Create database once
python3 create_alternative_formats.py \
  -v ../reference/structured/DSR_Vol_1_structured.json \
     ../reference/structured/DSR_Vol_2_structured.json \
  -o ../reference/database

# Match each project to its own output directory
python3 match_dsr_rates_sqlite.py \
  -i ../projects/office_repair/items.json \
  -d ../reference/database/DSR_combined.db \
  -o ../projects/office_repair/reports

python3 match_dsr_rates_sqlite.py \
  -i ../projects/school_construction/items.json \
  -d ../reference/database/DSR_combined.db \
  -o ../projects/school_construction/reports

python3 match_dsr_rates_sqlite.py \
  -i ../projects/hospital_renovation/items.json \
  -d ../reference/database/DSR_combined.db \
  -o ../projects/hospital_renovation/reports
```

## Tips for Multi-Volume Processing

1. **Volume Order Matters**: Volumes are named sequentially (Volume 1, Volume 2, etc.) based on the order you provide them. If duplicates exist, later volumes overwrite earlier ones.

2. **Memory Considerations**: Each volume is processed one at a time, so memory usage is proportional to the largest single volume, not the total.

3. **Database Updates**: Always recreate the database when adding new volumes. SQLite INSERT OR REPLACE ensures the latest data is used.

4. **File Naming**: Output files are named based on input filenames, so use descriptive names for your volumes.

5. **Verification**: Check the total code count after database creation to ensure all volumes were loaded correctly.

## Common Workflows

### Workflow A: Annual Update
When new DSR volumes are released annually:
1. Download new PDF files
2. Convert PDFs to JSON (using pdf2json)
3. Run convert_to_structured_json.py with ALL volumes (old + new)
4. Recreate database with all volumes
5. Use updated database for new projects

### Workflow B: Multi-Region Projects
When working across multiple regions:
1. Maintain separate databases per region
2. Match items against the appropriate regional database
3. Compare rates across regions if needed

### Workflow C: Historical Rate Analysis
When analyzing rate changes over time:
1. Keep all historical volumes
2. Create year-specific databases
3. Match same items against different year databases
4. Compare results for rate trend analysis
