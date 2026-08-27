import json
import subprocess
import sys

import pandas as pd


def test_daily_pipeline_help_is_offline():
    result = subprocess.run(
        [sys.executable, "exploration/02_daily_data_pipeline.py", "--help"],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "--data-root" in result.stdout
    assert "--network" in result.stdout


def test_factor_baseline_help_is_offline():
    result = subprocess.run(
        [sys.executable, "exploration/03_factor_baseline.py", "--help"],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "--price-path" in result.stdout
    assert "--cost-bps" in result.stdout
    assert "--validation-output" in result.stdout


def test_factor_baseline_writes_validation_json(tmp_path):
    rows = []
    dates = pd.date_range("2024-01-02", periods=80, freq="B")
    for day_index, date in enumerate(dates):
        for symbol_index in range(20):
            close = 100 + symbol_index * 2 + day_index * (1 + symbol_index / 100)
            rows.append(
                {
                    "symbol": f"S{symbol_index:02d}",
                    "trading_date": date.strftime("%Y-%m-%d"),
                    "normalized_open": close * 1.001,
                    "normalized_close": close,
                    "raw_volume": 1000 + symbol_index,
                    "quality_flags": [],
                }
            )
    price_path = tmp_path / "prices.jsonl"
    output_path = tmp_path / "periods.csv"
    pd.DataFrame(rows).to_json(price_path, orient="records", lines=True)

    result = subprocess.run(
        [
            sys.executable,
            "exploration/03_factor_baseline.py",
            "--price-path",
            str(price_path),
            "--output",
            str(output_path),
            "--factor",
            "momentum_1m",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    assert {
        "price_rows", "feature_rows", "factors", "period_rows", "summary_rows",
        "blocked_missing_market_cap_rows", "output", "summary_output",
    } <= set(payload)
    validation_path = tmp_path / "periods_validation.json"
    assert validation_path.exists()
    validation = json.loads(validation_path.read_text(encoding="utf-8"))
    assert any(row["factor"] == "momentum_1m" and row["horizon"] == 1 for row in validation)
    summary = json.loads((tmp_path / "periods_summary.json").read_text(encoding="utf-8"))
    assert {0, 50, 100} <= {row["cost_bps"] for row in summary}
    assert '"validation_output"' in result.stdout


def test_daily_pipeline_without_network_does_not_fetch():
    result = subprocess.run(
        [sys.executable, "exploration/02_daily_data_pipeline.py", "--data-root", "offline-test-root"],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 2
    assert "no HTTP request was made" in result.stderr
