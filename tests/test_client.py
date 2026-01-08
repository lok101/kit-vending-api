"""
Тесты для KitVendingAPIClient
"""

import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
from zoneinfo import ZoneInfo
from aiohttp import ClientResponse, ClientSession
from aiohttp.client_exceptions import ClientError

from kit_api.client import KitVendingAPIClient, ResultCodes
from kit_api.exceptions import (
    KitAPIValidationError,
    KitAPIResponseError,
    KitAPINetworkError,
    KitAPIError,
    KitAPIAuthError,
)


def create_mock_session_with_post(mock_response, post_side_effect=None):
    """Создать мок сессии с правильным асинхронным контекстным менеджером для post"""
    mock_session = MagicMock(spec=ClientSession)
    if post_side_effect:
        mock_session.post = MagicMock(side_effect=post_side_effect)
    else:
        mock_context_manager = AsyncMock()
        mock_context_manager.__aenter__ = AsyncMock(return_value=mock_response)
        mock_context_manager.__aexit__ = AsyncMock(return_value=None)
        mock_session.post = MagicMock(return_value=mock_context_manager)
    mock_session.closed = False
    return mock_session


class TestKitVendingAPIClientInit:
    """Тесты инициализации клиента"""

    def test_init_with_credentials(self, api_credentials):
        """Тест инициализации с переданными учетными данными"""
        client = KitVendingAPIClient(
            login=api_credentials["login"],
            password=api_credentials["password"],
            company_id=api_credentials["company_id"]
        )
        assert client._login == api_credentials["login"]
        assert client._password == api_credentials["password"]
        assert client._company_id == api_credentials["company_id"]

    def test_init_without_credentials(self):
        """Тест что инициализация без учетных данных не вызывает ошибку"""
        client = KitVendingAPIClient()
        assert client._login is None
        assert client._password is None
        assert client._company_id is None
        assert not client.is_authenticated()

    def test_init_with_session(self, api_credentials):
        """Тест инициализации с переданной сессией"""
        session = MagicMock(spec=ClientSession)
        client = KitVendingAPIClient(
            login=api_credentials["login"],
            password=api_credentials["password"],
            company_id=api_credentials["company_id"],
            session=session
        )
        assert client._session == session
        assert client._own_session is False

    def test_init_creates_own_session(self, api_credentials):
        """Тест что клиент создает свою сессию если не передана"""
        client = KitVendingAPIClient(
            login=api_credentials["login"],
            password=api_credentials["password"],
            company_id=api_credentials["company_id"]
        )
        assert client._session is None
        assert client._own_session is True


class TestAuthMethods:
    """Тесты методов авторизации"""

    def test_login(self):
        """Тест установки учётных данных"""
        client = KitVendingAPIClient()
        client.login("test_login", "test_password", "test_company_id")
        
        assert client._login == "test_login"
        assert client._password == "test_password"
        assert client._company_id == "test_company_id"
        assert client.is_authenticated()

    def test_login_empty_login_raises_error(self):
        """Тест что установка пустого login вызывает ошибку"""
        client = KitVendingAPIClient()
        with pytest.raises(KitAPIValidationError, match="login не может быть пустым"):
            client.login("", "password", "company_id")

    def test_login_empty_password_raises_error(self):
        """Тест что установка пустого password вызывает ошибку"""
        client = KitVendingAPIClient()
        with pytest.raises(KitAPIValidationError, match="password не может быть пустым"):
            client.login("login", "", "company_id")

    def test_login_empty_company_id_raises_error(self):
        """Тест что установка пустого company_id вызывает ошибку"""
        client = KitVendingAPIClient()
        with pytest.raises(KitAPIValidationError, match="company_id не может быть пустым"):
            client.login("login", "password", "")

    def test_logout(self, api_credentials):
        """Тест удаления учётных данных"""
        client = KitVendingAPIClient(
            login=api_credentials["login"],
            password=api_credentials["password"],
            company_id=api_credentials["company_id"]
        )
        assert client.is_authenticated()
        
        client.logout()
        
        assert client._login is None
        assert client._password is None
        assert client._company_id is None
        assert not client.is_authenticated()

    def test_is_authenticated(self):
        """Тест проверки статуса авторизации"""
        client = KitVendingAPIClient()
        assert not client.is_authenticated()
        
        client.login("login", "password", "company_id")
        assert client.is_authenticated()
        
        client.logout()
        assert not client.is_authenticated()


class TestBuildAuth:
    """Тесты построения объекта авторизации"""

    def test_build_auth(self, api_credentials):
        """Тест построения объекта авторизации"""
        client = KitVendingAPIClient(
            login=api_credentials["login"],
            password=api_credentials["password"],
            company_id=api_credentials["company_id"]
        )
        request_id = 1234567890
        auth = client._build_auth(request_id)

        assert auth["CompanyId"] == api_credentials["company_id"]
        assert auth["RequestId"] == request_id
        assert auth["UserLogin"] == api_credentials["login"]
        assert "Sign" in auth
        assert len(auth["Sign"]) == 32  # MD5 hash length

    def test_build_auth_without_credentials_raises_error(self):
        """Тест что построение объекта авторизации без учётных данных вызывает ошибку"""
        client = KitVendingAPIClient()
        request_id = 1234567890
        
        with pytest.raises(KitAPIAuthError, match="Учётные данные не установлены"):
            client._build_auth(request_id)


class TestGetSession:
    """Тесты получения HTTP сессии"""

    @pytest.mark.asyncio
    async def test_get_session_creates_new(self, api_credentials):
        """Тест создания новой сессии если её нет"""
        client = KitVendingAPIClient(
            login=api_credentials["login"],
            password=api_credentials["password"],
            company_id=api_credentials["company_id"]
        )
        session = await client._get_session()
        assert isinstance(session, ClientSession)
        assert client._own_session is True
        await client.close()

    @pytest.mark.asyncio
    async def test_get_session_reuses_existing(self, api_credentials):
        """Тест переиспользования существующей сессии"""
        session = MagicMock(spec=ClientSession)
        session.closed = False
        client = KitVendingAPIClient(
            login=api_credentials["login"],
            password=api_credentials["password"],
            company_id=api_credentials["company_id"],
            session=session
        )
        result = await client._get_session()
        assert result == session


class TestAsyncSendPostRequest:
    """Тесты отправки POST запросов"""

    @pytest.mark.asyncio
    async def test_successful_request(self, api_credentials, sample_api_response):
        """Тест успешного запроса"""
        client = KitVendingAPIClient(
            login=api_credentials["login"],
            password=api_credentials["password"],
            company_id=api_credentials["company_id"]
        )

        mock_response = MagicMock(spec=ClientResponse)
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=sample_api_response)
        mock_response.raise_for_status = MagicMock()

        mock_session = create_mock_session_with_post(mock_response)
        client._session = mock_session

        result = await client._async_send_post_request("http://test.com", {"test": "data"})

        assert result == sample_api_response
        mock_session.post.assert_called_once()
        await client.close()

    @pytest.mark.asyncio
    async def test_request_with_error_code(self, api_credentials):
        """Тест запроса с кодом ошибки"""
        client = KitVendingAPIClient(
            login=api_credentials["login"],
            password=api_credentials["password"],
            company_id=api_credentials["company_id"]
        )

        error_response = {
            "ResultCode": 1,
            "ErrorMessage": "Test error"
        }

        mock_response = MagicMock(spec=ClientResponse)
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=error_response)
        mock_response.raise_for_status = MagicMock()

        mock_session = create_mock_session_with_post(mock_response)
        client._session = mock_session

        with pytest.raises(KitAPIResponseError) as exc_info:
            await client._async_send_post_request("http://test.com", {"test": "data"})

        assert exc_info.value.result_code == 1
        await client.close()

    @pytest.mark.asyncio
    async def test_request_too_many_requests(self, api_credentials):
        """Тест обработки ошибки превышения лимита запросов"""
        client = KitVendingAPIClient(
            login=api_credentials["login"],
            password=api_credentials["password"],
            company_id=api_credentials["company_id"]
        )

        error_response = {
            "ResultCode": ResultCodes.TOO_MANY_REQUEST,
            "ErrorMessage": "Too many requests"
        }

        mock_response = MagicMock(spec=ClientResponse)
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=error_response)
        mock_response.raise_for_status = MagicMock()

        mock_session = create_mock_session_with_post(mock_response)
        client._session = mock_session

        with pytest.raises(KitAPIResponseError) as exc_info:
            await client._async_send_post_request("http://test.com", {"test": "data"})

        assert exc_info.value.result_code == ResultCodes.TOO_MANY_REQUEST
        await client.close()

    @pytest.mark.asyncio
    async def test_request_invalid_json(self, api_credentials):
        """Тест обработки невалидного JSON"""
        client = KitVendingAPIClient(
            login=api_credentials["login"],
            password=api_credentials["password"],
            company_id=api_credentials["company_id"]
        )

        mock_response = MagicMock(spec=ClientResponse)
        mock_response.status = 200
        mock_response.json = AsyncMock(side_effect=json.JSONDecodeError("Invalid JSON", "", 0))
        mock_response.raise_for_status = MagicMock()

        mock_session = create_mock_session_with_post(mock_response)
        client._session = mock_session

        with pytest.raises(KitAPIResponseError) as exc_info:
            await client._async_send_post_request("http://test.com", {"test": "data"})

        assert exc_info.value.result_code == -1
        await client.close()

    @pytest.mark.asyncio
    async def test_request_missing_result_code(self, api_credentials):
        """Тест обработки ответа без ResultCode"""
        client = KitVendingAPIClient(
            login=api_credentials["login"],
            password=api_credentials["password"],
            company_id=api_credentials["company_id"]
        )

        invalid_response = {"Data": []}

        mock_response = MagicMock(spec=ClientResponse)
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=invalid_response)
        mock_response.raise_for_status = MagicMock()

        mock_session = create_mock_session_with_post(mock_response)
        client._session = mock_session

        with pytest.raises(KitAPIResponseError) as exc_info:
            await client._async_send_post_request("http://test.com", {"test": "data"})

        assert exc_info.value.result_code == -1
        await client.close()

    @pytest.mark.asyncio
    async def test_request_network_error(self, api_credentials):
        """Тест обработки сетевой ошибки"""
        client = KitVendingAPIClient(
            login=api_credentials["login"],
            password=api_credentials["password"],
            company_id=api_credentials["company_id"]
        )

        # Исключение должно выбрасываться при вызове post(), а не при входе в контекстный менеджер
        mock_session = create_mock_session_with_post(
            None, 
            post_side_effect=ClientError("Network error")
        )
        client._session = mock_session

        with pytest.raises(KitAPINetworkError):
            await client._async_send_post_request("http://test.com", {"test": "data"})

        await client.close()


class TestAPIMethods:
    """Тесты методов API"""

    @pytest.mark.asyncio
    async def test_get_sales_without_auth_raises_error(self, mock_timestamp_provider):
        """Тест что запрос без учётных данных вызывает ошибку"""
        client = KitVendingAPIClient(timestamp_provider=mock_timestamp_provider)
        from_date = datetime(2024, 1, 1, tzinfo=ZoneInfo('Europe/Moscow'))
        to_date = datetime(2024, 1, 31, tzinfo=ZoneInfo('Europe/Moscow'))
        
        with pytest.raises(KitAPIAuthError, match="Учётные данные не установлены"):
            await client.get_sales(1, from_date, to_date)

    @pytest.mark.asyncio
    async def test_get_sales(self, api_credentials, mock_timestamp_provider):
        """Тест получения продаж"""
        client = KitVendingAPIClient(
            login=api_credentials["login"],
            password=api_credentials["password"],
            company_id=api_credentials["company_id"],
            timestamp_provider=mock_timestamp_provider
        )

        from_date = datetime(2024, 1, 1, tzinfo=ZoneInfo('Europe/Moscow'))
        to_date = datetime(2024, 1, 31, tzinfo=ZoneInfo('Europe/Moscow'))

        response_data = {
            "ResultCode": 0,
            "Sales": []
        }

        mock_response = MagicMock(spec=ClientResponse)
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=response_data)
        mock_response.raise_for_status = MagicMock()

        mock_session = create_mock_session_with_post(mock_response)
        client._session = mock_session

        result = await client.get_sales(1, from_date, to_date)

        assert result is not None
        mock_session.post.assert_called_once()
        await client.close()

    @pytest.mark.asyncio
    async def test_get_products_without_auth_raises_error(self, mock_timestamp_provider):
        """Тест что запрос без учётных данных вызывает ошибку"""
        client = KitVendingAPIClient(timestamp_provider=mock_timestamp_provider)
        
        with pytest.raises(KitAPIAuthError, match="Учётные данные не установлены"):
            await client.get_products()

    @pytest.mark.asyncio
    async def test_get_products(self, api_credentials, mock_timestamp_provider):
        """Тест получения товаров"""
        client = KitVendingAPIClient(
            login=api_credentials["login"],
            password=api_credentials["password"],
            company_id=api_credentials["company_id"],
            timestamp_provider=mock_timestamp_provider
        )

        response_data = {
            "ResultCode": 0,
            "Goods": []
        }

        mock_response = MagicMock(spec=ClientResponse)
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=response_data)
        mock_response.raise_for_status = MagicMock()

        mock_session = create_mock_session_with_post(mock_response)
        client._session = mock_session

        result = await client.get_products()

        assert result is not None
        await client.close()

    @pytest.mark.asyncio
    async def test_get_recipes_without_auth_raises_error(self, mock_timestamp_provider):
        """Тест что запрос без учётных данных вызывает ошибку"""
        client = KitVendingAPIClient(timestamp_provider=mock_timestamp_provider)
        
        with pytest.raises(KitAPIAuthError, match="Учётные данные не установлены"):
            await client.get_recipes()

    @pytest.mark.asyncio
    async def test_get_recipes(self, api_credentials, mock_timestamp_provider):
        """Тест получения рецептов"""
        client = KitVendingAPIClient(
            login=api_credentials["login"],
            password=api_credentials["password"],
            company_id=api_credentials["company_id"],
            timestamp_provider=mock_timestamp_provider
        )

        response_data = {
            "ResultCode": 0,
            "Formulations": []
        }

        mock_response = MagicMock(spec=ClientResponse)
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=response_data)
        mock_response.raise_for_status = MagicMock()

        mock_session = create_mock_session_with_post(mock_response)
        client._session = mock_session

        result = await client.get_recipes()

        assert result is not None
        await client.close()

    @pytest.mark.asyncio
    async def test_get_product_matrices_without_auth_raises_error(self, mock_timestamp_provider):
        """Тест что запрос без учётных данных вызывает ошибку"""
        client = KitVendingAPIClient(timestamp_provider=mock_timestamp_provider)
        
        with pytest.raises(KitAPIAuthError, match="Учётные данные не установлены"):
            await client.get_product_matrices()

    @pytest.mark.asyncio
    async def test_get_product_matrices(self, api_credentials, mock_timestamp_provider):
        """Тест получения матриц товаров"""
        client = KitVendingAPIClient(
            login=api_credentials["login"],
            password=api_credentials["password"],
            company_id=api_credentials["company_id"],
            timestamp_provider=mock_timestamp_provider
        )

        response_data = {
            "ResultCode": 0,
            "GoodsMatrices": []
        }

        mock_response = MagicMock(spec=ClientResponse)
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=response_data)
        mock_response.raise_for_status = MagicMock()

        mock_session = create_mock_session_with_post(mock_response)
        client._session = mock_session

        result = await client.get_product_matrices()

        assert result is not None
        await client.close()

    @pytest.mark.asyncio
    async def test_get_vending_machines_without_auth_raises_error(self, mock_timestamp_provider):
        """Тест что запрос без учётных данных вызывает ошибку"""
        client = KitVendingAPIClient(timestamp_provider=mock_timestamp_provider)
        
        with pytest.raises(KitAPIAuthError, match="Учётные данные не установлены"):
            await client.get_vending_machines()

    @pytest.mark.asyncio
    async def test_get_vending_machines(self, api_credentials, mock_timestamp_provider):
        """Тест получения торговых автоматов"""
        client = KitVendingAPIClient(
            login=api_credentials["login"],
            password=api_credentials["password"],
            company_id=api_credentials["company_id"],
            timestamp_provider=mock_timestamp_provider
        )

        response_data = {
            "ResultCode": 0,
            "VendingMachines": []
        }

        mock_response = MagicMock(spec=ClientResponse)
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=response_data)
        mock_response.raise_for_status = MagicMock()

        mock_session = create_mock_session_with_post(mock_response)
        client._session = mock_session

        result = await client.get_vending_machines()

        assert result is not None
        await client.close()


class TestContextManager:
    """Тесты контекстного менеджера"""

    @pytest.mark.asyncio
    async def test_context_manager(self, api_credentials):
        """Тест использования клиента как контекстного менеджера"""
        async with KitVendingAPIClient(
            login=api_credentials["login"],
            password=api_credentials["password"],
            company_id=api_credentials["company_id"]
        ) as client:
            assert client is not None
            # Сессия должна быть закрыта после выхода из контекста

    @pytest.mark.asyncio
    async def test_close(self, api_credentials):
        """Тест закрытия сессии"""
        client = KitVendingAPIClient(
            login=api_credentials["login"],
            password=api_credentials["password"],
            company_id=api_credentials["company_id"]
        )
        # Создаем сессию
        await client._get_session()
        # Закрываем
        await client.close()
        # Проверяем что сессия закрыта
        assert client._session is None or client._session.closed

