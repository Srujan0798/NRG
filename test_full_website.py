#!/usr/bin/env python3
"""Comprehensive website test - captures all errors and screenshots."""
import subprocess, time, json, os, sys

# Start backend in background
print("=== STARTING BACKEND ===")
proc = subprocess.Popen(
    ["python3", "-m", "uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"],
    stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd="/Users/srujansai/Desktop/NRG"
)
time.sleep(3)

# Start Playwright test
print("=== RUNNING BROWSER TESTS ===")
test_code = '''
const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: false });
  const context = await browser.newContext({
    viewport: { width: 1400, height: 900 },
    recordHar: { path: '/Users/srujansai/Desktop/NRG/test_results/network.har' }
  });
  const page = await context.newPage();

  const errors = [];
  const consoleMsgs = [];
  const requests = [];

  page.on('pageerror', e => errors.push({type: 'pageerror', message: e.message}));
  page.on('console', msg => consoleMsgs.push({type: msg.type(), text: msg.text()}));
  page.on('requestfinished', req => {
    if (req.url().includes('/login') || req.url().includes('/health') || req.url().includes('/stats') || req.url().includes('/researchers')) {
      requests.push({url: req.url(), method: req.method(), status: req.response()?.status()});
    }
  });

  // Test 1: Homepage
  console.log('--- Test 1: Homepage ---');
  await page.goto('http://localhost:8000/', { waitUntil: 'networkidle' });
  await page.waitForTimeout(2000);
  await page.screenshot({ path: '/Users/srujansai/Desktop/NRG/test_results/01_homepage.png' });

  // Test 2: Researcher Login
  console.log('--- Test 2: Researcher Login ---');
  await page.goto('http://localhost:8000/', { waitUntil: 'networkidle' });
  await page.click('button[type="submit"]');
  await page.waitForTimeout(5000);
  await page.screenshot({ path: '/Users/srujansai/Desktop/NRG/test_results/02_after_login.png' });

  // Test 3: Government Login
  console.log('--- Test 3: Government Login ---');
  await page.reload();
  await page.waitForTimeout(1000);
  await page.click('button[type="button"]:has-text("Government")');
  await page.waitForTimeout(500);
  await page.click('button[type="submit"]');
  await page.waitForTimeout(5000);
  await page.screenshot({ path: '/Users/srujansai/Desktop/NRG/test_results/03_gov_login.png' });

  // Test 4: Industry Login
  console.log('--- Test 4: Industry Login ---');
  await page.reload();
  await page.waitForTimeout(1000);
  await page.click('button[type="button"]:has-text("Industry")');
  await page.waitForTimeout(500);
  await page.click('button[type="submit"]');
  await page.waitForTimeout(5000);
  await page.screenshot({ path: '/Users/srujansai/Desktop/NRG/test_results/04_industry_login.png' });

  await context.close();
  await browser.close();

  // Write results
  require('fs').writeFileSync('/Users/srujansai/Desktop/NRG/test_results/errors.json', JSON.stringify(errors, null, 2));
  require('fs').writeFileSync('/Users/srujansai/Desktop/NRG/test_results/console.json', JSON.stringify(consoleMsgs, null, 2));
  require('fs').writeFileSync('/Users/srujansai/Desktop/NRG/test_results/requests.json', JSON.stringify(requests, null, 2));

  console.log('DONE');
})();
'''

os.makedirs("/Users/srujansai/Desktop/NRG/test_results", exist_ok=True)
with open("/Users/srujansai/Desktop/NRG/test_runner.js", "w") as f:
    f.write(test_code)

result = subprocess.run(
    ["node", "/Users/srujansai/Desktop/NRG/test_runner.js"],
    capture_output=True, text=True, timeout=120
)
print("STDOUT:", result.stdout)
print("STDERR:", result.stderr)

proc.terminate()

# Read results
for fname in ['errors.json', 'console.json', 'requests.json']:
    fpath = f"/Users/srujansai/Desktop/NRG/test_results/{fname}"
    if os.path.exists(fpath):
        print(f"\n=== {fname} ===")
        with open(fpath) as f:
            data = json.load(f)
            print(json.dumps(data, indent=2)[:3000])
