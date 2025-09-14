import type { TokenStatus } from '../types/api';

// Date formatting utilities
export const formatDate = (dateString: string | null | undefined): string => {
  if (!dateString) return '—';
  
  try {
    const date = new Date(dateString);
    return new Intl.DateTimeFormat('ru-RU', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    }).format(date);
  } catch {
    return '—';
  }
};

export const formatRelativeTime = (dateString: string | null | undefined): string => {
  if (!dateString) return '—';
  
  try {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    
    const seconds = Math.floor(diffMs / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);
    const days = Math.floor(hours / 24);
    
    if (days > 0) {
      return `${days} ${days === 1 ? 'день' : days < 5 ? 'дня' : 'дней'} назад`;
    } else if (hours > 0) {
      return `${hours} ${hours === 1 ? 'час' : hours < 5 ? 'часа' : 'часов'} назад`;
    } else if (minutes > 0) {
      return `${minutes} ${minutes === 1 ? 'минута' : minutes < 5 ? 'минуты' : 'минут'} назад`;
    } else {
      return 'только что';
    }
  } catch {
    return '—';
  }
};

// Number formatting utilities
export const formatNumber = (num: number | null | undefined): string => {
  if (num === null || num === undefined) return '—';
  
  return new Intl.NumberFormat('ru-RU').format(num);
};

export const formatScore = (score: number | null | undefined): string => {
  if (score === null || score === undefined) return '—';
  
  return score.toFixed(3);
};

export const formatPercentage = (value: number | null | undefined): string => {
  if (value === null || value === undefined) return '—';
  
  return new Intl.NumberFormat('ru-RU', {
    style: 'percent',
    minimumFractionDigits: 1,
    maximumFractionDigits: 1,
  }).format(value / 100);
};

// Address formatting utilities
export const shortenAddress = (address: string | null | undefined, chars = 6): string => {
  if (!address) return '—';
  
  if (address.length <= chars * 2) return address;
  
  return `${address.slice(0, chars)}...${address.slice(-chars)}`;
};

export const copyToClipboard = async (text: string): Promise<boolean> => {
  try {
    await navigator.clipboard.writeText(text);
    return true;
  } catch {
    // Fallback for older browsers
    try {
      const textArea = document.createElement('textarea');
      textArea.value = text;
      textArea.style.position = 'fixed';
      textArea.style.left = '-999999px';
      textArea.style.top = '-999999px';
      document.body.appendChild(textArea);
      textArea.focus();
      textArea.select();
      const result = document.execCommand('copy');
      document.body.removeChild(textArea);
      return result;
    } catch {
      return false;
    }
  }
};

// Status formatting
export const getStatusColor = (status: TokenStatus): string => {
  switch (status) {
    case 'initial':
      return 'badge-initial';
    case 'active':
      return 'badge-active';
    case 'archived':
      return 'badge-archived';
    default:
      return 'badge-initial';
  }
};

export const getStatusText = (status: TokenStatus): string => {
  switch (status) {
    case 'initial':
      return 'Начальный';
    case 'active':
      return 'Активный';
    case 'archived':
      return 'Архивный';
    default:
      return status;
  }
};

// Health status formatting
export const getHealthStatusColor = (status: string): string => {
  switch (status) {
    case 'healthy':
      return 'text-success-600';
    case 'degraded':
      return 'text-warning-600';
    case 'unhealthy':
      return 'text-danger-600';
    default:
      return 'text-gray-600';
  }
};

export const getHealthStatusText = (status: string): string => {
  switch (status) {
    case 'healthy':
      return 'Здоров';
    case 'degraded':
      return 'Деградация';
    case 'unhealthy':
      return 'Неисправен';
    case 'unknown':
      return 'Неизвестно';
    default:
      return status;
  }
};
