# Соглашения по разработке кода

> **Базовый документ:** [vision.md](./vision.md) - обязательно изучи перед началом работы

## Основные принципы

### Простота и KISS
- **Никакого оверинжиниринга** - выбирай самое простое решение
- **Один компонент = одна задача** - четкое разделение ответственности
- **Минимум зависимостей** - используй только необходимые библиотеки
- **Явное лучше неявного** - все зависимости и конфигурации должны быть явными

### Архитектурные требования
- **Модульность скоринга** - новые модели должны добавляться без изменения основной логики
- **Dependency Injection** - используй DI для всех сервисов и конфигурации
- **Event-driven** - обрабатывай WebSocket события и фоновые задачи через события
- **Graceful degradation** - система должна работать при недоступности внешних API

## Код Python

### Обязательные требования
```python
# ✅ Type hints всегда
def calculate_score(token_metrics: TokenMetrics) -> ScoringResult:
    pass

# ✅ Pydantic для валидации
class TokenMetrics(BaseModel):
    tx_count_5m: int
    volume_5m_usd: Decimal

# ✅ Asyncio для I/O
async def fetch_birdeye_data(token_address: str) -> BirdeyeResponse:
    pass
```

### Структура модулей
- `app/core/scoring/` - каждая модель скоринга = отдельный файл
- `app/models/` - SQLAlchemy модели
- `app/schemas/` - Pydantic схемы (валидация)
- `app/api/` - FastAPI endpoints
- `app/workers/` - Celery tasks

### Обработка ошибок
```python
# ✅ Fail Fast - быстрое обнаружение проблем
if not token_address:
    raise ValueError("Token address is required")

# ✅ Graceful degradation для внешних API
try:
    data = await birdeye_api.get_token_data(token_address)
except APIError:
    logger.warning("Birdeye API unavailable, using cached data")
    data = await cache.get_token_data(token_address)
```

## Код TypeScript/React

### Структура компонентов
- `src/components/` - переиспользуемые компоненты
- `src/pages/` - страницы (главная, админ-панель)
- `src/hooks/` - кастомные хуки для бизнес-логики
- `src/types/` - TypeScript типы

### Принципы компонентов
```typescript
// ✅ Простые, функциональные компоненты
interface TokenRowProps {
  token: TokenData;
  onTokenClick: (tokenId: string) => void;
}

// ✅ Один компонент = одна ответственность
const TokenRow: React.FC<TokenRowProps> = ({ token, onTokenClick }) => {
  return (
    <tr onClick={() => onTokenClick(token.id)}>
      {/* ... */}
    </tr>
  );
};
```

## Конфигурация
- **Configuration over code** - настройки через конфиг, а не хардкод
- **Environment variables** для системных параметров
- **БД (system_config)** для бизнес-параметров с hot reload
- **YAML файлы** для операционных настроек

## База данных
- **Партиционирование** для `token_metrics` (по дням)
- **TTL** для raw данных (7 дней)
- **Индексы** по token_address, timestamp, status
- **UUID** для всех primary keys

## Логирование
```python
# ✅ Структурированные JSON логи
logger.info(
    "Score calculated",
    extra={
        "token_address": token_address,
        "score_value": score,
        "execution_time_ms": exec_time,
        "correlation_id": correlation_id
    }
)
```

## Что НЕ делать
- ❌ Не создавай абстракции "на всякий случай"
- ❌ Не добавляй функции, которых нет в vision.md
- ❌ Не используй сложные паттерны без необходимости
- ❌ Не создавай глубокую вложенность папок
- ❌ Не добавляй зависимости без обоснования

## Документация
- **Docstrings** только для публичных методов
- **Комментарии** для неочевидных решений
- **README** для быстрого старта
- **Никаких** избыточных документов
