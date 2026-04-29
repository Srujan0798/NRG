import type { Page } from '@playwright/test'

type TestPersona = 'researcher' | 'government' | 'industry'

const PERSONA_SESSION: Record<TestPersona, { id: string; username: string; tier: number }> = {
  researcher: { id: 'e2e-researcher', username: 'researcher@iitgn.ac.in', tier: 1 },
  government: { id: 'e2e-government', username: 'ministry@nrg.gov.in', tier: 2 },
  industry: { id: 'e2e-industry', username: 'partner@industry.in', tier: 3 },
}

export async function installAuthSession(page: Page, role: TestPersona = 'researcher') {
  await page.addInitScript(({ selectedRole, session }) => {
    window.sessionStorage.setItem('nrg.auth.session', JSON.stringify({
      accessToken: '',
      refreshToken: '',
      tokenType: 'cookie',
      user: {
        id: session.id,
        username: session.username,
        role: selectedRole,
        tier: session.tier,
      },
    }))
  }, { selectedRole: role, session: PERSONA_SESSION[role] })
}
