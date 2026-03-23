const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');

const TOOL_URL = 'https://cmegroup-tools.quikstrike.net/User/QuikStrikeTools.aspx?viewitemid=IntegratedFedWatchTool&userId=lwolf&jobRole=&company=&companyType=&userId=&jobRole=&company=&companyType=';
const REFERER = 'https://www.cmegroup.com/markets/interest-rates/cme-fedwatch-tool.html?redirect=/trading/interest-rates/countdown-to-fomc.html';

function clean(text) {
  return String(text || '').replace(/\s+/g, ' ').trim();
}

function csvEscape(value) {
  const s = String(value ?? '');
  return /[",\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
}

async function loadFrame() {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  await page.goto(TOOL_URL, {
    referer: REFERER,
    waitUntil: 'domcontentloaded',
    timeout: 120000,
  });
  await page.waitForTimeout(8000);
  const frame = page.frames().find((f) => /QuikStrikeView\.aspx/.test(f.url())) || page.mainFrame();
  return { browser, page, frame };
}

async function extractTable(table) {
  await table.waitFor({ state: 'visible', timeout: 30000 });
  const rowLocators = table.locator('tr');
  const rowCount = await rowLocators.count();
  const firstRowHeaders = (await rowLocators.nth(0).locator('th').allTextContents()).map(clean);
  const secondRowHeaders = rowCount > 1 ? (await rowLocators.nth(1).locator('th').allTextContents()).map(clean) : [];
  const headers = secondRowHeaders.length > 1
    ? (firstRowHeaders.length > secondRowHeaders.length ? [firstRowHeaders[0], ...secondRowHeaders] : secondRowHeaders)
    : firstRowHeaders;
  const startIndex = secondRowHeaders.length > 1 ? 2 : 1;
  const rows = await rowLocators.evaluateAll((trs, start) =>
    trs
      .slice(start)
      .map((tr) => Array.from(tr.querySelectorAll('td,th')).map((cell) => cell.textContent.replace(/\s+/g, ' ').trim()))
      .filter((row) => row.length && row.some(Boolean)),
    startIndex
  );
  return { headers, rows };
}

function writeCsv(headers, rows, outputPath) {
  const csv = [headers.map(csvEscape).join(','), ...rows.map((row) => row.map(csvEscape).join(','))].join('\n');
  fs.writeFileSync(path.resolve(outputPath), csv, 'utf8');
}

async function fetchConditionalMeetingProbabilities(outputPath = 'fedwatch_conditional_probabilities.csv') {
  const { browser, frame } = await loadFrame();
  try {
    await frame.locator('#ctl00_MainContent_ucViewControl_IntegratedFedWatchTool_lbPTree').click();
    await new Promise((r) => setTimeout(r, 5000));
    const table = frame.locator('table:has-text("Conditional Meeting Probabilities")').first();
    const { headers, rows } = await extractTable(table);
    writeCsv(headers, rows, outputPath);
    return { mode: 'conditional', outputPath: path.resolve(outputPath), headers, rowCount: rows.length, rows };
  } finally {
    await browser.close();
  }
}

async function fetchCurrentTargetRate(outputPath = 'fedwatch_current_target_rate.csv') {
  const { browser, frame } = await loadFrame();
  try {
    const table = frame.locator('table.grid-thm.grid-thm-v2.w-lg').last();
    const { headers, rows } = await extractTable(table);
    const normalizedHeaders = rows.length && rows[0].length === headers.length + 1 ? ['Target Rate (bps)', ...headers] : headers;
    writeCsv(normalizedHeaders, rows, outputPath);
    return { mode: 'current', outputPath: path.resolve(outputPath), headers: normalizedHeaders, rowCount: rows.length, rows };
  } finally {
    await browser.close();
  }
}

if (require.main === module) {
  const mode = (process.argv[2] || 'conditional').toLowerCase();
  const outputPath = process.argv[3] || (mode === 'current' ? 'fedwatch_current_target_rate.csv' : 'fedwatch_conditional_probabilities.csv');
  const runner = mode === 'current' ? fetchCurrentTargetRate : fetchConditionalMeetingProbabilities;
  runner(outputPath)
    .then((result) => {
      console.log(JSON.stringify({
        mode: result.mode,
        outputPath: result.outputPath,
        headers: result.headers,
        rowCount: result.rowCount,
        sampleRows: result.rows.slice(0, 3),
      }, null, 2));
    })
    .catch((err) => {
      console.error(err);
      process.exit(1);
    });
}

module.exports = { fetchConditionalMeetingProbabilities, fetchCurrentTargetRate };
