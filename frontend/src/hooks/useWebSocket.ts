import { useEffect, useRef, useState, useCallback } from 'react';

// Types for WebSocket messages
export interface WebSocketMessage {
  type: string;
  data?: any;
  timestamp?: string;
}

export interface TokenUpdate {
  type: 'token_update';
  update_type: 'status_changed' | 'score_updated' | 'created';
  token_address: string;
  data: any;
  timestamp: string;
}

export interface ScoringUpdate {
  type: 'scoring_update';
  token_address: string;
  data: {
    score_value: number;
    score_smoothed: number;
    model_name: string;
    components: any;
  };
  timestamp: string;
}

export interface SystemStatsUpdate {
  type: 'system_stats_update';
  data: any;
  timestamp: string;
}

export interface LifecycleEvent {
  type: 'lifecycle_event';
  event_type: 'activated' | 'archived' | 'deactivated';
  token_address: string;
  data: any;
  timestamp: string;
}

// Hook for WebSocket connection
export function useWebSocket() {
  const [isConnected, setIsConnected] = useState(false);
  const [connectionError, setConnectionError] = useState<string | null>(null);
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null);
  const websocketRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<number | null>(null);
  const subscriptionsRef = useRef<Set<string>>(new Set());

  const connect = useCallback(() => {
    try {
      // WebSocket URL (ws для HTTP, wss для HTTPS)
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const wsUrl = `${protocol}//${window.location.host}/api/realtime/ws`;
      
      console.log('Connecting to WebSocket:', wsUrl);
      
      const ws = new WebSocket(wsUrl);
      
      ws.onopen = () => {
        console.log('✅ WebSocket connected');
        setIsConnected(true);
        setConnectionError(null);
        
        // Восстанавливаем подписки
        subscriptionsRef.current.forEach(subscription => {
          ws.send(JSON.stringify({
            type: 'subscribe',
            subscription: subscription
          }));
        });
      };
      
      ws.onclose = (event) => {
        console.log('WebSocket closed:', event.code, event.reason);
        setIsConnected(false);
        websocketRef.current = null;
        
        // Попытка переподключения через 5 секунд
        if (!event.wasClean) {
          reconnectTimeoutRef.current = setTimeout(() => {
            console.log('Attempting to reconnect...');
            connect();
          }, 5000);
        }
      };
      
      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        setConnectionError('WebSocket connection error');
      };
      
      ws.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data);
          setLastMessage(message);
          
          // Логируем важные сообщения
          if (message.type !== 'connection_established' && message.type !== 'pong') {
            console.log('WebSocket message:', message.type, message.data);
          }
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error);
        }
      };
      
      websocketRef.current = ws;
      
    } catch (error) {
      console.error('Failed to create WebSocket connection:', error);
      setConnectionError('Failed to create connection');
    }
  }, []);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
    
    if (websocketRef.current) {
      websocketRef.current.close(1000, 'Manual disconnect');
      websocketRef.current = null;
    }
    
    setIsConnected(false);
    setConnectionError(null);
  }, []);

  const subscribe = useCallback((subscriptionType: string) => {
    subscriptionsRef.current.add(subscriptionType);
    
    if (websocketRef.current && isConnected) {
      websocketRef.current.send(JSON.stringify({
        type: 'subscribe',
        subscription: subscriptionType
      }));
    }
  }, [isConnected]);

  const unsubscribe = useCallback((subscriptionType: string) => {
    subscriptionsRef.current.delete(subscriptionType);
    
    if (websocketRef.current && isConnected) {
      websocketRef.current.send(JSON.stringify({
        type: 'unsubscribe',
        subscription: subscriptionType
      }));
    }
  }, [isConnected]);

  const sendMessage = useCallback((message: any) => {
    if (websocketRef.current && isConnected) {
      websocketRef.current.send(JSON.stringify(message));
    }
  }, [isConnected]);

  // Автоматическое подключение при монтировании
  useEffect(() => {
    connect();
    
    // Cleanup при размонтировании
    return () => {
      disconnect();
    };
  }, [connect, disconnect]);

  // Периодический ping для поддержания соединения
  useEffect(() => {
    if (!isConnected) return;
    
    const pingInterval = setInterval(() => {
      sendMessage({ type: 'ping' });
    }, 30000); // Ping каждые 30 секунд
    
    return () => clearInterval(pingInterval);
  }, [isConnected, sendMessage]);

  return {
    isConnected,
    connectionError,
    lastMessage,
    connect,
    disconnect,
    subscribe,
    unsubscribe,
    sendMessage,
    subscriptions: Array.from(subscriptionsRef.current)
  };
}

// Hook for token updates
export function useTokenUpdates() {
  const { isConnected, lastMessage, subscribe, unsubscribe } = useWebSocket();
  const [tokenUpdates, setTokenUpdates] = useState<TokenUpdate[]>([]);

  useEffect(() => {
    if (isConnected) {
      subscribe('token_updates');
      return () => unsubscribe('token_updates');
    }
  }, [isConnected, subscribe, unsubscribe]);

  useEffect(() => {
    if (lastMessage && lastMessage.type === 'token_update') {
      const update = lastMessage as TokenUpdate;
      setTokenUpdates(prev => [update, ...prev.slice(0, 49)]); // Последние 50 обновлений
    }
  }, [lastMessage]);

  return { tokenUpdates, isConnected };
}

// Hook for scoring updates
export function useScoringUpdates() {
  const { isConnected, lastMessage, subscribe, unsubscribe } = useWebSocket();
  const [scoringUpdates, setScoringUpdates] = useState<ScoringUpdate[]>([]);

  useEffect(() => {
    if (isConnected) {
      subscribe('scoring_updates');
      return () => unsubscribe('scoring_updates');
    }
  }, [isConnected, subscribe, unsubscribe]);

  useEffect(() => {
    if (lastMessage && lastMessage.type === 'scoring_update') {
      const update = lastMessage as ScoringUpdate;
      setScoringUpdates(prev => [update, ...prev.slice(0, 29)]); // Последние 30 обновлений
    }
  }, [lastMessage]);

  return { scoringUpdates, isConnected };
}

// Hook for system stats updates
export function useSystemStatsUpdates() {
  const { isConnected, lastMessage, subscribe, unsubscribe } = useWebSocket();
  const [systemStats, setSystemStats] = useState<any>(null);
  const [lastUpdate, setLastUpdate] = useState<string | null>(null);

  useEffect(() => {
    if (isConnected) {
      subscribe('system_stats');
      return () => unsubscribe('system_stats');
    }
  }, [isConnected, subscribe, unsubscribe]);

  useEffect(() => {
    if (lastMessage && lastMessage.type === 'system_stats_update') {
      const update = lastMessage as SystemStatsUpdate;
      setSystemStats(update.data);
      setLastUpdate(update.timestamp);
    }
  }, [lastMessage]);

  return { systemStats, lastUpdate, isConnected };
}

// Hook for lifecycle events
export function useLifecycleEvents() {
  const { isConnected, lastMessage, subscribe, unsubscribe } = useWebSocket();
  const [lifecycleEvents, setLifecycleEvents] = useState<LifecycleEvent[]>([]);

  useEffect(() => {
    if (isConnected) {
      subscribe('lifecycle_events');
      return () => unsubscribe('lifecycle_events');
    }
  }, [isConnected, subscribe, unsubscribe]);

  useEffect(() => {
    if (lastMessage && lastMessage.type === 'lifecycle_event') {
      const event = lastMessage as LifecycleEvent;
      setLifecycleEvents(prev => [event, ...prev.slice(0, 19)]); // Последние 20 событий
    }
  }, [lastMessage]);

  return { lifecycleEvents, isConnected };
}

// Hook for Celery status updates
export function useCeleryStatus() {
  const { isConnected, lastMessage, subscribe, unsubscribe } = useWebSocket();
  const [celeryStatus, setCeleryStatus] = useState<any>(null);
  const [lastUpdate, setLastUpdate] = useState<string | null>(null);

  useEffect(() => {
    if (isConnected) {
      subscribe('celery_status');
      return () => unsubscribe('celery_status');
    }
  }, [isConnected, subscribe, unsubscribe]);

  useEffect(() => {
    if (lastMessage && lastMessage.type === 'celery_status') {
      setCeleryStatus(lastMessage.data);
      setLastUpdate(lastMessage.timestamp || new Date().toISOString());
    }
  }, [lastMessage]);

  return { celeryStatus, lastUpdate, isConnected };
}
