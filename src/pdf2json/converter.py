"""PDF to JSON converter using PyMuPDF."""

import fitz  # PyMuPDF
import json
import logging
from pathlib import Path
from typing import Optional, List, Dict, Tuple, Union

logger = logging.getLogger(__name__)


class PDFConversionError(Exception):
    """Custom exception for PDF conversion errors."""

    pass


class PDFToXMLConverter:
    """Convert PDF files to JSON format with advanced features.

    This converter provides methods to extract text, tables, and metadata
    from PDF files and export to JSON format.

    Example:
        >>> with PDFToXMLConverter("document.pdf") as converter:
        >>>     data = converter.convert(extract_tables=True)
        >>>     converter.save_json("output.json")

    Args:
        pdf_path: Path to PDF file (str or Path object)

    Raises:
        FileNotFoundError: If PDF file doesn't exist
        PDFConversionError: If PDF cannot be opened or processed
    """

    def __init__(self, pdf_path: Union[str, Path]):
        """Initialize with PDF file path."""
        self.pdf_path = Path(pdf_path)
        if not self.pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        try:
            self.doc = fitz.open(str(self.pdf_path))
            logger.info(f"Opened PDF: {self.pdf_path.name} ({len(self.doc)} pages)")
        except Exception as e:
            raise PDFConversionError(f"Failed to open PDF: {e}")

    @staticmethod
    def _is_valid_xml_char(char: str) -> bool:
        """Check if character is valid in XML 1.0."""
        codepoint = ord(char)
        return (
            0x20 <= codepoint <= 0xD7FF
            or codepoint in (0x9, 0xA, 0xD)
            or 0xE000 <= codepoint <= 0xFFFD
            or 0x10000 <= codepoint <= 0x10FFFF
        )

    def _detect_tables(self, page: fitz.Page) -> List[Dict]:
        """Detect tables using text positioning analysis."""
        tables = []

        tabs = page.find_tables()

        if tabs and tabs.tables:
            for idx, table in enumerate(tabs.tables):
                table_data = {
                    "index": idx,
                    "bbox": table.bbox,
                    "rows": [],
                    "row_count": 0,
                    "col_count": 0,
                }

                try:
                    table_extract = table.extract()
                    if table_extract:
                        table_data["rows"] = table_extract
                        table_data["row_count"] = len(table_extract)
                        table_data["col_count"] = len(table_extract[0]) if table_extract else 0
                        tables.append(table_data)
                except Exception:
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
        doc_data = {"source": self.pdf_path.name, "pages": len(self.doc), "pages_data": []}

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
                "blocks": [],
            }

            # Extract text
            text = page.get_text()
            if text.strip():
                page_data["text"] = text

            # Extract text blocks with positions
            blocks = page.get_text("dict")["blocks"]

            for block in blocks:
                if block.get("type") == 0:  # Text block
                    block_data = {"bbox": [round(coord, 2) for coord in block["bbox"]], "lines": []}

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
                            "index": table_data["index"],
                            "bbox": [round(coord, 2) for coord in table_data["bbox"]],
                            "rows": table_data["rows"],
                            "row_count": table_data["row_count"],
                            "col_count": table_data["col_count"],
                        }
                        page_data["tables"].append(table_dict)

            doc_data["pages_data"].append(page_data)

        return {"document": doc_data}

    def save_json(
        self,
        output_path: str,
        include_metadata: bool = False,
        extract_tables: bool = False,
        indent: int = 2,
    ) -> None:
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
        with output_file.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=indent, ensure_ascii=False)

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - close PDF document."""
        self.close()

    def close(self):
        """Close the PDF document and free resources."""
        if self.doc:
            self.doc.close()
            logger.debug(f"Closed PDF: {self.pdf_path.name}")

    @classmethod
    def convert_file(
        cls, pdf_path: Union[str, Path], output_path: Union[str, Path], **kwargs
    ) -> Path:
        """Convenience method to convert PDF in one call.

        Args:
            pdf_path: Input PDF file path
            output_path: Output JSON file path
            **kwargs: Additional arguments (include_metadata, extract_tables, indent)

        Returns:
            Path to created JSON file

        Example:
            >>> PDFToXMLConverter.convert_file("input.pdf", "output.json", extract_tables=True)
        """
        with cls(pdf_path) as converter:
            converter.save_json(output_path, **kwargs)
        return Path(output_path)

    @property
    def page_count(self) -> int:
        """Get total number of pages."""
        return len(self.doc)

    @property
    def metadata(self) -> Dict:
        """Get PDF metadata."""
        return {key: value for key, value in self.doc.metadata.items() if value}

    def get_page_text(self, page_num: int) -> str:
        """Get text content from specific page.

        Args:
            page_num: Page number (1-indexed)

        Returns:
            Extracted text from the page

        Raises:
            ValueError: If page number is invalid
        """
        if page_num < 1 or page_num > len(self.doc):
            raise ValueError(f"Invalid page number: {page_num} (valid: 1-{len(self.doc)})")

        page = self.doc[page_num - 1]
        return page.get_text()

    def get_page_tables(self, page_num: int) -> List[Dict]:
        """Extract tables from specific page.

        Args:
            page_num: Page number (1-indexed)

        Returns:
            List of detected tables with their data

        Raises:
            ValueError: If page number is invalid
        """
        if page_num < 1 or page_num > len(self.doc):
            raise ValueError(f"Invalid page number: {page_num} (valid: 1-{len(self.doc)})")

        page = self.doc[page_num - 1]
        return self._detect_tables(page)

    def convert_page(self, page_num: int, extract_tables: bool = False) -> Dict:
        """Convert single page to JSON structure.

        Args:
            page_num: Page number (1-indexed)
            extract_tables: Whether to detect and extract tables

        Returns:
            Dict representing the page structure

        Raises:
            ValueError: If page number is invalid
        """
        if page_num < 1 or page_num > len(self.doc):
            raise ValueError(f"Invalid page number: {page_num} (valid: 1-{len(self.doc)})")

        page = self.doc[page_num - 1]
        page_data = {
            "number": page_num,
            "width": page.rect.width,
            "height": page.rect.height,
            "blocks": [],
        }

        # Extract text
        text = page.get_text()
        if text.strip():
            page_data["text"] = text

        # Extract text blocks with positions
        blocks = page.get_text("dict")["blocks"]

        for block in blocks:
            if block.get("type") == 0:  # Text block
                block_data = {"bbox": [round(coord, 2) for coord in block["bbox"]], "lines": []}

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
                        "index": table_data["index"],
                        "bbox": [round(coord, 2) for coord in table_data["bbox"]],
                        "rows": table_data["rows"],
                        "row_count": table_data["row_count"],
                        "col_count": table_data["col_count"],
                    }
                    page_data["tables"].append(table_dict)

        return page_data
