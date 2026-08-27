import pandas as pd

from vietnam_quant.factors import compute_features


def make_price_frame(dates=None, closes=None, symbols=("FPT", "VCB")):
    dates = dates or pd.date_range("2024-01-01", periods=40, freq="B").strftime("%Y-%m-%d").tolist()
    closes = closes or [100.0 + index for index in range(len(dates))]
    rows = []
    for symbol_index, symbol in enumerate(symbols):
        for day, close in zip(dates, closes):
            rows.append({
                "symbol": symbol, "trading_date": day, "normalized_open": close,
                "normalized_high": close * 1.01, "normalized_low": close * 0.99,
                "normalized_close": close + symbol_index, "raw_volume": 1000 + symbol_index,
                "quality_flags": [],
            })
    return pd.DataFrame(rows)


def test_momentum_uses_previous_day_not_same_day_close():
    frame = make_price_frame(
        dates=["2024-01-01", "2024-01-02", "2024-01-03"],
        closes=[10.0, 11.0, 20.0],
        symbols=("FPT",),
    )
    features = compute_features(frame)
    row = features.loc[features["trading_date"] == "2024-01-03"].iloc[0]
    assert pd.isna(row["momentum_1m"])
    assert pd.isna(row["reversal_1m"])
    assert row["market_cap_status"] == "blocked_missing_market_cap"


def test_feature_columns_include_lagged_risk_and_liquidity_signals():
    features = compute_features(make_price_frame())
    expected = {
        "momentum_1m", "momentum_3m", "momentum_6m", "momentum_12m",
        "reversal_1m", "volatility_1m", "volatility_3m",
        "avg_volume_1m", "amihud_1m", "avg_traded_value_proxy_1m",
        "boundary_price_proxy", "tradable_quality", "market_cap_status",
    }
    assert expected <= set(features.columns)
