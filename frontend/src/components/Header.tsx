import React from 'react';
import { TrendingUp, Activity, AlertCircle } from 'lucide-react';
import type { HealthStatus } from '../types/api';
import { getHealthStatusColor, getHealthStatusText } from '../utils/format';

interface HeaderProps {
  health: HealthStatus | null;
  healthLoading: boolean;
  onNavigateToAdmin?: () => void;
}

export const Header: React.FC<HeaderProps> = ({ health, healthLoading, onNavigateToAdmin }) => {
  const getHealthIcon = (status: string) => {
    switch (status) {
      case 'healthy':
        return <Activity className="w-4 h-4" />;
      case 'degraded':
      case 'unhealthy':
        return <AlertCircle className="w-4 h-4" />;
      default:
        return <AlertCircle className="w-4 h-4" />;
    }
  };

  return (
    <header className="bg-white border-b border-gray-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center py-6">
          <div className="flex items-center">
            <div className="flex items-center">
              <TrendingUp className="w-8 h-8 text-primary-600 mr-3" />
              <div>
                <h1 className="text-2xl font-bold text-gray-900">ToTheMoon2</h1>
                <p className="text-sm text-gray-600">Система скоринга токенов Solana</p>
              </div>
            </div>
          </div>

          <div className="flex items-center space-x-4">
            {/* Health Status */}
            <div className="flex items-center space-x-2">
              {healthLoading ? (
                <div className="flex items-center space-x-2">
                  <div className="w-4 h-4 bg-gray-300 rounded animate-pulse" />
                  <span className="text-sm text-gray-500">Проверка...</span>
                </div>
              ) : health ? (
                <div className="flex items-center space-x-2">
                  <div className={getHealthStatusColor(health.status)}>
                    {getHealthIcon(health.status)}
                  </div>
                  <span className={`text-sm ${getHealthStatusColor(health.status)}`}>
                    {getHealthStatusText(health.status)}
                  </span>
                </div>
              ) : (
                <div className="flex items-center space-x-2">
                  <AlertCircle className="w-4 h-4 text-gray-400" />
                  <span className="text-sm text-gray-500">Неизвестно</span>
                </div>
              )}
            </div>

            {/* Admin Panel Button */}
            {onNavigateToAdmin && (
              <button
                onClick={onNavigateToAdmin}
                className="btn-primary text-sm"
              >
                Админ-панель
              </button>
            )}
            
            {/* API Docs Link */}
            <a
              href="/api/docs"
              target="_blank"
              rel="noopener noreferrer"
              className="btn-secondary text-sm"
            >
              API Документация
            </a>
          </div>
        </div>
      </div>
    </header>
  );
};
