import React from 'react'

export const StreamIndicator: React.FC = () => {
  return (
    <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-blue-50 border border-blue-200">
      <div className="flex gap-0.5">
        <div className="w-1.5 h-1.5 rounded-full bg-blue-500 animate-pulse" style={{ animationDelay: '0ms' }} />
        <div className="w-1.5 h-1.5 rounded-full bg-blue-500 animate-pulse" style={{ animationDelay: '150ms' }} />
        <div className="w-1.5 h-1.5 rounded-full bg-blue-500 animate-pulse" style={{ animationDelay: '300ms' }} />
      </div>
      <span className="text-xs font-medium text-blue-700">Streaming</span>
    </div>
  )
}

export default StreamIndicator