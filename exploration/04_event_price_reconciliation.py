"""Generate an offline corporate-action to price evidence report."""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import date
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from vietnam_quant.corporate_actions import parse_corporate_action_events
from vietnam_quant.event_price import (
    reconcile_corporate_action_prices,
    write_event_price_reconciliation,
)
from vietnam_quant.schemas import PriceDailyRecord
from vietnam_quant.storage import ExternalDataStore


DEFAULT_DATA_ROOT = Path(r"D:\data\vietnam-quant-research")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--data-root",
        default=os.environ.get("VIETNAM_QUANT_DATA_ROOT", str(DEFAULT_DATA_ROOT)),
    )
    parser.add_argument("--events-file", type=Path, required=True)
    parser.add_argument("--price-path", default="bronze/price_daily.jsonl")
    parser.add_argument("--before-bars", type=int, default=5)
    parser.add_argument("--after-bars", type=int, default=5)
    return parser


def _read_events(path: Path):
    if path.suffix.lower() == ".jsonl":
        payload = [
            json.loads(line)
            for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
    else:
        payload = json.loads(path.read_text(encoding="utf-8"))
    return parse_corporate_action_events(payload)


def _read_price_rows(store: ExternalDataStore, price_path: str) -> list[PriceDailyRecord]:
    path = Path(price_path)
    if path.is_absolute():
        records = [
            json.loads(line)
            for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
    else:
        records = store.read_jsonl(path)
    output: list[PriceDailyRecord] = []
    for record in records:
        normalized = dict(record)
        normalized["trading_date"] = date.fromisoformat(normalized["trading_date"])
        output.append(PriceDailyRecord(**normalized))
    return output


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        store = ExternalDataStore(args.data_root)
        events = _read_events(args.events_file)
        price_rows = _read_price_rows(store, args.price_path)
        reports = reconcile_corporate_action_prices(
            events,
            price_rows,
            before_bars=args.before_bars,
            after_bars=args.after_bars,
        )
        jsonl_path, json_path = write_event_price_reconciliation(store, reports)
    except (OSError, TypeError, ValueError, KeyError) as exc:
        print(
            json.dumps(
                {"status": "error", "error_type": type(exc).__name__, "error_message": str(exc)},
                ensure_ascii=False,
            )
        )
        return 1
    print(
        json.dumps(
            {
                "status": "ok",
                "event_count": len(reports),
                "price_row_count": len(price_rows),
                "jsonl_output": str(jsonl_path),
                "json_output": str(json_path),
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
