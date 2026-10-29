# Copyright 2026 maxcode contributors
# SPDX-License-Identifier: Apache-2.0
"""Tests for git checkpoints."""

import subprocess
from pathlib import Path

from maxcode.checkpoints import (
    create,
    delete_ref,
    diff_stats,
    latest_ref,
    restore,
)


def init_repo(repo: Path) -> None:
    repo.mkdir()
    subprocess.run(["git", "init", "-q", "-b", "main"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, check=True)


def cached_diff(repo: Path) -> str:
    return subprocess.run(
        ["git", "diff", "--cached"],
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
    ).stdout


def test_create_and_restore(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    init_repo(repo)
    tracked = repo / "tracked.txt"
    tracked.write_text("before\n", encoding="utf-8")
    subprocess.run(["git", "add", "tracked.txt"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "initial"], cwd=repo, check=True)

    before_diff = cached_diff(repo)
    tracked.write_text("changed\n", encoding="utf-8")
    (repo / "untracked.txt").write_text("new\n", encoding="utf-8")

    ref = create("run1", 1, repo)
    assert ref == "refs/maxcode/run1/1"

    tracked.write_text("after\n", encoding="utf-8")
    (repo / "untracked.txt").write_text("after-new\n", encoding="utf-8")
    (repo / "extra.txt").write_text("extra\n", encoding="utf-8")

    restore(ref, repo)
    assert tracked.read_text(encoding="utf-8") == "changed\n"
    assert (repo / "untracked.txt").read_text(encoding="utf-8") == "new\n"
    assert not (repo / "extra.txt").exists()
    assert cached_diff(repo) == before_diff


def test_restore_rejects_non_git(tmp_path: Path) -> None:
    from maxcode.errors import NotAGitRepo

    with __import__("pytest").raises(NotAGitRepo):
        create("run1", 1, tmp_path)


def test_latest_ref_and_delete(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    init_repo(repo)
    (repo / "a.txt").write_text("a\n", encoding="utf-8")
    subprocess.run(["git", "add", "a.txt"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "initial"], cwd=repo, check=True)
    ref = create("run2", 1, repo)
    assert latest_ref(repo) == ref
    delete_ref(ref, repo)
    assert latest_ref(repo) is None


def test_diff_stats_counts_working_tree_changes(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    init_repo(repo)
    (repo / "a.txt").write_text("one\ntwo\n", encoding="utf-8")
    subprocess.run(["git", "add", "a.txt"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "initial"], cwd=repo, check=True)
    ref = create("run3", 1, repo)
    (repo / "a.txt").write_text("one\ntwo\nthree\n", encoding="utf-8")
    (repo / "b.txt").write_text("new\n", encoding="utf-8")
    files, lines = diff_stats(ref, repo)
    assert "a.txt" in files
    assert "b.txt" in files
    assert lines == 2
