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
  authenticated?: boolean
  user: {
    id: string
    username: string
    role: PersonaRole
    tier: number
    researcher_id?: string
  } | null
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
  timeout: 30000,
  withCredentials: true,
})

const PERSONA_CREDENTIALS: Record<PersonaRole, { username: string; password: string; tier: number }> = {
  researcher: { username: 'researcher@iitgn.ac.in', password: 'Researcher@2026', tier: 1 },
  government: { username: 'ministry@nrg.gov.in', password: 'Ministry@2026', tier: 2 },
  industry: { username: 'partner@industry.in', password: 'Industry@2026', tier: 3 },
}

const buildSession = (
  payload: LoginApiResponse | RefreshApiResponse,
  existingUser?: AuthUser
): AuthSession => {
  if (!existingUser && (!('user' in payload) || !payload.user)) {
    throw new Error('Missing user payload during session refresh')
  }

  const user = 'user' in payload
    ? {
        id: payload.user!.id,
        username: payload.user!.username,
        role: payload.user!.role,
        tier: payload.user!.tier,
        researcherId: payload.user!.researcher_id
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

  async switchPersona(role: PersonaRole): Promise<AuthSession> {
    const persona = PERSONA_CREDENTIALS[role]
    try {
      return await this.login(persona.username, persona.password)
    } catch (error) {
      const currentSession = this.getStoredSession()
      if (!currentSession) throw error

      const session: AuthSession = {
        ...currentSession,
        user: {
          ...currentSession.user,
          username: persona.username,
          role,
          tier: persona.tier,
        },
      }
      this.saveSession(session)
      return session
    }
  },

  async refreshSession(refreshToken?: string): Promise<AuthSession> {
    const existingSession = this.getStoredSession()

    if (!existingSession) {
      return this.fetchSession()
    }

    const response = await api.post<RefreshApiResponse>('/auth/refresh', {
      refresh_token: refreshToken || existingSession.refreshToken || undefined,
      access_token: existingSession.accessToken || undefined,
    })

    const session = buildSession(response.data, existingSession.user)
    this.saveSession(session)
    return session
  },

  async fetchSession(): Promise<AuthSession> {
    const response = await api.get<LoginApiResponse>('/auth/session')
    if (!response.data.user) {
      throw new Error('No active authenticated session')
    }
    const session = buildSession({
      access_token: '',
      refresh_token: '',
      token_type: 'cookie',
      user: response.data.user,
    })
    this.saveSession(session)
    return session
  },

  async logout(session?: AuthSession | null): Promise<void> {
    const activeSession = session || this.getStoredSession()

    try {
      await api.post(
        '/auth/logout',
        { refresh_token: activeSession?.refreshToken || undefined },
        {
          headers: this.getAuthHeaders(activeSession?.accessToken),
        }
      )
    } catch {
      // Best-effort logout; local cleanup still happens.
    }

    this.clearSession()
  },

  getStoredSession(): AuthSession | null {
    const rawSession = sessionStorage.getItem(STORAGE_KEY)
    if (!rawSession) {
      return null
    }

    try {
      return JSON.parse(rawSession) as AuthSession
    } catch {
      this.clearSession()
      return null
    }
  },

  saveSession(session: AuthSession): void {
    const persisted: AuthSession = {
      ...session,
      accessToken: '',
      refreshToken: '',
    }
    sessionStorage.setItem(STORAGE_KEY, JSON.stringify(persisted))
  },

  clearSession(): void {
    sessionStorage.removeItem(STORAGE_KEY)
    localStorage.removeItem(STORAGE_KEY)
  },

  getAuthHeaders(accessToken?: string | null): Record<string, string> {
    return accessToken ? { Authorization: `Bearer ${accessToken}` } : {}
  },

  async withAuthenticatedRequest<T>(
    operation: (accessToken: string) => Promise<T>
  ): Promise<T> {
    const session = this.getStoredSession() || await this.fetchSession()

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
        headers: this.getAuthHeaders(accessToken),
      })

      return response.data
    })
  }
}
