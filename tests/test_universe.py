from datetime import datetime, timezone
from collections import Counter

from vietnam_quant.schemas import InstrumentRecord
from vietnam_quant.universe import select_sample


def make_listing_rows():
    rows = []
    for exchange, count in (("HOSE", 30), ("HNX", 10), ("UPCOM", 10)):
        for index in range(count):
            symbol = f"{exchange[:2]}{index:02d}"
            rows.append(InstrumentRecord(
                instrument_id=f"vci:{symbol}", symbol=symbol, exchange_raw=exchange,
                exchange=exchange, source="vci",
                retrieved_at_utc=datetime(2026, 8, 27, tzinfo=timezone.utc),
            ))
    rows.append(InstrumentRecord(
        instrument_id="vci:AGE", symbol="AGE", exchange_raw="DELISTED",
        exchange="DELISTED", listing_status="observed_delisted", source="vci",
        retrieved_at_utc=datetime(2026, 8, 27, tzinfo=timezone.utc),
    ))
    return rows


def test_select_sample_is_stable_and_respects_exchange_quotas():
    sample = select_sample(make_listing_rows(), sample_size=50)
    counts = Counter(row.exchange for row in sample if row.exchange in {"HOSE", "HNX", "UPCOM"})
    assert counts == {"HOSE": 30, "HNX": 10, "UPCOM": 10}
    assert [row.symbol for row in sample] == [row.symbol for row in select_sample(make_listing_rows(), sample_size=50)]


def test_delisted_edge_case_keeps_delisted_status():
    sample = select_sample(make_listing_rows(), sample_size=50, edge_symbols=("AGE",))
    age = next(row for row in sample if row.symbol == "AGE")
    assert age.exchange == "DELISTED"
    assert age.selection_reason == "edge_case"
