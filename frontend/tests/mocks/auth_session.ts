import type { Page } from '@playwright/test'

type TestRole = 'researcher' | 'government' | 'industry'

const TEST_USERS: Record<TestRole, { username: string; tier: number }> = {
  researcher: { username: 'researcher@iitgn.ac.in', tier: 1 },
  government: { username: 'ministry@nrg.gov.in', tier: 2 },
  industry: { username: 'partner@industry.in', tier: 3 },
}

export async function installAuthenticatedSession(page: Page, role: TestRole = 'researcher') {
  const user = TEST_USERS[role]

  await page.addInitScript(({ role, user }) => {
    const session = JSON.stringify({
      accessToken: `${role}-e2e-access-token`,
      refreshToken: `${role}-e2e-refresh-token`,
      tokenType: 'bearer',
      user: {
        id: `e2e-${role}`,
        username: user.username,
        role,
        tier: user.tier,
      },
    })

    window.sessionStorage.setItem('nrg.auth.session', session)
    window.localStorage.setItem('nrg.auth.session', session)

    const grantedAt = Date.now()
    window.localStorage.setItem('nrg-dpdp-state', JSON.stringify({
      state: {
        consents: {
          research_access: {
            purpose: 'research_access',
            granted: true,
            grantedAt,
            retentionDays: 365,
            expiresAt: grantedAt + 365 * 24 * 60 * 60 * 1000,
          },
        },
        auditLog: [],
      },
      version: 0,
    }))
  }, { role, user })
}
