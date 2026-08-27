# Daily data contracts

The v0 pipeline stores three linked record families: `instrument_master`,
`price_daily`, and `source_observations`. Raw API responses remain outside the
repository under the configured external data root.

## `instrument_master`

`InstrumentRecord` keeps the source exchange value in `exchange_raw` and the
normalized value in `exchange`. The normalizer maps `HSX` to `HOSE` and keeps
`DELISTED` as `DELISTED`; it never invents a current exchange for a delisted
instrument. `valid_from`, `valid_to`, `listing_date`, and `delisting_date` are
nullable because a current listing response cannot prove historical validity.

## `price_daily`

`PriceDailyRecord` stores raw and normalized price fields together. The VCI and
KBS historical OHLC endpoints expose price values in VND; the adapter preserves
those values in both raw and normalized fields and sets both units to `VND`.
There is no unit-conversion quality flag. Volume is preserved in source units
and labeled `shares_or_source_units` until a source-specific volume contract is
verified.

The VND unit does not establish whether a provider's historical series is raw,
adjusted, or otherwise revised. That price-semantics question remains an
explicit unresolved quality dimension and must be confirmed before factor
research uses long-horizon returns.

`PriceDailyRecord.adjusted_close` is an optional separate field for a source
that explicitly supplies an adjusted close, such as SSI's
`ClosePriceAdjusted`. It never overwrites `raw_close` or
`normalized_close`. `price_semantics` records the field boundary, not a claim
that the provider's adjustment methodology has been independently confirmed.

The parser performs inclusive date cropping after timestamp normalization. KBS
responses are sorted ascending before output. No row is silently deleted: missing
fields, duplicate dates, invalid OHLC relations, negative values, zero volume,
source reordering, and boundary-price proxies are quality flags.

## `source_observations`

`SourceObservation` records endpoint, request parameters, retrieval time, HTTP
status, latency, raw snapshot path, SHA-256, row count, parser/schema versions,
and quality/error status. The snapshot path and hash refer to the external data
root; complete raw market data is not committed to Git.

## Quality semantics

- `invalid_ohlc` and `missing_required` are structural failures and are excluded
  from the default factor stage.
- `zero_volume` means no observed volume and is not filled or treated as normal
  trading.
- `boundary_price_proxy` is only a proxy when formal price limits are absent; it
  is not a claim that a confirmed limit event occurred.
- Reconciliation reports missing dates and close differences by source/date.

## `corporate_action_events`

`CorporateActionEvent` is the event evidence table used to explain price
regime changes and to build a future adjustment layer. It keeps
`announcement_date`, `ex_date`, `record_date`, `payment_date`, and
`listing_date` as separate nullable fields. The parser requires a symbol, an
event type, a source URL, an explicit confidence value, and at least one dated
event field. It rejects duplicate `event_id` values and does not infer missing
ratios or dates from price series. An announcement date can be the only known
date, but it does not become an ex-date, record date, payment date, or listing
date.

`write_corporate_action_events` appends these records idempotently to
`metadata/corporate_action_events.jsonl` in the external data root. The
repository fixture contains only small APG/A32 metadata examples and public
source links. It is not a replacement for a complete event history.

## `price_semantic_anchors`

`PriceSemanticAnchor` stores an independently sourced price point. The HNX
UPCoM parser currently emits exchange-displayed VND OHLC as
`semantic_label=exchange_raw`, with the source endpoint and observation ID
retained. An anchor is evidence for later reconciliation; it does not rewrite
VCI/KBS rows or decide which vendor series should be used for returns.

## `corporate_action_price_reconciliation`

`CorporateActionPriceReconciliation` is a read-only evidence record linking one
explicit company-action date to nearby source price bars. The report keeps all
event dates and labels the selected `reference_date_kind`: `ex_date` is used
when present, listing events may use `listing_date`, and an announcement-only
date is marked `announcement_date_reference_only`. `record_date` and
`payment_date` are never silently treated as an ex-date.

The offline command below reads bronze JSONL and a JSON/JSONL event file, then
writes these external-root metadata files:

```text
python exploration/04_event_price_reconciliation.py \
  --data-root D:\\data\\vietnam-quant-research\\pilot-v6 \
  --events-file tests\\fixtures\\corporate_actions_apg_a32.json
```

```text
metadata/corporate_action_price_reconciliation.jsonl
metadata/corporate_action_price_reconciliation.json
```

Each event report includes per-source bars, raw/normalized prices, volume,
quality flags, source observation IDs, pre/post descriptive returns, and a
cross-source difference summary. `matched`, `nearby`, `no_evidence`, and
`unresolved` describe evidence alignment only; they do not establish causality,
construct an adjustment factor, or change `price_semantics`/`factor_ready`.
