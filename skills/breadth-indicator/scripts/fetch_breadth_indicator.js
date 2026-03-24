#!/usr/bin/env node

const fs = require("fs");
const path = require("path");
const { chromium } = require("playwright");

const INDEX_CONFIG = {
  nasdaq100: {
    slug: "nasdaq100",
    url: "https://www.barchart.com/stocks/indices/nasdaq/nasdaq100",
    widgetTitle: "Percentage of Nasdaq 100 Stocks Above Moving Average",
    summaryTitle: "Summary of Nasdaq 100 Stocks With New Highs and Lows",
    screenshotName: "nasdaq100-breadth-widget.png",
  },
  sp500: {
    slug: "sp500",
    url: "https://www.barchart.com/stocks/indices/sp/sp500",
    widgetTitle: "Percentage of S&P 500 Stocks Above Moving Average",
    summaryTitle: "Summary of S&P 500 Stocks With New Highs and Lows",
    screenshotName: "sp500-breadth-widget.png",
  },
};

const DEFAULT_USER_AGENT =
  "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36";

function parseArgs(argv) {
  const args = {
    index: "all",
    jsonOut: null,
    screenshotDir: null,
  };

  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];
    if (arg === "--index") {
      args.index = argv[++i];
    } else if (arg === "--json-out") {
      args.jsonOut = argv[++i];
    } else if (arg === "--screenshot-dir") {
      args.screenshotDir = argv[++i];
    } else if (arg === "--help" || arg === "-h") {
      printHelp();
      process.exit(0);
    } else {
      throw new Error(`Unknown argument: ${arg}`);
    }
  }

  if (!args.index || !["nasdaq100", "sp500", "all"].includes(args.index)) {
    throw new Error("--index must be one of: nasdaq100, sp500, all");
  }

  return args;
}

function printHelp() {
  console.log(`Usage:
  node skills/breadth-indicator/scripts/fetch_breadth_indicator.js --index all
  node skills/breadth-indicator/scripts/fetch_breadth_indicator.js --index nasdaq100
  node skills/breadth-indicator/scripts/fetch_breadth_indicator.js --index sp500 --json-out outputs/breadth-indicator/sp500.json
  node skills/breadth-indicator/scripts/fetch_breadth_indicator.js --index all --json-out outputs/breadth-indicator/breadth-values.json --screenshot-dir outputs/breadth-indicator/screenshots
`);
}

function ensureDirForFile(filePath) {
  fs.mkdirSync(path.dirname(filePath), { recursive: true });
}

function ensureDir(dirPath) {
  fs.mkdirSync(dirPath, { recursive: true });
}

function extractValuesFromText(segmentText) {
  const labels = ["5", "20", "50", "100", "150", "200"];
  const values = {};

  for (const label of labels) {
    const regex = new RegExp(`${label}-DAY AVERAGE\\s+([0-9]+(?:\\.[0-9]+)?%)`, "i");
    const match = segmentText.match(regex);
    if (!match) {
      throw new Error(`Could not find ${label}-day breadth value in widget text`);
    }
    values[`${label}_day`] = match[1];
  }

  return values;
}

async function visitHome(page) {
  await page.goto("https://www.barchart.com/", {
    waitUntil: "domcontentloaded",
    timeout: 60000,
  });
  await page.waitForTimeout(2500);
}

async function captureIndex(page, config, screenshotDir) {
  await page.goto(config.url, {
    waitUntil: "domcontentloaded",
    timeout: 60000,
  });
  await page.waitForTimeout(5000);

  const pageTitle = await page.title();
  const start = page.locator(`h4:has-text("${config.widgetTitle}")`).first();
  const end = page.locator(`h4:has-text("${config.summaryTitle}")`).first();

  await start.scrollIntoViewIfNeeded();
  await page.waitForTimeout(1200);

  const startBox = await start.boundingBox();
  const endBox = await end.boundingBox();

  if (!startBox || !endBox) {
    throw new Error(`Could not find widget bounds for ${config.slug}`);
  }

  const segmentText = await page.evaluate(
    ({ widgetTitle, summaryTitle }) => {
      const text = document.body.innerText || "";
      const startIndex = text.indexOf(widgetTitle);
      const endIndex = text.indexOf(summaryTitle);
      if (startIndex === -1 || endIndex === -1 || endIndex <= startIndex) {
        return null;
      }
      return text.slice(startIndex, endIndex);
    },
    {
      widgetTitle: config.widgetTitle,
      summaryTitle: config.summaryTitle,
    }
  );

  if (!segmentText) {
    throw new Error(`Could not extract widget text for ${config.slug}`);
  }

  const result = {
    page_title: pageTitle,
    source_url: config.url,
    widget_title: config.widgetTitle,
    values: extractValuesFromText(segmentText),
  };

  if (screenshotDir) {
    ensureDir(screenshotDir);
    const clip = {
      x: Math.max(0, startBox.x - 8),
      y: Math.max(0, startBox.y - 12),
      width: Math.min(1100, page.viewportSize().width - Math.max(0, startBox.x - 8) - 10),
      height: Math.max(220, endBox.y - startBox.y + 16),
    };
    const screenshotPath = path.resolve(screenshotDir, config.screenshotName);
    await page.screenshot({ path: screenshotPath, clip });
    result.screenshot = screenshotPath;
  }

  return result;
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  const targets = args.index === "all" ? ["nasdaq100", "sp500"] : [args.index];

  const browser = await chromium.launch({
    headless: true,
    args: ["--disable-blink-features=AutomationControlled"],
  });

  const context = await browser.newContext({
    userAgent: DEFAULT_USER_AGENT,
    viewport: { width: 1440, height: 1400 },
    locale: "en-US",
  });

  try {
    const page = await context.newPage();
    await visitHome(page);

    const output = {};
    for (const key of targets) {
      output[key] = await captureIndex(page, INDEX_CONFIG[key], args.screenshotDir);
    }

    const json = JSON.stringify(output, null, 2);

    if (args.jsonOut) {
      const jsonPath = path.resolve(args.jsonOut);
      ensureDirForFile(jsonPath);
      fs.writeFileSync(jsonPath, `${json}\n`, "utf8");
    }

    process.stdout.write(`${json}\n`);
  } finally {
    await context.close();
    await browser.close();
  }
}

main().catch((error) => {
  console.error(error.message || String(error));
  process.exit(1);
});
