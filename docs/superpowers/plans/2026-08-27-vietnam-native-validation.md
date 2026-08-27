# Vietnam Native Validation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a Vietnam-native, market-neutral Alpha validation layer and connect it to the existing local factor baseline without importing the A-share research framework.

**Architecture:** Keep Vietnam-specific price, liquidity, suspension, limit, and corporate-action semantics in this repository. Add a pure validation module that consumes the existing feature panel and produces auditable forward returns, cross-sectional Rank IC, quantile spreads, monotonicity, and chronological IS/OOS summaries. Keep the existing cost-aware monthly backtest as the execution-oriented companion rather than replacing it.

**Tech Stack:** Python 3.11, pandas, numpy, pytest, JSON/CSV outputs.

**Spec:** The approved design in the conversation and `docs/research-validation-conventions.md`.

## Global Constraints

- Do not import or depend on `research-workspace` or its submodule packages.
- Use only data available at the formation date; validation returns are close-to-close diagnostics with explicit forward horizons.
- Keep `raw_close`, `normalized_close`, and `adjusted_close` semantics separate.
- Exclude `research_eligible=false`, structural quality failures, zero-volume, and non-positive price rows from factor validation.
- Preserve chronological OOS splitting; no random split and no parameter tuning on the final OOS period.
- Report costs and execution backtest separately from gross factor diagnostics.
- Do not run the network pipeline or claim the 50-stock data gate has passed.

## Task 1: Forward return and Rank IC primitives

**Files:**
- Create: `src/vietnam_quant/validation.py`
- Test: `tests/test_validation.py`

**Interfaces:**
- `compute_forward_returns(features: pd.DataFrame, horizons: tuple[int, ...] = (1, 5, 20), close_col: str = "normalized_close") -> pd.DataFrame`
- `compute_rank_ic(panel: pd.DataFrame, factor: str, horizon: int, min_cross_section: int = 10) -> pd.Series`

- [x] Write failing tests for next-day and multi-day forward returns, grouped by symbol, with current-day factor values and no future-row contamination.
- [x] Run `python -m pytest tests/test_validation.py -q` and observe the missing-module failure.
- [x] Implement date normalization, per-symbol forward close-to-close return `close[t+h] / close[t] - 1`, and a pure Spearman rank correlation per formation date.
- [x] Mark dates with fewer than `min_cross_section` valid pairs as missing rather than manufacturing an IC value.
- [x] Run the targeted tests and confirm they pass.

## Task 2: Quantile spread, monotonicity, and chronological summary

**Files:**
- Modify: `src/vietnam_quant/validation.py`
- Test: `tests/test_validation.py`

**Interfaces:**
- `compute_quantile_returns(panel: pd.DataFrame, factor: str, horizon: int, n_quantiles: int = 5, min_cross_section: int = 10) -> pd.DataFrame`
- `summarize_factor_validation(panel: pd.DataFrame, factor: str, horizons: tuple[int, ...] = (1, 5, 20), n_quantiles: int = 5, oos_fraction: float = 0.3, min_cross_section: int = 10) -> pd.DataFrame`

- [x] Add failing tests for per-date quantile returns, high-minus-low spread, positive quantile monotonicity, and an OOS period whose start date is later than the IS period.
- [x] Run the targeted tests and confirm the new behavior fails before implementation.
- [x] Implement deterministic rank-based quantiles, per-date equal-weight forward returns, spread and adjacent-quantile monotonicity, then summarize full/IS/OOS metrics with counts and date bounds.
- [x] Make invalid `n_quantiles`, `oos_fraction`, and horizon inputs fail with `ValueError`.
- [x] Run the targeted tests and confirm they pass.

## Task 3: Integrate validation into the local baseline CLI

**Files:**
- Modify: `exploration/03_factor_baseline.py`
- Modify: `tests/test_cli_contracts.py`
- Test: `tests/test_validation.py`

**Interfaces:**
- Add CLI option `--validation-output`.
- Default validation output to `<output stem>_validation.json`.
- Keep the existing period CSV and summary JSON outputs unchanged.

- [x] Add a CLI help assertion and a fixture-driven invocation test that writes validation JSON without network access.
- [x] Run the CLI tests and confirm the option/output behavior fails before implementation.
- [x] Implement validation after `compute_features`, using each requested factor and writing a JSON list with factor/horizon/period rows.
- [x] Keep the existing backtest cost scenarios in the summary output and include a pointer to the validation file in the CLI status payload.
- [x] Run the CLI tests and confirm they pass.

## Task 4: Document the two local layers

**Files:**
- Modify: `docs/research-validation-conventions.md`
- Modify: `docs/daily-data-loop-v0.md`

- [x] Document that factor diagnostics are close-to-close and market-neutral while `backtest.py` owns next-available-open execution, turnover, cost, and liquidity exclusions.
- [x] Document the validation output fields and state that no result is considered investable before price semantics and the 50-stock gate are cleared.
- [x] Run the full test suite, compileall, and diff checks.

## Verification

```text
python -m pytest
python -m compileall -q src tests exploration
git diff --check
```

The PR must state that no network data was fetched and no Alpha conclusion was produced from the unresolved pilot data.
