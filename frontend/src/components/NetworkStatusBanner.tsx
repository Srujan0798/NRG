import React, { useEffect, useState } from 'react'
import { WifiOff } from 'lucide-react'
import { t } from '../i18n'

const readOnlineState = () => {
  if (typeof navigator === 'undefined') return true
  return navigator.onLine
}

export const NetworkStatusBanner: React.FC = () => {
  const [isOnline, setIsOnline] = useState(readOnlineState)

  useEffect(() => {
    const handleOnline = () => setIsOnline(true)
    const handleOffline = () => setIsOnline(false)

    window.addEventListener('online', handleOnline)
    window.addEventListener('offline', handleOffline)
    return () => {
      window.removeEventListener('online', handleOnline)
      window.removeEventListener('offline', handleOffline)
    }
  }, [])

  if (isOnline) return null

  return (
    <div
      role="status"
      aria-live="polite"
      className="fixed inset-x-0 top-0 z-[100] border-b border-amber-300 bg-amber-50 px-4 py-3 text-amber-900 shadow-lg"
    >
      <div className="mx-auto flex max-w-7xl items-center justify-center gap-2 text-sm font-medium">
        <WifiOff size={18} aria-hidden="true" />
        <span>{t("auto.components.NetworkStatusBanner.1")}</span>
      </div>
    </div>
  )
}

export default NetworkStatusBanner
