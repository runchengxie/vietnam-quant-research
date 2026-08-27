"""Stable, serializable data contracts for the Vietnam daily data loop."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import date, datetime, timezone
from typing import Any

SCHEMA_VERSION = "daily-v0"


def _serialize(value: Any) -> Any:
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, list):
        return [_serialize(item) for item in value]
    if isinstance(value, dict):
        return {key: _serialize(item) for key, item in value.items()}
    return value


class SerializableMixin:
    def to_dict(self) -> dict[str, Any]:
        return _serialize(asdict(self))


@dataclass(frozen=True)
class InstrumentRecord(SerializableMixin):
    instrument_id: str
    symbol: str
    issuer_name: str | None = None
    exchange_raw: str | None = None
    exchange: str | None = None
    security_type: str | None = None
    listing_status: str = "observed_current"
    valid_from: date | None = None
    valid_to: date | None = None
    listing_date: date | None = None
    delisting_date: date | None = None
    selection_reason: str | None = None
    source: str = "unknown"
    retrieved_at_utc: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass(frozen=True)
class CorporateActionEvent(SerializableMixin):
    """One dated corporate-action observation with explicit provenance."""

    event_id: str
    symbol: str
    event_type: str
    source_url: str
    exchange: str | None = None
    announcement_date: date | None = None
    ex_date: date | None = None
    record_date: date | None = None
    payment_date: date | None = None
    listing_date: date | None = None
    cash_amount_per_share: float | None = None
    share_ratio: float | None = None
    rights_ratio: float | None = None
    source_kind: str = "secondary_discovery"
    confidence: str = "discovered"
    notes: str | None = None


@dataclass(frozen=True)
class RawPriceBar(SerializableMixin):
    symbol: str
    trading_date: date
    source: str
    event_time_raw: str
    raw_open: float | None
    raw_high: float | None
    raw_low: float | None
    raw_close: float | None
    raw_volume: float | None
    raw_price_unit: str = "unknown"
    event_time_utc: datetime | None = None
    exchange: str | None = None


@dataclass(frozen=True)
class PriceDailyRecord(SerializableMixin):
    symbol: str
    trading_date: date
    source: str
    event_time_raw: str = ""
    event_time_utc: datetime | None = None
    exchange: str | None = None
    raw_open: float | None = None
    raw_high: float | None = None
    raw_low: float | None = None
    raw_close: float | None = None
    raw_volume: float | None = None
    raw_price_unit: str = "unknown"
    normalized_open: float | None = None
    normalized_high: float | None = None
    normalized_low: float | None = None
    normalized_close: float | None = None
    normalized_price_unit: str = "VND"
    volume_unit: str | None = "unknown"
    quality_flags: list[str] = field(default_factory=list)
    source_observation_id: str = ""
    parser_version: str = "unknown"
    schema_version: str = SCHEMA_VERSION
    adjusted_close: float | None = None
    adjusted_price_unit: str | None = None
    price_semantics: str = "unknown"

    @property
    def tradable_quality(self) -> bool:
        return not bool({"missing_required", "invalid_ohlc", "duplicate_date"} & set(self.quality_flags))


@dataclass(frozen=True)
class PriceSemanticAnchor(SerializableMixin):
    """An independently sourced price point used to audit provider semantics."""

    anchor_id: str
    symbol: str
    exchange: str
    trading_date: date
    source: str
    source_endpoint: str
    raw_open: float | None = None
    raw_high: float | None = None
    raw_low: float | None = None
    raw_close: float | None = None
    raw_volume: float | None = None
    raw_price_unit: str = "VND"
    semantic_label: str = "exchange_raw"
    confidence: str = "high"
    source_observation_id: str = ""
    notes: str | None = None


@dataclass(frozen=True)
class ResearchPriceDailyRecord(PriceDailyRecord):
    research_status: str = "selected"
    arbitration_reason: str = "primary_valid"
    research_eligible: bool = True
    tradable: bool = True


@dataclass(frozen=True)
class SourceArbitrationReport(SerializableMixin):
    symbol: str
    primary_source: str
    secondary_source: str | None = None
    primary_row_count: int = 0
    secondary_row_count: int = 0
    selected_row_count: int = 0
    primary_selected_count: int = 0
    secondary_selected_count: int = 0
    fallback_count: int = 0
    quarantine_count: int = 0
    zero_volume_count: int = 0
    disagreement_count: int = 0
    missing_both_count: int = 0
    research_eligible_count: int = 0
    tradable_count: int = 0
    coverage_rate: float = 0.0
    tradable_rate: float = 0.0
    sample_disagreements: list[dict[str, Any]] = field(default_factory=list)


@dataclass(frozen=True)
class PriceSemanticsReport(SerializableMixin):
    symbol: str
    primary_source: str
    secondary_source: str | None = None
    status: str = "unresolved"
    matched_dates: int = 0
    difference_count: int = 0
    ratio_median: float | None = None
    ratio_p90: float | None = None
    ratio_max: float | None = None
    relative_difference_median: float | None = None
    relative_difference_p90: float | None = None
    relative_difference_max: float | None = None
    yearly: dict[str, dict[str, Any]] = field(default_factory=dict)


@dataclass(frozen=True)
class SourceObservation(SerializableMixin):
    observation_id: str
    source: str
    endpoint: str
    symbol: str | None = None
    request_parameters: dict[str, Any] = field(default_factory=dict)
    retrieved_at_utc: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    response_status: int | None = None
    latency_ms: float | None = None
    raw_snapshot_path: str | None = None
    raw_payload_sha256: str | None = None
    row_count: int = 0
    first_trading_date: date | None = None
    last_trading_date: date | None = None
    quality_status: str = "WARN"
    quality_issue_count: int = 0
    parser_version: str = "unknown"
    schema_version: str = SCHEMA_VERSION
    error_type: str | None = None
    error_message: str | None = None


@dataclass(frozen=True)
class FetchResult(SerializableMixin):
    status: str
    payload: Any = None
    response_status: int | None = None
    latency_ms: float | None = None
    request_parameters: dict[str, Any] = field(default_factory=dict)
    endpoint: str = ""
    error_type: str | None = None
    error_message: str | None = None
    attempts: int = 1


@dataclass(frozen=True)
class QualityReport(SerializableMixin):
    rows: list[PriceDailyRecord] = field(default_factory=list)
    issue_counts: dict[str, int] = field(default_factory=dict)
    issue_count: int = 0
    status: str = "PASS"


@dataclass(frozen=True)
class ReconciliationReport(SerializableMixin):
    missing_in_primary: list[str] = field(default_factory=list)
    missing_in_secondary: list[str] = field(default_factory=list)
    close_differences: list[dict[str, Any]] = field(default_factory=list)
    matched_dates: int = 0
    status: str = "PASS"


@dataclass(frozen=True)
class CredentialStatus(SerializableMixin):
    source: str
    status: str
    detail: str | None = None
