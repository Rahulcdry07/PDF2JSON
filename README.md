# PDF2JSON - PDF Conversion & DSR Rate Matching System

A comprehensive Python application that converts PDF files to JSON format and provides advanced DSR (Detailed Schedule of Rates) rate matching capabilities for construction project cost estimation.

## 🏗️ Features

### Core Functionality
- **PDF to JSON Conversion**: Convert PDF documents to structured JSON format using PyMuPDF
- **DSR Rate Matching**: Match construction items with DSR rates using SQLite database (50-100x faster)
- **Web Interface**: Upload, convert, view files, and run cost estimations through a modern web UI
- **Multi-Format Support**: Work with JSON, CSV, Markdown, and SQLite databases
- **Multi-Volume DSR**: Process any number of DSR volumes from different years or regions

### DSR Matching System
- **Smart Code Extraction**: Automatically extract DSR codes from construction documents
- **SQLite Performance**: O(1) lookups with <1ms query time for 2,200+ DSR codes
- **Flexible Matching**: Exact code matching with similarity-based fallback
- **Cost Calculation**: Automatic quantity × rate calculations with detailed breakdowns
- **High Match Rate**: Achieve 100% exact code matching for properly formatted inputs
- **Generic CLI**: Configurable via command-line arguments (no hardcoded paths)

## 📁 Project Structure

```
PDF2JSON/
├── src/pdf2json/           # Core application modules
│   ├── cli.py             # Command-line interface for PDF conversion
│   ├── converter.py       # PDF to JSON conversion logic
│   └── web.py             # Flask web application (UPDATED)
├── scripts/               # DSR matching system (CLEANED UP)
│   ├── convert_to_structured_json.py  # PDF JSON → Structured JSON
│   ├── create_alternative_formats.py  # Structured JSON → CSV/SQLite
│   ├── match_dsr_rates_sqlite.py      # Match items with SQLite (MAIN)
│   ├── dsr_extractor.py               # DSR code extraction utilities
│   ├── dsr_rate_extractor.py          # Rate extraction from PDFs
│   ├── text_similarity.py             # Similarity scoring
│   ├── dsr_matcher.py                 # Matching logic
│   ├── read_json.py                   # JSON utilities
│   ├── USAGE.md                       # Complete usage guide
│   ├── EXAMPLES.md                    # 7 practical examples
│   └── README.md                      # Scripts documentation
├── examples/              # Example files and outputs
│   ├── input_files/       # Input documents
│   ├── reference_files/   # DSR databases (JSON & SQLite)
│   └── output_reports/    # Generated reports
├── templates/             # Web interface templates
├── tests/                 # Unit tests
└── uploads/              # Temporary upload storage
```

## 🚀 Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd PDF2JSON
   ```

2. **Create virtual environment (recommended)**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # On macOS/Linux
   # .venv\Scripts\activate  # On Windows
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Verify installation**
   ```bash
   python -m src.pdf2json.cli --help
   python -c "from src.pdf2json.web import app; print('✓ Web app ready')"
   ```

## 💻 Usage

### 1. Web Interface (Recommended)

Start the web server:
```bash
python -m src.pdf2json.web
```

Then open **http://localhost:8000** in your browser to:
- Upload and convert PDF files
- View organized file structure (input/output/reference)
- Browse JSON, CSV, and Markdown reports
- Run DSR cost estimations with a click
- Search across all converted files

**Web Features:**
- 📤 Upload PDFs (max 100 MB)
- 🔄 Auto-convert to JSON
- 📊 View reports in formatted tables
- 💰 Run cost estimations (uses SQLite backend)
- 🔍 Global search across all files

### 2. DSR Rate Matching (Command Line)

**Complete workflow:**
```bash
cd scripts

# Step 1: Convert PDF JSON to structured format (any number of volumes)
python3 convert_to_structured_json.py -v vol1.json vol2.json

# Step 2: Create SQLite database
python3 create_alternative_formats.py -v vol1_structured.json vol2_structured.json

# Step 3: Match your items
python3 match_dsr_rates_sqlite.py -i items.json -d DSR_combined.db
```

**See detailed documentation:**
- [scripts/USAGE.md](scripts/USAGE.md) - Complete usage guide
- [scripts/EXAMPLES.md](scripts/EXAMPLES.md) - 7 practical examples
- [scripts/README.md](scripts/README.md) - Architecture overview

### 3. PDF to JSON Conversion (Command Line)

Convert a single PDF:
```bash
python -m src.pdf2json.cli input.pdf --output output.json
```

Convert with metadata:
```bash
python -m src.pdf2json.cli input.pdf --include-metadata
```

## 📊 DSR Matching Performance

| Format | Size | Query Speed | Match Rate | Best For |
|--------|------|-------------|------------|----------|
| JSON (old) | 2.2 MB | 2-5 seconds | 14.3% | Development |
| Structured JSON | 786 KB | ~1 second | 50% | Medium projects |
| SQLite (new) | 786 KB | <0.1 second | 100% | Production ✅ |

**Current System:**
- 2,233 DSR codes from Volume I + II
- <1ms per query with indexed lookups
- 100% exact code matching
- All 14/14 items matched (₹3.54M total)

## 📈 Generated Reports

### JSON Report (match_dsr_rates_sqlite.py)
```json
{
  "summary": {
    "total_items": 14,
    "exact_matches": 7,
    "code_match_description_mismatch": 7,
    "not_found": 0,
    "total_estimated_amount": 3540921.89
  },
  "matched_items": [...]
}
```

### SQLite Database
- Indexed on: code, chapter, section, rate, unit
- 9 columns per row
- Supports complex SQL queries
- Cross-volume duplicate handling

## 🎯 Key Improvements

### Recent Updates (Nov 2025)
✅ **Multi-volume support** - Process any number of DSR volumes  
✅ **SQLite backend** - 50-100x faster than JSON parsing  
✅ **Generic scripts** - Command-line arguments (no hardcoded paths)  
✅ **Web integration** - Cost estimation through web UI (FIXED)  
✅ **Code cleanup** - Removed 8 obsolete files (50% reduction)  
✅ **Documentation** - Complete USAGE.md + EXAMPLES.md guides  

### Migration from Old System
- ❌ `match_dsr_rates.py` (JSON-based) → ✅ `match_dsr_rates_sqlite.py` (SQLite)
- ❌ `config.py` (hardcoded) → ✅ CLI arguments (flexible)
- ❌ Dual format detection → ✅ Unified extraction
- ❌ Manual file paths → ✅ Dynamic output naming

## 🔧 Development

### Running Tests
```bash
pytest tests/
```

### Adding Custom DSR Volumes
```bash
# 1. Convert your PDFs to JSON first (if needed)
python -m src.pdf2json.cli DSR_Vol_3.pdf

# 2. Convert to structured format
python3 scripts/convert_to_structured_json.py -v DSR_Vol_3.json

# 3. Recreate database with all volumes
python3 scripts/create_alternative_formats.py \
  -v vol1_structured.json vol2_structured.json vol3_structured.json

# 4. Match against new database
python3 scripts/match_dsr_rates_sqlite.py -i items.json -d DSR_combined.db
```

## 📋 Requirements

- Python 3.8+
- PyMuPDF (fitz) - PDF processing
- Flask - Web interface
- Click - CLI framework
- Markdown - Report formatting
- sqlite3 - Database (built-in)

See `requirements.txt` for complete list.

## 🆘 Troubleshooting

### Web Interface
**Issue**: Cost estimation fails  
**Fix**: Ensure `DSR_combined.db` exists in `examples/reference_files/`
```bash
cd scripts
python3 create_alternative_formats.py  # Creates database
```

**Issue**: "DSR matching script not found"  
**Fix**: The web app now uses `match_dsr_rates_sqlite.py` (updated Nov 2025)

### DSR Matching
**Issue**: Low match rates  
**Fix**: Check similarity threshold (default 0.3), adjust with `-t` parameter

**Issue**: Missing DSR codes  
**Fix**: Verify codes follow DSR-YYYY-XX.XX.X format in input file

See [scripts/USAGE.md](scripts/USAGE.md) troubleshooting section for more details.

## 📝 Credits

- PDF processing: PyMuPDF (fitz)
- Web framework: Flask
- Database: SQLite3
- Text similarity: difflib.SequenceMatcher

## 📄 License

MIT License - See LICENSE file for details

## 📁 Project Structure

```
PDF2JSON/
├── src/pdf2json/           # Core application modules
│   ├── cli.py             # Command-line interface
│   ├── converter.py       # PDF conversion logic
│   └── web.py             # Flask web application
├── scripts/               # DSR matching system
│   ├── config.py          # Project configuration
│   ├── match_dsr_rates.py # Core matching logic
│   ├── create_dsr_report.py # Report generation
│   └── read_json.py       # JSON utilities
├── examples/              # Example files and outputs
│   ├── input_files/       # Input documents
│   ├── reference_files/   # DSR databases
│   └── output_reports/    # Generated reports
├── templates/             # Web interface templates
├── tests/                 # Unit tests
└── uploads/              # Temporary upload storage
```

## 🚀 Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd PDF2JSON
   ```

2. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Verify installation**
   ```bash
   python -m src.pdf2json.cli --help
   ```

## 💻 Usage

### 1. Web Interface (Recommended)

Start the web server:
```bash
python -m src.pdf2json.web
```

Then open http://localhost:5000 in your browser to:
- Upload and convert PDF files
- View organized file structure
- Browse JSON, CSV, and Markdown reports
- Search and navigate through converted content

### 2. Command Line Interface

Convert a single PDF:
```bash
python -m src.pdf2json.cli input.pdf --output output.json
```

### 3. DSR Rate Matching

Use the demo script to see the complete DSR matching workflow:
```bash
python demo_dsr_matching.py
```

Or run the matching scripts directly:
```bash
cd scripts
python match_dsr_rates.py
python create_dsr_report.py
```

### 4. Configuration

The system supports multiple projects through `scripts/config.py`. Add new projects by defining:
- Input file specifications
- Reference database mappings  
- Output report preferences

## 📊 DSR Matching Workflow

1. **Input Processing**: Extract DSR codes from construction documents
2. **Database Loading**: Load rates from multiple DSR reference databases
3. **Smart Matching**: Match items using fuzzy string matching algorithms
4. **Cost Calculation**: Calculate quantities × rates for total project cost
5. **Report Generation**: Create comprehensive reports in multiple formats

### Example DSR Match Results
```
✅ Found 13/13 DSR matches (100% match rate)
💰 Total project cost: ₹6,10,44,685.55
📊 Generated reports:
   • JSON: Complete matching data
   • CSV: Tabular analysis for Excel
   • Markdown: Formatted summary report
```

## 📈 Generated Reports

### JSON Report
Complete matching data with:
- Original item descriptions
- Matched DSR codes and descriptions
- Unit rates and quantities
- Cost calculations
- Volume information

### CSV Report
Tabular format perfect for Excel analysis with columns:
- Item descriptions
- DSR codes and rates
- Quantities and units
- Cost breakdowns
- Volume references

### Markdown Report
Formatted summary including:
- Executive summary
- Detailed item analysis
- Cost breakdowns by volume
- Match statistics

## 🏗️ Example Projects

### Lucknow Office Repair Project
- **Input**: `Lko_Office_Repair_revise.json`
- **References**: DAR Vol I Civil, DSR Vol 2 Civil
- **Output**: Complete cost analysis with ₹6.1 Crore total estimate

The system automatically:
1. Extracts 13 DSR items from the input document
2. Matches against 20,000+ reference rates
3. Calculates detailed cost breakdowns
4. Generates professional reports

## 🔧 Development

### Running Tests
```bash
pytest tests/
```

### Adding New Projects
1. Add input files to `examples/input_files/`
2. Configure project in `scripts/config.py`
3. Add reference databases to `examples/reference_files/`
4. Run matching using the demo script

### Web Interface Development
The Flask web application supports:
- File upload and conversion
- Multi-format file viewing (JSON, CSV, Markdown)
- Search functionality
- Responsive design

## 📋 Requirements

- Python 3.8+
- PyMuPDF (fitz) for PDF processing
- Flask for web interface
- Markdown for report formatting
- Click for CLI interface

See `requirements.txt` for complete dependency list.

## 🎯 Use Cases

- **Construction Cost Estimation**: Match project items with official DSR rates
- **Document Processing**: Convert PDF specifications to structured JSON
- **Cost Analysis**: Generate detailed project cost breakdowns
- **Rate Comparison**: Compare costs across different DSR volumes
- **Project Management**: Track and analyze construction project costs

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## 📝 Legacy Features

The original PDF2JSON functionality remains fully intact:
- Extract text and structure from PDF files
- Generate readable JSON output with text blocks and positions
- Search functionality within JSON files (CLI and Web UI)
- Page-by-page or full document conversion

## 🆘 Support

For issues and questions:
1. Check the web interface at http://localhost:5000
2. Run the demo script: `python demo_dsr_matching.py`
3. Review example outputs in `examples/output_reports/`
4. Check the configuration in `scripts/config.py`