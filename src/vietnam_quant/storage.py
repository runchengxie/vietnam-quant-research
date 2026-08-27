"""Atomic, external-root storage for raw snapshots and metadata."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from datetime import date
from pathlib import Path
from typing import Any, Iterable


class ExternalDataStore:
    def __init__(self, data_root: Path | str):
        self.data_root = Path(data_root).expanduser()
        self.data_root.mkdir(parents=True, exist_ok=True)

    def _resolve(self, relative_path: Path | str) -> tuple[Path, Path]:
        relative = Path(relative_path)
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError("storage paths must be relative to data_root")
        return relative, self.data_root / relative

    def _write_atomic(self, relative_path: Path | str, payload: bytes) -> Path:
        relative, destination = self._resolve(relative_path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        fd, temporary_name = tempfile.mkstemp(prefix=f".{destination.name}.", dir=destination.parent)
        try:
            with os.fdopen(fd, "wb") as handle:
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
            Path(temporary_name).replace(destination)
        except BaseException:
            try:
                Path(temporary_name).unlink(missing_ok=True)
            finally:
                raise
        return relative

    @staticmethod
    def _json_bytes(payload: Any) -> bytes:
        return (json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")

    def write_raw(self, source: str, symbol: str, payload: Any, run_date: date) -> tuple[Path, str]:
        relative = Path("raw") / source / run_date.isoformat() / f"{symbol.upper()}.json"
        payload_bytes = self._json_bytes(payload)
        written = self._write_atomic(relative, payload_bytes)
        return written, hashlib.sha256(payload_bytes).hexdigest()

    def write_json(self, relative_path: Path | str, payload: Any) -> Path:
        return self._write_atomic(relative_path, self._json_bytes(payload))

    def read_jsonl(self, relative_path: Path | str) -> list[dict[str, Any]]:
        _, path = self._resolve(relative_path)
        if not path.exists():
            return []
        records: list[dict[str, Any]] = []
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                value = json.loads(line)
                if not isinstance(value, dict):
                    raise ValueError(f"JSONL record must be an object: {relative_path}")
                records.append(value)
        return records

    def append_jsonl(self, relative_path: Path | str, record: dict[str, Any], key: str | None = None) -> Path:
        records = self.read_jsonl(relative_path)
        if key is not None and any(existing.get(key) == record.get(key) for existing in records):
            return Path(relative_path)
        records.append(record)
        payload = "".join(json.dumps(item, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n" for item in records).encode("utf-8")
        return self._write_atomic(relative_path, payload)

    def ensure_layout(self) -> None:
        for relative in ("raw", "bronze", "metadata", "logs", "reports"):
            (self.data_root / relative).mkdir(parents=True, exist_ok=True)
