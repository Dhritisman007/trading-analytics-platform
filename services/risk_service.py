# services/risk_service.py

import logging
from utils.formatters import format_number

logger = logging.getLogger(__name__)

# Minimum R:R ratios for trade quality scoring
RR_THRESHOLDS = {
    "excellent": 3.0,
    "good":      2.0,
    "fair":      1.5,
    "poor":      1.0,
}

# Maximum position size as % of capital — never bet the farm
MAX_POSITION_PCT = 20.0


def calculate_position_size(
    capital: float,
    risk_pct: float,
    entry_price: float,
    stop_loss: float,
) -> dict:
    """
    Calculate how many units to buy based on capital and risk tolerance.

    Args:
        capital:    total trading capital in ₹
        risk_pct:   % of capital willing to risk (e.g. 1.0 = 1%)
        entry_price: price at which you enter the trade
        stop_loss:   price at which you exit if wrong

    Returns:
        dict with units, risk amounts, and capital allocation
    """
    if stop_loss >= entry_price:
        raise ValueError(
            f"Stop loss ({stop_loss}) must be below entry price ({entry_price}) "
            f"for a long trade."
        )
    if not (0.1 <= risk_pct <= 5.0):
        raise ValueError(
            f"Risk % must be between 0.1 and 5.0. Got {risk_pct}. "
            f"Risking more than 5% per trade is considered reckless."
        )
    if capital <= 0:
        raise ValueError("Capital must be positive.")

    risk_amount   = capital * (risk_pct / 100)   # ₹ at risk
    risk_per_unit = entry_price - stop_loss        # ₹ lost per unit if stop hits
    units         = risk_amount / risk_per_unit    # units to buy
    units_floor   = int(units)                     # round down — never over-risk

    total_cost         = units_floor * entry_price
    capital_used_pct   = (total_cost / capital) * 100
    actual_risk_amount = units_floor * risk_per_unit
    actual_risk_pct    = (actual_risk_amount / capital) * 100

    # Warn if position requires more than MAX_POSITION_PCT of capital
    capital_warning = None
    if capital_used_pct > MAX_POSITION_PCT:
        capital_warning = (
            f"This position uses {capital_used_pct:.1f}% of your capital. "
            f"Consider reducing units to stay under {MAX_POSITION_PCT}%."
        )

    return {
        "units":             units_floor,
        "units_exact":       format_number(units, 3),
        "total_cost":        format_number(total_cost),
        "risk_amount":       format_number(actual_risk_amount),
        "risk_pct_actual":   format_number(actual_risk_pct),
        "capital_used_pct":  format_number(capital_used_pct),
        "risk_per_unit":     format_number(risk_per_unit),
        "capital_warning":   capital_warning,
    }


def calculate_risk_reward(
    entry_price: float,
    stop_loss: float,
    target_price: float,
) -> dict:
    """
    Calculate the Risk:Reward ratio and trade profitability metrics.

    Args:
        entry_price:  price at which you enter
        stop_loss:    price at which you exit if wrong
        target_price: price at which you take profit

    Returns:
        dict with R:R ratio, quality rating, and profit/loss amounts
    """
    if stop_loss >= entry_price:
        raise ValueError("Stop loss must be below entry price for a long trade.")
    if target_price <= entry_price:
        raise ValueError("Target price must be above entry price for a long trade.")

    risk_per_unit   = entry_price - stop_loss
    reward_per_unit = target_price - entry_price
    rr_ratio        = reward_per_unit / risk_per_unit

    # Trade quality based on R:R ratio
    if rr_ratio >= RR_THRESHOLDS["excellent"]:
        quality = "EXCELLENT"
        quality_color = "#1D9E75"
        quality_msg   = "Outstanding R:R ratio. High-conviction trade setup."
    elif rr_ratio >= RR_THRESHOLDS["good"]:
        quality = "GOOD"
        quality_color = "#5DCAA5"
        quality_msg   = "Good R:R ratio. Worth taking with proper position sizing."
    elif rr_ratio >= RR_THRESHOLDS["fair"]:
        quality = "FAIR"
        quality_color = "#BA7517"
        quality_msg   = "Acceptable R:R. Proceed only with high-confidence signal."
    elif rr_ratio >= RR_THRESHOLDS["poor"]:
        quality = "POOR"
        quality_color = "#E24B4A"
        quality_msg   = "Low R:R ratio. Risk outweighs reward. Consider skipping."
    else:
        quality = "SKIP"
        quality_color = "#791F1F"
        quality_msg   = "R:R below 1:1. This trade risks more than it can gain. Skip it."

    return {
        "rr_ratio":       format_number(rr_ratio, 3),
        "rr_display":     f"1:{format_number(rr_ratio, 2)}",
        "risk_per_unit":  format_number(risk_per_unit),
        "reward_per_unit": format_number(reward_per_unit),
        "quality":        quality,
        "quality_color":  quality_color,
        "quality_message": quality_msg,
        "stop_distance_pct": format_number(
            (entry_price - stop_loss) / entry_price * 100
        ),
        "target_distance_pct": format_number(
            (target_price - entry_price) / entry_price * 100
        ),
    }


def calculate_atr_stops(
    entry_price: float,
    atr: float,
    atr_multiplier: float = 1.5,
    rr_ratio: float = 2.0,
) -> dict:
    """
    Calculate stop loss and target based on ATR (volatility-adaptive).

    Instead of picking arbitrary stop distances, ATR-based stops
    adapt to the market's actual volatility. Wide ATR = wider stop.

    Args:
        entry_price:     price at which you enter
        atr:             Average True Range value from indicators
        atr_multiplier:  how many ATRs to place stop (default 1.5)
        rr_ratio:        desired reward:risk ratio (default 2.0)

    Returns:
        dict with suggested stop loss and target prices
    """
    if atr <= 0:
        raise ValueError("ATR must be positive.")
    if atr_multiplier <= 0:
        raise ValueError("ATR multiplier must be positive.")

    stop_distance  = atr * atr_multiplier
    stop_loss      = entry_price - stop_distance
    reward_distance = stop_distance * rr_ratio
    target_price   = entry_price + reward_distance

    return {
        "atr":               format_number(atr),
        "atr_multiplier":    atr_multiplier,
        "stop_loss":         format_number(stop_loss),
        "target_price":      format_number(target_price),
        "stop_distance":     format_number(stop_distance),
        "reward_distance":   format_number(reward_distance),
        "rr_ratio":          f"1:{rr_ratio}",
        "explanation": (
            f"Stop placed {atr_multiplier}× ATR below entry "
            f"({atr_multiplier} × ₹{format_number(atr)} = ₹{format_number(stop_distance)} away). "
            f"Target placed at {rr_ratio}× the risk distance."
        ),
    }


def calculate_breakeven(
    entry_price: float,
    units: int,
    brokerage_pct: float = 0.03,
) -> dict:
    """
    Calculate the breakeven price accounting for brokerage costs.
    You need price to go above this before you actually profit.

    Args:
        entry_price:   price at which you enter
        units:         number of units purchased
        brokerage_pct: total transaction cost as % (default 0.03%)

    Returns:
        dict with breakeven price and cost details
    """
    total_cost       = entry_price * units
    brokerage_amount = total_cost * (brokerage_pct / 100)
    breakeven_price  = entry_price + (brokerage_amount / units)

    return {
        "entry_price":       format_number(entry_price),
        "breakeven_price":   format_number(breakeven_price),
        "brokerage_amount":  format_number(brokerage_amount),
        "brokerage_pct":     brokerage_pct,
        "breakeven_gap":     format_number(breakeven_price - entry_price),
        "note": (
            f"Price must exceed ₹{format_number(breakeven_price)} "
            f"to cover ₹{format_number(brokerage_amount)} in transaction costs."
        ),
    }


def score_trade(
    rr_ratio: float,
    signal_confidence: float | None = None,
    rsi_value: float | None = None,
    signal: str | None = None,
) -> dict:
    """
    Score a trade holistically using R:R, ML confidence, and RSI.
    Returns a 0–100 score and a final recommendation.

    Args:
        rr_ratio:          risk:reward ratio
        signal_confidence: ML model confidence % (optional)
        rsi_value:         current RSI (optional)
        signal:            BUY or SELL (optional)

    Returns:
        dict with score, grade, and recommendation
    """
    score = 0
    factors = []

    # R:R score (0–40 points)
    if rr_ratio >= 3.0:
        rr_score = 40
        factors.append("Excellent R:R ratio (+40)")
    elif rr_ratio >= 2.0:
        rr_score = 30
        factors.append("Good R:R ratio (+30)")
    elif rr_ratio >= 1.5:
        rr_score = 20
        factors.append("Fair R:R ratio (+20)")
    elif rr_ratio >= 1.0:
        rr_score = 10
        factors.append("Poor R:R ratio (+10)")
    else:
        rr_score = 0
        factors.append("R:R below 1 — very poor (+0)")
    score += rr_score

    # ML confidence score (0–30 points)
    if signal_confidence is not None:
        if signal_confidence >= 70:
            conf_score = 30
            factors.append(f"Strong ML signal at {signal_confidence}% (+30)")
        elif signal_confidence >= 60:
            conf_score = 20
            factors.append(f"Moderate ML signal at {signal_confidence}% (+20)")
        else:
            conf_score = 10
            factors.append(f"Weak ML signal at {signal_confidence}% (+10)")
        score += conf_score

    # RSI alignment score (0–30 points)
    if rsi_value is not None and signal is not None:
        if signal == "BUY":
            if 30 <= rsi_value <= 50:
                rsi_score = 30
                factors.append(f"RSI {rsi_value:.0f} — ideal BUY zone (+30)")
            elif 50 < rsi_value <= 65:
                rsi_score = 20
                factors.append(f"RSI {rsi_value:.0f} — acceptable BUY zone (+20)")
            elif rsi_value < 30:
                rsi_score = 25
                factors.append(f"RSI {rsi_value:.0f} — oversold, strong BUY (+25)")
            else:
                rsi_score = 5
                factors.append(f"RSI {rsi_value:.0f} — overbought, risky BUY (+5)")
        else:  # SELL
            if 50 <= rsi_value <= 70:
                rsi_score = 30
                factors.append(f"RSI {rsi_value:.0f} — ideal SELL zone (+30)")
            elif rsi_value > 70:
                rsi_score = 25
                factors.append(f"RSI {rsi_value:.0f} — overbought, strong SELL (+25)")
            else:
                rsi_score = 5
                factors.append(f"RSI {rsi_value:.0f} — oversold, risky SELL (+5)")
        score += rsi_score

    # Final grade
    if score >= 80:
        grade = "A"
        recommendation = "STRONG — All factors align. High-conviction setup."
        color = "#1D9E75"
    elif score >= 65:
        grade = "B"
        recommendation = "GOOD — Most factors align. Take with proper sizing."
        color = "#5DCAA5"
    elif score >= 50:
        grade = "C"
        recommendation = "FAIR — Some concerns. Reduce position size."
        color = "#BA7517"
    elif score >= 35:
        grade = "D"
        recommendation = "WEAK — Multiple red flags. Consider skipping."
        color = "#E24B4A"
    else:
        grade = "F"
        recommendation = "SKIP — Trade does not meet minimum criteria."
        color = "#791F1F"

    return {
        "score":          score,
        "max_score":      100,
        "grade":          grade,
        "recommendation": recommendation,
        "color":          color,
        "factors":        factors,
    }


def full_risk_analysis(
    capital: float,
    risk_pct: float,
    entry_price: float,
    stop_loss: float,
    target_price: float,
    atr: float | None = None,
    signal_confidence: float | None = None,
    rsi_value: float | None = None,
    signal: str | None = None,
    brokerage_pct: float = 0.03,
) -> dict:
    """
    Master function — runs all risk calculations and returns complete analysis.
    This is what the router calls.
    """
    position  = calculate_position_size(capital, risk_pct, entry_price, stop_loss)
    rr        = calculate_risk_reward(entry_price, stop_loss, target_price)
    breakeven = calculate_breakeven(entry_price, position["units"], brokerage_pct)
    trade_score = score_trade(
        rr_ratio=float(rr["rr_ratio"]),
        signal_confidence=signal_confidence,
        rsi_value=rsi_value,
        signal=signal,
    )

    # ATR-based stops (if ATR provided)
    atr_stops = None
    if atr and atr > 0:
        atr_stops = calculate_atr_stops(entry_price, atr)

    # Profit/loss projections
    units = position["units"]
    projections = {
        "max_profit":      format_number(units * float(rr["reward_per_unit"])),
        "max_loss":        format_number(units * float(rr["risk_per_unit"])),
        "profit_at_1r":    format_number(units * float(rr["risk_per_unit"])),
        "profit_at_2r":    format_number(units * float(rr["risk_per_unit"]) * 2),
        "profit_at_3r":    format_number(units * float(rr["risk_per_unit"]) * 3),
    }

    return {
        "inputs": {
            "capital":       capital,
            "risk_pct":      risk_pct,
            "entry_price":   entry_price,
            "stop_loss":     stop_loss,
            "target_price":  target_price,
            "atr":           atr,
            "signal":        signal,
        },
        "position_size":  position,
        "risk_reward":    rr,
        "atr_stops":      atr_stops,
        "breakeven":      breakeven,
        "projections":    projections,
        "trade_score":    trade_score,
        "summary": (
            f"{position['units']} units · "
            f"Risk ₹{position['risk_amount']} ({position['risk_pct_actual']}%) · "
            f"R:R {rr['rr_display']} · "
            f"Grade {trade_score['grade']}"
        ),
    }