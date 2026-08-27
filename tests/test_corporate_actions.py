from datetime import date

import pytest

from vietnam_quant.corporate_actions import parse_corporate_action_events
from vietnam_quant.corporate_actions import write_corporate_action_events
from vietnam_quant.storage import ExternalDataStore


def test_parse_corporate_actions_keeps_apg_and_a32_dates_and_source_kinds(load_fixture):
    events = parse_corporate_action_events(load_fixture("corporate_actions_apg_a32.json"))

    assert [event.symbol for event in events] == ["APG", "A32", "A32", "APG"]
    assert events[0].record_date == date(2021, 6, 22)
    assert events[0].listing_date == date(2021, 9, 9)
    assert events[0].source_kind == "official"
    assert events[1].ex_date == date(2019, 6, 6)
    assert events[1].record_date == date(2019, 6, 7)
    assert events[1].payment_date == date(2019, 6, 20)
    assert events[1].cash_amount_per_share == 700.0
    assert events[1].source_kind == "secondary_discovery"
    assert events[2].ex_date == date(2020, 6, 1)
    assert events[2].record_date == date(2020, 6, 2)
    assert events[2].payment_date == date(2020, 6, 16)
    assert events[3].listing_date == date(2024, 8, 23)
    assert events[3].source_kind == "official"


def test_parse_corporate_actions_rejects_duplicate_event_ids():
    payload = [
        {
            "event_id": "duplicate",
            "symbol": "APG",
            "event_type": "cash_dividend",
            "ex_date": "2024-01-02",
            "source_url": "https://example.test/event",
            "confidence": "low",
        },
        {
            "event_id": "duplicate",
            "symbol": "APG",
            "event_type": "cash_dividend",
            "ex_date": "2024-01-03",
            "source_url": "https://example.test/event-2",
            "confidence": "low",
        },
    ]

    with pytest.raises(ValueError, match="duplicate event_id"):
        parse_corporate_action_events(payload)


def test_parse_corporate_actions_requires_confidence():
    payload = {
        "symbol": "APG",
        "event_type": "cash_dividend",
        "ex_date": "2024-01-02",
        "source_url": "https://example.test/event",
    }

    with pytest.raises(ValueError, match="confidence"):
        parse_corporate_action_events([payload])


def test_parse_corporate_actions_accepts_announcement_date_as_only_known_date():
    events = parse_corporate_action_events(
        [
            {
                "symbol": "APG",
                "event_type": "announced_action",
                "announcement_date": "2024-01-02",
                "source_url": "https://example.test/event",
                "confidence": "low",
            }
        ]
    )

    assert events[0].announcement_date == date(2024, 1, 2)
    assert events[0].event_id.startswith("APG:2024-01-02:announced_action")


@pytest.mark.parametrize(
    "invalid_row, message",
    [
        ({"symbol": "APG", "event_type": "cash_dividend", "ex_date": "2024-01-02"}, "source_url"),
        ({"event_type": "cash_dividend", "ex_date": "2024-01-02", "source_url": "https://example.test"}, "symbol"),
        ({"symbol": "APG", "event_type": "cash_dividend", "source_url": "https://example.test", "confidence": "low"}, "event date"),
    ],
)
def test_parse_corporate_actions_rejects_incomplete_rows(invalid_row, message):
    with pytest.raises(ValueError, match=message):
        parse_corporate_action_events([invalid_row])


def test_write_corporate_action_events_is_idempotent(tmp_path, load_fixture):
    events = parse_corporate_action_events(load_fixture("corporate_actions_apg_a32.json"))
    store = ExternalDataStore(tmp_path)

    relative_path = write_corporate_action_events(store, events)
    write_corporate_action_events(store, events)

    assert relative_path.as_posix() == "metadata/corporate_action_events.jsonl"
    assert len(store.read_jsonl(relative_path)) == 4
