---
name: cnn-fear-greed-index
description: Fetch CNN Fear & Greed Index data from the public CNN dataviz endpoint, including the current score, rating, previous close/week/month/year values, and historical timeline data. Use this when the user wants the latest CNN Fear & Greed reading, the current fear/greed level, a timeline export, CSV/JSON output, or screenshots of the Timeline or Overview widgets.
---

# CNN Fear & Greed Index

Use this skill when the user wants CNN Fear & Greed Index data. Prefer data fetches over screenshots.

## What this skill does

- Reads the current Fear & Greed score and rating directly
- Fetches previous close, 1 week ago, 1 month ago, and 1 year ago values
- Fetches the historical timeline series
- Exports raw JSON and optional CSV
- Captures a screenshot of the `Timeline` widget through the stable local-HTML workflow
- Captures a screenshot of the `Overview` widget through the same stable local-HTML workflow
- Removes the right sidebar by default and keeps only the requested widget area

## Primary source

CNN's public page:

- `https://www.cnn.com/markets/fear-and-greed`

The page calls this public dataviz endpoint:

- `https://production.dataviz.cnn.io/index/fearandgreed/graphdata`

## Important constraints

Do not call the dataviz endpoint with a bare client. CNN often returns:

```text
I'm a teapot. You're a bot.
```

Always send browser-like headers:

- `User-Agent: Mozilla/5.0 ...`
- `Referer: https://www.cnn.com/markets/fear-and-greed`
- `Origin: https://www.cnn.com`
- `Accept: application/json,text/plain,*/*`

Do not default to the live-page screenshot flow. The live CNN page is unstable in automation and can return `Unknown Error`.

## Default workflow

1. Use `scripts/read_current_fng.py` when the user only wants the latest index and level.
2. Use `scripts/fetch_cnn_fng.py` when the user wants timeline data or exports.
3. Read `fear_and_greed_historical.data` for the timeline series.
4. If the user wants exports, write JSON and CSV.
5. If the user wants a screenshot, use the stable local-HTML screenshot workflow below.

## Scripts

- Current value reader: `scripts/read_current_fng.py`
- Data fetch: `scripts/fetch_cnn_fng.py`
- Save local page: `scripts/save_local_page.py`
- Screenshot wrapper: `scripts/capture_timeline_widget.sh`
- Crop helper: `scripts/crop_timeline_widget.py`

## Current value command

Read the current index and fear/greed level directly:

```bash
python skills/cnn-fear-greed-index/scripts/read_current_fng.py
```

This prints:

- `score`
- `rating`
- `timestamp`
- `previous_close`
- `previous_1_week`
- `previous_1_month`
- `previous_1_year`

## Data fetch commands

Fetch JSON only:

```bash
python skills/cnn-fear-greed-index/scripts/fetch_cnn_fng.py
```

Fetch JSON and CSV:

```bash
python skills/cnn-fear-greed-index/scripts/fetch_cnn_fng.py \
  --json-out outputs/cnn-fear-greed/cnn-fear-greed.json \
  --csv-out outputs/cnn-fear-greed/cnn-fear-greed-timeline.csv
```

## Output files

Default output directory:

- `outputs/cnn-fear-greed/`

Data files:

- `cnn-fear-greed.json`
- `cnn-fear-greed-timeline.csv`
- `cnn-fear-greed-page.html`

Screenshot files:

- `cnn-fear-greed-timeline-widget.png`
- `cnn-fear-greed-timeline-widget-only.png`
- `cnn-fear-greed-overview-widget.png`
- `cnn-fear-greed-overview-widget-only.png`

Default screenshot deliverable for timeline:

- `cnn-fear-greed-timeline-widget-only.png`

Default screenshot deliverable for overview:

- `cnn-fear-greed-overview-widget-only.png`

## Screenshot workflow

Use this workflow by default for screenshots.

Timeline:

```bash
bash skills/cnn-fear-greed-index/scripts/capture_timeline_widget.sh timeline
```

Overview:

```bash
bash skills/cnn-fear-greed-index/scripts/capture_timeline_widget.sh overview
```

The workflow is the proven stable path:

1. Download the CNN page HTML locally with browser-like headers.
2. Inject `<base href="https://www.cnn.com/">` into the local HTML.
3. Open the local HTML with `agent-browser`.
4. Dismiss the consent wall if it appears.
5. Click the requested tab via DOM lookup.
6. Scroll to the widget position.
7. Save a viewport screenshot.
8. Crop out the right sidebar and keep only the requested widget area.

Do not replace this with the live-page screenshot path unless you first re-verify that live CNN rendering is stable.

## Cropping rule

The final image should remove the right sidebar and keep only the requested widget area.

Timeline crop keeps:

- tab toggle
- line chart
- right axis labels inside the widget
- bottom axis labels
- timestamp

Overview crop keeps:

- tab toggle
- gauge graphic
- current score
- previous close, week, month, year summary values
- timestamp

The current stable crops are based on the viewport screenshot and remove the right rail by default.

## Notes

- Prefer data from the dataviz endpoint over OCR or scraping the visible chart.
- The page can change layout; screenshots are less stable than data fetches.
- If the user asks for the latest reading, return the exact timestamp from the payload.
