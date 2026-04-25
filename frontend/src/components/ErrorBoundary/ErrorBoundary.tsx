import React, { Component, ReactNode } from 'react'
import { RefreshCw } from 'lucide-react'

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
  error?: Error
}

export class ErrorBoundary extends Component<ErrorBoundaryProps, State> {
  constructor(props: ErrorBoundaryProps) {
    super(props)
    this.state = { hasError: false }
    this.handleRetry = this.handleRetry.bind(this)
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('ErrorBoundary caught an error:', error, errorInfo)
  }

  handleRetry() {
    this.setState({ hasError: false, error: undefined })
    this.props.onRetry?.()
  }

  renderWidgetFallback() {
    return (
      <div className={`nrg-panel border-rose-200/70 dark:border-rose-800/60 p-6 text-center ${this.props.className || ''}`}>
        <div className="mx-auto mb-3 flex h-10 w-10 items-center justify-center rounded-full bg-rose-100/70 dark:bg-rose-900/30">
          <RefreshCw size={18} className="text-rose-500" />
        </div>
        <h3 className="text-sm font-semibold text-nrg-text mb-1">
          {this.props.title || 'Widget failed to load'}
        </h3>
        <p className="text-xs text-nrg-muted mb-4">
          {this.props.description || 'This widget could not render. The rest of the page is still available.'}
        </p>
        <button
          onClick={this.handleRetry}
          className="inline-flex items-center gap-1.5 rounded-lg border border-nrg-border bg-[var(--glass-bg)] px-3 py-1.5 text-xs font-medium text-nrg-text hover:bg-saffron-500/10 transition"
        >
          <RefreshCw size={12} />
          Retry
        </button>
      </div>
    )
  }

  renderPageFallback() {
    return (
      <div className="min-h-screen flex items-center justify-center nrg-app-canvas px-6">
        <div className="max-w-md w-full nrg-panel p-8 text-center">
          <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-rose-100/70 dark:bg-rose-900/30">
            <span className="text-2xl">⚠️</span>
          </div>
          <h2 className="text-xl font-semibold text-nrg-text mb-2">
            {this.props.title || 'NRG could not render this section'}
          </h2>
          <p className="text-sm text-nrg-muted mb-6">
            {this.props.description || 'This view could not render. Your audit trail remains safe.'}
          </p>
          <button
            onClick={this.handleRetry}
            className="nrg-btn-primary inline-flex items-center justify-center rounded-xl px-6 py-2.5 text-sm font-medium"
          >
            Retry
          </button>
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
