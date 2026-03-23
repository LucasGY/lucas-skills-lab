---
name: fetch-fedwatch
description: Fetch CME FedWatch public web data, especially the Current target rate table or the Target Rate -> Probabilities conditional meeting probabilities table, and export it to CSV, JSON, or automation scripts without using the paid FedWatch API.
metadata: {"openclaw":{"homepage":"https://www.cmegroup.com/markets/interest-rates/cme-fedwatch-tool.html?redirect=/trading/interest-rates/countdown-to-fomc.html","requires":{"anyBins":["python","node"]},"install":[{"id":"node-playwright","kind":"node","package":"playwright","bins":["playwright"],"label":"Install Playwright (node)"}]}}
---

# Fetch FedWatch

Use this skill when the user wants data from the public CME FedWatch web tool rather than the paid CME FedWatch API.

## What this skill does

- Fetches the `Current` target rate table
- Fetches `CME FedWatch Tool - Conditional Meeting Probabilities`
- Exports the result to CSV
- Provides either Node or Python automation

## Workflow

1. Use the public CME page as the `Referer`.
2. Load the QuikStrike FedWatch tool URL.
3. Wait for the embedded `QuikStrikeView.aspx` frame to load.
4. For current target rate data, stay on the default `Current` tab and extract the `Target Rate (bps)` table.
5. For conditional meeting probabilities, click the `Probabilities` tab and extract the table titled `CME FedWatch Tool - Conditional Meeting Probabilities`.
6. Export to CSV or transform to JSON/DataFrame as requested.

## Important constraints

- Do not use the ShareThis or analytics requests; they are unrelated tracking calls.
- The public FedWatch page embeds the real tool in a QuikStrike frame.
- Direct access without a CME `Referer` can be denied.
- Prefer Playwright over raw `requests` because the tool is an old ASP.NET/WebForms UI and the tab switch is browser-driven.

## Scripts

- Node script: `scripts/fetch_fedwatch_conditional.js`
- Python script: `scripts/fetch_fedwatch_conditional.py`

## Script modes

- `current`: Export the current target rate table
- `conditional`: Export the conditional meeting probabilities table

## Outputs

Defaults:
- `current` -> `fedwatch_current_target_rate.csv`
- `conditional` -> `fedwatch_conditional_probabilities.csv`
