import React, { Component, ReactNode } from 'react'
import { RefreshCw } from 'lucide-react'

interface WidgetErrorBoundaryProps {
  children: ReactNode
  title?: string
  description?: string
  fallback?: ReactNode
  onRetry?: () => void
  className?: string
}

interface State {
  hasError: boolean
  error?: Error
}

export class WidgetErrorBoundary extends Component<WidgetErrorBoundaryProps, State> {
  constructor(props: WidgetErrorBoundaryProps) {
    super(props)
    this.state = { hasError: false }
    this.handleRetry = this.handleRetry.bind(this)
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error }
  }

  handleRetry() {
    this.setState({ hasError: false, error: undefined })
    this.props.onRetry?.()
  }

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback
      }

      return (
        <div className="bg-white dark:bg-navy-800 rounded-2xl border border-rose-200 dark:border-rose-800 p-6 text-center">
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

    return this.props.children
  }
}
