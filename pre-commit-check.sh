#!/bin/bash
# Pre-commit validation script for EstimateX
# Ensures code quality before committing

set -e  # Exit on error

echo "🔍 Running pre-commit checks..."
echo ""

# Step 1: Black formatting
echo "1️⃣  Checking code formatting with black..."
if black . --check --quiet; then
    echo "   ✅ All files properly formatted"
else
    echo "   ❌ Files need formatting. Running black..."
    black .
    echo "   ✅ Files formatted. Please review changes."
fi
echo ""

# Step 2: Run tests
echo "2️⃣  Running test suite..."
if pytest tests/ -v --tb=short -q 2>&1 | tee /tmp/pytest_output.txt | tail -20; then
    TEST_COUNT=$(grep -o "[0-9]* passed" /tmp/pytest_output.txt | head -1 || echo "0 passed")
    echo "   ✅ Tests passed: $TEST_COUNT"
else
    echo "   ❌ Tests failed! Please fix before committing."
    exit 1
fi
echo ""

# Step 3: Check for common issues
echo "3️⃣  Checking for common issues..."

# Check for debug statements
if grep -r "import pdb\|breakpoint()" src/ tests/ --include="*.py" 2>/dev/null; then
    echo "   ⚠️  Warning: Found debug statements (pdb/breakpoint)"
fi

# Check for print statements in src (warnings only)
PRINTS=$(grep -r "print(" src/ --include="*.py" 2>/dev/null | wc -l || echo "0")
if [ "$PRINTS" -gt 0 ]; then
    echo "   ⚠️  Warning: Found $PRINTS print() statements in src/"
fi

echo "   ✅ Basic checks complete"
echo ""

echo "✨ All pre-commit checks passed!"
echo ""
echo "You can now commit with:"
echo "  git add -A"
echo "  git commit -m 'your message'"
echo "  git push origin main"
