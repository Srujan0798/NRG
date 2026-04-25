import React from 'react'

export interface GlassCardProps {
  children: React.ReactNode
  accent?: 'researcher' | 'government' | 'industry' | 'sovereign'
  title?: string
  description?: string
  icon?: React.ReactNode
  onClick?: () => void
  className?: string
  hover?: boolean
}

const ACCENT_MAP: Record<string, string> = {
  researcher: 'var(--nrg-chart-5)',
  government: 'var(--nrg-chart-2)',
  industry:   'var(--nrg-chart-3)',
  sovereign:  'var(--nrg-chart-1)',
}

const ACCENT_BG_MAP: Record<string, string> = {
  researcher: 'bg-researcher-50',
  government: 'bg-government-50',
  industry:   'bg-industry-50',
  sovereign:  'bg-saffron-50',
}

export function GlassCard({
  children,
  accent = 'researcher',
  title,
  description,
  icon,
  onClick,
  className = '',
  hover = true,
}: GlassCardProps) {
  const accentColor = ACCENT_MAP[accent]

  return (
    <div
      className={`
        nrg-glass p-6
        ${hover ? 'cursor-pointer' : ''}
        ${className}
      `}
      onClick={onClick}
      role={onClick ? 'button' : undefined}
      tabIndex={onClick ? 0 : undefined}
      onKeyDown={onClick ? (e) => e.key === 'Enter' && onClick() : undefined}
    >
      {(title || icon) && (
        <div className="flex items-center gap-3 mb-4">
          {icon && (
            <div
              className={`w-10 h-10 rounded-xl flex items-center justify-center shrink-0 ${ACCENT_BG_MAP[accent]}`}
              style={{ color: accentColor }}
            >
              {icon}
            </div>
          )}
          {title && (
            <div>
              <h3 className="text-base font-semibold text-nrg-text">{title}</h3>
              {description && <p className="text-xs text-nrg-muted mt-0.5">{description}</p>}
            </div>
          )}
        </div>
      )}
      {children}
    </div>
  )
}