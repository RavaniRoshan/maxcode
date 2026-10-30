#!/usr/bin/env python3
"""Fake engine executable used by engine tests."""

import json
import os
import sys
import time
from pathlib import Path

mode = os.environ.get("FAKE_ENGINE_MODE", "success")
repo = Path.cwd()
for index, value in enumerate(sys.argv):
    if value == "-C" and index + 1 < len(sys.argv):
        repo = Path(sys.argv[index + 1])
        break

if mode == "success":
    (repo / "hello.txt").write_text("hello from fake engine", encoding="utf-8")
    events = [
        {
            "type": "item.completed",
            "item": {"id": "msg_1", "type": "agent_message", "text": "editing"},
        },
        {
            "type": "item.completed",
            "item": {
                "id": "cmd_1",
                "type": "command_execution",
                "exit_code": 0,
                "status": "completed",
            },
        },
        {
            "type": "turn.completed",
            "usage": {
                "input_tokens": 7,
                "cached_input_tokens": 0,
                "cache_write_input_tokens": 0,
                "output_tokens": 3,
                "reasoning_output_tokens": 0,
            },
        },
    ]
    for event in events:
        print(json.dumps(event), flush=True)
    raise SystemExit(0)

if mode == "exit1":
    print(json.dumps({"type": "item.completed", "item": {"type": "agent_message", "text": "boom"}}))
    raise SystemExit(1)

if mode == "timeout":
    time.sleep(30)
    raise SystemExit(0)

if mode == "no_usage":
    print(json.dumps({"type": "item.completed", "item": {"type": "agent_message", "text": "done"}}))
    raise SystemExit(0)

raise SystemExit(2)
