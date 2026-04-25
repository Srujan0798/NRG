import React from 'react'
import { LoaderIcon, ShieldCheckIcon } from '../Icons'
import type { StreamPhase } from '../../hooks/useStreamingQuery'
import { t } from '../../i18n'

interface PhaseHeaderProps {
  phase: StreamPhase | null
  isStreaming: boolean
}

const phaseOrder = ['planning', 'planned', 'executing', 'synthesizing', 'verified']

export const PhaseHeader: React.FC<PhaseHeaderProps> = ({ phase, isStreaming }) => {
  const currentIndex = Math.max(phaseOrder.indexOf(phase?.phase || 'planning'), 0)
  const isVerified = phase?.phase === 'verified'

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-3">
        <span className="flex h-10 w-10 items-center justify-center rounded-lg bg-[var(--nrg-surface-2)] text-[var(--nrg-focus)]">
          {isVerified ? (
            <ShieldCheckIcon className="h-5 w-5" />
          ) : (
            <LoaderIcon className={`h-5 w-5 ${isStreaming ? 'animate-spin' : ''}`} />
          )}
        </span>
        <div>
          <p className="text-sm font-semibold text-nrg-text">{phase?.label || 'Planning evidence path'}</p>
          <p className="text-xs font-medium uppercase tracking-wider text-nrg-muted">{t("auto.components.PhaseHeader.PhaseHeader.1")}</p>
        </div>
      </div>

      <div className="grid grid-cols-5 gap-2" aria-hidden="true">
        {phaseOrder.map((item, index) => (
          <span
            key={item}
            className={`h-1.5 rounded-full transition-all duration-300 ${
              index <= currentIndex ? 'bg-[var(--nrg-focus)]' : 'bg-[var(--nrg-border)]'
            }`}
          />
        ))}
      </div>
    </div>
  )
}

export default PhaseHeader
