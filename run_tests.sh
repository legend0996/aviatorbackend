#!/bin/bash
# Quick test runner for Aviator application

set -e

cd "$(dirname "$0")"

echo "🚀 Aviator Testing Suite"
echo "========================"
echo ""

# Check if pytest is installed
if ! command -v pytest &> /dev/null; then
    echo "📦 Installing pytest dependencies..."
    pip install pytest pytest-cov httpx
fi

echo "📝 Running Backend Tests..."
echo "============================"
echo ""

# Run tests with verbose output
pytest test_full_app.py -v --tb=short

echo ""
echo "✅ All tests completed!"
echo ""
echo "📊 Generating coverage report..."
pytest test_full_app.py --cov=services --cov-report=term-missing

echo ""
echo "🎉 Testing complete!"
echo ""
echo "📚 Next steps:"
echo "  1. Review test output above"
echo "  2. Test in browser: http://localhost:5174"
echo "  3. Run specific test: pytest test_full_app.py::TestAuthentication -v"
echo "  4. Generate HTML coverage: pytest test_full_app.py --cov=services --cov-report=html"
