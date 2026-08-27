import numpy as np
import pandas as pd
import pytest

from vietnam_quant.validation import compute_forward_returns, compute_rank_ic
from vietnam_quant.validation import compute_quantile_returns, summarize_factor_validation


def test_forward_returns_are_grouped_by_symbol_and_use_future_rows_only():
    frame = pd.DataFrame(
        [
            {"symbol": "A", "trading_date": "2024-01-02", "normalized_close": 10.0, "raw_volume": 100},
            {"symbol": "B", "trading_date": "2024-01-02", "normalized_close": 100.0, "raw_volume": 100},
            {"symbol": "A", "trading_date": "2024-01-03", "normalized_close": 20.0, "raw_volume": 100},
            {"symbol": "B", "trading_date": "2024-01-03", "normalized_close": 90.0, "raw_volume": 100},
            {"symbol": "A", "trading_date": "2024-01-04", "normalized_close": 30.0, "raw_volume": 100},
            {"symbol": "B", "trading_date": "2024-01-04", "normalized_close": 80.0, "raw_volume": 100},
        ]
    )

    result = compute_forward_returns(frame, horizons=(1, 2))
    result = result.set_index(["symbol", "trading_date"])

    assert result.loc[("A", "2024-01-02"), "forward_return_1d"] == 1.0
    assert result.loc[("B", "2024-01-02"), "forward_return_1d"] == pytest.approx(-0.1)
    assert result.loc[("A", "2024-01-02"), "forward_return_2d"] == pytest.approx(2.0)
    assert result.loc[("B", "2024-01-02"), "forward_return_2d"] == pytest.approx(-0.2)
    assert np.isnan(result.loc[("A", "2024-01-04"), "forward_return_1d"])


def test_forward_horizon_counts_only_eligible_observations():
    frame = pd.DataFrame(
        [
            {"symbol": "A", "trading_date": "2024-01-02", "normalized_close": 10.0, "raw_volume": 100},
            {"symbol": "A", "trading_date": "2024-01-03", "normalized_close": 20.0, "raw_volume": 0},
            {"symbol": "A", "trading_date": "2024-01-04", "normalized_close": 30.0, "raw_volume": 100},
        ]
    )

    result = compute_forward_returns(frame, horizons=(1,)).set_index("trading_date")

    assert result.loc["2024-01-02", "forward_return_1d"] == pytest.approx(2.0)
    assert np.isnan(result.loc["2024-01-03", "forward_return_1d"])


def test_rank_ic_is_cross_sectional_and_marks_small_dates_missing():
    rows = []
    for date_index, date in enumerate(pd.date_range("2024-01-02", periods=2, freq="B")):
        for symbol_index in range(3):
            rows.append(
                {
                    "symbol": f"S{symbol_index}",
                    "trading_date": date.strftime("%Y-%m-%d"),
                    "normalized_close": 100.0,
                    "raw_volume": 100,
                    "test_factor": float(symbol_index),
                    "forward_return_1d": float(symbol_index + date_index),
                }
            )
    panel = pd.DataFrame(rows)

    result = compute_rank_ic(panel, factor="test_factor", horizon=1, min_cross_section=3)

    assert result.iloc[0] == 1.0
    assert result.iloc[1] == 1.0
    assert result.index.tolist() == list(pd.to_datetime(["2024-01-02", "2024-01-03"]))

    small = panel[panel["symbol"] != "S2"]
    assert np.isnan(compute_rank_ic(small, "test_factor", 1, min_cross_section=3).iloc[0])


def make_quantile_panel(days=10, symbols=10):
    rows = []
    for day_index, date in enumerate(pd.date_range("2024-01-02", periods=days, freq="B")):
        for symbol_index in range(symbols):
            factor = float(symbol_index)
            rows.append(
                {
                    "symbol": f"S{symbol_index:02d}",
                    "trading_date": date.strftime("%Y-%m-%d"),
                    "normalized_close": 100.0,
                    "raw_volume": 100,
                    "test_factor": factor,
                    "forward_return_1d": day_index / 1000 + factor / 100,
                }
            )
    return pd.DataFrame(rows)


def test_quantile_returns_report_spread_and_monotonicity():
    result = compute_quantile_returns(
        make_quantile_panel(),
        factor="test_factor",
        horizon=1,
        n_quantiles=5,
        min_cross_section=10,
    )

    assert len(result) == 10
    assert result.loc[0, "quantile_1"] < result.loc[0, "quantile_5"]
    assert result.loc[0, "high_minus_low"] == pytest.approx(0.08)
    assert result.loc[0, "monotonicity"] == pytest.approx(1.0)
    assert (result["cross_section"] == 10).all()


def test_validation_excludes_explicitly_non_tradable_rows():
    panel = make_quantile_panel(days=1).copy()
    panel["tradable"] = True
    panel.loc[panel["symbol"] == "S00", "tradable"] = False

    result = compute_quantile_returns(
        panel,
        factor="test_factor",
        horizon=1,
        n_quantiles=3,
        min_cross_section=9,
    )

    assert result.loc[0, "cross_section"] == 9


def test_summary_uses_chronological_is_and_oos_periods():
    result = summarize_factor_validation(
        make_quantile_panel(),
        factor="test_factor",
        horizons=(1,),
        n_quantiles=5,
        oos_fraction=0.3,
        min_cross_section=10,
    )

    assert {"FULL", "IS", "OOS"} == set(result["period"])
    is_row = result[result["period"] == "IS"].iloc[0]
    oos_row = result[result["period"] == "OOS"].iloc[0]
    assert is_row["period_end"] < oos_row["period_start"]
    assert oos_row["oos_start"] == oos_row["period_start"]
    assert is_row["mean_high_minus_low"] == pytest.approx(0.08)
    assert oos_row["mean_rank_ic"] == pytest.approx(1.0)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"horizons": (0,)},
        {"n_quantiles": 1},
        {"oos_fraction": 0},
        {"oos_fraction": 1},
        {"min_cross_section": 1},
    ],
)
def test_summary_rejects_invalid_parameters(kwargs):
    with pytest.raises(ValueError):
        summarize_factor_validation(make_quantile_panel(), factor="test_factor", **kwargs)
