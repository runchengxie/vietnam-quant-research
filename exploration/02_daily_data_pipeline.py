"""Run the auditable VCI/KBS daily data pipeline into an external data root."""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import date
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from vietnam_quant.adapters.kbs import KBSAdapter
from vietnam_quant.adapters.ssi import SSIAdapter
from vietnam_quant.adapters.vci import VCIAdapter
from vietnam_quant.pipeline import PipelineConfig, run_pipeline


DEFAULT_DATA_ROOT = Path(r"D:\data\vietnam-quant-research")


def _date(value: str) -> date:
    return date.fromisoformat(value)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", default=os.environ.get("VIETNAM_QUANT_DATA_ROOT", str(DEFAULT_DATA_ROOT)))
    parser.add_argument("--start", type=_date, default=date(2018, 1, 1))
    parser.add_argument("--end", type=_date, default=date.today())
    parser.add_argument("--sample-size", type=int, default=50)
    parser.add_argument("--symbols-file", type=Path)
    parser.add_argument("--primary-source", choices=("vci", "kbs", "ssi"), default="vci")
    parser.add_argument("--secondary-source", choices=("vci", "kbs", "ssi", "none"), default="kbs")
    parser.add_argument("--rate-limit-seconds", type=float, default=0.25)
    parser.add_argument("--network", action="store_true", help="Explicitly enable HTTP requests")
    parser.add_argument("--strict", action="store_true", help="Return non-zero if coverage or quality gates fail")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not args.network:
        print(
            "Network access is disabled. Use --network for the pilot, or provide a fixture/cached raw input "
            "through the library pipeline; no HTTP request was made.",
            file=sys.stderr,
        )
        return 2
    edge_symbols: tuple[str, ...] = ()
    if args.symbols_file:
        edge_symbols = tuple(
            line.strip().upper()
            for line in args.symbols_file.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        )
    sample_size = len(edge_symbols) if args.symbols_file else args.sample_size
    adapters = {"vci": VCIAdapter(), "kbs": KBSAdapter(), "ssi": SSIAdapter()}
    secondary = None if args.secondary_source == "none" else args.secondary_source
    config = PipelineConfig(
        data_root=Path(args.data_root),
        start=args.start,
        end=args.end,
        sample_size=sample_size,
        primary_source=args.primary_source,
        secondary_source=secondary,
        strict=args.strict,
        network=True,
        rate_limit_seconds=args.rate_limit_seconds,
        edge_symbols=edge_symbols,
    )
    try:
        report = run_pipeline(config, adapters)
    except (OSError, ValueError, KeyError) as exc:
        print(json.dumps({"status": "error", "error_type": type(exc).__name__, "error_message": str(exc)}, ensure_ascii=False))
        return 1
    print(json.dumps(report.to_dict(), ensure_ascii=False, indent=2))
    return 1 if args.strict and report.strict_failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
