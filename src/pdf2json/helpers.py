"""Helper functions and utilities for pdf2json library."""

import logging
from pathlib import Path
from typing import Union, List, Dict, Optional
import sqlite3

logger = logging.getLogger(__name__)


class DSRMatcherHelper:
    """Helper class for DSR rate matching operations.
    
    Simplifies common DSR matching tasks with sensible defaults.
    
    Example:
        >>> matcher = DSRMatcherHelper("data/reference/DSR_combined.db")
        >>> results = matcher.match_items([
        ...     {"code": "1.1", "description": "Excavation", "quantity": 100}
        ... ])
        >>> for result in results:
        ...     print(f"{result['code']}: ₹{result['total_cost']}")
    """
    
    def __init__(self, db_path: Union[str, Path]):
        """Initialize with DSR database path.
        
        Args:
            db_path: Path to SQLite DSR database
            
        Raises:
            FileNotFoundError: If database file doesn't exist
        """
        self.db_path = Path(db_path)
        if not self.db_path.exists():
            raise FileNotFoundError(f"Database not found: {db_path}")
        
        self.conn = sqlite3.connect(str(self.db_path))
        logger.info(f"Connected to DSR database: {self.db_path.name}")
    
    def match_items(self, items: List[Dict], similarity_threshold: float = 0.3) -> List[Dict]:
        """Match construction items with DSR rates.
        
        Args:
            items: List of items with 'code', 'description', 'quantity'
            similarity_threshold: Minimum similarity for fuzzy matching (0.0-1.0)
            
        Returns:
            List of matched results with rates and costs
        """
        from pdf2json import match_with_database
        
        # Ensure items have required fields
        formatted_items = []
        for item in items:
            formatted_items.append({
                'dsr_code': item.get('code', ''),
                'clean_dsr_code': item.get('clean_code', item.get('code', '')),
                'description': item.get('description', ''),
                'quantity': item.get('quantity', 0),
                'unit': item.get('unit', ''),
                'chapter': item.get('chapter', ''),
                'section': item.get('section', '')
            })
        
        return match_with_database(formatted_items, self.conn, similarity_threshold)
    
    def search_by_code(self, code: str) -> Optional[Dict]:
        """Search for DSR entry by exact code.
        
        Args:
            code: DSR code to search
            
        Returns:
            DSR entry dict or None if not found
        """
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT * FROM dsr_rates WHERE clean_code = ? OR code = ?",
            (code.strip(), code.strip())
        )
        row = cursor.fetchone()
        
        if row:
            columns = [desc[0] for desc in cursor.description]
            return dict(zip(columns, row))
        return None
    
    def search_by_description(self, description: str, limit: int = 10) -> List[Dict]:
        """Search for DSR entries by description keyword.
        
        Args:
            description: Search keyword
            limit: Maximum results to return
            
        Returns:
            List of matching DSR entries
        """
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT * FROM dsr_rates WHERE description LIKE ? LIMIT ?",
            (f"%{description}%", limit)
        )
        rows = cursor.fetchall()
        
        columns = [desc[0] for desc in cursor.description]
        return [dict(zip(columns, row)) for row in rows]
    
    def get_statistics(self) -> Dict:
        """Get database statistics.
        
        Returns:
            Dict with total codes, categories, chapters
        """
        cursor = self.conn.cursor()
        
        # Total codes
        cursor.execute("SELECT COUNT(*) FROM dsr_rates")
        total_codes = cursor.fetchone()[0]
        
        # Categories
        cursor.execute("SELECT COUNT(DISTINCT category) FROM dsr_rates")
        categories = cursor.fetchone()[0]
        
        # Chapters
        cursor.execute("SELECT COUNT(DISTINCT chapter_no) FROM dsr_rates WHERE chapter_no IS NOT NULL")
        chapters = cursor.fetchone()[0]
        
        return {
            'total_codes': total_codes,
            'categories': categories,
            'chapters': chapters,
            'database': self.db_path.name
        }
    
    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            logger.debug(f"Closed database connection: {self.db_path.name}")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


def quick_convert(pdf_path: Union[str, Path], 
                  output_path: Optional[Union[str, Path]] = None,
                  **kwargs) -> Dict:
    """Quick PDF to JSON conversion with automatic output naming.
    
    Args:
        pdf_path: Input PDF file
        output_path: Output JSON file (optional, auto-generated if None)
        **kwargs: Additional converter options
        
    Returns:
        Converted JSON data as dict
        
    Example:
        >>> data = quick_convert("document.pdf", extract_tables=True)
        >>> print(f"Converted {data['document']['pages']} pages")
    """
    from pdf2json import PDFToXMLConverter
    
    pdf_path = Path(pdf_path)
    if output_path is None:
        output_path = pdf_path.with_suffix('.json')
    
    with PDFToXMLConverter(pdf_path) as converter:
        data = converter.convert(**kwargs)
        converter.save_json(output_path, **kwargs)
    
    logger.info(f"Converted: {pdf_path.name} → {output_path}")
    return data


def quick_match(input_items: Union[List[Dict], str, Path],
                db_path: Union[str, Path] = None,
                similarity_threshold: float = 0.3) -> List[Dict]:
    """Quick DSR rate matching with automatic database detection.
    
    Args:
        input_items: List of items or path to JSON file
        db_path: DSR database path (auto-detected if None)
        similarity_threshold: Minimum similarity for fuzzy matching
        
    Returns:
        List of matched results
        
    Example:
        >>> results = quick_match([
        ...     {"code": "1.1", "description": "Excavation", "quantity": 100}
        ... ])
        >>> total = sum(r['total_cost'] for r in results)
    """
    from pdf2json import load_input_file, load_dsr_database, match_with_database
    
    # Load items
    if isinstance(input_items, (str, Path)):
        items = load_input_file(Path(input_items))
    else:
        items = input_items
    
    # Auto-detect database
    if db_path is None:
        possible_paths = [
            Path("data/reference/DSR_combined.db"),
            Path("reference_files/DSR_combined.db"),
            Path("DSR_combined.db")
        ]
        for path in possible_paths:
            if path.exists():
                db_path = path
                break
        
        if db_path is None:
            raise FileNotFoundError("Could not auto-detect DSR database. Please provide db_path.")
    
    # Match
    conn = load_dsr_database(Path(db_path))
    try:
        results = match_with_database(items, conn, similarity_threshold)
        return results
    finally:
        conn.close()


def batch_convert_pdfs(pdf_directory: Union[str, Path],
                       output_directory: Optional[Union[str, Path]] = None,
                       **kwargs) -> List[Path]:
    """Convert all PDFs in a directory.
    
    Args:
        pdf_directory: Directory containing PDF files
        output_directory: Output directory (same as input if None)
        **kwargs: Converter options
        
    Returns:
        List of created JSON file paths
        
    Example:
        >>> converted = batch_convert_pdfs("pdfs/", "json/", extract_tables=True)
        >>> print(f"Converted {len(converted)} files")
    """
    from pdf2json import PDFToXMLConverter
    
    pdf_dir = Path(pdf_directory)
    out_dir = Path(output_directory) if output_directory else pdf_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    
    converted = []
    for pdf_file in pdf_dir.glob("*.pdf"):
        try:
            output_file = out_dir / pdf_file.with_suffix('.json').name
            PDFToXMLConverter.convert_file(pdf_file, output_file, **kwargs)
            converted.append(output_file)
            logger.info(f"Converted: {pdf_file.name}")
        except Exception as e:
            logger.error(f"Failed to convert {pdf_file.name}: {e}")
    
    return converted


def validate_dsr_database(db_path: Union[str, Path]) -> Dict:
    """Validate DSR database structure and contents.
    
    Args:
        db_path: Path to SQLite database
        
    Returns:
        Dict with validation results and statistics
        
    Example:
        >>> results = validate_dsr_database("DSR_combined.db")
        >>> if results['valid']:
        ...     print(f"Database OK: {results['total_codes']} codes")
    """
    db_path = Path(db_path)
    if not db_path.exists():
        return {'valid': False, 'error': 'Database file not found'}
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Check table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='dsr_rates'")
        if not cursor.fetchone():
            return {'valid': False, 'error': 'Table dsr_rates not found'}
        
        # Check required columns
        cursor.execute("PRAGMA table_info(dsr_rates)")
        columns = {row[1] for row in cursor.fetchall()}
        required = {'code', 'description', 'rate', 'unit'}
        missing = required - columns
        
        if missing:
            return {'valid': False, 'error': f'Missing columns: {missing}'}
        
        # Get statistics
        cursor.execute("SELECT COUNT(*) FROM dsr_rates")
        total_codes = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM dsr_rates WHERE rate IS NULL OR rate = 0")
        null_rates = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'valid': True,
            'total_codes': total_codes,
            'null_rates': null_rates,
            'columns': list(columns),
            'database': db_path.name
        }
        
    except Exception as e:
        return {'valid': False, 'error': str(e)}


def get_version_info() -> Dict:
    """Get version information for pdf2json and dependencies.
    
    Returns:
        Dict with version numbers
        
    Example:
        >>> info = get_version_info()
        >>> print(f"pdf2json version: {info['pdf2json']}")
    """
    import sys
    try:
        import fitz
        pymupdf_version = fitz.version[0]
    except:
        pymupdf_version = "unknown"
    
    try:
        import flask
        flask_version = flask.__version__
    except:
        flask_version = "not installed"
    
    from pdf2json import __version__
    
    return {
        'pdf2json': __version__,
        'python': sys.version.split()[0],
        'pymupdf': pymupdf_version,
        'flask': flask_version
    }
