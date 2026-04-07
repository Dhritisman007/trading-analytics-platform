from services.indicator_calculator import calculate_sma


def test_sma_basic():
    values = [1,2,3,4,5]
    assert calculate_sma(values, 3) == [None, None, 2.0, 3.0, 4.0]


def test_sma_empty():
    assert calculate_sma([], 3) == []


def test_sma_invalid_window():
    try:
        calculate_sma([1,2,3], 0)
        assert False
    except ValueError:
        assert True
