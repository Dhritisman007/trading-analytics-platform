"""
Pytest configuration and fixtures.
Makes the project root modules (core, services, routers) importable in tests.
"""

import sys
from pathlib import Path

# Add project root to sys.path so tests can import core, services, routers
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
