import { test, expect } from '@playwright/test'
import { installStreamingQueryMock } from '../mocks/sse_server'

test('hybrid answer exposes SQL and document proof in the source drawer', async ({ page }) => {
  await installStreamingQueryMock(page)
  await page.addInitScript(() => {
    window.sessionStorage.setItem('nrg.auth.session', JSON.stringify({
      accessToken: '',
      refreshToken: '',
      tokenType: 'cookie',
      user: {
        id: 'e2e-researcher',
        username: 'researcher@iitgn.ac.in',
        role: 'researcher',
        tier: 1,
      },
    }))
  })
  await page.goto('/app')

  await expect(page.getByTestId('hero-search-input')).toBeVisible()
  await page.getByTestId('hero-search-input').fill('top funding agencies and explain the policy pattern')
  await page.getByTestId('hero-search-input').press('Enter')

  await expect(page.getByTestId('streaming-answer-panel')).toBeVisible()
  await expect(page.getByTestId('source-data-toggle')).toBeVisible()
  await page.getByTestId('source-data-toggle').click()

  const sourcePanel = page.getByTestId('source-data-panel')
  await expect(sourcePanel).toContainText('Evidence mix')
  await expect(sourcePanel).toContainText('Structured SQL rows')
  await expect(sourcePanel).toContainText('Document excerpts')
  await expect(sourcePanel).toContainText('SELECT institute')
  await expect(sourcePanel).toContainText('hmac-renewable-001')
})
