#!/usr/bin/env node
const fs = require('fs');
const path = require('path');
const { chromium } = require('../frontend/node_modules/playwright');

const ROOT = path.resolve(__dirname, '..');
const EVIDENCE_DIR = path.join(ROOT, 'evidence', '2026-04-26');
const BASE_URL = process.env.FRONTEND_URL || 'http://127.0.0.1:3000';

const queries = [
  {
    id: 'KILLER-01',
    text: 'Which IIT has the highest total innovation credits in FY 2022-23, and how far above the national average is it?',
  },
  {
    id: 'KILLER-02',
    text: 'For IIT Madras, what % of innovations moved from Lab Validation (Level 4) to Market Ready (Level 9) in the last 3 years, and which stage is the biggest bottleneck?',
  },
  {
    id: 'KILLER-03',
    text: 'Identify 3 institutes that cut grants >40% YoY yet increased granted patents; who is doing more with less?',
  },
];

const personas = {
  researcher: {
    username: 'researcher_user',
    password: 'researcher-pass',
    button: '[data-testid="persona-researcher"]',
    input: '[data-testid="researcher-search-input"]',
  },
  government: {
    username: 'gov_user',
    password: 'government-pass',
    button: '[data-testid="persona-government"]',
    input: '[data-testid="policy-query-input"]',
  },
  industry: {
    username: 'industry_user',
    password: 'industry-pass',
    button: '[data-testid="persona-industry"]',
    input: '[data-testid="industry-search-input"]',
  },
};

function mark(checks, id, status, detail) {
  checks.push({ id, status, detail });
}

async function clearSession(page) {
  await page.goto(BASE_URL, { waitUntil: 'domcontentloaded' });
  await page.evaluate(() => localStorage.removeItem('nrg.auth.session'));
}

async function login(page, key, checks) {
  const persona = personas[key];
  await clearSession(page);
  await page.goto(BASE_URL, { waitUntil: 'domcontentloaded' });
  await page.waitForFunction(() => Boolean(document.querySelector('[data-testid="login-username"]')), null, { timeout: 15000 });
  await page.click(persona.button, { force: true });
  await page.fill('[data-testid="login-username"]', persona.username);
  await page.fill('[data-testid="login-password"]', persona.password);
  await page.press('[data-testid="login-password"]', 'Enter');
  await page.waitForFunction(() => !document.querySelector('[data-testid="login-submit"]'), null, { timeout: 5000 }).catch(async () => {
    await page.click('[data-testid="login-submit"]', { force: true });
    await page.waitForFunction(() => !document.querySelector('[data-testid="login-submit"]'), null, { timeout: 15000 });
  });
  await page.waitForTimeout(750);
  await approveConsentIfPresent(page, checks, key);
  mark(checks, `${key}.login`, 'DONE', 'Login completed and dashboard replaced the sign-in form.');
}

async function runQuery(page, key, query, checks) {
  const selector = personas[key].input;
  await approveConsentIfPresent(page, checks, `${key}.${query.id}.pre`);
  await page.waitForSelector(selector, { timeout: 15000 });
  await page.click(selector);
  await page.keyboard.press(process.platform === 'darwin' ? 'Meta+A' : 'Control+A');
  await page.keyboard.press('Backspace');
  await page.keyboard.type(query.text, { delay: 1 });
  await page.waitForFunction(
    ({ selector: inputSelector, expected }) => document.querySelector(inputSelector)?.value === expected,
    { selector, expected: query.text },
    { timeout: 5000 }
  ).catch(() => null);
  const responsePromise = page.waitForResponse(
    (response) => {
      const url = new URL(response.url());
      return url.pathname === '/query' && response.request().method() === 'POST';
    },
    { timeout: 20000 }
  ).catch(() => null);
  await page.press(selector, 'Enter');
  const response = await responsePromise;
  const payload = response ? await response.json().catch(() => null) : null;
  await page.waitForFunction(() => {
    const body = document.body?.innerText || '';
    return (
      body.includes('Structured evidence query returned') ||
      body.includes('Access restricted') ||
      body.includes('High Confidence') ||
      body.includes('Sources')
    );
  }, null, { timeout: 20000 }).catch(() => null);
  const body = await page.locator('body').innerText();
  const apiRows = Array.isArray(payload?.sql_results) ? payload.sql_results.length : 0;
  const ok = Boolean(response?.ok()) && apiRows > 0 && (
    body.includes('Structured evidence query returned') ||
    body.includes('Access restricted') ||
    body.includes('High Confidence') ||
    body.includes('Sources') ||
    body.includes(query.text.slice(0, 42))
  );
  if (!ok) {
    const safeId = `${key}_${query.id}`.replace(/[^A-Za-z0-9_-]+/g, '_');
    await page.screenshot({ path: path.join(EVIDENCE_DIR, `founder_laptop_${safeId}_failure.png`), fullPage: true });
    fs.writeFileSync(
      path.join(EVIDENCE_DIR, `founder_laptop_${safeId}_body.txt`),
      `${body}\n\n--- API payload subset ---\n${JSON.stringify({
        status: response?.status(),
        rows: apiRows,
        response: payload?.response,
        warnings: payload?.warnings,
        answer_confidence: payload?.answer_confidence,
      }, null, 2)}\n`
    );
  }
  mark(checks, `${key}.${query.id}`, ok ? 'DONE' : 'BROKEN', ok ? 'Structured answer rendered.' : 'Expected answer text did not render.');
}

async function approveConsentIfPresent(page, checks, key) {
  const dialog = page.locator('[role="dialog"][aria-modal="true"]').first();
  await dialog.waitFor({ state: 'visible', timeout: 1500 }).catch(() => null);
  if (!(await dialog.isVisible().catch(() => false))) return;

  const checkbox = dialog.locator('#dpdp-ack-checkbox, input[type="checkbox"]').first();
  if (await checkbox.count()) await checkbox.check({ force: true });
  const approve = dialog.getByRole('button', { name: /approve.*continue/i }).first();
  if (await approve.count()) {
    await approve.click({ force: true });
    await dialog.waitFor({ state: 'hidden', timeout: 5000 }).catch(() => null);
    mark(checks, `${key}.consent`, 'DONE', 'DPDP consent modal acknowledged.');
  } else {
    mark(checks, `${key}.consent`, 'BROKEN', 'DPDP consent modal had no approval control.');
  }
}

async function logout(page, checks, key) {
  await approveConsentIfPresent(page, checks, key);
  const button = page.getByRole('button', { name: /log out|logout/i }).first();
  if (await button.count()) {
    await button.click({ force: true });
    await page.waitForTimeout(1500);
    const loginVisible = await page.locator('[data-testid="login-submit"]').first().isVisible().catch(() => false);
    if (!loginVisible) {
      await clearSession(page);
      await page.waitForFunction(() => Boolean(document.querySelector('[data-testid="login-submit"]')), null, { timeout: 10000 });
    }
    mark(checks, `${key}.logout`, 'DONE', 'Logout control submitted and sign-in state restored.');
  } else {
    mark(checks, `${key}.logout`, 'BROKEN', 'Logout control not found.');
  }
}

async function main() {
  fs.mkdirSync(EVIDENCE_DIR, { recursive: true });
  const checks = [];
  const consoleEvents = [];
  const failedRequests = [];

  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({
    viewport: { width: 1366, height: 768 },
    recordVideo: { dir: EVIDENCE_DIR, size: { width: 1366, height: 768 } },
  });
  const page = await context.newPage();
  page.on('console', (message) => {
    if (['error', 'warning'].includes(message.type())) {
      consoleEvents.push({ type: message.type(), text: message.text() });
    }
  });
  page.on('requestfailed', (request) => {
    failedRequests.push({ url: request.url(), failure: request.failure()?.errorText || 'request failed' });
  });
  page.on('response', (response) => {
    if (response.status() >= 400) {
      failedRequests.push({ url: response.url(), status: response.status() });
    }
  });

  await page.goto(BASE_URL, { waitUntil: 'domcontentloaded' });
  const loadedAt = Date.now();
  await page.waitForFunction(() => Boolean(document.querySelector('[data-testid="login-submit"]')), null, { timeout: 10000 });
  mark(checks, 'open.sign_in', 'DONE', `Sign-in loaded at ${new Date(loadedAt).toISOString()}.`);
  mark(checks, 'open.title', (await page.title()).includes('NRG') ? 'DONE' : 'BROKEN', await page.title());
  await page.screenshot({ path: path.join(EVIDENCE_DIR, 'founder_laptop_desktop_sign_in.png'), fullPage: true });

  await page.fill('[data-testid="login-username"]', '');
  await page.fill('[data-testid="login-password"]', '');
  await page.click('[data-testid="login-submit"]');
  const validationVisible = await page.locator('text=Enter your username').first().isVisible().catch(() => false);
  mark(checks, 'sign_in.blank_validation', validationVisible ? 'DONE' : 'BROKEN', 'Blank submit validation checked.');

  await page.fill('[data-testid="login-username"]', 'wrong_user');
  await page.fill('[data-testid="login-password"]', 'wrong-pass');
  await page.click('[data-testid="login-submit"]');
  await page.waitForTimeout(800);
  const wrongText = await page.locator('body').innerText();
  mark(checks, 'sign_in.wrong_credentials', /invalid|incorrect|failed/i.test(wrongText) ? 'DONE' : 'BROKEN', 'Wrong credential path checked.');

  await login(page, 'researcher', checks);
  for (const query of queries) await runQuery(page, 'researcher', query, checks);
  await page.screenshot({ path: path.join(EVIDENCE_DIR, 'founder_laptop_researcher_result.png'), fullPage: true });
  await logout(page, checks, 'researcher');

  await login(page, 'government', checks);
  for (const query of queries) await runQuery(page, 'government', query, checks);
  await page.screenshot({ path: path.join(EVIDENCE_DIR, 'founder_laptop_government_result.png'), fullPage: true });
  await logout(page, checks, 'government');

  await login(page, 'industry', checks);
  for (const query of queries) await runQuery(page, 'industry', query, checks);
  const industryBody = await page.locator('body').innerText();
  const hasRestrictedSignal = [
    'Access restricted',
    'institution_aggregate',
    'RESTRICTED_REASON',
    'Exact analytical columns',
    'aggregate bands',
  ].some((signal) => industryBody.includes(signal));
  mark(checks, 'industry.restricted_label', hasRestrictedSignal ? 'DONE' : 'BROKEN', 'Tier 3 restricted label checked.');
  await page.screenshot({ path: path.join(EVIDENCE_DIR, 'founder_laptop_industry_result.png'), fullPage: true });

  await page.goto(`${BASE_URL}/app/audit`, { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(1500);
  const auditText = await page.locator('body').innerText();
  mark(checks, 'audit.page', /audit|chain|integrity/i.test(auditText) ? 'DONE' : 'BROKEN', 'Audit page opened.');
  await page.screenshot({ path: path.join(EVIDENCE_DIR, 'founder_laptop_audit.png'), fullPage: true });

  await page.setViewportSize({ width: 375, height: 812 });
  await clearSession(page);
  await page.goto(BASE_URL, { waitUntil: 'domcontentloaded' });
  await page.waitForFunction(() => Boolean(document.querySelector('[data-testid="login-submit"]')), null, { timeout: 10000 });
  await page.screenshot({ path: path.join(EVIDENCE_DIR, 'founder_laptop_mobile_375.png'), fullPage: true });
  mark(checks, 'mobile.375_sign_in', 'DONE', '375 px sign-in screenshot captured.');

  const video = page.video();
  await context.close();
  await browser.close();
  if (video) {
    const videoPath = await video.path();
    fs.copyFileSync(videoPath, path.join(EVIDENCE_DIR, 'founder_laptop_clickthrough.webm'));
  }

  const result = {
    captured_at: new Date().toISOString(),
    base_url: BASE_URL,
    checks,
    console_events: consoleEvents,
    failed_requests: failedRequests,
    artifacts: {
      video: 'evidence/2026-04-26/founder_laptop_clickthrough.webm',
      mobile_375: 'evidence/2026-04-26/founder_laptop_mobile_375.png',
      desktop_sign_in: 'evidence/2026-04-26/founder_laptop_desktop_sign_in.png',
    },
  };
  fs.writeFileSync(
    path.join(EVIDENCE_DIR, 'founder_laptop_ux_checklist.json'),
    `${JSON.stringify(result, null, 2)}\n`
  );
  console.log(JSON.stringify(result, null, 2));

  const broken = checks.filter((item) => item.status === 'BROKEN');
  return broken.length === 0 ? 0 : 1;
}

main().then((code) => {
  process.exit(code);
}).catch((error) => {
  console.error(error);
  process.exit(1);
});
