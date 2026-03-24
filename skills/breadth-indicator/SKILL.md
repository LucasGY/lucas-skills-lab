---
name: breadth-indicator
description: Read Barchart breadth indicators, also called market breadth, market width, 市场广度, or 市场宽度, for the Nasdaq 100 and S&P 500, including the percentages of components above the 5-day, 20-day, 50-day, 100-day, 150-day, and 200-day moving averages. Use this when the user wants the latest breadth values for Nasdaq 100 or S&P 500, JSON export, or direct widget screenshots from the Barchart index pages.
---

# Breadth Indicator

Use this skill when the user wants Barchart breadth data for:

- `Nasdaq 100`
- `S&P 500`

Common user wording that should trigger this skill:

- market breadth
- market width
- 市场广度
- 市场宽度
- `Percentage of Stocks Above Moving Average`

This skill supports two outputs:

- reading the moving-average breadth values directly
- exporting the widget screenshots for both indices

## Sources

- Nasdaq 100: `https://www.barchart.com/stocks/indices/nasdaq/nasdaq100`
- S&P 500: `https://www.barchart.com/stocks/indices/sp/sp500`

## What this skill does

- Opens Barchart with a browser-like Playwright session
- Reads the widget text for `5-day`, `20-day`, `50-day`, `100-day`, `150-day`, and `200-day` breadth values
- Exports JSON for one index or both indices
- Crops the widget region between the breadth heading and the next `Summary ... New Highs and Lows` section
- Saves standalone PNG screenshots for:
  - Nasdaq 100
  - S&P 500

## Default workflow

1. Run the script with `--index all` unless the user asks for only one index.
2. Save JSON if the user wants structured output.
3. Save screenshots when the user asks for images or wants the exact Barchart widget.
4. Return the exact percentages from the script output rather than reading them manually from the screenshot.

## Script

- Main script: `scripts/fetch_breadth_indicator.js`

## Commands

Read both indices and print JSON to stdout:

```bash
node skills/breadth-indicator/scripts/fetch_breadth_indicator.js --index all
```

Read only Nasdaq 100:

```bash
node skills/breadth-indicator/scripts/fetch_breadth_indicator.js --index nasdaq100
```

Read only S&P 500:

```bash
node skills/breadth-indicator/scripts/fetch_breadth_indicator.js --index sp500
```

Write JSON and screenshots for both indices:

```bash
node skills/breadth-indicator/scripts/fetch_breadth_indicator.js \
  --index all \
  --json-out outputs/breadth-indicator/breadth-values.json \
  --screenshot-dir outputs/breadth-indicator/screenshots
```

## Output files

Suggested output directory:

- `outputs/breadth-indicator/`

JSON:

- `breadth-values.json`

Screenshots:

- `nasdaq100-breadth-widget.png`
- `sp500-breadth-widget.png`

## Expected JSON shape

```json
{
  "nasdaq100": {
    "page_title": "Nasdaq 100 Index Chart, Components, Prices - Barchart.com",
    "source_url": "https://www.barchart.com/stocks/indices/nasdaq/nasdaq100",
    "widget_title": "Percentage of Nasdaq 100 Stocks Above Moving Average",
    "values": {
      "5_day": "46.53%",
      "20_day": "23.76%",
      "50_day": "20.79%",
      "100_day": "35.64%",
      "150_day": "40.59%",
      "200_day": "40.59%"
    }
  },
  "sp500": {
    "page_title": "S&P 500 Index Chart, Components, Prices - Barchart.com",
    "source_url": "https://www.barchart.com/stocks/indices/sp/sp500",
    "widget_title": "Percentage of S&P 500 Stocks Above Moving Average",
    "values": {
      "5_day": "47.91%",
      "20_day": "16.69%",
      "50_day": "22.86%",
      "100_day": "37.97%",
      "150_day": "43.33%",
      "200_day": "47.11%"
    }
  }
}
```

Values will change over time. Treat the numbers above as an example only.

## Notes

- Prefer the script over manual browser automation for this task.
- Use the widget screenshot only as a visual deliverable. Use the extracted JSON values for the actual answer.
- The script uses a browser-like user agent and visits the Barchart homepage first because direct automation access can trigger `403` responses.
