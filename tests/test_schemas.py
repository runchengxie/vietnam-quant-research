from datetime import date, datetime, timezone

from vietnam_quant.schemas import (
    CorporateActionEvent,
    InstrumentRecord,
    PriceDailyRecord,
    PriceSemanticAnchor,
    SourceObservation,
)


def test_instrument_record_serializes_exchange_and_validity():
    record = InstrumentRecord(
        instrument_id="VCI:FPT",
        symbol="FPT",
        issuer_name=None,
        exchange_raw="HSX",
        exchange="HOSE",
        security_type="STOCK",
        listing_status="observed_current",
        valid_from=None,
        valid_to=None,
        listing_date=None,
        delisting_date=None,
        selection_reason="explicit_symbol",
        source="vci",
        retrieved_at_utc=datetime(2026, 8, 27, tzinfo=timezone.utc),
    )
    payload = record.to_dict()
    assert payload["exchange_raw"] == "HSX"
    assert payload["exchange"] == "HOSE"
    assert payload["valid_from"] is None


def test_source_observation_serializes_request_and_quality_fields():
    observation = SourceObservation(
        observation_id="vci:FPT:2024-01-01:2024-01-31",
        source="vci",
        endpoint="https://example.test",
        symbol="FPT",
        request_parameters={"countBack": 1000},
        retrieved_at_utc=datetime(2026, 8, 27, tzinfo=timezone.utc),
        response_status=200,
        latency_ms=12.5,
        raw_snapshot_path="raw/vci/FPT.json",
        raw_payload_sha256="abc",
        row_count=22,
        first_trading_date=date(2024, 1, 2),
        last_trading_date=date(2024, 1, 31),
        quality_status="PASS",
        quality_issue_count=0,
        parser_version="vci-1",
        schema_version="daily-v0",
        error_type=None,
        error_message=None,
    )
    assert observation.to_dict()["request_parameters"] == {"countBack": 1000}


def test_corporate_action_event_keeps_event_dates_and_provenance_separate():
    event = CorporateActionEvent(
        event_id="APG:2021-06-22:stock_dividend",
        symbol="APG",
        exchange="HOSE",
        event_type="stock_dividend",
        ex_date=date(2021, 6, 21),
        record_date=date(2021, 6, 22),
        listing_date=date(2021, 9, 9),
        source_url="https://www.vsd.vn/vi/ad/144285",
        source_kind="official",
        confidence="high",
    )

    payload = event.to_dict()

    assert payload["ex_date"] == "2021-06-21"
    assert payload["record_date"] == "2021-06-22"
    assert payload["payment_date"] is None
    assert payload["listing_date"] == "2021-09-09"
    assert payload["source_kind"] == "official"


def test_price_semantic_anchor_serializes_exchange_raw_evidence():
    anchor = PriceSemanticAnchor(
        anchor_id="hnx:A32:2024-08-16",
        symbol="A32",
        exchange="UPCoM",
        trading_date=date(2024, 8, 16),
        source="hnx",
        source_endpoint="https://www.gov.hnx.vn/ModuleReportStockETFs/Report_MD_PriceVolatilyti/ListData_UPCoM",
        raw_close=35100.0,
        raw_volume=1100.0,
    )

    payload = anchor.to_dict()

    assert payload["semantic_label"] == "exchange_raw"
    assert payload["raw_price_unit"] == "VND"
    assert payload["raw_close"] == 35100.0
    assert payload["raw_volume"] == 1100.0


def test_price_daily_record_can_carry_adjusted_close_without_overwriting_raw_close():
    record = PriceDailyRecord(
        symbol="FPT",
        trading_date=date(2024, 1, 2),
        source="ssi",
        raw_close=101000.0,
        normalized_close=101000.0,
        adjusted_close=98000.0,
        adjusted_price_unit="VND",
        price_semantics="raw_and_adjusted_close",
    )

    payload = record.to_dict()

    assert payload["raw_close"] == 101000.0
    assert payload["normalized_close"] == 101000.0
    assert payload["adjusted_close"] == 98000.0
    assert payload["price_semantics"] == "raw_and_adjusted_close"


def test_price_daily_record_preserves_legacy_positional_field_order():
    record = PriceDailyRecord(
        "FPT",
        date(2024, 1, 2),
        "vci",
        "2024-01-02",
        None,
        "HOSE",
        100.0,
        101.0,
        99.0,
        100.5,
        1000.0,
        "VND",
        100.0,
        101.0,
        99.0,
        100.5,
        "VND",
        "shares_or_source_units",
        [],
        "observation",
        "parser",
        "daily-v0",
    )

    assert record.volume_unit == "shares_or_source_units"
    assert record.quality_flags == []
    assert record.source_observation_id == "observation"
    assert record.adjusted_close is None
