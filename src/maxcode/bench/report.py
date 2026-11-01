# Copyright 2026 maxcode contributors
# SPDX-License-Identifier: Apache-2.0
"""Read benchmark logs and print a summary table."""

import argparse
import csv
from collections import defaultdict
from pathlib import Path


def summarize(results_dirs: list[Path]) -> str:
    """Return a markdown table summarising benchmark runs."""
    groups: dict[str, dict[str, float]] = defaultdict(
        lambda: {"tasks": 0, "passed": 0, "cost": 0.0, "unverified": 0}
    )
    invalid: list[tuple[str, str]] = []
    for directory in results_dirs:
        csv_path = directory / "results.csv"
        if not csv_path.is_file():
            continue
        with csv_path.open(newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                status = row.get("status", "")
                if status == "invalid":
                    reason = row.get("excluded_reason") or "baseline passed"
                    invalid.append((row.get("task", ""), reason))
                    continue
                verifier = row.get("verifier", "on")
                group = groups[verifier]
                group["tasks"] += 1
                if status:
                    if status == "pass":
                        group["passed"] += 1
                elif row.get("score_passed") == "True":
                    group["passed"] += 1
                group["cost"] += float(row.get("cost_usd") or 0.0)
                group["unverified"] += int(row.get("unverified") or 0)
    header = "| verifier | tasks | pass rate | cost per completed task | unverified |"
    divider = "|---|---:|---:|---:|---:|"
    lines = [header, divider]
    for verifier in sorted(groups):
        data = groups[verifier]
        tasks = int(data["tasks"])
        passed = int(data["passed"])
        rate = (passed / tasks * 100) if tasks else 0.0
        completed = passed if passed else 1
        cost_per = data["cost"] / completed
        lines.append(
            f"| {verifier} | {tasks} | {rate:.1f}% | ${cost_per:.4f} | "
            f"{int(data['unverified'])} |"
        )
    if len(lines) == 2:
        lines.append("| (no data) | 0 | 0.0% | $0.0000 | 0 |")
    if invalid:
        lines.append("")
        lines.append("Excluded from N (baseline passed):")
        for task, reason in invalid:
            lines.append(f"- {task}: {reason}")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Summarise maxcode benchmark runs.")
    parser.add_argument(
        "directory", nargs="?", default=".maxcode/bench", help="Benchmark output directory"
    )
    args = parser.parse_args()
    root = Path(args.directory)
    directories = [p.parent for p in root.rglob("results.csv")]
    if not directories:
        directories = [root]
    print(summarize(directories))


if __name__ == "__main__":
    main()
