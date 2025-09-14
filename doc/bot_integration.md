# Интеграция с NotArb арбитражным ботом

## 📋 Общая информация

ToTheMoon2 генерирует TOML конфигурацию для интеграции с NotArb арбитражным ботом.

**Репозиторий бота:** [NotArb/Release/onchain-bot](https://github.com/NotArb/Release/tree/main/onchain-bot)

## 🔗 URL для интеграции

```
Production:  http://tothemoon.sh1z01d.ru/config/dynamic_strategy.toml
Development: http://localhost/config/dynamic_strategy.toml
```

## 📊 Логика отбора токенов

Согласно функциональному заданию:

1. **Отбор токенов в статусе Active**
2. **Фильтрация по min_score_for_config** (настраиваемый параметр, по умолчанию 0.7)
3. **Сортировка по Score по убыванию**
4. **Выбор топ-3 токенов** (настраиваемо через CONFIG_TOP_COUNT)
5. **Включение активных пулов** для каждого токена

## 📄 Формат TOML конфигурации

```toml
[strategy]
name = "dynamic_strategy"
description = "ToTheMoon2 dynamic arbitrage strategy"
version = "1.0.0"
generated_at = "2025-09-14T12:00:00Z"
model_name = "hybrid_momentum_v1"
min_score_threshold = 0.7
tokens_count = 3

[[tokens]]
address = "TokenAddress1111111111111111111111111111"
score = 0.85
calculated_at = "2025-09-14T12:00:00Z"
status = "active"
pools_count = 2

[tokens.pools]
raydium = ["PoolAddress1111111111111111111111111111"]
orca = ["PoolAddress2222222222222222222222222222"]

[tokens.metadata]
token_id = "uuid-here"
last_score_calculated = "2025-09-14T12:00:00Z"
activated_at = "2025-09-14T10:00:00Z"

[[tokens]]
address = "TokenAddress3333333333333333333333333333"
score = 0.78
# ... аналогично для других токенов

[metadata]
source = "ToTheMoon2"
generation_time = "2025-09-14T12:00:00Z"
tokens_selected = 2
total_pools = 3

[metadata.selection_criteria]
status = "active"
min_score = 0.7
top_count = 3
model = "hybrid_momentum_v1"
```

## ⚙️ Кастомизация параметров

Поддерживаются GET параметры для кастомизации:

```bash
# Кастомный минимальный скор
curl "http://localhost/config/dynamic_strategy.toml?min_score=0.8"

# Кастомное количество токенов
curl "http://localhost/config/dynamic_strategy.toml?top_count=5"

# Кастомная модель скоринга
curl "http://localhost/config/dynamic_strategy.toml?model=hybrid_momentum_v1"

# Комбинация параметров
curl "http://localhost/config/dynamic_strategy.toml?min_score=0.8&top_count=5"
```

## 🕐 Частота обновления

- **Генерация конфигурации:** каждые 5 минут
- **Кеширование:** 1 минута (Nginx)
- **Rate limiting:** 10 запросов в минуту

## 📡 API для мониторинга

```bash
# Предварительный просмотр без генерации TOML
GET /config/preview

# Валидация конфигурации экспорта
GET /config/validate

# Статистика экспорта
GET /config/stats

# Пример TOML конфигурации
GET /config/sample

# Тестовая генерация с кастомными параметрами
POST /config/test-generation?min_score=0.5&top_count=3
```

## 🔧 Настройка в админ-панели

Управляемые параметры через веб-интерфейс:

### Категория "export"
- **MIN_SCORE_FOR_CONFIG** - минимальный скор для включения в конфигурацию (по умолчанию 0.7)
- **CONFIG_TOP_COUNT** - количество топ токенов (по умолчанию 3)

### Категория "scoring"
- **SCORING_MODEL** - активная модель скоринга
- **SCORING_WEIGHTS** - веса компонентов скоринга
- **EWMA_ALPHA** - параметр сглаживания

## 🤖 Интеграция с NotArb ботом

### Рекомендуемая частота запросов
- **Интервал:** 2-5 минут
- **Таймаут:** 30 секунд
- **Retry:** 3 попытки с экспоненциальной задержкой

### Пример кода интеграции

```python
import requests
import toml
import time

class ToTheMoon2Integration:
    def __init__(self, config_url: str):
        self.config_url = config_url
        self.last_config = None
        self.last_update = None
    
    def fetch_config(self) -> dict:
        """Получение актуальной конфигурации"""
        try:
            response = requests.get(self.config_url, timeout=30)
            response.raise_for_status()
            
            config = toml.loads(response.text)
            self.last_config = config
            self.last_update = time.time()
            
            return config
            
        except Exception as e:
            print(f"Error fetching ToTheMoon2 config: {e}")
            return self.last_config  # Возвращаем последнюю рабочую
    
    def get_active_tokens(self) -> list:
        """Получение списка активных токенов для торгов"""
        config = self.fetch_config()
        
        if not config or "tokens" not in config:
            return []
        
        return [
            {
                "address": token["address"],
                "score": token["score"],
                "pools": token["pools"]
            }
            for token in config["tokens"]
        ]

# Использование
integration = ToTheMoon2Integration("http://tothemoon.sh1z01d.ru/config/dynamic_strategy.toml")
active_tokens = integration.get_active_tokens()

for token in active_tokens:
    print(f"Token: {token['address'][:8]}... Score: {token['score']:.3f}")
    for dex, pools in token['pools'].items():
        print(f"  {dex}: {len(pools)} пулов")
```

## 🚨 Обработка ошибок

### Пустая конфигурация
Если нет токенов, отвечающих критериям, возвращается TOML с пустым массивом `tokens = []` и предупреждением.

### Недоступность сервиса
Бот должен использовать последнюю рабочую конфигурацию при недоступности ToTheMoon2.

### Валидация данных
Всегда проверяйте:
- Наличие секции `tokens`
- Валидность адресов токенов и пулов
- Актуальность временных меток

## 📈 Мониторинг интеграции

Через админ-панель ToTheMoon2 можно мониторить:
- Количество запросов к TOML endpoint
- Время последней генерации
- Количество экспортированных токенов
- Ошибки генерации

## 🔄 Lifecycle токенов в экспорте

Токены в экспорте могут:
- **Появляться** при достижении min_score_for_config
- **Исчезать** при падении скора или деактивации
- **Изменять порядок** при изменении скоров

NotArb бот должен адаптироваться к изменениям в реальном времени.
