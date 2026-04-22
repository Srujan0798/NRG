import React from 'react'

export interface SkeletonLoaderProps {
  type?: 'card' | 'list' | 'chart' | 'table' | 'stat'
  count?: number
}

const StatSkeleton: React.FC = () => (
  <div className="nrg-stat-card">
    <div className="nrg-skeleton h-4 w-20 rounded mb-3" />
    <div className="nrg-skeleton h-8 w-28 rounded mb-2" />
    <div className="nrg-skeleton h-3 w-16 rounded" />
  </div>
)

const CardSkeleton: React.FC = () => (
  <div className="nrg-glass p-6">
    <div className="flex items-center gap-3 mb-4">
      <div className="nrg-skeleton w-10 h-10 rounded-xl" />
      <div className="flex-1">
        <div className="nrg-skeleton h-4 w-32 rounded mb-2" />
        <div className="nrg-skeleton h-3 w-48 rounded" />
      </div>
    </div>
    <div className="space-y-2">
      <div className="nrg-skeleton h-10 w-full rounded-lg" />
      <div className="nrg-skeleton h-10 w-5/6 rounded-lg" />
    </div>
  </div>
)

const ListSkeleton: React.FC<{ count?: number }> = ({ count = 5 }) => (
  <div className="space-y-3">
    {Array.from({ length: count }).map((_, i) => (
      <div key={i} className="nrg-glass p-4 flex items-center gap-4">
        <div className="nrg-skeleton w-10 h-10 rounded-full" />
        <div className="flex-1 space-y-2">
          <div className="nrg-skeleton h-4 w-1/3 rounded" />
          <div className="nrg-skeleton h-3 w-2/3 rounded" />
        </div>
        <div className="nrg-skeleton w-16 h-6 rounded-full" />
      </div>
    ))}
  </div>
)

const ChartSkeleton: React.FC = () => (
  <div className="nrg-glass p-6">
    <div className="nrg-skeleton h-4 w-28 rounded mb-4" />
    <div className="flex items-end gap-3 h-40 px-2">
      {[55, 70, 45, 85, 60, 95, 50, 75].map((h, i) => (
        <div
          key={i}
          className="flex-1 nrg-skeleton rounded-t"
          style={{ height: `${h}%` }}
        />
      ))}
    </div>
    <div className="flex justify-around mt-3">
      {[1, 2, 3, 4, 5, 6, 7, 8].map((i) => (
        <div key={i} className="nrg-skeleton h-2 w-6 rounded" />
      ))}
    </div>
  </div>
)

const TableSkeleton: React.FC<{ count?: number }> = ({ count = 5 }) => (
  <div className="nrg-glass overflow-hidden">
    <div className="flex gap-4 px-6 py-3 bg-nrg-navy-50 border-b border-nrg-border">
      {[1, 2, 3, 4].map((i) => (
        <div key={i} className="nrg-skeleton h-3 w-20 rounded" />
      ))}
    </div>
    {Array.from({ length: count }).map((_, i) => (
      <div key={i} className="flex gap-4 px-6 py-4 border-b border-nrg-border last:border-0">
        {[1, 2, 3, 4].map((j) => (
          <div key={j} className="nrg-skeleton h-3 w-full rounded" />
        ))}
      </div>
    ))}
  </div>
)

export function SkeletonLoader({ type = 'card', count = 1 }: SkeletonLoaderProps) {
  const renderSkeleton = () => {
    switch (type) {
      case 'card':
        return Array.from({ length: count }).map((_, i) => <CardSkeleton key={i} />)
      case 'list':
        return <ListSkeleton count={count} />
      case 'chart':
        return <ChartSkeleton />
      case 'table':
        return <TableSkeleton count={count} />
      case 'stat':
        return (
          <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
            {Array.from({ length: count }).map((_, i) => <StatSkeleton key={i} />)}
          </div>
        )
      default:
        return <CardSkeleton />
    }
  }

  return <>{renderSkeleton()}</>
}