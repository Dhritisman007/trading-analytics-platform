#!/bin/bash
# Run tests with minimal startup

cd "$(dirname "$0")" || exit

# Activate venv
source venv/bin/activate

# Set environment variables to skip expensive startup operations
export PYTEST_SKIP_STARTUP=1
export SKIP_SCHEDULER=1

# Run pytest with verbose output and short traceback
python -m pytest tests/ -v --tb=short --no-header 2>&1 | tee test_results.log

echo ""
echo "=== Test Results Summary ==="
tail -20 test_results.log
