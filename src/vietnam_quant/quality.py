"""Quality flags and cross-source reconciliation for normalized daily bars."""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import replace
from dataclasses import fields
from datetime import date
from typing import Any, Iterable

from vietnam_quant.schemas import (
    PriceDailyRecord,
    PriceSemanticsReport,
    QualityReport,
    ReconciliationReport,
    ResearchPriceDailyRecord,
    SourceArbitrationReport,
)

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


_RESEARCH_BLOCKING_FLAGS = {"missing_required", "invalid_ohlc", "duplicate_date"}


def _copy_as_research(
    row: PriceDailyRecord,
    *,
    quality_flags: list[str],
    research_status: str,
    arbitration_reason: str,
    research_eligible: bool,
    tradable: bool,
) -> ResearchPriceDailyRecord:
    base_values = {field.name: getattr(row, field.name) for field in fields(PriceDailyRecord)}
    base_values["quality_flags"] = quality_flags
    return ResearchPriceDailyRecord(
        **base_values,
        research_status=research_status,
        arbitration_reason=arbitration_reason,
        research_eligible=research_eligible,
        tradable=tradable,
    )


def _rows_by_date(rows: Iterable[PriceDailyRecord]) -> dict[date, list[PriceDailyRecord]]:
    grouped: dict[date, list[PriceDailyRecord]] = defaultdict(list)
    for row in rows:
        grouped[row.trading_date].append(row)
    return dict(grouped)


def _valid_candidate(rows: list[PriceDailyRecord]) -> PriceDailyRecord | None:
    if len(rows) != 1:
        return None
    candidate = rows[0]
    if _RESEARCH_BLOCKING_FLAGS & set(candidate.quality_flags):
        return None
    return candidate


def _percentile(values: list[float], fraction: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    index = min(len(ordered) - 1, int((len(ordered) - 1) * fraction))
    return ordered[index]


def _semantic_summary(
    primary_by_date: dict[date, list[PriceDailyRecord]],
    secondary_by_date: dict[date, list[PriceDailyRecord]],
    *,
    symbol: str,
    primary_source: str,
    secondary_source: str | None,
    relative_tolerance: float,
) -> PriceSemanticsReport:
    ratios: list[float] = []
    relative_differences: list[float] = []
    yearly: dict[str, list[float]] = defaultdict(list)
    for day in sorted(set(primary_by_date) & set(secondary_by_date)):
        primary = _valid_candidate(primary_by_date[day])
        secondary = _valid_candidate(secondary_by_date[day])
        if primary is None or secondary is None:
            continue
        primary_close = _close(primary)
        secondary_close = _close(secondary)
        if primary_close is None or secondary_close is None or primary_close == 0:
            continue
        ratio = secondary_close / primary_close
        relative = abs(primary_close - secondary_close) / max(abs(primary_close), abs(secondary_close), 1e-12)
        ratios.append(ratio)
        relative_differences.append(relative)
        yearly[str(day.year)].append(relative)
    yearly_summary = {
        year: {
            "matched_dates": len(values),
            "difference_count": sum(value > relative_tolerance for value in values),
            "relative_difference_median": _percentile(values, 0.5),
            "relative_difference_p90": _percentile(values, 0.9),
            "relative_difference_max": max(values) if values else None,
        }
        for year, values in sorted(yearly.items())
    }
    return PriceSemanticsReport(
        symbol=symbol,
        primary_source=primary_source,
        secondary_source=secondary_source,
        status="unresolved",
        matched_dates=len(relative_differences),
        difference_count=sum(value > relative_tolerance for value in relative_differences),
        ratio_median=_percentile(ratios, 0.5),
        ratio_p90=_percentile(ratios, 0.9),
        ratio_max=max(ratios) if ratios else None,
        relative_difference_median=_percentile(relative_differences, 0.5),
        relative_difference_p90=_percentile(relative_differences, 0.9),
        relative_difference_max=max(relative_differences) if relative_differences else None,
        yearly=yearly_summary,
    )


def arbitrate_price_bars(
    primary: Iterable[PriceDailyRecord],
    secondary: Iterable[PriceDailyRecord],
    *,
    primary_source: str,
    secondary_source: str | None,
    relative_tolerance: float = 0.001,
    symbol: str | None = None,
) -> tuple[list[ResearchPriceDailyRecord], SourceArbitrationReport, PriceSemanticsReport]:
    """Build a traceable research view without changing source rows."""
    primary_quality = validate_price_bars(primary)
    secondary_quality = validate_price_bars(secondary)
    primary_by_date = _rows_by_date(primary_quality.rows)
    secondary_by_date = _rows_by_date(secondary_quality.rows)
    inferred_symbol = symbol or next(
        (row.symbol for row in [*primary_quality.rows, *secondary_quality.rows]),
        "UNKNOWN",
    )
    selected_rows: list[ResearchPriceDailyRecord] = []
    primary_selected_count = 0
    secondary_selected_count = 0
    fallback_count = 0
    quarantine_count = 0
    zero_volume_count = 0
    disagreement_count = 0
    sample_disagreements: list[dict[str, Any]] = []
    for day in sorted(set(primary_by_date) | set(secondary_by_date)):
        primary_candidate = _valid_candidate(primary_by_date.get(day, []))
        secondary_candidate = _valid_candidate(secondary_by_date.get(day, []))
        primary_present = bool(primary_by_date.get(day))
        secondary_present = bool(secondary_by_date.get(day))
        if primary_candidate is not None:
            selected = primary_candidate
            primary_selected_count += 1
            reason = "primary_valid" if secondary_present else "primary_only"
            status = "selected"
        elif secondary_candidate is not None:
            selected = secondary_candidate
            secondary_selected_count += 1
            fallback_count += int(primary_present)
            reason = "secondary_fallback" if primary_present else "secondary_only"
            status = "selected"
        else:
            selected = (primary_by_date.get(day) or secondary_by_date.get(day) or [None])[0]
            if selected is None:
                continue
            reason = "both_invalid_primary_kept" if primary_present else "secondary_only"
            status = "quarantined"
            quarantine_count += 1

        derived_flags = list(selected.quality_flags)
        if primary_candidate is not None and secondary_candidate is not None:
            primary_close = _close(primary_candidate)
            secondary_close = _close(secondary_candidate)
            if primary_close is not None and secondary_close is not None:
                absolute = abs(primary_close - secondary_close)
                relative = absolute / max(abs(primary_close), abs(secondary_close), 1e-12)
                if relative > relative_tolerance:
                    derived_flags.append("source_disagreement")
                    disagreement_count += 1
                    if len(sample_disagreements) < 5:
                        sample_disagreements.append({
                            "trading_date": day.isoformat(),
                            "primary_close": primary_close,
                            "secondary_close": secondary_close,
                            "absolute_difference": absolute,
                            "relative_difference": relative,
                            "selected_source": selected.source,
                        })
        research_eligible = not (_RESEARCH_BLOCKING_FLAGS & set(derived_flags))
        tradable = research_eligible and selected.raw_volume is not None and selected.raw_volume > 0
        if selected.raw_volume == 0:
            zero_volume_count += 1
        selected_rows.append(_copy_as_research(
            selected,
            quality_flags=sorted(set(derived_flags)),
            research_status=status,
            arbitration_reason=reason,
            research_eligible=research_eligible,
            tradable=tradable,
        ))
    selected_count = len(selected_rows)
    eligible_count = sum(row.research_eligible for row in selected_rows)
    tradable_count = sum(row.tradable for row in selected_rows)
    report = SourceArbitrationReport(
        symbol=inferred_symbol,
        primary_source=primary_source,
        secondary_source=secondary_source,
        primary_row_count=len(primary_quality.rows),
        secondary_row_count=len(secondary_quality.rows),
        selected_row_count=selected_count,
        primary_selected_count=primary_selected_count,
        secondary_selected_count=secondary_selected_count,
        fallback_count=fallback_count,
        quarantine_count=quarantine_count,
        zero_volume_count=zero_volume_count,
        disagreement_count=disagreement_count,
        missing_both_count=0,
        research_eligible_count=eligible_count,
        tradable_count=tradable_count,
        coverage_rate=eligible_count / selected_count if selected_count else 0.0,
        tradable_rate=tradable_count / selected_count if selected_count else 0.0,
        sample_disagreements=sample_disagreements,
    )
    semantics = _semantic_summary(
        primary_by_date,
        secondary_by_date,
        symbol=inferred_symbol,
        primary_source=primary_source,
        secondary_source=secondary_source,
        relative_tolerance=relative_tolerance,
    )
    return selected_rows, report, semantics


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
