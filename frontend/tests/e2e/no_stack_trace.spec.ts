import { test, expect } from '@playwright/test'

test('error surfaces do not expose stack traces or raw exception markers', async ({ page }) => {
  await page.goto('/app/audit/event/hmac-release-001')

  await expect(page.locator('pre')).toHaveCount(0)
  await expect(page.getByText('Traceback')).toHaveCount(0)
  await expect(page.getByText('Error:')).toHaveCount(0)
})
