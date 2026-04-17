import React from 'react';

export interface SkeletonLoaderProps {
  type?: 'card' | 'list' | 'chart' | 'table';
  count?: number;
}

function CardSkeleton() {
  return (
    <div className="bg-white rounded-lg shadow-md p-6 border-l-4 border-gray-200 animate-pulse">
      <div className="h-5 bg-gray-200 rounded w-1/3 mb-3" />
      <div className="h-3 bg-gray-100 rounded w-2/3 mb-4" />
      <div className="space-y-2">
        <div className="h-10 bg-gray-100 rounded" />
        <div className="h-10 bg-gray-100 rounded w-5/6" />
      </div>
    </div>
  );
}

function ListSkeleton({ count = 5 }: { count?: number }) {
  return (
    <div className="space-y-3 animate-pulse">
      {Array.from({ length: count }).map((_, i) => (
        <div key={i} className="flex items-center gap-4 p-3 bg-white rounded border border-gray-100">
          <div className="w-10 h-10 bg-gray-200 rounded-full" />
          <div className="flex-1 space-y-2">
            <div className="h-4 bg-gray-200 rounded w-1/4" />
            <div className="h-3 bg-gray-100 rounded w-2/3" />
          </div>
          <div className="w-16 h-6 bg-gray-100 rounded-full" />
        </div>
      ))}
    </div>
  );
}

function ChartSkeleton() {
  return (
    <div className="bg-white rounded-lg shadow-md p-6 animate-pulse">
      <div className="h-5 bg-gray-200 rounded w-1/4 mb-4" />
      <div className="h-48 bg-gray-100 rounded flex items-end justify-around px-4">
        {Array.from({ length: 8 }).map((_, i) => (
          <div
            key={i}
            className="w-8 bg-gray-200 rounded-t"
            style={{ height: `${Math.random() * 60 + 20}%` }}
          />
        ))}
      </div>
    </div>
  );
}

function TableSkeleton({ count = 5 }: { count?: number }) {
  return (
    <div className="bg-white rounded-lg shadow-md overflow-hidden animate-pulse">
      <div className="px-6 py-3 bg-gray-50 border-b border-gray-200">
        <div className="flex gap-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="h-4 bg-gray-200 rounded w-24" />
          ))}
        </div>
      </div>
      {Array.from({ length: count }).map((_, i) => (
        <div key={i} className="px-6 py-3 border-b border-gray-100 flex gap-4">
          {Array.from({ length: 4 }).map((_, j) => (
            <div key={j} className="h-4 bg-gray-100 rounded w-24" />
          ))}
        </div>
      ))}
    </div>
  );
}

export function SkeletonLoader({ type = 'card', count = 1 }: SkeletonLoaderProps) {
  const renderSkeleton = () => {
    switch (type) {
      case 'card':
        return Array.from({ length: count }).map((_, i) => <CardSkeleton key={i} />);
      case 'list':
        return <ListSkeleton count={count} />;
      case 'chart':
        return <ChartSkeleton />;
      case 'table':
        return <TableSkeleton count={count} />;
      default:
        return <CardSkeleton />;
    }
  };

  return <>{renderSkeleton()}</>;
}
