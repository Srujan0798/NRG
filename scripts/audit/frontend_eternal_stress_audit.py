from __future__ import annotations

import json
import os
import re
import time
from pathlib import Path
from typing import Any

from playwright.sync_api import Browser, BrowserContext, Page, TimeoutError, expect, sync_playwright


BASE_URL = os.environ.get("NRG_UI_AUDIT_BASE_URL", "http://127.0.0.1:3100")
OUT_DIR = Path(os.environ.get("NRG_UI_AUDIT_OUT_DIR", "docs/audits/frontend_eternal_2026-04-26"))
SCREEN_DIR = OUT_DIR / "screenshots"
VIDEO_DIR = OUT_DIR / "videos"
DOWNLOAD_DIR = OUT_DIR / "downloads"
REPORT_JSON = OUT_DIR / "frontend_eternal_stress_results.json"

KEY_QUERY = "Which institutes in India have the highest grant amount in renewable energy?"
FOLLOWUP_QUERY = "Now show the same for computer science"
LONG_QUERY = (
    "Compare renewable energy grants, publications, patents, institute capacity, and collaboration networks "
    "for Gujarat, Tamil Nadu, Karnataka, Maharashtra, Delhi, and Telangana. "
    * 24
)


def ensure_dirs() -> None:
    SCREEN_DIR.mkdir(parents=True, exist_ok=True)
    VIDEO_DIR.mkdir(parents=True, exist_ok=True)
    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)


def shot(page: Page, name: str, full_page: bool = True) -> str:
    path = SCREEN_DIR / f"{name}.png"
    page.screenshot(path=str(path), full_page=full_page)
    return str(path)


def approve_consent_if_present(page: Page) -> None:
    try:
        dialog = page.get_by_role("dialog", name="DPDP Consent Required")
        if dialog.is_visible(timeout=1200):
            page.locator("#dpdp-ack-checkbox").check()
            page.get_by_role("button", name="Approve & Continue").click()
            expect(dialog).not_to_be_visible(timeout=5000)
    except TimeoutError:
        return


def login(page: Page, role_label: str, username: str, password: str) -> float:
    page.get_by_role("button", name=re.compile(role_label, re.I)).first.click()
    page.locator('input[autocomplete="username"]').fill(username)
    page.locator('input[autocomplete="current-password"]').fill(password)
    start = time.perf_counter()
    page.locator('input[autocomplete="current-password"]').press("Enter")
    page.wait_for_selector(
        '[data-testid="hero-search-input"], [data-testid="stat-researchers"], [data-testid="stat-opportunities"], [data-testid="industry-search-input"]',
        timeout=30000,
    )
    approve_consent_if_present(page)
    return time.perf_counter() - start


def go_login(page: Page, path: str = "/") -> None:
    page.goto(f"{BASE_URL}{path}", wait_until="commit", timeout=60000)
    page.wait_for_selector('input[autocomplete="username"]', timeout=60000)


def clear_browser_session(context: BrowserContext, page: Page) -> None:
    context.clear_cookies()
    page.evaluate(
        """() => {
          window.localStorage.clear();
          window.sessionStorage.clear();
        }"""
    )


def assert_no_page_overflow(page: Page) -> bool:
    return bool(page.evaluate("() => document.documentElement.scrollWidth <= document.documentElement.clientWidth + 1"))


def visible_text_matches(page: Page, patterns: dict[str, str]) -> dict[str, list[str]]:
    return page.evaluate(
        """(patterns) => {
          const out = Object.fromEntries(Object.keys(patterns).map((key) => [key, []]));
          const compiled = Object.fromEntries(Object.entries(patterns).map(([key, pattern]) => [key, new RegExp(pattern, 'gi')]));
          const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
          while (walker.nextNode()) {
            const text = (walker.currentNode.nodeValue || '').trim();
            if (!text) continue;
            for (const [key, regex] of Object.entries(compiled)) {
              if (regex.test(text)) out[key].push(text.slice(0, 180));
            }
          }
          return out;
        }""",
        patterns,
    )


def attach_capture(page: Page, results: dict[str, Any], phase: dict[str, str]) -> None:
    def on_console(msg: Any) -> None:
        entry = {"phase": phase["name"], "type": msg.type, "text": msg.text}
        if msg.type == "warning":
            results["console_warnings"].append(entry)
        if msg.type == "error":
            if phase["name"] == "expected_network_loss" and "Failed to load resource" in msg.text:
                results["expected_console_errors"].append(entry)
            else:
                results["console_errors"].append(entry)

    def on_response(response: Any) -> None:
        if response.status < 400 or "favicon" in response.url:
            return
        entry = {"phase": phase["name"], "url": response.url, "status": response.status}
        if phase["name"] == "expected_network_loss":
            results["expected_error_requests"].append(entry)
            return
        results["failed_requests"].append(entry)

    def on_requestfailed(req: Any) -> None:
        entry = {"phase": phase["name"], "url": req.url, "failure": req.failure}
        if phase["name"] == "expected_network_loss":
            results["expected_error_requests"].append(entry)
            return
        results["failed_requests"].append(entry)

    page.on("console", on_console)
    page.on("response", on_response)
    page.on("requestfailed", on_requestfailed)


def run_researcher_flow(browser: Browser, results: dict[str, Any]) -> None:
    context = browser.new_context(
        viewport={"width": 1366, "height": 768},
        record_video_dir=str(VIDEO_DIR),
        accept_downloads=True,
    )
    page = context.new_page()
    phase = {"name": "desktop"}
    attach_capture(page, results, phase)

    query_posts: list[float] = []

    def count_query_post(req: Any) -> None:
        if phase["name"] == "rapid_submit" and req.method == "POST" and req.url.endswith("/query"):
            query_posts.append(time.perf_counter())

    page.on("request", count_query_post)

    go_login(page, "/app")
    results["screenshots"]["direct_app_requires_auth"] = shot(page, "01_direct_app_requires_auth")
    results["checks"]["direct_app_route_has_login"] = page.locator('input[autocomplete="username"]').is_visible()

    results["timings"]["direct_app_login_seconds"] = round(login(page, "Researcher", "researcher_user", "researcher-pass"), 2)
    page.wait_for_selector('[data-testid="hero-search-input"]', timeout=10000)
    results["screenshots"]["direct_app_after_auth"] = shot(page, "02_direct_app_after_auth")
    results["checks"]["direct_app_has_provider_context"] = page.locator('[data-testid="hero-search-input"]').is_visible()

    page.locator('[data-testid="hero-search-input"]').fill(LONG_QUERY)
    page.wait_for_timeout(300)
    results["screenshots"]["long_query_hero"] = shot(page, "03_long_query_hero")
    results["checks"]["long_query_chars_retained"] = len(page.locator('[data-testid="hero-search-input"]').input_value())
    results["checks"]["long_query_no_horizontal_overflow"] = assert_no_page_overflow(page)

    phase["name"] = "expected_network_loss"
    context.set_offline(True)
    page.evaluate("() => window.dispatchEvent(new Event('offline'))")
    page.wait_for_selector("text=NRG cannot reach the network right now", timeout=5000)
    results["screenshots"]["offline_banner"] = shot(page, "04_offline_banner")
    results["checks"]["offline_banner_visible"] = page.get_by_role("status").is_visible()
    context.set_offline(False)
    page.evaluate("() => window.dispatchEvent(new Event('online'))")
    phase["name"] = "desktop"

    clear_browser_session(context, page)
    go_login(page, "/")
    results["timings"]["researcher_login_seconds"] = round(login(page, "Researcher", "researcher_user", "researcher-pass"), 2)
    page.wait_for_selector('[data-testid="researcher-search-input"]', timeout=10000)
    results["screenshots"]["desktop_dashboard"] = shot(page, "05_desktop_dashboard")
    results["checks"]["desktop_no_horizontal_overflow"] = assert_no_page_overflow(page)

    input_box = page.locator('[data-testid="researcher-search-input"]')
    input_box.fill(KEY_QUERY)
    phase["name"] = "rapid_submit"
    start = time.perf_counter()
    for _ in range(10):
        try:
            page.locator('[data-testid="researcher-search-submit"]').click(timeout=250)
        except TimeoutError:
            pass
    page.wait_for_selector("text=IIT Gandhinagar", timeout=20000)
    phase["name"] = "desktop"
    results["timings"]["rapid_submit_query_seconds"] = round(time.perf_counter() - start, 2)
    results["checks"]["rapid_submit_post_count"] = len(query_posts)
    results["screenshots"]["rapid_submit_result"] = shot(page, "06_rapid_submit_result")

    with page.expect_download(timeout=10000) as download_info:
        page.get_by_role("button", name="Export answer brief").first.click()
    download = download_info.value
    export_path = DOWNLOAD_DIR / download.suggested_filename
    download.save_as(str(export_path))
    results["downloads"]["answer_brief"] = str(export_path)
    results["checks"]["answer_brief_exported"] = export_path.exists() and export_path.stat().st_size > 0

    page.get_by_test_id("source-data-toggle").first.click()
    page.wait_for_selector('[data-testid="source-data-panel"]', timeout=5000)
    results["screenshots"]["source_data_panel"] = shot(page, "07_source_data_panel")
    results["checks"]["source_data_panel_visible"] = page.get_by_test_id("source-data-panel").first.is_visible()

    input_box.fill(FOLLOWUP_QUERY)
    input_box.press("Enter")
    page.wait_for_selector("text=Computer Science", timeout=20000)
    results["screenshots"]["followup_after_stress"] = shot(page, "08_followup_after_stress")
    results["checks"]["followup_distinct"] = page.get_by_text("Computer Science").first.is_visible()

    results["checks"]["visible_bad_runtime_text"] = visible_text_matches(
        page,
        {
            "undefined": r"(^|[^A-Za-z])undefined([^A-Za-z]|$)",
            "nan": r"(^|[^A-Za-z])NaN([^A-Za-z]|$)",
            "infinity": r"(^|[^A-Za-z])Infinity([^A-Za-z]|$)",
            "invalid_date": r"Invalid Date",
        },
    )
    context.close()


def run_tier3_flow(browser: Browser, results: dict[str, Any]) -> None:
    context = browser.new_context(viewport={"width": 1366, "height": 768}, accept_downloads=True)
    page = context.new_page()
    phase = {"name": "tier3"}
    attach_capture(page, results, phase)
    go_login(page, "/")
    results["timings"]["tier3_login_seconds"] = round(login(page, "Industry", "industry_user", "industry-pass"), 2)
    page.wait_for_selector('[data-testid="industry-search-input"]', timeout=10000)
    results["screenshots"]["tier3_dashboard"] = shot(page, "09_tier3_dashboard")
    page.locator('[data-testid="industry-search-input"]').fill(KEY_QUERY)
    page.locator('[data-testid="industry-search-input"]').press("Enter")
    page.wait_for_selector("text=Access restricted", timeout=20000)
    results["screenshots"]["tier3_restricted_result"] = shot(page, "10_tier3_restricted_result")
    pii_matches = visible_text_matches(
        page,
        {
            "email": r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}",
            "aadhaar": r"\\b[0-9]{4}[- ]?[0-9]{4}[- ]?[0-9]{4}\\b",
            "phone": r"\\b[6-9][0-9]{9}\\b",
        },
    )
    results["checks"]["tier3_visible_pii_matches"] = pii_matches
    results["checks"]["tier3_no_visible_pii"] = all(len(items) == 0 for items in pii_matches.values())
    context.close()


def run_responsive_flow(browser: Browser, results: dict[str, Any]) -> None:
    for name, viewport, mobile in [
        ("tablet", {"width": 768, "height": 1024}, False),
        ("mobile", {"width": 375, "height": 812}, True),
    ]:
        context = browser.new_context(viewport=viewport, is_mobile=mobile)
        page = context.new_page()
        phase = {"name": name}
        attach_capture(page, results, phase)
        go_login(page, "/")
        login(page, "Researcher", "researcher_user", "researcher-pass")
        page.wait_for_selector('[data-testid="researcher-search-input"]', timeout=10000)
        results["screenshots"][f"{name}_dashboard"] = shot(page, f"11_{name}_dashboard")
        page.locator('[data-testid="researcher-search-input"]').fill(KEY_QUERY)
        page.locator('[data-testid="researcher-search-input"]').press("Enter")
        page.wait_for_selector("text=IIT Gandhinagar", timeout=20000)
        results["screenshots"][f"{name}_query_result"] = shot(page, f"12_{name}_query_result")
        results["checks"][f"{name}_no_horizontal_overflow"] = assert_no_page_overflow(page)
        context.close()


def run_cross_browser_smoke(playwright: Any, results: dict[str, Any]) -> None:
    for name in ["chromium", "firefox", "webkit"]:
        browser_type = getattr(playwright, name)
        browser = browser_type.launch(headless=True)
        context: BrowserContext = browser.new_context(viewport={"width": 1280, "height": 720})
        page = context.new_page()
        phase = {"name": f"{name}_smoke"}
        local: dict[str, Any] = {"console_errors": [], "failed_requests": []}

        def on_console(msg: Any) -> None:
            if msg.type == "error":
                local["console_errors"].append(msg.text)

        def on_response(response: Any) -> None:
            if response.status >= 400 and "favicon" not in response.url:
                local["failed_requests"].append({"url": response.url, "status": response.status})

        page.on("console", on_console)
        page.on("response", on_response)
        start = time.perf_counter()
        go_login(page, "/")
        login(page, "Researcher", "researcher_user", "researcher-pass")
        page.wait_for_selector('[data-testid="researcher-search-input"]', timeout=15000)
        results["cross_browser"][name] = {
            "ok": True,
            "seconds": round(time.perf_counter() - start, 2),
            "console_errors": local["console_errors"],
            "failed_requests": local["failed_requests"],
            "phase": phase["name"],
        }
        context.close()
        browser.close()


def main() -> None:
    ensure_dirs()
    results: dict[str, Any] = {
        "base_url": BASE_URL,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "console_errors": [],
        "expected_console_errors": [],
        "console_warnings": [],
        "failed_requests": [],
        "expected_error_requests": [],
        "screenshots": {},
        "downloads": {},
        "timings": {},
        "checks": {},
        "cross_browser": {},
    }

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        run_researcher_flow(browser, results)
        run_tier3_flow(browser, results)
        run_responsive_flow(browser, results)
        browser.close()
        run_cross_browser_smoke(p, results)

    REPORT_JSON.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
