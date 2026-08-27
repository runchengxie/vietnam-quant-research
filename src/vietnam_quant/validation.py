"""Vietnam-native cross-sectional factor validation helpers.

This module deliberately stops at signal diagnostics.  The close-to-close
forward returns, Rank IC, and quantile portfolios here do not model execution;
the execution-oriented next-available-open, turnover, liquidity, and cost
logic remains in :mod:`vietnam_quant.backtest`.
"""

from __future__ import annotations

from collections.abc import Iterable

import numpy as np
import pandas as pd


_SEVERE_FLAGS = {"missing_required", "invalid_ohlc", "duplicate_date", "zero_volume"}


def _validate_horizons(horizons: Iterable[int]) -> tuple[int, ...]:
    try:
        values = tuple(int(horizon) for horizon in horizons)
    except (TypeError, ValueError) as exc:
        raise ValueError("horizons must contain positive integers") from exc
    if not values or any(horizon <= 0 for horizon in values) or len(set(values)) != len(values):
        raise ValueError("horizons must contain unique positive integers")
    return values


def _validate_horizon(horizon: int) -> int:
    values = _validate_horizons((horizon,))
    return values[0]


def _as_bool(value: object) -> bool:
    if value is None or value is pd.NA:
        return False
    missing = pd.isna(value)
    if isinstance(missing, (bool, np.bool_)) and bool(missing):
        return False
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "t", "yes", "y"}
    return bool(value)


def _flags(value: object) -> set[str]:
    if isinstance(value, (list, tuple, set)):
        return {str(flag) for flag in value}
    if isinstance(value, str):
        return {value}
    return set()


def _eligibility_mask(frame: pd.DataFrame, close_col: str | None = None) -> pd.Series:
    mask = pd.Series(True, index=frame.index, dtype=bool)
    if "research_eligible" in frame.columns:
        mask &= frame["research_eligible"].map(_as_bool).fillna(False)
    if "tradable" in frame.columns:
        mask &= frame["tradable"].map(_as_bool).fillna(False)
    if "tradable_quality" in frame.columns:
        mask &= frame["tradable_quality"].map(_as_bool).fillna(False)
    if "quality_flags" in frame.columns:
        mask &= ~frame["quality_flags"].map(lambda value: bool(_flags(value) & _SEVERE_FLAGS))

    candidate_close = close_col
    if candidate_close is None:
        candidate_close = next(
            (column for column in ("normalized_close", "close", "adjusted_close") if column in frame.columns),
            None,
        )
    if candidate_close is not None:
        mask &= pd.to_numeric(frame[candidate_close], errors="coerce").gt(0)

    volume_col = next((column for column in ("raw_volume", "volume") if column in frame.columns), None)
    if volume_col is not None:
        mask &= pd.to_numeric(frame[volume_col], errors="coerce").gt(0)
    return mask


def _normalise_dates(frame: pd.DataFrame) -> pd.DataFrame:
    if "symbol" not in frame.columns or "trading_date" not in frame.columns:
        raise ValueError("panel requires symbol and trading_date")
    result = frame.copy()
    result["_validation_date"] = pd.to_datetime(result["trading_date"], errors="coerce").dt.normalize()
    if result["_validation_date"].isna().any():
        raise ValueError("trading_date contains an unparseable value")
    result = result.sort_values(["symbol", "_validation_date"], kind="mergesort").reset_index(drop=True)
    if result.duplicated(["symbol", "_validation_date"]).any():
        raise ValueError("panel contains duplicate symbol/trading_date rows")
    result["trading_date"] = result["_validation_date"].dt.strftime("%Y-%m-%d")
    return result


def compute_forward_returns(
    features: pd.DataFrame,
    horizons: tuple[int, ...] = (1, 5, 20),
    close_col: str = "normalized_close",
) -> pd.DataFrame:
    """Attach per-symbol close-to-close returns at trading-row horizons.

    A horizon is measured in eligible observations for each symbol, not
    calendar days. Ineligible rows are removed from the return path and remain
    missing in the output. This keeps the diagnostic panel from silently using
    suspended, zero-volume, or structurally invalid observations.
    """
    values = _validate_horizons(horizons)
    if close_col not in features.columns:
        raise ValueError(f"panel requires {close_col}")
    frame = _normalise_dates(features)
    close = pd.to_numeric(frame[close_col], errors="coerce")
    frame["_eligible"] = _eligibility_mask(frame, close_col=close_col)
    frame["_eligible_close"] = close.where(frame["_eligible"])
    for horizon in values:
        frame[f"forward_return_{horizon}d"] = np.nan
    eligible_groups = frame[frame["_eligible"]].groupby("symbol", sort=False)
    for _, eligible_group in eligible_groups:
        eligible_index = eligible_group.index
        current_close = frame.loc[eligible_index, "_eligible_close"]
        for horizon in values:
            future_close = current_close.shift(-horizon)
            frame.loc[eligible_index, f"forward_return_{horizon}d"] = future_close / current_close - 1.0
    return frame.drop(columns=["_validation_date", "_eligible", "_eligible_close"])


def _factor_panel(panel: pd.DataFrame, factor: str, horizon: int) -> pd.DataFrame:
    horizon = _validate_horizon(horizon)
    if factor not in panel.columns:
        raise ValueError(f"panel requires factor column {factor}")
    forward_col = f"forward_return_{horizon}d"
    frame = panel
    if forward_col not in frame.columns:
        frame = compute_forward_returns(frame, horizons=(horizon,))
    frame = _normalise_dates(frame)
    frame["_eligible"] = _eligibility_mask(frame)
    frame["_factor_value"] = pd.to_numeric(frame[factor], errors="coerce")
    frame["_forward_value"] = pd.to_numeric(frame[forward_col], errors="coerce")
    return frame


def compute_rank_ic(
    panel: pd.DataFrame,
    factor: str,
    horizon: int,
    min_cross_section: int = 10,
) -> pd.Series:
    """Compute cross-sectional Spearman Rank IC for every formation date."""
    if min_cross_section < 2:
        raise ValueError("min_cross_section must be at least 2")
    frame = _factor_panel(panel, factor, horizon)
    values: list[float] = []
    dates: list[pd.Timestamp] = []
    for date, group in frame.groupby("_validation_date", sort=True):
        valid = group.loc[
            group["_eligible"] & group["_factor_value"].notna() & group["_forward_value"].notna(),
            ["_factor_value", "_forward_value"],
        ]
        dates.append(date)
        if len(valid) < min_cross_section:
            values.append(np.nan)
            continue
        values.append(valid["_factor_value"].rank(method="average").corr(valid["_forward_value"].rank(method="average")))
    return pd.Series(values, index=pd.DatetimeIndex(dates, name="trading_date"), name=f"{factor}_rank_ic_{horizon}d")


def _empty_quantile_frame(n_quantiles: int) -> pd.DataFrame:
    return pd.DataFrame(
        columns=[
            "trading_date",
            *[f"quantile_{index}" for index in range(1, n_quantiles + 1)],
            "high_minus_low",
            "monotonicity",
            "cross_section",
        ]
    )


def compute_quantile_returns(
    panel: pd.DataFrame,
    factor: str,
    horizon: int,
    n_quantiles: int = 5,
    min_cross_section: int = 10,
) -> pd.DataFrame:
    """Compute equal-weight forward returns for deterministic factor quantiles."""
    if n_quantiles < 2:
        raise ValueError("n_quantiles must be at least 2")
    if min_cross_section < 2:
        raise ValueError("min_cross_section must be at least 2")
    frame = _factor_panel(panel, factor, horizon)
    output: list[dict[str, object]] = []
    for date, group in frame.groupby("_validation_date", sort=True):
        valid = group.loc[
            group["_eligible"] & group["_factor_value"].notna() & group["_forward_value"].notna(),
            ["_factor_value", "_forward_value"],
        ]
        if len(valid) < min_cross_section or len(valid) < n_quantiles:
            continue
        ranked = valid["_factor_value"].rank(method="first")
        labels = pd.qcut(ranked, q=n_quantiles, labels=False, duplicates="drop")
        row: dict[str, object] = {"trading_date": date.strftime("%Y-%m-%d"), "cross_section": len(valid)}
        quantile_values: list[float] = []
        for quantile in range(n_quantiles):
            value = valid.loc[labels == quantile, "_forward_value"].mean()
            quantile_values.append(float(value) if pd.notna(value) else np.nan)
            row[f"quantile_{quantile + 1}"] = quantile_values[-1]
        row["high_minus_low"] = quantile_values[-1] - quantile_values[0]
        q_values = pd.Series(quantile_values, dtype=float).dropna()
        row["monotonicity"] = (
            q_values.index.to_series().corr(q_values, method="spearman") if len(q_values) >= 2 else np.nan
        )
        output.append(row)
    if not output:
        return _empty_quantile_frame(n_quantiles)
    return pd.DataFrame(output)


def _mean_or_nan(values: pd.Series) -> float:
    values = pd.to_numeric(values, errors="coerce").dropna()
    return float(values.mean()) if not values.empty else np.nan


def _ratio_or_nan(numerator: float, denominator: float) -> float:
    if pd.isna(numerator) or pd.isna(denominator) or denominator == 0:
        return np.nan
    return float(numerator / denominator)


def summarize_factor_validation(
    panel: pd.DataFrame,
    factor: str,
    horizons: tuple[int, ...] = (1, 5, 20),
    n_quantiles: int = 5,
    oos_fraction: float = 0.3,
    min_cross_section: int = 10,
) -> pd.DataFrame:
    """Summarize full, chronological IS, and chronological OOS diagnostics."""
    values = _validate_horizons(horizons)
    if n_quantiles < 2:
        raise ValueError("n_quantiles must be at least 2")
    if not 0 < oos_fraction < 1:
        raise ValueError("oos_fraction must be between 0 and 1")
    if min_cross_section < 2:
        raise ValueError("min_cross_section must be at least 2")
    if factor not in panel.columns:
        raise ValueError(f"panel requires factor column {factor}")

    forward_panel = _normalise_dates(panel)
    missing_horizons = tuple(
        horizon for horizon in values if f"forward_return_{horizon}d" not in forward_panel.columns
    )
    if missing_horizons:
        generated = compute_forward_returns(forward_panel, horizons=missing_horizons)
        for horizon in missing_horizons:
            forward_panel[f"forward_return_{horizon}d"] = generated[f"forward_return_{horizon}d"]
    all_dates = pd.DatetimeIndex(pd.to_datetime(forward_panel["trading_date"], errors="coerce").sort_values().unique())
    if all_dates.empty:
        return pd.DataFrame(
            columns=[
                "factor", "horizon", "period", "valid_date_count", "rank_ic_valid_date_count",
                "mean_rank_ic", "rank_ic_ir", "rank_ic_positive_rate", "mean_high_minus_low",
                "mean_monotonicity", "mean_cross_section", "period_start", "period_end", "oos_start",
            ]
        )
    oos_index = min(len(all_dates) - 1, max(0, int(len(all_dates) * (1 - oos_fraction))))
    oos_start = all_dates[oos_index]
    rows: list[dict[str, object]] = []
    for horizon in values:
        rank_ic = compute_rank_ic(forward_panel, factor, horizon, min_cross_section=min_cross_section)
        quantiles = compute_quantile_returns(
            forward_panel,
            factor,
            horizon,
            n_quantiles=n_quantiles,
            min_cross_section=min_cross_section,
        )
        quantile_metrics = (
            quantiles.assign(_validation_date=pd.to_datetime(quantiles["trading_date"], errors="coerce"))
            .set_index("_validation_date")
            if not quantiles.empty
            else pd.DataFrame(index=pd.DatetimeIndex([], name="_validation_date"))
        )
        metrics = pd.DataFrame(index=all_dates)
        metrics["rank_ic"] = rank_ic.reindex(all_dates)
        for column in ("high_minus_low", "monotonicity", "cross_section"):
            metrics[column] = quantile_metrics[column].reindex(all_dates) if column in quantile_metrics else np.nan

        period_masks = {
            "FULL": pd.Series(True, index=all_dates),
            "IS": pd.Series(all_dates < oos_start, index=all_dates),
            "OOS": pd.Series(all_dates >= oos_start, index=all_dates),
        }
        for period, period_mask in period_masks.items():
            selected = metrics.loc[period_mask.to_numpy()]
            spread_values = selected["high_minus_low"].dropna()
            ic_values = selected["rank_ic"].dropna()
            ic_mean = _mean_or_nan(ic_values)
            ic_std = float(ic_values.std(ddof=1)) if len(ic_values) > 1 else np.nan
            valid_dates = selected.dropna(subset=["high_minus_low"]).index
            rows.append(
                {
                    "factor": factor,
                    "horizon": horizon,
                    "period": period,
                    "valid_date_count": int(len(spread_values)),
                    "rank_ic_valid_date_count": int(len(ic_values)),
                    "mean_rank_ic": ic_mean,
                    "rank_ic_ir": _ratio_or_nan(ic_mean, ic_std),
                    "rank_ic_positive_rate": float((ic_values > 0).mean()) if not ic_values.empty else np.nan,
                    "mean_high_minus_low": _mean_or_nan(spread_values),
                    "mean_monotonicity": _mean_or_nan(selected["monotonicity"]),
                    "mean_cross_section": _mean_or_nan(selected["cross_section"]),
                    "period_start": valid_dates.min().strftime("%Y-%m-%d") if len(valid_dates) else None,
                    "period_end": valid_dates.max().strftime("%Y-%m-%d") if len(valid_dates) else None,
                    "oos_start": oos_start.strftime("%Y-%m-%d"),
                }
            )
    return pd.DataFrame(rows)
