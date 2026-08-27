import json
from datetime import date
from pathlib import Path

import pytest


@pytest.fixture
def load_fixture():
    def _load(name: str):
        return json.loads((Path(__file__).parent / "fixtures" / name).read_text(encoding="utf-8"))

    return _load


def make_price_row(
    symbol="FPT",
    trading_date=date(2024, 1, 2),
    open=10.0,
    high=10.0,
    low=9.0,
    close=10.0,
    volume=100.0,
    source="vci",
):
    from vietnam_quant.schemas import PriceDailyRecord

    return PriceDailyRecord(
        symbol=symbol,
        trading_date=trading_date,
        source=source,
        raw_open=open / 1000,
        raw_high=high / 1000,
        raw_low=low / 1000,
        raw_close=close / 1000,
        raw_volume=volume,
        normalized_open=open,
        normalized_high=high,
        normalized_low=low,
        normalized_close=close,
        raw_price_unit="thousand_vnd",
        normalized_price_unit="VND",
        source_observation_id="test-observation",
        parser_version="test",
    )
