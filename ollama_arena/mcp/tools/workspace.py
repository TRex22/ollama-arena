"""Workspace-scoped filesystem tools with path containment."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Callable

WORKSPACE_DIR = Path.home() / "arena_workspace"
WORKSPACE_DIR.mkdir(parents=True, exist_ok=True)


class SecurityError(Exception):
    """Raised when a workspace path escapes the sandbox root."""


def _safe_path(rel: str) -> Path:
    rel = (rel or ".").lstrip("/")
    target = (WORKSPACE_DIR / rel).resolve()
    root = WORKSPACE_DIR.resolve()
    if target != root and root not in target.parents:
        raise SecurityError("Path escape attempt")
    return target


def ls(args: dict) -> str:
    try:
        target = _safe_path(args.get("path", "."))
        if not target.exists():
            return "Error: Path not found."
        if target.is_file():
            return target.name
        return "\n".join(sorted(os.listdir(target))) or "(empty)"
    except SecurityError as exc:
        return f"Error: {exc}"
    except Exception as exc:
        return f"Error: {exc}"


def read_file(args: dict) -> str:
    try:
        target = _safe_path(args.get("path", ""))
        if not target.exists():
            return "Error: File not found."
        return target.read_text()
    except SecurityError as exc:
        return f"Error: {exc}"
    except Exception as exc:
        return f"Error: {exc}"


def write_file(args: dict) -> str:
    try:
        target = _safe_path(args.get("path", ""))
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(args.get("content", ""))
        return f"Wrote {len(args.get('content', ''))} bytes to {target.relative_to(WORKSPACE_DIR)}"
    except SecurityError as exc:
        return f"Error: {exc}"
    except Exception as exc:
        return f"Error: {exc}"


def mock_read_file(args: dict) -> str:
    # Pure fake - no real filesystem read, even within the sandboxed
    # workspace. Benchmark tasks only need to confirm the model called
    # read_file with the right path.
    path = args.get("path", "")
    if not path:
        return "Error: File not found."
    return f"(mock contents of {path})"


def mock_write_file(args: dict) -> str:
    # Pure fake - no real filesystem write, even within the sandboxed
    # workspace.
    path = args.get("path", "")
    content = args.get("content", "")
    return f"Wrote {len(content)} bytes to {path} (mock)"


READ_FILE_SCHEMA = {
    "type": "function",
    "function": {
        "name": "read_file",
        "description": "Read a file from the arena workspace.",
        "parameters": {
            "type": "object",
            "properties": {"path": {"type": "string"}},
            "required": ["path"],
        },
    },
}
WRITE_FILE_SCHEMA = {
    "type": "function",
    "function": {
        "name": "write_file",
        "description": "Write content to a file in the arena workspace.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "content": {"type": "string"},
            },
            "required": ["path", "content"],
        },
    },
}


def tool_defs(include_mock: bool = False) -> list[tuple[str, Callable[[dict], str], dict, str]]:
    defs: list[tuple[str, Callable[[dict], str], dict, str]] = [
        (
            "ls",
            ls,
            {
                "type": "function",
                "function": {
                    "name": "ls",
                    "description": "List files in the arena workspace directory.",
                    "parameters": {
                        "type": "object",
                        "properties": {"path": {"type": "string"}},
                    },
                },
            },
            "safe",
        ),
    ]
    if include_mock:
        # Mock mode: neither touches the real filesystem, even within the
        # sandbox - safe.
        defs.append(("read_file", mock_read_file, READ_FILE_SCHEMA, "safe"))
        defs.append(("write_file", mock_write_file, WRITE_FILE_SCHEMA, "safe"))
    else:
        # Real mode: genuinely reads/writes real files (sandboxed to
        # WORKSPACE_DIR via _safe_path), correctly gated.
        defs.append(("read_file", read_file, READ_FILE_SCHEMA, "confirm"))
        defs.append(("write_file", write_file, WRITE_FILE_SCHEMA, "confirm"))
    return defs
