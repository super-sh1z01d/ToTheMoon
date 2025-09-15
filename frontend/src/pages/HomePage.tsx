import React, { useState, useCallback } from 'react';
import type { Token, TokenStatus } from '../types/api';
import { useTokens, useSystemStats, useHealth } from '../hooks/useApi';
import { Header } from '../components/Header';
import { SystemStats } from '../components/SystemStats';
import { TokensFilter } from '../components/TokensFilter';
import { TokensTable } from '../components/TokensTable';

const TOKENS_PER_PAGE = 20;

interface HomePageProps {
  onNavigateToAdmin?: () => void;
}

export const HomePage: React.FC<HomePageProps> = ({ onNavigateToAdmin }) => {
  const [selectedStatus, setSelectedStatus] = useState<TokenStatus | null>(null);
  const [currentPage, setCurrentPage] = useState(0);

  // API hooks
  const { data: health, loading: healthLoading } = useHealth();
  const { data: systemStats, loading: statsLoading, error: statsError } = useSystemStats();
  
  const {
    data: tokensData,
    loading: tokensLoading,
    error: tokensError,
    refresh: refreshTokens,
    isRefreshing
  } = useTokens({
    status: selectedStatus || undefined,
    limit: TOKENS_PER_PAGE,
    offset: currentPage * TOKENS_PER_PAGE
  });

  // Handlers
  const handleStatusChange = useCallback((status: TokenStatus | null) => {
    setSelectedStatus(status);
    setCurrentPage(0); // Reset pagination when filter changes
  }, []);

  const handleLoadMore = useCallback(() => {
    setCurrentPage(prev => prev + 1);
  }, []);

  const handleCreateToken = useCallback(() => {
    // TODO: Implement create token modal
    console.log('Create token clicked');
  }, []);

  const handleViewToken = useCallback((token: Token) => {
    // TODO: Implement token details modal
    console.log('View token:', token);
  }, []);

  // Generate status counts for filter
  const statusCounts: Record<TokenStatus, number> = {
    initial: systemStats?.by_status?.initial || 0,
    active: systemStats?.by_status?.active || 0,
    archived: systemStats?.by_status?.archived || 0,
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Header 
        health={health} 
        healthLoading={healthLoading}
        onNavigateToAdmin={onNavigateToAdmin}
      />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* System Stats */}
        <div className="mb-8">
          <SystemStats
            stats={systemStats}
            loading={statsLoading}
            error={statsError}
          />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
          {/* Filters Sidebar */}
          <div className="lg:col-span-1">
            <TokensFilter
              selectedStatus={selectedStatus}
              onStatusChange={handleStatusChange}
              totalCounts={statusCounts}
              totalTokens={systemStats?.total_tokens || 0}
            />
          </div>

          {/* Main Content */}
          <div className="lg:col-span-3">
            <TokensTable
              tokens={tokensData?.tokens || []}
              loading={tokensLoading}
              error={tokensError}
              onRefresh={refreshTokens}
              onCreateToken={handleCreateToken}
              onViewToken={handleViewToken}
              totalTokens={tokensData?.total || 0}
              hasMore={tokensData?.has_more || false}
              onLoadMore={handleLoadMore}
              isRefreshing={isRefreshing}
            />
          </div>
        </div>
      </main>
    </div>
  );
};
