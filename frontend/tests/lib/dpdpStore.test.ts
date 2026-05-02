import { useDPDPStore } from '../../src/stores/dpdpStore'
import { dpdpService } from '../../src/services/dpdpService'

describe('useDPDPStore consent revocation', () => {
  beforeEach(() => {
    jest.spyOn(dpdpService, 'grantConsent').mockResolvedValue({ success: true })
    jest.spyOn(dpdpService, 'revokeConsent').mockResolvedValue({ success: true })

    useDPDPStore.setState({
      consents: {},
      auditLog: [],
      isWithdrawalMode: false,
      isSyncing: false,
      lastSyncedAt: null,
    })
  })

  afterEach(() => {
    jest.restoreAllMocks()
    localStorage.clear()
  })

  it('marks revoked consent inactive and records the withdrawal audit entry', async () => {
    await useDPDPStore.getState().grantConsent('research_access', 365)
    await useDPDPStore.getState().withdrawConsent('research_access')

    const state = useDPDPStore.getState()
    expect(state.consents.research_access.granted).toBe(false)
    expect(state.consents.research_access.withdrawnAt).toEqual(expect.any(Number))
    expect(state.auditLog[0]).toMatchObject({
      action: 'consent_withdrawn',
      details: 'Consent withdrawn for: research_access',
    })
  })
})
