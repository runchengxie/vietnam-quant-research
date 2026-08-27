from datetime import date, datetime, timezone

from vietnam_quant.schemas import InstrumentRecord, SourceObservation


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
