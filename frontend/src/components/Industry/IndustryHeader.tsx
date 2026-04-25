import { motion } from 'framer-motion'
import { Building2, HeartHandshake, Users, TrendingUp } from 'lucide-react'

interface IndustryHeaderProps {
  onThemeToggle: () => void
  theme: 'light' | 'dark'
}

export const IndustryHeader: React.FC<IndustryHeaderProps> = ({ onThemeToggle, theme }) => {
  const SunIcon = () => (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="4"/>
      <path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M6.34 17.66l-1.41 1.41M19.07 4.93l-1.41 1.41"/>
    </svg>
  )

  const MoonIcon = () => (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>
    </svg>
  )

  return (
    <motion.header
      initial={{ y: -20, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      className="sticky top-0 z-40 bg-white/95 dark:bg-navy-800/95 backdrop-blur-md border-b border-slate-200 dark:border-navy-700"
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <motion.div
              className="w-10 h-10 rounded-xl bg-gradient-to-br from-emerald-500 to-emerald-600 flex items-center justify-center shadow-lg"
              whileHover={{ scale: 1.05, rotate: 2 }}
              transition={{ type: 'spring', stiffness: 400, damping: 25 }}
            >
              <span className="text-white font-bold text-lg">न</span>
            </motion.div>
            <div>
              <h1 className="text-lg font-bold text-slate-900 dark:text-white font-devanagari">राष्ट्रीय गवेषण मंच</h1>
              <p className="text-xs text-slate-500 dark:text-slate-400">Industry Partnership Platform</p>
            </div>
          </div>

          <div className="flex items-center gap-4">
            <div className="hidden md:flex items-center gap-2 px-3 py-1.5 rounded-lg bg-emerald-50 dark:bg-emerald-900/20 border border-emerald-200 dark:border-emerald-700">
              <HeartHandshake size={14} className="text-emerald-600 dark:text-emerald-400" />
              <span className="text-xs font-medium text-emerald-700 dark:text-emerald-300">Partnership Mode</span>
            </div>

            <motion.button
              onClick={onThemeToggle}
              className="w-9 h-9 rounded-xl border border-slate-200 dark:border-navy-600 flex items-center justify-center text-slate-500 dark:text-slate-400 hover:text-emerald-500 hover:border-emerald-300 transition-all duration-200"
              aria-label="Toggle theme"
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
            >
              {theme === 'dark' ? <SunIcon /> : <MoonIcon />}
            </motion.button>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex gap-1 -mb-px overflow-x-auto scrollbar-hide">
          <NavTab icon={<Building2 size={14} />} label="Opportunities" active />
          <NavTab icon={<Users size={14} />} label="Researchers" />
          <NavTab icon={<TrendingUp size={14} />} label="Analytics" />
        </div>
      </div>
    </motion.header>
  )
}

const NavTab: React.FC<{ icon: React.ReactNode; label: string; active?: boolean }> = ({ icon, label, active }) => (
  <motion.button
    className={`flex items-center gap-1.5 px-4 py-2.5 text-sm font-medium border-b-2 transition-all duration-200 whitespace-nowrap ${
      active
        ? 'border-emerald-500 text-emerald-600 dark:text-emerald-400'
        : 'border-transparent text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-300 hover:border-slate-300 dark:hover:border-navy-600'
    }`}
    whileHover={{ scale: 1.02 }}
    whileTap={{ scale: 0.98 }}
  >
    {icon}
    {label}
  </motion.button>
)

export default IndustryHeader
