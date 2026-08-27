from datetime import date

from vietnam_quant.adapters.vci import normalize_price_bars
from vietnam_quant.adapters.vci import normalize_exchange
from vietnam_quant.quality import reconcile_price_bars, validate_price_bars
from tests.conftest import make_price_row


def test_quality_flags_keep_invalid_rows_and_mark_zero_volume():
    rows = [make_price_row(open=10, high=8, low=7, close=9, volume=0)]
    report = validate_price_bars(rows)
    assert report.issue_count == 2
    assert "invalid_ohlc" in report.rows[0].quality_flags
    assert "zero_volume" in report.rows[0].quality_flags


def test_reconciliation_reports_missing_dates_and_close_difference():
    report = reconcile_price_bars(
        primary=[make_price_row(symbol="FPT", trading_date=date(2024, 1, 2), close=10)],
        secondary=[make_price_row(symbol="FPT", trading_date=date(2024, 1, 3), close=10.1)],
    )
    assert report.missing_in_primary == ["2024-01-03"]
    assert report.missing_in_secondary == ["2024-01-02"]


def test_exchange_normalization_preserves_raw_value():
    assert normalize_exchange("HSX") == ("HSX", "HOSE")


def test_normalize_price_bars_keeps_raw_and_normalized_units():
    row = make_price_row(open=10, high=11, low=9, close=10.5)
    normalized = normalize_price_bars([row])[0]
    assert normalized.raw_close == 0.0105
    assert normalized.normalized_close == 10.5
