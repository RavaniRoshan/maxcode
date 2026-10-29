# Copyright 2026 maxcode contributors
# SPDX-License-Identifier: Apache-2.0
"""Save and restore the working tree using temporary git refs."""

import os
import subprocess
from pathlib import Path

from maxcode.errors import CheckpointError, NotAGitRepo

MAXCODE_REF_PREFIX = "refs/maxcode/"
AUTHOR_NAME = "maxcode"
AUTHOR_EMAIL = "maxcode@localhost"


GitResult = subprocess.CompletedProcess[str]


def _run(args: list[str], repo: Path, env: dict[str, str], *, check: bool = True) -> GitResult:
    result = subprocess.run(
        ["git", *args],
        cwd=repo,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    if check and result.returncode != 0:
        raise CheckpointError(
            f"Git command failed: {' '.join(args)}.",
            (result.stderr or result.stdout or "").strip(),
            "Check the repository state and the checkpoint ref, then retry.",
        )
    return result


def _temp_index() -> Path:
    import tempfile

    fd, name = tempfile.mkstemp(prefix="maxcode-index-", suffix=".lock")
    os.close(fd)
    path = Path(name)
    path.unlink(missing_ok=True)
    return path


def _git_env(repo: Path, index_path: Path) -> dict[str, str]:
    env = os.environ.copy()
    env["GIT_INDEX_FILE"] = str(index_path)
    env["GIT_AUTHOR_NAME"] = AUTHOR_NAME
    env["GIT_AUTHOR_EMAIL"] = AUTHOR_EMAIL
    env["GIT_COMMITTER_NAME"] = AUTHOR_NAME
    env["GIT_COMMITTER_EMAIL"] = AUTHOR_EMAIL
    return env


def is_git_repo(repo: str | Path) -> bool:
    """Return true when the path is inside a git work tree."""
    root = Path(repo)
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        return False
    return result.returncode == 0 and result.stdout.strip() == "true"


def repo_head(repo: str | Path) -> str:
    """Return the current HEAD commit, or an empty string for an unborn branch."""
    root = Path(repo)
    result = subprocess.run(
        ["git", "rev-parse", "--verify", "HEAD^{commit}"],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    return result.stdout.strip() if result.returncode == 0 else ""


def _ensure_git(repo: Path) -> None:
    if not is_git_repo(repo):
        raise NotAGitRepo(
            f"'{repo}' is not a git repository.",
            "maxcode needs a git repository to create checkpoints.",
            "Run 'git init' in the project directory, then run the command again.",
        )


def _read_head_commit(repo: Path, env: dict[str, str]) -> str:
    result = subprocess.run(
        ["git", "rev-parse", "--verify", "HEAD^{commit}"],
        cwd=repo,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    return result.stdout.strip() if result.returncode == 0 else ""


def create(run_id: str, step_id: int, repo: str | Path = ".") -> str:
    """Save the working tree as a commit under refs/maxcode/ and return its ref."""
    root = Path(repo).resolve()
    _ensure_git(root)
    index_path = _temp_index()
    env = _git_env(root, index_path)
    try:
        head = _read_head_commit(root, env)
        if head:
            _run(["read-tree", head], root, env)
        else:
            _run(["read-tree", "--empty"], root, env)
        _run(["add", "-A"], root, env)
        tree = _run(["write-tree"], root, env).stdout.strip()
        if not tree:
            raise CheckpointError(
                "Could not write the checkpoint tree.",
                "git write-tree returned no value.",
                "Check the repository state, then retry.",
            )
        commit_args = ["commit-tree", tree]
        if head:
            commit_args += ["-p", head]
        commit_args += ["-m", f"maxcode checkpoint {run_id}/{step_id}"]
        commit = _run(commit_args, root, env).stdout.strip()
        ref = f"{MAXCODE_REF_PREFIX}{run_id}/{step_id}"
        _run(["update-ref", ref, commit], root, env)
        return ref
    finally:
        index_path.unlink(missing_ok=True)


def _ref_files(root: Path, ref: str) -> set[str]:
    result = _run(
        ["ls-tree", "-r", "--name-only", ref],
        root,
        os.environ.copy(),
        check=True,
    )
    return {line for line in result.stdout.splitlines() if line.strip()}


def _current_files(root: Path) -> set[str]:
    result = subprocess.run(
        ["git", "ls-files", "-co", "--exclude-standard"],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return set()
    return {line for line in result.stdout.splitlines() if line.strip()}


def _prune_empty_dirs(root: Path, removed: set[str]) -> None:
    parents = {Path(name).parent for name in removed}
    for parent in sorted(parents, key=lambda item: len(item.parts), reverse=True):
        if parent == Path("."):
            continue
        current = root / parent
        while current != root and current.exists():
            try:
                current.rmdir()
            except OSError:
                break
            current = current.parent


def restore(ref: str, repo: str | Path = ".") -> None:
    """Restore tracked and untracked files to the state saved in ref."""
    root = Path(repo).resolve()
    _ensure_git(root)
    index_path = _temp_index()
    env = _git_env(root, index_path)
    try:
        _run(["read-tree", ref], root, env)
        _run(["checkout-index", "-a", "-f"], root, env)
        before = _ref_files(root, ref)
        after = _current_files(root)
        extras = after - before
        for name in extras:
            target = root / name
            try:
                if target.is_file() or target.is_symlink():
                    target.unlink()
            except OSError:
                pass
        _prune_empty_dirs(root, extras)
    finally:
        index_path.unlink(missing_ok=True)


def latest_ref(repo: str | Path = ".") -> str | None:
    """Return the most recently created checkpoint ref, if any."""
    root = Path(repo).resolve()
    if not is_git_repo(root):
        return None
    result = subprocess.run(
        ["git", "for-each-ref", "--sort=-creatordate", "--format=%(refname)", "refs/maxcode"],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    lines = [line for line in result.stdout.splitlines() if line.strip()]
    return lines[0] if lines else None


def delete_ref(ref: str, repo: str | Path = ".") -> None:
    """Delete a checkpoint ref after it has been restored."""
    root = Path(repo).resolve()
    _ensure_git(root)
    _run(["update-ref", "-d", ref], root, os.environ.copy(), check=True)


def list_refs(repo: str | Path = ".") -> list[str]:
    """List all checkpoint refs in the repository."""
    root = Path(repo).resolve()
    if not is_git_repo(root):
        return []
    result = subprocess.run(
        ["git", "for-each-ref", "--format=%(refname)", "refs/maxcode"],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    return [line for line in result.stdout.splitlines() if line.strip()]


def diff_stats(ref: str, repo: str | Path = ".") -> tuple[list[str], int]:
    """Return changed files and added plus removed lines since ref."""
    root = Path(repo).resolve()
    _ensure_git(root)
    index_path = _temp_index()
    env = _git_env(root, index_path)
    try:
        _run(["read-tree", ref], root, env)
        _run(["add", "-A"], root, env)
        numstat = _run(["diff", "--cached", "--numstat", ref], root, env).stdout
        name_status = _run(["diff", "--cached", "--name-only", ref], root, env).stdout
        changed_files = [line for line in name_status.splitlines() if line.strip()]
        total_lines = 0
        for line in numstat.splitlines():
            parts = line.split()
            if len(parts) < 2:
                continue
            added, removed = parts[0], parts[1]
            if added.isdigit():
                total_lines += int(added)
            if removed.isdigit():
                total_lines += int(removed)
        return changed_files, total_lines
    finally:
        index_path.unlink(missing_ok=True)
