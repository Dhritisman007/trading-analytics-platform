#!/usr/bin/env python
"""
Simple test runner to check if pytest works without hanging.
Run this directly with: python test_runner.py
"""

import os
import sys

# Set testing mode BEFORE anything else
os.environ["TESTING"] = "1"

# Add project to path
sys.path.insert(0, str(os.path.dirname(__file__)))

print("✓ Environment variables set")
print("✓ Python path configured")

try:
    print("\n[1] Attempting to import pytest...")
    import pytest
    print("✓ pytest imported successfully")
except Exception as e:
    print(f"✗ Failed to import pytest: {e}")
    sys.exit(1)

try:
    print("\n[2] Attempting to import conftest...")
    import conftest
    print("✓ conftest imported successfully")
except Exception as e:
    print(f"✗ Failed to import conftest: {e}")
    sys.exit(1)

try:
    print("\n[3] Attempting to import main (FastAPI app)...")
    from main import app
    print("✓ main.app imported successfully")
except Exception as e:
    print(f"✗ Failed to import main: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

try:
    print("\n[4] Attempting to run pytest...")
    exit_code = pytest.main([
        "tests/test_market.py::test_get_price",
        "-xvs",
        "--tb=short"
    ])
    print(f"✓ pytest completed with exit code: {exit_code}")
    sys.exit(exit_code)
except Exception as e:
    print(f"✗ pytest failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
