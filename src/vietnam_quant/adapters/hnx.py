"""Offline parser for HNX UPCoM displayed price anchors."""

from __future__ import annotations

import re
import unicodedata
from datetime import date
from html.parser import HTMLParser
from typing import Any

from vietnam_quant.schemas import PriceSemanticAnchor

HNX_UPCOM_PRICE_ENDPOINT = (
    "https://www.gov.hnx.vn/ModuleReportStockETFs/Report_MD_PriceVolatilyti/"
    "ListData_UPCoM"
)


class _TableParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.rows: list[list[str]] = []
        self._row: list[str] | None = None
        self._cell: list[str] | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        del attrs
        tag = tag.lower()
        if tag == "tr":
            self._row = []
        elif tag in {"th", "td"} and self._row is not None:
            self._cell = []

    def handle_data(self, data: str) -> None:
        if self._cell is not None:
            self._cell.append(data)

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag in {"th", "td"} and self._cell is not None and self._row is not None:
            self._row.append(" ".join("".join(self._cell).split()))
            self._cell = None
        elif tag == "tr" and self._row is not None:
            if self._row:
                self.rows.append(self._row)
            self._row = None


def _header_key(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value).replace("đ", "d").replace("Đ", "D")
    without_marks = "".join(char for char in normalized if not unicodedata.combining(char))
    return re.sub(r"[^a-z0-9]", "", without_marks.lower())


def _as_number(value: str) -> float | None:
    text = value.strip().replace(" ", "")
    if not text or text in {"-", "--", "n/a", "N/A"}:
        return None
    if "," in text and "." in text:
        text = text.replace(".", "").replace(",", ".")
    elif text.count(".") > 1 or ("." in text and len(text.rsplit(".", 1)[1]) == 3):
        text = text.replace(".", "")
    elif "," in text and len(text.rsplit(",", 1)[1]) == 3:
        text = text.replace(",", "")
    else:
        text = text.replace(",", ".")
    try:
        return float(text)
    except ValueError as exc:
        raise ValueError(f"unsupported HNX price value: {value!r}") from exc


def _column_index(headers: list[str], *aliases: str) -> int | None:
    normalized = [_header_key(header) for header in headers]
    for index, header in enumerate(normalized):
        if any(alias in header for alias in aliases):
            return index
    return None


def parse_hnx_upcom_price_anchor(
    html: str,
    *,
    symbol: str,
    trading_date: date,
    source_observation_id: str = "",
) -> PriceSemanticAnchor:
    """Parse one HNX UPCoM table row as independently sourced raw VND data."""

    parser = _TableParser()
    parser.feed(html)
    if not parser.rows:
        raise ValueError("HNX price table is empty")

    header_position = next(
        (
            position
            for position, row in enumerate(parser.rows)
            if _column_index(row, "dongcua", "close") is not None
        ),
        None,
    )
    if header_position is None:
        raise ValueError("HNX price table is missing close header")
    headers = parser.rows[header_position]
    indexes = {
        "symbol": _column_index(headers, "mack", "symbol", "code"),
        "open": _column_index(headers, "mocua", "open"),
        "close": _column_index(headers, "dongcua", "close"),
        "high": _column_index(headers, "caonhat", "high"),
        "low": _column_index(headers, "thapnhat", "low"),
    }
    if indexes["symbol"] is None:
        raise ValueError("HNX price table is missing symbol column")
    close_index = indexes["close"]
    if close_index is None:
        raise ValueError("HNX price table is missing close column")

    target = symbol.upper()
    data_rows = parser.rows[header_position + 1 :]
    selected: list[str] | None = None
    for row in data_rows:
        symbol_index = indexes["symbol"]
        if symbol_index < len(row) and row[symbol_index].strip().upper() == target:
            selected = row
            break
    if selected is None:
        raise ValueError(f"HNX price table has no row for symbol {target}")

    def value(name: str) -> float | None:
        index = indexes[name]
        if index is None or index >= len(selected):
            return None
        return _as_number(selected[index])

    raw_close = value("close")
    if raw_close is None:
        raise ValueError(f"HNX price table has no close price for symbol {target}")
    return PriceSemanticAnchor(
        anchor_id=f"hnx:{target}:{trading_date.isoformat()}",
        symbol=target,
        exchange="UPCoM",
        trading_date=trading_date,
        source="hnx",
        source_endpoint=HNX_UPCOM_PRICE_ENDPOINT,
        raw_open=value("open"),
        raw_high=value("high"),
        raw_low=value("low"),
        raw_close=raw_close,
        raw_price_unit="VND",
        semantic_label="exchange_raw",
        confidence="high",
        source_observation_id=source_observation_id,
    )


__all__ = ["HNX_UPCOM_PRICE_ENDPOINT", "parse_hnx_upcom_price_anchor"]
