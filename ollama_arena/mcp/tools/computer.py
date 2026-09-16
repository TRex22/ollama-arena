"""Host computer automation tools (macOS)."""
from __future__ import annotations

import platform
import subprocess
from pathlib import Path
from typing import Callable


def computer_screenshot(args: dict) -> str:
    path = Path("/tmp/arena_screenshot.png")
    try:
        if platform.system() == "Darwin":
            subprocess.run(["screencapture", "-x", str(path)], check=True)
            return f"Screenshot saved to {path}."
        return "Screenshot not supported on this OS."
    except Exception as exc:
        return f"Error: {exc}"


def computer_click(args: dict) -> str:
    x, y = args.get("x", 0), args.get("y", 0)
    try:
        x_int, y_int = int(x), int(y)
    except (TypeError, ValueError):
        return "Error: x and y must be integers."
    try:
        if platform.system() == "Darwin":
            subprocess.run(
                ["osascript", "-e", f'tell application "System Events" to click at {{{x_int}, {y_int}}}'],
                check=True,
            )
            return f"Clicked at ({x_int}, {y_int})"
        return "Clicking not supported on this OS."
    except Exception as exc:
        return f"Error: {exc}"


def computer_type(args: dict) -> str:
    text = args.get("text", "")
    try:
        if platform.system() == "Darwin":
            escaped = text.replace('"', '\\"')
            subprocess.run(
                ["osascript", "-e", f'tell application "System Events" to keystroke "{escaped}"'],
                check=True,
            )
            return f"Typed '{text}'"
        return "Typing not supported on this OS."
    except Exception as exc:
        return f"Error: {exc}"


def mock_computer_screenshot(args: dict) -> str:
    # Pure fake - no screencapture subprocess invoked, no real screen touched.
    return "Screenshot saved to /tmp/arena_screenshot.png. (mock)"


def mock_computer_click(args: dict) -> str:
    # Pure fake - no osascript/System Events invoked, nothing on the real
    # host machine is clicked.
    x, y = args.get("x", 0), args.get("y", 0)
    try:
        x_int, y_int = int(x), int(y)
    except (TypeError, ValueError):
        return "Error: x and y must be integers."
    return f"Clicked at ({x_int}, {y_int}) (mock)"


def mock_computer_type(args: dict) -> str:
    # Pure fake - no osascript keystroke injection, nothing is typed
    # anywhere on the real host machine (this is the one that actually
    # matters most: the real handler types into WHATEVER window currently
    # has OS focus, completely unrelated to any benchmark sandbox).
    text = args.get("text", "")
    return f"Typed '{text}' (mock)"


COMPUTER_SCREENSHOT_SCHEMA = {
    "type": "function",
    "function": {
        "name": "computer_screenshot",
        "description": "Capture the host screen (macOS screencapture).",
        "parameters": {"type": "object", "properties": {}},
    },
}
COMPUTER_CLICK_SCHEMA = {
    "type": "function",
    "function": {
        "name": "computer_click",
        "description": "Click at screen coordinates (x, y).",
        "parameters": {
            "type": "object",
            "properties": {
                "x": {"type": "integer"},
                "y": {"type": "integer"},
            },
            "required": ["x", "y"],
        },
    },
}
COMPUTER_TYPE_SCHEMA = {
    "type": "function",
    "function": {
        "name": "computer_type",
        "description": "Type text via keyboard automation.",
        "parameters": {
            "type": "object",
            "properties": {"text": {"type": "string"}},
            "required": ["text"],
        },
    },
}


def tool_defs(include_mock: bool = False) -> list[tuple[str, Callable[[dict], str], dict, str]]:
    if include_mock:
        # Mock mode: none of these touch the real host screen/keyboard/
        # mouse at all - safe.
        return [
            ("computer_screenshot", mock_computer_screenshot, COMPUTER_SCREENSHOT_SCHEMA, "safe"),
            ("computer_click", mock_computer_click, COMPUTER_CLICK_SCHEMA, "safe"),
            ("computer_type", mock_computer_type, COMPUTER_TYPE_SCHEMA, "safe"),
        ]
    # Real mode: genuinely controls the host screen/keyboard/mouse via
    # osascript/screencapture - correctly gated, especially computer_type
    # (types into whatever window currently has real OS focus).
    return [
        ("computer_screenshot", computer_screenshot, COMPUTER_SCREENSHOT_SCHEMA, "confirm"),
        ("computer_click", computer_click, COMPUTER_CLICK_SCHEMA, "confirm"),
        ("computer_type", computer_type, COMPUTER_TYPE_SCHEMA, "confirm"),
    ]
