import React from 'react';
import type { TokenStatus as TokenStatusType } from '../types/api';
import { getStatusColor, getStatusText } from '../utils/format';

interface TokenStatusProps {
  status: TokenStatusType;
  className?: string;
}

export const TokenStatus: React.FC<TokenStatusProps> = ({ status, className = '' }) => {
  const colorClass = getStatusColor(status);
  const statusText = getStatusText(status);

  return (
    <span className={`badge ${colorClass} ${className}`}>
      {statusText}
    </span>
  );
};
