# Contributing to EstimateX DSR System

Thank you for your interest in contributing! This document provides guidelines and instructions for contributing to the project.

## 🚀 Getting Started

### Prerequisites

- Python 3.8 or higher
- Git
- Virtual environment tool (venv, virtualenv, or conda)

### Setup Development Environment

1. **Fork and clone the repository**
   ```bash
   git clone https://github.com/YOUR-USERNAME/EstimateX.git
   cd EstimateX
   ```

2. **Create a virtual environment**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # On macOS/Linux
   # .venv\Scripts\activate   # On Windows
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   pip install -e ".[dev]"  # Install development dependencies
   ```

4. **Install pre-commit hooks**
   ```bash
   pip install pre-commit
   pre-commit install
   ```

5. **Run tests to verify setup**
   ```bash
   pytest tests/ -v
   ```

## 📝 Development Workflow

### 1. Create a Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/your-bug-fix
```

Branch naming conventions:
- `feature/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation updates
- `test/` - Test additions or modifications
- `refactor/` - Code refactoring

### 2. Make Your Changes

- Write clean, readable code
- Follow PEP 8 style guidelines
- Add docstrings to functions and classes
- Update documentation as needed

### 3. Write Tests

All new features and bug fixes should include tests:

```python
# tests/test_your_feature.py
import pytest

def test_your_feature():
    """Test description."""
    # Arrange
    input_data = "test"
    
    # Act
    result = your_function(input_data)
    
    # Assert
    assert result == expected_output
```

### 4. Run Tests and Linters

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src --cov=scripts --cov-report=html

# Format code with black
black src/ scripts/ tests/

# Check types with mypy
mypy src/ scripts/

# Lint with pylint
pylint src/ scripts/
```

### 5. Commit Your Changes

Write clear, descriptive commit messages:

```bash
git add .
git commit -m "feat: add support for multi-category DSR matching"
```

Commit message format:
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `test:` - Test additions or changes
- `refactor:` - Code refactoring
- `style:` - Formatting changes
- `chore:` - Maintenance tasks

### 6. Push and Create Pull Request

```bash
git push origin feature/your-feature-name
```

Then create a Pull Request on GitHub with:
- Clear title and description
- Reference to related issues
- Screenshots (if UI changes)
- Test results

## 🧪 Testing Guidelines

### Test Structure

```
tests/
├── conftest.py              # Shared fixtures
├── test_converter.py        # PDF conversion tests
├── test_dsr_matcher.py      # DSR matching tests
├── test_database_operations.py
├── test_web_interface.py
└── ...
```

### Writing Good Tests

1. **Use descriptive names**
   ```python
   def test_dsr_matcher_finds_exact_match_when_code_exists():
       pass
   ```

2. **Follow AAA pattern** (Arrange, Act, Assert)
   ```python
   def test_calculate_cost():
       # Arrange
       rate = 100.0
       quantity = 5
       
       # Act
       cost = calculate_cost(rate, quantity)
       
       # Assert
       assert cost == 500.0
   ```

3. **Use fixtures for common setup**
   ```python
   @pytest.fixture
   def sample_dsr_data():
       return {"code": "15.12.2", "rate": 502.75}
   ```

4. **Test edge cases**
   - Empty inputs
   - Invalid data
   - Boundary conditions
   - Error handling

### Test Coverage

Aim for >80% code coverage:

```bash
pytest tests/ --cov=src --cov=scripts --cov-report=term --cov-report=html
open htmlcov/index.html  # View coverage report
```

## 📋 Code Style Guidelines

### Python Style (PEP 8)

- **Line length**: 100 characters max
- **Indentation**: 4 spaces (no tabs)
- **Imports**: Grouped (standard library, third-party, local)
- **Naming**:
  - Functions/variables: `snake_case`
  - Classes: `PascalCase`
  - Constants: `UPPER_CASE`

### Docstrings

Use Google-style docstrings:

```python
def match_dsr_code(code: str, database: str) -> dict:
    """Match a DSR code against the database.
    
    Args:
        code: The DSR code to search for (e.g., "15.12.2")
        database: Path to the DSR database file
        
    Returns:
        Dictionary containing matched rate information
        
    Raises:
        ValueError: If code format is invalid
        FileNotFoundError: If database doesn't exist
        
    Example:
        >>> result = match_dsr_code("15.12.2", "DSR_combined.db")
        >>> print(result['rate'])
        502.75
    """
    pass
```

### Type Hints

Use type hints for better code clarity:

```python
from typing import List, Dict, Optional

def process_items(items: List[Dict[str, str]], 
                 threshold: float = 0.5) -> Optional[Dict]:
    """Process items with type safety."""
    pass
```

## 🐛 Bug Reports

When reporting bugs, include:

1. **Description**: Clear description of the issue
2. **Steps to reproduce**: Exact steps to reproduce the bug
3. **Expected behavior**: What should happen
4. **Actual behavior**: What actually happens
5. **Environment**: 
   - Python version
   - Operating system
   - Package versions
6. **Screenshots**: If applicable
7. **Logs**: Relevant error messages or logs

Use the bug report template when creating an issue.

## 💡 Feature Requests

When requesting features, include:

1. **Problem**: What problem does this solve?
2. **Proposed solution**: How should it work?
3. **Alternatives**: Other solutions considered
4. **Use cases**: Real-world scenarios
5. **Priority**: Low/Medium/High

## 📚 Documentation

### Update Documentation When:

- Adding new features
- Changing APIs
- Modifying configuration
- Adding new scripts
- Updating dependencies

### Documentation Files

- `README.md` - Project overview and quick start
- `DEPLOYMENT.md` - Deployment instructions
- `MCP_INTEGRATION.md` - MCP server documentation
- `TESTING.md` - Testing guide
- `scripts/USAGE.md` - Script usage guide
- `scripts/EXAMPLES.md` - Usage examples

## 🔍 Code Review Process

### As a Reviewer

- Be respectful and constructive
- Focus on code quality and maintainability
- Check for test coverage
- Verify documentation updates
- Test the changes locally

### As a Contributor

- Respond to feedback promptly
- Make requested changes
- Keep discussions focused
- Be open to suggestions

## 🏆 Recognition

Contributors are recognized in:
- README.md contributors section
- Release notes
- GitHub contributors page

## 📞 Getting Help

- **Questions**: Open a GitHub Discussion
- **Bugs**: Create an issue with bug template
- **Features**: Create an issue with feature template
- **Security**: Email security@example.com (private disclosure)

## 📜 Code of Conduct

### Our Standards

- Be welcoming and inclusive
- Be respectful of differing viewpoints
- Accept constructive criticism gracefully
- Focus on what's best for the community
- Show empathy towards others

### Unacceptable Behavior

- Harassment or discriminatory language
- Trolling or insulting comments
- Personal or political attacks
- Publishing others' private information
- Other unprofessional conduct

## 📄 License

By contributing, you agree that your contributions will be licensed under the MIT License.

## 🎉 Thank You!

Your contributions make this project better for everyone. We appreciate your time and effort!
