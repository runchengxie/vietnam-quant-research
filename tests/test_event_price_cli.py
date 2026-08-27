import json
import subprocess
import sys
from dataclasses import replace
from datetime import date

from vietnam_quant.event_price import write_event_price_reconciliation
from vietnam_quant.schemas import CorporateActionPriceReconciliation
from vietnam_quant.storage import ExternalDataStore


def make_report(event_id="event-1"):
    return CorporateActionPriceReconciliation(
        event_id=event_id,
        symbol="A32",
        event_type="cash_dividend",
        reference_date=date(2020, 6, 1),
        reference_date_kind="ex_date",
        event_dates={"ex_date": date(2020, 6, 1)},
        source_evidence={},
        cross_source={},
        assessment="unresolved",
        notes="Evidence only.",
    )


def test_write_event_price_reconciliation_is_idempotent(tmp_path):
    store = ExternalDataStore(tmp_path)
    report = make_report()

    paths = write_event_price_reconciliation(store, [report])
    write_event_price_reconciliation(store, [report])

    assert tuple(path.as_posix() for path in paths) == (
        "metadata/corporate_action_price_reconciliation.jsonl",
        "metadata/corporate_action_price_reconciliation.json",
    )
    assert len(store.read_jsonl(paths[0])) == 1
    summary = (tmp_path / paths[1]).read_text(encoding="utf-8")
    assert '"entries"' in summary


def test_write_event_price_reconciliation_updates_existing_event_without_duplicate(tmp_path):
    store = ExternalDataStore(tmp_path)
    original = make_report()
    updated = replace(original, notes="Updated evidence.")

    write_event_price_reconciliation(store, [original])
    write_event_price_reconciliation(store, [updated])

    records = store.read_jsonl("metadata/corporate_action_price_reconciliation.jsonl")
    assert len(records) == 1
    assert records[0]["notes"] == "Updated evidence."


def test_write_event_price_reconciliation_keeps_json_summary_aligned_with_jsonl(tmp_path):
    store = ExternalDataStore(tmp_path)
    first = make_report("event-1")
    second = make_report("event-2")
    updated_first = replace(first, notes="Updated evidence.")

    write_event_price_reconciliation(store, [first, second])
    write_event_price_reconciliation(store, [updated_first])

    jsonl_records = store.read_jsonl(
        "metadata/corporate_action_price_reconciliation.jsonl"
    )
    summary = json.loads(
        (tmp_path / "metadata/corporate_action_price_reconciliation.json").read_text(
            encoding="utf-8"
        )
    )
    assert [record["event_id"] for record in summary["entries"]] == [
        record["event_id"] for record in jsonl_records
    ]
    assert summary["entries"][0]["notes"] == "Updated evidence."


def test_event_price_cli_reads_bronze_and_writes_metadata_without_network(tmp_path):
    data_root = tmp_path / "data"
    bronze_path = data_root / "bronze" / "price_daily.jsonl"
    bronze_path.parent.mkdir(parents=True)
    rows = [
        {
            "symbol": "A32",
            "trading_date": f"2024-01-0{day}",
            "source": "vci",
            "normalized_close": float(day),
            "raw_close": float(day),
            "raw_volume": 100.0,
            "quality_flags": [],
            "source_observation_id": "vci:A32:test",
        }
        for day in (1, 2, 3)
    ]
    bronze_path.write_text(
        "".join(json.dumps(row) + "\n" for row in rows),
        encoding="utf-8",
    )
    events_path = tmp_path / "events.json"
    events_path.write_text(
        json.dumps(
            [
                {
                    "event_id": "event-cli",
                    "symbol": "A32",
                    "event_type": "cash_dividend",
                    "ex_date": "2024-01-02",
                    "source_url": "https://example.test/event",
                    "confidence": "high",
                }
            ]
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            "exploration/04_event_price_reconciliation.py",
            "--data-root",
            str(data_root),
            "--events-file",
            str(events_path),
            "--price-path",
            "bronze/price_daily.jsonl",
            "--before-bars",
            "1",
            "--after-bars",
            "1",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    output_path = data_root / "metadata" / "corporate_action_price_reconciliation.json"
    assert output_path.exists()
    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["entries"][0]["event_id"] == "event-cli"
    assert len(bronze_path.read_text(encoding="utf-8").splitlines()) == 3
