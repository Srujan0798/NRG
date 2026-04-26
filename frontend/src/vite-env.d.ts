/// <reference types="vite/client" />

interface Window {
  __nrgBootQuery?: string
  __nrgBootSubmit?: boolean
  __nrgLoadApp?: () => Promise<unknown>
}
