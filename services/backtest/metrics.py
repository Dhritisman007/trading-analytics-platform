# services/backtest/metrics.py

import numpy as np
from utils.formatters import format_number


def calculate_sharpe_ratio(
    returns: list[float],
    risk_free_rate: float = 0.065,  # 6.5% — approximate Indian 10yr bond yield
    periods_per_year: int = 252,    # trading days per year
) -> float:
    """
    Sharpe Ratio = (Mean Return - Risk-free Rate) / Std Dev of Returns

    Annualised. Higher is better.
    > 1.0 = acceptable
    > 2.0 = good
    > 3.0 = excellent
    """
    if not returns or len(returns) < 2:
        return 0.0

    returns_arr   = np.array(returns)
    mean_return   = np.mean(returns_arr) * periods_per_year
    std_return    = np.std(returns_arr, ddof=1) * np.sqrt(periods_per_year)
    daily_rf_rate = risk_free_rate / periods_per_year

    excess_return = np.mean(returns_arr) - daily_rf_rate
    annualised_excess = excess_return * periods_per_year

    if std_return == 0:
        return 0.0

    return round(annualised_excess / std_return, 3)


def calculate_max_drawdown(equity_curve: list[float]) -> dict:
    """
    Maximum Drawdown = biggest peak-to-trough decline.

    Returns the drawdown % and the dates of peak and trough.
    Lower is better. Above 20% is considered high risk.
    """
    if not equity_curve:
        return {"max_drawdown_pct": 0.0, "peak_value": 0.0, "trough_value": 0.0}

    equity    = np.array(equity_curve)
    peak      = equity[0]
    max_dd    = 0.0
    peak_val  = equity[0]
    trough_val = equity[0]

    for value in equity:
        if value > peak:
            peak = value
        drawdown = (peak - value) / peak * 100
        if drawdown > max_dd:
            max_dd     = drawdown
            peak_val   = peak
            trough_val = value

    return {
        "max_drawdown_pct": round(max_dd, 2),
        "peak_value":       round(peak_val, 2),
        "trough_value":     round(trough_val, 2),
    }


def calculate_profit_factor(trades: list[dict]) -> float:
    """
    Profit Factor = Total Gross Profit / Total Gross Loss

    > 1.5 = good strategy
    > 2.0 = excellent strategy
    < 1.0 = losing strategy
    """
    gross_profit = sum(t["pnl"] for t in trades if t["pnl"] > 0)
    gross_loss   = abs(sum(t["pnl"] for t in trades if t["pnl"] < 0))

    if gross_loss == 0:
        return float("inf") if gross_profit > 0 else 0.0

    return round(gross_profit / gross_loss, 3)


def calculate_win_rate(trades: list[dict]) -> dict:
    """Win rate and average win/loss amounts."""
    if not trades:
        return {
            "win_rate_pct": 0.0,
            "wins": 0, "losses": 0, "total": 0,
            "avg_win": 0.0, "avg_loss": 0.0,
        }

    wins   = [t for t in trades if t["pnl"] > 0]
    losses = [t for t in trades if t["pnl"] <= 0]

    return {
        "win_rate_pct": round(len(wins) / len(trades) * 100, 2),
        "wins":         len(wins),
        "losses":       len(losses),
        "total":        len(trades),
        "avg_win":      round(np.mean([t["pnl"] for t in wins]), 2) if wins else 0.0,
        "avg_loss":     round(np.mean([t["pnl"] for t in losses]), 2) if losses else 0.0,
    }


def grade_strategy(
    total_return_pct: float,
    sharpe_ratio: float,
    max_drawdown_pct: float,
    win_rate_pct: float,
    profit_factor: float,
    buy_hold_return: float,
) -> dict:
    """
    Grade the overall strategy performance A–F.
    Considers all metrics together, not just return.
    """
    score = 0

    # Return vs buy & hold (0–25 pts)
    if total_return_pct > buy_hold_return * 1.2:
        score += 25
    elif total_return_pct > buy_hold_return:
        score += 18
    elif total_return_pct > 0:
        score += 10
    else:
        score += 0

    # Sharpe ratio (0–25 pts)
    if sharpe_ratio >= 2.0:
        score += 25
    elif sharpe_ratio >= 1.0:
        score += 18
    elif sharpe_ratio >= 0.5:
        score += 10
    elif sharpe_ratio > 0:
        score += 5

    # Max drawdown (0–25 pts) — lower is better
    if max_drawdown_pct <= 5:
        score += 25
    elif max_drawdown_pct <= 10:
        score += 18
    elif max_drawdown_pct <= 20:
        score += 10
    elif max_drawdown_pct <= 30:
        score += 5

    # Win rate + profit factor (0–25 pts)
    if win_rate_pct >= 60 and profit_factor >= 1.5:
        score += 25
    elif win_rate_pct >= 50 and profit_factor >= 1.2:
        score += 18
    elif win_rate_pct >= 45:
        score += 10
    else:
        score += 5

    # Grade
    if score >= 80:
        grade, color = "A", "#1D9E75"
        verdict = "Excellent strategy. Consistently outperforms."
    elif score >= 65:
        grade, color = "B", "#5DCAA5"
        verdict = "Good strategy. Solid risk-adjusted returns."
    elif score >= 50:
        grade, color = "C", "#BA7517"
        verdict = "Average strategy. Needs optimisation."
    elif score >= 35:
        grade, color = "D", "#E24B4A"
        verdict = "Below average. High risk or low returns."
    else:
        grade, color = "F", "#791F1F"
        verdict = "Poor strategy. Does not meet minimum criteria."

    return {
        "score":   score,
        "grade":   grade,
        "color":   color,
        "verdict": verdict,
    }