from cwfc.metrics import mae, normalized_mae, rmse, smape


def test_metrics_basic():
    y = [1, 2, 3]
    p = [1, 3, 1]
    assert mae(y, p) == 1.0
    assert round(rmse(y, p), 8) == round((5 / 3) ** 0.5, 8)
    assert smape(y, p) > 0
    assert normalized_mae(y, p, [1, 1, 1]) > 0
