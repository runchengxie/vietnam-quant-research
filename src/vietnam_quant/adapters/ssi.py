"""SSI credential boundary; no data is fetched without explicit credentials."""

from __future__ import annotations

import os
from datetime import date
from typing import Any

from vietnam_quant.schemas import CredentialStatus, FetchResult, InstrumentRecord, PriceDailyRecord


class SSIAdapter:
    source_name = "ssi"

    def check_credentials(self) -> CredentialStatus:
        if not os.environ.get("SSI_API_KEY") or not os.environ.get("SSI_SECRET"):
            return CredentialStatus(source="ssi", status="skipped_missing_credentials", detail="SSI_API_KEY and SSI_SECRET are required")
        return CredentialStatus(source="ssi", status="credentials_present")

    def fetch_listing(self) -> FetchResult:
        status = self.check_credentials()
        return FetchResult(status=status.status, endpoint="ssi://listing", error_type=None if status.status == "credentials_present" else "missing_credentials", error_message=status.detail)

    def fetch_daily(self, symbol: str, end_date: date, count_back: int) -> FetchResult:
        status = self.check_credentials()
        return FetchResult(status=status.status, endpoint="ssi://daily", error_type=None if status.status == "credentials_present" else "missing_credentials", error_message=status.detail)

    def parse_listing(self, payload: Any) -> list[InstrumentRecord]:
        return []

    def parse_daily(self, payload: Any, symbol: str, requested_start: date, requested_end: date) -> list[PriceDailyRecord]:
        return []
