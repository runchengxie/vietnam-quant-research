# Company Action Anchors Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add auditable corporate-action records, exchange-raw price anchors, and an explicit SSI raw/adjusted close contract without claiming unresolved VCI/KBS historical price semantics.

**Architecture:** Keep `raw` and existing `PriceDailyRecord` observations unchanged in meaning. Add small serializable evidence records beside them, parse offline fixtures through source-specific pure functions, and keep network adapters credential- or snapshot-bound. The new records are inputs to a later adjustment/research layer, not automatic price corrections.

**Tech Stack:** Python 3.11, frozen dataclasses, stdlib HTML parsing, JSON fixtures, pytest.

**Spec:** The approved design in the conversation, `docs/data-contracts.md`, and the existing research-view arbitration design.

## Global constraints

- Preserve raw snapshots and existing VCI/KBS bronze rows.
- Do not label VCI or KBS as raw or adjusted from cross-source similarity alone.
- Do not fetch SSI without explicit credentials and do not commit credentials or runtime data.
- Keep official exchange anchors separate from provider price observations.
- Use an isolated worktree and keep the change focused on evidence contracts and parsing boundaries.

## Tasks

- [ ] Add serializable `CorporateActionEvent` and `PriceSemanticAnchor` contracts, plus optional adjusted-close fields on `PriceDailyRecord`.
  - Add tests for date/source/semantic serialization and backward-compatible price-row construction.
  - Keep event dates separate: ex-date, record date, payment date, and listing date.

- [ ] Add a pure corporate-action parser and small APG/A32 metadata fixture.
  - Require symbol, event type, source URL, confidence, and at least one event date.
  - Reject duplicate event IDs and retain official versus secondary discovery provenance.

- [ ] Implement the SSI daily response parser as a raw-plus-adjusted boundary.
  - Parse raw OHLC/volume and `ClosePriceAdjusted` independently.
  - Crop inclusive requested dates and preserve missing adjusted close as `None`.
  - Keep `SSIAdapter` credential behavior unchanged and make its pure parser callable without network access.

- [ ] Implement an offline HNX UPCoM price-table parser and fixture.
  - Parse exchange-displayed VND OHLC as `exchange_raw` anchor data.
  - Preserve the source endpoint and avoid treating the web page as a complete corporate-action history.

- [ ] Update data-contract documentation and add a small evidence-layer usage note.
  - Explain that anchors and events enable later, auditable adjusted-price construction.
  - Record reusable validation conventions observed in `research-workspace`: formation-date shift, PIT alignment, OOS/walk-forward, market-rule constraints, transaction costs, and capacity checks.

- [ ] Run targeted tests, full pytest, compileall, and diff checks; inspect the final diff for secrets and runtime paths.

## Verification

```text
python -m pytest
python -m compileall -q src tests
git diff --check
```

The PR must report that no factor backtest was run and that VCI/KBS price semantics remain unresolved.
