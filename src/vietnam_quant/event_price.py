"""Auditable evidence linking corporate-action dates to nearby price bars."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable
from datetime import date
from pathlib import Path
from statistics import median
from typing import Any

from .schemas import (
    CorporateActionEvent,
    CorporateActionPriceReconciliation,
    PriceDailyRecord,
)
from .storage import ExternalDataStore


def select_event_reference_date(event: CorporateActionEvent) -> tuple[date | None, str]:
    """Select an explicit event date without treating payment as ex-date."""

    if event.ex_date is not None:
        return event.ex_date, "ex_date"
    event_type = event.event_type.lower()
    if event.listing_date is not None and any(
        marker in event_type for marker in ("listing", "share", "stock", "rights")
    ):
        return event.listing_date, "listing_date"
    if event.announcement_date is not None:
        return event.announcement_date, "announcement_date_reference_only"
    return None, "none"


def _event_dates(event: CorporateActionEvent) -> dict[str, date | None]:
    return {
        "announcement_date": event.announcement_date,
        "ex_date": event.ex_date,
        "record_date": event.record_date,
        "payment_date": event.payment_date,
        "listing_date": event.listing_date,
    }


def _close(row: PriceDailyRecord) -> float | None:
    if row.normalized_close is not None:
        return row.normalized_close
    return row.raw_close


def _bar_evidence(row: PriceDailyRecord) -> dict[str, Any]:
    return {
        "symbol": row.symbol,
        "source": row.source,
        "trading_date": row.trading_date,
        "raw_open": row.raw_open,
        "raw_high": row.raw_high,
        "raw_low": row.raw_low,
        "raw_close": row.raw_close,
        "raw_volume": row.raw_volume,
        "raw_price_unit": row.raw_price_unit,
        "normalized_open": row.normalized_open,
        "normalized_high": row.normalized_high,
        "normalized_low": row.normalized_low,
        "normalized_close": row.normalized_close,
        "normalized_price_unit": row.normalized_price_unit,
        "volume_unit": row.volume_unit,
        "quality_flags": list(row.quality_flags),
        "source_observation_id": row.source_observation_id,
    }


def _source_evidence(
    rows: list[PriceDailyRecord],
    reference_date: date | None,
    *,
    before_bars: int,
    after_bars: int,
) -> dict[str, Any]:
    if reference_date is None:
        selected: list[PriceDailyRecord] = []
        before: list[PriceDailyRecord] = []
        exact: list[PriceDailyRecord] = []
        after: list[PriceDailyRecord] = []
    else:
        before_candidates = [row for row in rows if row.trading_date < reference_date]
        before = before_candidates[-before_bars:] if before_bars else []
        exact = [row for row in rows if row.trading_date == reference_date]
        after_candidates = [row for row in rows if row.trading_date > reference_date]
        after = after_candidates[:after_bars] if after_bars else []
        selected = [*before, *exact, *after]

    def close_at(items: list[PriceDailyRecord]) -> float | None:
        return next((_close(row) for row in items if _close(row) is not None), None)

    pre_close = close_at(list(reversed(before)))
    reference_close = close_at(exact)
    post_close = close_at(after)
    pre_to_post_return = None
    if pre_close not in (None, 0) and post_close is not None:
        pre_to_post_return = post_close / pre_close - 1.0

    flags = [flag for row in selected for flag in row.quality_flags]
    return {
        "bars": [_bar_evidence(row) for row in selected],
        "available_bar_count": len(selected),
        "reference_date_present": bool(exact),
        "context_available": bool(before and after),
        "pre_close": pre_close,
        "reference_close": reference_close,
        "post_close": post_close,
        "pre_to_post_return": pre_to_post_return,
        "zero_volume_count": sum(
            flag == "zero_volume" for flag in flags
        ),
        "invalid_ohlc_count": sum(flag == "invalid_ohlc" for flag in flags),
    }


def _cross_source_summary(
    source_evidence: dict[str, dict[str, Any]],
    *,
    relative_tolerance: float,
) -> dict[str, Any]:
    source_names = sorted(source_evidence)
    if len(source_names) < 2:
        return {
            "sources": source_names,
            "common_date_count": 0,
            "close_difference_count": 0,
            "relative_difference_median": None,
            "relative_difference_max": None,
            "missing_date_count": 0,
            "invalid_context_count": sum(
                evidence["invalid_ohlc_count"] for evidence in source_evidence.values()
            ),
        }

    date_to_close: dict[str, dict[date, float]] = {}
    date_sets: dict[str, set[date]] = {}
    for source in source_names:
        date_to_close[source] = {}
        for bar in source_evidence[source]["bars"]:
            close = bar["normalized_close"]
            if close is not None:
                date_to_close[source][bar["trading_date"]] = close
        date_sets[source] = {
            bar["trading_date"] for bar in source_evidence[source]["bars"]
        }
    first, second = source_names[:2]
    common_dates = sorted(date_sets[first] & date_sets[second])
    relative_differences = []
    for day in common_dates:
        first_close = date_to_close[first].get(day)
        second_close = date_to_close[second].get(day)
        if first_close is None or second_close is None:
            continue
        denominator = max(abs(first_close), abs(second_close), 1e-12)
        relative_differences.append(abs(first_close - second_close) / denominator)
    return {
        "sources": source_names,
        "common_date_count": len(common_dates),
        "close_difference_count": sum(
            difference > relative_tolerance for difference in relative_differences
        ),
        "relative_difference_median": median(relative_differences)
        if relative_differences
        else None,
        "relative_difference_max": max(relative_differences)
        if relative_differences
        else None,
        "missing_date_count": sum(
            len(date_sets[source_names[index]] - date_sets[source_names[1 - index]])
            for index in (0, 1)
        ),
        "invalid_context_count": sum(
            evidence["invalid_ohlc_count"] for evidence in source_evidence.values()
        ),
    }


def reconcile_corporate_action_prices(
    events: Iterable[CorporateActionEvent],
    price_rows: Iterable[PriceDailyRecord],
    *,
    before_bars: int = 5,
    after_bars: int = 5,
    relative_tolerance: float = 0.001,
) -> list[CorporateActionPriceReconciliation]:
    """Build descriptive event windows without altering source price rows."""

    if before_bars < 0 or after_bars < 0:
        raise ValueError("before_bars and after_bars must be non-negative")
    if relative_tolerance < 0:
        raise ValueError("relative_tolerance must be non-negative")

    rows_by_symbol_source: dict[tuple[str, str], list[PriceDailyRecord]] = defaultdict(list)
    for row in price_rows:
        rows_by_symbol_source[(row.symbol.upper(), row.source)].append(row)
    for rows in rows_by_symbol_source.values():
        rows.sort(key=lambda row: row.trading_date)

    reports: list[CorporateActionPriceReconciliation] = []
    for event in events:
        reference_date, reference_date_kind = select_event_reference_date(event)
        source_evidence: dict[str, dict[str, Any]] = {}
        for (symbol, source), rows in rows_by_symbol_source.items():
            if symbol != event.symbol.upper():
                continue
            source_evidence[source] = _source_evidence(
                rows,
                reference_date,
                before_bars=before_bars,
                after_bars=after_bars,
            )

        cross_source = _cross_source_summary(
            source_evidence,
            relative_tolerance=relative_tolerance,
        )
        contexts = [
            evidence
            for evidence in source_evidence.values()
            if evidence["context_available"]
        ]
        exact_context = any(
            evidence["reference_date_present"] for evidence in contexts
        )
        has_conflict = bool(
            cross_source["close_difference_count"]
            or cross_source["invalid_context_count"]
        )
        if not contexts:
            assessment = "no_evidence"
        elif has_conflict:
            assessment = "unresolved"
        elif exact_context:
            assessment = "matched"
        else:
            assessment = "nearby"
        if reference_date is None:
            assessment = "no_evidence"

        reports.append(
            CorporateActionPriceReconciliation(
                event_id=event.event_id,
                symbol=event.symbol,
                event_type=event.event_type,
                reference_date=reference_date,
                reference_date_kind=reference_date_kind,
                event_dates=_event_dates(event),
                source_evidence=source_evidence,
                cross_source=cross_source,
                assessment=assessment,
                notes=(
                    "Evidence only; price changes are not attributed to the event "
                    "and no adjustment factor was inferred."
                ),
            )
        )
    return reports


def write_event_price_reconciliation(
    store: ExternalDataStore,
    reports: Iterable[CorporateActionPriceReconciliation],
    *,
    relative_jsonl: Path | str = "metadata/corporate_action_price_reconciliation.jsonl",
    relative_json: Path | str = "metadata/corporate_action_price_reconciliation.json",
) -> tuple[Path, Path]:
    """Persist event evidence without duplicating stable event IDs."""

    serialized = [report.to_dict() for report in reports]
    existing = store.read_jsonl(relative_jsonl)
    positions = {record.get("event_id"): index for index, record in enumerate(existing)}
    merged = list(existing)
    for record in serialized:
        event_id = record.get("event_id")
        if event_id in positions:
            merged[positions[event_id]] = record
        else:
            positions[event_id] = len(merged)
            merged.append(record)
    jsonl_path = store.write_jsonl(relative_jsonl, merged)
    json_path = store.write_json(relative_json, {"entries": serialized})
    return jsonl_path, json_path


__all__ = [
    "reconcile_corporate_action_prices",
    "select_event_reference_date",
    "write_event_price_reconciliation",
]
