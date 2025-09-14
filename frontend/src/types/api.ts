// API Response Types

export interface ApiResponse<T> {
  data?: T;
  error?: string;
  message?: string;
}

export interface PaginationParams {
  limit?: number;
  offset?: number;
}

export interface PaginationResponse<T> {
  items: T[];
  total: number;
  limit: number;
  offset: number;
  has_more: boolean;
}

// Token Types
export type TokenStatus = 'initial' | 'active' | 'archived';

export interface Token {
  id: string;
  token_address: string;
  status: TokenStatus;
  created_at: string;
  updated_at: string;
  activated_at?: string | null;
  archived_at?: string | null;
  last_score_value?: number | null;
  last_score_calculated_at?: string | null;
  pools_count?: number;
}

export interface TokenCreate {
  token_address: string;
}

export interface TokenUpdate {
  status?: TokenStatus;
  last_score_value?: number;
}

export interface TokenListResponse {
  tokens: Token[];
  total: number;
  limit: number;
  offset: number;
  has_more: boolean;
}

export interface TokenStatusHistory {
  id: string;
  old_status?: TokenStatus | null;
  new_status: TokenStatus;
  reason: string;
  changed_at: string;
  change_metadata?: string | null;
}

// Pool Types
export interface Pool {
  id: string;
  pool_address: string;
  token_id: string;
  dex_name: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface PoolCreate {
  pool_address: string;
  token_id: string;
  dex_name: string;
  is_active?: boolean;
}

export interface PoolUpdate {
  dex_name?: string;
  is_active?: boolean;
}

// System Types
export interface SystemStats {
  total_tokens: number;
  by_status: Record<TokenStatus, number>;
  total_pools: number;
  active_pools: number;
  config_params: number;
}

export interface SystemConfig {
  config: Record<string, Record<string, {
    value: any;
    description?: string;
    updated_at?: string;
  }>>;
  total_params: number;
}

export interface HealthStatus {
  status: 'healthy' | 'degraded' | 'unhealthy';
  timestamp: number;
  services: {
    api: 'healthy' | 'unhealthy';
    redis: 'healthy' | 'unhealthy' | 'unknown';
    postgres: 'healthy' | 'unhealthy' | 'unknown';
  };
}

export interface AppInfo {
  name: string;
  version: string;
  description: string;
  environment: string;
  features: string[];
}
