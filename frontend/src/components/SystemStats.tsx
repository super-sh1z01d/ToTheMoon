import React from 'react';
import { Activity, Database, Settings, TrendingUp } from 'lucide-react';
import type { SystemStats as SystemStatsType } from '../types/api';
import { LoadingSkeleton } from './LoadingSkeleton';
import { formatNumber } from '../utils/format';

interface SystemStatsProps {
  stats: SystemStatsType | null;
  loading: boolean;
  error: string | null;
}

interface StatCardProps {
  title: string;
  value: number;
  icon: React.ReactNode;
  color: string;
  loading?: boolean;
}

const StatCard: React.FC<StatCardProps> = ({
  title,
  value,
  icon,
  color,
  loading = false
}) => {
  return (
    <div className="card">
      <div className="p-6">
        <div className="flex items-center">
          <div className={`p-3 rounded-lg ${color} mr-4`}>
            {icon}
          </div>
          <div className="flex-1">
            <p className="text-sm font-medium text-gray-600">{title}</p>
            {loading ? (
              <LoadingSkeleton width="w-16" height="h-6" className="mt-1" />
            ) : (
              <p className="text-2xl font-semibold text-gray-900">
                {formatNumber(value)}
              </p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export const SystemStats: React.FC<SystemStatsProps> = ({
  stats,
  loading,
  error
}) => {
  if (error) {
    return (
      <div className="card">
        <div className="p-6 text-center">
          <p className="text-danger-600 font-medium">Ошибка загрузки статистики</p>
          <p className="text-sm text-gray-600 mt-1">{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      <StatCard
        title="Всего токенов"
        value={stats?.total_tokens || 0}
        icon={<TrendingUp className="w-6 h-6 text-white" />}
        color="bg-primary-500"
        loading={loading}
      />
      
      <StatCard
        title="Активных токенов"
        value={stats?.by_status?.active || 0}
        icon={<Activity className="w-6 h-6 text-white" />}
        color="bg-success-500"
        loading={loading}
      />
      
      <StatCard
        title="Всего пулов"
        value={stats?.total_pools || 0}
        icon={<Database className="w-6 h-6 text-white" />}
        color="bg-warning-500"
        loading={loading}
      />
      
      <StatCard
        title="Параметров конфигурации"
        value={stats?.config_params || 0}
        icon={<Settings className="w-6 h-6 text-white" />}
        color="bg-gray-500"
        loading={loading}
      />
    </div>
  );
};
