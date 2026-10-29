# Copyright 2026 maxcode contributors
# SPDX-License-Identifier: Apache-2.0
"""Tests for the benchmark report."""

import csv
from pathlib import Path

from maxcode.bench.report import summarize


def test_summarize_prints_table(tmp_path: Path) -> None:
    out = tmp_path / "run1"
    out.mkdir()
    with (out / "results.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            ["task", "repo_url", "commit", "verifier", "run_passed", "score_passed",
             "score_exit_code", "cost_usd", "tokens_in", "tokens_out", "unverified", "log", "error"]
        )
        writer.writerow(
            ["t1", "u", "c", "on", "True", "True", "0", "0.5", "10", "5", "0", "", ""]
        )
        writer.writerow(
            ["t2", "u", "c", "off", "False", "False", "1", "0.2", "4", "2", "1", "", ""]
        )
    table = summarize([out])
    assert "pass rate" in table
    assert "on" in table
    assert "off" in table
    assert "50.0%" in table or "100.0%" in table
