# tests/test_error_handling.py

import pytest
from fastapi.testclient import TestClient

from core.exceptions import DataFetchError
from core.exceptions import InsufficientDataError
from core.exceptions import InvalidParameterError
from core.exceptions import SymbolNotFoundError
from core.exceptions import TradingPlatformError
from main import app

client = TestClient(app)


# ── Unit tests: custom exception classes ──────────────────────────────────────


class TestCustomExceptions:

    def test_symbol_not_found_has_404_status(self):
        exc = SymbolNotFoundError("^FAKE")
        assert exc.status_code == 404
        assert "^FAKE" in exc.message

    def test_insufficient_data_has_422_status(self):
        exc = InsufficientDataError(required=36, got=10)
        assert exc.status_code == 422
        assert "36" in exc.message
        assert "10" in exc.message

    def test_invalid_parameter_has_400_status(self):
        exc = InvalidParameterError("period", "999y", "Must be 1mo–5y")
        assert exc.status_code == 400
        assert "period" in exc.message
        assert "999y" in exc.message

    def test_data_fetch_error_has_503_status(self):
        exc = DataFetchError("yfinance", "connection timeout")
        assert exc.status_code == 503
        assert "yfinance" in exc.message

    def test_all_exceptions_inherit_base(self):
        for exc_class in [
            SymbolNotFoundError,
            InsufficientDataError,
            InvalidParameterError,
            DataFetchError,
        ]:
            assert issubclass(exc_class, TradingPlatformError)

    def test_base_exception_has_message_and_status(self):
        exc = TradingPlatformError("something broke", status_code=418)
        assert exc.message == "something broke"
        assert exc.status_code == 418


# ── Integration: error response shape ────────────────────────────────────────


class TestErrorResponseShape:

    def _assert_error_shape(self, response, expected_status: int):
        """Every error must have these exact fields."""
        assert response.status_code == expected_status
        body = response.json()
        for field in ["error", "message", "status_code", "path", "timestamp"]:
            assert field in body, f"Missing field in error response: {field}"
        assert body["status_code"] == expected_status

    def test_invalid_period_returns_400_with_correct_shape(self):
        r = client.get("/market/?period=999y")
        self._assert_error_shape(r, 400)
        assert r.json()["error"] == "InvalidParameterError"

    def test_invalid_interval_returns_400_with_correct_shape(self):
        r = client.get("/market/?interval=5min")
        self._assert_error_shape(r, 400)

    def test_invalid_symbol_returns_404_with_correct_shape(self):
        r = client.get("/market/?symbol=TOTALLYFAKESYMBOL999XYZ")
        self._assert_error_shape(r, 404)
        assert r.json()["error"] == "SymbolNotFoundError"

    def test_rsi_window_too_large_returns_422(self):
        r = client.get("/indicators/?rsi_window=999")
        self._assert_error_shape(r, 422)
        assert r.json()["error"] == "ValidationError"

    def test_validation_error_has_details_field(self):
        r = client.get("/indicators/?rsi_window=999")
        body = r.json()
        assert "details" in body
        assert "errors" in body["details"]
        assert len(body["details"]["errors"]) > 0

    def test_validation_error_details_has_field_and_message(self):
        r = client.get("/indicators/?rsi_window=999")
        error = r.json()["details"]["errors"][0]
        assert "field" in error
        assert "message" in error

    def test_not_found_route_returns_404(self):
        r = client.get("/this-route-does-not-exist")
        self._assert_error_shape(r, 404)

    def test_error_path_matches_request_path(self):
        r = client.get("/market/?period=bad")
        assert r.json()["path"] == "/market/"

    def test_error_has_iso_timestamp(self):
        r = client.get("/market/?period=bad")
        ts = r.json()["timestamp"]
        # ISO timestamp contains T and +
        assert "T" in ts

    def test_min_gap_size_negative_returns_422(self):
        r = client.get("/fvg/?min_gap_size=-10")
        self._assert_error_shape(r, 422)


# ── Verify successful responses still work ────────────────────────────────────


class TestSuccessfulResponsesUnaffected:
    """
    Make sure the error handling changes didn't break anything.
    Happy-path tests from previous days should still pass.
    """

    def test_market_still_returns_200(self):
        r = client.get("/market/?period=1mo")
        assert r.status_code == 200

    def test_indicators_still_returns_200(self):
        r = client.get("/indicators/?period=3mo")
        assert r.status_code == 200

    def test_fvg_still_returns_200(self):
        r = client.get("/fvg/?period=3mo")
        assert r.status_code == 200

    def test_health_still_returns_200(self):
        r = client.get("/health")
        assert r.status_code == 200
