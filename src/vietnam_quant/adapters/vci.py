"""VCI/Vietcap daily data adapter and normalization helpers."""

from __future__ import annotations

import time
from datetime import date, datetime, time as dt_time, timedelta, timezone
from typing import Any, Iterable
from zoneinfo import ZoneInfo

import requests

from vietnam_quant.schemas import FetchResult, InstrumentRecord, PriceDailyRecord, RawPriceBar

VN_TZ = ZoneInfo("Asia/Ho_Chi_Minh")
VCI_BASE_URL = "https://trading.vietcap.com.vn/api"
VCI_LISTING_ENDPOINT = f"{VCI_BASE_URL}/price/symbols/getAll"
VCI_DAILY_ENDPOINT = f"{VCI_BASE_URL}/chart/OHLCChart/gap-chart"
VCI_HEADERS = {
    "Accept": "application/json, text/plain, */*",
    "Content-Type": "application/json",
    "Origin": "https://trading.vietcap.com.vn",
    "Referer": "https://trading.vietcap.com.vn/",
    "User-Agent": "vietnam-quant-research daily data loop",
}


def _first(mapping: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in mapping:
            return mapping[key]
    return None


def _as_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    if isinstance(value, bool):
        return float(value)
    try:
        return float(str(value).replace(",", ""))
    except (TypeError, ValueError):
        return None


def normalize_exchange(raw_value: object) -> tuple[str | None, str | None]:
    if raw_value is None:
        return None, None
    raw = str(raw_value).strip()
    if not raw:
        return raw, None
    upper = raw.upper().replace(" ", "")
    if upper in {"HSX", "HOSE"}:
        return raw, "HOSE"
    if upper == "HNX":
        return raw, "HNX"
    if upper in {"UPCOM", "UPCOM-INDEX", "UPCOMINDEX"}:
        return raw, "UPCOM"
    if upper in {"DELISTED", "DELIST", "DELISTING"}:
        return raw, "DELISTED"
    return raw, "UNKNOWN"


def _as_records(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [row for row in payload if isinstance(row, dict)]
    if not isinstance(payload, dict):
        return []
    for key in ("data", "result", "rows", "items"):
        value = payload.get(key)
        if isinstance(value, list):
            return [row for row in value if isinstance(row, dict)]
        if isinstance(value, dict):
            return [value]
    return [payload]


def _ohlcv_records(payload: Any, preferred_keys: tuple[str, ...] = ()) -> list[dict[str, Any]]:
    container: Any = payload
    if isinstance(payload, dict):
        for key in preferred_keys + ("data", "result", "rows", "items"):
            if isinstance(payload.get(key), (list, dict)):
                container = payload[key]
                break
    if isinstance(container, dict):
        records = [container]
    elif isinstance(container, list):
        records = [row for row in container if isinstance(row, dict)]
    else:
        return []
    if not records:
        return []
    first = records[0]
    time_value = _first(first, "t", "time", "timestamp", "date", "tradingDate", "trading_date")
    value_keys = ("o", "open"), ("h", "high"), ("l", "low"), ("c", "close"), ("v", "volume", "vol")
    if isinstance(time_value, list) and all(isinstance(_first(first, *keys), list) for keys in value_keys):
        arrays = [time_value] + [_first(first, *keys) for keys in value_keys]
        count = min(len(values) for values in arrays)
        return [
            {
                "time": arrays[0][index],
                "open": arrays[1][index],
                "high": arrays[2][index],
                "low": arrays[3][index],
                "close": arrays[4][index],
                "volume": arrays[5][index],
            }
            for index in range(count)
        ]
    rows: list[dict[str, Any]] = []
    for record in records:
        rows.append({
            "time": _first(record, "t", "time", "timestamp", "date", "tradingDate", "trading_date"),
            "open": _first(record, "o", "open"),
            "high": _first(record, "h", "high"),
            "low": _first(record, "l", "low"),
            "close": _first(record, "c", "close"),
            "volume": _first(record, "v", "volume", "vol"),
        })
    return rows


def _parse_event_time(value: Any) -> tuple[date | None, datetime | None]:
    if value is None:
        return None, None
    if isinstance(value, datetime):
        dt = value if value.tzinfo else value.replace(tzinfo=VN_TZ)
        return dt.astimezone(VN_TZ).date(), dt.astimezone(timezone.utc)
    if isinstance(value, date):
        dt = datetime.combine(value, dt_time.min, tzinfo=VN_TZ)
        return value, dt.astimezone(timezone.utc)
    if isinstance(value, (int, float)) or str(value).strip().isdigit():
        try:
            numeric = float(value)
            if numeric > 10_000_000_000:
                numeric /= 1000
            dt = datetime.fromtimestamp(numeric, tz=timezone.utc)
            return dt.astimezone(VN_TZ).date(), dt
        except (ValueError, OverflowError, OSError):
            return None, None
    text = str(value).strip()
    for candidate in (text, text.replace("/", "-")):
        try:
            parsed = datetime.fromisoformat(candidate.replace("Z", "+00:00"))
            dt = parsed if parsed.tzinfo else parsed.replace(tzinfo=VN_TZ)
            return dt.astimezone(VN_TZ).date(), dt.astimezone(timezone.utc)
        except ValueError:
            pass
    for fmt in ("%d-%m-%Y", "%d/%m/%Y", "%Y%m%d"):
        try:
            parsed = datetime.strptime(text, fmt).replace(tzinfo=VN_TZ)
            return parsed.date(), parsed.astimezone(timezone.utc)
        except ValueError:
            pass
    return None, None


def _record_from_values(
    row: dict[str, Any],
    *,
    symbol: str,
    source: str,
    exchange: str | None,
    parser_version: str,
    source_observation_id: str,
    event_date: date,
    event_time_utc: datetime | None,
    event_time_raw: str,
    reordered: bool = False,
) -> PriceDailyRecord:
    raw_open = _as_float(row.get("open"))
    raw_high = _as_float(row.get("high"))
    raw_low = _as_float(row.get("low"))
    raw_close = _as_float(row.get("close"))
    raw_volume = _as_float(row.get("volume"))
    flags: list[str] = []
    if reordered:
        flags.append("reordered_source_rows")
    return PriceDailyRecord(
        symbol=symbol,
        trading_date=event_date,
        source=source,
        event_time_raw=event_time_raw,
        event_time_utc=event_time_utc,
        exchange=exchange,
        raw_open=raw_open,
        raw_high=raw_high,
        raw_low=raw_low,
        raw_close=raw_close,
        raw_volume=raw_volume,
        raw_price_unit="VND",
        normalized_open=raw_open,
        normalized_high=raw_high,
        normalized_low=raw_low,
        normalized_close=raw_close,
        normalized_price_unit="VND",
        volume_unit="shares_or_source_units",
        quality_flags=flags,
        source_observation_id=source_observation_id,
        parser_version=parser_version,
    )


def parse_vci_listing(
    payload: object,
    retrieved_at_utc: datetime | None = None,
) -> list[InstrumentRecord]:
    retrieved_at_utc = retrieved_at_utc or datetime.now(timezone.utc)
    records: list[InstrumentRecord] = []
    for row in _as_records(payload):
        symbol_value = _first(row, "symbol", "code", "ticker")
        if not symbol_value:
            continue
        symbol = str(symbol_value).strip().upper()
        exchange_raw, exchange = normalize_exchange(_first(row, "board", "exchange", "group"))
        status = "observed_delisted" if exchange == "DELISTED" else "observed_current"
        records.append(InstrumentRecord(
            instrument_id=f"vci:{symbol}",
            symbol=symbol,
            issuer_name=_first(row, "companyName", "company_name", "name"),
            exchange_raw=exchange_raw,
            exchange=exchange,
            security_type=_first(row, "type", "security_type"),
            listing_status=status,
            selection_reason=None,
            source="vci",
            retrieved_at_utc=retrieved_at_utc,
        ))
    return records


def normalize_price_bars(rows: Iterable[RawPriceBar | PriceDailyRecord]) -> list[PriceDailyRecord]:
    normalized: list[PriceDailyRecord] = []
    for row in rows:
        if isinstance(row, PriceDailyRecord):
            if row.normalized_close is not None:
                normalized.append(row)
                continue
            normalized.append(PriceDailyRecord(
                **{**row.to_dict(),
                   "trading_date": row.trading_date, "event_time_utc": row.event_time_utc,
                   "quality_flags": list(row.quality_flags),
                   "raw_price_unit": "VND",
                   "normalized_open": row.raw_open,
                   "normalized_high": row.raw_high,
                   "normalized_low": row.raw_low,
                   "normalized_close": row.raw_close}))
            continue
        normalized.append(_record_from_values(
            {"open": row.raw_open, "high": row.raw_high, "low": row.raw_low, "close": row.raw_close, "volume": row.raw_volume},
            symbol=row.symbol, source=row.source, exchange=row.exchange, parser_version="normalized-v1",
            source_observation_id="", event_date=row.trading_date, event_time_utc=row.event_time_utc,
            event_time_raw=row.event_time_raw))
    return normalized


def parse_vci_ohlcv(
    payload: object,
    symbol: str,
    requested_start: date,
    requested_end: date,
    source_observation_id: str,
    exchange: str | None = None,
) -> list[PriceDailyRecord]:
    raw_rows = _ohlcv_records(payload)
    parsed: list[tuple[date, PriceDailyRecord]] = []
    dates: list[date] = []
    for row in raw_rows:
        event_date, event_time_utc = _parse_event_time(row.get("time"))
        if event_date is None:
            continue
        dates.append(event_date)
        parsed.append((event_date, _record_from_values(
            row, symbol=symbol.upper(), source="vci", exchange=exchange,
            parser_version="vci-ohlcv-v2", source_observation_id=source_observation_id,
            event_date=event_date, event_time_utc=event_time_utc, event_time_raw=str(row.get("time")),
        )))
    reordered = dates != sorted(dates)
    filtered = [
        record if not reordered else PriceDailyRecord(**{**record.to_dict(),
            "trading_date": record.trading_date, "event_time_utc": record.event_time_utc,
            "quality_flags": sorted(set(record.quality_flags + ["reordered_source_rows"]))})
        for event_date, record in parsed
        if requested_start <= event_date <= requested_end
    ]
    return sorted(filtered, key=lambda record: record.trading_date)


class VCIAdapter:
    source_name = "vci"

    def __init__(self, session: requests.Session | None = None, timeout: float = 30.0):
        self.session = session or requests.Session()
        self.timeout = timeout

    def fetch_listing(self) -> FetchResult:
        return self._request("GET", VCI_LISTING_ENDPOINT)

    def fetch_daily(
        self, symbol: str, end_date: date, count_back: int, start_date: date | None = None
    ) -> FetchResult:
        end_exclusive = datetime.combine(end_date + timedelta(days=1), dt_time.min, tzinfo=VN_TZ)
        payload = {"timeFrame": "ONE_DAY", "symbols": [symbol.upper()], "to": int(end_exclusive.timestamp()), "countBack": count_back}
        return self._request("POST", VCI_DAILY_ENDPOINT, json=payload)

    def parse_listing(self, payload: Any) -> list[InstrumentRecord]:
        return parse_vci_listing(payload)

    def parse_daily(self, payload: Any, symbol: str, requested_start: date, requested_end: date) -> list[PriceDailyRecord]:
        return parse_vci_ohlcv(payload, symbol, requested_start, requested_end, source_observation_id="unassigned")

    def _request(self, method: str, endpoint: str, **kwargs: Any) -> FetchResult:
        started = time.perf_counter()
        params = kwargs.get("json") or kwargs.get("params") or {}
        try:
            response = self.session.request(method, endpoint, headers=VCI_HEADERS, timeout=self.timeout, **kwargs)
            latency = round((time.perf_counter() - started) * 1000, 1)
            try:
                payload = response.json()
            except ValueError:
                payload = None
            return FetchResult(status="ok" if response.ok else "http_error", payload=payload, response_status=response.status_code, latency_ms=latency, request_parameters=params, endpoint=endpoint)
        except requests.RequestException as exc:
            return FetchResult(status="error", response_status=None, latency_ms=round((time.perf_counter() - started) * 1000, 1), request_parameters=params, endpoint=endpoint, error_type=type(exc).__name__, error_message=str(exc))
