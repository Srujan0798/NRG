const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: false });
  const results = [];

  for (const persona of [
    { name: 'Researcher', card: 'Researcher' },
    { name: 'Government', card: 'Government' },
    { name: 'Industry', card: 'Industry' }
  ]) {
    // Fresh context for each persona to avoid session leakage
    const context = await browser.newContext({ viewport: { width: 1400, height: 900 } });
    const page = await context.newPage();
    const consoleMsgs = [];
    page.on('console', msg => { if (msg.type() === 'error') consoleMsgs.push(msg.text().substring(0,150)); });

    console.log(`\n=== Testing ${persona.name} ===`);
    await page.goto('http://127.0.0.1:8000/', { waitUntil: 'networkidle' });
    await page.waitForTimeout(1500);

    if (persona.name !== 'Researcher') {
      await page.locator('button[type="button"]').filter({ hasText: persona.card }).first().click();
      await page.waitForTimeout(500);
    }
    await page.screenshot({ path: `test_results/${persona.name.toLowerCase()}_login.png` });

    await page.click('button[type="submit"]');
    await page.waitForTimeout(4000);

    // Handle DPDP consent
    const hasConsent = await page.locator('text=DPDP Consent Required').isVisible().catch(() => false);
    if (hasConsent) {
      await page.locator('input[type="checkbox"]').first().check();
      await page.waitForTimeout(300);
      await page.locator('button:has-text("Approve & Continue")').click();
      await page.waitForTimeout(2000);
    }

    await page.screenshot({ path: `test_results/${persona.name.toLowerCase()}_dashboard.png` });

    const url = page.url();
    const title = await page.title().catch(() => 'no title');
    results.push({ persona: persona.name, url, title, consoleErrors: consoleMsgs.length, hasConsent });
    console.log(`${persona.name}: URL=${url}, Title=${title}, Consent=${hasConsent}, ConsoleErrors=${consoleMsgs.length}`);

    await context.close();
  }

  require('fs').writeFileSync('test_results/all_personas.json', JSON.stringify(results, null, 2));
  await browser.close();
  console.log('\nAll tests done!');
})();
