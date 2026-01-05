"""
Тесты для TimestampAPI
"""

import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch
from aiohttp import ClientResponse, ClientError as AioHTTPClientError
from requests.exceptions import RequestException

from kit_api.timestamp_api import TimestampAPI
from kit_api.exceptions import KitAPINetworkError, KitAPIError


def create_mock_session_with_get(mock_response=None, get_side_effect=None):
    """Создать мок сессии с правильным асинхронным контекстным менеджером для get"""
    mock_session = MagicMock()
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)
    
    if get_side_effect:
        mock_session.get = MagicMock(side_effect=get_side_effect)
    else:
        mock_context_manager = AsyncMock()
        mock_context_manager.__aenter__ = AsyncMock(return_value=mock_response)
        mock_context_manager.__aexit__ = AsyncMock(return_value=None)
        mock_session.get = MagicMock(return_value=mock_context_manager)
    
    return mock_session


class TestTimestampAPIInit:
    """Тесты инициализации TimestampAPI"""

    def test_init_with_default_url(self):
        """Тест инициализации с URL по умолчанию"""
        api = TimestampAPI()
        assert api._base_url is not None
        assert "sberdevices.ru" in api._base_url

    def test_init_with_custom_url(self):
        """Тест инициализации с кастомным URL"""
        custom_url = "https://example.com/api/timestamp"
        api = TimestampAPI(base_url=custom_url)
        assert api._base_url == custom_url


class TestAsyncGetNow:
    """Тесты асинхронного метода async_get_now"""

    @pytest.mark.asyncio
    async def test_async_get_now_success(self):
        """Тест успешного получения timestamp"""
        api = TimestampAPI(base_url="https://example.com/api/timestamp")

        mock_response = MagicMock(spec=ClientResponse)
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={"timestamp": 1234567890})
        mock_response.raise_for_status = MagicMock()

        with patch("aiohttp.ClientSession") as mock_session_class:
            mock_session = create_mock_session_with_get(mock_response)
            mock_session_class.return_value = mock_session

            result = await api.async_get_now()

            assert result == 1234567890

    @pytest.mark.asyncio
    async def test_async_get_now_invalid_json(self):
        """Тест обработки невалидного JSON"""
        api = TimestampAPI(base_url="https://example.com/api/timestamp")

        mock_response = MagicMock(spec=ClientResponse)
        mock_response.status = 200
        mock_response.json = AsyncMock(side_effect=json.JSONDecodeError("Invalid JSON", "", 0))
        mock_response.raise_for_status = MagicMock()

        with patch("aiohttp.ClientSession") as mock_session_class:
            mock_session = create_mock_session_with_get(mock_response)
            mock_session_class.return_value = mock_session

            with pytest.raises(KitAPIError, match="Не удалось разобрать JSON"):
                await api.async_get_now()

    @pytest.mark.asyncio
    async def test_async_get_now_missing_timestamp(self):
        """Тест обработки ответа без поля timestamp"""
        api = TimestampAPI(base_url="https://example.com/api/timestamp")

        mock_response = MagicMock(spec=ClientResponse)
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={"data": "some data"})
        mock_response.raise_for_status = MagicMock()

        with patch("aiohttp.ClientSession") as mock_session_class:
            mock_session = create_mock_session_with_get(mock_response)
            mock_session_class.return_value = mock_session

            with pytest.raises(KitAPIError, match="не содержит поле 'timestamp'"):
                await api.async_get_now()

    @pytest.mark.asyncio
    async def test_async_get_now_network_error(self):
        """Тест обработки сетевой ошибки"""
        api = TimestampAPI(base_url="https://example.com/api/timestamp")

        with patch("aiohttp.ClientSession") as mock_session_class:
            mock_session = create_mock_session_with_get(get_side_effect=AioHTTPClientError("Network error"))
            mock_session_class.return_value = mock_session

            with pytest.raises(KitAPINetworkError, match="Ошибка сети"):
                await api.async_get_now()


class TestGetNow:
    """Тесты синхронного метода get_now"""

    def test_get_now_success(self):
        """Тест успешного получения timestamp"""
        api = TimestampAPI(base_url="https://example.com/api/timestamp")

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json = MagicMock(return_value={"timestamp": 1234567890})
        mock_response.raise_for_status = MagicMock()

        with patch("requests.get", return_value=mock_response):
            result = api.get_now()

            assert result == 1234567890

    def test_get_now_invalid_json(self):
        """Тест обработки невалидного JSON"""
        api = TimestampAPI(base_url="https://example.com/api/timestamp")

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json = MagicMock(side_effect=json.JSONDecodeError("Invalid JSON", "", 0))
        mock_response.raise_for_status = MagicMock()

        with patch("requests.get", return_value=mock_response):
            with pytest.raises(KitAPIError, match="Не удалось разобрать JSON"):
                api.get_now()

    def test_get_now_missing_timestamp(self):
        """Тест обработки ответа без поля timestamp"""
        api = TimestampAPI(base_url="https://example.com/api/timestamp")

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json = MagicMock(return_value={"data": "some data"})
        mock_response.raise_for_status = MagicMock()

        with patch("requests.get", return_value=mock_response):
            with pytest.raises(KitAPIError, match="не содержит поле 'timestamp'"):
                api.get_now()

    def test_get_now_network_error(self):
        """Тест обработки сетевой ошибки"""
        api = TimestampAPI(base_url="https://example.com/api/timestamp")

        with patch("requests.get", side_effect=RequestException("Network error")):
            with pytest.raises(KitAPINetworkError, match="Ошибка сети"):
                api.get_now()

