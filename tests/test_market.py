from routers.market import get_price


def test_get_price():
    res = get_price()
    assert res["symbol"] == "BTCUSD"
    assert "price" in res
