# Vietnam Daily Data Loop v0 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (- [ ]) syntax for tracking.

**Goal:** 建立可离线测试、可网络运行、可追溯到来源观察的越南日频数据管线，并生成带交易成本和样本外结果的基础因子基线。

**Architecture:** 使用 src/vietnam_quant 提供数据契约、VCI/KBS/SSI 适配器、质量检查、外部存储、因子和回测模块；exploration 目录只放命令行入口。每个阶段从已合并的 main 创建独立 worktree、独立分支和独立 PR，按依赖顺序合并。

**Tech Stack:** Python 3.11、pandas、requests、pytest、标准库 dataclasses/zoneinfo/hashlib/json；市场原始数据和运行产物写入外部数据根目录。

**Spec:** docs/superpowers/specs/2026-08-27-vietnam-daily-data-loop-v0-design.md

## Global Constraints

- 第一轮默认运行 50 只股票，最低覆盖 HOSE 30、HNX 10、UPCoM 10；2050 只作为通过试点后的可配置扩展。
- VCI 是主来源，KBS 是第二来源；SSI 只实现可插拔接口和无凭证跳过状态。
- 不提交 API key、secret、token、账号信息、完整行情、商业数据文件或外部运行产物。
- 原始价格和标准化价格必须并列保存；千 VND 转 VND 时保留原始值和原始单位。
- VCI 的 to + countBack 响应必须在客户端做严格日期裁剪；KBS 响应必须先升序排序。
- 缺失、重复、OHLC 异常、零成交和边界价格只能被标记，不能静默删除、填充或覆盖。
- 因子信号只能使用形成日前可用数据；回测必须包含流动性过滤、不可交易约束、交易成本和时间切分 OOS。
- 离线单元测试不得访问网络；网络集成运行必须显式启用并写入外部数据根目录。
- 每个独立任务按 codex/<short-task> 创建 worktree 和分支，提交、推送、创建 PR；检查通过后合并并删除分支与 worktree。

---

### Task 1: Foundation, schemas, adapters, and quality rules

**Files:**
- Create: pyproject.toml
- Create: src/vietnam_quant/__init__.py
- Create: src/vietnam_quant/schemas.py
- Create: src/vietnam_quant/adapters/__init__.py
- Create: src/vietnam_quant/adapters/vci.py
- Create: src/vietnam_quant/adapters/kbs.py
- Create: src/vietnam_quant/adapters/ssi.py
- Create: src/vietnam_quant/quality.py
- Create: tests/conftest.py
- Create: tests/fixtures/vci_listing.json
- Create: tests/fixtures/vci_ohlcv.json
- Create: tests/fixtures/kbs_ohlcv.json
- Create: tests/test_adapters.py
- Create: tests/test_quality.py
- Create: docs/data-contracts.md

**Interfaces:**
- Produces InstrumentRecord, RawPriceBar, PriceDailyRecord, SourceObservation, FetchResult, QualityReport, and their to_dict() methods in schemas.py.
- Produces parse_vci_listing, parse_vci_ohlcv, parse_kbs_ohlcv, normalize_price_bars, normalize_exchange, validate_price_bars, and reconcile_price_bars.
- vietnam_quant must be importable after python -m pip install -e ".[dev]".

- [ ] Step 1: Add package metadata and failing contract tests

Add pyproject.toml with Python 3.11 support, runtime dependencies pandas>=2.0 and requests>=2.0, and optional dev dependency pytest>=8.0. Add tests that import the public dataclasses and assert serialized keys:

```python
from datetime import date, datetime, timezone

from vietnam_quant.schemas import InstrumentRecord, SourceObservation


def test_instrument_record_serializes_exchange_and_validity():
    record = InstrumentRecord(
        instrument_id="VCI:FPT",
        symbol="FPT",
        issuer_name=None,
        exchange_raw="HSX",
        exchange="HOSE",
        security_type="STOCK",
        listing_status="observed_current",
        valid_from=None,
        valid_to=None,
        listing_date=None,
        delisting_date=None,
        selection_reason="explicit_symbol",
        source="vci",
        retrieved_at_utc=datetime(2026, 8, 27, tzinfo=timezone.utc),
    )
    payload = record.to_dict()
    assert payload["exchange_raw"] == "HSX"
    assert payload["exchange"] == "HOSE"
    assert payload["valid_from"] is None


def test_source_observation_serializes_request_and_quality_fields():
    observation = SourceObservation(
        observation_id="vci:FPT:2024-01-01:2024-01-31",
        source="vci",
        endpoint="https://example.test",
        symbol="FPT",
        request_parameters={"countBack": 1000},
        retrieved_at_utc=datetime(2026, 8, 27, tzinfo=timezone.utc),
        response_status=200,
        latency_ms=12.5,
        raw_snapshot_path="raw/vci/FPT.json",
        raw_payload_sha256="abc",
        row_count=22,
        first_trading_date=date(2024, 1, 2),
        last_trading_date=date(2024, 1, 31),
        quality_status="PASS",
        quality_issue_count=0,
        parser_version="vci-1",
        schema_version="daily-v0",
        error_type=None,
        error_message=None,
    )
    assert observation.to_dict()["request_parameters"] == {"countBack": 1000}
```

Run:

```text
python -m pytest tests/test_adapters.py tests/test_quality.py -q
```

Expected: FAIL because vietnam_quant and the dataclasses do not exist.

- [ ] Step 2: Implement the schemas minimally

Use frozen dataclasses with typed nullable fields. Implement to_dict() by converting dates and datetimes to ISO-8601 strings, preserving dictionaries and quality flag lists. Define RawPriceBar with raw source fields and PriceDailyRecord with raw and normalized prices, trading_date, quality_flags, source_observation_id, parser_version, and schema_version. Define FetchResult with status, latency, raw payload, request parameters, and error fields.

- [ ] Step 3: Add failing parser and normalization tests

Add fixtures with a VCI listing row containing board HSX, a VCI array response with epoch-second timestamps outside and inside the requested window, a KBS response whose data_day rows are reverse ordered and whose price values are thousand VND, and an OHLC row where high is below max(open, close) plus a zero-volume row.

Add tests:

```python
def test_vci_listing_maps_hsx_to_hose_and_keeps_raw_board():
    records = parse_vci_listing(load_fixture("vci_listing.json"))
    assert records[0].exchange == "HOSE"
    assert records[0].exchange_raw == "HSX"


def test_kbs_parser_sorts_and_strictly_crops_dates():
    rows = parse_kbs_ohlcv(
        load_fixture("kbs_ohlcv.json"),
        symbol="FPT",
        requested_start=date(2024, 1, 2),
        requested_end=date(2024, 1, 31),
        source_observation_id="obs",
    )
    assert [row.trading_date for row in rows] == sorted(row.trading_date for row in rows)
    assert rows[0].trading_date == date(2024, 1, 2)
    assert rows[-1].trading_date == date(2024, 1, 31)
    assert rows[0].normalized_close == rows[0].raw_close * 1000
```

Run the focused tests and confirm they fail for missing parser functions, not a fixture or import typo.

- [ ] Step 4: Implement VCI/KBS parsing and normalization

Implement:

```python
def normalize_exchange(raw_value: object) -> tuple[str | None, str | None]: ...

def parse_vci_listing(
    payload: object,
    retrieved_at_utc: datetime | None = None,
) -> list[InstrumentRecord]: ...

def parse_vci_ohlcv(
    payload: object,
    symbol: str,
    requested_start: date,
    requested_end: date,
    source_observation_id: str,
    exchange: str | None = None,
) -> list[PriceDailyRecord]: ...

def parse_kbs_ohlcv(
    payload: object,
    symbol: str,
    requested_start: date,
    requested_end: date,
    source_observation_id: str,
    exchange: str | None = None,
) -> list[PriceDailyRecord]: ...
```

VCI must support array-shaped t/o/h/l/c/v payloads and row-shaped payloads. Convert epoch timestamps through Asia/Ho_Chi_Minh to trading_date; parse KBS timestamps as local Vietnam time. Sort normalized rows and filter inclusively to the requested dates. Use raw_price_unit thousand_vnd and normalized VND values without overwriting raw fields.

- [ ] Step 5: Add failing quality and reconciliation tests

Test that quality validation returns named flags and counts:

```python
def test_quality_flags_keep_invalid_rows_and_mark_zero_volume():
    rows = [
        make_price_row(open=10, high=8, low=7, close=9, volume=0),
    ]
    report = validate_price_bars(rows)
    assert report.issue_count == 2
    assert "invalid_ohlc" in report.rows[0].quality_flags
    assert "zero_volume" in report.rows[0].quality_flags


def test_reconciliation_reports_missing_dates_and_close_difference():
    report = reconcile_price_bars(
        primary=[make_price_row(symbol="FPT", trading_date=date(2024, 1, 2), close=10)],
        secondary=[make_price_row(symbol="FPT", trading_date=date(2024, 1, 3), close=10.1)],
    )
    assert report.missing_in_primary == ["2024-01-03"]
    assert report.missing_in_secondary == ["2024-01-02"]
```

Run the tests and confirm the expected failure before implementing quality logic.

- [ ] Step 6: Implement quality flags and reconciliation

Implement validate_price_bars(rows) without dropping rows. It must check required fields, duplicate dates, sort order, OHLC relations, negative values, zero volume, unit conversion, and close equals high/low boundary proxies. Implement reconcile_price_bars(primary, secondary) by date and report missing dates plus absolute/relative close differences. Make the report serializable.

- [ ] Step 7: Add SSI credential boundary and contract documentation

Implement:

```python
class SSIAdapter:
    source_name = "ssi"

    def check_credentials(self) -> CredentialStatus: ...
```

Return skipped_missing_credentials when SSI_API_KEY or SSI_SECRET is absent. Add docs/data-contracts.md documenting field names, units, quality flags, source observation lineage, and the fact that historical validity dates are null when the current listing cannot prove them.

- [ ] Step 8: Run Task 1 verification and commit

Run:

```text
python -m pip install -e ".[dev]"
python -m pytest -q
python -m compileall src tests
git diff --check
```

Commit on branch codex/daily-loop-foundation:

```text
git add pyproject.toml src tests docs/data-contracts.md
git commit -m "feat: add daily data contracts and parsers"
```

Push and open PR targeting main. Merge only after tests pass, then delete the branch and worktree before starting Task 2.

---

### Task 2: External storage, universe selection, and pipeline orchestration

**Files:**
- Create: src/vietnam_quant/storage.py
- Create: src/vietnam_quant/universe.py
- Create: src/vietnam_quant/pipeline.py
- Create: exploration/02_daily_data_pipeline.py
- Create: tests/test_storage.py
- Create: tests/test_universe.py
- Create: tests/test_pipeline.py
- Modify: src/vietnam_quant/adapters/vci.py
- Modify: src/vietnam_quant/adapters/kbs.py
- Modify: src/vietnam_quant/schemas.py

**Interfaces:**
- ExternalDataStore(data_root: Path) writes raw JSON, JSONL records, and JSON reports atomically.
- select_sample(instruments, sample_size=50, quotas={"HOSE": 30, "HNX": 10, "UPCOM": 10}, edge_symbols=()) -> list[InstrumentRecord].
- run_pipeline(config: PipelineConfig, adapters: Mapping[str, MarketDataAdapter]) -> PipelineReport.
- PipelineConfig contains data_root, start, end, sample_size, primary_source, secondary_source, strict, network, and rate_limit_seconds.

- [ ] Step 1: Write failing storage tests

Test raw snapshot hashing, atomic JSONL writing, and idempotent duplicate prevention:

```python
def test_store_raw_snapshot_returns_sha256_and_relative_path(tmp_path):
    store = ExternalDataStore(tmp_path)
    path, digest = store.write_raw("vci", "FPT", {"data": [1]}, run_date=date(2026, 8, 27))
    assert path == Path("raw/vci/2026-08-27/FPT.json")
    assert len(digest) == 64
    assert (tmp_path / path).exists()


def test_append_jsonl_does_not_duplicate_observation(tmp_path):
    store = ExternalDataStore(tmp_path)
    record = {"observation_id": "one", "source": "vci"}
    store.append_jsonl("metadata/source_observations.jsonl", record, key="observation_id")
    store.append_jsonl("metadata/source_observations.jsonl", record, key="observation_id")
    assert len((tmp_path / "metadata/source_observations.jsonl").read_text().splitlines()) == 1
```

Run focused tests and confirm failure because ExternalDataStore does not exist.

- [ ] Step 2: Implement ExternalDataStore

Implement write_raw, append_jsonl, write_json, and read_jsonl. Use UTF-8 JSON with stable key ordering and SHA-256 over exact raw payload bytes. Write to a temporary sibling file and use Path.replace() for atomic replacement. All paths returned to SourceObservation must be relative to data_root.

- [ ] Step 3: Write failing universe tests

Test stable exchange quotas, explicit edge symbols, and no fabricated exchange for DELISTED:

```python
def test_select_sample_is_stable_and_respects_exchange_quotas():
    sample = select_sample(make_listing_rows(), sample_size=50)
    counts = Counter(row.exchange for row in sample if row.exchange in {"HOSE", "HNX", "UPCOM"})
    assert counts == {"HOSE": 30, "HNX": 10, "UPCOM": 10}


def test_delisted_edge_case_keeps_delisted_status():
    sample = select_sample(
        make_listing_rows(),
        sample_size=50,
        edge_symbols=("AGE",),
    )
    age = next(row for row in sample if row.symbol == "AGE")
    assert age.exchange == "DELISTED"
    assert age.selection_reason == "edge_case"
```

Confirm expected failure before implementing selection.

- [ ] Step 4: Implement sample selection

Sort rows by exchange and symbol, select the exchange quotas, and honor explicit edge symbols without changing their source exchange. If edge symbols would exceed sample_size, fail with a descriptive ValueError rather than silently dropping a requested symbol. Persist selection_reason in selected records.

- [ ] Step 5: Write failing pipeline orchestration tests

Use a fake adapter with deterministic payloads and assert that the pipeline writes raw snapshots, observations, normalized rows, and quality reports while continuing after one symbol failure:

```python
def test_pipeline_continues_after_symbol_failure(tmp_path):
    report = run_pipeline(
        PipelineConfig(
            data_root=tmp_path,
            start=date(2024, 1, 1),
            end=date(2024, 1, 31),
            sample_size=2,
            primary_source="fake",
            secondary_source=None,
            strict=False,
            network=False,
            rate_limit_seconds=0,
        ),
        adapters={"fake": FakeAdapter(fails_for={"BAD"})},
    )
    assert report.failed_symbols == ["BAD"]
    assert (tmp_path / "metadata/source_observations.jsonl").exists()
    assert (tmp_path / "bronze/price_daily.jsonl").exists()
```

Run and confirm failure because orchestration types and functions are missing.

- [ ] Step 6: Implement pipeline orchestration and adapter fetch methods

Add bounded retry for connection errors, 429, and 5xx; record each final request outcome in SourceObservation; continue to the next symbol after 4xx, parse, or credential errors. Implement VCI and KBS HTTP fetch methods with request parameters, elapsed time, raw payload capture, and explicit parser versions. The pipeline must fetch and store the listing, select the sample, fetch primary and optional secondary daily data, write raw snapshots before parsing, write normalized instrument_master and price_daily, write quality_report.json and reconciliation_report.json, and return a serializable PipelineReport.

- [ ] Step 7: Add CLI and SSI skip behavior

Implement exploration/02_daily_data_pipeline.py with these options:

```text
--data-root
--start YYYY-MM-DD
--end YYYY-MM-DD
--sample-size
--symbols-file
--primary-source
--secondary-source
--rate-limit-seconds
--network
--strict
```

Without --network, the command must explain that a fixture or cached raw input is required. When SSI is selected without credentials, write skipped_missing_credentials and continue.

- [ ] Step 8: Run Task 2 verification and commit

Run:

```text
python -m pytest tests/test_storage.py tests/test_universe.py tests/test_pipeline.py -q
python exploration/02_daily_data_pipeline.py --help
python -m compileall src exploration
git diff --check
```

Commit on branch codex/daily-loop-pipeline:

```text
git add src exploration/02_daily_data_pipeline.py tests
git commit -m "feat: add external daily data pipeline"
```

Push, open PR, merge after checks, and remove the branch/worktree before Task 3.

---

### Task 3: Factor features and cost-aware backtest

**Files:**
- Create: src/vietnam_quant/factors.py
- Create: src/vietnam_quant/backtest.py
- Create: exploration/03_factor_baseline.py
- Create: tests/test_factors.py
- Create: tests/test_backtest.py

**Interfaces:**
- compute_features(price_frame: pd.DataFrame) -> pd.DataFrame.
- run_factor_backtest(features: pd.DataFrame, factor: str, config: BacktestConfig) -> pd.DataFrame.
- summarize_backtest(period_returns: pd.DataFrame, oos_fraction: float) -> pd.DataFrame.
- BacktestConfig contains n_quantiles=5, cost_bps=(0, 50, 100), liquidity_quantile=0.2, oos_fraction=0.3, and exclude_boundary_proxy=False.

- [ ] Step 1: Write failing feature tests

Use a small synthetic DataFrame with multiple symbols and dates. Test lagged momentum, reversal, volatility, Amihud, volume intensity, and blocked market-cap behavior:

```python
def test_momentum_uses_previous_day_not_same_day_close():
    frame = make_price_frame(
        dates=["2024-01-01", "2024-01-02", "2024-01-03"],
        closes=[10.0, 11.0, 20.0],
    )
    features = compute_features(frame)
    row = features.loc[features["trading_date"] == "2024-01-03"].iloc[0]
    assert row["momentum_1m"] != 20.0 / 10.0 - 1.0
    assert row["market_cap_status"] == "blocked_missing_market_cap"
```

Run and confirm failure because compute_features does not exist.

- [ ] Step 2: Implement feature computation

Sort by symbol and date, compute daily returns from normalized close, and shift all signal inputs by one row before calculating:

```text
momentum_1m=22 trading-day lag
momentum_3m=64 trading-day lag
momentum_6m=127 trading-day lag
momentum_12m=253 trading-day lag
reversal_1m=-momentum_1m
volatility_1m=21-day rolling standard deviation
volatility_3m=63-day rolling standard deviation
avg_volume_1m=21-day rolling mean
amihud_1m=21-day mean(abs(return)/(close*volume))
```

Add avg_traded_value_proxy_1m, boundary_price_proxy, tradable_quality, and market_cap_status. Do not create a size signal if market_cap is absent.

- [ ] Step 3: Write failing backtest tests

Test quantile formation, no same-day execution, non-tradable exclusions, turnover, costs, and OOS labels:

```python
def test_backtest_applies_cost_and_oos_without_same_day_execution():
    result = run_factor_backtest(
        make_feature_frame(),
        factor="momentum_1m",
        config=BacktestConfig(cost_bps=(0, 50, 100), oos_fraction=0.3),
    )
    assert {"IS", "OOS"} <= set(result["period"])
    assert (result["net_return_cost_50bp"] <= result["gross_return"]).all()
    assert "excluded_for_non_tradable" in result.columns
```

Confirm expected failure before implementing the backtest.

- [ ] Step 4: Implement monthly quantile portfolios

Use the last available trading date of each month for formation and the next available trading day for execution. Use five cross-sectional quantiles and skip formation dates with fewer than 10 valid securities. Construct equal-weight high-minus-low portfolios. Exclude missing/non-positive open, zero-volume, invalid-OHLC, and duplicate-date rows. Keep boundary proxies unless configuration says otherwise.

- [ ] Step 5: Implement liquidity, turnover, cost, and OOS reporting

Remove the cross-sectional bottom 20% by pre-formation 21-day close times raw_volume proxy. Calculate one-way turnover and net return:

```text
turnover_t = 0.5 * sum(abs(target_weight_i - previous_weight_i))
net_return_t = gross_return_t - cost_bps / 10000 * turnover_t
```

Label the last 30% of trading dates OOS without shuffling. Return period-level rows with factor, formation date, counts, returns, turnover, cost scenarios, and exclusion counts. Return insufficient_coverage when no valid formation exists.

- [ ] Step 6: Implement summary metrics and CLI

Add cumulative return, annualized return, volatility, maximum drawdown, Sharpe proxy, average turnover, valid formation count, and missing ratio summaries for IS, OOS, and full sample. Implement:

```text
python exploration/03_factor_baseline.py \
  --price-path external/bronze/price_daily.jsonl \
  --output external/reports/factor_baseline.csv \
  --oos-fraction 0.3 \
  --cost-bps 0,50,100
```

The CLI must emit CSV/JSON only under the external data root and print a short summary with factor coverage and blocked size status.

- [ ] Step 7: Run Task 3 verification and commit

Run:

```text
python -m pytest tests/test_factors.py tests/test_backtest.py -q
python exploration/03_factor_baseline.py --help
python -m compileall src exploration
git diff --check
```

Commit on branch codex/daily-loop-factors:

```text
git add src/vietnam_quant/factors.py src/vietnam_quant/backtest.py exploration/03_factor_baseline.py tests
git commit -m "feat: add daily factor baseline backtest"
```

Push, open PR, merge after checks, and remove the branch/worktree before Task 4.

---

### Task 4: Pilot run, documentation, and acceptance report

**Files:**
- Modify: README.md
- Modify: docs/exploration-data-audit.md
- Modify: docs/recommended-data-stack.md
- Create: docs/daily-data-loop-v0.md
- Create: tests/test_cli_contracts.py

**Interfaces:**
- Documents exact pilot commands, output locations, quality gates, and limitations.
- Does not commit raw market data or generated external reports.

- [ ] Step 1: Write CLI contract tests

Test that both exploration commands expose data-root and the relevant date/input options, and that help exits successfully without network access:

```python
def test_daily_pipeline_help_is_offline():
    result = subprocess.run(
        [sys.executable, "exploration/02_daily_data_pipeline.py", "--help"],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "--data-root" in result.stdout
```

- [ ] Step 2: Run the offline full suite

Run:

```text
python -m pytest -q
python -m compileall src exploration tests
git diff --check
```

Expected: all offline tests pass; no command accesses a network endpoint.

- [ ] Step 3: Run the 50-symbol network pilot outside the repository

Use the configured external root:

```text
python exploration/02_daily_data_pipeline.py \
  --network \
  --data-root D:\data\vietnam-quant-research \
  --start 2018-01-01 \
  --end 2026-08-27 \
  --sample-size 50 \
  --primary-source vci \
  --secondary-source kbs \
  --strict
```

If network access, rate limits, or source authorization prevents completion, preserve per-source error observations and report the block; do not replace missing data with fabricated values.

- [ ] Step 4: Run the factor baseline only after quality gates

If the pilot quality report contains unresolved structural errors, stop and document them. Otherwise run:

```text
python exploration/03_factor_baseline.py \
  --price-path D:\data\vietnam-quant-research\bronze\price_daily.jsonl \
  --output D:\data\vietnam-quant-research\reports\factor_baseline.csv \
  --oos-fraction 0.3 \
  --cost-bps 0,50,100
```

Review that results include IS/OOS, costs, turnover, exclusions, and blocked_missing_market_cap for size when applicable.

- [ ] Step 5: Update project documentation

Add docs/daily-data-loop-v0.md with the pilot timestamp, source coverage, row counts, unresolved quality issues, commands, output locations, and the decision whether 2050-symbol scaling is allowed. Update README and existing audit/stack docs so next step points to the implemented pipeline and states that results are provisional.

- [ ] Step 6: Run final acceptance checks and commit

Run:

```text
git status --short
git diff --check
git ls-files
python -m pytest -q
```

Verify that tracked files contain no .env, key, token, CSV, Parquet, JSONL, raw snapshot, or external report. Commit on branch codex/daily-loop-pilot-report:

```text
git add README.md docs/daily-data-loop-v0.md docs/exploration-data-audit.md docs/recommended-data-stack.md tests/test_cli_contracts.py
git commit -m "docs: record daily data loop pilot"
```

Push, open PR, merge after checks, remove the branch/worktree, and verify a clean main.


