# Kit API Client

Клиент для работы с Kit Vending API (api2.kit-invest.ru).

## Установка

```bash
pip install -e .
```

Или для установки в режиме разработки:

```bash
pip install -e ".[dev]"
```

## Использование

### Базовый пример

```python
import asyncio
from datetime import datetime, timedelta
from kit_api import KitVendingAPIClient

async def main():
    # Создаем клиент
    client = KitVendingAPIClient(
        login="your_login",
        password="your_password",
        company_id="your_company_id"
    )
    
    # Получаем список торговых автоматов
    machines = await client.get_vending_machines()
    print(f"Найдено автоматов: {len(machines.items)}")
    
    # Получаем список товаров
    products = await client.get_products()
    print(f"Найдено товаров: {len(products.items)}")
    
    # Получаем продажи за последние 7 дней
    to_date = datetime.now()
    from_date = to_date - timedelta(days=7)
    
    if machines.items:
        machine_id = machines.items[0].id
        sales = await client.get_sales(machine_id, from_date, to_date)
        print(f"Найдено продаж: {len(sales.items)}")
    
    # Получаем матрицы товаров
    matrices = await client.get_product_matrices()
    print(f"Найдено матриц: {len(matrices.items)}")

if __name__ == "__main__":
    asyncio.run(main())
```

### Использование с кастомным TimestampAPI

```python
from kit_api import KitVendingAPIClient
from kit_api.timestamp_api import TimestampAPI

# Создаем кастомный провайдер timestamp
custom_timestamp = TimestampAPI(
    base_url="https://your-timestamp-api.com/now"
)

client = KitVendingAPIClient(
    login="your_login",
    password="your_password",
    company_id="your_company_id",
    timestamp_provider=custom_timestamp
)
```

## API

### KitVendingAPIClient

Основной класс для работы с API.

#### Методы

- `get_sales(vending_machine_id, from_date, to_date)` - Получить продажи по торговому автомату
- `get_products()` - Получить список товаров
- `get_product_matrices()` - Получить матрицы товаров
- `get_vending_machines()` - Получить список торговых автоматов

### Модели

Все модели находятся в модуле `kit_api.models`:

- `ProductKitModel` - Модель товара
- `ProductsKitCollection` - Коллекция товаров
- `VendingMachineModel` - Модель торгового автомата
- `VendingMachinesCollection` - Коллекция торговых автоматов
- `SaleKitModel` - Модель продажи
- `SalesKitCollection` - Коллекция продаж
- `MatricesKitCollection` - Коллекция матриц
- `GoodsMatrixKitModel` - Модель матрицы товаров
- `RecipeMatrixKitModel` - Модель матрицы рецептов
- `ComboMatrixKitModel` - Модель комбо-матрицы

## Зависимости

- `aiohttp>=3.13.2` - Для асинхронных HTTP запросов
- `pydantic>=2.12.5` - Для валидации данных
- `requests>=2.32.5` - Для синхронных HTTP запросов
- `tzdata>=2025.3` - Для работы с часовыми поясами

## Лицензия

MIT

