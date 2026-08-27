# 公司行动—价格核对层 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a reusable, read-only event-to-price evidence report for APG/A32 that preserves source quality issues and never infers an adjustment factor.

**Architecture:** Keep `CorporateActionEvent` and `PriceDailyRecord` as the input contracts. Add one serializable `CorporateActionPriceReconciliation` record and a pure `event_price` module that selects an explicit event reference date, extracts per-source trading-day windows, computes descriptive price evidence, and assigns a conservative alignment status. Add a local CLI that reads external bronze JSONL plus a fixture or external event file and writes only metadata reports under the external data root.

**Tech Stack:** Python 3.11, frozen dataclasses, standard-library date/JSON/path utilities, pytest, existing `ExternalDataStore`; no new dependency and no network call in the report command.

**Spec:** `docs/superpowers/specs/2026-08-28-event-price-reconciliation-design.md`

## Global Constraints

- Do not modify or overwrite `raw`, `bronze/price_daily.jsonl`, or research price records.
- Do not infer missing event dates, adjustment ratios, or raw/adjusted provider semantics from price data.
- Keep `record_date` and `payment_date` separate from `ex_date`; only an explicit `ex_date` can be the primary cash/rights price reference date.
- Preserve raw/normalized closes, volume, quality flags, and `source_observation_id` in the evidence window.
- Keep all pilot-v6 runtime inputs/outputs outside Git; commit only source code, tests, fixtures, and concise documentation.
- Do not run the factor baseline and do not change `factor_ready=false`.

---

### Task 1: Correct the event fixture and add the report contract

**Files:**
- Modify: `tests/fixtures/corporate_actions_apg_a32.json`
- Modify: `tests/test_corporate_actions.py`
- Modify: `src/vietnam_quant/schemas.py`
- Modify: `src/vietnam_quant/__init__.py`
- Test: `tests/test_schemas.py`

**Interfaces:**
- Consumes: existing `CorporateActionEvent` and `SerializableMixin` contracts.
- Produces: `CorporateActionPriceReconciliation`, with fields `event_id`, `symbol`, `event_type`, `reference_date`, `reference_date_kind`, `event_dates`, `source_evidence`, `cross_source`, `assessment`, and `notes`; nested dates must serialize through the existing `_serialize` helper.

- [x] **Step 1: Write failing tests for the corrected A32 event semantics and report serialization**

Add tests that assert the A32 2020 fixture has `ex_date=2020-06-01`, `record_date=2020-06-02`, and `payment_date=2020-06-16`; assert the 2019 event has `record_date=2019-06-07` and `payment_date=2019-06-20`; and assert a `CorporateActionPriceReconciliation` serializes nested `event_dates` and keeps `assessment="unresolved"` without an adjustment field.

- [x] **Step 2: Run the focused tests and confirm the expected failure**

Run: `python -m pytest tests/test_corporate_actions.py tests/test_schemas.py -q`  
Expected: FAIL because the current fixture has the 2020 payment date in `ex_date` and the new report contract does not yet exist.

- [x] **Step 3: Make the minimum fixture and schema changes**

Correct only the source-supported A32 dates in the fixture, add the frozen report dataclass with the exact fields above, and export it from `vietnam_quant.__init__`. Do not add an adjusted-price or inferred-ratio field.

- [x] **Step 4: Run the focused tests and confirm they pass**

Run: `python -m pytest tests/test_corporate_actions.py tests/test_schemas.py -q`  
Expected: PASS.

- [x] **Step 5: Commit the contract and evidence-fixture correction**

```text
git add src/vietnam_quant/schemas.py src/vietnam_quant/__init__.py tests/test_schemas.py tests/test_corporate_actions.py tests/fixtures/corporate_actions_apg_a32.json
git commit -m "fix: correct A32 corporate action date semantics"
```

### Task 2: Implement the pure event-to-price reconciliation engine

**Files:**
- Create: `src/vietnam_quant/event_price.py`
- Create: `tests/test_event_price.py`

**Interfaces:**
- Consumes: `CorporateActionEvent` objects and an iterable of `PriceDailyRecord` objects.
- Produces:
  - `select_event_reference_date(event: CorporateActionEvent) -> tuple[date | None, str]`;
  - `reconcile_corporate_action_prices(events: Iterable[CorporateActionEvent], price_rows: Iterable[PriceDailyRecord], *, before_bars: int = 5, after_bars: int = 5, relative_tolerance: float = 0.001) -> list[CorporateActionPriceReconciliation]`.

- [ ] **Step 1: Write failing tests for reference-date selection**

Cover these exact cases: cash dividend with `ex_date` returns `(ex_date, "ex_date")`; employee-share listing with no `ex_date` returns `(listing_date, "listing_date")`; announcement-only event returns `(announcement_date, "announcement_date_reference_only")`; event with no announcement/ex/listing date returns `(None, "none")`. Assert that a payment date is never selected.

- [ ] **Step 2: Run the reference-date tests and confirm the expected failure**

Run: `python -m pytest tests/test_event_price.py -q`  
Expected: FAIL because `src/vietnam_quant/event_price.py` and `select_event_reference_date` do not exist.

- [ ] **Step 3: Implement explicit reference-date selection**

Implement `select_event_reference_date` with the four rules above. Return `announcement_date_reference_only` for an announcement-only anchor and never fall back to `record_date` or `payment_date`.

- [ ] **Step 4: Write failing tests for source windows, quality evidence, and statuses**

Use small in-memory `PriceDailyRecord` rows to assert: five bars before and after are selected by source trading-date order; a non-trading reference date yields `nearby` without a fabricated bar; raw/normalized close, volume, quality flags, and `source_observation_id` are present in the window; invalid OHLC and zero volume remain visible; no source context yields `no_evidence`; and source close differences or invalid context yield `unresolved` rather than an inferred ratio.

- [ ] **Step 5: Run the new engine tests and confirm the expected failure**

Run: `python -m pytest tests/test_event_price.py -q`  
Expected: FAIL on the missing reconciliation function and report fields.

- [ ] **Step 6: Implement the minimal pure reconciliation engine**

Group rows by `(symbol, source)` and sort only the in-memory view by `trading_date`. For each event, use the selected reference date, collect at most `before_bars` strictly earlier and `after_bars` strictly later bars plus an exact reference-day bar when present, and compute per-source `pre_close`, `reference_close`, `post_close`, `pre_to_post_return`, `available_bar_count`, `zero_volume_count`, and `invalid_ohlc_count`. Preserve each selected row as a serializable evidence dictionary.

Compute cross-source common-date count, close-difference count, relative-difference median/max, and missing/invalid context counts using valid closes only. Set `assessment` to `no_evidence` when no source has context, `nearby` when context exists but no source has the exact reference date and no conflict is observed, `matched` when at least one source has exact-date plus before/after context and no conflict is observed, and `unresolved` for structural invalidity, insufficient context, or cross-source differences above tolerance. Descriptive ratios may be reported, but no adjustment factor may be emitted.

- [ ] **Step 7: Run the engine tests and confirm they pass**

Run: `python -m pytest tests/test_event_price.py -q`  
Expected: PASS, including assertions that input row objects are unchanged.

- [ ] **Step 8: Commit the pure engine**

```text
git add src/vietnam_quant/event_price.py tests/test_event_price.py
git commit -m "feat: add event price reconciliation engine"
```

### Task 3: Add external-root persistence, CLI loading, and documentation

**Files:**
- Modify: `src/vietnam_quant/event_price.py`
- Create: `exploration/04_event_price_reconciliation.py`
- Create: `tests/test_event_price_cli.py`
- Modify: `docs/data-contracts.md`
- Modify: `README.md`

**Interfaces:**
- Consumes: external `bronze/price_daily.jsonl`, a JSON array or JSONL event file, and `ExternalDataStore`.
- Produces:
  - `write_event_price_reconciliation(store: ExternalDataStore, reports: Iterable[CorporateActionPriceReconciliation], *, relative_jsonl: Path | str = "metadata/corporate_action_price_reconciliation.jsonl", relative_json: Path | str = "metadata/corporate_action_price_reconciliation.json") -> tuple[Path, Path]`;
  - CLI command `python exploration/04_event_price_reconciliation.py --data-root <external-root> --events-file <fixture-or-external-file>` that performs no network call and writes only the two metadata outputs.

- [ ] **Step 1: Write failing tests for idempotent persistence and CLI help**

Assert that writing the same reports twice leaves one JSONL record per `event_id` and writes a JSON summary with `entries`. Add a CLI contract test that `--help` exits zero and exposes `--data-root`, `--events-file`, `--price-path`, `--before-bars`, and `--after-bars`.

- [ ] **Step 2: Run the focused persistence/CLI tests and confirm the expected failure**

Run: `python -m pytest tests/test_event_price_cli.py -q`  
Expected: FAIL because the writer and CLI do not yet exist.

- [ ] **Step 3: Implement persistence and the offline CLI**

Use `ExternalDataStore.append_jsonl_many(..., key="event_id")` for JSONL and `write_json(..., {"entries": [...]})` for the summary. The CLI must parse event JSON arrays or JSONL, convert JSON price rows to `PriceDailyRecord` with `trading_date=date.fromisoformat(...)`, call the pure engine, and exit zero after writing reports. It must not instantiate an HTTP adapter or enable network access.

- [ ] **Step 4: Document the new evidence output and non-goals**

Add the two metadata paths, CLI usage, status definitions, and explicit “no adjusted price / no factor readiness” boundary to `docs/data-contracts.md` and the relevant README usage section.

- [ ] **Step 5: Run focused tests and confirm they pass**

Run: `python -m pytest tests/test_event_price.py tests/test_event_price_cli.py tests/test_cli_contracts.py -q`  
Expected: PASS.

- [ ] **Step 6: Commit persistence, CLI, tests, and documentation**

```text
git add src/vietnam_quant/event_price.py exploration/04_event_price_reconciliation.py tests/test_event_price_cli.py tests/test_cli_contracts.py docs/data-contracts.md README.md
git commit -m "feat: expose offline event price reconciliation report"
```

### Task 4: Run the pilot-v6 evidence report and finish verification

**Files:**
- Create: `docs/event-price-reconciliation-2026-08-28.md`
- Modify: `docs/superpowers/plans/2026-08-28-event-price-reconciliation.md`

**Interfaces:**
- Consumes: `D:\data\vietnam-quant-research\pilot-v6\bronze\price_daily.jsonl` and the corrected repository fixture.
- Produces: external `D:\data\vietnam-quant-research\pilot-v6\metadata\corporate_action_price_reconciliation.jsonl` and `.json`, plus a concise repository evidence note.

- [ ] **Step 1: Run the offline CLI against pilot-v6**

```text
python exploration/04_event_price_reconciliation.py --data-root D:\data\vietnam-quant-research\pilot-v6 --events-file tests\fixtures\corporate_actions_apg_a32.json --price-path bronze\price_daily.jsonl --before-bars 5 --after-bars 5
```

Expected: exit zero, create only metadata outputs under pilot-v6, and leave bronze row count unchanged.

- [ ] **Step 2: Inspect the generated APG/A32 evidence without changing it**

Record event reference-date kinds, per-source context counts, zero-volume/invalid flags, cross-source differences, and assessment statuses. Explicitly report that the evidence does not prove causality or adjusted-price semantics.

- [ ] **Step 3: Write the concise evidence note and mark the plan steps complete**

Include the corrected A32 dates, APG/A32 event statuses, pilot-v6 input/output paths, and the remaining `factor_ready=false` decision. Do not copy raw price rows or runtime JSON into the repository.

- [ ] **Step 4: Run final verification**

```text
python -m pytest
python -m compileall -q src tests exploration
git diff --check
git status --short --branch
```

Expected: all tests pass, compileall and diff-check exit zero, and only intended source/test/docs files are tracked.

- [ ] **Step 5: Commit the evidence note and final plan state**

```text
git add docs/event-price-reconciliation-2026-08-28.md docs/superpowers/plans/2026-08-28-event-price-reconciliation.md
git commit -m "docs: record event price reconciliation evidence"
```

The PR must state that no factor baseline was run, `factor_ready` remains false, and pilot-v6 runtime data was not committed.
