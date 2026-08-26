"""Probe a public VCI/Vietcap endpoint without storing market data in Git.

This is an availability and schema smoke test, not a production downloader.
It records only metadata and quality counts under ``artifacts/``.
"""

from __future__ import annotations

import json
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import requests


REPO_ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = REPO_ROOT / "artifacts"
BASE_URL = "https://trading.vietcap.com.vn/api"
HEADERS = {
    "Accept": "application/json, text/plain, */*",
    "Content-Type": "application/json",
    "Origin": "https://trading.vietcap.com.vn",
    "Referer": "https://trading.vietcap.com.vn/",
    "User-Agent": "Mozilla/5.0 (research availability probe)",
}


def get_json(session: requests.Session, method: str, url: str, **kwargs: Any) -> tuple[int, Any, float]:
    started = time.perf_counter()
    response = session.request(method, url, timeout=30, **kwargs)
    elapsed_ms = round((time.perf_counter() - started) * 1000, 1)
    try:
        payload = response.json()
    except ValueError:
        payload = None
    return response.status_code, payload, elapsed_ms


def as_records(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [row for row in payload if isinstance(row, dict)]
    if isinstance(payload, dict):
        data = payload.get("data")
        if isinstance(data, list):
            return [row for row in data if isinstance(row, dict)]
        if isinstance(data, dict):
            return [data]
        return [payload]
    return []


def symbol_rows(payload: Any) -> list[dict[str, Any]]:
    rows = as_records(payload)
    return [
        {
            "symbol": row.get("symbol") or row.get("code"),
            "exchange": {
                "HSX": "HOSE",
                "HOSE": "HOSE",
                "HNX": "HNX",
                "UPCOM": "UPCOM",
            }.get(
                str(row.get("board") or row.get("exchange") or row.get("group") or "").upper(),
                row.get("board") or row.get("exchange") or row.get("group"),
            ),
            "type": row.get("type") or row.get("security_type"),
        }
        for row in rows
        if row.get("symbol") or row.get("code")
    ]


def extract_ohlcv(payload: Any) -> list[dict[str, Any]]:
    """Normalize the array-shaped OHLC response into rows for quality checks."""
    rows = as_records(payload)
    if not rows:
        return []
    first = rows[0]
    if all(isinstance(first.get(key), list) for key in ("t", "o", "h", "l", "c", "v")):
        lengths = [len(first[key]) for key in ("t", "o", "h", "l", "c", "v")]
        count = min(lengths)
        return [
            {
                "time": first["t"][i],
                "open": first["o"][i],
                "high": first["h"][i],
                "low": first["l"][i],
                "close": first["c"][i],
                "volume": first["v"][i],
            }
            for i in range(count)
        ]
    return [
        {
            "time": row.get("t") or row.get("time"),
            "open": row.get("o") or row.get("open"),
            "high": row.get("h") or row.get("high"),
            "low": row.get("l") or row.get("low"),
            "close": row.get("c") or row.get("close"),
            "volume": row.get("v") or row.get("volume"),
        }
        for row in rows
    ]


def extract_kbs_ohlcv(payload: Any) -> list[dict[str, Any]]:
    if not isinstance(payload, dict):
        return []
    for key in ("data_day", "data_1D", "data_1d"):
        if isinstance(payload.get(key), list):
            return extract_ohlcv(payload[key])
    return extract_ohlcv(payload.get("data"))


def time_key(value: Any) -> str | None:
    if value is None:
        return None
    try:
        if isinstance(value, (int, float)) or str(value).isdigit():
            return datetime.fromtimestamp(int(value), tz=timezone.utc).date().isoformat()
    except (ValueError, OverflowError, OSError):
        pass
    text = str(value)
    return text[:10] if len(text) >= 10 else text


def quality_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    required = ("time", "open", "high", "low", "close", "volume")
    missing_cells = sum(1 for row in rows for key in required if row.get(key) is None)
    timestamps = [row.get("time") for row in rows]
    numeric_rows = [row for row in rows if all(isinstance(row.get(key), (int, float)) for key in required[1:])]
    invalid_ohlc = sum(
        1
        for row in numeric_rows
        if row["high"] < max(row["open"], row["close"])
        or row["low"] > min(row["open"], row["close"])
        or row["low"] < 0
        or row["volume"] < 0
    )
    return {
        "row_count": len(rows),
        "missing_required_cells": missing_cells,
        "duplicate_timestamps": len(timestamps) - len(set(timestamps)),
        "invalid_ohlc_rows": invalid_ohlc,
        "first_time": timestamps[0] if timestamps else None,
        "last_time": timestamps[-1] if timestamps else None,
        "sorted_non_decreasing": timestamps == sorted(timestamps) if timestamps else True,
    }


def main() -> int:
    start = datetime(2024, 1, 1)
    end = datetime(2024, 1, 31) + timedelta(days=1)
    payload = {
        "timeFrame": "ONE_DAY",
        "symbols": [],
        "to": int(end.timestamp()),
        "countBack": 1000,
    }
    result: dict[str, Any] = {
        "retrieved_at_utc": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "endpoint": BASE_URL,
        "test_window": {"start": start.date().isoformat(), "end": "2024-01-31"},
        "listing": {},
        "ohlcv": {},
    }

    with requests.Session() as session:
        status, listing_payload, elapsed_ms = get_json(
            session, "GET", f"{BASE_URL}/price/symbols/getAll", headers=HEADERS
        )
        listing = symbol_rows(listing_payload)
        result["listing"] = {
            "status_code": status,
            "latency_ms": elapsed_ms,
            "row_count": len(listing),
            "sample_by_exchange": {},
        }
        grouped: dict[str, list[str]] = {}
        for row in listing:
            exchange = str(row.get("exchange") or "UNKNOWN").upper()
            symbol = str(row.get("symbol") or "").upper()
            if symbol and row.get("type", "STOCK") in ("STOCK", None):
                grouped.setdefault(exchange, []).append(symbol)
        for exchange, symbols in sorted(grouped.items()):
            result["listing"]["sample_by_exchange"][exchange] = sorted(set(symbols))[:5]

        # Use a small deterministic cross-exchange sample if the listing endpoint responds.
        samples = []
        for exchange in ("HOSE", "HNX", "UPCOM"):
            samples.extend(result["listing"]["sample_by_exchange"].get(exchange, [])[:2])
        if not samples:
            samples = ["FPT", "VCB", "PVS", "VEA"]

        for symbol in samples:
            request_payload = dict(payload)
            request_payload["symbols"] = [symbol]
            status, ohlcv_payload, elapsed_ms = get_json(
                session,
                "POST",
                f"{BASE_URL}/chart/OHLCChart/gap-chart",
                headers=HEADERS,
                json=request_payload,
            )
            rows = extract_ohlcv(ohlcv_payload)
            result["ohlcv"][symbol] = {
                "status_code": status,
                "latency_ms": elapsed_ms,
                "quality": quality_summary(rows),
                "response_type": type(ohlcv_payload).__name__,
            }

        # Compare the same small sample against the current public KBS history endpoint.
        result["cross_source"] = {}
        for symbol in ("FPT",):
            sdate = start.strftime("%d-%m-%Y")
            edate = (end - timedelta(days=1)).strftime("%d-%m-%Y")
            url = f"https://kbbuddywts.kbsec.com.vn/iis-server/investment/stocks/{symbol}/data_day"
            status, kbs_payload, elapsed_ms = get_json(
                session,
                "GET",
                url,
                headers={**HEADERS, "x-lang": "vi"},
                params={"sdate": sdate, "edate": edate},
            )
            kbs_rows = extract_kbs_ohlcv(kbs_payload)
            vci_status, vci_payload, _ = get_json(
                    session,
                    "POST",
                    f"{BASE_URL}/chart/OHLCChart/gap-chart",
                    headers=HEADERS,
                    json={
                        "timeFrame": "ONE_DAY",
                        "symbols": [symbol],
                        "to": int(end.timestamp()),
                        "countBack": 1000,
                    },
                )
            vci_rows = extract_ohlcv(vci_payload)
            vci_by_date = {time_key(row.get("time")): row for row in vci_rows}
            kbs_by_date = {time_key(row.get("time")): row for row in kbs_rows}
            matched = sorted(set(vci_by_date) & set(kbs_by_date) - {None})
            close_diffs = []
            close_diffs_scaled = []
            close_diffs_pct = []
            for day in matched:
                vci_close = vci_by_date[day].get("close")
                kbs_close = kbs_by_date[day].get("close")
                if isinstance(vci_close, (int, float)) and isinstance(kbs_close, (int, float)):
                    close_diffs.append(round(abs(float(vci_close) - float(kbs_close)), 6))
                    # Both public endpoints expose stock prices in thousand-VND raw units;
                    # vnstock's KBS adapter divides the normalized result by 1000.
                    vci_close_scaled = float(vci_close) / 1000
                    kbs_close_scaled = float(kbs_close) / 1000
                    scaled_diff = abs(vci_close_scaled - kbs_close_scaled)
                    close_diffs_scaled.append(round(scaled_diff, 6))
                    close_diffs_pct.append(
                        round(
                            scaled_diff
                            / max(abs(vci_close_scaled), abs(kbs_close_scaled), 1e-9),
                            6,
                        )
                    )
            result["cross_source"][symbol] = {
                "vci": {"status_code": vci_status, "row_count": len(vci_rows)},
                "kbs": {
                    "status_code": status,
                    "latency_ms": elapsed_ms,
                    "row_count": len(kbs_rows),
                    "quality": quality_summary(kbs_rows),
                },
                "matched_trading_dates": len(matched),
                "max_abs_close_difference_raw_units": max(close_diffs) if close_diffs else None,
                "max_abs_close_difference_after_both_price_div_1000": max(close_diffs_scaled)
                if close_diffs_scaled
                else None,
                "max_relative_close_difference_after_scaling": max(close_diffs_pct)
                if close_diffs_pct
                else None,
            }

    ARTIFACTS.mkdir(exist_ok=True)
    (ARTIFACTS / "public_ohlcv_probe.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
