import React, { Component, ReactNode } from 'react'
import { AlertTriangle, RefreshCw, ShieldCheck } from 'lucide-react'
import { t } from '../../i18n'
import { actionCopy, errorCopy } from '../../i18n/en-IN'
import { emitTelemetry } from '../../lib/telemetry'

interface ErrorBoundaryProps {
  children: ReactNode
  fallback?: ReactNode
  title?: string
  description?: string
  onRetry?: () => void
  className?: string
  scope?: 'page' | 'widget'
}

interface State {
  hasError: boolean
  errorRef?: string
}

const newRecoveryReference = () => {
  const random = typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function'
    ? crypto.randomUUID().slice(0, 8)
    : Math.random().toString(36).slice(2, 10)
  return `UI-${Date.now().toString(36).toUpperCase()}-${random.toUpperCase()}`
}

export class ErrorBoundary extends Component<ErrorBoundaryProps, State> {
  constructor(props: ErrorBoundaryProps) {
    super(props)
    this.state = { hasError: false }
    this.handleRetry = this.handleRetry.bind(this)
  }

  static getDerivedStateFromError(): State {
    return { hasError: true, errorRef: newRecoveryReference() }
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    emitTelemetry('ui.error_boundary', {
      error_ref: this.state.errorRef || newRecoveryReference(),
      error_name: error.name || 'Error',
      component_stack_lines: errorInfo.componentStack?.split('\n').filter(Boolean).length || 0,
      scope: this.props.scope || 'page',
    })
  }

  handleRetry() {
    this.setState({ hasError: false, errorRef: undefined })
    this.props.onRetry?.()
  }

  handleGoHome() {
    window.location.assign('/app')
  }

  renderWidgetFallback() {
    const errorRef = this.state.errorRef || newRecoveryReference()

    return (
      <div
        role="alert"
        aria-live="assertive"
        data-testid="nrg-error-boundary"
        className={`nrg-panel border-rose-200/70 dark:border-rose-800/60 p-6 text-center ${this.props.className || ''}`}
      >
        <div className="mx-auto mb-3 flex h-10 w-10 items-center justify-center rounded-full bg-rose-100/70 dark:bg-rose-900/30">
          <AlertTriangle size={18} className="text-rose-500" aria-hidden="true" />
        </div>
        <h3 className="text-sm font-semibold text-nrg-text mb-1">
          {this.props.title || errorCopy.boundaryWidgetTitle}
        </h3>
        <p className="text-xs text-nrg-muted mb-4">
          {this.props.description || errorCopy.boundaryWidgetBody}
        </p>
        <p className="mb-4 inline-flex items-center gap-1.5 rounded-lg border border-nrg-border bg-[var(--glass-bg)] px-2.5 py-1 text-xs font-medium text-nrg-muted">
          <ShieldCheck size={12} aria-hidden="true" />
          {errorCopy.boundaryReferenceLabel}: {errorRef}
        </p>
        <button
          type="button"
          onClick={this.handleRetry}
          className="inline-flex items-center gap-1.5 rounded-lg border border-nrg-border bg-[var(--glass-bg)] px-3 py-1.5 text-xs font-medium text-nrg-text hover:bg-saffron-500/10 transition"
        >
          <RefreshCw size={12} aria-hidden="true" />
          {t("auto.components.ErrorBoundary.ErrorBoundary.1")}</button>
      </div>
    )
  }

  renderPageFallback() {
    const errorRef = this.state.errorRef || newRecoveryReference()

    return (
      <div
        role="alert"
        aria-live="assertive"
        data-testid="nrg-error-boundary"
        className="min-h-screen flex items-center justify-center nrg-app-canvas px-6"
      >
        <div className="max-w-md w-full nrg-panel p-8 text-center">
          <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-rose-100/70 dark:bg-rose-900/30">
            <AlertTriangle size={28} className="text-rose-500" aria-hidden="true" />
          </div>
          <h2 className="text-xl font-semibold text-nrg-text mb-2">
            {this.props.title || errorCopy.boundaryPageTitle}
          </h2>
          <p className="text-sm text-nrg-muted mb-6">
            {this.props.description || errorCopy.boundaryPageBody}
          </p>
          <div className="mb-6 rounded-xl border border-nrg-border bg-[var(--glass-bg)] px-4 py-3 text-left">
            <p className="flex items-center gap-2 text-sm font-medium text-nrg-text">
              <ShieldCheck size={16} className="text-emerald-500" aria-hidden="true" />
              {errorCopy.boundaryDataSafe}
            </p>
            <p className="mt-1 text-xs text-nrg-muted">
              {errorCopy.boundaryReferenceLabel}: <span className="font-mono">{errorRef}</span>
            </p>
          </div>
          <div className="flex flex-wrap items-center justify-center gap-3">
            <button
              type="button"
              onClick={this.handleRetry}
              className="nrg-btn-primary inline-flex items-center justify-center gap-2 rounded-xl px-5 py-2.5 text-sm font-medium"
            >
              <RefreshCw size={15} aria-hidden="true" />
              {t("auto.components.ErrorBoundary.ErrorBoundary.2")}</button>
            <button
              type="button"
              onClick={this.handleGoHome}
              className="inline-flex items-center justify-center rounded-xl border border-nrg-border bg-[var(--glass-bg)] px-5 py-2.5 text-sm font-medium text-nrg-text hover:bg-saffron-500/10 transition"
            >
              {actionCopy.goHome}</button>
          </div>
        </div>
      </div>
    )
  }

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback
      }

      return this.props.scope === 'widget'
        ? this.renderWidgetFallback()
        : this.renderPageFallback()
    }

    return this.props.children
  }
}

export const WidgetErrorBoundary: React.FC<Omit<ErrorBoundaryProps, 'scope'>> = (props) => (
  <ErrorBoundary {...props} scope="widget" />
)

export default ErrorBoundary
