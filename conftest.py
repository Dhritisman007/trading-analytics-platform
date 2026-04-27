"""
Pytest configuration and fixtures.
Makes the project root modules (core, services, routers) importable in tests.
Mocks scheduler and WebSocket to avoid startup hangs.
"""

import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock
import pytest

# Add project root to sys.path so tests can import core, services, routers
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Set test mode before importing anything from the app
os.environ["TESTING"] = "1"


@pytest.fixture(scope="session", autouse=True)
def disable_scheduler_and_websocket_on_session_start():
    """Mock scheduler and WebSocket at session level to prevent startup hangs."""
    with patch("core.scheduler.start_scheduler"), \
         patch("core.scheduler.stop_scheduler"), \
         patch("services.websocket_manager.start_websocket_feed", new_callable=AsyncMock), \
         patch("services.websocket_manager.stop_websocket_feed", new_callable=AsyncMock):
        yield


@pytest.fixture(autouse=True)
def reset_mocks_between_tests():
    """Reset mocks between tests to ensure isolation."""
    yield
    # Cleanup after each test
    pass
