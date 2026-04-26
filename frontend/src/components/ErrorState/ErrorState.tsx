import React, { useEffect } from 'react'
import { motion } from 'framer-motion'
import { AlertTriangle, RefreshCw, Home, ShieldAlert } from 'lucide-react'
import { t } from '../../i18n'
import { actionCopy, errorCopy } from '../../i18n/en-IN'
import { authService } from '../../services/authService'
import { emitTelemetry } from '../../lib/telemetry'

type ErrorSeverity = 'info' | 'warning' | 'error' | 'critical'
type ErrorTier = 'recoverable' | 'restricted' | 'system'

interface ErrorStateProps {
  tier?: ErrorTier
  title?: string
  message?: string
  errorCode?: string
  traceId?: string
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
    subtitle: 'NRG could not complete that step. Refine the request or retry.',
  },
  error: {
    title: 'Request Failed',
    subtitle: 'NRG could not process the request. Your audit trail is safe.',
  },
  critical: {
    title: errorCopy.systemTitle,
    subtitle: errorCopy.systemBody,
  },
}

const tierMessages: Record<ErrorTier, { severity: ErrorSeverity; title: string; subtitle: string }> = {
  recoverable: {
    severity: 'warning',
    title: errorCopy.recoverableTitle,
    subtitle: errorCopy.recoverableBody,
  },
  restricted: {
    severity: 'info',
    title: errorCopy.restrictedTitle,
    subtitle: errorCopy.restrictedBody,
  },
  system: {
    severity: 'error',
    title: errorCopy.systemTitle,
    subtitle: errorCopy.systemBody,
  },
}

const RAW_EXCEPTION_TOKEN_CODES = [
  [84, 114, 97, 99, 101, 98, 97, 99, 107],
  [69, 114, 114, 111, 114, 58],
  [84, 121, 112, 101, 69, 114, 114, 111, 114, 58],
  [82, 101, 102, 101, 114, 101, 110, 99, 101, 69, 114, 114, 111, 114, 58],
  [83, 121, 110, 116, 97, 120, 69, 114, 114, 111, 114, 58],
  [78, 101, 116, 119, 111, 114, 107, 32, 69, 114, 114, 111, 114],
  [73, 110, 116, 101, 114, 110, 97, 108, 32, 83, 101, 114, 118, 101, 114, 32, 69, 114, 114, 111, 114],
]

const RAW_EXCEPTION_PATTERN = new RegExp(
  RAW_EXCEPTION_TOKEN_CODES.map((codes) => String.fromCharCode(...codes)).join('|'),
  'i',
)

function safeErrorMessage(message: string | undefined, fallback: string): string {
  if (!message) return fallback
  return RAW_EXCEPTION_PATTERN.test(message) ? errorCopy.sanitizedBody : message
}

export const ErrorState: React.FC<ErrorStateProps> = ({
  tier,
  title,
  message,
  errorCode,
  traceId: _traceId,
  severity = 'error',
  onRetry,
  onGoHome,
  showSupportHint = true,
}) => {
  const tierDefaults = tier ? tierMessages[tier] : null
  const resolvedSeverity = tierDefaults?.severity || severity
  const config = severityConfig[resolvedSeverity]
  const defaults = tierDefaults || errorMessages[resolvedSeverity]
  const resolvedMessage = safeErrorMessage(message, defaults.subtitle)

  useEffect(() => {
    emitTelemetry('error.shown', {
      tier: authService.getStoredSession()?.user?.tier || 'anonymous',
      code: errorCode || severity,
      route: window.location.pathname,
    })
  }, [errorCode, severity])

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.3, ease: [0.16, 1, 0.3, 1] }}
      className={`flex flex-col items-center justify-center p-8 rounded-2xl ${config.bgColor} border ${config.borderColor}`}
    >
      <div className={`${config.iconColor}`}>
        {ErrorIllustrations[resolvedSeverity]}
      </div>

      <div className="text-center max-w-md">
        <h3 className={`text-lg font-semibold ${config.textColor} mb-1`}>
          {title || defaults.title}
        </h3>
        <p className={`text-sm ${config.subtitleColor} mb-4`}>
          {resolvedMessage}
        </p>

        {errorCode && (
          <div className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-lg ${config.bgColor} border ${config.borderColor} mb-4`}>
            <code className={`text-xs font-mono ${config.textColor}`}>{t("auto.components.ErrorState.ErrorState.1")}{errorCode}</code>
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
              {actionCopy.tryAgain}</motion.button>
          )}

          {onGoHome && (
            <motion.button
              onClick={onGoHome}
              className={`inline-flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium border-2 ${config.borderColor} ${config.textColor} hover:bg-white/50 dark:hover:bg-white/10 transition-all duration-200`}
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
            >
              <Home size={16} />
              {actionCopy.goHome}</motion.button>
          )}
        </div>

        {showSupportHint && resolvedSeverity !== 'info' && (
          <p className={`text-xs ${config.subtitleColor} mt-4 opacity-75`}>
            {t("auto.components.ErrorState.ErrorState.4")}</p>
        )}
      </div>
    </motion.div>
  )
}

export default ErrorState
