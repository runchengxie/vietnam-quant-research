"""Orchestration for source observations, normalized bars, and quality reports."""

from __future__ import annotations

import time
from collections import Counter
from dataclasses import dataclass, replace
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from vietnam_quant.adapters import MarketDataAdapter
from vietnam_quant.quality import (
    arbitrate_price_bars,
    assess_research_quality,
    reconcile_price_bars,
    validate_price_bars,
)
from vietnam_quant.schemas import FetchResult, InstrumentRecord, PriceDailyRecord, SerializableMixin, SourceObservation
from vietnam_quant.storage import ExternalDataStore
from vietnam_quant.universe import select_sample


@dataclass(frozen=True)
class PipelineConfig:
    data_root: Path
    start: date
    end: date
    sample_size: int = 50
    primary_source: str = "vci"
    secondary_source: str | None = "kbs"
    strict: bool = False
    network: bool = False
    rate_limit_seconds: float = 0.0
    edge_symbols: tuple[str, ...] = ()
    exchange_quotas: Mapping[str, int] | None = None
    max_retries: int = 2

    def __post_init__(self):
        if self.start > self.end:
            raise ValueError("start must be on or before end")
        if self.sample_size < 0:
            raise ValueError("sample_size must be non-negative")


@dataclass(frozen=True)
class PipelineReport(SerializableMixin):
    selected_symbols: list[str]
    failed_symbols: list[str]
    secondary_failed_symbols: list[str]
    observation_count: int
    price_row_count: int
    quality_status: str
    strict_failed: bool
    quality_report: dict[str, Any]
    reconciliation_report: dict[str, Any]
    skipped_sources: list[str]
    research_quality_status: str = "FAIL"
    research_row_count: int = 0
    research_quarantined_row_count: int = 0
    factor_ready: bool = False
    research_report: dict[str, Any] = None
    message: str | None = None


_RETRYABLE_ERROR_TYPES = {
    "ConnectionError",
    "ConnectTimeout",
    "ReadTimeout",
    "Timeout",
    "RequestException",
}


def _is_retryable(result: FetchResult) -> bool:
    status_code = result.response_status or 0
    return (
        result.error_type in _RETRYABLE_ERROR_TYPES
        or status_code == 429
        or status_code >= 500
    )


def _estimate_count_back(start: date, end: date) -> int:
    calendar_days = (end - start).days + 1
    return max(32, int(calendar_days * 1.7) + 10)


def _fetch_with_retries(adapter: Any, symbol: str, end: date, count_back: int, start: date, max_retries: int) -> FetchResult:
    attempts = 0
    result = FetchResult(status="error", endpoint="")
    while attempts <= max_retries:
        attempts += 1
        try:
            result = adapter.fetch_daily(symbol, end, count_back, start_date=start)
        except TypeError:
            result = adapter.fetch_daily(symbol, end, count_back)
        result = replace(result, attempts=attempts)
        if not _is_retryable(result) or result.status == "ok" or attempts > max_retries:
            break
        time.sleep(min(2 ** (attempts - 1), 8))
    return result


def _observation_from_result(
    result: FetchResult,
    *,
    source: str,
    symbol: str | None,
    observation_id: str,
    raw_snapshot_path: str | None = None,
    raw_payload_sha256: str | None = None,
    row_count: int = 0,
    first_trading_date: date | None = None,
    last_trading_date: date | None = None,
    quality_status: str = "WARN",
    quality_issue_count: int = 0,
    parser_version: str = "unknown",
) -> SourceObservation:
    return SourceObservation(
        observation_id=observation_id, source=source, endpoint=result.endpoint, symbol=symbol,
        request_parameters=result.request_parameters, retrieved_at_utc=datetime.now(timezone.utc),
        response_status=result.response_status, latency_ms=result.latency_ms,
        raw_snapshot_path=raw_snapshot_path, raw_payload_sha256=raw_payload_sha256,
        row_count=row_count, first_trading_date=first_trading_date, last_trading_date=last_trading_date,
        quality_status=quality_status, quality_issue_count=quality_issue_count,
        parser_version=parser_version, error_type=result.error_type, error_message=result.error_message,
    )


def _listing_result(adapter: Any, max_retries: int) -> FetchResult:
    attempts = 0
    result = FetchResult(status="error", endpoint="")
    while attempts <= max_retries:
        attempts += 1
        result = adapter.fetch_listing()
        result = replace(result, attempts=attempts)
        if not _is_retryable(result) or result.status == "ok" or attempts > max_retries:
            break
        time.sleep(min(2 ** (attempts - 1), 8))
    return result


def run_pipeline(config: PipelineConfig, adapters: Mapping[str, MarketDataAdapter]) -> PipelineReport:
    store = ExternalDataStore(config.data_root)
    store.ensure_layout()
    if config.primary_source not in adapters:
        raise KeyError(f"primary adapter not provided: {config.primary_source}")
    primary_adapter = adapters[config.primary_source]
    retrieved_at = datetime.now(timezone.utc)
    run_date = retrieved_at.date()
    observations: list[SourceObservation] = []
    quality_entries: list[dict[str, Any]] = []
    reconciliation_entries: list[dict[str, Any]] = []
    skipped_sources: list[str] = []

    listing_result = _listing_result(primary_adapter, config.max_retries)
    listing_id = f"{config.primary_source}:listing:{run_date.isoformat()}"
    listing_raw_path = None
    listing_digest = None
    if listing_result.payload is not None:
        listing_raw_path, listing_digest = store.write_raw(config.primary_source, "_listing", listing_result.payload, run_date)
    listing: list[InstrumentRecord] = []
    if listing_result.status == "ok" and listing_result.payload is not None:
        try:
            listing = primary_adapter.parse_listing(listing_result.payload)
        except Exception as exc:
            listing_result = replace(listing_result, status="parse_error", error_type=type(exc).__name__, error_message=str(exc))
    listing_observation = _observation_from_result(
        listing_result, source=config.primary_source, symbol=None, observation_id=listing_id,
        raw_snapshot_path=str(listing_raw_path) if listing_raw_path else None, raw_payload_sha256=listing_digest,
        row_count=len(listing), quality_status="PASS" if listing else "FAIL",
        parser_version="listing-v1",
    )
    store.append_jsonl("metadata/source_observations.jsonl", listing_observation.to_dict(), key="observation_id")
    observations.append(listing_observation)
    if not listing:
        return PipelineReport(
            [], [], [], len(observations), 0, "FAIL", True, {}, {}, skipped_sources,
            message="listing unavailable",
        )

    selected = select_sample(
        listing, sample_size=config.sample_size, quotas=config.exchange_quotas, edge_symbols=config.edge_symbols
    )
    selected_by_symbol = {instrument.symbol: instrument for instrument in selected}
    instrument_output = [
        selected_by_symbol.get(instrument.symbol, instrument)
        for instrument in listing
    ]
    store.append_jsonl_many(
        "bronze/instrument_master.jsonl",
        [instrument.to_dict() for instrument in instrument_output],
        key="instrument_id",
    )
    selected_symbols = [record.symbol for record in selected]
    failed_symbols: list[str] = []
    secondary_failed_symbols: list[str] = []
    price_row_count = 0
    source_rows: dict[tuple[str, str], list[PriceDailyRecord]] = {}
    research_rows: list[PriceDailyRecord] = []
    arbitration_reports = []
    semantics_reports = []
    count_back = _estimate_count_back(config.start, config.end)

    sources = [config.primary_source]
    if config.secondary_source:
        if config.secondary_source not in adapters:
            skipped_sources.append(config.secondary_source)
        else:
            sources.append(config.secondary_source)
    for instrument in selected:
        for source in sources:
            adapter = adapters[source]
            if source == "ssi" and hasattr(adapter, "check_credentials"):
                credential_status = adapter.check_credentials()
                if credential_status.status == "skipped_missing_credentials":
                    skipped_sources.append(source)
                    observation = SourceObservation(
                        observation_id=f"{source}:{instrument.symbol}:credentials", source=source, endpoint=f"{source}://credentials",
                        symbol=instrument.symbol, quality_status="WARN", parser_version="credential-check-v1",
                        error_type="missing_credentials", error_message=credential_status.detail,
                    )
                    store.append_jsonl("metadata/source_observations.jsonl", observation.to_dict(), key="observation_id")
                    observations.append(observation)
                    continue
            observation_id = f"{source}:{instrument.symbol}:{config.start.isoformat()}:{config.end.isoformat()}"
            result = _fetch_with_retries(adapter, instrument.symbol, config.end, count_back, config.start, config.max_retries)
            raw_path = None
            digest = None
            if result.payload is not None:
                raw_path, digest = store.write_raw(source, instrument.symbol, result.payload, run_date)
            parsed: list[PriceDailyRecord] = []
            parser_version = "unknown"
            parse_error: Exception | None = None
            if result.status == "ok" and result.payload is not None:
                try:
                    parsed = adapter.parse_daily(result.payload, instrument.symbol, config.start, config.end)
                    parsed = [replace(row, source_observation_id=observation_id, exchange=instrument.exchange) for row in parsed]
                    parser_version = parsed[0].parser_version if parsed else "daily-v1"
                except Exception as exc:
                    parse_error = exc
                    result = replace(result, status="parse_error", error_type=type(exc).__name__, error_message=str(exc))
            if parse_error is not None or result.status != "ok":
                if source == config.primary_source:
                    failed_symbols.append(instrument.symbol)
                else:
                    secondary_failed_symbols.append(instrument.symbol)
            quality = validate_price_bars(parsed)
            store.append_jsonl_many(
                "bronze/price_daily.jsonl",
                [row.to_dict() for row in quality.rows],
                identity_fields=("source", "symbol", "trading_date"),
            )
            price_row_count += len(quality.rows) if source == config.primary_source else 0
            source_rows[(source, instrument.symbol)] = quality.rows
            diagnostic_flags = {"missing_required", "duplicate_date", "invalid_ohlc", "zero_volume"}
            diagnostic_rows = [
                row.to_dict()
                for row in quality.rows
                if diagnostic_flags & set(row.quality_flags)
            ]
            quality_entries.append({
                'source': source,
                'symbol': instrument.symbol,
                'status': quality.status,
                'issue_counts': quality.issue_counts,
                'issue_count': quality.issue_count,
                'diagnostic_row_count': len(diagnostic_rows),
                'diagnostic_rows': diagnostic_rows,
            })
            first_day = min((row.trading_date for row in quality.rows), default=None)
            last_day = max((row.trading_date for row in quality.rows), default=None)
            observation = _observation_from_result(
                result, source=source, symbol=instrument.symbol, observation_id=observation_id,
                raw_snapshot_path=str(raw_path) if raw_path else None, raw_payload_sha256=digest,
                row_count=len(quality.rows), first_trading_date=first_day, last_trading_date=last_day,
                quality_status=quality.status if result.status == "ok" else "FAIL",
                quality_issue_count=quality.issue_count, parser_version=parser_version,
            )
            store.append_jsonl("metadata/source_observations.jsonl", observation.to_dict(), key="observation_id")
            observations.append(observation)
            if config.rate_limit_seconds > 0:
                time.sleep(config.rate_limit_seconds)
        if config.secondary_source:
            primary_rows = source_rows.get((config.primary_source, instrument.symbol))
            secondary_rows = source_rows.get((config.secondary_source, instrument.symbol))
            if primary_rows is not None and secondary_rows is not None:
                reconciliation = reconcile_price_bars(primary_rows, secondary_rows)
                reconciliation_entries.append({'symbol': instrument.symbol, **reconciliation.to_dict()})
        primary_rows = source_rows.get((config.primary_source, instrument.symbol), [])
        secondary_rows = (
            source_rows.get((config.secondary_source, instrument.symbol), [])
            if config.secondary_source else []
        )
        selected_rows, arbitration_report, semantics_report = arbitrate_price_bars(
            primary_rows,
            secondary_rows,
            primary_source=config.primary_source,
            secondary_source=config.secondary_source,
            symbol=instrument.symbol,
        )
        research_rows.extend(selected_rows)
        arbitration_reports.append(arbitration_report)
        semantics_reports.append(semantics_report)

    quality_status = "FAIL" if failed_symbols or any(entry.get("status") == "FAIL" for entry in quality_entries) else ("WARN" if quality_entries else "FAIL")
    strict_failed = bool(failed_symbols or not selected or quality_status == "FAIL")
    quality_issue_counts: Counter[str] = Counter()
    for entry in quality_entries:
        quality_issue_counts.update(entry.get('issue_counts', {}))
    quality_summary = {
        'status': quality_status,
        'entry_count': len(quality_entries),
        'issue_counts': dict(sorted(quality_issue_counts.items())),
        'diagnostic_row_count': sum(entry.get('diagnostic_row_count', 0) for entry in quality_entries),
    }
    store.write_json('metadata/quality_report.json', {'summary': quality_summary, 'entries': quality_entries})
    store.write_json('metadata/reconciliation_report.json', {'entries': reconciliation_entries})
    reconciliation_summary = {
        'entry_count': len(reconciliation_entries),
        'warn_count': sum(entry.get('status') == 'WARN' for entry in reconciliation_entries),
        'matched_dates': sum(entry.get('matched_dates', 0) for entry in reconciliation_entries),
    }
    store.append_jsonl_many(
        "derived/research_price_daily.jsonl",
        [row.to_dict() for row in research_rows],
        identity_fields=("symbol", "trading_date"),
    )
    semantics_status = "unresolved" if config.secondary_source and semantics_reports else "not_available"
    research_summary = assess_research_quality(
        arbitration_reports,
        expected_symbols=selected_symbols,
        observations=observations,
        semantics_status=semantics_status,
    )
    store.write_json(
        "metadata/source_arbitration_report.json",
        {"entries": [report.to_dict() for report in arbitration_reports]},
    )
    store.write_json(
        "metadata/price_semantics_report.json",
        {"entries": [report.to_dict() for report in semantics_reports]},
    )
    store.write_json("metadata/research_quality_report.json", research_summary)
    message = "primary source has failed symbols" if failed_symbols else None
    return PipelineReport(
        selected_symbols=selected_symbols, failed_symbols=failed_symbols, secondary_failed_symbols=secondary_failed_symbols,
        observation_count=len(observations), price_row_count=price_row_count, quality_status=quality_status,
        strict_failed=strict_failed, quality_report=quality_summary,
        reconciliation_report=reconciliation_summary, skipped_sources=sorted(set(skipped_sources)),
        research_quality_status=research_summary["status"],
        research_row_count=len(research_rows),
        research_quarantined_row_count=research_summary["quarantined_rows"],
        factor_ready=research_summary["factor_ready"],
        research_report=research_summary,
        message=message,
    )
