import React from 'react'
import { motion } from 'framer-motion'

interface SkeletonProps {
  className?: string
  variant?: 'rectangular' | 'circular' | 'text' | 'card'
}

export const Skeleton: React.FC<SkeletonProps> = ({ className = '', variant = 'rectangular' }) => {
  const baseClass = 'bg-gradient-to-r from-slate-200 via-slate-100 to-slate-200 dark:from-navy-600 dark:via-navy-500 dark:to-navy-600'

  const variantClass = {
    rectangular: 'rounded-lg',
    circular: 'rounded-full',
    text: 'rounded h-4',
    card: 'rounded-xl',
  }[variant]

  return (
    <motion.div
      className={`${baseClass} ${variantClass} ${className}`}
      animate={{
        backgroundPosition: ['200% 0', '-200% 0'],
      }}
      transition={{
        duration: 1.8,
        repeat: Infinity,
        ease: 'easeInOut',
      }}
      style={{ backgroundSize: '200% 100%' }}
    />
  )
}

interface SkeletonLoaderProps {
  type?: 'stats' | 'card' | 'list' | 'chart' | 'table' | 'graph'
  count?: number
}

const StatsSkeleton: React.FC = () => (
  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
    {[1, 2, 3, 4].map(i => (
      <div key={i} className="p-5 rounded-2xl bg-white border border-slate-200/80 shadow-md">
        <Skeleton className="h-3 w-20 mb-3" variant="text" />
        <Skeleton className="h-8 w-28 mb-2" variant="text" />
        <Skeleton className="h-2 w-16" variant="text" />
      </div>
    ))}
  </div>
)

const CardSkeleton: React.FC = () => (
  <div className="p-6 rounded-2xl bg-white border border-slate-200/80 shadow-md">
    <div className="flex items-center gap-3 mb-4">
      <Skeleton className="w-10 h-10 rounded-xl" />
      <div className="flex-1">
        <Skeleton className="h-4 w-32 mb-2" variant="text" />
        <Skeleton className="h-3 w-48" variant="text" />
      </div>
    </div>
    <Skeleton className="h-10 w-full mb-2" />
    <Skeleton className="h-10 w-5/6" />
  </div>
)

const ListSkeleton: React.FC<{ count?: number }> = ({ count = 5 }) => (
  <div className="space-y-3">
    {Array.from({ length: count }).map((_, i) => (
      <div key={i} className="p-4 rounded-xl bg-white border border-slate-200/80 shadow-md flex items-center gap-4">
        <Skeleton className="w-10 h-10 rounded-full" variant="circular" />
        <div className="flex-1 space-y-2">
          <Skeleton className="h-4 w-1/3" variant="text" />
          <Skeleton className="h-3 w-2/3" variant="text" />
        </div>
        <Skeleton className="h-6 w-16 rounded-full" />
      </div>
    ))}
  </div>
)

const ChartSkeleton: React.FC = () => (
  <div className="p-6 rounded-2xl bg-white border border-slate-200/80 shadow-md">
    <Skeleton className="h-4 w-28 mb-4" variant="text" />
    <div className="flex items-end gap-3 h-40 px-2">
      {[55, 70, 45, 85, 60, 95, 50, 75].map((h, i) => (
        <motion.div
          key={i}
          className="flex-1 rounded-t"
          style={{ height: `${h}%` }}
          initial={{ opacity: 0, scaleY: 0 }}
          animate={{ opacity: 1, scaleY: 1 }}
          transition={{ delay: i * 0.05, duration: 0.3 }}
        >
          <Skeleton className="h-full w-full" />
        </motion.div>
      ))}
    </div>
    <div className="flex justify-around mt-3">
      {[1, 2, 3, 4, 5, 6, 7, 8].map(i => (
        <Skeleton key={i} className="h-2 w-6 rounded" />
      ))}
    </div>
  </div>
)

const TableSkeleton: React.FC<{ count?: number }> = ({ count = 5 }) => (
  <div className="rounded-2xl bg-white border border-slate-200/80 shadow-md overflow-hidden">
    <div className="flex gap-4 px-6 py-3 bg-gradient-to-r from-saffron-50 to-white border-b border-slate-200/50">
      {[1, 2, 3, 4].map(i => (
        <Skeleton key={i} className="h-3 w-20" variant="text" />
      ))}
    </div>
    {Array.from({ length: count }).map((_, i) => (
      <div key={i} className="flex gap-4 px-6 py-4 border-b border-slate-100 last:border-0">
        {[1, 2, 3, 4].map(j => (
          <Skeleton key={j} className="h-3 w-full" variant="text" />
        ))}
      </div>
    ))}
  </div>
)

const GraphSkeleton: React.FC = () => (
  <div className="rounded-2xl bg-white border border-slate-200/80 shadow-md p-6">
    <div className="flex items-center justify-between mb-4">
      <Skeleton className="h-4 w-40" variant="text" />
      <div className="flex gap-2">
        <Skeleton className="h-8 w-24 rounded-lg" />
        <Skeleton className="h-8 w-24 rounded-lg" />
      </div>
    </div>
    <div className="relative w-full h-80 rounded-xl bg-gradient-to-br from-slate-50 to-slate-100">
      <div className="absolute inset-0 flex items-center justify-center">
        <div className="flex flex-col items-center gap-3">
          <div className="w-12 h-12 rounded-full border-3 border-saffron-400 border-t-saffron-600 animate-spin" />
          <Skeleton className="h-3 w-32" variant="text" />
        </div>
      </div>
    </div>
  </div>
)

export const SkeletonLoader: React.FC<SkeletonLoaderProps> = ({ type = 'card', count = 1 }) => {
  const renderSkeleton = () => {
    switch (type) {
      case 'stats':
        return <StatsSkeleton />
      case 'card':
        return Array.from({ length: count }).map((_, i) => <CardSkeleton key={i} />)
      case 'list':
        return <ListSkeleton count={count} />
      case 'chart':
        return <ChartSkeleton />
      case 'table':
        return <TableSkeleton count={count} />
      case 'graph':
        return <GraphSkeleton />
      default:
        return <CardSkeleton />
    }
  }

  return <>{renderSkeleton()}</>
}

export default SkeletonLoader
