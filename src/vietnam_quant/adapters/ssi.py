"""SSI credential boundary; no data is fetched without explicit credentials."""

from __future__ import annotations

import os
from datetime import date, datetime
from collections.abc import Mapping
from typing import Any

from vietnam_quant.adapters.vci import normalize_exchange
from vietnam_quant.schemas import CredentialStatus, FetchResult, InstrumentRecord, PriceDailyRecord


def _field(row: Mapping[str, Any], *names: str) -> Any:
    values = {str(key).lower(): value for key, value in row.items()}
    for name in names:
        if name.lower() in values:
            return values[name.lower()]
    return None


def _as_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(str(value).replace(",", "").strip())
    except (TypeError, ValueError):
        return None


def _as_date(value: Any) -> date | None:
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    text = str(value).strip()
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00")).date()
    except ValueError:
        pass
    for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%Y%m%d"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            pass
    return None


def _rows(payload: Any) -> list[Mapping[str, Any]]:
    if isinstance(payload, list):
        return [row for row in payload if isinstance(row, Mapping)]
    if not isinstance(payload, Mapping):
        return []
    for key in ("data", "result", "rows", "items"):
        nested = payload.get(key)
        if isinstance(nested, list):
            return [row for row in nested if isinstance(row, Mapping)]
        if isinstance(nested, Mapping):
            return [nested]
    return [payload]


def parse_ssi_daily(
    payload: Any,
    symbol: str,
    requested_start: date,
    requested_end: date,
    source_observation_id: str = "unassigned",
) -> list[PriceDailyRecord]:
    """Parse SSI daily prices while retaining raw and adjusted close separately."""

    parsed: list[tuple[date, PriceDailyRecord]] = []
    source_dates: list[date] = []
    requested_symbol = symbol.upper()
    for row in _rows(payload):
        row_symbol = _field(row, "Symbol", "Ticker", "Code")
        if row_symbol and str(row_symbol).strip().upper() != requested_symbol:
            continue
        trading_date = _as_date(_field(row, "TradingDate", "Trading_Date", "Date"))
        if trading_date is None:
            continue
        source_dates.append(trading_date)
        raw_open = _as_float(_field(row, "OpenPrice", "Openprice"))
        raw_high = _as_float(_field(row, "HighestPrice", "Highestprice", "HighPrice"))
        raw_low = _as_float(_field(row, "LowestPrice", "Lowestprice", "LowPrice"))
        raw_close = _as_float(_field(row, "ClosePrice", "Closeprice"))
        adjusted_close = _as_float(
            _field(row, "ClosePriceAdjusted", "Closepriceadjusted", "AdjustedClose")
        )
        volume = _as_float(
            _field(row, "TotalMatchVol", "Totalmatchvol", "TotalTradedVol", "TotalDealVol")
        )
        _, exchange = normalize_exchange(_field(row, "Market", "Exchange", "Board"))
        parsed.append(
            (
                trading_date,
                PriceDailyRecord(
                    symbol=requested_symbol,
                    trading_date=trading_date,
                    source="ssi",
                    event_time_raw=str(_field(row, "TradingDate", "Trading_Date", "Date")),
                    exchange=exchange,
                    raw_open=raw_open,
                    raw_high=raw_high,
                    raw_low=raw_low,
                    raw_close=raw_close,
                    raw_volume=volume,
                    raw_price_unit="VND",
                    normalized_open=raw_open,
                    normalized_high=raw_high,
                    normalized_low=raw_low,
                    normalized_close=raw_close,
                    normalized_price_unit="VND",
                    adjusted_close=adjusted_close,
                    adjusted_price_unit="VND" if adjusted_close is not None else None,
                    price_semantics=(
                        "raw_and_adjusted_close" if adjusted_close is not None else "raw_only"
                    ),
                    volume_unit="shares",
                    source_observation_id=source_observation_id,
                    parser_version="ssi-daily-v1",
                ),
            )
        )

    reordered = source_dates != sorted(source_dates)
    output: list[PriceDailyRecord] = []
    for trading_date, record in parsed:
        if not requested_start <= trading_date <= requested_end:
            continue
        if reordered:
            record = PriceDailyRecord(
                **{
                    **record.to_dict(),
                    "trading_date": record.trading_date,
                    "quality_flags": sorted(set(record.quality_flags + ["reordered_source_rows"])),
                }
            )
        output.append(record)
    return sorted(output, key=lambda record: record.trading_date)


class SSIAdapter:
    source_name = "ssi"

    def check_credentials(self) -> CredentialStatus:
        if not os.environ.get("SSI_API_KEY") or not os.environ.get("SSI_SECRET"):
            return CredentialStatus(source="ssi", status="skipped_missing_credentials", detail="SSI_API_KEY and SSI_SECRET are required")
        return CredentialStatus(source="ssi", status="credentials_present")

    def fetch_listing(self) -> FetchResult:
        status = self.check_credentials()
        return FetchResult(status=status.status, endpoint="ssi://listing", error_type=None if status.status == "credentials_present" else "missing_credentials", error_message=status.detail)

    def fetch_daily(self, symbol: str, end_date: date, count_back: int) -> FetchResult:
        status = self.check_credentials()
        return FetchResult(status=status.status, endpoint="ssi://daily", error_type=None if status.status == "credentials_present" else "missing_credentials", error_message=status.detail)

    def parse_listing(self, payload: Any) -> list[InstrumentRecord]:
        return []

    def parse_daily(self, payload: Any, symbol: str, requested_start: date, requested_end: date) -> list[PriceDailyRecord]:
        return parse_ssi_daily(payload, symbol, requested_start, requested_end)


__all__ = ["SSIAdapter", "parse_ssi_daily"]
