# Сводка по пакету Kit API

## Структура пакета

```
kit_api_package/
├── kit_api/                    # Основной пакет
│   ├── __init__.py            # Экспорт основных классов и моделей
│   ├── client.py              # KitVendingAPIClient - основной клиент API
│   ├── timestamp_api.py       # TimestampAPI - провайдер timestamp
│   ├── project_time.py        # ProjectTime - утилиты для работы с датами
│   ├── rate_limiter.py        # RateLimiter - ограничитель запросов
│   └── models/                 # Модели данных
│       ├── __init__.py
│       ├── matrices.py        # Модели матриц товаров
│       ├── products.py        # Модели товаров
│       ├── sales.py           # Модели продаж
│       └── vending_machine.py # Модели торговых автоматов
├── pyproject.toml             # Конфигурация пакета
├── README.md                  # Документация
├── INSTALL.md                 # Инструкция по установке
└── SUMMARY.md                 # Этот файл
```

## Включенные компоненты

### Основные файлы Kit API:
- ✅ `kit_vending_api_client.py` → `kit_api/client.py`
- ✅ Все модели из `models/` (matrices, products, sales, vending_machine)
- ✅ `timestamp_api.py` → `kit_api/timestamp_api.py`
- ✅ `project_time.py` → `kit_api/project_time.py`
- ✅ `rate_limiter.py` → `kit_api/rate_limiter.py`

### Исключенные компоненты (не относятся к Kit API):
- ❌ Модели MS API (ProductMSModel, ProductStocksMSModel и т.д.)
- ❌ Доменные модели (domain/)
- ❌ Репозитории и use cases
- ❌ Контроллеры и мапперы

## Установка

```bash
cd kit_api_package
pip install -e .
```

## Использование

```python
from kit_api import KitVendingAPIClient

client = KitVendingAPIClient(
    login="your_login",
    password="your_password",
    company_id="your_company_id"
)

# Использование API
machines = await client.get_vending_machines()
products = await client.get_products()
sales = await client.get_sales(machine_id, from_date, to_date)
matrices = await client.get_product_matrices()
```

## Зависимости

- `aiohttp>=3.13.2`
- `pydantic>=2.12.5`
- `requests>=2.32.5`
- `tzdata>=2025.3`

