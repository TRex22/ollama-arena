"""Code execution tools."""
from __future__ import annotations

from typing import Callable

from ...sandboxes.runner import run_in_language


def code_interpreter(args: dict) -> str:
    code = args.get("code", "")
    language = args.get("language", "python")
    if not code:
        return "Error: No code provided."
    result = run_in_language(code, language=language, use_docker=True)
    if result.error:
        return f"Exit {result.exit_code}: {result.error}\n{result.output}"
    return result.output or "(no output)"


def mock_code_interpreter(args: dict) -> str:
    # Pure fake - no sandbox/Docker/subprocess invoked at all. Benchmark
    # tasks only need to confirm the model called code_interpreter with
    # code/language, not that it actually ran anywhere.
    code = args.get("code", "")
    if not code:
        return "Error: No code provided."
    return "(mock output) code accepted, not actually executed"


CODE_INTERPRETER_SCHEMA = {
    "type": "function",
    "function": {
        "name": "code_interpreter",
        "description": "Execute Python/JS code in a Docker sandbox.",
        "parameters": {
            "type": "object",
            "properties": {
                "code": {"type": "string"},
                "language": {"type": "string"},
            },
            "required": ["code"],
        },
    },
}


def tool_defs(include_mock: bool = False) -> list[tuple[str, Callable[[dict], str], dict, str]]:
    if include_mock:
        # Mock mode: no real sandbox execution - safe.
        return [("code_interpreter", mock_code_interpreter, CODE_INTERPRETER_SCHEMA, "safe")]
    # Real mode: genuinely runs code in a Docker sandbox, correctly gated.
    return [("code_interpreter", code_interpreter, CODE_INTERPRETER_SCHEMA, "confirm")]
