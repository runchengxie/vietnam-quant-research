"""Deterministic universe selection with explicit edge-case inclusion."""

from __future__ import annotations

from dataclasses import replace
from typing import Iterable, Mapping

from vietnam_quant.schemas import InstrumentRecord

DEFAULT_EXCHANGE_QUOTAS = {"HOSE": 30, "HNX": 10, "UPCOM": 10}


def select_sample(
    instruments: Iterable[InstrumentRecord],
    sample_size: int = 50,
    quotas: Mapping[str, int] | None = None,
    edge_symbols: Iterable[str] = (),
) -> list[InstrumentRecord]:
    """Select a stable sample without fabricating exchange history."""
    if sample_size < 0:
        raise ValueError("sample_size must be non-negative")
    quota_map = dict(DEFAULT_EXCHANGE_QUOTAS if quotas is None else quotas)
    by_symbol = {
        record.symbol.upper(): record
        for record in instruments
        if record.security_type is None
        or str(record.security_type).upper() in {"STOCK", "EQUITY"}
    }
    requested_edges = [symbol.upper() for symbol in edge_symbols]
    missing_edges = [symbol for symbol in requested_edges if symbol not in by_symbol]
    if missing_edges:
        raise ValueError(f"edge symbols not found in instrument listing: {missing_edges}")
    if len(requested_edges) > sample_size:
        raise ValueError("explicit edge symbols exceed sample_size")

    selected: list[InstrumentRecord] = []
    selected_symbols: set[str] = set()
    for symbol in requested_edges:
        if symbol in selected_symbols:
            continue
        selected.append(replace(by_symbol[symbol], selection_reason="edge_case"))
        selected_symbols.add(symbol)

    remaining_slots = sample_size - len(selected)
    candidates = sorted(
        (record for symbol, record in by_symbol.items() if symbol not in selected_symbols),
        key=lambda record: (record.exchange or "UNKNOWN", record.symbol),
    )
    for exchange in ("HOSE", "HNX", "UPCOM"):
        if remaining_slots <= 0:
            break
        exchange_rows = [record for record in candidates if record.exchange == exchange]
        for record in exchange_rows[: min(quota_map.get(exchange, 0), remaining_slots)]:
            selected.append(replace(record, selection_reason="exchange_quota"))
            selected_symbols.add(record.symbol.upper())
            remaining_slots -= 1

    if remaining_slots > 0:
        for record in candidates:
            if remaining_slots <= 0:
                break
            if record.symbol.upper() in selected_symbols:
                continue
            selected.append(replace(record, selection_reason="sample_fill"))
            selected_symbols.add(record.symbol.upper())
            remaining_slots -= 1
    return selected
