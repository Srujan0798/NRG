const { chromium } = require('playwright');

async function runTests() {
  const browser = await chromium.launch({ headless: true });
  const results = [];
  const screenshots = [];
  
  // Test 1: Researcher (Tier 1)
  console.log('\n=== Testing Researcher (Tier 1) ===');
  {
    const context = await browser.newContext();
    const page = await context.newPage();
    const errors = [];
    page.on('console', msg => { if (msg.type() === 'error') errors.push(msg.text()); });
    page.on('pageerror', err => errors.push(err.message));
    
    try {
      await page.goto('http://localhost:3000', { timeout: 30000, waitUntil: 'domcontentloaded' });
      await page.waitForTimeout(3000);
      await page.screenshot({ path: '/tmp/nrg-t1-login.png' });
      
      await page.getByRole('button', { name: /Researcher.*Tier 1/i }).click();
      await page.waitForTimeout(1000);
      
      await page.locator('input[type="text"]').fill('researcher_user');
      await page.locator('input[type="password"]').fill('researcher-pass');
      await page.locator('button[type="submit"]').click();
      
      // Wait for dashboard
      await page.waitForFunction(() => document.body.textContent.includes('Researcher Workspace'), { timeout: 30000 });
      await page.waitForTimeout(2000);
      await page.screenshot({ path: '/tmp/nrg-t1-dashboard.png' });
      screenshots.push('/tmp/nrg-t1-dashboard.png');
      
      // Test query
      const queryInput = page.locator('input[placeholder*="research" i], input[placeholder*="topic" i]').first();
      if (await queryInput.isVisible({ timeout: 5000 })) {
        await queryInput.fill('machine learning India');
        await page.locator('button[type="submit"]').or(page.locator('button:has-text("Search")')).first().click();
        await page.waitForTimeout(10000);
        await page.screenshot({ path: '/tmp/nrg-t1-query.png' });
        screenshots.push('/tmp/nrg-t1-query.png');
      }
      
      results.push({ persona: 'Researcher (Tier 1)', status: 'PASS', errors, screenshots: ['/tmp/nrg-t1-login.png', '/tmp/nrg-t1-dashboard.png', '/tmp/nrg-t1-query.png'].filter(f => f) });
    } catch (e) {
      await page.screenshot({ path: '/tmp/nrg-t1-error.png' }).catch(() => {});
      results.push({ persona: 'Researcher (Tier 1)', status: 'FAIL', errors, error: e.message });
    }
    await context.close();
  }
  
  // Test 2: Government (Tier 2)
  console.log('\n=== Testing Government (Tier 2) ===');
  {
    const context = await browser.newContext();
    const page = await context.newPage();
    const errors = [];
    page.on('console', msg => { if (msg.type() === 'error') errors.push(msg.text()); });
    page.on('pageerror', err => errors.push(err.message));
    
    try {
      await page.goto('http://localhost:3000', { timeout: 30000, waitUntil: 'domcontentloaded' });
      await page.waitForTimeout(3000);
      await page.screenshot({ path: '/tmp/nrg-t2-login.png' });
      
      await page.getByRole('button', { name: /Government.*Tier 2/i }).click();
      await page.waitForTimeout(1000);
      
      await page.locator('input[type="text"]').fill('gov_user');
      await page.locator('input[type="password"]').fill('government-pass');
      await page.locator('button[type="submit"]').click();
      
      await page.waitForFunction(() => document.body.textContent.includes('Government Analytics'), { timeout: 30000 });
      await page.waitForTimeout(2000);
      await page.screenshot({ path: '/tmp/nrg-t2-dashboard.png' });
      screenshots.push('/tmp/nrg-t2-dashboard.png');
      
      results.push({ persona: 'Government (Tier 2)', status: 'PASS', errors });
    } catch (e) {
      await page.screenshot({ path: '/tmp/nrg-t2-error.png' }).catch(() => {});
      results.push({ persona: 'Government (Tier 2)', status: 'FAIL', errors, error: e.message });
    }
    await context.close();
  }
  
  // Test 3: Industry (Tier 3)
  console.log('\n=== Testing Industry (Tier 3) ===');
  {
    const context = await browser.newContext();
    const page = await context.newPage();
    const errors = [];
    page.on('console', msg => { if (msg.type() === 'error') errors.push(msg.text()); });
    page.on('pageerror', err => errors.push(err.message));
    
    try {
      await page.goto('http://localhost:3000', { timeout: 30000, waitUntil: 'domcontentloaded' });
      await page.waitForTimeout(3000);
      await page.screenshot({ path: '/tmp/nrg-t3-login.png' });
      
      await page.getByRole('button', { name: /Industry.*Tier 3/i }).click();
      await page.waitForTimeout(1000);
      
      await page.locator('input[type="text"]').fill('industry_user');
      await page.locator('input[type="password"]').fill('industry-pass');
      await page.locator('button[type="submit"]').click();
      
      await page.waitForFunction(() => document.body.textContent.includes('Industry Innovation'), { timeout: 30000 });
      await page.waitForTimeout(2000);
      await page.screenshot({ path: '/tmp/nrg-t3-dashboard.png' });
      screenshots.push('/tmp/nrg-t3-dashboard.png');
      
      results.push({ persona: 'Industry (Tier 3)', status: 'PASS', errors });
    } catch (e) {
      await page.screenshot({ path: '/tmp/nrg-t3-error.png' }).catch(() => {});
      results.push({ persona: 'Industry (Tier 3)', status: 'FAIL', errors, error: e.message });
    }
    await context.close();
  }
  
  await browser.close();
  
  console.log('\n' + '='.repeat(60));
  console.log('NRG FRONTEND E2E TEST RESULTS');
  console.log('='.repeat(60));
  
  let allPassed = true;
  results.forEach(r => {
    const icon = r.status === 'PASS' ? '✅' : '❌';
    console.log(`${icon} ${r.persona}: ${r.status}`);
    if (r.errors.length > 0) {
      console.log(`   Console Errors: ${r.errors.slice(0, 3).join('; ')}`);
    }
    if (r.error) {
      console.log(`   Error: ${r.error.substring(0, 150)}`);
      allPassed = false;
    }
  });
  
  console.log('\nScreenshots saved to /tmp/nrg-*.png');
  console.log('='.repeat(60));
  
  return results;
}

runTests().catch(console.error);
