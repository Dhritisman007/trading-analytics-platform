# services/fii_dii/flow_analyzer.py

import logging
from utils.formatters import format_number

logger = logging.getLogger(__name__)


def calculate_moving_average(values: list[float], window: int) -> float | None:
    """Simple moving average of last N values."""
    if len(values) < window:
        return None
    return round(sum(values[-window:]) / window, 2)


def detect_consecutive_days(data: list[dict], entity: str) -> dict:
    """
    Count how many consecutive days FII or DII has been
    buying or selling. Streaks of 5+ days are significant.

    Args:
        data:   sorted list of daily flow records (oldest first)
        entity: "fii" or "dii"
    """
    if not data:
        return {"days": 0, "action": "none", "significant": False}

    # Look at last 20 days for streak detection
    recent = data[-20:]
    action = recent[-1][entity]["action"]
    count  = 0

    for record in reversed(recent):
        if record[entity]["action"] == action:
            count += 1
        else:
            break

    return {
        "days":        count,
        "action":      action,
        "significant": count >= 5,  # 5+ consecutive days is notable
    }


def compute_pressure_score(
    fii_net: float,
    dii_net: float,
    fii_5d_avg: float | None,
    dii_5d_avg: float | None,
) -> dict:
    """
    Compute a -100 to +100 buy/sell pressure score.

    Positive = buying pressure (bullish)
    Negative = selling pressure (bearish)

    FII gets 60% weight (larger impact on markets)
    DII gets 40% weight
    """
    fii_score = 0.0
    dii_score = 0.0

    # FII component (60% weight)
    if fii_5d_avg and abs(fii_5d_avg) > 0:
        # How strong is today vs recent average?
        fii_score = min(max(fii_net / abs(fii_5d_avg) * 60, -60), 60)
    elif fii_net != 0:
        fii_score = 30.0 if fii_net > 0 else -30.0

    # DII component (40% weight)
    if dii_5d_avg and abs(dii_5d_avg) > 0:
        dii_score = min(max(dii_net / abs(dii_5d_avg) * 40, -40), 40)
    elif dii_net != 0:
        dii_score = 20.0 if dii_net > 0 else -20.0

    total = round(fii_score + dii_score, 1)

    if total >= 50:
        label = "strong buying"
        color = "#1D9E75"
    elif total >= 20:
        label = "moderate buying"
        color = "#5DCAA5"
    elif total >= -20:
        label = "neutral"
        color = "#888780"
    elif total >= -50:
        label = "moderate selling"
        color = "#F09595"
    else:
        label = "strong selling"
        color = "#E24B4A"

    return {
        "score": total,
        "label": label,
        "color": color,
        "fii_contribution": round(fii_score, 1),
        "dii_contribution": round(dii_score, 1),
    }


def generate_signal(
    fii_action: str,
    dii_action: str,
    fii_streak: dict,
    dii_streak: dict,
    pressure: dict,
) -> dict:
    """
    Generate a combined market signal from FII + DII activity.
    """
    # Both buying = most bullish
    if fii_action == "buy" and dii_action == "buy":
        signal      = "BULLISH"
        color       = "#1D9E75"
        description = (
            "Both FII and DII are buying — strong institutional support. "
            "Markets likely to sustain upward momentum."
        )

    # FII buying, DII selling (DIIs taking profits)
    elif fii_action == "buy" and dii_action == "sell":
        signal      = "CAUTIOUSLY BULLISH"
        color       = "#5DCAA5"
        description = (
            "FII buying but DII selling — foreign inflows driving market up "
            "while domestic institutions book profits."
        )

    # FII selling, DII buying (DIIs providing support)
    elif fii_action == "sell" and dii_action == "buy":
        signal      = "CAUTIOUSLY BEARISH"
        color       = "#F09595"
        description = (
            "FII selling but DII buying — domestic institutions providing support. "
            "Market may consolidate or see limited downside."
        )

    # Both selling = most bearish
    else:
        signal      = "BEARISH"
        color       = "#E24B4A"
        description = (
            "Both FII and DII are selling — weak institutional support. "
            "Markets under pressure, caution advised."
        )

    # Amplify if streaks are significant
    if fii_streak["significant"] and fii_streak["action"] == "buy":
        description += (
            f" FII has been buying for {fii_streak['days']} consecutive days — "
            f"strong conviction."
        )
    elif fii_streak["significant"] and fii_streak["action"] == "sell":
        description += (
            f" FII has been selling for {fii_streak['days']} consecutive days — "
            f"persistent outflow."
        )

    return {
        "signal":      signal,
        "color":       color,
        "description": description,
    }


def analyze_flows(data: list[dict]) -> dict:
    """
    Full flow analysis — takes raw daily data and returns
    all computed metrics, signals, and chart-ready arrays.
    """
    if not data:
        return {"error": "No flow data available"}

    # ── Extract time series ───────────────────────────────────────────────
    fii_nets = [float(d["fii"]["net"])      for d in data]
    dii_nets = [float(d["dii"]["net"])      for d in data]
    combined = [float(d["combined_net"])    for d in data]
    dates    = [d["date"]                   for d in data]

    # ── Latest day ────────────────────────────────────────────────────────
    latest      = data[-1]
    fii_net_today = float(latest["fii"]["net"])
    dii_net_today = float(latest["dii"]["net"])

    # ── Moving averages ───────────────────────────────────────────────────
    fii_5d  = calculate_moving_average(fii_nets,  5)
    fii_10d = calculate_moving_average(fii_nets, 10)
    fii_30d = calculate_moving_average(fii_nets, 30)
    dii_5d  = calculate_moving_average(dii_nets,  5)
    dii_10d = calculate_moving_average(dii_nets, 10)
    dii_30d = calculate_moving_average(dii_nets, 30)

    # ── Streaks ───────────────────────────────────────────────────────────
    fii_streak = detect_consecutive_days(data, "fii")
    dii_streak = detect_consecutive_days(data, "dii")

    # ── Pressure score ────────────────────────────────────────────────────
    pressure = compute_pressure_score(
        fii_net=fii_net_today,
        dii_net=dii_net_today,
        fii_5d_avg=fii_5d,
        dii_5d_avg=dii_5d,
    )

    # ── Signal ────────────────────────────────────────────────────────────
    signal = generate_signal(
        fii_action=latest["fii"]["action"],
        dii_action=latest["dii"]["action"],
        fii_streak=fii_streak,
        dii_streak=dii_streak,
        pressure=pressure,
    )

    # ── Period totals ─────────────────────────────────────────────────────
    period_days = len(data)
    fii_buy_days  = sum(1 for d in data if d["fii"]["action"] == "buy")
    dii_buy_days  = sum(1 for d in data if d["dii"]["action"] == "buy")

    return {
        "latest_date":  latest["date"],
        "today": {
            "fii":          latest["fii"],
            "dii":          latest["dii"],
            "combined_net": latest["combined_net"],
        },
        "signal":   signal,
        "pressure": pressure,
        "streaks": {
            "fii": fii_streak,
            "dii": dii_streak,
        },
        "moving_averages": {
            "fii": {
                "5d":  fii_5d,
                "10d": fii_10d,
                "30d": fii_30d,
            },
            "dii": {
                "5d":  dii_5d,
                "10d": dii_10d,
                "30d": dii_30d,
            },
        },
        "period_summary": {
            "days":           period_days,
            "fii_buy_days":   fii_buy_days,
            "fii_sell_days":  period_days - fii_buy_days,
            "dii_buy_days":   dii_buy_days,
            "dii_sell_days":  period_days - dii_buy_days,
            "fii_total_net":  format_number(sum(fii_nets), 2),
            "dii_total_net":  format_number(sum(dii_nets), 2),
            "combined_total": format_number(sum(combined),  2),
        },
        "chart_data": {
            "dates":     dates,
            "fii_net":   [format_number(v, 2) for v in fii_nets],
            "dii_net":   [format_number(v, 2) for v in dii_nets],
            "combined":  [format_number(v, 2) for v in combined],
            "fii_colors": [
                "#1D9E75" if v >= 0 else "#E24B4A"
                for v in fii_nets
            ],
            "dii_colors": [
                "#378ADD" if v >= 0 else "#F09595"
                for v in dii_nets
            ],
        },
    }