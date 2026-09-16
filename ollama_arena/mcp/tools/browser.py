"""Browser automation tools (Playwright optional)."""
from __future__ import annotations

import json
from typing import Callable


def browser_use(args: dict) -> str:
    action = args.get("action", "navigate")
    url = args.get("url", "")
    selector = args.get("selector", "")

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return (
            "Error: Playwright is not installed. "
            "Install with: pip install playwright && playwright install chromium"
        )

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            if action == "navigate" and url:
                page.goto(url, timeout=15000)
                content = page.content()[:4000]
                browser.close()
                return f"Navigated to {url}. Page content preview:\n{content}"
            if action == "click" and selector:
                if url:
                    page.goto(url, timeout=15000)
                page.click(selector, timeout=10000)
                content = page.content()[:4000]
                browser.close()
                return f"Clicked '{selector}'. Page content preview:\n{content}"
            if action == "scrape" and selector:
                if url:
                    page.goto(url, timeout=15000)
                text = page.inner_text(selector)[:4000]
                browser.close()
                return f"Scraped '{selector}':\n{text}"
            browser.close()
            return "Error: browser_use requires action + url and/or selector."
    except Exception as exc:
        return f"Error: {exc}"


def mock_browser_navigate(args: dict) -> str:
    url = args.get("url", "about:blank")
    return json.dumps({"status": "ok", "url": url, "title": "Mock Browser Page"})


def mock_browser_use(args: dict) -> str:
    # Pure fake, same shape as browser_use's real return strings but with
    # no Playwright/network/filesystem access at all - safe to run
    # unattended. Benchmark tasks only care that the model called
    # browser_use with the right action/url/selector (eval_tool_use
    # grades the tool call itself, not this string), not that a real
    # page was actually rendered.
    action = args.get("action", "navigate")
    url = args.get("url", "")
    selector = args.get("selector", "")
    if action == "click":
        return f"Clicked '{selector}'. Page content preview:\n<html><body>Mock page after click.</body></html>"
    if action == "scrape":
        return f"Scraped '{selector}':\nMock scraped text."
    return f"Navigated to {url}. Page content preview:\n<html><body>Mock Browser Page for {url}</body></html>"


BROWSER_USE_SCHEMA = {
    "type": "function",
    "function": {
        "name": "browser_use",
        "description": (
            "Automate Chromium via Playwright: navigate, click CSS selectors, scrape."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["navigate", "click", "scrape"],
                },
                "url": {"type": "string"},
                "selector": {"type": "string"},
            },
            "required": ["action"],
        },
    },
}


def tool_defs(include_mock: bool = False) -> list[tuple[str, Callable[[dict], str], dict, str]]:
    defs: list[tuple[str, Callable[[dict], str], dict, str]] = []
    if include_mock:
        # Mock mode: browser_use maps to the inert mock handler, "safe" -
        # no real browser is ever launched, so no confirmation is needed.
        defs.append(("browser_use", mock_browser_use, BROWSER_USE_SCHEMA, "safe"))
    else:
        # Real mode: the actual Playwright-driving handler - genuinely
        # launches a browser and hits real URLs, correctly gated.
        defs.append(("browser_use", browser_use, BROWSER_USE_SCHEMA, "confirm"))
    if include_mock:
        defs.append(
            (
                "browser_navigate",
                mock_browser_navigate,
                {
                    "type": "function",
                    "function": {
                        "name": "browser_navigate",
                        "description": "Navigate a browser to a URL (mock for benchmarks).",
                        "parameters": {
                            "type": "object",
                            "properties": {"url": {"type": "string"}},
                            "required": ["url"],
                        },
                    },
                },
                # This handler (mock_browser_navigate, above) is a pure fake -
                # it does no I/O at all, just returns a canned JSON string.
                # "confirm" here was a copy-paste from browser_use's REAL,
                # Playwright-driving tier (correct for that one) - it made
                # every tool_use benchmark task expecting this mock tool hang
                # on an interactive y/N prompt for something that can't
                # possibly do anything dangerous. "safe" is correct for a
                # mock with zero real-world effect.
                "safe",
            )
        )
    return defs
