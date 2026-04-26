import React from 'react'
import { t } from '../../../i18n'

export const StreamIndicator: React.FC = () => {
  return (
    <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-blue-50 border border-blue-200" style={{ '--delay-1': '0ms', '--delay-2': '150ms', '--delay-3': '300ms' } as React.CSSProperties}>
      <div className="flex gap-0.5">
        <div className="w-1.5 h-1.5 rounded-full bg-blue-500 animate-pulse" style={{ animationDelay: 'var(--delay-1)' }} />
        <div className="w-1.5 h-1.5 rounded-full bg-blue-500 animate-pulse" style={{ animationDelay: 'var(--delay-2)' }} />
        <div className="w-1.5 h-1.5 rounded-full bg-blue-500 animate-pulse" style={{ animationDelay: 'var(--delay-3)' }} />
      </div>
      <span className="text-xs font-medium text-blue-700">{t("auto.components.IntelligenceBrief.components.StreamIndicator.1")}</span>
    </div>
  )
}

export default StreamIndicator