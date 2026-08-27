"""Pure parsing helpers for auditable corporate-action event metadata."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import date, datetime
from pathlib import Path
from typing import Any

from .schemas import CorporateActionEvent
from .storage import ExternalDataStore


def _first(row: Mapping[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in row:
            return row[key]
    return None


def _as_date(value: Any) -> date | None:
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    text = str(value).strip()
    for candidate in (text, text.replace("/", "-")):
        try:
            return date.fromisoformat(candidate[:10])
        except ValueError:
            pass
    for fmt in ("%d-%m-%Y", "%d/%m/%Y", "%Y%m%d"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            pass
    raise ValueError(f"unsupported corporate action date: {value!r}")


def _as_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(str(value).replace(",", "").strip())
    except (TypeError, ValueError) as exc:
        raise ValueError(f"unsupported corporate action number: {value!r}") from exc


def _records(payload: Any) -> list[Mapping[str, Any]]:
    if isinstance(payload, list):
        return [row for row in payload if isinstance(row, Mapping)]
    if not isinstance(payload, Mapping):
        raise ValueError("corporate action payload must be a list or object")
    for key in ("events", "data", "rows", "items"):
        nested = payload.get(key)
        if isinstance(nested, list):
            return [row for row in nested if isinstance(row, Mapping)]
        if isinstance(nested, Mapping):
            return [nested]
    return [payload]


def parse_corporate_action_events(payload: Any) -> list[CorporateActionEvent]:
    """Parse event metadata while retaining source kind and uncertain dates.

    This parser intentionally does not infer a missing event date or adjustment
    ratio from prices. Such inference belongs to a later, separately audited
    adjustment layer.
    """

    events: list[CorporateActionEvent] = []
    seen_ids: set[str] = set()
    for row in _records(payload):
        symbol_value = _first(row, "symbol", "ticker", "code")
        if not symbol_value:
            raise ValueError("corporate action row is missing symbol")
        event_type_value = _first(row, "event_type", "eventType", "type")
        if not event_type_value:
            raise ValueError("corporate action row is missing event_type")
        source_url_value = _first(row, "source_url", "sourceUrl", "url")
        if not source_url_value:
            raise ValueError("corporate action row is missing source_url")
        confidence_value = _first(row, "confidence")
        if not confidence_value:
            raise ValueError("corporate action row is missing confidence")

        dates = {
            "announcement_date": _as_date(_first(row, "announcement_date", "announcementDate")),
            "ex_date": _as_date(_first(row, "ex_date", "exDate")),
            "record_date": _as_date(_first(row, "record_date", "recordDate")),
            "payment_date": _as_date(_first(row, "payment_date", "paymentDate")),
            "listing_date": _as_date(_first(row, "listing_date", "listingDate")),
        }
        if not any(value is not None for value in dates.values()):
            raise ValueError("corporate action row is missing an event date")

        symbol = str(symbol_value).strip().upper()
        event_type = str(event_type_value).strip()
        source_url = str(source_url_value).strip()
        first_event_date = next(
            dates[key]
            for key in dates
            if dates[key] is not None
        )
        event_id = str(
            _first(row, "event_id", "eventId")
            or f"{symbol}:{first_event_date.isoformat()}:{event_type}:{source_url}"
        ).strip()
        if event_id in seen_ids:
            raise ValueError(f"duplicate event_id: {event_id}")
        seen_ids.add(event_id)

        events.append(
            CorporateActionEvent(
                event_id=event_id,
                symbol=symbol,
                exchange=_first(row, "exchange", "market"),
                event_type=event_type,
                source_url=source_url,
                **dates,
                cash_amount_per_share=_as_float(
                    _first(row, "cash_amount_per_share", "cashAmountPerShare", "cash_amount")
                ),
                share_ratio=_as_float(_first(row, "share_ratio", "shareRatio")),
                rights_ratio=_as_float(_first(row, "rights_ratio", "rightsRatio")),
                source_kind=str(_first(row, "source_kind", "sourceKind") or "secondary_discovery"),
                confidence=str(confidence_value),
                notes=_first(row, "notes"),
            )
        )
    return events


def write_corporate_action_events(
    store: ExternalDataStore,
    events: list[CorporateActionEvent],
    relative_path: Path | str = "metadata/corporate_action_events.jsonl",
) -> Path:
    """Append event records to the external evidence layer by stable ID."""

    return store.append_jsonl_many(
        relative_path,
        (event.to_dict() for event in events),
        key="event_id",
    )


__all__ = ["parse_corporate_action_events", "write_corporate_action_events"]
