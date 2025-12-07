# Test Suite Documentation

This directory contains the comprehensive test suite for the EstimateX DSR Rate Matching System.

## Test Structure

### Test Files

1. **test_converter.py** - PDF to JSON conversion tests
   - PDF parsing and conversion
   - Table extraction
   - XML/JSON output generation
   - Context manager functionality

2. **test_dsr_matcher.py** - DSR rate matching tests
   - Input file loading (structured/unstructured)
   - DSR code searching
   - Text similarity calculations
   - Report generation

3. **test_database_operations.py** - Database management tests
   - Version tracking and updates
   - Rate and description updates
   - Adding new codes
   - Master database creation
   - Multi-category support
   - Batch updates from CSV

4. **test_web_interface.py** - Flask web application tests
   - Route testing
   - File upload functionality
   - Cost estimation interface
   - Search functionality
   - Template rendering

5. **test_text_similarity.py** - Text matching algorithm tests
   - Similarity calculations
   - Fuzzy matching
   - Jaccard similarity
   - Cosine similarity
   - Edge cases

6. **test_input_converter.py** - Input format conversion tests
   - Unstructured to structured conversion
   - Code extraction
   - Data preservation

## Running Tests

### Run all tests
```bash
pytest
```

### Run specific test file
```bash
pytest tests/test_dsr_matcher.py
```

### Run specific test function
```bash
pytest tests/test_dsr_matcher.py::test_search_dsr_code_exact_match
```

### Run with verbose output
```bash
pytest -v
```

### Run with coverage report
```bash
pytest --cov=src --cov=scripts --cov-report=html
```

### Run only fast tests (exclude slow tests)
```bash
pytest -m "not slow"
```

### Run only integration tests
```bash
pytest -m integration
```

### Run only web interface tests
```bash
pytest -m web
```

## Test Coverage

The test suite covers:

### Core Functionality (90%+ coverage target)
- ✅ PDF to JSON conversion
- ✅ DSR rate matching
- ✅ Database operations (CRUD)
- ✅ Text similarity algorithms
- ✅ Input format conversion
- ✅ Version management
- ✅ Web interface routes

### Edge Cases
- ✅ Empty inputs
- ✅ Invalid file paths
- ✅ Non-existent DSR codes
- ✅ Duplicate codes
- ✅ Case sensitivity
- ✅ Special characters
- ✅ File size limits

### Error Handling
- ✅ File not found errors
- ✅ Invalid JSON format
- ✅ Database connection errors
- ✅ Missing required fields
- ✅ Type validation

## Required Test Dependencies

Install test dependencies:
```bash
pip install pytest pytest-cov
```

Or install all project dependencies:
```bash
pip install -r requirements.txt
```

## Writing New Tests

### Test Naming Convention
- Test files: `test_*.py`
- Test classes: `Test*`
- Test functions: `test_*`

### Example Test Structure
```python
import pytest

@pytest.fixture
def sample_data():
    """Create sample test data."""
    # Setup
    data = create_test_data()
    yield data
    # Teardown (if needed)
    cleanup(data)

def test_functionality(sample_data):
    """Test specific functionality."""
    result = function_under_test(sample_data)
    assert result == expected_value
```

### Using Markers
```python
@pytest.mark.slow
def test_large_dataset():
    """Test with large dataset."""
    pass

@pytest.mark.integration
def test_full_workflow():
    """Test complete workflow."""
    pass

@pytest.mark.web
def test_api_endpoint():
    """Test web API endpoint."""
    pass
```

## Continuous Integration

Tests are designed to run in CI/CD pipelines:
```yaml
# Example GitHub Actions workflow
- name: Run tests
  run: |
    pip install -r requirements.txt
    pytest --cov=src --cov=scripts
```

## Test Data

Test files use temporary files and in-memory databases:
- PDF fixtures created using PyMuPDF
- SQLite databases created in temp directories
- JSON files created as temporary files
- Automatic cleanup after tests

## Troubleshooting

### Import Errors
If you encounter import errors, ensure:
1. You're in the project root directory
2. Virtual environment is activated
3. All dependencies are installed

### Path Issues
Tests use `conftest.py` to configure paths automatically. If paths are incorrect:
```python
# Check Python path
import sys
print(sys.path)
```

### Database Lock Errors
If SQLite database locks occur:
- Ensure all connections are properly closed
- Check for concurrent access in fixtures
- Verify cleanup in teardown code

## Performance

- Fast tests: < 100ms
- Integration tests: < 1s
- Full test suite: < 30s

Run performance profiling:
```bash
pytest --durations=10
```

## Best Practices

1. **Isolation**: Each test should be independent
2. **Cleanup**: Use fixtures with teardown for resources
3. **Descriptive Names**: Test names should describe what they test
4. **Single Assertion**: Prefer one assertion per test (when possible)
5. **Fixtures**: Reuse common setup code via fixtures
6. **Mocking**: Mock external dependencies (network, file system)
7. **Coverage**: Aim for 80%+ code coverage

## Future Enhancements

- [ ] Add performance benchmarking tests
- [ ] Add load testing for web interface
- [ ] Add security testing (SQL injection, XSS)
- [ ] Add end-to-end workflow tests
- [ ] Add property-based testing with Hypothesis
- [ ] Add mutation testing with mutmut
