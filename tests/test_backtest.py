import pandas as pd

from vietnam_quant.backtest import BacktestConfig, run_factor_backtest, summarize_backtest


def make_feature_frame():
    dates = pd.date_range("2024-01-01", periods=150, freq="B")
    rows = []
    for day_index, day in enumerate(dates):
        for symbol_index in range(20):
            symbol = f"S{symbol_index:02d}"
            close = 100 + symbol_index * 2 + day_index * (1 + symbol_index / 100)
            rows.append({
                "symbol": symbol,
                "trading_date": day.strftime("%Y-%m-%d"),
                "normalized_open": close * (1 + symbol_index / 10000),
                "normalized_close": close,
                "raw_volume": 1000 + symbol_index,
                "avg_traded_value_proxy_1m": close * (1000 + symbol_index),
                "momentum_1m": float(symbol_index),
                "quality_flags": ["boundary_price_proxy"] if symbol_index == 19 else [],
                "tradable_quality": symbol_index != 18,
                "boundary_price_proxy": symbol_index == 19,
            })
    return pd.DataFrame(rows)


def test_backtest_applies_cost_and_oos_without_same_day_execution():
    result = run_factor_backtest(
        make_feature_frame(),
        factor="momentum_1m",
        config=BacktestConfig(cost_bps=(0, 50, 100), oos_fraction=0.3),
    )
    assert {"IS", "OOS"} <= set(result["period"])
    assert (result["net_return_cost_50bp"] <= result["gross_return"]).all()
    assert (result["execution_date"] > result["formation_date"]).all()
    assert "excluded_for_non_tradable" in result.columns
    assert result["turnover"].ge(0).all()


def test_summary_reports_cost_scenarios_and_coverage():
    period_returns = run_factor_backtest(
        make_feature_frame(),
        factor="momentum_1m",
        config=BacktestConfig(cost_bps=(0, 50), oos_fraction=0.3),
    )
    summary = summarize_backtest(period_returns, oos_fraction=0.3)
    assert {"IS", "OOS", "FULL"} <= set(summary["period"])
    assert {0, 50} <= set(summary["cost_bps"])
    assert (summary["valid_formation_count"] > 0).all()
