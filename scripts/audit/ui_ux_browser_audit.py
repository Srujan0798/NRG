from __future__ import annotations

import json
import re
import time
from pathlib import Path

from playwright.sync_api import Page, TimeoutError, expect, sync_playwright


BASE_URL = "http://127.0.0.1:3000"
OUT_DIR = Path("docs/audits/ui_ux_2026-04-24")
SCREEN_DIR = OUT_DIR / "screenshots"
VIDEO_DIR = OUT_DIR / "videos"
REPORT_JSON = OUT_DIR / "browser_audit_results.json"


def shot(page: Page, name: str, full_page: bool = True) -> str:
    path = SCREEN_DIR / f"{name}.png"
    page.screenshot(path=str(path), full_page=full_page)
    return str(path)


def approve_consent_if_present(page: Page) -> None:
    try:
        dialog = page.get_by_role("dialog", name="DPDP Consent Required")
        if dialog.is_visible(timeout=1500):
            page.locator("#dpdp-ack-checkbox").check()
            page.get_by_role("button", name="Approve & Continue").click()
            expect(dialog).not_to_be_visible(timeout=5000)
    except TimeoutError:
        return


def login(page: Page, username: str, password: str) -> float:
    page.locator('input[autocomplete="username"]').fill(username)
    page.locator('input[autocomplete="current-password"]').fill(password)
    start = time.perf_counter()
    page.locator('input[autocomplete="current-password"]').press("Enter")
    page.wait_for_selector('[data-testid="stat-researchers"], [data-testid="stat-opportunities"]', timeout=30000)
    approve_consent_if_present(page)
    return time.perf_counter() - start


def run_query(page: Page, selector: str, query: str, wait_text: str) -> float:
    page.locator(selector).fill(query)
    start = time.perf_counter()
    page.locator(selector).press("Enter")
    page.wait_for_selector(f"text={wait_text}", timeout=15000)
    return time.perf_counter() - start


def main() -> None:
    SCREEN_DIR.mkdir(parents=True, exist_ok=True)
    VIDEO_DIR.mkdir(parents=True, exist_ok=True)
    results: dict = {
        "console_errors": [],
        "expected_console_errors": [],
        "console_warnings": [],
        "failed_requests": [],
        "expected_error_requests": [],
        "screenshots": {},
        "timings": {},
        "checks": {},
    }

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1366, "height": 768},
            record_video_dir=str(VIDEO_DIR),
        )
        page = context.new_page()
        current_phase = {"name": "normal"}

        def on_console(msg):
            if msg.type != "error":
                return
            if current_phase["name"] in {"wrong_credentials", "pii_block"} and "Failed to load resource" in msg.text:
                results["expected_console_errors"].append({"phase": current_phase["name"], "message": msg.text})
                return
            results["console_errors"].append(msg.text)

        page.on("console", on_console)
        page.on("console", lambda msg: results["console_warnings"].append(msg.text) if msg.type == "warning" else None)

        def on_response(response):
            if response.status >= 400 and "favicon" not in response.url:
                if current_phase["name"] == "wrong_credentials" and response.status == 401 and response.url.endswith("/login"):
                    results["expected_error_requests"].append({"phase": current_phase["name"], "url": response.url, "status": response.status})
                    return
                if current_phase["name"] == "pii_block" and response.status == 400 and response.url.endswith("/query"):
                    results["expected_error_requests"].append({"phase": current_phase["name"], "url": response.url, "status": response.status})
                    return
                results["failed_requests"].append({"url": response.url, "status": response.status})

        page.on("response", on_response)
        page.on("requestfailed", lambda req: results["failed_requests"].append({"url": req.url, "failure": req.failure}))

        start = time.perf_counter()
        page.goto(BASE_URL, wait_until="commit", timeout=60000)
        page.wait_for_selector('input[autocomplete="username"]', timeout=30000)
        results["timings"]["login_page_load_seconds"] = round(time.perf_counter() - start, 2)
        results["screenshots"]["login"] = shot(page, "01_login")
        results["checks"]["login_placeholders"] = {
            "username": page.locator('input[autocomplete="username"]').get_attribute("placeholder"),
            "password": page.locator('input[autocomplete="current-password"]').get_attribute("placeholder"),
        }

        page.locator('input[autocomplete="username"]').fill("")
        page.locator('input[autocomplete="current-password"]').fill("")
        page.locator('button[type="submit"]').click()
        page.wait_for_selector("text=Enter your username", timeout=3000)
        results["screenshots"]["blank_validation"] = shot(page, "02_blank_login_validation")

        page.locator('input[autocomplete="username"]').fill(f"bad_user_{int(time.time())}")
        page.locator('input[autocomplete="current-password"]').fill("bad_pass")
        current_phase["name"] = "wrong_credentials"
        page.locator('button[type="submit"]').click()
        page.wait_for_selector("text=Invalid username or password", timeout=12000)
        page.wait_for_timeout(300)
        current_phase["name"] = "normal"
        results["screenshots"]["wrong_credentials"] = shot(page, "03_wrong_credentials")

        page.get_by_role("button", name=re.compile("Researcher")).first.click()
        results["timings"]["researcher_login_seconds"] = round(login(page, "researcher_user", "researcher-pass"), 2)
        page.wait_for_selector('[data-testid="stat-researchers"]', timeout=10000)
        results["screenshots"]["tier1_dashboard"] = shot(page, "04_tier1_dashboard")

        results["timings"]["key_query_seconds"] = round(
            run_query(
                page,
                '[data-testid="researcher-search-input"]',
                "Which institutes in India have the highest grant amount in renewable energy?",
                "IIT Gandhinagar",
            ),
            2,
        )
        results["screenshots"]["query_result_with_citations"] = shot(page, "05_query_result_with_citations")

        results["timings"]["followup_query_seconds"] = round(
            run_query(
                page,
                '[data-testid="researcher-search-input"]',
                "Now show the same for computer science",
                "Computer Science",
            ),
            2,
        )
        results["screenshots"]["followup_result"] = shot(page, "06_followup_result")

        page.locator('[data-testid="researcher-search-input"]').fill("Show all researchers with Aadhaar 1234 5678 9012")
        current_phase["name"] = "pii_block"
        page.locator('[data-testid="researcher-search-input"]').press("Enter")
        page.wait_for_selector("text=This query contains sensitive information", timeout=12000)
        page.wait_for_timeout(300)
        current_phase["name"] = "normal"
        results["screenshots"]["pii_block"] = shot(page, "07_pii_block")

        page.get_by_test_id("tab-audit").click()
        page.wait_for_selector("text=DPDP Audit Log", timeout=5000)
        page.get_by_role("button", name="Verify integrity").click()
        page.wait_for_selector("text=Audit chain", timeout=8000)
        results["screenshots"]["audit_trail"] = shot(page, "08_audit_trail")

        page.get_by_test_id("tab-dashboard").click()
        page.locator('[data-testid="researcher-search-input"]').fill("Show me the research network around hydrogen fuel cells")
        page.locator('[data-testid="researcher-search-input"]').press("Enter")
        page.wait_for_selector('[data-testid="tab-graph"][aria-current="page"]', timeout=5000)
        page.wait_for_timeout(1500)
        results["screenshots"]["knowledge_graph"] = shot(page, "09_knowledge_graph")

        page.locator('button[aria-label="Log out"]').click()
        page.wait_for_selector("text=Sign in", timeout=8000)
        results["screenshots"]["logout_to_login"] = shot(page, "10_logout")

        page.get_by_role("button", name=re.compile("Industry")).first.click()
        results["timings"]["industry_login_seconds"] = round(login(page, "industry_user", "industry-pass"), 2)
        page.wait_for_selector('[data-testid="industry-search-input"]', timeout=10000)
        results["screenshots"]["tier3_dashboard"] = shot(page, "11_tier3_dashboard")
        results["timings"]["tier3_query_seconds"] = round(
            run_query(
                page,
                '[data-testid="industry-search-input"]',
                "Which institutes in India have the highest grant amount in renewable energy?",
                "Access restricted",
            ),
            2,
        )
        results["screenshots"]["tier3_restricted_result"] = shot(page, "12_tier3_restricted_result")

        mobile = browser.new_context(viewport={"width": 375, "height": 812}, is_mobile=True)
        mobile_page = mobile.new_page()
        mobile_page.goto(BASE_URL, wait_until="commit", timeout=60000)
        mobile_page.wait_for_selector('input[autocomplete="username"]', timeout=30000)
        results["screenshots"]["mobile_login"] = shot(mobile_page, "13_mobile_login")
        mobile_page.get_by_role("button", name=re.compile("Researcher")).first.click()
        login(mobile_page, "researcher_user", "researcher-pass")
        mobile_page.wait_for_selector('[data-testid="stat-researchers"]', timeout=10000)
        results["screenshots"]["mobile_dashboard"] = shot(mobile_page, "14_mobile_dashboard")
        run_query(
            mobile_page,
            '[data-testid="researcher-search-input"]',
            "Which institutes in India have the highest grant amount in renewable energy?",
            "IIT Gandhinagar",
        )
        results["screenshots"]["mobile_query_result"] = shot(mobile_page, "15_mobile_query_result")
        mobile.close()

        bad_text_matches = page.evaluate(
            """() => {
              const terms = ['undefined', 'NaN', 'null', 'Infinity'];
              const matches = [];
              const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
              while (walker.nextNode()) {
                const text = walker.currentNode.nodeValue || '';
                for (const term of terms) {
                  const re = new RegExp(`(^|[^A-Za-z])${term}([^A-Za-z]|$)`);
                  if (re.test(text)) {
                    matches.push({ term, text: text.trim().slice(0, 180) });
                  }
                }
              }
              return matches;
            }"""
        )
        results["checks"]["bad_text_matches"] = bad_text_matches
        results["checks"]["visible_undefined"] = sum(1 for item in bad_text_matches if item["term"] == "undefined")
        results["checks"]["visible_nan"] = sum(1 for item in bad_text_matches if item["term"] == "NaN")
        context.close()
        browser.close()

    REPORT_JSON.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
