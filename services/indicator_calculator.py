def calculate_sma(values: list[float], window: int):
    if window <= 0:
        raise ValueError("window must be > 0")
    if not values:
        return []
    sma = []
    for i in range(len(values)):
        if i + 1 < window:
            sma.append(None)
        else:
            window_vals = values[i - window + 1: i + 1]
            sma.append(sum(window_vals) / window)
    return sma
