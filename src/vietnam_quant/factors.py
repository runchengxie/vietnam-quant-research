"""Point-in-time daily factor features."""

from __future__ import annotations

import numpy as np
import pandas as pd


def _column(frame: pd.DataFrame, preferred: str, fallback: str) -> str:
    if preferred in frame.columns:
        return preferred
    if fallback in frame.columns:
        return fallback
    raise ValueError(f"price frame requires {preferred} or {fallback}")


def _flags(value: object) -> set[str]:
    if isinstance(value, (list, tuple, set)):
        return {str(flag) for flag in value}
    if isinstance(value, str):
        return {value}
    return set()


def compute_features(price_frame: pd.DataFrame) -> pd.DataFrame:
    """Compute lagged signals without using the current day's close."""
    if price_frame.empty:
        return price_frame.copy()
    if "symbol" not in price_frame.columns or "trading_date" not in price_frame.columns:
        raise ValueError("price frame requires symbol and trading_date")
    close_col = _column(price_frame, "normalized_close", "close")
    open_col = _column(price_frame, "normalized_open", "open")
    volume_col = "raw_volume" if "raw_volume" in price_frame.columns else "volume"
    if volume_col not in price_frame.columns:
        raise ValueError("price frame requires raw_volume or volume")

    frame = price_frame.copy()
    frame["_trade_date"] = pd.to_datetime(frame["trading_date"], errors="coerce")
    if frame["_trade_date"].isna().any():
        raise ValueError("trading_date contains an unparseable value")
    frame = frame.sort_values(["symbol", "_trade_date"], kind="mergesort").reset_index(drop=True)
    grouped_close = frame.groupby("symbol", sort=False)[close_col]
    grouped_volume = frame.groupby("symbol", sort=False)[volume_col]
    frame["daily_return"] = grouped_close.pct_change()

    for name, window in (("1m", 22), ("3m", 64), ("6m", 127), ("12m", 253)):
        frame[f"momentum_{name}"] = grouped_close.shift(1) / grouped_close.shift(window) - 1.0
    frame["reversal_1m"] = -frame["momentum_1m"]

    grouped_returns = frame.groupby("symbol", sort=False)["daily_return"]
    for name, window in (("1m", 21), ("3m", 63)):
        frame[f"volatility_{name}"] = grouped_returns.transform(
            lambda values: values.shift(1).rolling(window, min_periods=window).std()
        )
    frame["avg_volume_1m"] = grouped_volume.transform(
        lambda values: values.shift(1).rolling(21, min_periods=21).mean()
    )

    lagged_close = grouped_close.shift(1)
    lagged_volume = grouped_volume.shift(1)
    amihud_daily = frame["daily_return"].groupby(frame["symbol"], sort=False).shift(1).abs() / (
        lagged_close.abs() * lagged_volume.abs()
    ).clip(lower=1e-12)
    frame["amihud_1m"] = amihud_daily.groupby(frame["symbol"], sort=False).transform(
        lambda values: values.rolling(21, min_periods=21).mean()
    )
    traded_value = lagged_close.abs() * lagged_volume.abs()
    frame["avg_traded_value_proxy_1m"] = traded_value.groupby(frame["symbol"], sort=False).transform(
        lambda values: values.rolling(21, min_periods=21).mean()
    )

    if "boundary_price_proxy" not in frame.columns:
        frame["boundary_price_proxy"] = frame.get("quality_flags", pd.Series(index=frame.index)).map(
            lambda value: "boundary_price_proxy" in _flags(value)
        )
    else:
        frame["boundary_price_proxy"] = frame["boundary_price_proxy"].fillna(False).astype(bool)
    severe_flags = {"missing_required", "invalid_ohlc", "duplicate_date", "zero_volume"}
    if "quality_flags" in frame.columns:
        frame["tradable_quality"] = frame["quality_flags"].map(
            lambda value: not bool(_flags(value) & severe_flags)
        )
    else:
        frame["tradable_quality"] = True
    frame["tradable_quality"] &= frame[volume_col].fillna(0).gt(0)
    frame["tradable_quality"] &= frame[open_col].fillna(0).gt(0)
    if "market_cap" in frame.columns and frame["market_cap"].notna().any():
        frame["market_cap_status"] = "available"
    else:
        frame["market_cap_status"] = "blocked_missing_market_cap"

    frame["trading_date"] = frame["_trade_date"].dt.strftime("%Y-%m-%d")
    return frame.drop(columns=["_trade_date"])
