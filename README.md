# PDF2JSON

A Python CLI tool to convert PDF files to JSON format using PyMuPDF.

## Features

- Extract text and structure from PDF files
- Generate readable JSON output with text blocks and positions
- **Search functionality**: Search keywords within JSON files (CLI and Web UI)
- Command-line interface with customizable options
- Web UI for upload, conversion, viewing, and searching
- Supports page-by-page or full document conversion

## Installation

1. Create a virtual environment:
```bash
python3 -m venv .venv
source .venv/bin/activate  # On macOS/Linux
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### CLI

Convert a PDF to JSON:
```bash
python -m src.pdf2xml.cli input.pdf
```

Convert with metadata:
```bash
python -m src.pdf2xml.cli input.pdf --include-metadata
```

View help:
```bash
python -m src.pdf2xml.cli --help
```

### Web UI

Start the web server:
```bash
PYTHONPATH=src python -m pdf2xml.web
```

Open http://127.0.0.1:5000 in your browser to upload PDFs, view JSON output, and search within files.

**Search Features:**
- Search within individual JSON files to highlight all matching indexed items
- Real-time highlighting as you type in the current file
- Submit search form to highlight all matches and scroll to the first result

### Reading JSON Files

Print all text blocks:
```bash
python scripts/read_json.py --json output.json --print-text
```

Search for text:
```bash
python scripts/read_json.py --json output.json --search "keyword"
```

### Web UI Features

- **Upload & Convert**: Upload PDF files and convert them to JSON
- **View JSON**: Display JSON content with search highlighting within the current file
- **File Search**: Search within the current JSON file and highlight all matching indexed items
- **Global Search**: Search across all converted JSON files for keywords (available in the file view)
- **Clickable Results**: Click on search results to jump directly to the matching location in the JSON file
- **Download**: Download the JSON files

## Example

Try the example PDF:
```bash
python -m src.pdf2xml.cli examples/sample.pdf
```

## Development

Run tests:
```bash
python -m pytest tests/
```

## Requirements

- Python 3.8+
- PyMuPDF (fitz)
- click

## License

MIT
