from datetime import date
from pathlib import Path

import pytest

from vietnam_quant.adapters.hnx import parse_hnx_upcom_price_anchor
from vietnam_quant.adapters.kbs import parse_kbs_ohlcv
from vietnam_quant.adapters.ssi import parse_ssi_daily
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


def test_ssi_parser_keeps_raw_ohlc_and_adjusted_close_separate(load_fixture):
    rows = parse_ssi_daily(
        load_fixture("ssi_daily_price.json"),
        symbol="FPT",
        requested_start=date(2024, 1, 2),
        requested_end=date(2024, 1, 3),
        source_observation_id="ssi-obs",
    )

    assert [row.trading_date for row in rows] == [date(2024, 1, 2), date(2024, 1, 3)]
    assert rows[0].raw_close == 101000.0
    assert rows[0].normalized_close == 101000.0
    assert rows[0].adjusted_close == 98000.0
    assert rows[0].price_semantics == "raw_and_adjusted_close"
    assert rows[0].raw_price_unit == "VND"
    assert rows[0].volume_unit == "shares"
    assert rows[0].exchange == "HOSE"


def test_ssi_parser_does_not_invent_adjusted_close_when_field_is_missing(load_fixture):
    rows = parse_ssi_daily(
        load_fixture("ssi_daily_price.json"),
        symbol="FPT",
        requested_start=date(2024, 1, 3),
        requested_end=date(2024, 1, 3),
        source_observation_id="ssi-obs",
    )

    assert len(rows) == 1
    assert rows[0].adjusted_close is None
    assert rows[0].adjusted_price_unit is None
    assert rows[0].price_semantics == "raw_only"


def test_hnx_upcom_parser_returns_an_exchange_raw_price_anchor():
    html = (Path(__file__).parent / "fixtures" / "hnx_upcom_price.html").read_text(
        encoding="utf-8"
    )

    anchor = parse_hnx_upcom_price_anchor(
        html,
        symbol="A32",
        trading_date=date(2024, 8, 16),
        source_observation_id="hnx-obs",
    )

    assert anchor.anchor_id == "hnx:A32:2024-08-16"
    assert anchor.exchange == "UPCoM"
    assert anchor.raw_open == 35000.0
    assert anchor.raw_high == 36000.0
    assert anchor.raw_low == 34500.0
    assert anchor.raw_close == 35100.0
    assert anchor.raw_price_unit == "VND"
    assert anchor.semantic_label == "exchange_raw"
    assert anchor.source_observation_id == "hnx-obs"


def test_hnx_upcom_parser_rejects_a_table_without_close_price():
    with pytest.raises(ValueError, match="close"):
        parse_hnx_upcom_price_anchor(
            "<table><tr><th>Open</th><th>Close</th></tr><tr><td>25.000</td><td>-</td></tr></table>",
            symbol="A32",
            trading_date=date(2024, 8, 16),
        )
