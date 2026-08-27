"""Market-data source adapters and parser helpers."""
from typing import Any, Protocol
from datetime import date

from vietnam_quant.schemas import FetchResult, InstrumentRecord, PriceDailyRecord


class MarketDataAdapter(Protocol):
    source_name: str

    def fetch_listing(self) -> FetchResult: ...

    def fetch_daily(self, symbol: str, end_date: date, count_back: int) -> FetchResult: ...

    def parse_listing(self, payload: Any) -> list[InstrumentRecord]: ...

    def parse_daily(
        self,
        payload: Any,
        symbol: str,
        requested_start: date,
        requested_end: date,
    ) -> list[PriceDailyRecord]: ...
