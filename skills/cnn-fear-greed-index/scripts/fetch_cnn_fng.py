#!/usr/bin/env python3
import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


ENDPOINT = "https://production.dataviz.cnn.io/index/fearandgreed/graphdata"
PAGE_URL = "https://www.cnn.com/markets/fear-and-greed"
DEFAULT_OUT_DIR = Path("outputs/cnn-fear-greed")


def iso_from_ms(value):
    return datetime.fromtimestamp(value / 1000, tz=timezone.utc).isoformat()


def fetch_payload():
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
        ),
        "Referer": PAGE_URL,
        "Origin": "https://www.cnn.com",
        "Accept": "application/json,text/plain,*/*",
    }
    request = Request(ENDPOINT, headers=headers)
    try:
        with urlopen(request, timeout=30) as response:
            body = response.read().decode("utf-8")
    except HTTPError as exc:
        raise SystemExit(f"HTTP error from CNN endpoint: {exc.code}") from exc
    except URLError as exc:
        raise SystemExit(f"Network error while fetching CNN endpoint: {exc}") from exc

    if body.strip() == "I'm a teapot. You're a bot.":
        raise SystemExit("CNN bot check triggered. Retry with browser-like headers.")

    try:
        return json.loads(body)
    except json.JSONDecodeError as exc:
        raise SystemExit("CNN endpoint did not return valid JSON.") from exc


def build_summary(payload):
    current = payload["fear_and_greed"]
    historical = payload["fear_and_greed_historical"]
    return {
        "score": round(current["score"], 1),
        "rating": current["rating"],
        "timestamp": current["timestamp"],
        "previous_close": current["previous_close"],
        "previous_1_week": current["previous_1_week"],
        "previous_1_month": current["previous_1_month"],
        "previous_1_year": current["previous_1_year"],
        "historical_points": len(historical["data"]),
        "historical_latest_timestamp_utc": iso_from_ms(historical["timestamp"]),
    }


def write_json(path, payload, summary):
    path.parent.mkdir(parents=True, exist_ok=True)
    wrapped = {
        "summary": summary,
        "payload": payload,
    }
    path.write_text(json.dumps(wrapped, indent=2), encoding="utf-8")


def write_csv(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = payload["fear_and_greed_historical"]["data"]
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=["timestamp_ms", "timestamp_utc", "score", "rating"],
        )
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    "timestamp_ms": int(row["x"]),
                    "timestamp_utc": iso_from_ms(row["x"]),
                    "score": row["y"],
                    "rating": row["rating"],
                }
            )


def main():
    parser = argparse.ArgumentParser(description="Fetch CNN Fear & Greed Index data.")
    parser.add_argument(
        "--json-out",
        default=str(DEFAULT_OUT_DIR / "cnn-fear-greed.json"),
        help="Path to write JSON output.",
    )
    parser.add_argument(
        "--csv-out",
        default=str(DEFAULT_OUT_DIR / "cnn-fear-greed-timeline.csv"),
        help="Path to write historical timeline CSV.",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Do not print the summary to stdout.",
    )
    args = parser.parse_args()

    payload = fetch_payload()
    summary = build_summary(payload)

    write_json(Path(args.json_out), payload, summary)
    if args.csv_out:
        write_csv(Path(args.csv_out), payload)

    if not args.quiet:
        print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
