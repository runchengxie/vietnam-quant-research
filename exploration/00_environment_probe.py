"""Check whether the local audit dependencies are importable."""

from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
for candidate in (REPO_ROOT / ".audit_lib", REPO_ROOT / ".venv" / "Lib" / "site-packages"):
    if candidate.exists():
        sys.path.insert(0, str(candidate))


packages = {}
for name in ("pandas", "vnstock", "nbformat", "nbclient", "requests"):
    try:
        module = importlib.import_module(name)
        packages[name] = {
            "imported": True,
            "file": str(getattr(module, "__file__", "")),
            "version": str(getattr(module, "__version__", "unknown")),
        }
    except Exception as exc:  # noqa: BLE001 - probe should report all failures
        packages[name] = {"imported": False, "error": f"{type(exc).__name__}: {exc}"}


print(json.dumps(packages, ensure_ascii=False, indent=2))
