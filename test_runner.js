const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: false });
  const context = await browser.newContext({
    viewport: { width: 1400, height: 900 }
  });
  const page = await context.newPage();

  const errors = [];
  const consoleMsgs = [];

  page.on('pageerror', e => errors.push({type: 'pageerror', message: e.message}));
  page.on('console', msg => consoleMsgs.push({type: msg.type(), text: msg.text().substring(0,200)}));

  // Test 1: Homepage
  console.log('--- Test 1: Homepage ---');
  await page.goto('http://127.0.0.1:8000/', { waitUntil: 'networkidle' });
  await page.waitForTimeout(2000);
  await page.screenshot({ path: '/Users/srujansai/Desktop/NRG/test_results/01_homepage.png' });

  // Check for backend banner
  const hasBackendBanner = await page.locator('text=Backend server unreachable').isVisible().catch(() => false);
  console.log('Backend unreachable banner:', hasBackendBanner);

  // Test 2: Researcher Login
  console.log('--- Test 2: Researcher Login ---');
  await page.click('button[type="submit"]');
  await page.waitForTimeout(5000);
  await page.screenshot({ path: '/Users/srujansai/Desktop/NRG/test_results/02_after_login.png' });

  // Check if dashboard loaded
  const url = page.url();
  console.log('URL after login:', url);
  const hasPublications = await page.locator('text=Publications').first().isVisible().catch(() => false);
  console.log('Has Publications text:', hasPublications);

  await context.close();
  await browser.close();

  require('fs').writeFileSync('/Users/srujansai/Desktop/NRG/test_results/errors.json', JSON.stringify(errors, null, 2));
  require('fs').writeFileSync('/Users/srujansai/Desktop/NRG/test_results/console.json', JSON.stringify(consoleMsgs.slice(-50), null, 2));

  console.log('DONE');
})();
