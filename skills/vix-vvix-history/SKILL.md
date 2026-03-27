---
name: vix-vvix-history
description: Fetch daily historical close data for the Cboe VIX and VVIX indices from official Cboe CSV sources, then export a merged CSV with date, vix_close, and vvix_close. Use this when the user wants the last year of VIX and VVIX history, a custom date range, or a CSV file for dashboards and backend services.
---

# VIX + VVIX History

Use this skill when the user wants:

- recent `VIX` and `VVIX` history
- a single CSV for dashboard ingestion
- a custom date range for volatility history

## Source

Official Cboe historical CSV files:

- `https://cdn.cboe.com/api/global/us_indices/daily_prices/VIX_History.csv`
- `https://cdn.cboe.com/api/global/us_indices/daily_prices/VVIX_History.csv`

## What this skill does

- downloads official `VIX` daily history
- downloads official `VVIX` daily history
- filters to the requested date range
- merges the two series by date
- writes a single CSV with:
  - `date`
  - `vix_close`
  - `vvix_close`

## Default behavior

- default range is the last `365` days ending today
- output path defaults to `outputs/vix-vvix-history/vix_vvix_1y.csv`
- rows are kept only for dates that exist in both series

## Script

- `scripts/fetch_vix_vvix_history.py`

## Commands

Export the last year:

```bash
python skills/vix-vvix-history/scripts/fetch_vix_vvix_history.py
```

Export a custom rolling window:

```bash
python skills/vix-vvix-history/scripts/fetch_vix_vvix_history.py --days 180
```

Export an explicit date range:

```bash
python skills/vix-vvix-history/scripts/fetch_vix_vvix_history.py \
  --start-date 2025-01-01 \
  --end-date 2025-12-31
```

Write to a custom CSV path:

```bash
python skills/vix-vvix-history/scripts/fetch_vix_vvix_history.py \
  --days 365 \
  --csv-out outputs/vix-vvix-history/custom.csv
```
