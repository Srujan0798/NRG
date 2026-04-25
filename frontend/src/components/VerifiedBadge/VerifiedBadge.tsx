import React from 'react'
import { ShieldCheckIcon } from '../Icons'
import { t } from '../../i18n'
import { emitTelemetry } from '../../lib/telemetry'

interface VerifiedBadgeProps {
  auditEventId: string | null
  signatureBytes: number | null
  onOpenProof?: () => void
}

export const VerifiedBadge: React.FC<VerifiedBadgeProps> = ({
  auditEventId,
  signatureBytes,
  onOpenProof,
}) => {
  const handleOpenProof = () => {
    if (auditEventId) {
      emitTelemetry('audit.verified', {
        hmac: auditEventId,
        valid: true,
        ms: 0,
      })
    }
    onOpenProof?.()
  }

  return (
    <button
      type="button"
      data-testid="verified-badge"
      onClick={handleOpenProof}
      className="inline-flex items-center gap-3 rounded-lg border border-[var(--nrg-success)] bg-[var(--nrg-success-soft)] px-4 py-3 text-left text-sm font-semibold text-[var(--nrg-success)] shadow-sm transition duration-300 hover:translate-y-[-0.0625rem]"
    >
      <span className="relative flex h-9 w-9 items-center justify-center rounded-full bg-[var(--nrg-success)] text-white">
        <span className="absolute h-full w-full animate-ping rounded-full bg-[var(--nrg-success)] opacity-30" />
        <ShieldCheckIcon className="relative h-5 w-5" />
      </span>
      <span>
        {t("auto.components.VerifiedBadge.VerifiedBadge.1")}{signatureBytes ?? 26}{t("auto.components.VerifiedBadge.VerifiedBadge.2")}{auditEventId && <span className="block text-xs font-medium text-nrg-muted">{auditEventId}</span>}
      </span>
    </button>
  )
}

export default VerifiedBadge
