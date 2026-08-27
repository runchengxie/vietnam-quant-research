from dataclasses import replace
from datetime import date, datetime, timezone
from pathlib import Path

from vietnam_quant.pipeline import PipelineConfig, run_pipeline
from vietnam_quant.schemas import FetchResult, InstrumentRecord


class FakeAdapter:
    source_name = "fake"

    def __init__(self, fails_for=()):
        self.fails_for = set(fails_for)

    def fetch_listing(self):
        return FetchResult(
            status="ok",
            payload={"data": [
                {"symbol": "GOOD", "board": "HSX", "type": "STOCK"},
                {"symbol": "BAD", "board": "HSX", "type": "STOCK"},
            ]},
            response_status=200, endpoint="fake://listing",
        )

    def parse_listing(self, payload):
        return [
            InstrumentRecord(
                instrument_id=f"fake:{row['symbol']}", symbol=row["symbol"],
                exchange_raw="HSX", exchange="HOSE", source="fake",
                retrieved_at_utc=datetime(2026, 8, 27, tzinfo=timezone.utc),
            )
            for row in payload["data"]
        ]

    def fetch_daily(self, symbol, end_date, count_back, start_date=None):
        if symbol in self.fails_for:
            return FetchResult(
                status="error", endpoint=f"fake://daily/{symbol}",
                error_type="fixture_failure", error_message="fixture failure",
            )
        return FetchResult(
            status="ok",
            payload={"data": [{"t": 1704153600, "o": 100, "h": 101, "l": 99, "c": 100, "v": 1000}]},
            response_status=200, endpoint=f"fake://daily/{symbol}",
        )

    def parse_daily(self, payload, symbol, requested_start, requested_end):
        from vietnam_quant.adapters.vci import parse_vci_ohlcv
        return parse_vci_ohlcv(payload, symbol, requested_start, requested_end, "pipeline")


def test_pipeline_continues_after_symbol_failure(tmp_path):
    report = run_pipeline(
        PipelineConfig(
            data_root=tmp_path,
            start=date(2024, 1, 1),
            end=date(2024, 1, 31),
            sample_size=2,
            primary_source="fake",
            secondary_source=None,
            strict=False,
            network=False,
            rate_limit_seconds=0,
        ),
        adapters={"fake": FakeAdapter(fails_for={"BAD"})},
    )
    assert report.failed_symbols == ["BAD"]
    assert (tmp_path / "metadata/source_observations.jsonl").exists()
    assert (tmp_path / "bronze/price_daily.jsonl").exists()
    assert report.price_row_count == 1
