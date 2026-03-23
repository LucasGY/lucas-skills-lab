import csv
import os
import sys
from playwright.sync_api import sync_playwright

TOOL_URL = "https://cmegroup-tools.quikstrike.net/User/QuikStrikeTools.aspx?viewitemid=IntegratedFedWatchTool&userId=lwolf&jobRole=&company=&companyType=&userId=&jobRole=&company=&companyType="
REFERER = "https://www.cmegroup.com/markets/interest-rates/cme-fedwatch-tool.html?redirect=/trading/interest-rates/countdown-to-fomc.html"


def clean(text: str) -> str:
    return " ".join((text or "").split())


def write_csv(headers, rows, output_path: str):
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(rows)


def extract_table(table):
    table.wait_for(state="visible", timeout=30000)
    rows_locator = table.locator("tr")
    row_count = rows_locator.count()
    first_headers = [clean(x) for x in rows_locator.nth(0).locator("th").all_text_contents()]
    second_headers = [clean(x) for x in rows_locator.nth(1).locator("th").all_text_contents()] if row_count > 1 else []
    headers = [first_headers[0], *second_headers] if len(second_headers) > 1 and len(first_headers) > len(second_headers) else (second_headers if len(second_headers) > 1 else first_headers)
    start_index = 2 if len(second_headers) > 1 else 1

    rows = []
    for i in range(start_index, row_count):
        row = [clean(x) for x in rows_locator.nth(i).locator("td,th").all_text_contents()]
        if row and any(row):
            rows.append(row)
    return headers, rows


def load_frame():
    p = sync_playwright().start()
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto(TOOL_URL, referer=REFERER, wait_until="domcontentloaded", timeout=120000)
    page.wait_for_timeout(8000)
    frame = next((f for f in page.frames if "QuikStrikeView.aspx" in f.url), page.main_frame)
    return p, browser, page, frame


def fetch_conditional_meeting_probabilities(output_path: str = "fedwatch_conditional_probabilities.csv"):
    p, browser, page, frame = load_frame()
    try:
        frame.locator("#ctl00_MainContent_ucViewControl_IntegratedFedWatchTool_lbPTree").click()
        page.wait_for_timeout(5000)
        table = frame.locator('table:has-text("Conditional Meeting Probabilities")').first
        headers, rows = extract_table(table)
        write_csv(headers, rows, output_path)
        return {
            "mode": "conditional",
            "output_path": os.path.abspath(output_path),
            "headers": headers,
            "row_count": len(rows),
            "rows": rows,
        }
    finally:
        browser.close()
        p.stop()


def fetch_current_target_rate(output_path: str = "fedwatch_current_target_rate.csv"):
    p, browser, page, frame = load_frame()
    try:
        table = frame.locator("table.grid-thm.grid-thm-v2.w-lg").last
        headers, rows = extract_table(table)
        normalized_headers = ["Target Rate (bps)", *headers] if rows and len(rows[0]) == len(headers) + 1 else headers
        write_csv(normalized_headers, rows, output_path)
        return {
            "mode": "current",
            "output_path": os.path.abspath(output_path),
            "headers": normalized_headers,
            "row_count": len(rows),
            "rows": rows,
        }
    finally:
        browser.close()
        p.stop()


if __name__ == "__main__":
    mode = (sys.argv[1] if len(sys.argv) > 1 else "conditional").lower()
    output_path = sys.argv[2] if len(sys.argv) > 2 else (
        "fedwatch_current_target_rate.csv" if mode == "current" else "fedwatch_conditional_probabilities.csv"
    )
    result = fetch_current_target_rate(output_path) if mode == "current" else fetch_conditional_meeting_probabilities(output_path)
    print({
        "mode": result["mode"],
        "output_path": result["output_path"],
        "headers": result["headers"],
        "row_count": result["row_count"],
        "sample_rows": result["rows"][:3],
    })
