# Project Structure

PDF2JSON follows a clean, organized directory structure:

```
PDF2JSON/
├── .github/              # GitHub Actions workflows
│   └── workflows/        # CI/CD pipelines
│
├── config/               # Configuration files
│   └── env.example       # Environment variables template
│
├── data/                 # Data directories
│   ├── reference/        # DSR reference databases
│   ├── examples/         # Example files and outputs
│   ├── uploads/          # User uploaded files
│   ├── backups/          # Database backups
│   ├── logs/             # Application logs
│   └── legacy/           # Legacy/archived files
│
├── docs/                 # Documentation
│   ├── CHANGELOG.md      # Version history
│   ├── CONTRIBUTING.md   # Contribution guidelines
│   ├── DEPLOYMENT.md     # Deployment guide
│   ├── TESTING.md        # Testing documentation
│   ├── MCP_INTEGRATION.md           # MCP setup guide

│   ├── EXCEL_CONVERTER_SUMMARY.md   # Excel feature summary
│   ├── MULTI_CATEGORY_GUIDE.md      # Multi-category guide
│   ├── STRUCTURED_INPUT_FORMAT.md   # Input format specs
│   ├── GENERIC_FEATURES.md          # Generic features
│   ├── TEST_IMPLEMENTATION_SUMMARY.md # Test summary
│   └── TEST_QUICK_REFERENCE.md      # Test quick ref
│
├── scripts/              # Utility scripts

│   ├── dsr_matcher.py            # DSR matching logic
│   ├── dsr_rate_extractor.py     # Rate extraction
│   ├── match_dsr_rates_sqlite.py # SQLite-based matching
│   ├── input_file_converter.py   # Input conversion
│   ├── create_master_database.py # Database creation
│   ├── update_dsr_database.py    # Database updates
│   └── ...                        # Other utilities
│
├── src/                  # Source code
│   └── pdf2json/         # Main package
│       ├── __init__.py
│       ├── converter.py  # PDF to JSON converter
│       └── web.py        # Flask web application
│
├── templates/            # Web templates
│   ├── index.html                 # Main page
│   ├── upload.html                # Upload page
│   ├── cost_estimation.html       # Cost estimation
│   ├── excel_converter.html       # Excel converter
│   ├── database_manager.html      # Database management
│   ├── mcp_interface.html         # MCP testing
│   └── ...                        # Other templates
│
├── tests/                # Test suite
│   ├── conftest.py                # Test configuration
│   ├── test_converter.py          # PDF converter tests
│   ├── test_dsr_matcher.py        # Matcher tests
│   ├── test_excel_converter.py    # Excel converter tests
│   ├── test_web_interface.py      # Web interface tests
│   └── ...                        # Other tests
│
├── .dockerignore         # Docker ignore file
├── .gitignore            # Git ignore file
├── database_manager.py   # Database management app
├── docker-compose.yml    # Docker services config
├── Dockerfile            # Docker image config
├── LICENSE               # MIT License
├── mcp_server.py         # MCP protocol server
├── mcp_web_interface.py  # MCP web testing UI
├── pyproject.toml        # Python project config
├── pytest.ini            # Pytest configuration
├── quickstart.sh         # Quick setup script
├── README.md             # Project documentation
├── requirements.txt      # Python dependencies
└── run_tests.sh          # Test runner script
```

## Directory Descriptions

### `/config`
Contains all configuration files including environment variables and settings.

### `/data`
All data files organized by purpose:
- `reference/` - DSR databases (Civil, Electrical, Plumbing, etc.)
- `examples/` - Sample input/output files for testing
- `uploads/` - Temporary user uploads
- `backups/` - Database backups with timestamps
- `logs/` - Application logs
- `legacy/` - Archived or deprecated files

### `/docs`
Comprehensive documentation:
- Setup and deployment guides
- Feature documentation
- Testing guides
- Version history

### `/scripts`
Standalone utility scripts for:
- Excel to PDF conversion
- DSR rate matching
- Database management
- Data transformation

### `/src`
Main application source code:
- PDF to JSON converter
- Web interface
- Core business logic

### `/templates`
Flask HTML templates for the web interface

### `/tests`
Complete test suite with 60+ tests covering all functionality

## Migration Notes

If you have existing paths in your code, update them:

**Old paths** → **New paths**
```
reference_files/  → data/reference/
examples/         → data/examples/
uploads/          → data/uploads/
backups/          → data/backups/
logs/             → data/logs/
.env.example      → config/env.example
```

## Benefits

✅ **Organized**: Clear separation of concerns
✅ **Scalable**: Easy to add new features
✅ **Professional**: Industry-standard structure
✅ **Maintainable**: Easy to navigate and understand
✅ **Clean**: Root directory not cluttered
