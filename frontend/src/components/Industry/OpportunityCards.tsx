import React from 'react'
import { motion } from 'framer-motion'
import { HeartHandshake, Star, ArrowRight } from 'lucide-react'

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
      className="relative overflow-hidden rounded-2xl bg-white dark:bg-navy-800 border border-slate-200 dark:border-navy-700 shadow-md p-5"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ y: -4, boxShadow: '0 12px 40px rgba(0,0,0,0.12)' }}
      transition={{ duration: 0.3 }}
    >
      <div className="absolute top-0 right-0 w-24 h-24 opacity-5 rounded-bl-full bg-emerald-500" />

      <div className="flex items-start justify-between mb-3">
        <div className="flex-1">
          <p className="text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider">{institution}</p>
          <p className="text-sm font-devanagari text-slate-400">{titleHi}</p>
        </div>
        <div className="flex flex-col items-end gap-1">
          <span className={`px-2 py-0.5 rounded text-xs font-medium ${potentialColors[potential]}`}>
            {potential} potential
          </span>
          <div className="flex items-center gap-1">
            <Star size={12} className="text-amber-500 fill-amber-500" />
            <span className="text-xs font-bold text-slate-900 dark:text-white">{matchScore}%</span>
            <span className="text-xs text-slate-500">match</span>
          </div>
        </div>
      </div>

      <h3 className="text-base font-semibold text-slate-900 dark:text-white mb-1">{title}</h3>
      <p className="text-sm text-slate-600 dark:text-slate-300 leading-relaxed mb-4">{description}</p>

      <div className="flex items-center gap-2 mb-4">
        <span className="px-2.5 py-1 rounded-lg text-xs font-medium bg-slate-100 dark:bg-navy-700 text-slate-600 dark:text-slate-300">
          {researchArea}
        </span>
        <span className="px-2.5 py-1 rounded-lg text-xs font-medium bg-emerald-50 dark:bg-emerald-900/30 text-emerald-600 dark:text-emerald-400">
          {typeLabels[collaborationType]}
        </span>
      </div>

      <motion.button
        className="w-full py-2 rounded-xl text-sm font-medium bg-gradient-to-r from-emerald-500 to-emerald-600 text-white shadow-md hover:shadow-lg transition-all duration-200 flex items-center justify-center gap-2"
        whileHover={{ scale: 1.02 }}
        whileTap={{ scale: 0.98 }}
      >
        View Details
        <ArrowRight size={14} />
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
    className="rounded-2xl bg-white dark:bg-navy-800 border border-emerald-200 dark:border-emerald-700 shadow-md overflow-hidden"
    initial={{ opacity: 0, scale: 0.95 }}
    animate={{ opacity: 1, scale: 1 }}
  >
    <div className="px-5 py-4 bg-gradient-to-r from-emerald-50 to-white dark:from-emerald-900/20 dark:to-navy-800 border-b border-emerald-100 dark:border-emerald-700/50">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-emerald-100 dark:bg-emerald-900/30 flex items-center justify-center">
            <HeartHandshake size={16} className="text-emerald-600" />
          </div>
          <div>
            <p className="text-sm font-semibold text-slate-900 dark:text-white">{institution}</p>
            <p className="text-xs font-devanagari text-slate-500">{institutionHi}</p>
          </div>
        </div>
        <div className="text-right">
          <p className="text-2xl font-bold text-emerald-600 dark:text-emerald-400">{matchScore}%</p>
          <p className="text-xs text-slate-500">match score</p>
        </div>
      </div>
    </div>

    <div className="p-5 space-y-4">
      <div className="flex items-center gap-4">
        <div className="flex-1">
          <p className="text-xs text-slate-500 dark:text-slate-400">Researchers</p>
          <p className="text-lg font-bold text-slate-900 dark:text-white">{researcherCount.toLocaleString('en-IN')}</p>
        </div>
        <div className="h-10 w-px bg-slate-200 dark:bg-navy-600" />
        <div className="flex-1">
          <p className="text-xs text-slate-500 dark:text-slate-400">Collab. Types</p>
          <p className="text-sm font-medium text-slate-700 dark:text-slate-300">{collaborationTypes.length}</p>
        </div>
      </div>

      <div>
        <p className="text-xs text-slate-500 dark:text-slate-400 mb-1.5">Collaboration Types</p>
        <div className="flex flex-wrap gap-1.5">
          {collaborationTypes.map(type => (
            <span key={type} className="px-2 py-0.5 rounded text-xs bg-slate-100 dark:bg-navy-700 text-slate-600 dark:text-slate-300">
              {type}
            </span>
          ))}
        </div>
      </div>

      <div>
        <p className="text-xs text-slate-500 dark:text-slate-400 mb-1.5">Top Research Areas</p>
        <div className="flex flex-wrap gap-1.5">
          {topAreas.map(area => (
            <span key={area} className="px-2 py-0.5 rounded text-xs bg-emerald-50 dark:bg-emerald-900/30 text-emerald-600 dark:text-emerald-400">
              {area}
            </span>
          ))}
        </div>
      </div>
    </div>
  </motion.div>
)

export default OpportunityCard
