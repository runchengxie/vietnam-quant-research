from datetime import date

from vietnam_quant.adapters.vci import normalize_price_bars
from vietnam_quant.adapters.vci import normalize_exchange
from vietnam_quant.schemas import SourceArbitrationReport
from vietnam_quant.quality import (
    arbitrate_price_bars,
    assess_research_quality,
    reconcile_price_bars,
    validate_price_bars,
)
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


def test_arbitration_prefers_valid_primary_and_marks_tradability():
    rows, report, semantics = arbitrate_price_bars(
        [make_price_row(symbol="FPT", trading_date=date(2024, 1, 2), close=10, volume=100)],
        [make_price_row(symbol="FPT", trading_date=date(2024, 1, 2), high=10.02, close=10.02, volume=100, source="kbs")],
        primary_source="vci", secondary_source="kbs",
    )
    assert rows[0].source == "vci"
    assert rows[0].arbitration_reason == "primary_valid"
    assert rows[0].research_eligible is True
    assert rows[0].tradable is True
    assert "source_disagreement" in rows[0].quality_flags
    assert report.disagreement_count == 1
    assert semantics.status == "unresolved"


def test_arbitration_falls_back_to_valid_secondary_without_rewriting_bronze_row():
    invalid_primary = make_price_row(
        symbol="FPT", trading_date=date(2024, 1, 2), open=10, high=8, low=7, close=9, volume=100
    )
    valid_secondary = make_price_row(
        symbol="FPT", trading_date=date(2024, 1, 2), close=10, volume=100, source="kbs"
    )
    rows, report, _ = arbitrate_price_bars(
        [invalid_primary], [valid_secondary], primary_source="vci", secondary_source="kbs"
    )
    assert rows[0].source == "kbs"
    assert rows[0].arbitration_reason == "secondary_fallback"
    assert rows[0].research_eligible is True
    assert rows[0].raw_close == 0.01
    assert report.fallback_count == 1
    assert invalid_primary.source == "vci"
    assert "invalid_ohlc" not in invalid_primary.quality_flags


def test_arbitration_quarantines_when_both_sources_are_invalid():
    primary = make_price_row(
        symbol="A32", trading_date=date(2024, 1, 2), open=10, high=8, low=7, close=9, volume=100
    )
    secondary = make_price_row(
        symbol="A32", trading_date=date(2024, 1, 2), open=11, high=9, low=8, close=10, volume=100
    )
    rows, report, _ = arbitrate_price_bars(
        [primary], [secondary], primary_source="vci", secondary_source="kbs"
    )
    assert rows[0].research_status == "quarantined"
    assert rows[0].research_eligible is False
    assert rows[0].tradable is False
    assert rows[0].arbitration_reason == "both_invalid_primary_kept"
    assert report.quarantine_count == 1


def test_arbitration_keeps_valid_zero_volume_marked_not_tradable():
    rows, report, _ = arbitrate_price_bars(
        [make_price_row(symbol="A32", trading_date=date(2024, 1, 2), close=10, volume=0)],
        [],
        primary_source="vci", secondary_source="kbs",
    )
    assert rows[0].research_eligible is True
    assert rows[0].tradable is False
    assert report.zero_volume_count == 1


def test_research_quality_passes_with_quarantine_but_blocks_factor_ready():
    reports = [
        SourceArbitrationReport(
            symbol="A32", primary_source="vci", secondary_source="kbs",
            primary_row_count=100, secondary_row_count=90, selected_row_count=100,
            primary_selected_count=95, secondary_selected_count=5, fallback_count=5,
            quarantine_count=5, zero_volume_count=10, disagreement_count=3,
            missing_both_count=0, research_eligible_count=95, tradable_count=85,
            coverage_rate=0.95, tradable_rate=0.85, sample_disagreements=[],
        )
    ]
    result = assess_research_quality(
        reports,
        expected_symbols=["A32"],
        observations=[{"symbol": "A32", "source": "vci", "response_status": 200, "row_count": 100}],
        semantics_status="unresolved",
    )
    assert result["status"] == "PASS_WITH_QUARANTINE"
    assert result["factor_ready"] is False
    assert result["quarantined_rows"] == 5
