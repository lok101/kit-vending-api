"""
Тесты для KitVendingAPIClient
"""

import pytest
import json
import logging
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
from zoneinfo import ZoneInfo
from aiohttp import ClientResponse, ClientSession
from aiohttp.client_exceptions import ClientError

from kit_api.client import KitVendingAPIClient, KitAPIAccount
from kit_api.enums import ResultCode
from kit_api.exceptions import (
    KitAPIResponseError,
    KitAPINetworkError,
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


def make_post_async_cm(mock_response):
    """Один вызов session.post() — контекстный менеджер с данным mock_response."""
    mock_context_manager = MagicMock()
    mock_context_manager.__aenter__ = AsyncMock(return_value=mock_response)
    mock_context_manager.__aexit__ = AsyncMock(return_value=None)
    return mock_context_manager


def mock_json_response(json_data):
    mock_response = MagicMock(spec=ClientResponse)
    mock_response.status = 200
    mock_response.json = AsyncMock(return_value=json_data)
    mock_response.raise_for_status = MagicMock()
    return mock_response


class TestKitVendingAPIClientInit:
    """Тесты инициализации клиента"""

    def test_init_with_credentials(self, api_account, api_credentials):
        """Тест инициализации с переданным аккаунтом"""
        client = KitVendingAPIClient(account=api_account)
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

    def test_init_with_session(self, api_account):
        """Тест инициализации с переданной сессией"""
        session = MagicMock(spec=ClientSession)
        client = KitVendingAPIClient(account=api_account, session=session)
        assert client._session == session
        assert client._own_session is False

    def test_init_creates_own_session(self, api_account):
        """Тест что клиент создает свою сессию если не передана"""
        client = KitVendingAPIClient(account=api_account)
        assert client._session is None
        assert client._own_session is True


class TestBuildAuth:
    """Тесты построения объекта авторизации"""

    def test_build_auth(self, api_account, api_credentials):
        """Тест построения объекта авторизации"""
        client = KitVendingAPIClient(account=api_account)
        request_id = 1234567890
        auth = client._build_auth(request_id, None)

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
            client._build_auth(request_id, None)


class TestGetSession:
    """Тесты получения HTTP сессии"""

    @pytest.mark.asyncio
    async def test_get_session_creates_new(self, api_account):
        """Тест создания новой сессии если её нет"""
        client = KitVendingAPIClient(account=api_account)
        session = await client._get_session()
        assert isinstance(session, ClientSession)
        assert client._own_session is True
        await client.close()

    @pytest.mark.asyncio
    async def test_get_session_reuses_existing(self, api_account):
        """Тест переиспользования существующей сессии"""
        session = MagicMock(spec=ClientSession)
        session.closed = False
        client = KitVendingAPIClient(account=api_account, session=session)
        result = await client._get_session()
        assert result == session


class TestAsyncSendPostRequest:
    """Тесты отправки POST запросов"""

    @pytest.mark.asyncio
    async def test_successful_request(self, api_account, sample_api_response):
        """Тест успешного запроса"""
        client = KitVendingAPIClient(account=api_account)

        mock_response = MagicMock(spec=ClientResponse)
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=sample_api_response)
        mock_response.raise_for_status = MagicMock()

        mock_session = create_mock_session_with_post(mock_response)
        client._session = mock_session

        async def build_data():
            return {"test": "data"}

        result = await client._async_send_post_request("http://test.com", build_data)

        assert result == sample_api_response
        mock_session.post.assert_called_once()
        await client.close()

    @pytest.mark.asyncio
    async def test_request_with_error_code(self, api_account):
        """Тест запроса с кодом ошибки"""
        client = KitVendingAPIClient(account=api_account)

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

        async def build_data():
            return {"test": "data"}

        with pytest.raises(KitAPIResponseError) as exc_info:
            await client._async_send_post_request("http://test.com", build_data)

        assert exc_info.value.result_code == 1
        await client.close()

    @pytest.mark.asyncio
    async def test_request_too_many_requests(self, api_account):
        """Тест обработки ошибки превышения лимита запросов"""
        client = KitVendingAPIClient(account=api_account)

        error_response = {
            "ResultCode": ResultCode.TOO_MANY_REQUEST,
            "ErrorMessage": "Too many requests"
        }

        mock_response = MagicMock(spec=ClientResponse)
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=error_response)
        mock_response.raise_for_status = MagicMock()

        mock_session = create_mock_session_with_post(mock_response)
        client._session = mock_session

        async def build_data():
            return {"test": "data"}

        with pytest.raises(KitAPIResponseError) as exc_info:
            await client._async_send_post_request("http://test.com", build_data)

        assert exc_info.value.result_code == ResultCode.TOO_MANY_REQUEST
        await client.close()

    @pytest.mark.asyncio
    async def test_request_invalid_json(self, api_account):
        """Тест обработки невалидного JSON"""
        client = KitVendingAPIClient(account=api_account)

        mock_response = MagicMock(spec=ClientResponse)
        mock_response.status = 200
        mock_response.json = AsyncMock(side_effect=json.JSONDecodeError("Invalid JSON", "", 0))
        mock_response.raise_for_status = MagicMock()

        mock_session = create_mock_session_with_post(mock_response)
        client._session = mock_session

        async def build_data():
            return {"test": "data"}

        with pytest.raises(KitAPIResponseError) as exc_info:
            await client._async_send_post_request("http://test.com", build_data)

        assert exc_info.value.result_code == -1
        await client.close()

    @pytest.mark.asyncio
    async def test_request_missing_result_code(self, api_account):
        """Тест обработки ответа без ResultCode"""
        client = KitVendingAPIClient(account=api_account)

        invalid_response = {"Data": []}

        mock_response = MagicMock(spec=ClientResponse)
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=invalid_response)
        mock_response.raise_for_status = MagicMock()

        mock_session = create_mock_session_with_post(mock_response)
        client._session = mock_session

        async def build_data():
            return {"test": "data"}

        with pytest.raises(KitAPIResponseError) as exc_info:
            await client._async_send_post_request("http://test.com", build_data)

        assert exc_info.value.result_code == -1
        await client.close()

    @pytest.mark.asyncio
    async def test_request_network_error(self, api_account):
        """Тест обработки сетевой ошибки"""
        client = KitVendingAPIClient(account=api_account)

        # Исключение должно выбрасываться при вызове post(), а не при входе в контекстный менеджер
        mock_session = create_mock_session_with_post(
            None, 
            post_side_effect=ClientError("Network error")
        )
        client._session = mock_session

        async def build_data():
            return {"test": "data"}

        with pytest.raises(KitAPINetworkError):
            await client._async_send_post_request("http://test.com", build_data)

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
            await client.get_sales(from_date, to_date)

    @pytest.mark.asyncio
    async def test_get_sales(self, api_account, mock_timestamp_provider):
        """Тест получения продаж"""
        client = KitVendingAPIClient(
            account=api_account,
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

        result = await client.get_sales(from_date, to_date)

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
    async def test_get_products(self, api_account, mock_timestamp_provider):
        """Тест получения товаров"""
        client = KitVendingAPIClient(
            account=api_account,
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
    async def test_get_recipes(self, api_account, mock_timestamp_provider):
        """Тест получения рецептов"""
        client = KitVendingAPIClient(
            account=api_account,
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
    async def test_get_product_matrices(self, api_account, mock_timestamp_provider):
        """Тест получения матриц товаров"""
        client = KitVendingAPIClient(
            account=api_account,
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
    async def test_get_vending_machines(self, api_account, mock_timestamp_provider):
        """Тест получения торговых автоматов"""
        client = KitVendingAPIClient(
            account=api_account,
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


class TestGetSalesResolved:
    """Тесты get_sales_resolved."""

    @pytest.mark.asyncio
    async def test_resolves_code_from_goods_matrix(self, mock_timestamp_provider):
        """Плейсхолдер «Товар N» + товарная матрица — код из GoodsName ячейки."""
        account = KitAPIAccount(login="u", password="p", company_id=1)
        client = KitVendingAPIClient(account=account, timestamp_provider=mock_timestamp_provider)

        from_date = datetime(2024, 1, 1, tzinfo=ZoneInfo("Asia/Yekaterinburg"))
        to_date = datetime(2024, 1, 31, tzinfo=ZoneInfo("Asia/Yekaterinburg"))

        sales_json = {
            "ResultCode": 0,
            "Sales": [
                {
                    "LineNumber": 3,
                    "Sum": 55.5,
                    "DateTime": "01.01.2024 12:00:00",
                    "GoodsName": "Товар 3",
                    "VendingMachine": 1,
                    "VendingMachineName": "VM [001]",
                    "MatrixId": 100,
                }
            ],
        }
        matrices_json = {
            "ResultCode": 0,
            "GoodsMatrices": [
                {
                    "MatrixId": 100,
                    "MatrixName": "Snack",
                    "MatrixType": 1,
                    "Details": [
                        {
                            "LineNumber": 3,
                            "Price2": 55.5,
                            "GoodsName": "77|Snack bar",
                            "MaxCount": 10,
                        }
                    ],
                }
            ],
        }

        mock_session = create_mock_session_with_post(
            None,
            post_side_effect=[
                make_post_async_cm(mock_json_response(sales_json)),
                make_post_async_cm(mock_json_response(matrices_json)),
            ],
        )
        client._session = mock_session

        result = await client.get_sales_resolved(from_date, to_date)

        assert len(result) == 1
        assert result[0].price == 55.5
        assert result[0].product_code == "77"
        assert mock_session.post.call_count == 2
        await client.close()

    @pytest.mark.asyncio
    async def test_resolves_code_from_recipe_matrix(self, mock_timestamp_provider):
        """Плейсхолдер + рецептурная матрица — код из формуляции."""
        account = KitAPIAccount(login="u", password="p", company_id=1)
        client = KitVendingAPIClient(account=account, timestamp_provider=mock_timestamp_provider)

        from_date = datetime(2024, 1, 1, tzinfo=ZoneInfo("Asia/Yekaterinburg"))
        to_date = datetime(2024, 1, 31, tzinfo=ZoneInfo("Asia/Yekaterinburg"))

        sales_json = {
            "ResultCode": 0,
            "Sales": [
                {
                    "LineNumber": 3,
                    "Sum": 99.0,
                    "DateTime": "01.01.2024 12:00:00",
                    "GoodsName": "Товар 3",
                    "VendingMachine": 2,
                    "VendingMachineName": "VM [001]",
                    "MatrixId": 7,
                }
            ],
        }
        matrices_json = {
            "ResultCode": 0,
            "GoodsMatrices": [
                {
                    "MatrixId": 7,
                    "MatrixName": "Matrix R",
                    "MatrixType": 2,
                    "Details": [
                        {"LineNumber": 3, "Price2": 99.0, "FormulationId": 100},
                    ],
                }
            ],
        }
        formulations_json = {
            "ResultCode": 0,
            "Formulations": [
                {"FormulationId": 100, "FormulationName": "42|Recipe Title"},
            ],
        }

        mock_session = create_mock_session_with_post(
            None,
            post_side_effect=[
                make_post_async_cm(mock_json_response(sales_json)),
                make_post_async_cm(mock_json_response(matrices_json)),
                make_post_async_cm(mock_json_response(formulations_json)),
            ],
        )
        client._session = mock_session

        result = await client.get_sales_resolved(from_date, to_date)

        assert len(result) == 1
        assert result[0].product_code == "42"
        assert mock_session.post.call_count == 3
        await client.close()

    @pytest.mark.asyncio
    async def test_non_placeholder_does_not_fetch_matrices(
        self, mock_timestamp_provider, caplog
    ):
        """Без плейсхолдера и без кода в названии — только GetSales, без GetGoodsMatrices."""
        account = KitAPIAccount(login="u", password="p", company_id=1)
        client = KitVendingAPIClient(account=account, timestamp_provider=mock_timestamp_provider)

        from_date = datetime(2024, 1, 1, tzinfo=ZoneInfo("Asia/Yekaterinburg"))
        to_date = datetime(2024, 1, 31, tzinfo=ZoneInfo("Asia/Yekaterinburg"))

        sales_json = {
            "ResultCode": 0,
            "Sales": [
                {
                    "LineNumber": 1,
                    "Sum": 10.0,
                    "DateTime": "01.01.2024 12:00:00",
                    "GoodsName": "Без кода в названии",
                    "VendingMachine": 1,
                    "VendingMachineName": "VM [001]",
                    "MatrixId": 50,
                }
            ],
        }

        mock_session = create_mock_session_with_post(
            None,
            post_side_effect=[
                make_post_async_cm(mock_json_response(sales_json)),
            ],
        )
        client._session = mock_session

        with caplog.at_level(logging.DEBUG, logger="kit_api.client"):
            result = await client.get_sales_resolved(from_date, to_date)

        assert len(result) == 0
        assert mock_session.post.call_count == 1
        assert "Не удалось определить код товара для продажи" in caplog.text
        await client.close()

    @pytest.mark.asyncio
    async def test_product_zero_skips_debug_no_matrices(
        self, mock_timestamp_provider, caplog
    ):
        """Плейсхолдер «Товар 0» — некритично, матрицы не запрашиваются."""
        account = KitAPIAccount(login="u", password="p", company_id=1)
        client = KitVendingAPIClient(account=account, timestamp_provider=mock_timestamp_provider)

        from_date = datetime(2024, 1, 1, tzinfo=ZoneInfo("Asia/Yekaterinburg"))
        to_date = datetime(2024, 1, 31, tzinfo=ZoneInfo("Asia/Yekaterinburg"))

        sales_json = {
            "ResultCode": 0,
            "Sales": [
                {
                    "LineNumber": 1,
                    "Sum": 10.0,
                    "DateTime": "01.01.2024 12:00:00",
                    "GoodsName": "Товар 0",
                    "VendingMachine": 1,
                    "VendingMachineName": "VM [100]",
                    "MatrixId": 50,
                }
            ],
        }

        mock_session = create_mock_session_with_post(
            None,
            post_side_effect=[
                make_post_async_cm(mock_json_response(sales_json)),
            ],
        )
        client._session = mock_session

        with caplog.at_level(logging.DEBUG, logger="kit_api.client"):
            result = await client.get_sales_resolved(from_date, to_date)

        assert result == []
        assert mock_session.post.call_count == 1
        assert "Товар 0" in caplog.text
        assert "Пропуск продажи без кода товара" in caplog.text
        await client.close()

    @pytest.mark.asyncio
    async def test_missing_cell_logs_warning(self, mock_timestamp_provider, caplog):
        """Нет строки в матрице — предупреждение в логе."""
        account = KitAPIAccount(login="u", password="p", company_id=1)
        client = KitVendingAPIClient(account=account, timestamp_provider=mock_timestamp_provider)

        from_date = datetime(2024, 1, 1, tzinfo=ZoneInfo("Asia/Yekaterinburg"))
        to_date = datetime(2024, 1, 31, tzinfo=ZoneInfo("Asia/Yekaterinburg"))

        sales_json = {
            "ResultCode": 0,
            "Sales": [
                {
                    "LineNumber": 9,
                    "Sum": 1.0,
                    "DateTime": "01.01.2024 12:00:00",
                    "GoodsName": "Товар 9",
                    "VendingMachine": 1,
                    "VendingMachineName": "VM [001]",
                    "MatrixId": 1,
                }
            ],
        }
        matrices_json = {
            "ResultCode": 0,
            "GoodsMatrices": [
                {
                    "MatrixId": 1,
                    "MatrixName": "M",
                    "MatrixType": 1,
                    "Details": [
                        {"LineNumber": 1, "Price2": 1.0, "GoodsName": "1|A", "MaxCount": 1},
                    ],
                }
            ],
        }

        mock_session = create_mock_session_with_post(
            None,
            post_side_effect=[
                make_post_async_cm(mock_json_response(sales_json)),
                make_post_async_cm(mock_json_response(matrices_json)),
            ],
        )
        client._session = mock_session

        with caplog.at_level(logging.WARNING, logger="kit_api.client"):
            result = await client.get_sales_resolved(from_date, to_date)

        assert result == []
        assert "Не удалось определить код товара" in caplog.text
        assert "ячейка" in caplog.text
        await client.close()


class TestRecipeMatricesWithCodes:
    """Тесты get_recipe_matrices_with_codes"""

    @pytest.mark.asyncio
    async def test_without_auth_raises_error(self, mock_timestamp_provider):
        """Запрос без учётных данных вызывает ошибку"""
        client = KitVendingAPIClient(timestamp_provider=mock_timestamp_provider)

        with pytest.raises(KitAPIAuthError, match="Учётные данные не установлены"):
            await client.get_recipe_matrices_with_codes()

    @pytest.mark.asyncio
    async def test_resolves_recipe_code_from_formulations(self, mock_timestamp_provider):
        """Рецептурная матрица обогащается recipe_code по FormulationId"""
        account = KitAPIAccount(login="u", password="p", company_id=1)
        client = KitVendingAPIClient(account=account, timestamp_provider=mock_timestamp_provider)

        formulations_json = {
            "ResultCode": 0,
            "Formulations": [
                {"FormulationId": 100, "FormulationName": "42|Recipe Title"},
            ],
        }
        matrices_json = {
            "ResultCode": 0,
            "GoodsMatrices": [
                {
                    "MatrixId": 7,
                    "MatrixName": "Matrix R",
                    "MatrixType": 2,
                    "Details": [
                        {"LineNumber": 3, "Price2": 99.5, "FormulationId": 100},
                    ],
                }
            ],
        }

        mock_session = create_mock_session_with_post(
            None,
            post_side_effect=[
                make_post_async_cm(mock_json_response(formulations_json)),
                make_post_async_cm(mock_json_response(matrices_json)),
            ],
        )
        client._session = mock_session

        result = await client.get_recipe_matrices_with_codes()

        assert len(result) == 1
        assert result[0].id == 7
        assert result[0].name == "Matrix R"
        assert result[0].type == 2
        assert len(result[0].cells) == 1
        cell = result[0].cells[0]
        assert cell.line_number == 3
        assert cell.price == 99.5
        assert cell.recipe_id == 100
        assert cell.recipe_code == "42"

        assert mock_session.post.call_count == 2
        await client.close()

    @pytest.mark.asyncio
    async def test_missing_formulation_yields_none_code(self, mock_timestamp_provider):
        """Если формуляции нет в списке — recipe_code None, recipe_id сохраняется"""
        account = KitAPIAccount(login="u", password="p", company_id=1)
        client = KitVendingAPIClient(account=account, timestamp_provider=mock_timestamp_provider)

        formulations_json = {"ResultCode": 0, "Formulations": []}
        matrices_json = {
            "ResultCode": 0,
            "GoodsMatrices": [
                {
                    "MatrixId": 1,
                    "MatrixName": "M",
                    "MatrixType": 2,
                    "Details": [
                        {"LineNumber": 1, "Price2": 10.0, "FormulationId": 999},
                    ],
                }
            ],
        }

        mock_session = create_mock_session_with_post(
            None,
            post_side_effect=[
                make_post_async_cm(mock_json_response(formulations_json)),
                make_post_async_cm(mock_json_response(matrices_json)),
            ],
        )
        client._session = mock_session

        result = await client.get_recipe_matrices_with_codes()

        assert len(result) == 1
        assert result[0].cells[0].recipe_id == 999
        assert result[0].cells[0].recipe_code is None
        await client.close()


def _post_urls_from_session(mock_session) -> list[str]:
    urls: list[str] = []
    for call in mock_session.post.call_args_list:
        if "url" in call.kwargs:
            urls.append(call.kwargs["url"])
        elif call.args:
            urls.append(call.args[0])
        else:
            urls.append("")
    return urls


def _count_posts_containing(mock_session, substring: str) -> int:
    return sum(1 for url in _post_urls_from_session(mock_session) if substring in url)


class TestMatricesRecipesCache:
    """Кэш GetGoodsMatrices / GetFormulations по (company_id, login)."""

    @pytest.mark.asyncio
    async def test_second_get_sales_resolved_reuses_cached_matrices(self, mock_timestamp_provider):
        """Два вызова get_sales_resolved с одним аккаунтом — GetGoodsMatrices один раз."""
        account = KitAPIAccount(login="u", password="p", company_id=1)
        client = KitVendingAPIClient(account=account, timestamp_provider=mock_timestamp_provider)

        from_date = datetime(2024, 1, 1, tzinfo=ZoneInfo("Asia/Yekaterinburg"))
        to_date = datetime(2024, 1, 31, tzinfo=ZoneInfo("Asia/Yekaterinburg"))

        sales_json = {
            "ResultCode": 0,
            "Sales": [
                {
                    "LineNumber": 3,
                    "Sum": 55.5,
                    "DateTime": "01.01.2024 12:00:00",
                    "GoodsName": "Товар 3",
                    "VendingMachine": 1,
                    "VendingMachineName": "VM [001]",
                    "MatrixId": 100,
                }
            ],
        }
        matrices_json = {
            "ResultCode": 0,
            "GoodsMatrices": [
                {
                    "MatrixId": 100,
                    "MatrixName": "Snack",
                    "MatrixType": 1,
                    "Details": [
                        {
                            "LineNumber": 3,
                            "Price2": 55.5,
                            "GoodsName": "77|Snack bar",
                            "MaxCount": 10,
                        }
                    ],
                }
            ],
        }

        mock_session = create_mock_session_with_post(
            None,
            post_side_effect=[
                make_post_async_cm(mock_json_response(sales_json)),
                make_post_async_cm(mock_json_response(matrices_json)),
                make_post_async_cm(mock_json_response(sales_json)),
            ],
        )
        client._session = mock_session

        r1 = await client.get_sales_resolved(from_date, to_date)
        r2 = await client.get_sales_resolved(from_date, to_date)

        assert len(r1) == 1 and r1[0].product_code == "77"
        assert len(r2) == 1 and r2[0].product_code == "77"
        assert mock_session.post.call_count == 3
        assert _count_posts_containing(mock_session, "GetGoodsMatrices") == 1
        await client.close()

    @pytest.mark.asyncio
    async def test_second_get_sales_resolved_reuses_cached_formulations(self, mock_timestamp_provider):
        """Два вызова с рецептурной матрицей — по одному запросу к GetGoodsMatrices и GetFormulations."""
        account = KitAPIAccount(login="u", password="p", company_id=1)
        client = KitVendingAPIClient(account=account, timestamp_provider=mock_timestamp_provider)

        from_date = datetime(2024, 1, 1, tzinfo=ZoneInfo("Asia/Yekaterinburg"))
        to_date = datetime(2024, 1, 31, tzinfo=ZoneInfo("Asia/Yekaterinburg"))

        sales_json = {
            "ResultCode": 0,
            "Sales": [
                {
                    "LineNumber": 3,
                    "Sum": 99.0,
                    "DateTime": "01.01.2024 12:00:00",
                    "GoodsName": "Товар 3",
                    "VendingMachine": 2,
                    "VendingMachineName": "VM [001]",
                    "MatrixId": 7,
                }
            ],
        }
        matrices_json = {
            "ResultCode": 0,
            "GoodsMatrices": [
                {
                    "MatrixId": 7,
                    "MatrixName": "Matrix R",
                    "MatrixType": 2,
                    "Details": [
                        {"LineNumber": 3, "Price2": 99.0, "FormulationId": 100},
                    ],
                }
            ],
        }
        formulations_json = {
            "ResultCode": 0,
            "Formulations": [
                {"FormulationId": 100, "FormulationName": "42|Recipe Title"},
            ],
        }

        mock_session = create_mock_session_with_post(
            None,
            post_side_effect=[
                make_post_async_cm(mock_json_response(sales_json)),
                make_post_async_cm(mock_json_response(matrices_json)),
                make_post_async_cm(mock_json_response(formulations_json)),
                make_post_async_cm(mock_json_response(sales_json)),
            ],
        )
        client._session = mock_session

        r1 = await client.get_sales_resolved(from_date, to_date)
        r2 = await client.get_sales_resolved(from_date, to_date)

        assert r1[0].product_code == "42" and r2[0].product_code == "42"
        assert mock_session.post.call_count == 4
        assert _count_posts_containing(mock_session, "GetGoodsMatrices") == 1
        assert _count_posts_containing(mock_session, "GetFormulations") == 1
        await client.close()

    @pytest.mark.asyncio
    async def test_different_accounts_separate_matrix_cache(self, mock_timestamp_provider):
        """Разные KitAPIAccount — отдельные запросы GetGoodsMatrices, повтор с тем же аккаунтом из кэша."""
        acc1 = KitAPIAccount(login="user1", password="p", company_id=10)
        acc2 = KitAPIAccount(login="user2", password="p", company_id=20)
        client = KitVendingAPIClient(timestamp_provider=mock_timestamp_provider)

        matrices_json = {
            "ResultCode": 0,
            "GoodsMatrices": [
                {
                    "MatrixId": 1,
                    "MatrixName": "M",
                    "MatrixType": 1,
                    "Details": [
                        {"LineNumber": 1, "Price2": 1.0, "GoodsName": "1|A", "MaxCount": 1},
                    ],
                }
            ],
        }

        mock_session = create_mock_session_with_post(
            None,
            post_side_effect=[
                make_post_async_cm(mock_json_response(matrices_json)),
                make_post_async_cm(mock_json_response(matrices_json)),
            ],
        )
        client._session = mock_session

        await client.get_product_matrices(acc1)
        await client.get_product_matrices(acc2)
        await client.get_product_matrices(acc1)

        assert _count_posts_containing(mock_session, "GetGoodsMatrices") == 2
        await client.close()

    @pytest.mark.asyncio
    async def test_clear_matrices_cache_refetches(self, mock_timestamp_provider):
        """clear_matrices_and_recipes_cache(account) сбрасывает кэш только для этого ключа."""
        account = KitAPIAccount(login="u", password="p", company_id=1)
        client = KitVendingAPIClient(account=account, timestamp_provider=mock_timestamp_provider)

        matrices_json = {
            "ResultCode": 0,
            "GoodsMatrices": [
                {
                    "MatrixId": 1,
                    "MatrixName": "M",
                    "MatrixType": 1,
                    "Details": [
                        {"LineNumber": 1, "Price2": 1.0, "GoodsName": "1|A", "MaxCount": 1},
                    ],
                }
            ],
        }

        mock_session = create_mock_session_with_post(
            None,
            post_side_effect=[
                make_post_async_cm(mock_json_response(matrices_json)),
                make_post_async_cm(mock_json_response(matrices_json)),
            ],
        )
        client._session = mock_session

        await client.get_product_matrices()
        client.clear_matrices_and_recipes_cache(account)
        await client.get_product_matrices()

        assert _count_posts_containing(mock_session, "GetGoodsMatrices") == 2
        await client.close()


class TestContextManager:
    """Тесты контекстного менеджера"""

    @pytest.mark.asyncio
    async def test_context_manager(self, api_account):
        """Тест использования клиента как контекстного менеджера"""
        async with KitVendingAPIClient(account=api_account) as client:
            assert client is not None
            # Сессия должна быть закрыта после выхода из контекста

    @pytest.mark.asyncio
    async def test_close(self, api_account):
        """Тест закрытия сессии"""
        client = KitVendingAPIClient(account=api_account)
        # Создаем сессию
        await client._get_session()
        # Закрываем
        await client.close()
        # Проверяем что сессия закрыта
        assert client._session is None or client._session.closed

