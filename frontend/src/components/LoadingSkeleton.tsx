import React from 'react';

interface LoadingSkeletonProps {
  className?: string;
  width?: string;
  height?: string;
  rows?: number;
}

export const LoadingSkeleton: React.FC<LoadingSkeletonProps> = ({
  className = '',
  width = 'w-full',
  height = 'h-4',
  rows = 1
}) => {
  if (rows === 1) {
    return (
      <div className={`loading-skeleton ${width} ${height} ${className}`} />
    );
  }

  return (
    <div className={`space-y-2 ${className}`}>
      {Array.from({ length: rows }, (_, index) => (
        <div
          key={index}
          className={`loading-skeleton ${width} ${height}`}
        />
      ))}
    </div>
  );
};

// Table skeleton specifically for token rows
export const TokenTableSkeleton: React.FC<{ rows?: number }> = ({ rows = 5 }) => {
  return (
    <div className="animate-pulse">
      {Array.from({ length: rows }, (_, index) => (
        <div key={index} className="border-b border-gray-200 px-6 py-4">
          <div className="flex items-center space-x-4">
            <LoadingSkeleton width="w-32" height="h-4" />
            <LoadingSkeleton width="w-20" height="h-6" />
            <LoadingSkeleton width="w-24" height="h-4" />
            <LoadingSkeleton width="w-16" height="h-4" />
            <LoadingSkeleton width="w-12" height="h-4" />
            <LoadingSkeleton width="w-24" height="h-4" />
          </div>
        </div>
      ))}
    </div>
  );
};
