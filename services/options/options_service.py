# services/options/options_service.py

import logging
from datetime import datetime, timezone

from services.options.nse_fetcher import fetch_option_chain_raw
from services.options.options_analyzer import (
    calculate_pcr,
    calculate_max_pain,
    calculate_oi_analysis,
    calculate_iv_summary,
)
from core.cache import cache
from utils.formatters import format_number

logger = logging.getLogger(__name__)

CACHE_TTL = 300   # 5 minutes during market hours


def get_option_chain(
    symbol: str = "NIFTY",
    expiry_index: int = 0,
) -> dict:
    """
    Full option chain analysis — PCR, Max Pain, OI levels, IV.

    Args:
        symbol:       NIFTY, BANKNIFTY, or FINNIFTY
        expiry_index: 0 = nearest expiry, 1 = next expiry, etc.

    Returns:
        Complete options analysis with all metrics
    """
    symbol = symbol.upper()
    cache_key = f"options:{symbol}:{expiry_index}"

    cached = cache.get(cache_key)
    if cached:
        cached["_cache"] = "HIT"
        return cached

    # Fetch raw data from NSE
    raw = fetch_option_chain_raw(symbol)

    # Extract data
    data         = raw.get("records", {})
    filtered     = raw.get("filtered", {})
    all_records  = data.get("data", [])
    expiry_dates = data.get("expiryDates", [])
    spot_price   = float(data.get("underlyingValue", 0))
    timestamp    = data.get("timestamp", "")

    if not all_records:
        raise ValueError(f"No option chain data returned for {symbol}")

    # Filter by expiry
    selected_expiry = (
        expiry_dates[expiry_index]
        if expiry_index < len(expiry_dates)
        else expiry_dates[0]
    )

    expiry_records = [
        r for r in all_records
        if r.get("expiryDate") == selected_expiry
    ]

    if not expiry_records:
        expiry_records = all_records

    # Run all analyses
    pcr        = calculate_pcr(expiry_records)
    max_pain   = calculate_max_pain(expiry_records)
    oi_analysis = calculate_oi_analysis(expiry_records, spot_price)
    iv_summary = calculate_iv_summary(expiry_records)

    # OI buildup — top strikes with highest OI change
    oi_buildup = _get_oi_buildup(expiry_records, spot_price)

    # Build chart data for frontend
    chart_data = _build_chart_data(expiry_records, spot_price)

    result = {
        "symbol":          symbol,
        "spot_price":      format_number(spot_price),
        "timestamp":       timestamp,
        "fetched_at":      datetime.now(timezone.utc).isoformat(),
        "selected_expiry": selected_expiry,
        "expiry_dates":    expiry_dates[:6],  # show next 6 expiries

        # Core metrics
        "pcr":        pcr,
        "max_pain":   max_pain,
        "oi_analysis": oi_analysis,
        "iv_summary": iv_summary,
        "oi_buildup": oi_buildup,

        # Chart data
        "chart_data": chart_data,

        # Summary for dashboard header
        "summary": {
            "spot":         format_number(spot_price),
            "pcr_oi":       pcr["pcr_oi"],
            "pcr_label":    pcr["label"],
            "pcr_color":    pcr["color"],
            "max_pain":     max_pain["max_pain"],
            "atm_strike":   oi_analysis["atm_strike"],
            "avg_iv":       iv_summary["avg_iv"],
            "iv_label":     iv_summary["iv_label"],
            "resistance":   [r["strike"] for r in oi_analysis["resistance_levels"]],
            "support":      [s["strike"] for s in oi_analysis["support_levels"]],
        },
    }

    cache.set(cache_key, result, ttl_seconds=CACHE_TTL)
    result["_cache"] = "MISS"
    return result


def _get_oi_buildup(records: list[dict], spot_price: float) -> dict:
    """Find where fresh OI is being added — signals institutional positioning."""
    call_buildup = []
    put_buildup  = []

    for r in records:
        strike    = r.get("strikePrice", 0)
        ce_change = r.get("CE", {}).get("changeinOpenInterest", 0)
        pe_change = r.get("PE", {}).get("changeinOpenInterest", 0)

        if ce_change > 0 and strike > spot_price:
            call_buildup.append({
                "strike": strike,
                "oi_change": ce_change,
                "type": "call_writing",
                "signal": "bearish",
                "description": f"Call writers adding ₹{strike:,} contracts — treating as resistance",
            })

        if pe_change > 0 and strike < spot_price:
            put_buildup.append({
                "strike": strike,
                "oi_change": pe_change,
                "type": "put_writing",
                "signal": "bullish",
                "description": f"Put writers adding ₹{strike:,} contracts — treating as support",
            })

    call_buildup.sort(key=lambda x: x["oi_change"], reverse=True)
    put_buildup.sort(key=lambda x:  x["oi_change"], reverse=True)

    return {
        "call_writing": call_buildup[:5],
        "put_writing":  put_buildup[:5],
        "overall_bias": (
            "bullish" if len(put_buildup) > len(call_buildup)
            else "bearish" if len(call_buildup) > len(put_buildup)
            else "neutral"
        ),
    }


def _build_chart_data(records: list[dict], spot_price: float) -> dict:
    """Build chart-ready arrays for the React OI chart."""
    strike_diff = 50
    atm = round(spot_price / strike_diff) * strike_diff
    strikes_near = [
        r for r in records
        if abs(r.get("strikePrice", 0) - atm) <= strike_diff * 10
    ]
    strikes_near.sort(key=lambda x: x.get("strikePrice", 0))

    return {
        "strikes":    [r.get("strikePrice", 0) for r in strikes_near],
        "call_oi":    [r.get("CE", {}).get("openInterest", 0) for r in strikes_near],
        "put_oi":     [r.get("PE", {}).get("openInterest", 0) for r in strikes_near],
        "call_change": [r.get("CE", {}).get("changeinOpenInterest", 0) for r in strikes_near],
        "put_change":  [r.get("PE", {}).get("changeinOpenInterest", 0) for r in strikes_near],
        "call_iv":    [r.get("CE", {}).get("impliedVolatility", 0) for r in strikes_near],
        "put_iv":     [r.get("PE", {}).get("impliedVolatility", 0) for r in strikes_near],
        "atm_strike": atm,
    }