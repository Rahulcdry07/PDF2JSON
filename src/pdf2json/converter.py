"""PDF to JSON converter using PyMuPDF."""

import fitz  # PyMuPDF
import json
from pathlib import Path
from typing import Optional, List, Dict, Tuple


class PDFToXMLConverter:
    """Convert PDF files to XML format."""

    def __init__(self, pdf_path: str):
        """Initialize converter with PDF file path.
        
        Args:
            pdf_path: Path to the PDF file
        """
        self.pdf_path = Path(pdf_path)
        if not self.pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        self.doc = fitz.open(str(self.pdf_path))
    
    @staticmethod
    def _is_valid_xml_char(char: str) -> bool:
        """Check if a character is valid in XML 1.0.
        
        Args:
            char: Character to check
            
        Returns:
            True if character is valid in XML
        """
        codepoint = ord(char)
        return (
            0x20 <= codepoint <= 0xD7FF or
            codepoint in (0x9, 0xA, 0xD) or
            0xE000 <= codepoint <= 0xFFFD or
            0x10000 <= codepoint <= 0x10FFFF
        )
    
    def _detect_tables(self, page: fitz.Page) -> List[Dict]:
        """Detect tables in a page using text positioning analysis.
        
        Args:
            page: PyMuPDF page object
            
        Returns:
            List of detected tables with their structure
        """
        tables = []
        
        # Try to find tables using PyMuPDF's table detection
        tabs = page.find_tables()
        
        if tabs and tabs.tables:
            for idx, table in enumerate(tabs.tables):
                table_data = {
                    'index': idx,
                    'bbox': table.bbox,
                    'rows': [],
                    'row_count': 0,
                    'col_count': 0
                }
                
                # Extract table content
                try:
                    table_extract = table.extract()
                    if table_extract:
                        table_data['rows'] = table_extract
                        table_data['row_count'] = len(table_extract)
                        table_data['col_count'] = len(table_extract[0]) if table_extract else 0
                        tables.append(table_data)
                except Exception:
                    # Skip tables that can't be extracted
                    continue
        
        return tables
    
    def convert(self, include_metadata: bool = False, extract_tables: bool = False) -> Dict:
        """Convert PDF to JSON structure.
        
        Args:
            include_metadata: Whether to include PDF metadata
            extract_tables: Whether to detect and extract tables
            
        Returns:
            Dict representing the document structure
        """
        doc_data = {
            "source": self.pdf_path.name,
            "pages": len(self.doc),
            "pages_data": []
        }
        
        # Add metadata if requested
        if include_metadata:
            metadata = self.doc.metadata
            doc_data["metadata"] = {key: value for key, value in metadata.items() if value}
        
        # Process each page
        for page_num, page in enumerate(self.doc, start=1):
            page_data = {
                "number": page_num,
                "width": page.rect.width,
                "height": page.rect.height,
                "blocks": []
            }
            
            # Extract text
            text = page.get_text()
            if text.strip():
                page_data["text"] = text
            
            # Extract text blocks with positions
            blocks = page.get_text("dict")["blocks"]
            
            for block in blocks:
                if block.get("type") == 0:  # Text block
                    block_data = {
                        "bbox": [round(coord, 2) for coord in block["bbox"]],
                        "lines": []
                    }
                    
                    # Extract lines within block
                    for line in block.get("lines", []):
                        line_text = ""
                        for span in line.get("spans", []):
                            line_text += span.get("text", "")
                        if line_text.strip():
                            block_data["lines"].append(line_text)
                    
                    if block_data["lines"]:
                        page_data["blocks"].append(block_data)
            
            # Extract tables if requested
            if extract_tables:
                tables = self._detect_tables(page)
                if tables:
                    page_data["tables"] = []
                    
                    for table_data in tables:
                        table_dict = {
                            "index": table_data['index'],
                            "bbox": [round(coord, 2) for coord in table_data['bbox']],
                            "rows": table_data['rows'],
                            "row_count": table_data['row_count'],
                            "col_count": table_data['col_count']
                        }
                        page_data["tables"].append(table_dict)
            
            doc_data["pages_data"].append(page_data)
        
        return {"document": doc_data}
    
    def save_json(self, output_path: str, include_metadata: bool = False, 
                  extract_tables: bool = False, indent: int = 2) -> None:
        """Convert PDF and save as JSON file.
        
        Args:
            output_path: Path to save the JSON file
            include_metadata: Whether to include PDF metadata
            extract_tables: Whether to detect and extract tables
            indent: JSON indentation level
        """
        data = self.convert(include_metadata=include_metadata, extract_tables=extract_tables)
        
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with output_file.open('w', encoding='utf-8') as f:
            json.dump(data, f, indent=indent, ensure_ascii=False)
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - close PDF document."""
        if self.doc:
            self.doc.close()
