import React from 'react';

export interface TierBadgeProps {
  tier: number;
  role: 'researcher' | 'government' | 'industry' | 'admin';
}

const TIER_CONFIGS: Record<number, { label: string; bg: string; text: string; border: string }> = {
  1: {
    label: 'TIER 1 · शोधकर्ता',
    bg: 'bg-indigo-100',
    text: 'text-indigo-700',
    border: 'border-indigo-200'
  },
  2: {
    label: 'TIER 2 · संस्थान',
    bg: 'bg-blue-100',
    text: 'text-blue-700',
    border: 'border-blue-200'
  },
  3: {
    label: 'TIER 3 · राष्ट्रीय',
    bg: 'bg-purple-100',
    text: 'text-purple-700',
    border: 'border-purple-200'
  },
  4: {
    label: 'TIER 4 · संप्रभु',
    bg: 'bg-amber-100',
    text: 'text-amber-700',
    border: 'border-amber-200'
  }
};

export function TierBadge({ tier, role }: TierBadgeProps) {
  const config = TIER_CONFIGS[tier] || TIER_CONFIGS[1];
  
  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold border ${config.bg} ${config.text} ${config.border}`}>
      <span className="w-1.5 h-1.5 rounded-full bg-current animate-pulse" />
      {config.label}
      <span className="opacity-60 ml-1 uppercase">{role}</span>
    </span>
  );
}
