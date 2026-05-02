/// <reference types="vite/client" />
declare const __NRG_API_TOKEN_HEADER__: string | undefined

interface Window {
  __nrgBootQuery?: string
  __nrgBootSubmit?: boolean
  __nrgLoadApp?: () => Promise<unknown>
}
