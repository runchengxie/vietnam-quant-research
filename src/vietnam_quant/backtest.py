"""Cost-aware monthly factor portfolios with a chronological OOS split."""

from __future__ import annotations

from dataclasses import dataclass
import re

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class BacktestConfig:
    n_quantiles: int = 5
    cost_bps: tuple[int, ...] = (0, 50, 100)
    liquidity_quantile: float = 0.2
    oos_fraction: float = 0.3
    exclude_boundary_proxy: bool = False

    def __post_init__(self):
        if self.n_quantiles < 2:
            raise ValueError("n_quantiles must be at least 2")
        if not 0 < self.liquidity_quantile < 1:
            raise ValueError("liquidity_quantile must be between 0 and 1")
        if not 0 < self.oos_fraction < 1:
            raise ValueError("oos_fraction must be between 0 and 1")
        if any(cost < 0 for cost in self.cost_bps):
            raise ValueError("cost_bps cannot be negative")


def _flag_set(value: object) -> set[str]:
    if isinstance(value, (list, tuple, set)):
        return {str(item) for item in value}
    if isinstance(value, str):
        return {value}
    return set()


def _net_column(cost_bps: int) -> str:
    return f"net_return_cost_{int(cost_bps)}bp"


def _empty_period_frame() -> pd.DataFrame:
    return pd.DataFrame(columns=[
        "factor", "formation_date", "execution_date", "period", "status",
        "universe_count", "long_count", "short_count", "gross_return", "turnover",
        "excluded_for_quality", "excluded_for_liquidity", "excluded_for_non_tradable",
    ])


def run_factor_backtest(features: pd.DataFrame, factor: str, config: BacktestConfig) -> pd.DataFrame:
    """Form monthly portfolios and execute them on the next available day."""
    if factor not in features.columns:
        raise ValueError(f"factor column not found: {factor}")
    if features.empty:
        result = _empty_period_frame()
        result.attrs["status"] = "insufficient_coverage"
        return result
    frame = features.copy()
    frame["_date"] = pd.to_datetime(frame["trading_date"], errors="coerce")
    if frame["_date"].isna().any():
        raise ValueError("features contain an unparseable trading_date")
    frame = frame.sort_values(["_date", "symbol"], kind="mergesort").reset_index(drop=True)
    dates = sorted(frame["_date"].drop_duplicates())
    monthly = frame.assign(_month=frame["_date"].dt.to_period("M"))
    formations = monthly.groupby("_month")["_date"].max().sort_values().tolist()
    if len(formations) < 2:
        result = _empty_period_frame()
        result.attrs["status"] = "insufficient_coverage"
        return result
    oos_index = min(len(formations) - 1, max(0, int(len(formations) * (1 - config.oos_fraction))))
    oos_start = formations[oos_index]
    previous_weights: dict[str, float] = {}
    output: list[dict[str, object]] = []
    severe_flags = {"missing_required", "invalid_ohlc", "duplicate_date", "zero_volume"}
    for formation_index, formation_date in enumerate(formations[:-1]):
        future_dates = [day for day in dates if day > formation_date]
        next_formation_date = formations[formation_index + 1]
        next_execution_dates = [day for day in dates if day > next_formation_date]
        if not future_dates or not next_execution_dates:
            continue
        execution_date = future_dates[0]
        exit_date = next_execution_dates[0]
        cross = frame[frame["_date"] == formation_date].copy()
        factor_valid = cross[factor].notna()
        if "tradable_quality" in cross.columns:
            quality_valid = cross["tradable_quality"].fillna(False).astype(bool)
        else:
            quality_valid = pd.Series(True, index=cross.index)
        if "quality_flags" in cross.columns:
            quality_valid &= ~cross["quality_flags"].map(lambda value: bool(_flag_set(value) & severe_flags))
        excluded_for_quality = int((factor_valid & ~quality_valid).sum())
        candidate = cross[factor_valid & quality_valid].copy()
        if config.exclude_boundary_proxy and "boundary_price_proxy" in candidate.columns:
            candidate = candidate[~candidate["boundary_price_proxy"].fillna(False).astype(bool)]
        if "raw_volume" in candidate.columns:
            candidate["_volume"] = pd.to_numeric(candidate["raw_volume"], errors="coerce")
        elif "volume" in candidate.columns:
            candidate["_volume"] = pd.to_numeric(candidate["volume"], errors="coerce")
        else:
            candidate["_volume"] = np.nan
        open_column = "normalized_open" if "normalized_open" in candidate.columns else "open"
        close_column = "normalized_close" if "normalized_close" in candidate.columns else "close"
        candidate["_open"] = pd.to_numeric(candidate[open_column], errors="coerce")
        candidate["_close"] = pd.to_numeric(candidate[close_column], errors="coerce")
        non_tradable_mask = (
            candidate["_open"].isna() | candidate["_open"].le(0)
            | candidate["_volume"].isna() | candidate["_volume"].le(0)
        )
        excluded_for_non_tradable = int(non_tradable_mask.sum())
        candidate = candidate[~non_tradable_mask].copy()
        if "avg_traded_value_proxy_1m" in candidate.columns:
            candidate["_liquidity"] = pd.to_numeric(candidate["avg_traded_value_proxy_1m"], errors="coerce")
        else:
            candidate["_liquidity"] = candidate["_close"] * candidate["_volume"]
        candidate = candidate[candidate["_liquidity"].notna()].copy()
        liquidity_rank = candidate["_liquidity"].rank(method="first", pct=True)
        liquidity_excluded = int((liquidity_rank <= config.liquidity_quantile).sum())
        candidate = candidate[liquidity_rank > config.liquidity_quantile].copy()
        if len(candidate) < 10:
            continue
        ranks = candidate[factor].rank(method="first")
        candidate["_quantile"] = pd.qcut(ranks, q=config.n_quantiles, labels=False, duplicates="drop")
        if candidate["_quantile"].isna().any():
            continue
        low_group = int(candidate["_quantile"].min())
        high_group = int(candidate["_quantile"].max())
        long_symbols = set(candidate.loc[candidate["_quantile"] == high_group, "symbol"])
        short_symbols = set(candidate.loc[candidate["_quantile"] == low_group, "symbol"])
        entry = frame[frame["_date"] == execution_date].set_index("symbol")
        exit_rows = frame[frame["_date"] == exit_date].set_index("symbol")

        def open_value(rows: pd.DataFrame, symbol: str) -> float | None:
            if symbol not in rows.index:
                return None
            value = pd.to_numeric(rows.loc[symbol, open_column], errors="coerce")
            if isinstance(value, pd.Series):
                value = value.iloc[0]
            return float(value) if pd.notna(value) and float(value) > 0 else None

        tradable_long: dict[str, float] = {}
        tradable_short: dict[str, float] = {}
        execution_exclusions = 0
        for symbol in long_symbols | short_symbols:
            entry_open = open_value(entry, symbol)
            exit_open = open_value(exit_rows, symbol)
            if entry_open is None or exit_open is None:
                execution_exclusions += 1
                continue
            entry_return = exit_open / entry_open - 1.0
            if symbol in long_symbols:
                tradable_long[symbol] = entry_return
            if symbol in short_symbols:
                tradable_short[symbol] = entry_return
        if not tradable_long or not tradable_short:
            continue
        gross_return = float(np.mean(list(tradable_long.values())) - np.mean(list(tradable_short.values())))
        target_weights = {
            **{symbol: 0.5 / len(tradable_long) for symbol in tradable_long},
            **{symbol: -0.5 / len(tradable_short) for symbol in tradable_short},
        }
        turnover = 0.5 * sum(
            abs(target_weights.get(symbol, 0.0) - previous_weights.get(symbol, 0.0))
            for symbol in set(target_weights) | set(previous_weights)
        )
        previous_weights = target_weights
        row: dict[str, object] = {
            "factor": factor,
            "formation_date": formation_date.strftime("%Y-%m-%d"),
            "execution_date": execution_date.strftime("%Y-%m-%d"),
            "period": "OOS" if formation_date >= oos_start else "IS",
            "status": "ok",
            "universe_count": len(candidate),
            "long_count": len(tradable_long),
            "short_count": len(tradable_short),
            "gross_return": gross_return,
            "turnover": turnover,
            "excluded_for_quality": excluded_for_quality,
            "excluded_for_liquidity": liquidity_excluded,
            "excluded_for_non_tradable": excluded_for_non_tradable + execution_exclusions,
        }
        for cost in config.cost_bps:
            row[_net_column(cost)] = gross_return - (cost / 10000.0) * turnover
        output.append(row)
    result = pd.DataFrame(output)
    if result.empty:
        result = _empty_period_frame()
        result.attrs["status"] = "insufficient_coverage"
    return result


def _metric_row(frame: pd.DataFrame, factor: str, period: str, cost: int) -> dict[str, object]:
    net_column = _net_column(cost)
    if frame.empty or net_column not in frame:
        return {
            "factor": factor, "period": period, "cost_bps": cost, "status": "insufficient_coverage",
            "cumulative_return": np.nan, "annualized_return": np.nan, "volatility": np.nan,
            "max_drawdown": np.nan, "sharpe_proxy": np.nan, "average_turnover": np.nan,
            "valid_formation_count": 0, "missing_ratio": np.nan,
        }
    returns = pd.to_numeric(frame[net_column], errors="coerce").dropna()
    if returns.empty:
        return {
            "factor": factor, "period": period, "cost_bps": cost, "status": "insufficient_coverage",
            "cumulative_return": np.nan, "annualized_return": np.nan, "volatility": np.nan,
            "max_drawdown": np.nan, "sharpe_proxy": np.nan, "average_turnover": np.nan,
            "valid_formation_count": 0, "missing_ratio": np.nan,
        }
    cumulative_path = (1.0 + returns).cumprod()
    cumulative_return = float(cumulative_path.iloc[-1] - 1.0)
    annualized_return = float(cumulative_path.iloc[-1] ** (252.0 / len(returns)) - 1.0)
    volatility = float(returns.std(ddof=1) * np.sqrt(252)) if len(returns) > 1 else np.nan
    drawdown = cumulative_path / cumulative_path.cummax() - 1.0
    standard_deviation = returns.std(ddof=1)
    sharpe = (
        float(returns.mean() / standard_deviation * np.sqrt(252))
        if len(returns) > 1 and standard_deviation > 0 else np.nan
    )
    total_excluded = frame[[
        "excluded_for_quality", "excluded_for_liquidity", "excluded_for_non_tradable"
    ]].sum(axis=1).sum()
    denominator = total_excluded + frame["universe_count"].sum()
    return {
        "factor": factor, "period": period, "cost_bps": cost, "status": "ok",
        "cumulative_return": cumulative_return, "annualized_return": annualized_return,
        "volatility": volatility, "max_drawdown": float(drawdown.min()), "sharpe_proxy": sharpe,
        "average_turnover": float(frame["turnover"].mean()), "valid_formation_count": int(len(returns)),
        "missing_ratio": float(total_excluded / denominator) if denominator else np.nan,
    }


def summarize_backtest(period_returns: pd.DataFrame, oos_fraction: float) -> pd.DataFrame:
    """Summarize IS, OOS, and full-sample performance for each cost scenario."""
    del oos_fraction
    factors = sorted(period_returns["factor"].dropna().unique()) if not period_returns.empty else ["unknown"]
    cost_columns = [
        column for column in period_returns.columns
        if re.fullmatch(r"net_return_cost_\d+bp", column)
    ]
    costs = [
        int(re.search(r"\d+", column).group())
        for column in cost_columns
    ] if cost_columns else [0]
    rows: list[dict[str, object]] = []
    for factor in factors:
        factor_frame = period_returns[period_returns["factor"] == factor] if "factor" in period_returns else period_returns
        for period in ("IS", "OOS", "FULL"):
            selected = factor_frame if period == "FULL" else factor_frame[factor_frame["period"] == period]
            for cost in costs:
                rows.append(_metric_row(selected, factor, period, cost))
    return pd.DataFrame(rows)
