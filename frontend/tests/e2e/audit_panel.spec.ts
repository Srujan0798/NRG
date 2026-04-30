import { test, expect } from '@playwright/test'
import { installAuthenticatedSession } from '../mocks/auth_session'

test('audit panel lists events and opens event proof drawer', async ({ page }) => {
  await installAuthenticatedSession(page)
  await page.goto('/app/audit')

  await expect(page.getByTestId('audit-list')).toBeVisible()
  await expect(page.getByTestId('audit-row').first()).toBeVisible()

  await page.getByTestId('audit-row').first().click()
  await expect(page.getByTestId('audit-event-drawer')).toBeVisible()
  await expect(page.getByTestId('hmac-proof')).toBeVisible()
})

test('single audit event route renders chain neighborhood', async ({ page }) => {
  await installAuthenticatedSession(page)
  await page.goto('/app/audit/event/hmac-release-001')

  await expect(page.getByTestId('hmac-proof')).toBeVisible()
  await page.getByTestId('verify-hmac-button').click()
  await expect(page.getByTestId('hmac-proof-status')).toContainText('Chain intact')
})
