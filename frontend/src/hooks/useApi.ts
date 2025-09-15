import { useState, useEffect, useCallback } from 'react';
import type { TokenStatus, PaginationParams } from '../types/api';
import { api, ApiError } from '../utils/api';

// Generic hook for API calls with loading and error states
export function useApiCall<T>(
  apiCall: () => Promise<T>,
  dependencies: any[] = []
) {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const execute = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const result = await apiCall();
      setData(result);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError(err instanceof Error ? err.message : 'Произошла ошибка');
      }
    } finally {
      setLoading(false);
    }
  }, dependencies);

  useEffect(() => {
    execute();
  }, [execute]);

  return { data, loading, error, refetch: execute };
}

// Hook for system health
export function useHealth() {
  return useApiCall(() => api.health.getHealth(), []);
}

// Hook for system stats
export function useSystemStats() {
  return useApiCall(() => api.system.getStats(), []);
}

// Hook for system config
export function useSystemConfig() {
  return useApiCall(() => api.system.getConfig(), []);
}

// Hook for tokens with pagination and filtering
export function useTokens(params: PaginationParams & { status?: TokenStatus } = {}) {
  const [isRefreshing, setIsRefreshing] = useState(false);
  
  const result = useApiCall(
    () => api.tokens.getTokens(params),
    [params.limit, params.offset, params.status]
  );

  const refresh = useCallback(async () => {
    setIsRefreshing(true);
    try {
      await result.refetch();
    } finally {
      setIsRefreshing(false);
    }
  }, [result.refetch]);

  return {
    ...result,
    isRefreshing,
    refresh
  };
}

// Hook for single token
export function useToken(id: string | null) {
  return useApiCall(
    () => id ? api.tokens.getToken(id) : Promise.resolve(null),
    [id]
  );
}

// Hook for token history
export function useTokenHistory(id: string | null) {
  return useApiCall(
    () => id ? api.tokens.getTokenHistory(id) : Promise.resolve([]),
    [id]
  );
}

// Hook for pools
export function usePools(params: {
  token_id?: string;
  dex_name?: string;
  active_only?: boolean;
  limit?: number;
  offset?: number;
} = {}) {
  return useApiCall(
    () => api.pools.getPools(params),
    [params.token_id, params.dex_name, params.active_only, params.limit, params.offset]
  );
}

// Hook for async actions with loading state
export function useAsyncAction<T extends any[], R>(
  action: (...args: T) => Promise<R>
) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const execute = useCallback(async (...args: T): Promise<R | null> => {
    try {
      setLoading(true);
      setError(null);
      const result = await action(...args);
      return result;
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError(err instanceof Error ? err.message : 'Произошла ошибка');
      }
      return null;
    } finally {
      setLoading(false);
    }
  }, [action]);

  return { execute, loading, error };
}

// Hook for creating tokens
export function useCreateToken() {
  return useAsyncAction(api.tokens.createToken);
}

// Hook for updating tokens
export function useUpdateToken() {
  return useAsyncAction(api.tokens.updateToken);
}

// Hook for deleting tokens
export function useDeleteToken() {
  return useAsyncAction(api.tokens.deleteToken);
}

// Hook for creating pools
export function useCreatePool() {
  return useAsyncAction(api.pools.createPool);
}

// Hook for updating pools
export function useUpdatePool() {
  return useAsyncAction(api.pools.updatePool);
}

// Hook for pool actions
export function usePoolActions() {
  const activate = useAsyncAction(api.pools.activatePool);
  const deactivate = useAsyncAction(api.pools.deactivatePool);
  const delete_ = useAsyncAction(api.pools.deletePool);

  return {
    activate,
    deactivate,
    delete: delete_
  };
}
