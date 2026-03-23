import csv
import os
import re
import sys
from playwright.sync_api import sync_playwright

TOOL_URL = "https://cmegroup-tools.quikstrike.net/User/QuikStrikeTools.aspx?viewitemid=IntegratedFedWatchTool&userId=lwolf&jobRole=&company=&companyType=&userId=&jobRole=&company=&companyType="
REFERER = "https://www.cmegroup.com/markets/interest-rates/cme-fedwatch-tool.html?redirect=/trading/interest-rates/countdown-to-fomc.html"


def clean(text: str) -> str:
    return " ".join((text or "").split())


def parse_rate_bucket(label: str):
    match = re.search(r"(\d+)\s*-\s*(\d+)", clean(label))
    if not match:
        return None
    return int(match.group(1)), int(match.group(2))


def cut_vs_current_bps(current_label: str, target_label: str) -> str:
    current = parse_rate_bucket(current_label)
    target = parse_rate_bucket(target_label)
    if not current or not target:
        return ""
    current_mid = sum(current) / 2
    target_mid = sum(target) / 2
    return str(int(target_mid - current_mid))


def parse_probability_percent(value: str):
    match = re.search(r"-?\d+(?:\.\d+)?", clean(value))
    return float(match.group(0)) if match else None


def expected_change_bps(change_cells, probability_cells) -> str:
    total = 0.0
    has_value = False
    for change, probability in zip(change_cells, probability_cells):
        try:
            change_value = float(change)
        except (TypeError, ValueError):
            continue
        probability_value = parse_probability_percent(probability)
        if probability_value is None:
            continue
        total += change_value * probability_value / 100.0
        has_value = True
    return f"{total:.2f}" if has_value else ""


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
    frame = None
    for _ in range(20):
        page.wait_for_timeout(1000)
        frame = next((f for f in page.frames if "QuikStrikeView.aspx" in f.url), None)
        if frame:
            break
    frame = frame or page.main_frame
    frame.locator("#ctl00_MainContent_ucViewControl_IntegratedFedWatchTool_lbPTree").wait_for(state="attached", timeout=30000)
    return p, browser, page, frame


def get_current_rate_bucket(frame):
    patterns = [
        r"Current target rate is (\d+\s*-\s*\d+)",
        r"(\d+\s*-\s*\d+)\s*\(Current\)",
    ]
    for _ in range(5):
        body_text = frame.locator("body").inner_text()
        for pattern in patterns:
            match = re.search(pattern, body_text, re.IGNORECASE)
            if match:
                return clean(match.group(1))
        frame.page.wait_for_timeout(1000)
    return None


def fetch_conditional_meeting_probabilities(output_path: str = "fedwatch_conditional_probabilities.csv"):
    p, browser, page, frame = load_frame()
    try:
        current_bucket = get_current_rate_bucket(frame)
        frame.locator("#ctl00_MainContent_ucViewControl_IntegratedFedWatchTool_lbPTree").click(force=True)
        page.wait_for_timeout(5000)
        table = frame.locator('table:has-text("Conditional Meeting Probabilities")').first
        headers, rows = extract_table(table)
        final_headers = [*headers, "Expected Change vs Current (bps)"]
        cut_row = None
        if current_bucket:
            cut_row = [f"Cut vs Current {current_bucket} (bps)", *[cut_vs_current_bps(current_bucket, header) for header in headers[1:]], ""]
        output_rows = []
        for row in rows:
            if cut_row:
                output_rows.append([*row, expected_change_bps(cut_row[1:-1], row[1:])])
            else:
                output_rows.append([*row, ""])
        final_rows = [cut_row, *output_rows] if cut_row else output_rows
        write_csv(final_headers, final_rows, output_path)
        return {
            "mode": "conditional",
            "output_path": os.path.abspath(output_path),
            "headers": final_headers,
            "row_count": len(final_rows),
            "rows": final_rows,
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
        "sample_rows": result["rows"][:4],
    })
