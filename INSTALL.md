# Инструкция по установке пакета Kit API

## Установка из локальной директории

1. Перейдите в директорию пакета:
```bash
cd kit_api_package
```

2. Установите пакет в режиме разработки:
```bash
pip install -e .
```

Или установите в обычном режиме:
```bash
pip install .
```

## Установка в другом проекте

### Вариант 1: Прямая установка из директории

```bash
pip install /path/to/kit_api_package
```

### Вариант 2: Установка из архива

1. Создайте архив пакета:
```bash
cd kit_api_package
python -m build
```

2. Установите из архива:
```bash
pip install dist/kit-api-0.1.0-py3-none-any.whl
```

### Вариант 3: Установка из Git (если пакет в репозитории)

```bash
pip install git+https://github.com/yourusername/kit-api.git
```

## Проверка установки

После установки проверьте, что пакет доступен:

```python
import kit_api
print(kit_api.__version__)

from kit_api import KitVendingAPIClient
print("Пакет установлен успешно!")
```

## Использование

См. файл `README.md` для примеров использования.

