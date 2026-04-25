import React from 'react'
import { motion } from 'framer-motion'
import { HeartHandshake, Star, ArrowRight } from 'lucide-react'
import { t } from '../../i18n'

interface OpportunityCardProps {
  id: string
  title: string
  titleHi: string
  institution: string
  researchArea: string
  collaborationType: 'funding' | 'joint_research' | 'licensing' | 'consulting'
  potential: 'high' | 'medium' | 'low'
  matchScore: number
  description: string
}

export const OpportunityCard: React.FC<OpportunityCardProps> = ({
  title,
  titleHi,
  institution,
  researchArea,
  collaborationType,
  potential,
  matchScore,
  description,
}) => {
  const potentialColors = {
    high: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
    medium: 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400',
    low: 'bg-slate-100 text-slate-600 dark:bg-slate-700 dark:text-slate-400',
  }

  const typeLabels = {
    funding: 'Research Funding',
    joint_research: 'Joint Research',
    licensing: 'IP Licensing',
    consulting: 'Consulting',
  }

  return (
    <motion.div
      className="nrg-panel relative overflow-hidden p-5"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ y: -4, boxShadow: 'var(--nrg-elevation-3)' }}
      transition={{ duration: 0.3 }}
    >
      <div className="absolute top-0 right-0 w-24 h-24 opacity-5 rounded-bl-full bg-emerald-500" />

      <div className="flex items-start justify-between mb-3">
        <div className="flex-1">
          <p className="text-xs font-medium text-nrg-muted uppercase tracking-[0.12em]">{institution}</p>
          <p className="text-sm font-devanagari text-nrg-muted">{titleHi}</p>
        </div>
        <div className="flex flex-col items-end gap-1">
          <span className={`px-2 py-0.5 rounded text-xs font-medium ${potentialColors[potential]}`}>
            {potential} {t("auto.components.Industry.OpportunityCards.1")}</span>
          <div className="flex items-center gap-1">
            <Star size={12} className="text-amber-500 fill-amber-500" />
            <span className="text-xs font-bold text-nrg-text">{matchScore}%</span>
            <span className="text-xs text-nrg-muted">{t("auto.components.Industry.OpportunityCards.2")}</span>
          </div>
        </div>
      </div>

      <h3 className="text-base font-semibold text-nrg-text mb-1">{title}</h3>
      <p className="text-sm text-nrg-muted leading-relaxed mb-4">{description}</p>

      <div className="flex items-center gap-2 mb-4">
        <span className="px-2.5 py-1 rounded-lg text-xs font-medium bg-[var(--glass-bg)] text-nrg-muted border border-nrg-border">
          {researchArea}
        </span>
        <span className="px-2.5 py-1 rounded-lg text-xs font-medium bg-emerald-50 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-300">
          {typeLabels[collaborationType]}
        </span>
      </div>

      <motion.button
        className="w-full py-2 rounded-xl text-sm font-medium bg-gradient-to-r from-emerald-500 to-emerald-600 text-white shadow-md hover:shadow-lg transition-all duration-200 flex items-center justify-center gap-2"
        whileHover={{ scale: 1.02 }}
        whileTap={{ scale: 0.98 }}
      >
        {t("auto.components.Industry.OpportunityCards.3")}<ArrowRight size={14} />
      </motion.button>
    </motion.div>
  )
}

interface CollaborationPotentialCardProps {
  institution: string
  institutionHi: string
  researcherCount: number
  collaborationTypes: string[]
  topAreas: string[]
  matchScore: number
}

export const CollaborationPotentialCard: React.FC<CollaborationPotentialCardProps> = ({
  institution,
  institutionHi,
  researcherCount,
  collaborationTypes,
  topAreas,
  matchScore,
}) => (
  <motion.div
    className="nrg-panel overflow-hidden"
    initial={{ opacity: 0, scale: 0.95 }}
    animate={{ opacity: 1, scale: 1 }}
  >
    <div className="px-5 py-4 bg-[var(--glass-bg)] border-b border-nrg-border">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-emerald-100 dark:bg-emerald-900/30 flex items-center justify-center">
            <HeartHandshake size={16} className="text-emerald-600" />
          </div>
          <div>
              <p className="text-sm font-semibold text-nrg-text">{institution}</p>
              <p className="text-xs font-devanagari text-nrg-muted">{institutionHi}</p>
            </div>
          </div>
        <div className="text-right">
          <p className="text-2xl font-bold text-emerald-600 dark:text-emerald-400">{matchScore}%</p>
          <p className="text-xs text-slate-500">{t("auto.components.Industry.OpportunityCards.4")}</p>
        </div>
      </div>
    </div>

    <div className="p-5 space-y-4">
      <div className="flex items-center gap-4">
        <div className="flex-1">
          <p className="text-xs text-nrg-muted">{t("auto.components.Industry.OpportunityCards.5")}</p>
          <p className="text-lg font-bold text-nrg-text">{researcherCount.toLocaleString('en-IN')}</p>
        </div>
        <div className="h-10 w-px bg-slate-200 dark:bg-navy-600" />
        <div className="flex-1">
          <p className="text-xs text-nrg-muted">{t("auto.components.Industry.OpportunityCards.6")}</p>
          <p className="text-sm font-medium text-nrg-text">{collaborationTypes.length}</p>
        </div>
      </div>

      <div>
        <p className="text-xs text-nrg-muted mb-1.5">{t("auto.components.Industry.OpportunityCards.7")}</p>
        <div className="flex flex-wrap gap-1.5">
          {collaborationTypes.map((type) => (
            <span key={type} className="px-2 py-0.5 rounded text-xs bg-[var(--glass-bg)] border border-nrg-border text-nrg-muted">
              {type}
            </span>
          ))}
        </div>
      </div>

      <div>
        <p className="text-xs text-nrg-muted mb-1.5">{t("auto.components.Industry.OpportunityCards.8")}</p>
        <div className="flex flex-wrap gap-1.5">
          {topAreas.map((area) => (
            <span key={area} className="px-2 py-0.5 rounded text-xs bg-emerald-50 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-300">
              {area}
            </span>
          ))}
        </div>
      </div>
    </div>
  </motion.div>
)

export default OpportunityCard
