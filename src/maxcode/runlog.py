# Copyright 2026 maxcode contributors
# SPDX-License-Identifier: Apache-2.0
"""Append-only JSONL run log."""

import json
import secrets
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from maxcode.errors import RunLogError
from maxcode.schemas import RunEvent


def new_run_id() -> str:
    """Return a sortable, unique run id."""
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S")
    return f"{stamp}-{secrets.token_hex(3)}"


def _now() -> str:
    return datetime.now(UTC).isoformat()


class RunLog:
    """Write one JSON object per line and flush after each event."""

    def __init__(self, path: str | Path, run_id: str) -> None:
        self.path = Path(path)
        self.run_id = run_id

    def write(self, event_type: str, data: dict[str, Any]) -> None:
        """Append one event and flush it to disk."""
        event = RunEvent(ts=_now(), run_id=self.run_id, type=event_type, data=data)
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(event.model_dump(), ensure_ascii=False) + "\n")
                handle.flush()
        except OSError as exc:
            raise RunLogError(
                f"Could not write run log '{self.path}'.",
                str(exc),
                "Check disk space and permissions for the .maxcode directory.",
            ) from exc


def read_events(path: str | Path) -> list[RunEvent]:
    """Read and validate every event in a run log."""
    log_path = Path(path)
    events: list[RunEvent] = []
    try:
        lines = log_path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise RunLogError(
            f"Could not read run log '{log_path}'.",
            str(exc),
            "Check that the run id is correct and the file is readable.",
        ) from exc
    for number, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        try:
            events.append(RunEvent.model_validate(json.loads(line)))
        except (json.JSONDecodeError, ValidationError) as exc:
            raise RunLogError(
                f"Run log '{log_path}' is corrupt at line {number}.",
                str(exc),
                "Restore the log from a backup, or rerun the task to create a new log.",
            ) from exc
    return events
