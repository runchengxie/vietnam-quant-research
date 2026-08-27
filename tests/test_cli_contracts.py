import subprocess
import sys


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


def test_daily_pipeline_without_network_does_not_fetch():
    result = subprocess.run(
        [sys.executable, "exploration/02_daily_data_pipeline.py", "--data-root", "offline-test-root"],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 2
    assert "no HTTP request was made" in result.stderr
