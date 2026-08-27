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

`PriceDailyRecord` stores raw and normalized price fields together. VCI and KBS
observations are currently treated as `thousand_vnd`; normalized prices are
stored as VND by multiplying by 1,000. The conversion is recorded with the
`unit_converted_thousand_vnd` quality flag. Volume is preserved in source units
and labeled `shares_or_source_units` until a source-specific volume contract is
verified.

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
