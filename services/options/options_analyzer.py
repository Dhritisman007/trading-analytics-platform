# services/options/options_analyzer.py

import logging
import math
from utils.formatters import format_number

logger = logging.getLogger(__name__)


def calculate_pcr(records: list[dict]) -> dict:
    """
    Put/Call Ratio — most watched F&O sentiment indicator.

    PCR > 1.2 → Bullish (more puts = more hedging = market likely to go up)
    PCR 0.8–1.2 → Neutral
    PCR < 0.8 → Bearish (more calls = more bullishness = could be overbought)
    """
    total_call_oi = sum(
        r.get("CE", {}).get("openInterest", 0) for r in records
    )
    total_put_oi  = sum(
        r.get("PE", {}).get("openInterest", 0) for r in records
    )
    total_call_vol = sum(
        r.get("CE", {}).get("totalTradedVolume", 0) for r in records
    )
    total_put_vol  = sum(
        r.get("PE", {}).get("totalTradedVolume", 0) for r in records
    )

    pcr_oi  = round(total_put_oi  / total_call_oi,  3) if total_call_oi  else 0
    pcr_vol = round(total_put_vol / total_call_vol, 3) if total_call_vol else 0

    # Sentiment from PCR OI
    if pcr_oi >= 1.3:
        sentiment = "strongly_bullish"
        color     = "#1D9E75"
        label     = "Strongly Bullish"
        description = (
            f"PCR of {pcr_oi} indicates heavy put writing — "
            "institutions are selling puts which means they expect market to hold or go up. "
            "Strong bullish signal."
        )
    elif pcr_oi >= 1.0:
        sentiment = "bullish"
        color     = "#5DCAA5"
        label     = "Bullish"
        description = (
            f"PCR of {pcr_oi} is above 1.0 — more puts than calls. "
            "Indicates mild bullish sentiment in the options market."
        )
    elif pcr_oi >= 0.8:
        sentiment = "neutral"
        color     = "#888780"
        label     = "Neutral"
        description = (
            f"PCR of {pcr_oi} is in the neutral zone (0.8–1.0). "
            "Market participants are balanced between bullish and bearish bets."
        )
    elif pcr_oi >= 0.6:
        sentiment = "bearish"
        color     = "#F09595"
        label     = "Bearish"
        description = (
            f"PCR of {pcr_oi} is below 0.8 — more calls than puts. "
            "Indicates bearish sentiment or excessive bullishness that could reverse."
        )
    else:
        sentiment = "strongly_bearish"
        color     = "#E24B4A"
        label     = "Strongly Bearish"
        description = (
            f"PCR of {pcr_oi} is very low — extremely heavy call writing. "
            "Market is overbought or strongly bearish signal."
        )

    return {
        "pcr_oi":       pcr_oi,
        "pcr_volume":   pcr_vol,
        "total_call_oi": total_call_oi,
        "total_put_oi":  total_put_oi,
        "total_call_vol": total_call_vol,
        "total_put_vol":  total_put_vol,
        "sentiment":    sentiment,
        "label":        label,
        "color":        color,
        "description":  description,
    }


def calculate_max_pain(records: list[dict]) -> dict:
    """
    Max Pain — the strike price at which option buyers
    lose the most money (and sellers make the most).

    Market tends to gravitate toward Max Pain near expiry
    as option sellers (institutions) defend their positions.
    """
    strikes = {}

    for record in records:
        strike = record.get("strikePrice", 0)
        if not strike:
            continue

        ce_oi = record.get("CE", {}).get("openInterest", 0)
        pe_oi = record.get("PE", {}).get("openInterest", 0)
        strikes[strike] = {"ce_oi": ce_oi, "pe_oi": pe_oi}

    if not strikes:
        return {"max_pain": 0, "strike_pain": []}

    all_strikes = sorted(strikes.keys())
    pain_values = []

    for target_strike in all_strikes:
        total_pain = 0

        for strike, data in strikes.items():
            # Pain to call buyers if market ends at target_strike
            if target_strike > strike:
                total_pain += (target_strike - strike) * data["ce_oi"]

            # Pain to put buyers if market ends at target_strike
            if target_strike < strike:
                total_pain += (strike - target_strike) * data["pe_oi"]

        pain_values.append({
            "strike":     strike,
            "total_pain": total_pain,
        })

    # Max pain = strike with minimum total pain to option buyers
    max_pain_row = min(pain_values, key=lambda x: x["total_pain"])
    max_pain     = max_pain_row["strike"]

    # Normalise pain values for chart (0–100 scale)
    max_val = max(p["total_pain"] for p in pain_values) or 1
    for p in pain_values:
        p["pain_pct"] = round(p["total_pain"] / max_val * 100, 1)

    return {
        "max_pain":    max_pain,
        "strike_pain": pain_values,
        "description": (
            f"Max Pain at ₹{max_pain:,}. "
            "Option sellers benefit most if market expires at this level. "
            "Market often gravitates here in the final days before expiry."
        ),
    }


def calculate_oi_analysis(
    records: list[dict],
    spot_price: float,
    num_strikes: int = 10,
) -> dict:
    """
    Analyse Open Interest distribution around spot price.

    Key levels:
    - Highest Call OI = strong resistance (call writers defending)
    - Highest Put OI  = strong support (put writers defending)
    - OI change > 0   = fresh positions being added
    - OI change < 0   = positions being unwound (squeezing)
    """
    # Find strikes near ATM (At The Money)
    strike_diff = 50   # Nifty strikes are ₹50 apart
    atm_strike  = round(spot_price / strike_diff) * strike_diff

    # Filter records near ATM
    near_atm = [
        r for r in records
        if abs(r.get("strikePrice", 0) - atm_strike) <= strike_diff * num_strikes
    ]
    near_atm.sort(key=lambda x: x.get("strikePrice", 0))

    # Build OI table
    oi_table = []
    for r in near_atm:
        strike    = r.get("strikePrice", 0)
        ce        = r.get("CE", {})
        pe        = r.get("PE", {})

        oi_table.append({
            "strike":       strike,
            "is_atm":       strike == atm_strike,
            "is_itm_call":  strike < spot_price,
            "is_itm_put":   strike > spot_price,
            "call": {
                "oi":        ce.get("openInterest", 0),
                "oi_change": ce.get("changeinOpenInterest", 0),
                "volume":    ce.get("totalTradedVolume", 0),
                "iv":        format_number(ce.get("impliedVolatility", 0)),
                "ltp":       format_number(ce.get("lastPrice", 0)),
                "bid":       format_number(ce.get("bidprice", 0)),
                "ask":       format_number(ce.get("askPrice", 0)),
            },
            "put": {
                "oi":        pe.get("openInterest", 0),
                "oi_change": pe.get("changeinOpenInterest", 0),
                "volume":    pe.get("totalTradedVolume", 0),
                "iv":        format_number(pe.get("impliedVolatility", 0)),
                "ltp":       format_number(pe.get("lastPrice", 0)),
                "bid":       format_number(pe.get("bidprice", 0)),
                "ask":       format_number(pe.get("askPrice", 0)),
            },
        })

    if not oi_table:
        return {
            "atm_strike": atm_strike,
            "oi_table": [],
            "resistance_levels": [],
            "support_levels": [],
        }

    # Find highest OI strikes (support/resistance)
    call_ois   = [(r["strike"], r["call"]["oi"]) for r in oi_table]
    put_ois    = [(r["strike"], r["put"]["oi"])  for r in oi_table]

    top_calls  = sorted(call_ois, key=lambda x: x[1], reverse=True)[:3]
    top_puts   = sorted(put_ois,  key=lambda x: x[1], reverse=True)[:3]

    resistance_levels = [
        {
            "strike": s,
            "oi":     oi,
            "label":  f"₹{s:,} — Strong resistance ({oi:,} call OI)",
        }
        for s, oi in top_calls if s > spot_price
    ]

    support_levels = [
        {
            "strike": s,
            "oi":     oi,
            "label":  f"₹{s:,} — Strong support ({oi:,} put OI)",
        }
        for s, oi in top_puts if s < spot_price
    ]

    # Max OI values for chart scaling
    max_call_oi = max((r["call"]["oi"] for r in oi_table), default=1)
    max_put_oi  = max((r["put"]["oi"]  for r in oi_table), default=1)

    for r in oi_table:
        r["call"]["oi_pct"] = round(r["call"]["oi"] / max_call_oi * 100, 1)
        r["put"]["oi_pct"]  = round(r["put"]["oi"]  / max_put_oi  * 100, 1)

    return {
        "atm_strike":        atm_strike,
        "spot_price":        spot_price,
        "oi_table":          oi_table,
        "resistance_levels": resistance_levels[:2],
        "support_levels":    support_levels[:2],
        "max_call_oi":       max_call_oi,
        "max_put_oi":        max_put_oi,
    }


def calculate_iv_summary(records: list[dict]) -> dict:
    """
    Implied Volatility summary — average IV of ATM options.
    High IV = big move expected, options expensive.
    Low IV = calm market, options cheap.
    """
    ivs = []
    for r in records:
        ce_iv = r.get("CE", {}).get("impliedVolatility", 0)
        pe_iv = r.get("PE", {}).get("impliedVolatility", 0)
        if ce_iv > 0:
            ivs.append(ce_iv)
        if pe_iv > 0:
            ivs.append(pe_iv)

    if not ivs:
        return {"avg_iv": 0, "iv_label": "unknown"}

    avg_iv = round(sum(ivs) / len(ivs), 2)

    if avg_iv > 20:
        iv_label       = "Very High"
        iv_color       = "#E24B4A"
        iv_description = f"IV at {avg_iv}% — market expecting large moves. Options are expensive."
    elif avg_iv > 15:
        iv_label       = "High"
        iv_color       = "#BA7517"
        iv_description = f"IV at {avg_iv}% — elevated volatility expected."
    elif avg_iv > 10:
        iv_label       = "Normal"
        iv_color       = "#888780"
        iv_description = f"IV at {avg_iv}% — normal market conditions."
    else:
        iv_label       = "Low"
        iv_color       = "#1D9E75"
        iv_description = f"IV at {avg_iv}% — calm market. Options are cheap. Big move may be coming."

    return {
        "avg_iv":        avg_iv,
        "iv_label":      iv_label,
        "iv_color":      iv_color,
        "iv_description": iv_description,
        "iv_values":     sorted(ivs),
    }