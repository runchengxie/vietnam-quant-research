from datetime import date

from vietnam_quant.adapters.kbs import parse_kbs_ohlcv
from vietnam_quant.adapters.vci import parse_vci_listing, parse_vci_ohlcv


def test_vci_listing_maps_hsx_to_hose_and_keeps_raw_board(load_fixture):
    records = parse_vci_listing(load_fixture("vci_listing.json"))
    assert records[0].exchange == "HOSE"
    assert records[0].exchange_raw == "HSX"


def test_vci_parser_strictly_crops_count_back_response(load_fixture):
    rows = parse_vci_ohlcv(
        load_fixture("vci_ohlcv.json"),
        symbol="FPT",
        requested_start=date(2024, 1, 2),
        requested_end=date(2024, 1, 31),
        source_observation_id="vci-obs",
    )
    assert [row.trading_date for row in rows] == [date(2024, 1, 2), date(2024, 1, 31)]
    assert rows[0].raw_close == 101.5
    assert rows[0].normalized_close == 101.5
    assert rows[0].raw_price_unit == "VND"
    assert rows[0].normalized_price_unit == "VND"
    assert "unit_converted_thousand_vnd" not in rows[0].quality_flags


def test_kbs_parser_sorts_and_strictly_crops_dates(load_fixture):
    rows = parse_kbs_ohlcv(
        load_fixture("kbs_ohlcv.json"),
        symbol="FPT",
        requested_start=date(2024, 1, 2),
        requested_end=date(2024, 1, 31),
        source_observation_id="kbs-obs",
    )
    assert [row.trading_date for row in rows] == sorted(row.trading_date for row in rows)
    assert rows[0].trading_date == date(2024, 1, 2)
    assert rows[-1].trading_date == date(2024, 1, 31)
    assert rows[0].normalized_close == rows[0].raw_close
    assert rows[0].raw_price_unit == "VND"
    assert "reordered_source_rows" in rows[0].quality_flags
