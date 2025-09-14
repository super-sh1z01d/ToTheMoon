import React from 'react';
import { Filter, X } from 'lucide-react';
import type { TokenStatus } from '../types/api';
import { getStatusText } from '../utils/format';

interface TokensFilterProps {
  selectedStatus: TokenStatus | null;
  onStatusChange: (status: TokenStatus | null) => void;
  totalCounts: Record<TokenStatus, number>;
  totalTokens: number;
}

const STATUS_OPTIONS: TokenStatus[] = ['initial', 'active', 'archived'];

export const TokensFilter: React.FC<TokensFilterProps> = ({
  selectedStatus,
  onStatusChange,
  totalCounts,
  totalTokens
}) => {
  return (
    <div className="card">
      <div className="p-6">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center">
            <Filter className="w-5 h-5 text-gray-400 mr-2" />
            <h3 className="text-lg font-medium text-gray-900">Фильтры</h3>
          </div>
          {selectedStatus && (
            <button
              onClick={() => onStatusChange(null)}
              className="flex items-center text-sm text-gray-500 hover:text-gray-700"
            >
              <X className="w-4 h-4 mr-1" />
              Сбросить
            </button>
          )}
        </div>

        <div className="space-y-3">
          <div>
            <p className="text-sm font-medium text-gray-700 mb-2">По статусу</p>
            <div className="space-y-2">
              {/* All tokens option */}
              <label className="flex items-center">
                <input
                  type="radio"
                  name="status"
                  checked={selectedStatus === null}
                  onChange={() => onStatusChange(null)}
                  className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300"
                />
                <span className="ml-3 text-sm text-gray-700">
                  Все токены
                  <span className="ml-2 text-gray-500">({totalTokens})</span>
                </span>
              </label>

              {/* Status options */}
              {STATUS_OPTIONS.map((status) => (
                <label key={status} className="flex items-center">
                  <input
                    type="radio"
                    name="status"
                    checked={selectedStatus === status}
                    onChange={() => onStatusChange(status)}
                    className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300"
                  />
                  <span className="ml-3 text-sm text-gray-700">
                    {getStatusText(status)}
                    <span className="ml-2 text-gray-500">
                      ({totalCounts[status] || 0})
                    </span>
                  </span>
                </label>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
