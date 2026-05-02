import { authService } from '../../src/services/authService'

describe('authService.getAuthHeaders', () => {
  afterEach(() => {
    sessionStorage.clear()
  })

  it('formats bearer authorization without storing a source literal token', () => {
    const headers = authService.getAuthHeaders('access-token-123', 'bearer')

    expect(headers).toEqual({ Authorization: 'Bearer access-token-123' })
  })
})
