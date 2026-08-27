from datetime import date

from vietnam_quant.storage import ExternalDataStore


def test_store_raw_snapshot_returns_sha256_and_relative_path(tmp_path):
    store = ExternalDataStore(tmp_path)
    path, digest = store.write_raw("vci", "FPT", {"data": [1]}, run_date=date(2026, 8, 27))
    assert path == __import__("pathlib").Path("raw/vci/2026-08-27/FPT.json")
    assert len(digest) == 64
    assert (tmp_path / path).exists()


def test_append_jsonl_does_not_duplicate_observation(tmp_path):
    store = ExternalDataStore(tmp_path)
    record = {"observation_id": "one", "source": "vci"}
    store.append_jsonl("metadata/source_observations.jsonl", record, key="observation_id")
    store.append_jsonl("metadata/source_observations.jsonl", record, key="observation_id")
    assert len((tmp_path / "metadata/source_observations.jsonl").read_text().splitlines()) == 1


def test_store_jsonl_round_trips_records(tmp_path):
    store = ExternalDataStore(tmp_path)
    store.append_jsonl("bronze/price_daily.jsonl", {"symbol": "FPT"})
    assert store.read_jsonl("bronze/price_daily.jsonl") == [{"symbol": "FPT"}]
