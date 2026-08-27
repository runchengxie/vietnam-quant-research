import json
from dataclasses import replace
from datetime import date, datetime, timezone
from pathlib import Path

from vietnam_quant.pipeline import PipelineConfig, _estimate_count_back, _listing_result, run_pipeline
from vietnam_quant.schemas import FetchResult, InstrumentRecord


def test_listing_retries_read_timeout(monkeypatch):
    class FlakyListingAdapter:
        def __init__(self):
            self.attempts = 0

        def fetch_listing(self):
            self.attempts += 1
            if self.attempts == 1:
                return FetchResult(
                    status="error",
                    endpoint="fake://listing",
                    error_type="ReadTimeout",
                    error_message="temporary timeout",
                )
            return FetchResult(
                status="ok",
                payload={"data": []},
                response_status=200,
                endpoint="fake://listing",
            )

    monkeypatch.setattr("vietnam_quant.pipeline.time.sleep", lambda _: None)
    adapter = FlakyListingAdapter()

    result = _listing_result(adapter, max_retries=2)

    assert result.status == "ok"
    assert result.attempts == 2
    assert adapter.attempts == 2


def test_count_back_is_capped_for_long_daily_ranges():
    assert _estimate_count_back(date(2018, 1, 1), date(2026, 8, 27)) == 2200


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


class FakeSecondaryAdapter(FakeAdapter):
    source_name = "fake2"

    def fetch_daily(self, symbol, end_date, count_back, start_date=None):
        return FetchResult(
            status="ok",
            payload={"data": [{"t": 1704153600, "o": 100, "h": 103, "l": 99, "c": 102, "v": 1000}]},
            response_status=200, endpoint=f"fake2://daily/{symbol}",
        )

    def parse_daily(self, payload, symbol, requested_start, requested_end):
        from vietnam_quant.adapters.vci import parse_vci_ohlcv
        return [
            replace(row, source="fake2")
            for row in parse_vci_ohlcv(payload, symbol, requested_start, requested_end, "pipeline")
        ]


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
    assert "entries" not in report.quality_report
    instruments = [
        json.loads(line)
        for line in (tmp_path / "bronze/instrument_master.jsonl").read_text().splitlines()
    ]
    assert next(row for row in instruments if row["symbol"] == "GOOD")["selection_reason"] in {
        "exchange_quota", "sample_fill"
    }


def test_pipeline_writes_research_view_without_changing_bronze(tmp_path):
    report = run_pipeline(
        PipelineConfig(
            data_root=tmp_path,
            start=date(2024, 1, 1),
            end=date(2024, 1, 31),
            sample_size=1,
            primary_source="fake",
            secondary_source="fake2",
            strict=False,
            network=False,
            rate_limit_seconds=0,
        ),
        adapters={"fake": FakeAdapter(), "fake2": FakeSecondaryAdapter()},
    )
    research = [
        json.loads(line)
        for line in (tmp_path / "derived/research_price_daily.jsonl").read_text().splitlines()
    ]
    bronze = [
        json.loads(line)
        for line in (tmp_path / "bronze/price_daily.jsonl").read_text().splitlines()
    ]
    assert len(research) == 1
    assert len(bronze) == 2
    assert report.research_quality_status in {"PASS", "PASS_WITH_QUARANTINE"}
    assert report.factor_ready is False
    assert json.loads((tmp_path / "metadata/price_semantics_report.json").read_text())
