import type {
  Token, TokenCreate, TokenUpdate, TokenListResponse, TokenStatusHistory,
  Pool, PoolCreate, PoolUpdate,
  SystemStats, SystemConfig, HealthStatus, AppInfo,
  PaginationParams
} from '../types/api';

// Base API configuration
// In dev (vite), set VITE_API_BASE_URL if needed; default to backend on 8000
const API_BASE_URL = (import.meta as any).env?.VITE_API_BASE_URL || 'http://localhost:8000/api';

// Generic API error class
export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
    public data?: any
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

// Generic fetch wrapper with error handling
async function apiFetch<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = endpoint.startsWith('http') ? endpoint : `${API_BASE_URL}${endpoint}`;
  
  const config: RequestInit = {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
  };

  try {
    const response = await fetch(url, config);
    
    if (!response.ok) {
      let errorMessage = `HTTP ${response.status}: ${response.statusText}`;
      let errorData: any = null;
      
      try {
        errorData = await response.json();
        errorMessage = errorData.message || errorData.detail || errorMessage;
      } catch {
        // Ignore JSON parsing errors
      }
      
      throw new ApiError(errorMessage, response.status, errorData);
    }

    const contentType = response.headers.get('content-type');
    if (contentType && contentType.includes('application/json')) {
      return await response.json();
    }
    
    return response.text() as any;
  } catch (error) {
    if (error instanceof ApiError) {
      throw error;
    }
    
    // Network or other errors
    throw new ApiError(
      error instanceof Error ? error.message : 'Network error',
      0
    );
  }
}

// Health & System APIs
export const healthApi = {
  getHealth: (): Promise<HealthStatus> => apiFetch('/health'),
  getInfo: (): Promise<AppInfo> => apiFetch('/info'),
};

export const systemApi = {
  getStats: (): Promise<SystemStats> => apiFetch('/system/stats'),
  getConfig: (): Promise<SystemConfig> => apiFetch('/system/config'),
  getConfigValue: (key: string): Promise<any> => apiFetch(`/system/config/${key}`),
  updateConfigValue: (key: string, value: any, description?: string): Promise<any> =>
    apiFetch(`/system/config/${key}`, {
      method: 'PUT',
      body: JSON.stringify({ value, description }),
    }),
};

// Token APIs
export const tokenApi = {
  getTokens: (params: PaginationParams & { status?: string } = {}): Promise<TokenListResponse> => {
    const searchParams = new URLSearchParams();
    
    if (params.limit) searchParams.append('limit', params.limit.toString());
    if (params.offset) searchParams.append('offset', params.offset.toString());
    if (params.status) searchParams.append('status', params.status);
    
    const query = searchParams.toString();
    return apiFetch(`/tokens${query ? `?${query}` : ''}`);
  },
  
  getToken: (id: string): Promise<Token> => apiFetch(`/tokens/${id}`),
  
  createToken: (data: TokenCreate): Promise<Token> =>
    apiFetch('/tokens', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
  
  updateToken: (id: string, data: TokenUpdate): Promise<Token> =>
    apiFetch(`/tokens/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    }),
  
  deleteToken: (id: string): Promise<{ message: string }> =>
    apiFetch(`/tokens/${id}`, {
      method: 'DELETE',
    }),
  
  getTokenHistory: (id: string): Promise<TokenStatusHistory[]> =>
    apiFetch(`/tokens/${id}/history`),
};

// Pool APIs
export const poolApi = {
  getPools: (params: {
    token_id?: string;
    dex_name?: string;
    active_only?: boolean;
    limit?: number;
    offset?: number;
  } = {}): Promise<Pool[]> => {
    const searchParams = new URLSearchParams();
    
    if (params.token_id) searchParams.append('token_id', params.token_id);
    if (params.dex_name) searchParams.append('dex_name', params.dex_name);
    if (params.active_only !== undefined) searchParams.append('active_only', params.active_only.toString());
    if (params.limit) searchParams.append('limit', params.limit.toString());
    if (params.offset) searchParams.append('offset', params.offset.toString());
    
    const query = searchParams.toString();
    return apiFetch(`/pools${query ? `?${query}` : ''}`);
  },
  
  getPool: (id: string): Promise<Pool> => apiFetch(`/pools/${id}`),
  
  createPool: (data: PoolCreate): Promise<Pool> =>
    apiFetch('/pools', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
  
  updatePool: (id: string, data: PoolUpdate): Promise<Pool> =>
    apiFetch(`/pools/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    }),
  
  deletePool: (id: string): Promise<{ message: string }> =>
    apiFetch(`/pools/${id}`, {
      method: 'DELETE',
    }),
  
  activatePool: (id: string): Promise<Pool> =>
    apiFetch(`/pools/${id}/activate`, {
      method: 'POST',
    }),
  
  deactivatePool: (id: string): Promise<Pool> =>
    apiFetch(`/pools/${id}/deactivate`, {
      method: 'POST',
    }),
};

// Combined API object
export const api = {
  health: healthApi,
  system: systemApi,
  tokens: tokenApi,
  pools: poolApi,
};
