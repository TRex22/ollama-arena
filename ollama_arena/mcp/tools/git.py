"""Git repository tools scoped to the arena workspace."""
from __future__ import annotations

import subprocess
from typing import Callable

from .workspace import WORKSPACE_DIR


def _git(args: list[str]) -> str:
    try:
        res = subprocess.run(
            ["git", *args],
            cwd=WORKSPACE_DIR,
            capture_output=True,
            text=True,
            timeout=30,
        )
        if res.returncode != 0:
            return f"Git error: {res.stderr.strip() or res.stdout.strip()}"
        return res.stdout.strip() or "OK"
    except Exception as exc:
        return f"Error: {exc}"


def git_status(args: dict) -> str:
    return _git(["status", "--short"])


def git_commit(args: dict) -> str:
    message = args.get("message", "")
    if not message:
        return "Error: commit message required."
    stage = _git(["add", "-A"])
    if stage.startswith("Git error") or stage.startswith("Error:"):
        return stage
    return _git(["commit", "-m", message])


def mock_git_commit(args: dict) -> str:
    # Pure fake - no subprocess, no real git repo touched. Benchmark tasks
    # only need to confirm the model called git_commit with the right
    # message, not that a real commit landed in some workspace dir.
    message = args.get("message", "")
    if not message:
        return "Error: commit message required."
    return f"[mock abc1234] {message}\n 1 file changed, 1 insertion(+)"


GIT_COMMIT_SCHEMA = {
    "type": "function",
    "function": {
        "name": "git_commit",
        "description": "Stage all changes and commit in the arena workspace.",
        "parameters": {
            "type": "object",
            "properties": {"message": {"type": "string"}},
            "required": ["message"],
        },
    },
}


def tool_defs(include_mock: bool = False) -> list[tuple[str, Callable[[dict], str], dict, str]]:
    defs: list[tuple[str, Callable[[dict], str], dict, str]] = [
        (
            "git_status",
            git_status,
            {
                "type": "function",
                "function": {
                    "name": "git_status",
                    "description": "Show git status in the arena workspace.",
                    "parameters": {"type": "object", "properties": {}},
                },
            },
            "safe",
        ),
    ]
    if include_mock:
        # Mock mode: no real subprocess/repo mutation - safe.
        defs.append(("git_commit", mock_git_commit, GIT_COMMIT_SCHEMA, "safe"))
    else:
        # Real mode: genuinely runs `git add -A && git commit`, correctly gated.
        defs.append(("git_commit", git_commit, GIT_COMMIT_SCHEMA, "confirm"))
    return defs
