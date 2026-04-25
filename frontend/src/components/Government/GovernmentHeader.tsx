import { motion } from 'framer-motion'
import { Shield, LogOut, Moon, Sun } from 'lucide-react'
import { useAuth } from '../../hooks/useAuth'

interface GovernmentHeaderProps {
  onThemeToggle: () => void
  theme: 'light' | 'dark'
}

export const GovernmentHeader: React.FC<GovernmentHeaderProps> = ({ onThemeToggle, theme }) => {
  const { logout } = useAuth()

  return (
    <motion.header
      initial={{ y: -20, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      className="sticky top-0 z-40 border-b border-nrg-border bg-[var(--glass-bg)] backdrop-blur-xl"
    >
      <div className="h-1 w-full bg-gradient-to-r from-saffron-600 via-saffron-400 to-navy-300" />
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex flex-wrap items-center gap-2 sm:gap-3">
            <motion.div
              className="w-11 h-11 rounded-2xl bg-gradient-to-br from-saffron-500 via-saffron-600 to-navy-500 flex items-center justify-center shadow-lg"
              whileHover={{ scale: 1.05, rotate: 4 }}
              transition={{ type: 'spring', stiffness: 400, damping: 25 }}
            >
              <span className="text-white font-display text-lg">न</span>
            </motion.div>
            <div>
              <h1 className="text-lg font-bold text-nrg-text font-devanagari">राष्ट्रीय गवेषण मंच</h1>
              <p className="text-xs uppercase tracking-[0.18em] text-nrg-muted">Sovereign Policy Intelligence</p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <div className="hidden md:flex items-center gap-2 px-3 py-1.5 rounded-full border border-saffron-400/40 bg-saffron-500/10">
              <Shield size={14} className="text-saffron-700 dark:text-saffron-300" />
              <span className="text-[11px] font-semibold uppercase tracking-[0.12em] text-saffron-700 dark:text-saffron-300">
                Command Node
              </span>
            </div>

            <motion.button
              onClick={onThemeToggle}
              className="w-10 h-10 rounded-xl border border-nrg-border flex items-center justify-center text-nrg-muted hover:text-saffron-500 hover:border-saffron-300 transition-all duration-200"
              aria-label="Toggle theme"
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
            >
              {theme === 'dark' ? <Sun size={16} /> : <Moon size={16} />}
            </motion.button>
            <motion.button
              onClick={logout}
              className="h-10 px-3 rounded-xl border border-nrg-border flex items-center gap-2 text-sm font-semibold text-nrg-muted hover:text-rose-600 hover:border-rose-300 transition-all duration-200"
              aria-label="Log out"
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
            >
              <LogOut size={16} />
              <span className="hidden sm:inline">Logout</span>
            </motion.button>
          </div>
        </div>
      </div>
    </motion.header>
  )
}

export default GovernmentHeader
