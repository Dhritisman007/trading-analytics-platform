from routers.fvg import compute_fvg


def test_compute_fvg():
    highs = [10, 12, 15]
    lows = [9, 11, 14]
    res = compute_fvg.__wrapped__({"highs": highs, "lows": lows}) if hasattr(compute_fvg, "__wrapped__") else compute_fvg(type("X", (), {"highs": highs, "lows": lows})())
    # The router returns a dict with gaps list
    assert "gaps" in res
    assert res["gaps"] == [1,1,1]
