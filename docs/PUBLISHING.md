# Publishing to PyPI Guide

This guide explains how to build, test, and publish the `estimatex-dsr` package to PyPI.

## Prerequisites

1. **Create PyPI Account**
   - Go to https://pypi.org/account/register/
   - Verify your email address
   - Enable 2FA (recommended)

2. **Create API Token**
   - Go to https://pypi.org/manage/account/
   - Scroll to "API tokens" section
   - Create a new token with scope for entire account or specific project
   - Save the token securely (you'll only see it once)

3. **Install Build Tools**
   ```bash
   pip install --upgrade build twine
   ```

## Version Management

### Semantic Versioning
We follow [Semantic Versioning](https://semver.org/): `MAJOR.MINOR.PATCH`

- **MAJOR**: Incompatible API changes
- **MINOR**: Add functionality (backwards-compatible)
- **PATCH**: Bug fixes (backwards-compatible)

### Update Version

1. **Edit `pyproject.toml`**
   ```toml
   [project]
   version = "1.0.0"  # Update this
   ```

2. **Edit `src/estimatex/__init__.py`**
   ```python
   __version__ = "1.0.0"  # Update this
   ```

3. **Update CHANGELOG.md**
   ```markdown
   ## [1.0.0] - 2025-12-04
   ### Added
   - New feature X
   ### Changed
   - Modified Y
   ### Fixed
   - Bug Z
   ```

## Building the Package

### 1. Clean Previous Builds
```bash
rm -rf dist/ build/ *.egg-info
```

### 2. Build Distribution Files
```bash
python -m build
```

This creates:
- `dist/estimatex_dsr-1.0.0-py3-none-any.whl` (wheel)
- `dist/estimatex-dsr-1.0.0.tar.gz` (source)

### 3. Verify Build
```bash
# Check package contents
tar -tzf dist/estimatex-dsr-1.0.0.tar.gz

# Verify wheel
unzip -l dist/estimatex_dsr-1.0.0-py3-none-any.whl
```

## Testing Before Publishing

### 1. Test Installation Locally
```bash
# Create test environment
python -m venv test_env
source test_env/bin/activate

# Install from local wheel
pip install dist/estimatex_dsr-1.0.0-py3-none-any.whl

# Test imports
python -c "from estimatex import PDFToXMLConverter; print('✅ Import successful')"
python -c "from estimatex import app, create_app; print('✅ Web app import successful')"
python -c "from estimatex import match_with_database; print('✅ DSR matching import successful')"

# Test CLI
estimatex --help

# Deactivate and clean up
deactivate
rm -rf test_env
```

### 2. Run All Tests
```bash
pytest tests/ -v
```

### 3. Check Package Metadata
```bash
twine check dist/*
```

## Publishing to Test PyPI (Recommended First)

### 1. Configure Test PyPI
Create `~/.pypirc`:
```ini
[distutils]
index-servers =
    pypi
    testpypi

[testpypi]
repository = https://test.pypi.org/legacy/
username = __token__
password = pypi-YOUR-TEST-PYPI-TOKEN-HERE

[pypi]
repository = https://upload.pypi.org/legacy/
username = __token__
password = pypi-YOUR-PRODUCTION-PYPI-TOKEN-HERE
```

### 2. Upload to Test PyPI
```bash
twine upload --repository testpypi dist/*
```

### 3. Test Installation from Test PyPI
```bash
# Create test environment
python -m venv test_testpypi
source test_testpypi/bin/activate

# Install from Test PyPI
pip install --index-url https://test.pypi.org/simple/ \
    --extra-index-url https://pypi.org/simple/ \
    estimatex-dsr

# Test functionality
python -c "from estimatex import PDFToXMLConverter"

# Clean up
deactivate
rm -rf test_testpypi
```

## Publishing to Production PyPI

### 1. Final Pre-flight Checks
- [ ] All tests passing
- [ ] Version number updated
- [ ] CHANGELOG.md updated
- [ ] README.md accurate
- [ ] Documentation complete
- [ ] Tested on Test PyPI

### 2. Upload to PyPI
```bash
twine upload dist/*
```

### 3. Verify Publication
```bash
# Check on PyPI
open https://pypi.org/project/estimatex-dsr/

# Install from PyPI
pip install estimatex-dsr

# Test installation
python -c "from estimatex import PDFToXMLConverter; print('✅ Published successfully!')"
```

### 4. Create Git Tag
```bash
git tag -a v1.0.0 -m "Release version 1.0.0"
git push origin v1.0.0
```

## Automated Publishing with GitHub Actions

### Create `.github/workflows/publish.yml`
```yaml
name: Publish to PyPI

on:
  release:
    types: [published]

jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        pip install --upgrade pip
        pip install build twine
    
    - name: Build package
      run: python -m build
    
    - name: Check package
      run: twine check dist/*
    
    - name: Publish to PyPI
      env:
        TWINE_USERNAME: __token__
        TWINE_PASSWORD: ${{ secrets.PYPI_TOKEN }}
      run: twine upload dist/*
```

### Setup GitHub Secret
1. Go to repository Settings → Secrets → Actions
2. Create new secret: `PYPI_TOKEN`
3. Paste your PyPI API token

## Usage After Publishing

### Installation
```bash
# Basic installation
pip install estimatex-dsr

# With development dependencies
pip install estimatex-dsr[dev]
```

### Import Examples
```python
# Core converter
from estimatex import PDFToXMLConverter

# Web application
from estimatex import app, create_app

# DSR matching
from estimatex import match_with_database, load_dsr_database

# Utilities
from estimatex import calculate_text_similarity, ExcelToPDFConverter
```

## Troubleshooting

### Package Name Already Taken
If `estimatex-dsr` is taken, modify in `pyproject.toml`:
```toml
name = "estimatex-dsr-yourname"
```

### Import Errors After Installation
Check that `src/` directory structure is correct:
```
src/
└── estimatex/
    ├── __init__.py  # Must export all public APIs
    ├── converter.py
    └── web.py
```

### Missing Dependencies
Ensure all dependencies in `pyproject.toml` have version constraints:
```toml
dependencies = [
    "PyMuPDF>=1.23.0",
    "Flask>=2.0.0,<4.0.0",
]
```

### Large Package Size
Check what's being included:
```bash
tar -tzf dist/estimatex-dsr-1.0.0.tar.gz | grep -E '\.(db|pdf|xlsx)$'
```

Exclude large files in `.gitignore` and ensure they're not in `dist/`.

## Best Practices

1. **Always test on Test PyPI first**
2. **Never publish untested code**
3. **Use semantic versioning consistently**
4. **Keep CHANGELOG.md updated**
5. **Tag releases in git**
6. **Document breaking changes clearly**
7. **Maintain backwards compatibility when possible**
8. **Include comprehensive examples in README**

## Quick Reference

```bash
# Complete publishing workflow
rm -rf dist/ build/ *.egg-info
python -m build
twine check dist/*
pytest tests/ -v
twine upload --repository testpypi dist/*  # Test first
twine upload dist/*                        # Production
git tag -a v1.0.0 -m "Release v1.0.0"
git push origin v1.0.0
```

## Resources

- PyPI: https://pypi.org/
- Test PyPI: https://test.pypi.org/
- Python Packaging Guide: https://packaging.python.org/
- Semantic Versioning: https://semver.org/
- Twine Documentation: https://twine.readthedocs.io/
