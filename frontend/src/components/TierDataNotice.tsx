import React from 'react'
import { Shield, Eye, UserCheck } from 'lucide-react'
import { useAuth } from '../hooks/useAuth'

const TIER_NOTICES: Record<string, { icon: React.ReactNode; message: string; className: string }> = {
  researcher: {
    icon: <UserCheck size={14} />,
    message: 'Full access — publications, grants, and researcher profiles visible.',
    className: 'bg-indigo-50 border-indigo-200 text-indigo-700',
  },
  government: {
    icon: <Eye size={14} />,
    message: 'Showing aggregated institutional data — individual-level PII is restricted.',
    className: 'bg-blue-50 border-blue-200 text-blue-700',
  },
  industry: {
    icon: <Shield size={14} />,
    message: 'Showing anonymized aggregate data — individual researcher identities are protected per DPDP.',
    className: 'bg-emerald-50 border-emerald-200 text-emerald-700',
  },
}

export function TierDataNotice() {
  const { user } = useAuth()
  const role = user?.role || 'researcher'
  const notice = TIER_NOTICES[role] || TIER_NOTICES.researcher

  return (
    <div
      className={`flex items-center gap-2 px-3 py-2 rounded-lg border text-xs font-medium ${notice.className}`}
      role="note"
      aria-label={`Data access notice: ${notice.message}`}
    >
      {notice.icon}
      <span>{notice.message}</span>
    </div>
  )
}

export default TierDataNotice
