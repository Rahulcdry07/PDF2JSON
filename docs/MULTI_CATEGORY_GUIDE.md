# Multi-Category DSR Organization Guide

## Overview
This guide explains how to organize and manage DSR (Delhi Schedule of Rates) codes from multiple categories like Civil, Electrical, Horticulture, Mechanical, etc.

## 📁 New Directory Structure

```
examples/
├── reference_files/
│   ├── civil/
│   │   ├── DSR_Vol_1_Civil.json
│   │   ├── DSR_Vol_2_Civil.json
│   │   ├── DSR_Vol_1_Civil_structured.json
│   │   ├── DSR_Vol_2_Civil_structured.json
│   │   └── DSR_Civil_combined.db
│   ├── electrical/
│   │   ├── DSR_Vol_1_Electrical.json
│   │   ├── DSR_Vol_2_Electrical.json
│   │   └── DSR_Electrical_combined.db
│   ├── horticulture/
│   │   ├── DSR_Horticulture.json
│   │   └── DSR_Horticulture_combined.db
│   ├── mechanical/
│   │   └── DSR_Mechanical_combined.db
│   ├── plumbing/
│   │   └── DSR_Plumbing_combined.db
│   └── master/
│       └── DSR_Master_All_Categories.db  ← Combined database
│
├── input_files/
│   ├── Project_ABC_items.json           ← Mixed category items
│   └── Building_XYZ_items_structured.json
│
└── output_reports/
    └── Project_ABC_matched_rates.json   ← Results with categories
```

## 🎯 Key Features

### 1. **Category Detection**
The system automatically detects which category each DSR code belongs to based on:
- Code patterns (e.g., Civil codes typically start with 1x.x, Electrical with 2x.x)
- Manual category specification in input files
- Database lookups

### 2. **Enhanced Database Schema**
```sql
CREATE TABLE dsr_codes (
    code TEXT,
    category TEXT,              ← NEW: Civil, Electrical, etc.
    chapter TEXT,
    section TEXT,
    description TEXT,
    unit TEXT,
    rate REAL,
    volume TEXT,
    page INTEGER,
    keywords TEXT,
    PRIMARY KEY (code, category)
);
```

### 3. **Category-Aware Matching**
- Searches within specific categories first
- Falls back to all categories if needed
- Reports which category each matched code belongs to

## 🚀 Setup Instructions

### Step 1: Migrate Existing Database

```bash
# Navigate to scripts directory
cd scripts

# Migrate your existing Civil database to new schema
python3 create_master_database.py \
    --migrate ../reference_files/DSR_combined.db \
    --category civil \
    --output ../reference_files/civil/DSR_Civil_combined.db
```

### Step 2: Organize by Categories

```bash
# Create category directories
mkdir -p ../reference_files/{civil,electrical,horticulture,mechanical,plumbing,master}

# Move Civil files
mv ../reference_files/DSR_Vol_*_Civil* ../reference_files/civil/
mv ../reference_files/civil/DSR_Civil_combined.db ../reference_files/civil/

# When you get Electrical PDFs, process them:
python3 ../src/pdf2json/cli.py DSR_Electrical.pdf -o DSR_Electrical.json
python3 convert_to_structured_json.py -v DSR_Electrical.json -o ../reference_files/electrical/
python3 create_alternative_formats.py -v ../reference_files/electrical/DSR_*_structured.json
```

### Step 3: Create Master Database

```bash
# Combine all categories into master database
python3 create_master_database.py --create-master \
    --civil ../reference_files/civil/DSR_Civil_combined.db \
    --electrical ../reference_files/electrical/DSR_Electrical_combined.db \
    --horticulture ../reference_files/horticulture/DSR_Horticulture_combined.db \
    --output ../reference_files/master/DSR_Master_All_Categories.db
```

## 📝 Input File Format (Enhanced)

### Structured Format with Categories

```json
{
  "metadata": {
    "type": "input_items",
    "project": "Building Construction Project",
    "total_items": 25,
    "categories": ["civil", "electrical", "plumbing"]
  },
  "items": [
    {
      "code": "DSR-2023-15.12.2",
      "clean_code": "15.12.2",
      "category": "civil",           ← NEW: Specify category
      "description": "Dismantling doors and windows",
      "quantity": "10.00",
      "unit": "Nos"
    },
    {
      "code": "DSR-2023-26.15.3",
      "clean_code": "26.15.3",
      "category": "electrical",       ← Electrical work
      "description": "Installation of MCB",
      "quantity": "5.00",
      "unit": "Nos"
    }
  ]
}
```

## 🔍 Matching with Categories

### Example 1: Match with Specific Category

```bash
# Match civil codes only
python3 match_dsr_rates_sqlite.py \
    -i ../examples/input_files/civil_work.json \
    -d ../reference_files/civil/DSR_Civil_combined.db \
    -o ../examples/output_reports/
```

### Example 2: Match with Master Database (All Categories)

```bash
# Match across all categories
python3 match_dsr_rates_sqlite.py \
    -i ../examples/input_files/mixed_project.json \
    -d ../reference_files/master/DSR_Master_All_Categories.db \
    -o ../examples/output_reports/
```

## 📊 Output Format (Enhanced)

```json
{
  "project": "DSR Rate Matching",
  "summary": {
    "total_items": 25,
    "by_category": {
      "civil": 15,
      "electrical": 8,
      "plumbing": 2
    },
    "exact_matches": 20,
    "not_found": 5
  },
  "matched_items": [
    {
      "dsr_code": "DSR-2023-15.12.2",
      "clean_dsr_code": "15.12.2",
      "category": "civil",              ← Shows which category
      "description": "...",
      "rate": 502.75,
      "match_type": "exact_match"
    }
  ]
}
```

## 💡 Best Practices

### 1. **Organize by Category from the Start**
- Keep separate databases for each category
- Easier to update individual categories
- Faster searches within specific categories

### 2. **Use Master Database for Mixed Projects**
- Single database with all categories
- Automatic category detection
- Comprehensive coverage

### 3. **Category Naming Convention**
```
civil         - Construction, masonry, plastering
electrical    - Wiring, fixtures, MCBs, panels
horticulture  - Landscaping, plants, irrigation
mechanical    - HVAC, elevators, escalators
plumbing      - Pipes, fixtures, drainage
```

### 4. **Code Pattern Recognition**
```
1x.x.x - Civil works (Chapter 1-20)
2x.x.x - Electrical works (Chapter 21-30)
3x.x.x - Horticulture (Chapter 31-40)
4x.x.x - Mechanical (Chapter 41-50)
5x.x.x - Plumbing (Chapter 51-60)
```

## 🔄 Migration Workflow

### For Existing Projects:

1. **Backup current database**
   ```bash
   cp DSR_combined.db DSR_combined_backup.db
   ```

2. **Create category structure**
   ```bash
   mkdir -p ../reference_files/{civil,master}
   ```

3. **Migrate to new schema**
   ```bash
   python3 create_master_database.py \
       --migrate ../reference_files/DSR_combined.db \
       --category civil \
       --output ../reference_files/civil/DSR_Civil_combined.db
   ```

4. **Update scripts to use new database path**
   ```bash
   # Old:
   -d ../reference_files/DSR_combined.db
   
   # New (category-specific):
   -d ../reference_files/civil/DSR_Civil_combined.db
   
   # New (all categories):
   -d ../reference_files/master/DSR_Master_All_Categories.db
   ```

## 🎨 Web Interface Updates

The web interface will automatically:
- Show available categories in dropdown
- Filter reference files by category
- Display category information in results
- Color-code items by category

## 🧪 Testing

```bash
# Test category-specific matching
python3 match_dsr_rates_sqlite.py \
    -i ../examples/input_files/Lko_Office_Repair_revise_structured.json \
    -d ../reference_files/civil/DSR_Civil_combined.db

# Test master database
python3 create_master_database.py --create-master \
    --civil ../reference_files/civil/DSR_Civil_combined.db \
    --output test_master.db

# Verify database
sqlite3 test_master.db "SELECT category, COUNT(*) FROM dsr_codes GROUP BY category"
```

## 📈 Benefits

1. ✅ **Better Organization** - Clear separation of categories
2. ✅ **Faster Searches** - Search within specific category first
3. ✅ **Scalability** - Easy to add new categories
4. ✅ **Flexibility** - Use category-specific or master database
5. ✅ **Clarity** - Know which category each code belongs to
6. ✅ **Maintenance** - Update categories independently

## 🔮 Future Enhancements

- Automatic category detection from code patterns
- Category-specific validation rules
- Cross-category dependency checking
- Category-based cost summaries
- Multi-category project templates
