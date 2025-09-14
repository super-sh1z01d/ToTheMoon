import React, { useState, useCallback } from 'react';
import { Settings, Save, RotateCcw, AlertTriangle, CheckCircle, Info } from 'lucide-react';
import { useSystemConfig } from '../hooks/useApi';

interface ConfigParam {
  value: any;
  description?: string;
  updated_at?: string;
}

interface ConfigSection {
  [key: string]: ConfigParam;
}


export const AdminPage: React.FC = () => {
  const { data: configData, loading, error, refetch } = useSystemConfig();
  const [editingConfig, setEditingConfig] = useState<Record<string, any>>({});
  const [pendingChanges, setPendingChanges] = useState<Set<string>>(new Set());
  const [saveStatus, setSaveStatus] = useState<'idle' | 'saving' | 'success' | 'error'>('idle');
  const [saveMessage, setSaveMessage] = useState<string>('');

  const handleConfigChange = useCallback((category: string, key: string, newValue: any) => {
    const configKey = `${category}.${key}`;
    setEditingConfig(prev => ({
      ...prev,
      [configKey]: newValue
    }));
    
    setPendingChanges(prev => new Set(prev).add(configKey));
  }, []);

  const handleSaveConfig = useCallback(async (category: string, key: string) => {
    const configKey = `${category}.${key}`;
    const newValue = editingConfig[configKey];
    
    if (newValue === undefined) return;
    
    setSaveStatus('saving');
    
    try {
      const response = await fetch(`/api/system/config/${key}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          value: newValue,
          description: `Updated via admin panel at ${new Date().toLocaleString()}`
        }),
      });
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      setSaveStatus('success');
      setSaveMessage(`Параметр ${key} обновлен успешно`);
      
      // Убираем из pending изменений
      setPendingChanges(prev => {
        const newSet = new Set(prev);
        newSet.delete(configKey);
        return newSet;
      });
      
      // Обновляем данные
      await refetch();
      
      // Сбрасываем статус через 3 секунды
      setTimeout(() => {
        setSaveStatus('idle');
        setSaveMessage('');
      }, 3000);
      
    } catch (error) {
      setSaveStatus('error');
      setSaveMessage(`Ошибка сохранения: ${error instanceof Error ? error.message : 'Неизвестная ошибка'}`);
      
      setTimeout(() => {
        setSaveStatus('idle');
        setSaveMessage('');
      }, 5000);
    }
  }, [editingConfig, refetch]);

  const handleResetConfig = useCallback((category: string, key: string) => {
    const configKey = `${category}.${key}`;
    
    // Убираем из редактируемых
    setEditingConfig(prev => {
      const newConfig = { ...prev };
      delete newConfig[configKey];
      return newConfig;
    });
    
    // Убираем из pending
    setPendingChanges(prev => {
      const newSet = new Set(prev);
      newSet.delete(configKey);
      return newSet;
    });
  }, []);

  const renderConfigValue = (category: string, key: string, param: ConfigParam) => {
    const configKey = `${category}.${key}`;
    const currentValue = editingConfig[configKey] !== undefined ? editingConfig[configKey] : param.value;
    const hasChanges = pendingChanges.has(configKey);
    
    // Определяем тип поля
    const isNumber = typeof param.value === 'number';
    const isBoolean = typeof param.value === 'boolean';
    const isObject = typeof param.value === 'object' && param.value !== null;
    
    return (
      <div key={key} className="border border-gray-200 rounded-lg p-4">
        <div className="flex items-start justify-between mb-3">
          <div className="flex-1">
            <div className="flex items-center space-x-2">
              <h4 className="font-medium text-gray-900">{key}</h4>
              {hasChanges && (
                <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-warning-100 text-warning-800">
                  Изменено
                </span>
              )}
            </div>
            {param.description && (
              <p className="text-sm text-gray-600 mt-1">{param.description}</p>
            )}
            <p className="text-xs text-gray-500 mt-1">
              Обновлено: {param.updated_at ? new Date(param.updated_at).toLocaleString() : 'Неизвестно'}
            </p>
          </div>
        </div>
        
        <div className="space-y-3">
          {/* Поле ввода */}
          <div>
            {isBoolean ? (
              <label className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  checked={currentValue}
                  onChange={(e) => handleConfigChange(category, key, e.target.checked)}
                  className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                />
                <span className="text-sm">{currentValue ? 'Включено' : 'Отключено'}</span>
              </label>
            ) : isNumber ? (
              <input
                type="number"
                value={currentValue}
                onChange={(e) => handleConfigChange(category, key, parseFloat(e.target.value) || 0)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-primary-500 focus:border-primary-500"
                step={key.includes('ALPHA') || key.includes('THRESHOLD') ? '0.01' : '1'}
                min="0"
              />
            ) : isObject ? (
              <textarea
                value={JSON.stringify(currentValue, null, 2)}
                onChange={(e) => {
                  try {
                    const parsed = JSON.parse(e.target.value);
                    handleConfigChange(category, key, parsed);
                  } catch {
                    // Игнорируем ошибки парсинга во время набора
                  }
                }}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-primary-500 focus:border-primary-500 font-mono text-sm"
                rows={4}
                placeholder="JSON объект"
              />
            ) : (
              <input
                type="text"
                value={currentValue}
                onChange={(e) => handleConfigChange(category, key, e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-primary-500 focus:border-primary-500"
              />
            )}
          </div>
          
          {/* Кнопки управления */}
          {hasChanges && (
            <div className="flex items-center space-x-2">
              <button
                onClick={() => handleSaveConfig(category, key)}
                disabled={saveStatus === 'saving'}
                className="btn-primary text-sm"
              >
                <Save className="w-4 h-4 mr-1" />
                {saveStatus === 'saving' ? 'Сохранение...' : 'Сохранить'}
              </button>
              <button
                onClick={() => handleResetConfig(category, key)}
                className="btn-secondary text-sm"
              >
                <RotateCcw className="w-4 h-4 mr-1" />
                Отменить
              </button>
            </div>
          )}
        </div>
      </div>
    );
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="text-center">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
            <p className="mt-2 text-gray-600">Загрузка конфигурации...</p>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="card">
            <div className="p-6 text-center">
              <AlertTriangle className="w-12 h-12 text-danger-500 mx-auto mb-4" />
              <h2 className="text-lg font-medium text-gray-900 mb-2">Ошибка загрузки</h2>
              <p className="text-gray-600 mb-4">{error}</p>
              <button onClick={refetch} className="btn-primary">
                Повторить
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  const config = configData?.config || {};

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between py-6">
            <div className="flex items-center">
              <Settings className="w-8 h-8 text-primary-600 mr-3" />
              <div>
                <h1 className="text-2xl font-bold text-gray-900">Админ-панель</h1>
                <p className="text-sm text-gray-600">Управление параметрами системы ToTheMoon2</p>
              </div>
            </div>
            
            {/* Status indicator */}
            <div className="flex items-center space-x-2">
              {saveStatus === 'success' && (
                <div className="flex items-center text-success-600">
                  <CheckCircle className="w-5 h-5 mr-2" />
                  <span className="text-sm">{saveMessage}</span>
                </div>
              )}
              {saveStatus === 'error' && (
                <div className="flex items-center text-danger-600">
                  <AlertTriangle className="w-5 h-5 mr-2" />
                  <span className="text-sm">{saveMessage}</span>
                </div>
              )}
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Warning */}
        <div className="card mb-8">
          <div className="p-6">
            <div className="flex items-start">
              <Info className="w-5 h-5 text-primary-600 mt-0.5 mr-3 flex-shrink-0" />
              <div>
                <h3 className="text-lg font-medium text-gray-900 mb-2">Внимание</h3>
                <p className="text-gray-700">
                  Изменения параметров системы влияют на работу scoring engine и жизненный цикл токенов. 
                  Некоторые изменения требуют перезагрузки моделей и могут занять несколько минут.
                </p>
                <p className="text-sm text-gray-600 mt-2">
                  Всего параметров: {configData?.total_params || 0} | 
                  Изменений ожидает сохранения: {pendingChanges.size}
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Configuration Sections */}
        <div className="space-y-8">
          {Object.entries(config).map(([category, params]) => (
            <div key={category} className="card">
              <div className="p-6">
                <h2 className="text-xl font-bold text-gray-900 mb-6 capitalize">
                  {category === 'scoring' && '🧮 Скоринг'}
                  {category === 'lifecycle' && '🔄 Жизненный цикл'}
                  {category === 'api' && '🌐 API интеграция'}
                  {category === 'storage' && '💾 Хранение данных'}
                  {category === 'export' && '📤 Экспорт'}
                  {category === 'general' && '⚙️ Общие настройки'}
                  {!['scoring', 'lifecycle', 'api', 'storage', 'export', 'general'].includes(category) && `📁 ${category}`}
                </h2>
                
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  {Object.entries(params as ConfigSection).map(([key, param]) =>
                    renderConfigValue(category, key, param)
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Quick Actions */}
        <div className="mt-8 card">
          <div className="p-6">
            <h2 className="text-xl font-bold text-gray-900 mb-4">🚀 Быстрые действия</h2>
            
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              <button
                onClick={() => fetch('/api/scoring/reload-model', { method: 'POST' })}
                className="btn-primary flex items-center justify-center"
              >
                <RotateCcw className="w-4 h-4 mr-2" />
                Перезагрузить модель скоринга
              </button>
              
              <button
                onClick={() => fetch('/api/lifecycle/monitor-initial', { method: 'POST' })}
                className="btn-secondary flex items-center justify-center"
              >
                <Settings className="w-4 h-4 mr-2" />
                Проверить Initial токены
              </button>
              
              <button
                onClick={() => fetch('/api/birdeye/fetch-all', { method: 'POST' })}
                className="btn-secondary flex items-center justify-center"
              >
                <Settings className="w-4 h-4 mr-2" />
                Обновить метрики всех токенов
              </button>
            </div>
          </div>
        </div>

        {/* Lifecycle Status */}
        <LifecycleStatusSection />
      </main>
    </div>
  );
};

const LifecycleStatusSection: React.FC = () => {
  const [lifecycleData, setLifecycleData] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const fetchLifecycleStats = useCallback(async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/lifecycle/stats');
      const data = await response.json();
      setLifecycleData(data);
    } catch (error) {
      console.error('Error fetching lifecycle stats:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  React.useEffect(() => {
    fetchLifecycleStats();
  }, [fetchLifecycleStats]);

  return (
    <div className="mt-8 card">
      <div className="p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-bold text-gray-900">📊 Статистика жизненного цикла</h2>
          <button
            onClick={fetchLifecycleStats}
            disabled={loading}
            className="btn-secondary text-sm"
          >
            <RotateCcw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            Обновить
          </button>
        </div>
        
        {loading ? (
          <div className="text-center py-8">
            <div className="inline-block animate-spin rounded-full h-6 w-6 border-b-2 border-primary-600"></div>
            <p className="mt-2 text-gray-600">Загрузка статистики...</p>
          </div>
        ) : lifecycleData ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="bg-gray-50 rounded-lg p-4">
              <h4 className="font-medium text-gray-900">Initial токенов проверено</h4>
              <p className="text-2xl font-bold text-primary-600">
                {lifecycleData.manager_stats?.initial_tokens_checked || 0}
              </p>
            </div>
            <div className="bg-gray-50 rounded-lg p-4">
              <h4 className="font-medium text-gray-900">Активировано</h4>
              <p className="text-2xl font-bold text-success-600">
                {lifecycleData.manager_stats?.tokens_activated || 0}
              </p>
            </div>
            <div className="bg-gray-50 rounded-lg p-4">
              <h4 className="font-medium text-gray-900">Архивировано</h4>
              <p className="text-2xl font-bold text-warning-600">
                {lifecycleData.manager_stats?.tokens_archived || 0}
              </p>
            </div>
            <div className="bg-gray-50 rounded-lg p-4">
              <h4 className="font-medium text-gray-900">Деактивировано</h4>
              <p className="text-2xl font-bold text-danger-600">
                {lifecycleData.manager_stats?.tokens_deactivated || 0}
              </p>
            </div>
          </div>
        ) : (
          <p className="text-gray-600">Нет данных о статистике</p>
        )}
      </div>
    </div>
  );
};
