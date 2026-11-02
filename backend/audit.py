"""Append-only audit trail: output/audit_trail.json (a JSON list, never wiped)."""

from __future__ import annotations

import json
import threading
from datetime import datetime, timezone
from typing import Any

from pydantic_core import to_json

from config import AUDIT_PATH, AUDIT_TEXT_LIMIT

_lock = threading.Lock()


def _trim(value: Any) -> Any:
    text = value if isinstance(value, str) else to_json(value).decode("utf-8", "replace")
    if len(text) <= AUDIT_TEXT_LIMIT:
        return value if isinstance(value, (str, dict, list, int, float, bool, type(None))) else text
    return text[:AUDIT_TEXT_LIMIT] + f"... [trimmed, {len(text)} chars total]"


def record(run_id: str, ticket_id: int | None, agent: str | None, event: str, **details: Any) -> None:
    """Add one entry to the end of the audit trail."""
    entry = {
        "time_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "run_id": run_id,
        "ticket_id": ticket_id,
        "agent": agent,
        "event": event,
        **{k: _trim(v) for k, v in details.items()},
    }
    with _lock:
        AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
        entries: list = []
        if AUDIT_PATH.exists() and AUDIT_PATH.stat().st_size:
            entries = json.loads(AUDIT_PATH.read_text(encoding="utf-8"))
        entries.append(entry)
        AUDIT_PATH.write_text(json.dumps(entries, indent=1, default=str), encoding="utf-8")
