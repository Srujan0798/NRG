import { test, expect } from '@playwright/test'

test.skip(process.env.NRG_LIVE_BACKEND_E2E !== '1', 'requires a live backend through frontend/e2e-server.js')

test('live backend hybrid proof reaches the source drawer', async ({ page }) => {
  const loginResponse = await page.request.post('/login', {
    data: {
      username: 'researcher@iitgn.ac.in',
      password: 'Researcher@2026',
    },
  })
  expect(loginResponse.ok()).toBeTruthy()
  const loginPayload = await loginResponse.json()

  await page.addInitScript((user) => {
    window.sessionStorage.setItem('nrg.auth.session', JSON.stringify({
      accessToken: '',
      refreshToken: '',
      tokenType: 'cookie',
      user,
    }))
  }, loginPayload.user)

  await page.goto('/app')
  await expect(page.getByTestId('answer-engine-query')).toBeVisible()

  await page.getByTestId('answer-engine-query').fill('Top funding agencies and explain the policy pattern')
  await page.getByTestId('answer-engine-query').press('Enter')

  await expect(page.getByTestId('source-data-toggle')).toBeVisible({ timeout: 20000 })
  await page.getByTestId('source-data-toggle').click()

  const sourcePanel = page.getByTestId('source-data-panel')
  await expect(sourcePanel).toContainText('Evidence mix')
  await expect(sourcePanel).toContainText('Structured SQL rows')
  await expect(sourcePanel).toContainText('Document excerpts')
  await expect(sourcePanel).toContainText('SELECT gov_organisation_name')
  await expect(sourcePanel).toContainText('This answer combines measurable database evidence')
})
