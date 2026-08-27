from datetime import date

import pytest

from vietnam_quant.event_price import (
    reconcile_corporate_action_prices,
    select_event_reference_date,
)
from vietnam_quant.schemas import CorporateActionEvent, PriceDailyRecord


def make_event(**overrides):
    values = {
        "event_id": "event-1",
        "symbol": "A32",
        "event_type": "cash_dividend",
        "source_url": "https://example.test/event",
        "confidence": "high",
    }
    values.update(overrides)
    return CorporateActionEvent(**values)


def test_select_event_reference_date_prefers_explicit_ex_date():
    event = make_event(
        ex_date=date(2020, 6, 1),
        record_date=date(2020, 6, 2),
        payment_date=date(2020, 6, 16),
    )

    assert select_event_reference_date(event) == (date(2020, 6, 1), "ex_date")


def test_select_event_reference_date_uses_listing_date_for_new_shares():
    event = make_event(
        event_type="employee_share_listing",
        listing_date=date(2024, 8, 23),
        payment_date=date(2024, 8, 30),
    )

    assert select_event_reference_date(event) == (date(2024, 8, 23), "listing_date")


def test_select_event_reference_date_uses_listing_date_for_stock_rights_issue():
    event = make_event(
        event_type="stock_dividend_and_rights_issue",
        listing_date=date(2021, 9, 9),
        record_date=date(2021, 6, 22),
    )

    assert select_event_reference_date(event) == (date(2021, 9, 9), "listing_date")


def test_select_event_reference_date_marks_announcement_only_as_reference_only():
    event = make_event(
        announcement_date=date(2024, 1, 2),
        record_date=date(2024, 1, 5),
        payment_date=date(2024, 1, 10),
    )

    assert select_event_reference_date(event) == (
        date(2024, 1, 2),
        "announcement_date_reference_only",
    )


@pytest.mark.parametrize(
    "event_kwargs",
    [
        {"record_date": date(2024, 1, 5)},
        {"payment_date": date(2024, 1, 10)},
        {"record_date": date(2024, 1, 5), "payment_date": date(2024, 1, 10)},
    ],
)
def test_select_event_reference_date_never_uses_record_or_payment_date(event_kwargs):
    assert select_event_reference_date(make_event(**event_kwargs)) == (None, "none")


def make_price_row(symbol, source, day, close, *, volume=100.0, quality_flags=None):
    return PriceDailyRecord(
        symbol=symbol,
        trading_date=day,
        source=source,
        raw_open=close,
        raw_high=close,
        raw_low=close,
        raw_close=close,
        raw_volume=volume,
        normalized_open=close,
        normalized_high=close,
        normalized_low=close,
        normalized_close=close,
        quality_flags=list(quality_flags or []),
        source_observation_id=f"{source}:{symbol}:observation",
    )


def make_window_rows(symbol="A32", source="vci", start=1, end=15, offset=0.0):
    return [
        make_price_row(
            symbol,
            source,
            date(2024, 1, day),
            float(day) + offset,
        )
        for day in range(start, end + 1)
    ]


def test_reconciliation_keeps_source_windows_and_quality_evidence():
    event = make_event(event_id="event-window", ex_date=date(2024, 1, 8))
    vci_rows = make_window_rows(source="vci")
    kbs_rows = make_window_rows(source="kbs")
    vci_rows[2] = make_price_row(
        "A32",
        "vci",
        date(2024, 1, 3),
        3.0,
        volume=0.0,
        quality_flags=["zero_volume", "invalid_ohlc"],
    )
    original_flags = list(vci_rows[2].quality_flags)

    reports = reconcile_corporate_action_prices([event], [*vci_rows, *kbs_rows])

    report = reports[0]
    vci_evidence = report.source_evidence["vci"]
    assert report.assessment == "unresolved"
    assert report.reference_date == date(2024, 1, 8)
    assert report.reference_date_kind == "ex_date"
    assert [bar["trading_date"] for bar in vci_evidence["bars"]] == [
        date(2024, 1, day) for day in range(3, 14)
    ]
    assert vci_evidence["available_bar_count"] == 11
    assert vci_evidence["zero_volume_count"] == 1
    assert vci_evidence["invalid_ohlc_count"] == 1
    assert vci_evidence["bars"][0]["source_observation_id"] == "vci:A32:observation"
    assert vci_evidence["bars"][0]["raw_close"] == 3.0
    assert vci_rows[2].quality_flags == original_flags


def test_reconciliation_marks_nontrading_event_date_as_nearby():
    event = make_event(event_id="event-nearby", ex_date=date(2024, 1, 8))
    rows = make_window_rows(end=15)
    rows = [row for row in rows if row.trading_date != date(2024, 1, 8)]

    report = reconcile_corporate_action_prices([event], rows)[0]

    assert report.assessment == "nearby"
    assert report.source_evidence["vci"]["reference_date_present"] is False
    assert report.source_evidence["vci"]["pre_close"] == 7.0
    assert report.source_evidence["vci"]["post_close"] == 9.0


def test_reconciliation_reports_no_evidence_without_fabricating_bars():
    event = make_event(event_id="event-empty", ex_date=date(2025, 1, 8))

    report = reconcile_corporate_action_prices(
        [event], make_window_rows(end=15)
    )[0]

    assert report.assessment == "no_evidence"
    assert report.source_evidence["vci"]["available_bar_count"] == 5
    assert all(
        bar["trading_date"] < date(2025, 1, 8)
        for bar in report.source_evidence["vci"]["bars"]
    )
    assert report.source_evidence["vci"]["reference_date_present"] is False


def test_reconciliation_marks_cross_source_close_differences_unresolved():
    event = make_event(event_id="event-difference", ex_date=date(2024, 1, 8))
    rows = [*make_window_rows(source="vci"), *make_window_rows(source="kbs", offset=10.0)]

    report = reconcile_corporate_action_prices([event], rows)[0]

    assert report.assessment == "unresolved"
    assert report.cross_source["common_date_count"] == 11
    assert report.cross_source["close_difference_count"] == 11
    assert report.cross_source["relative_difference_max"] > 0
