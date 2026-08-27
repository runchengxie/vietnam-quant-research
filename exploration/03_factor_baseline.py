"""Run the provisional daily factor baseline from an external research-price JSONL."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from vietnam_quant.backtest import BacktestConfig, run_factor_backtest, summarize_backtest
from vietnam_quant.factors import compute_features
from vietnam_quant.validation import summarize_factor_validation

DEFAULT_FACTORS = (
    "momentum_1m",
    "momentum_3m",
    "momentum_6m",
    "momentum_12m",
    "reversal_1m",
    "volatility_1m",
    "amihud_1m",
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--price-path", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--summary-output", type=Path)
    parser.add_argument("--validation-output", type=Path)
    parser.add_argument("--oos-fraction", type=float, default=0.3)
    parser.add_argument("--cost-bps", default="0,50,100", help="Comma-separated non-negative basis-point scenarios")
    parser.add_argument("--factor", action="append", dest="factors", help="Factor column; repeat for multiple factors")
    parser.add_argument("--exclude-boundary-proxy", action="store_true")
    return parser


def _costs(value: str) -> tuple[int, ...]:
    try:
        costs = tuple(int(part.strip()) for part in value.split(",") if part.strip())
    except ValueError as exc:
        raise ValueError("--cost-bps must be comma-separated integers") from exc
    if not costs:
        raise ValueError("--cost-bps must include at least one scenario")
    return costs


def _read_price_jsonl(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(path)
    frame = pd.read_json(path, lines=True)
    if frame.empty:
        raise ValueError("price JSONL is empty")
    return frame


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        frame = _read_price_jsonl(args.price_path)
        features = compute_features(frame)
        factors = tuple(args.factors or DEFAULT_FACTORS)
        config = BacktestConfig(
            cost_bps=_costs(args.cost_bps),
            oos_fraction=args.oos_fraction,
            exclude_boundary_proxy=args.exclude_boundary_proxy,
        )
        period_frames = [run_factor_backtest(features, factor, config) for factor in factors]
        periods = pd.concat(period_frames, ignore_index=True)
        summary = summarize_backtest(periods, oos_fraction=config.oos_fraction)
        validation_frames = [
            summarize_factor_validation(
                features,
                factor,
                horizons=(1, 5, 20),
                n_quantiles=5,
                oos_fraction=config.oos_fraction,
                min_cross_section=10,
            )
            for factor in factors
        ]
        validation = pd.concat(validation_frames, ignore_index=True)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        periods.to_csv(args.output, index=False)
        summary_path = args.summary_output or args.output.with_name(f"{args.output.stem}_summary.json")
        summary_path.parent.mkdir(parents=True, exist_ok=True)
        summary_path.write_text(
            json.dumps(summary.to_dict(orient="records"), ensure_ascii=False, indent=2, allow_nan=True),
            encoding="utf-8",
        )
        validation_path = args.validation_output or args.output.with_name(f"{args.output.stem}_validation.json")
        validation_path.parent.mkdir(parents=True, exist_ok=True)
        validation_path.write_text(
            json.dumps(validation.to_dict(orient="records"), ensure_ascii=False, indent=2, allow_nan=True),
            encoding="utf-8",
        )
        blocked_size = int((features["market_cap_status"] == "blocked_missing_market_cap").sum())
        print(json.dumps({
            "price_rows": len(frame),
            "feature_rows": len(features),
            "factors": list(factors),
            "period_rows": len(periods),
            "summary_rows": len(summary),
            "blocked_missing_market_cap_rows": blocked_size,
            "output": str(args.output),
            "summary_output": str(summary_path),
            "validation_output": str(validation_path),
        }, ensure_ascii=False, indent=2))
        return 0
    except (OSError, ValueError, KeyError) as exc:
        print(json.dumps({
            "status": "error",
            "error_type": type(exc).__name__,
            "error_message": str(exc),
        }, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
