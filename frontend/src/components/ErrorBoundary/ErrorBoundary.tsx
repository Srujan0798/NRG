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
      <div className={`bg-white dark:bg-navy-800 rounded-2xl border border-rose-200 dark:border-rose-800 p-6 text-center ${this.props.className || ''}`}>
        <div className="mx-auto mb-3 flex h-10 w-10 items-center justify-center rounded-full bg-rose-50 dark:bg-rose-900/30">
          <RefreshCw size={18} className="text-rose-500" />
        </div>
        <h3 className="text-sm font-semibold text-slate-900 dark:text-white mb-1">
          {this.props.title || 'Widget failed to load'}
        </h3>
        <p className="text-xs text-slate-500 dark:text-slate-400 mb-4">
          {this.props.description || this.state.error?.message || 'An unexpected error occurred.'}
        </p>
        <button
          onClick={this.handleRetry}
          className="inline-flex items-center gap-1.5 rounded-lg bg-slate-100 dark:bg-navy-700 px-3 py-1.5 text-xs font-medium text-slate-700 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-navy-600 transition"
        >
          <RefreshCw size={12} />
          Retry
        </button>
      </div>
    )
  }

  renderPageFallback() {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50 px-6">
        <div className="max-w-md w-full bg-white rounded-2xl shadow-lg border border-gray-100 p-8 text-center">
          <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-rose-50">
            <span className="text-2xl">⚠️</span>
          </div>
          <h2 className="text-xl font-semibold text-gray-900 mb-2">
            {this.props.title || 'Something went wrong'}
          </h2>
          <p className="text-sm text-gray-500 mb-6">
            {this.props.description || this.state.error?.message || 'An unexpected error occurred in this view.'}
          </p>
          <button
            onClick={this.handleRetry}
            className="inline-flex items-center justify-center rounded-xl bg-slate-900 px-6 py-2.5 text-sm font-medium text-white hover:bg-slate-800 transition"
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
