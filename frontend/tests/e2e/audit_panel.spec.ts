import { test, expect } from '@playwright/test'

test('audit panel virtualizes events and opens event proof drawer', async ({ page }) => {
  await page.goto('/app/audit')

  await expect(page.getByTestId('audit-event-list')).toHaveAttribute('data-virtualized', 'react-window')
  await expect(page.getByTestId('audit-event-row').first()).toBeVisible()

  await page.getByTestId('audit-event-row').first().click()
  await expect(page.getByTestId('citation-drawer')).toBeVisible()
  await expect(page.getByTestId('hmac-proof')).toBeVisible()
})

test('single audit event route renders chain neighborhood', async ({ page }) => {
  await page.goto('/app/audit/event/hmac-release-001')

  await expect(page.getByTestId('hmac-proof')).toBeVisible()
  await page.getByTestId('verify-hmac-button').click()
  await expect(page.getByTestId('hmac-proof-status')).toContainText('Chain intact')
})
