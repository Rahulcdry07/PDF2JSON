"""PDF2JSON - Convert PDF files to JSON format and DSR rate matching."""

import sys
from pathlib import Path

__version__ = "1.0.0"

# Core converter
from .converter import PDFConversionError, PDFToXMLConverter

# Web application
from .web import AnalyticsTracker, app, create_app

# Helper utilities
from .helpers import (
    DSRMatcherHelper,
    batch_convert_pdfs,
    get_version_info,
    quick_convert,
    quick_match,
    validate_dsr_database,
)

# Logging utilities
from .logging_config import (
    HumanReadableFormatter,
    StructuredFormatter,
    get_logger,
    log_error,
    log_performance,
    setup_logging,
)

# Import utility functions from scripts

# Add scripts directory to path for imports
_scripts_dir = Path(__file__).parents[2] / "scripts"
if str(_scripts_dir) not in sys.path:
    sys.path.insert(0, str(_scripts_dir))

# DSR Matching functions
try:
    from scripts.match_dsr_rates_sqlite import (
        load_input_file,
        load_dsr_database,
        match_with_database,
    )
except ImportError:
    # Fallback if scripts not in path
    from match_dsr_rates_sqlite import load_input_file, load_dsr_database, match_with_database

# DSR Extraction functions
try:
    from scripts.dsr_extractor import extract_dsr_codes_from_lko
    from scripts.dsr_rate_extractor import extract_rates_from_dsr
except ImportError:
    from dsr_extractor import extract_dsr_codes_from_lko
    from dsr_rate_extractor import extract_rates_from_dsr

# Input conversion
try:
    from scripts.input_file_converter import convert_input_to_structured
except ImportError:
    from input_file_converter import convert_input_to_structured

# Text similarity
try:
    from scripts.text_similarity import calculate_text_similarity
except ImportError:
    from text_similarity import calculate_text_similarity

# Database management
try:
    from scripts.update_dsr_database import (
        update_rate,
        update_description,
        add_new_code,
        view_code,
        show_version_history,
    )
except ImportError:
    from update_dsr_database import (
        update_rate,
        update_description,
        add_new_code,
        view_code,
        show_version_history,
    )

__all__ = [
    # Core
    "PDFToXMLConverter",
    "PDFConversionError",
    # Web
    "app",
    "create_app",
    "AnalyticsTracker",
    # Helper utilities
    "DSRMatcherHelper",
    "quick_convert",
    "quick_match",
    "batch_convert_pdfs",
    "validate_dsr_database",
    "get_version_info",
    # Logging utilities
    "setup_logging",
    "get_logger",
    "log_performance",
    "log_error",
    "StructuredFormatter",
    "HumanReadableFormatter",
    # DSR Matching
    "load_input_file",
    "load_dsr_database",
    "match_with_database",
    # DSR Extraction
    "extract_dsr_codes_from_lko",
    "extract_rates_from_dsr",
    # Conversion
    "convert_input_to_structured",
    # Utilities
    "calculate_text_similarity",
    # Database Management
    "update_rate",
    "update_description",
    "add_new_code",
    "view_code",
    "show_version_history",
]
