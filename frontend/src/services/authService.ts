import axios, { AxiosError } from 'axios'

const API_BASE = ''
const STORAGE_KEY = 'nrg.auth.session'

export type PersonaRole = 'researcher' | 'government' | 'industry'

export interface AuthUser {
  id: string
  username: string
  role: PersonaRole
  tier: number
  researcherId?: string
}

export interface AuthSession {
  accessToken: string
  refreshToken: string
  tokenType: string
  user: AuthUser
}

interface LoginApiResponse {
  access_token: string
  refresh_token: string
  token_type: string
  user: {
    id: string
    username: string
    role: PersonaRole
    tier: number
    researcher_id?: string
  }
}

interface RefreshApiResponse {
  access_token: string
  refresh_token: string
  token_type: string
}

const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json'
  },
  timeout: 10000,
})

const buildSession = (
  payload: LoginApiResponse | RefreshApiResponse,
  existingUser?: AuthUser
): AuthSession => {
  if (!existingUser && !('user' in payload)) {
    throw new Error('Missing user payload during session refresh')
  }

  const user = 'user' in payload
    ? {
        id: payload.user.id,
        username: payload.user.username,
        role: payload.user.role,
        tier: payload.user.tier,
        researcherId: payload.user.researcher_id
      }
    : existingUser!

  return {
    accessToken: payload.access_token,
    refreshToken: payload.refresh_token,
    tokenType: payload.token_type,
    user
  }
}

export const authService = {
  async login(username: string, password: string): Promise<AuthSession> {
    const response = await api.post<LoginApiResponse>('/login', {
      username,
      password
    })

    const session = buildSession(response.data)
    this.saveSession(session)
    return session
  },

  async refreshSession(refreshToken?: string): Promise<AuthSession> {
    const existingSession = this.getStoredSession()
    const activeRefreshToken = refreshToken || existingSession?.refreshToken

    if (!activeRefreshToken || !existingSession) {
      throw new Error('No refresh token available')
    }

    const response = await api.post<RefreshApiResponse>('/refresh', {
      refresh_token: activeRefreshToken
    })

    const session = buildSession(response.data, existingSession.user)
    this.saveSession(session)
    return session
  },

  async logout(session?: AuthSession | null): Promise<void> {
    const activeSession = session || this.getStoredSession()

    if (activeSession) {
      try {
        await api.post(
          '/logout',
          { refresh_token: activeSession.refreshToken },
          {
            headers: {
              Authorization: `Bearer ${activeSession.accessToken}`
            }
          }
        )
      } catch (_error) {
        // Best-effort logout; local cleanup still happens.
      }
    }

    this.clearSession()
  },

  getStoredSession(): AuthSession | null {
    const rawSession = localStorage.getItem(STORAGE_KEY)
    if (!rawSession) {
      return null
    }

    try {
      return JSON.parse(rawSession) as AuthSession
    } catch (_error) {
      this.clearSession()
      return null
    }
  },

  saveSession(session: AuthSession): void {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(session))
  },

  clearSession(): void {
    localStorage.removeItem(STORAGE_KEY)
  },

  async withAuthenticatedRequest<T>(
    operation: (accessToken: string) => Promise<T>
  ): Promise<T> {
    const session = this.getStoredSession()
    if (!session) {
      throw new Error('Not authenticated')
    }

    try {
      return await operation(session.accessToken)
    } catch (error) {
      const axiosError = error as AxiosError
      if (axiosError.response?.status !== 401) {
        throw error
      }

      const refreshedSession = await this.refreshSession(session.refreshToken)
      return operation(refreshedSession.accessToken)
    }
  },

  async fetchResearchers(): Promise<unknown> {
    return this.withAuthenticatedRequest(async (accessToken) => {
      const response = await api.get('/researchers', {
        headers: {
          Authorization: `Bearer ${accessToken}`
        }
      })

      return response.data
    })
  }
}
