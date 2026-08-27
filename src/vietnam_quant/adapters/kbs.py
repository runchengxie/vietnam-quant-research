"""KBS daily data adapter."""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any

import requests

from vietnam_quant.schemas import FetchResult, InstrumentRecord, PriceDailyRecord
from vietnam_quant.adapters.vci import (
    _as_records, _ohlcv_records, _parse_event_time, _record_from_values,
    _first,
)

KBS_BASE_URL = "https://kbbuddywts.kbsec.com.vn/iis-server/investment/stocks"
KBS_HEADERS = {"Accept": "application/json, text/plain, */*", "User-Agent": "vietnam-quant-research daily data loop", "x-lang": "vi"}


def parse_kbs_ohlcv(
    payload: object,
    symbol: str,
    requested_start: date,
    requested_end: date,
    source_observation_id: str,
    exchange: str | None = None,
) -> list[PriceDailyRecord]:
    rows = _ohlcv_records(payload, preferred_keys=("data_day", "data_1D", "data_1d"))
    parsed: list[tuple[date, PriceDailyRecord]] = []
    source_dates: list[date] = []
    for row in rows:
        event_date, event_time_utc = _parse_event_time(row.get("time"))
        if event_date is None:
            continue
        source_dates.append(event_date)
        parsed.append((event_date, _record_from_values(
            row, symbol=symbol.upper(), source="kbs", exchange=exchange,
            parser_version="kbs-ohlcv-v1", source_observation_id=source_observation_id,
            event_date=event_date, event_time_utc=event_time_utc, event_time_raw=str(row.get("time")),
        )))
    reordered = source_dates != sorted(source_dates)
    output: list[PriceDailyRecord] = []
    for event_date, record in parsed:
        if not requested_start <= event_date <= requested_end:
            continue
        if reordered:
            record = PriceDailyRecord(**{**record.to_dict(), "trading_date": record.trading_date, "event_time_utc": record.event_time_utc, "quality_flags": sorted(set(record.quality_flags + ["reordered_source_rows"]))})
        output.append(record)
    return sorted(output, key=lambda record: record.trading_date)


class KBSAdapter:
    source_name = "kbs"

    def __init__(self, session: requests.Session | None = None, timeout: float = 30.0):
        self.session = session or requests.Session()
        self.timeout = timeout

    def fetch_listing(self) -> FetchResult:
        return FetchResult(status="unsupported", endpoint=KBS_BASE_URL)

    def fetch_daily(self, symbol: str, end_date: date, count_back: int, start_date: date | None = None) -> FetchResult:
        start = start_date or (end_date - timedelta(days=count_back * 2))
        endpoint = f"{KBS_BASE_URL}/{symbol.upper()}/data_day"
        params = {"sdate": start.strftime("%d-%m-%Y"), "edate": end_date.strftime("%d-%m-%Y")}
        started = __import__("time").perf_counter()
        try:
            response = self.session.get(endpoint, headers=KBS_HEADERS, params=params, timeout=self.timeout)
            latency = round((__import__("time").perf_counter() - started) * 1000, 1)
            try:
                payload = response.json()
            except ValueError:
                payload = None
            return FetchResult(status="ok" if response.ok else "http_error", payload=payload, response_status=response.status_code, latency_ms=latency, request_parameters=params, endpoint=endpoint)
        except requests.RequestException as exc:
            return FetchResult(status="error", response_status=None, latency_ms=round((__import__("time").perf_counter() - started) * 1000, 1), request_parameters=params, endpoint=endpoint, error_type=type(exc).__name__, error_message=str(exc))

    def parse_listing(self, payload: Any) -> list[InstrumentRecord]:
        return []

    def parse_daily(self, payload: Any, symbol: str, requested_start: date, requested_end: date) -> list[PriceDailyRecord]:
        return parse_kbs_ohlcv(payload, symbol, requested_start, requested_end, source_observation_id="unassigned")
