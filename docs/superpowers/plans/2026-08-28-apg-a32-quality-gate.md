# APG/A32 Quality Gate Recovery Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Diagnose the APG/A32 pilot failures, replenish only the missing evidence in the external data root, and produce a reproducible 50-stock raw/research quality-gate decision without committing runtime data.

**Architecture:** Treat the existing pipeline as the source of truth for fetching, raw snapshots, source observations, arbitration, and quality reports. First inspect the existing pilot metadata and raw snapshots; then rerun the smallest safe recovery scope—APG/A32 if the current sample and date range are unchanged, otherwise the complete fixed 50-stock sample—before comparing row counts, failure states, anomalies, cross-source reconciliation, and `factor_ready` status. Any code change must remain offline-testable and isolated from external runtime data.

**Tech Stack:** Python 3.11, pandas, requests, pytest, JSONL metadata, PowerShell, external data root `D:\data\vietnam-quant-research\pilot-v2` when present.

**Spec:** `docs/daily-data-loop-v0.md`, `docs/exploration-data-audit.md`, `AGENTS.md`, and the user-approved recovery sequence.

## Global Constraints

- Never commit raw API payloads, bronze/derived runtime data, credentials, or commercial data.
- Preserve raw source rows and failed observations; do not silently delete, fill, or overwrite anomalies.
- Keep `research_eligible`, `tradable`, raw/normalized/adjusted price fields, and source observations explicit.
- Do not treat a successful HTTP fetch as a passed quality gate; report structural OHLC, zero-volume, date coverage, source disagreement, and price-semantics status separately.
- Do not run the factor baseline or claim Alpha until the raw gate, research gate, and price-semantics requirements are satisfied.
- If the external data root, credentials, or network endpoint is unavailable, document the blocker and retain the existing pilot unchanged.

---

### Task 1: Inspect the existing pilot and verify the recovery scope

**Files:**
- Read: `docs/daily-data-loop-v0.md`
- Read: `docs/exploration-data-audit.md`
- Read: external `D:\data\vietnam-quant-research\pilot-v2\metadata\*.json` when present

**Interfaces:**
- Consumes: existing `quality_report.json`, `reconciliation_report.json`, `source_observations.jsonl`, `research_quality_report.json`, and `instrument_master.jsonl`.
- Produces: a documented recovery scope with fixed sample symbols, date range, source configuration, and a before/after evidence checklist.

- [ ] **Step 1: Read current metadata without modifying it**

```powershell
Get-ChildItem D:\data\vietnam-quant-research\pilot-v2\metadata
Get-Content D:\data\vietnam-quant-research\pilot-v2\metadata\quality_report.json
Get-Content D:\data\vietnam-quant-research\pilot-v2\metadata\research_quality_report.json
```

- [ ] **Step 2: Confirm APG/A32 failure observations and sample membership**

```powershell
Select-String -Path D:\data\vietnam-quant-research\pilot-v2\metadata\source_observations.jsonl -Pattern 'APG|A32|timeout|FAIL'
Select-String -Path D:\data\vietnam-quant-research\pilot-v2\bronze\instrument_master.jsonl -Pattern 'APG|A32'
```

- [ ] **Step 3: Record whether targeted recovery is safe**

Use targeted APG/A32 recovery only if the existing sample, source priority, date interval, parser version, and schema version are unchanged. Otherwise rerun the fixed 50-stock sample to avoid mixing incompatible batches. Do not change the sample selection silently.

### Task 2: Replenish APG/A32 in the external data root

**Files:**
- Read: `exploration/02_daily_data_pipeline.py`
- Read: `src/vietnam_quant/pipeline.py`
- Write outside repository: `D:\data\vietnam-quant-research\pilot-v2\raw`, `bronze`, `derived`, `metadata`

**Interfaces:**
- Consumes: the verified sample and source configuration from Task 1.
- Produces: new raw snapshots, source observations, parsed price rows, arbitration output, and quality reports with request time, response status, parser/schema versions, and hashes.

- [ ] **Step 1: Run the existing offline help and command contract**

```powershell
python exploration/02_daily_data_pipeline.py --help
```

- [ ] **Step 2: Run the smallest authorized network recovery**

Use the existing command shape and the verified fixed sample/date range. If the CLI cannot target APG/A32 without changing sample semantics, rerun all 50 selected stocks rather than inventing a one-off data path. Keep raw snapshots outside Git.

```powershell
python exploration/02_daily_data_pipeline.py `
  --network `
  --data-root D:\data\vietnam-quant-research\pilot-v2 `
  --start 2018-01-01 `
  --end 2026-08-27 `
  --sample-size 50 `
  --primary-source vci `
  --secondary-source kbs `
  --rate-limit-seconds 0.05 `
  --strict
```

- [ ] **Step 3: Preserve failed requests as evidence**

For APG/A32, verify the final observation records contain endpoint, request parameters, retrieval time, HTTP status, latency, raw snapshot path, SHA-256, row count, parser/schema versions, and error/quality status. Do not treat timeout recovery as proof that historical coverage is correct.

### Task 3: Re-run the 50-stock quality gate and diagnose remaining anomalies

**Files:**
- Read: external `quality_report.json`, `reconciliation_report.json`, `research_quality_report.json`, `price_semantics_report.json`
- Read: external `derived/research_price_daily.jsonl`
- Modify only if required: `docs/daily-data-loop-v0.md` or a new evidence note under `docs/`

**Interfaces:**
- Consumes: the replenished external data artifacts.
- Produces: a compact before/after quality decision with APG/A32 status, row-level OHLC anomaly examples, zero-volume counts, source disagreement counts, quarantine counts, missing-date counts, and `factor_ready` status.

- [ ] **Step 1: Compare gate dimensions by count and rate**

Check selected instruments, exchange coverage, source observation completion, duplicate identity keys, invalid OHLC, zero volume, research eligibility, tradability, cross-source missing dates, close differences, and unresolved price semantics.

- [ ] **Step 2: Inspect APG/A32 row-level anomalies**

For every remaining `invalid_ohlc`, `zero_volume`, `source_disagreement`, or quarantine record for APG/A32, retain the date and raw/normalized fields in the evidence output. Classify whether it is a source issue, a parser/unit issue, a corporate-action/adjustment issue, or a legitimate market state.

- [ ] **Step 3: Decide whether the 50-stock gate passes**

The gate passes only when the existing project requirements are met, including explicit source evidence, no unexplained structural price issues in factor inputs, auditable research eligibility, and independently confirmed price semantics. A recovered HTTP request alone is not sufficient.

### Task 4: Add offline regression coverage only for discovered code defects

**Files:**
- Test: `tests/test_pipeline.py` or the narrowest existing test module
- Modify: the exact production file implicated by Task 3

**Interfaces:**
- Consumes: a minimal fixture reproducing the observed APG/A32 or gate-report defect.
- Produces: a tested fix that preserves source evidence and does not couple tests to external data.

- [ ] **Step 1: Write a failing fixture test for the specific discovered defect**
- [ ] **Step 2: Run the targeted test and record the expected failure**
- [ ] **Step 3: Implement the minimal production fix**
- [ ] **Step 4: Run the targeted and full offline test suites**

If no code defect is found, leave production code unchanged and document that the recovery was data/runtime-only.

### Verification

```text
python -m pytest
python -m compileall -q src tests exploration
git diff --check
git status --short --branch
```

The final handoff must state whether APG/A32 recovered, whether the fixed 50-stock raw/research gate passed, whether `factor_ready` is true, and which unresolved issues still block factor research. No factor baseline runs until that decision is positive.
