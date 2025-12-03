"""Tests for DSR matching functionality."""

import pytest
import sqlite3
import json
import tempfile
from pathlib import Path
import sys

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))

from match_dsr_rates_sqlite import (
    load_input_file,
    load_dsr_database,
    match_with_database
)
from text_similarity import calculate_text_similarity


@pytest.fixture
def sample_database():
    """Create a sample SQLite database with test DSR codes."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = Path(f.name)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create table
    cursor.execute('''
        CREATE TABLE dsr_codes (
            code TEXT,
            category TEXT,
            chapter TEXT,
            section TEXT,
            description TEXT,
            unit TEXT,
            rate REAL,
            volume TEXT,
            page INTEGER,
            keywords TEXT,
            PRIMARY KEY (code, category)
        )
    ''')
    
    # Insert sample data
    sample_data = [
        ('15.12.2', 'civil', 'Chapter 15', 'Brick Work', 
         'Brick work in superstructure with common burnt clay', 'Cum', 502.75,
         'Vol 1', 120, 'brick work superstructure'),
        ('16.5.1', 'civil', 'Chapter 16', 'Plastering',
         'Cement plaster 12mm thick in single coat', 'Sqm', 180.50,
         'Vol 1', 145, 'cement plaster 12mm'),
        ('20.3.4', 'civil', 'Chapter 20', 'Painting',
         'Painting with oil paint two coats', 'Sqm', 95.25,
         'Vol 1', 189, 'oil paint two coats'),
    ]
    
    cursor.executemany('''
        INSERT INTO dsr_codes VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', sample_data)
    
    conn.commit()
    conn.close()
    
    yield db_path
    
    # Cleanup
    db_path.unlink(missing_ok=True)


@pytest.fixture
def structured_input_file():
    """Create a structured input JSON file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix=".json", delete=False) as f:
        data = {
            "metadata": {
                "type": "input_items",
                "project": "Test Project",
                "date": "2024-01-01"
            },
            "items": [
                {
                    "code": "15.12.2",
                    "clean_code": "15.12.2",
                    "description": "Brick work in superstructure",
                    "quantity": 100.5,
                    "unit": "Cum",
                    "chapter": "15",
                    "section": "Brick Work"
                },
                {
                    "code": "16.5.1",
                    "clean_code": "16.5.1",
                    "description": "Cement plaster 12mm",
                    "quantity": 250.0,
                    "unit": "Sqm",
                    "chapter": "16",
                    "section": "Plastering"
                }
            ]
        }
        json.dump(data, f, indent=2)
        input_path = Path(f.name)
    
    yield input_path
    
    # Cleanup
    input_path.unlink(missing_ok=True)


def test_load_structured_input(structured_input_file):
    """Test loading structured input file."""
    items = load_input_file(structured_input_file)
    
    assert len(items) == 2
    assert items[0]['dsr_code'] == '15.12.2'
    assert items[0]['description'] == 'Brick work in superstructure'
    assert items[0]['quantity'] == 100.5
    assert items[1]['dsr_code'] == '16.5.1'


def test_load_dsr_database(sample_database):
    """Test loading DSR database."""
    conn = load_dsr_database(sample_database)
    
    assert conn is not None
    
    # Verify database has data
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM dsr_codes")
    count = cursor.fetchone()[0]
    
    assert count > 0
    conn.close()


def test_match_with_database_exact(sample_database, structured_input_file):
    """Test matching with exact code match."""
    items = load_input_file(structured_input_file)
    conn = load_dsr_database(sample_database)
    
    matched_items = match_with_database(items, conn, similarity_threshold=0.3)
    
    assert len(matched_items) > 0
    # First item should have a rate and match_type
    assert matched_items[0]['rate'] is not None
    assert 'match_type' in matched_items[0]
    
    conn.close()


def test_match_with_database_similarity(sample_database):
    """Test matching using text similarity."""
    items = [
        {
            'dsr_code': 'UNKNOWN',
            'clean_dsr_code': 'UNKNOWN',
            'description': 'Brick work superstructure',
            'quantity': 100,
            'unit': 'Cum',
            'chapter': '15',
            'section': 'Brick Work'
        }
    ]
    
    conn = load_dsr_database(sample_database)
    matched_items = match_with_database(items, conn, similarity_threshold=0.5)
    
    # Should process the item
    assert len(matched_items) > 0
    # Item should have similarity_score
    assert 'similarity_score' in matched_items[0]
    
    conn.close()


def test_text_similarity():
    """Test text similarity calculation."""
    text1 = "Brick work in superstructure with common burnt clay"
    text2 = "Brick work in superstructure"
    
    similarity = calculate_text_similarity(text1, text2)
    
    assert 0.0 <= similarity <= 1.0
    assert similarity > 0.5  # Should be fairly similar


def test_text_similarity_different():
    """Test similarity with very different texts."""
    text1 = "Brick work in superstructure"
    text2 = "Painting with oil paint"
    
    similarity = calculate_text_similarity(text1, text2)
    
    assert 0.0 <= similarity <= 1.0
    assert similarity < 0.5  # Should be quite different
