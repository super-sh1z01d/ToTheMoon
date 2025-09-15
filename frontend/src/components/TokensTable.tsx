import React, { useState } from 'react';
import { RefreshCw, Plus, Eye, MoreHorizontal } from 'lucide-react';
import type { Token } from '../types/api';
import { TokenStatus as TokenStatusBadge } from './TokenStatus';
import { AddressDisplay } from './AddressDisplay';
import { TokenTableSkeleton } from './LoadingSkeleton';
import { formatDate, formatRelativeTime, formatScore, formatNumber } from '../utils/format';

interface TokensTableProps {
  tokens: Token[];
  loading: boolean;
  error: string | null;
  onRefresh: () => void;
  onCreateToken: () => void;
  onViewToken: (token: Token) => void;
  totalTokens: number;
  hasMore: boolean;
  onLoadMore: () => void;
  isRefreshing?: boolean;
}

export const TokensTable: React.FC<TokensTableProps> = ({
  tokens,
  loading,
  error,
  onRefresh,
  onCreateToken,
  onViewToken,
  totalTokens,
  hasMore,
  onLoadMore,
  isRefreshing = false
}) => {
  const [selectedTokens, setSelectedTokens] = useState<Set<string>>(new Set());

  const handleSelectToken = (tokenId: string) => {
    const newSelected = new Set(selectedTokens);
    if (newSelected.has(tokenId)) {
      newSelected.delete(tokenId);
    } else {
      newSelected.add(tokenId);
    }
    setSelectedTokens(newSelected);
  };

  const handleSelectAll = () => {
    if (selectedTokens.size === tokens.length) {
      setSelectedTokens(new Set());
    } else {
      setSelectedTokens(new Set(tokens.map(t => t.id)));
    }
  };

  if (error) {
    return (
      <div className="card">
        <div className="p-6 text-center">
          <div className="text-danger-600 mb-4">
            <p className="font-medium">Ошибка загрузки токенов</p>
            <p className="text-sm text-gray-600 mt-1">{error}</p>
          </div>
          <button
            onClick={onRefresh}
            className="btn-primary"
          >
            <RefreshCw className="w-4 h-4 mr-2" />
            Повторить
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="card">
      {/* Header */}
      <div className="p-6 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-medium text-gray-900">
              Токены ({formatNumber(totalTokens)})
            </h2>
            <p className="text-sm text-gray-600 mt-1">
              Управление токенами в системе скоринга
            </p>
          </div>
          <div className="flex items-center space-x-3">
            <button
              onClick={onRefresh}
              disabled={isRefreshing}
              className="btn-secondary"
            >
              <RefreshCw className={`w-4 h-4 mr-2 ${isRefreshing ? 'animate-spin' : ''}`} />
              Обновить
            </button>
            <button
              onClick={onCreateToken}
              className="btn-primary"
            >
              <Plus className="w-4 h-4 mr-2" />
              Добавить токен
            </button>
          </div>
        </div>
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="table">
          <thead className="table-header">
            <tr>
              <th className="table-header-cell">
                <input
                  type="checkbox"
                  checked={selectedTokens.size === tokens.length && tokens.length > 0}
                  onChange={handleSelectAll}
                  className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                />
              </th>
              <th className="table-header-cell">Адрес токена</th>
              <th className="table-header-cell">Статус</th>
              <th className="table-header-cell">Скор</th>
              <th className="table-header-cell">Пулы</th>
              <th className="table-header-cell">Создан</th>
              <th className="table-header-cell">Обновлен</th>
              <th className="table-header-cell">Действия</th>
            </tr>
          </thead>
          <tbody className="table-body">
            {loading ? (
              <tr>
                <td colSpan={8} className="p-0">
                  <TokenTableSkeleton />
                </td>
              </tr>
            ) : tokens.length === 0 ? (
              <tr>
                <td colSpan={8} className="px-6 py-8 text-center text-gray-500">
                  <div className="flex flex-col items-center">
                    <div className="w-12 h-12 bg-gray-100 rounded-full flex items-center justify-center mb-3">
                      <Plus className="w-6 h-6 text-gray-400" />
                    </div>
                    <p className="font-medium mb-1">Токены не найдены</p>
                    <p className="text-sm">Добавьте первый токен для начала работы</p>
                  </div>
                </td>
              </tr>
            ) : (
              tokens.map((token) => (
                <tr
                  key={token.id}
                  className="hover:bg-gray-50 cursor-pointer"
                  onClick={() => onViewToken(token)}
                >
                  <td className="table-cell">
                    <input
                      type="checkbox"
                      checked={selectedTokens.has(token.id)}
                      onChange={(e) => {
                        e.stopPropagation();
                        handleSelectToken(token.id);
                      }}
                      className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                    />
                  </td>
                  <td className="table-cell">
                    <AddressDisplay
                      address={token.token_address}
                      className="text-gray-900"
                    />
                  </td>
                  <td className="table-cell">
                    <TokenStatusBadge status={token.status} />
                  </td>
                  <td className="table-cell">
                    <div className="flex flex-col">
                      <span className="font-medium">
                        {formatScore(token.last_score_value)}
                      </span>
                      {token.last_score_calculated_at && (
                        <span className="text-xs text-gray-500">
                          {formatRelativeTime(token.last_score_calculated_at)}
                        </span>
                      )}
                    </div>
                  </td>
                  <td className="table-cell">
                    <span className="text-gray-900">
                      {formatNumber(token.pools_count || 0)}
                    </span>
                  </td>
                  <td className="table-cell">
                    <div className="flex flex-col">
                      <span className="text-gray-900">
                        {formatDate(token.created_at)}
                      </span>
                      <span className="text-xs text-gray-500">
                        {formatRelativeTime(token.created_at)}
                      </span>
                    </div>
                  </td>
                  <td className="table-cell">
                    <div className="flex flex-col">
                      <span className="text-gray-900">
                        {formatDate(token.updated_at)}
                      </span>
                      <span className="text-xs text-gray-500">
                        {formatRelativeTime(token.updated_at)}
                      </span>
                    </div>
                  </td>
                  <td className="table-cell">
                    <div className="flex items-center space-x-2">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          onViewToken(token);
                        }}
                        className="p-1 text-gray-400 hover:text-primary-600 transition-colors duration-200"
                        title="Просмотр деталей"
                      >
                        <Eye className="w-4 h-4" />
                      </button>
                      <button
                        onClick={(e) => e.stopPropagation()}
                        className="p-1 text-gray-400 hover:text-gray-600 transition-colors duration-200"
                        title="Дополнительные действия"
                      >
                        <MoreHorizontal className="w-4 h-4" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Load More */}
      {hasMore && !loading && (
        <div className="p-6 border-t border-gray-200 text-center">
          <button
            onClick={onLoadMore}
            className="btn-secondary"
          >
            Загрузить еще
          </button>
        </div>
      )}
    </div>
  );
};
