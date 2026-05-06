"""
Общие фикстуры для тестов
"""

import os

# До импорта kit_api: иначе kit_api.client зафиксирует rate_limit (1 req / 10s) и тесты зависают.
os.environ.setdefault("KIT_API_REQUEST_PER_WINDOW", "100")
os.environ.setdefault("KIT_API_WINDOW_SECONDS", "1")

import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime
from zoneinfo import ZoneInfo

from kit_api.timestamp_api import TimestampAPI


@pytest.fixture
def mock_timestamp_provider():
    """Мок провайдера timestamp"""
    provider = MagicMock(spec=TimestampAPI)
    provider.async_get_now = AsyncMock(return_value=1234567890)
    return provider


@pytest.fixture
def sample_datetime():
    """Пример datetime для тестов"""
    return datetime(2024, 1, 15, 12, 30, 45, tzinfo=ZoneInfo('Europe/Moscow'))


@pytest.fixture
def sample_api_response():
    """Пример успешного ответа от API"""
    return {
        "ResultCode": 0,
        "ErrorMessage": None,
        "Data": []
    }


@pytest.fixture
def api_credentials():
    """Учетные данные для API"""
    return {
        "login": "test_login",
        "password": "test_password",
        "company_id": "test_company_id"
    }

