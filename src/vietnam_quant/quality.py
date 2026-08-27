"""Quality flags and cross-source reconciliation for normalized daily bars."""

from __future__ import annotations

from collections import Counter
from dataclasses import replace
from typing import Iterable

from vietnam_quant.schemas import PriceDailyRecord, QualityReport, ReconciliationReport

REQUIRED_FIELDS = (
    "symbol",
    "trading_date",
    "normalized_open",
    "normalized_high",
    "normalized_low",
    "normalized_close",
    "raw_volume",
)


def _add_flag(row: PriceDailyRecord, flag: str) -> PriceDailyRecord:
    if flag in row.quality_flags:
        return row
    return replace(row, quality_flags=[*row.quality_flags, flag])


def _value_is_missing(value: object) -> bool:
    return value is None or value == ""


def validate_price_bars(rows: Iterable[PriceDailyRecord]) -> QualityReport:
    """Return flagged copies while retaining every input row."""
    original = list(rows)
    dates = [row.trading_date for row in original]
    duplicate_dates = {day for day, count in Counter(dates).items() if count > 1}
    source_reordered = dates != sorted(dates)
    checked: list[PriceDailyRecord] = []
    for row in original:
        current = row
        if any(_value_is_missing(getattr(row, field, None)) for field in REQUIRED_FIELDS):
            current = _add_flag(current, "missing_required")
        if row.trading_date in duplicate_dates:
            current = _add_flag(current, "duplicate_date")
        if source_reordered:
            current = _add_flag(current, "reordered_source_rows")
        values = [row.normalized_open, row.normalized_high, row.normalized_low, row.normalized_close]
        numeric = all(isinstance(value, (int, float)) for value in values)
        if numeric:
            open_value, high_value, low_value, close_value = values
            if high_value < max(open_value, close_value) or low_value > min(open_value, close_value):
                current = _add_flag(current, "invalid_ohlc")
            if min(open_value, high_value, low_value, close_value) < 0:
                current = _add_flag(current, "invalid_ohlc")
            if close_value == high_value or close_value == low_value:
                current = _add_flag(current, "boundary_price_proxy")
        if isinstance(row.raw_volume, (int, float)) and row.raw_volume < 0:
            current = _add_flag(current, "invalid_ohlc")
        if row.raw_volume == 0:
            current = _add_flag(current, "zero_volume")
        checked.append(current)
    issue_counts: Counter[str] = Counter(
        flag for row in checked for flag in row.quality_flags
    )
    issue_count = sum(issue_counts.values())
    severe = {"missing_required", "invalid_ohlc"}
    status = "FAIL" if severe & set(issue_counts) else ("WARN" if issue_count else "PASS")
    return QualityReport(
        rows=checked,
        issue_counts=dict(sorted(issue_counts.items())),
        issue_count=issue_count,
        status=status,
    )


def _close(row: PriceDailyRecord) -> float | None:
    return row.normalized_close if row.normalized_close is not None else row.raw_close


def reconcile_price_bars(
    primary: Iterable[PriceDailyRecord],
    secondary: Iterable[PriceDailyRecord],
    relative_tolerance: float = 0.001,
) -> ReconciliationReport:
    """Compare bars by trading date without dropping or rewriting either source."""
    primary_by_date = {row.trading_date: row for row in primary}
    secondary_by_date = {row.trading_date: row for row in secondary}
    primary_dates = set(primary_by_date)
    secondary_dates = set(secondary_by_date)
    common_dates = sorted(primary_dates & secondary_dates)
    differences: list[dict[str, object]] = []
    for day in common_dates:
        primary_close = _close(primary_by_date[day])
        secondary_close = _close(secondary_by_date[day])
        if primary_close is None or secondary_close is None:
            continue
        absolute = abs(primary_close - secondary_close)
        relative = absolute / max(abs(primary_close), abs(secondary_close), 1e-12)
        if relative > relative_tolerance:
            differences.append({
                "trading_date": day.isoformat(),
                "primary_close": primary_close,
                "secondary_close": secondary_close,
                "absolute_difference": absolute,
                "relative_difference": relative,
            })
    missing_in_primary = sorted(day.isoformat() for day in secondary_dates - primary_dates)
    missing_in_secondary = sorted(day.isoformat() for day in primary_dates - secondary_dates)
    status = "WARN" if missing_in_primary or missing_in_secondary or differences else "PASS"
    return ReconciliationReport(
        missing_in_primary=missing_in_primary,
        missing_in_secondary=missing_in_secondary,
        close_differences=differences,
        matched_dates=len(common_dates),
        status=status,
    )
