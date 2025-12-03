# Excel to PDF Converter - User Guide

## Overview
The Excel to PDF Converter allows you to extract individual sheets from Excel workbooks (.xlsx, .xls) and convert them to professionally formatted PDF documents.

## Features

### 1. **Command-Line Interface**
Use the CLI for quick conversions and batch processing:

```bash
# List all sheets in an Excel file
python scripts/excel_to_pdf.py myfile.xlsx --list

# Convert a single sheet
python scripts/excel_to_pdf.py myfile.xlsx output.pdf --sheet "Sheet1"

# Convert multiple sheets to one PDF
python scripts/excel_to_pdf.py myfile.xlsx combined.pdf --sheets "Sheet1,Sheet2,Sheet3"

# Convert all sheets to separate PDFs
python scripts/excel_to_pdf.py myfile.xlsx output_dir/ --all-sheets

# Use landscape orientation
python scripts/excel_to_pdf.py myfile.xlsx output.pdf --sheet "Data" --landscape

# Use Letter page size instead of A4
python scripts/excel_to_pdf.py myfile.xlsx output.pdf --sheet "Report" --page-size Letter
```

### 2. **Web Interface**
Access the user-friendly web interface at **http://localhost:8000/excel-converter**

Features:
- Drag and drop Excel files
- Visual sheet selection with checkboxes
- Select all/individual sheets
- Choose orientation (Portrait/Landscape)
- Choose page size (A4/Letter)
- Choose output mode:
  - **Separate PDFs**: Each sheet as a separate PDF file (ZIP download)
  - **Combined PDF**: All selected sheets in one PDF file

### 3. **Python API**
Integrate into your own scripts:

```python
from pathlib import Path
from excel_to_pdf import ExcelToPDFConverter
from reportlab.lib.pagesizes import A4

# Initialize converter
converter = ExcelToPDFConverter(Path("data.xlsx"))

# List available sheets
sheets = converter.list_sheets()
print(f"Available sheets: {sheets}")

# Convert single sheet
converter.convert_sheet_to_pdf(
    "Sheet1",
    Path("output.pdf"),
    page_size=A4,
    orientation='portrait'
)

# Convert multiple sheets to one PDF
converter.convert_multiple_sheets(
    ["Sheet1", "Sheet2", "Sheet3"],
    Path("combined.pdf")
)

# Convert all sheets to separate PDFs
created_files = converter.convert_all_sheets(
    Path("output_directory/")
)

# Close the converter
converter.close()
```

## PDF Formatting

The converter applies professional formatting to the PDFs:

- **Header Row**: Purple gradient background (#667eea)
- **Data Rows**: Alternating row colors for readability
- **Table Borders**: Clean grid lines
- **Font Styling**: Bold headers, regular data
- **Auto-sizing**: Tables fit page width automatically
- **Page Breaks**: Automatic pagination for large datasets

## Use Cases

1. **DSR Rate Reports**: Convert DSR database sheets to PDF for distribution
2. **Financial Reports**: Export Excel financial data to PDF
3. **Data Archiving**: Convert dynamic Excel sheets to static PDF format
4. **Client Deliverables**: Professional PDF reports from Excel data
5. **Print-ready Documents**: Formatted tables for printing
6. **Batch Processing**: Convert multiple Excel files automatically

## Testing

Run the comprehensive test suite:

```bash
# Run all Excel converter tests
pytest tests/test_excel_converter.py -v

# Run with coverage
pytest tests/test_excel_converter.py --cov=scripts/excel_to_pdf --cov-report=html
```

The test suite includes:
- 21 test cases covering all functionality
- Edge cases (empty sheets, special characters, large datasets)
- Format validation (portrait/landscape, A4/Letter)
- Error handling
- Multiple conversion scenarios

## Integration with Main Web App

The Excel converter is fully integrated into the main web application:

1. Start the web server: `python -m src.pdf2json.web`
2. Navigate to **http://localhost:8000**
3. Click **"📊 Excel to PDF"** in the navigation
4. Upload your Excel file and convert sheets

## Examples

### Example 1: DSR Database Sheet Conversion

```bash
# Convert DSR rate sheet to PDF
python scripts/excel_to_pdf.py reference_files/DSR_Rates.xlsx rates.pdf --sheet "Civil Works"
```

### Example 2: Monthly Report

```bash
# Convert all sheets from monthly report
python scripts/excel_to_pdf.py Monthly_Report_Dec_2025.xlsx reports/ --all-sheets --landscape
```

### Example 3: Client Presentation

```bash
# Combine specific sheets for client
python scripts/excel_to_pdf.py Project_Data.xlsx client_report.pdf --sheets "Summary,Costs,Timeline"
```

## Technical Details

- **Dependencies**: openpyxl (Excel reading), reportlab (PDF generation)
- **Supported Formats**: .xlsx, .xls
- **Page Sizes**: A4, Letter
- **Orientations**: Portrait, Landscape
- **Max File Size**: Limited by available memory
- **Output Formats**: Single PDF or ZIP of multiple PDFs

## Troubleshooting

**Issue**: "Sheet not found"
- **Solution**: Use `--list` to see available sheet names

**Issue**: "File too large"
- **Solution**: Convert sheets separately or increase available memory

**Issue**: "Empty sheet error"
- **Solution**: Ensure the sheet contains data before conversion

**Issue**: "Formatting issues"
- **Solution**: Try different orientations or page sizes

## Future Enhancements

Planned features:
- Custom column widths
- Header/footer customization
- Page numbering
- Watermarks
- Multiple page sizes
- Custom styling themes
- Excel formulas in PDF
- Chart/image embedding
