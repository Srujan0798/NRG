import React from 'react'
import { motion } from 'framer-motion'
import { AlertTriangle, RefreshCw, Home, ShieldAlert } from 'lucide-react'

type ErrorSeverity = 'info' | 'warning' | 'error' | 'critical'

interface ErrorStateProps {
  title?: string
  message?: string
  errorCode?: string
  severity?: ErrorSeverity
  onRetry?: () => void
  onGoHome?: () => void
  showSupportHint?: boolean
}

const severityConfig = {
  info: {
    icon: ShieldAlert,
    bgColor: 'bg-blue-50 dark:bg-blue-950/30',
    borderColor: 'border-blue-200 dark:border-blue-800',
    iconColor: 'text-blue-500',
    textColor: 'text-blue-800 dark:text-blue-200',
    subtitleColor: 'text-blue-600 dark:text-blue-400',
  },
  warning: {
    icon: AlertTriangle,
    bgColor: 'bg-amber-50 dark:bg-amber-950/30',
    borderColor: 'border-amber-200 dark:border-amber-800',
    iconColor: 'text-amber-500',
    textColor: 'text-amber-800 dark:text-amber-200',
    subtitleColor: 'text-amber-600 dark:text-amber-400',
  },
  error: {
    icon: AlertTriangle,
    bgColor: 'bg-red-50 dark:bg-red-950/30',
    borderColor: 'border-red-200 dark:border-red-800',
    iconColor: 'text-red-500',
    textColor: 'text-red-800 dark:text-red-200',
    subtitleColor: 'text-red-600 dark:text-red-400',
  },
  critical: {
    icon: AlertTriangle,
    bgColor: 'bg-red-100 dark:bg-red-950/50',
    borderColor: 'border-red-300 dark:border-red-700',
    iconColor: 'text-red-600',
    textColor: 'text-red-900 dark:text-red-100',
    subtitleColor: 'text-red-700 dark:text-red-300',
  },
}

const ErrorIllustrations: Record<ErrorSeverity, React.ReactNode> = {
  info: (
    <svg viewBox="0 0 120 120" className="w-28 h-28 mb-4">
      <circle cx="60" cy="60" r="50" fill="currentColor" fillOpacity="0.1" />
      <path d="M60 30 L70 55 L60 50 L50 55 Z" fill="currentColor" fillOpacity="0.3" />
      <circle cx="60" cy="75" r="8" fill="currentColor" fillOpacity="0.5" />
      <circle cx="40" cy="60" r="4" fill="currentColor" fillOpacity="0.2" />
      <circle cx="80" cy="60" r="4" fill="currentColor" fillOpacity="0.2" />
    </svg>
  ),
  warning: (
    <svg viewBox="0 0 120 120" className="w-28 h-28 mb-4">
      <path d="M60 20 L90 85 L30 85 Z" fill="currentColor" fillOpacity="0.15" stroke="currentColor" strokeWidth="2" strokeDasharray="4 2" />
      <path d="M60 45 L65 65 L60 62 L55 65 Z" fill="currentColor" fillOpacity="0.5" />
      <circle cx="60" cy="75" r="5" fill="currentColor" fillOpacity="0.5" />
    </svg>
  ),
  error: (
    <svg viewBox="0 0 120 120" className="w-28 h-28 mb-4">
      <circle cx="60" cy="60" r="45" fill="currentColor" fillOpacity="0.1" />
      <path d="M40 40 L80 80 M80 40 L40 80" stroke="currentColor" strokeWidth="4" strokeLinecap="round" strokeOpacity="0.4" />
      <circle cx="60" cy="60" r="25" fill="currentColor" fillOpacity="0.05" />
    </svg>
  ),
  critical: (
    <svg viewBox="0 0 120 120" className="w-28 h-28 mb-4">
      <path d="M60 15 L75 35 L95 40 L80 55 L85 75 L60 65 L35 75 L40 55 L25 40 L45 35 Z" fill="currentColor" fillOpacity="0.2" />
      <path d="M60 30 L68 42 L82 45 L72 55 L75 68 L60 62 L45 68 L48 55 L38 45 L52 42 Z" fill="currentColor" fillOpacity="0.3" />
      <circle cx="60" cy="50" r="10" fill="currentColor" fillOpacity="0.4" />
    </svg>
  ),
}

const errorMessages: Record<ErrorSeverity, { title: string; subtitle: string }> = {
  info: {
    title: 'Information Notice',
    subtitle: 'This is informational and no action is required.',
  },
  warning: {
    title: 'Warning',
    subtitle: 'Something unexpected occurred. Please try again.',
  },
  error: {
    title: 'Request Failed',
    subtitle: 'We encountered an issue processing your request.',
  },
  critical: {
    title: 'System Error',
    subtitle: 'A critical error occurred. Please contact support if this persists.',
  },
}

export const ErrorState: React.FC<ErrorStateProps> = ({
  title,
  message,
  errorCode,
  severity = 'error',
  onRetry,
  onGoHome,
  showSupportHint = true,
}) => {
  const config = severityConfig[severity]
  const defaults = errorMessages[severity]

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.3, ease: [0.16, 1, 0.3, 1] }}
      className={`flex flex-col items-center justify-center p-8 rounded-2xl ${config.bgColor} border ${config.borderColor}`}
    >
      <div className={`${config.iconColor}`}>
        {ErrorIllustrations[severity]}
      </div>

      <div className="text-center max-w-md">
        <h3 className={`text-lg font-semibold ${config.textColor} mb-1`}>
          {title || defaults.title}
        </h3>
        <p className={`text-sm ${config.subtitleColor} mb-4`}>
          {message || defaults.subtitle}
        </p>

        {errorCode && (
          <div className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-lg ${config.bgColor} border ${config.borderColor} mb-4`}>
            <code className={`text-xs font-mono ${config.textColor}`}>ERR_{errorCode}</code>
          </div>
        )}

        <div className="flex items-center justify-center gap-3">
          {onRetry && (
            <motion.button
              onClick={onRetry}
              className={`inline-flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium text-white bg-gradient-to-r from-saffron-500 to-saffron-600 hover:from-saffron-600 hover:to-saffron-700 shadow-md hover:shadow-lg transition-all duration-200`}
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
            >
              <RefreshCw size={16} />
              Try Again
            </motion.button>
          )}

          {onGoHome && (
            <motion.button
              onClick={onGoHome}
              className={`inline-flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium border-2 ${config.borderColor} ${config.textColor} hover:bg-white/50 dark:hover:bg-white/10 transition-all duration-200`}
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
            >
              <Home size={16} />
              Go Home
            </motion.button>
          )}
        </div>

        {showSupportHint && severity !== 'info' && (
          <p className={`text-xs ${config.subtitleColor} mt-4 opacity-75`}>
            If this problem persists, please contact support with the error code.
          </p>
        )}
      </div>
    </motion.div>
  )
}

export default ErrorState
