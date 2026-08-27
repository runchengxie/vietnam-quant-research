# 日频研究视图与来源仲裁 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans (or superpowers:subagent-driven-development) to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在不改写 raw/bronze 的前提下生成带异常隔离、来源仲裁、可交易标记和复权语义诊断的日频研究视图。

**Architecture:** 在现有 per-source validation 之后增加纯函数仲裁层。仲裁结果写入外部 data root 的 `derived/research_price_daily.jsonl`，每个 symbol 的仲裁摘要和跨源价格语义摘要分别写入 metadata；原有 raw quality gate 保持严格失败，新增 research gate 和 `factor_ready` 分开呈现。

**Tech Stack:** Python 3.11 dataclasses, existing `ExternalDataStore`, pytest, JSONL/JSON external runtime artifacts.

**Spec:** `docs/superpowers/specs/2026-08-27-research-view-arbitration-design.md`

## Global Constraints

- 不删除、填充或修改 raw snapshot 或 `bronze/price_daily.jsonl`。
- OHLC 含 `missing_required`、`invalid_ohlc` 或 `duplicate_date` 的候选不能进入 `research_eligible=true` 的记录。
- 零成交保留，但 `tradable=false`。
- VCI/KBS 价格语义没有独立公司行动证据时必须保持 `unresolved`，`factor_ready=false`。
- 运行时原始数据、研究派生数据和报告只能写入仓库外的数据根目录。
- 新生产代码必须先有能失败的测试；每个任务完成后单独提交。

---

### Task 1: Add research record and source arbitration contracts

**Files:**
- Modify: `src/vietnam_quant/schemas.py`
- Modify: `src/vietnam_quant/quality.py`
- Test: `tests/test_quality.py`

**Interfaces:**
- Produces `ResearchPriceDailyRecord`, `SourceArbitrationReport`, `PriceSemanticsReport`.
- Produces `arbitrate_price_bars(primary, secondary, *, primary_source, secondary_source, relative_tolerance=0.001) -> tuple[list[ResearchPriceDailyRecord], SourceArbitrationReport, PriceSemanticsReport]`.

- [ ] **Step 1: Write the failing tests**

Add these tests to `tests/test_quality.py` using the existing `make_price_row` helper:

```python
def test_arbitration_prefers_valid_primary_and_marks_tradability():
    rows, report, semantics = arbitrate_price_bars(
        [make_price_row(symbol="FPT", trading_date=date(2024, 1, 2), close=10, volume=100)],
        [make_price_row(symbol="FPT", trading_date=date(2024, 1, 2), close=10.01, volume=100)],
        primary_source="vci", secondary_source="kbs",
    )
    assert rows[0].source == "vci"
    assert rows[0].arbitration_reason == "primary_valid"
    assert rows[0].research_eligible is True
    assert rows[0].tradable is True
    assert "source_disagreement" in rows[0].quality_flags
    assert report.disagreement_count == 1
    assert semantics.status == "unresolved"


def test_arbitration_falls_back_to_valid_secondary_without_rewriting_bronze_row():
    invalid_primary = make_price_row(symbol="FPT", trading_date=date(2024, 1, 2), open=10, high=8, low=7, close=9, volume=100)
    valid_secondary = make_price_row(symbol="FPT", trading_date=date(2024, 1, 2), close=10, volume=100)
    rows, report, _ = arbitrate_price_bars([invalid_primary], [valid_secondary], primary_source="vci", secondary_source="kbs")
    assert rows[0].source == "kbs"
    assert rows[0].arbitration_reason == "secondary_fallback"
    assert rows[0].research_eligible is True
    assert rows[0].raw_close == 0.01
    assert report.fallback_count == 1
    assert invalid_primary.source == "vci"
    assert "invalid_ohlc" in invalid_primary.quality_flags


def test_arbitration_quarantines_when_both_sources_are_invalid_and_zero_volume_is_not_tradable():
    primary = make_price_row(symbol="A32", trading_date=date(2024, 1, 2), open=10, high=8, low=7, close=9, volume=0)
    secondary = make_price_row(symbol="A32", trading_date=date(2024, 1, 2), open=11, high=9, low=8, close=10, volume=0)
    rows, report, _ = arbitrate_price_bars([primary], [secondary], primary_source="vci", secondary_source="kbs")
    assert rows[0].research_status == "quarantined"
    assert rows[0].research_eligible is False
    assert rows[0].tradable is False
    assert rows[0].arbitration_reason == "both_invalid_primary_kept"
    assert report.quarantine_count == 1
    assert report.zero_volume_count == 0


def test_arbitration_keeps_valid_zero_volume_marked_not_tradable():
    rows, report, _ = arbitrate_price_bars(
        [make_price_row(symbol="A32", trading_date=date(2024, 1, 2), close=10, volume=0)],
        [], primary_source="vci", secondary_source="kbs",
    )
    assert rows[0].research_eligible is True
    assert rows[0].tradable is False
    assert report.zero_volume_count == 1
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_quality.py -q`

Expected: collection failure with `ImportError` because the new contracts and `arbitrate_price_bars` do not exist.

- [ ] **Step 3: Implement the minimal contracts and arbitration**

In `schemas.py`, subclass `PriceDailyRecord` as:

```python
@dataclass(frozen=True)
class ResearchPriceDailyRecord(PriceDailyRecord):
    research_status: str = "selected"
    arbitration_reason: str = "primary_valid"
    research_eligible: bool = True
    tradable: bool = True
```

Add dataclasses with the exact fields needed by the tests and pipeline: `SourceArbitrationReport` fields `symbol`, `primary_source`, `secondary_source`, `primary_row_count`, `secondary_row_count`, `selected_row_count`, `primary_selected_count`, `secondary_selected_count`, `fallback_count`, `quarantine_count`, `zero_volume_count`, `disagreement_count`, `missing_both_count`, `research_eligible_count`, `tradable_count`, `coverage_rate`, `tradable_rate`, `sample_disagreements`; and `PriceSemanticsReport` fields `symbol`, `primary_source`, `secondary_source`, `status`, `matched_dates`, `difference_count`, `ratio_median`, `ratio_p90`, `ratio_max`, `relative_difference_median`, `relative_difference_p90`, `relative_difference_max`, `yearly`.

In `quality.py`, implement `arbitrate_price_bars` as a date union over the validated source rows. A candidate is valid only when it has exactly one row for the date and none of `missing_required`, `invalid_ohlc`, `duplicate_date` in `quality_flags`. Select a valid primary first, then a valid secondary. If both are invalid, keep the primary row when present, otherwise the secondary row, mark it `quarantined`, and set `research_eligible=False`. Copy all base fields without mutating inputs; append only derived flags to the `ResearchPriceDailyRecord`. Set `tradable=research_eligible and raw_volume is not None and raw_volume > 0`. Compare common valid closes using the existing `relative_tolerance`; append `source_disagreement` and collect up to five sample differences. Return `PriceSemanticsReport(status="unresolved")` for every comparison.

- [ ] **Step 4: Run the focused tests to verify they pass**

Run: `python -m pytest tests/test_quality.py -q`

Expected: all quality tests pass.

- [ ] **Step 5: Commit**

```powershell
git add src/vietnam_quant/schemas.py src/vietnam_quant/quality.py tests/test_quality.py
git commit -m "feat: add daily source arbitration view"
```

### Task 2: Add research quality assessment and external storage outputs

**Files:**
- Modify: `src/vietnam_quant/quality.py`
- Modify: `src/vietnam_quant/storage.py`
- Modify: `src/vietnam_quant/schemas.py`
- Test: `tests/test_quality.py`
- Test: `tests/test_storage.py`

**Interfaces:**
- Produces `assess_research_quality(reports, *, expected_symbols, observations, min_coverage=0.90, semantics_status="unresolved") -> dict[str, Any]`.
- Adds `derived` to `ExternalDataStore.ensure_layout()`.

- [ ] **Step 1: Write the failing tests**

Add:

```python
def test_research_quality_passes_with_quarantine_but_blocks_factor_ready():
    reports = [
        SourceArbitrationReport(
            symbol="A32", primary_source="vci", secondary_source="kbs",
            primary_row_count=100, secondary_row_count=90, selected_row_count=100,
            primary_selected_count=95, secondary_selected_count=5, fallback_count=5,
            quarantine_count=5, zero_volume_count=10, disagreement_count=3,
            missing_both_count=0, research_eligible_count=95, tradable_count=85,
            coverage_rate=0.95, tradable_rate=0.85, sample_disagreements=[],
        )
    ]
    result = assess_research_quality(
        reports, expected_symbols=["A32"], observations=[{"symbol": "A32", "source": "vci", "response_status": 200, "row_count": 100}],
        semantics_status="unresolved",
    )
    assert result["status"] == "PASS_WITH_QUARANTINE"
    assert result["factor_ready"] is False
    assert result["quarantined_rows"] == 5


def test_external_store_creates_derived_layout(tmp_path):
    ExternalDataStore(tmp_path).ensure_layout()
    assert (tmp_path / "derived").is_dir()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_quality.py::test_research_quality_passes_with_quarantine_but_blocks_factor_ready tests/test_storage.py::test_external_store_creates_derived_layout -q`

Expected: import failure for `assess_research_quality`, then missing `derived` directory.

- [ ] **Step 3: Implement the research gate**

Implement `assess_research_quality` with these exact rules: require every `expected_symbols` to have a report; require at least one successful nonempty source observation per symbol; fail if any coverage rate is below `min_coverage`; return `status="PASS_WITH_QUARANTINE"` if all coverage rules pass and at least one report has quarantine rows, otherwise `status="PASS"`; include `factor_ready = status in {"PASS", "PASS_WITH_QUARANTINE"} and semantics_status == "confirmed"`, plus `symbol_count`, `missing_symbols`, `quarantined_rows`, `research_eligible_rows`, `tradable_rows`, `min_coverage`, and `price_semantics_status`.

Add `derived` to `ensure_layout` without changing existing paths.

- [ ] **Step 4: Run focused tests, then the complete suite**

Run: `python -m pytest tests/test_quality.py tests/test_storage.py -q`

Expected: focused tests pass. Then run `python -m pytest -q` and expect the existing suite plus the new tests to pass.

- [ ] **Step 5: Commit**

```powershell
git add src/vietnam_quant/quality.py src/vietnam_quant/storage.py src/vietnam_quant/schemas.py tests/test_quality.py tests/test_storage.py
git commit -m "feat: add research view quality gate"
```

### Task 3: Integrate arbitration and reports into the pipeline

**Files:**
- Modify: `src/vietnam_quant/pipeline.py`
- Modify: `exploration/02_daily_data_pipeline.py`
- Test: `tests/test_pipeline.py`

**Interfaces:**
- Extends `PipelineReport` with `research_quality_status`, `research_row_count`, `research_quarantined_row_count`, `factor_ready`, `research_report`.
- Writes `derived/research_price_daily.jsonl`, `metadata/source_arbitration_report.json`, `metadata/price_semantics_report.json`, and `metadata/research_quality_report.json`.

- [ ] **Step 1: Write the failing pipeline test**

Extend `FakeAdapter` data so `GOOD` returns one valid primary row and add a secondary fake adapter that returns one close differing by more than 0.1%. In `tests/test_pipeline.py`, add:

```python
def test_pipeline_writes_research_view_without_changing_bronze(tmp_path):
    report = run_pipeline(
        PipelineConfig(
            data_root=tmp_path, start=date(2024, 1, 1), end=date(2024, 1, 31),
            sample_size=2, primary_source="fake", secondary_source="fake2", strict=False,
            network=False, rate_limit_seconds=0,
        ),
        adapters={"fake": FakeAdapter(), "fake2": FakeSecondaryAdapter()},
    )
    research = [json.loads(line) for line in (tmp_path / "derived/research_price_daily.jsonl").read_text().splitlines()]
    bronze = [json.loads(line) for line in (tmp_path / "bronze/price_daily.jsonl").read_text().splitlines()]
    assert len(research) == 1
    assert len(bronze) == 2
    assert report.research_quality_status in {"PASS", "PASS_WITH_QUARANTINE"}
    assert report.factor_ready is False
    assert json.loads((tmp_path / "metadata/price_semantics_report.json").read_text())
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python -m pytest tests/test_pipeline.py::test_pipeline_writes_research_view_without_changing_bronze -q`

Expected: failure because `PipelineReport` has no research fields and no derived file is written.

- [ ] **Step 3: Integrate the minimal pipeline behavior**

After all source fetches for a selected symbol finish, call `arbitrate_price_bars` with the validated `source_rows`. Accumulate research rows and per-symbol reports. After the symbol loop, append research rows with identity fields `("symbol", "trading_date")` to `derived/research_price_daily.jsonl`; write the two report lists as JSON; call `assess_research_quality` with selected symbols and successful source observations; write `metadata/research_quality_report.json`.

Keep the existing raw quality summary and `strict_failed` calculation unchanged. Populate the new `PipelineReport` fields from the research results. If listing is unavailable, return empty research fields and do not fabricate derived rows. Update the CLI JSON only through the serializable `PipelineReport`; do not add a second network path.

- [ ] **Step 4: Run focused and complete tests**

Run: `python -m pytest tests/test_pipeline.py -q`, then `python -m pytest -q`.

Expected: all tests pass and the bronze row-count assertion remains true.

- [ ] **Step 5: Commit**

```powershell
git add src/vietnam_quant/pipeline.py exploration/02_daily_data_pipeline.py tests/test_pipeline.py
git commit -m "feat: write auditable research price view"
```

### Task 4: Document outputs and validate against the 50-stock pilot

**Files:**
- Modify: `docs/daily-data-loop-v0.md`
- Modify: `README.md`
- Test: existing test suite plus command-level checks

- [ ] **Step 1: Add output documentation**

Document the new `derived/research_price_daily.jsonl` and three metadata reports, the primary-valid/secondary-fallback/quarantine rules, zero-volume handling, and the distinction between raw gate, research gate, and `factor_ready`.

- [ ] **Step 2: Run repository verification**

Run:

```powershell
python -m pytest -q
python -m compileall -q src exploration tests
git diff --check
```

Expected: pytest has zero failures, compileall exits 0, and `git diff --check` emits no output.

- [ ] **Step 3: Run the fixed 50-stock pilot in the external data root**

Use the existing fixed symbol file and network run:

```powershell
python exploration/02_daily_data_pipeline.py --network --data-root D:\data\vietnam-quant-research\pilot-v4-research-view --symbols-file D:\data\vietnam-quant-research\pilot-v3-quality-gate\symbols.txt --start 2018-01-01 --end 2026-08-27 --primary-source vci --secondary-source kbs --rate-limit-seconds 0.05
```

Verify with a read-only Python check that 50 symbols, 100 stock observations, no duplicate research keys, and all four report files exist. Report raw gate status, research gate status, quarantine count, price semantics status, and factor readiness separately. Do not run the factor baseline when `factor_ready` is false.

- [ ] **Step 4: Commit documentation**

```powershell
git add docs/daily-data-loop-v0.md README.md
git commit -m "docs: describe research view quality gates"
```

- [ ] **Step 5: Push, open, review, and merge the PR**

```powershell
git push -u origin codex/research-view-arbitration
$prNumber = gh pr create --base main --head codex/research-view-arbitration --title "feat: add auditable research price view" --body "Adds auditable daily research view with source arbitration, OHLC quarantine, zero-volume tradability flags, and unresolved VCI/KBS price semantics. Tests: pytest, compileall, diff check. Pilot: external pilot-v4-research-view. Raw gate remains visible; factor baseline stays blocked while price semantics are unresolved. No raw data, credentials, or commercial data are committed."
gh pr checks ($prNumber | Select-Object -Last 1) --watch
gh pr merge ($prNumber | Select-Object -Last 1) --merge --delete-branch
```

The PR body must include the changed files, tests, pilot data root, license/credential boundary, raw-vs-research gate distinction, unresolved price semantics, and why the factor baseline remains blocked.
