#!/usr/bin/env python3
import argparse
import csv
import json
from datetime import date, datetime, timedelta
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


VIX_URL = "https://cdn.cboe.com/api/global/us_indices/daily_prices/VIX_History.csv"
VVIX_URL = "https://cdn.cboe.com/api/global/us_indices/daily_prices/VVIX_History.csv"
DEFAULT_OUT_DIR = Path("outputs/vix-vvix-history")
DEFAULT_OUT_PATH = DEFAULT_OUT_DIR / "vix_vvix_1y.csv"
DATE_FORMAT = "%m/%d/%Y"


def parse_args():
    parser = argparse.ArgumentParser(
        description="Fetch merged VIX and VVIX close history from official Cboe CSV files."
    )
    parser.add_argument(
        "--days",
        type=int,
        default=365,
        help="Rolling window ending on --end-date or today. Ignored when --start-date is set.",
    )
    parser.add_argument(
        "--start-date",
        help="Inclusive start date in YYYY-MM-DD format.",
    )
    parser.add_argument(
        "--end-date",
        help="Inclusive end date in YYYY-MM-DD format. Defaults to today (UTC).",
    )
    parser.add_argument(
        "--csv-out",
        default=str(DEFAULT_OUT_PATH),
        help="Path to write the merged CSV output.",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Do not print the export summary to stdout.",
    )
    return parser.parse_args()


def parse_iso_date(value, flag_name):
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError as exc:
        raise SystemExit(f"{flag_name} must use YYYY-MM-DD format.") from exc


def resolve_date_range(args):
    end_date = parse_iso_date(args.end_date, "--end-date") if args.end_date else date.today()

    if args.start_date:
        start_date = parse_iso_date(args.start_date, "--start-date")
    else:
        if args.days <= 0:
            raise SystemExit("--days must be a positive integer.")
        start_date = end_date - timedelta(days=args.days - 1)

    if start_date > end_date:
        raise SystemExit("--start-date cannot be later than --end-date.")

    return start_date, end_date


def fetch_csv(url):
    request = Request(
        url,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
            ),
            "Accept": "text/csv,text/plain,*/*",
        },
    )
    try:
        with urlopen(request, timeout=30) as response:
            return response.read().decode("utf-8-sig")
    except HTTPError as exc:
        raise SystemExit(f"HTTP error while fetching {url}: {exc.code}") from exc
    except URLError as exc:
        raise SystemExit(f"Network error while fetching {url}: {exc}") from exc


def load_series(csv_text, value_column):
    reader = csv.DictReader(csv_text.splitlines())
    series = {}
    for row in reader:
        raw_date = (row.get("DATE") or "").strip()
        raw_value = (row.get(value_column) or "").strip()
        if not raw_date or not raw_value:
            continue
        parsed_date = datetime.strptime(raw_date, DATE_FORMAT).date()
        series[parsed_date] = raw_value
    return series


def build_rows(vix_series, vvix_series, start_date, end_date):
    common_dates = sorted(set(vix_series) & set(vvix_series))
    rows = []
    for current_date in common_dates:
        if start_date <= current_date <= end_date:
            rows.append(
                {
                    "date": current_date.isoformat(),
                    "vix_close": vix_series[current_date],
                    "vvix_close": vvix_series[current_date],
                }
            )
    return rows


def write_csv_output(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["date", "vix_close", "vvix_close"])
        writer.writeheader()
        writer.writerows(rows)


def main():
    args = parse_args()
    start_date, end_date = resolve_date_range(args)

    vix_series = load_series(fetch_csv(VIX_URL), "CLOSE")
    vvix_series = load_series(fetch_csv(VVIX_URL), "VVIX")
    rows = build_rows(vix_series, vvix_series, start_date, end_date)

    output_path = Path(args.csv_out)
    write_csv_output(output_path, rows)

    if not args.quiet:
        summary = {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "row_count": len(rows),
            "output_path": str(output_path.resolve()),
            "source_urls": {
                "vix": VIX_URL,
                "vvix": VVIX_URL,
            },
        }
        print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
