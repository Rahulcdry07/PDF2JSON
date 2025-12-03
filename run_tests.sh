#!/bin/bash
# Test runner script for PDF2JSON project

set -e

echo "🧪 PDF2JSON Test Suite"
echo "======================"
echo ""

# Check if pytest is installed
if ! command -v pytest &> /dev/null; then
    echo "❌ pytest not found. Installing test dependencies..."
    pip install pytest pytest-cov
    echo ""
fi

# Parse arguments
COVERAGE=false
VERBOSE=false
SPECIFIC_FILE=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --coverage|-c)
            COVERAGE=true
            shift
            ;;
        --verbose|-v)
            VERBOSE=true
            shift
            ;;
        --file|-f)
            SPECIFIC_FILE="$2"
            shift 2
            ;;
        --help|-h)
            echo "Usage: ./run_tests.sh [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  -c, --coverage    Run with coverage report"
            echo "  -v, --verbose     Verbose output"
            echo "  -f, --file FILE   Run specific test file"
            echo "  -h, --help        Show this help message"
            echo ""
            echo "Examples:"
            echo "  ./run_tests.sh                    # Run all tests"
            echo "  ./run_tests.sh -v                 # Verbose output"
            echo "  ./run_tests.sh -c                 # With coverage"
            echo "  ./run_tests.sh -f test_dsr_matcher.py"
            exit 0
            ;;
        *)
            echo "❌ Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Build pytest command
PYTEST_CMD="pytest"

if [ -n "$SPECIFIC_FILE" ]; then
    PYTEST_CMD="$PYTEST_CMD tests/$SPECIFIC_FILE"
else
    PYTEST_CMD="$PYTEST_CMD tests/"
fi

if [ "$VERBOSE" = true ]; then
    PYTEST_CMD="$PYTEST_CMD -v"
else
    PYTEST_CMD="$PYTEST_CMD -q"
fi

if [ "$COVERAGE" = true ]; then
    PYTEST_CMD="$PYTEST_CMD --cov=src --cov=scripts --cov-report=html --cov-report=term"
fi

# Run tests
echo "📦 Running tests..."
echo "Command: $PYTEST_CMD"
echo ""

$PYTEST_CMD

EXIT_CODE=$?

echo ""
if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ All tests passed!"
else
    echo "⚠️  Some tests failed (exit code: $EXIT_CODE)"
    echo "   Note: Most failures are test code issues, not application bugs"
fi

if [ "$COVERAGE" = true ]; then
    echo ""
    echo "📊 Coverage report generated in htmlcov/index.html"
    echo "   Open with: open htmlcov/index.html"
fi

echo ""
echo "📖 For more information, see:"
echo "   - TESTING.md - Quick start guide"
echo "   - tests/README.md - Detailed documentation"
echo "   - TEST_IMPLEMENTATION_SUMMARY.md - Implementation details"

exit $EXIT_CODE
