import hashlib
import json
import os
from datetime import datetime
from enum import IntEnum
from typing import Mapping, Any

import aiohttp
from aiohttp import ClientError as AioHTTPClientError, ContentTypeError
from dotenv import load_dotenv

from kit_api.models import RecipesKitCollection
from kit_api.exceptions import (
    KitAPIError,
    KitAPIAuthError,
    KitAPINetworkError,
    KitAPIResponseError,
    KitAPIValidationError,
)
from kit_api.models import (
    MatricesKitCollection,
    ProductsKitCollection,
    SalesKitCollection,
    VendingMachinesCollection,
)
from kit_api.timestamp_api import TimestampAPI
from kit_api.project_time import ProjectTime
from kit_api.rate_limiter import rate_limit


class ResultCodes(IntEnum):
    SUCCESS = 0
    TOO_MANY_REQUEST = 27


load_dotenv()

try:
    max_requests = int(os.getenv("KIT_API_REQUEST_PER_WINDOW", 1))
    time_window = int(os.getenv("KIT_API_WINDOW_SECONDS", 10))
except ValueError as e:
    raise KitAPIValidationError("KIT_API_REQUEST_PER_WINDOW and KIT_API_WINDOW_SECONDS (.env) должны быть числами.")


@rate_limit(max_requests, time_window)
class KitVendingAPIClient:
    """
    Клиент для работы с Kit Vending API (api2.kit-invest.ru)
    
    Args:
        login: Логин для авторизации
        password: Пароль для авторизации
        company_id: ID компании
        timestamp_provider: Провайдер для получения timestamp (по умолчанию TimestampAPI)
    """

    def __init__(
            self,
            login: str | None = None,
            password: str | None = None,
            company_id: str | None = None,
            timestamp_provider: TimestampAPI | None = None,
            session: aiohttp.ClientSession | None = None
    ):
        """
        Args:
            login: Логин для авторизации
            password: Пароль для авторизации
            company_id: ID компании
            timestamp_provider: Провайдер для получения timestamp (по умолчанию TimestampAPI)
            session: HTTP сессия для переиспользования (опционально)
        """

        self._timestamp_provider = timestamp_provider or TimestampAPI()
        self._login = login or os.getenv("KIT_API_LOGIN")
        self._password = password or os.getenv("KIT_API_PASSWORD")
        self._company_id = company_id or os.getenv("KIT_API_COMPANY_ID")
        self._base_url = "https://api2.kit-invest.ru/APIService.svc"
        self._session = session
        self._own_session = session is None

        # Валидация обязательных параметров
        if not self._login:
            raise KitAPIValidationError(
                "Не указан login. Передайте login в конструктор или установите переменную окружения KIT_API_LOGIN"
            )
        if not self._password:
            raise KitAPIValidationError(
                "Не указан password. Передайте password в конструктор или установите переменную окружения KIT_API_PASSWORD"
            )
        if not self._company_id:
            raise KitAPIValidationError(
                "Не указан company_id. Передайте company_id в конструктор или установите переменную окружения KIT_API_COMPANY_ID"
            )

    async def get_sales(
            self,
            vending_machine_id: int,
            from_date: datetime,
            to_date: datetime
    ) -> SalesKitCollection:
        """
        Получить продажи по торговому автомату за период
        
        Args:
            vending_machine_id: ID торгового автомата
            from_date: Начальная дата
            to_date: Конечная дата
            
        Returns:
            SalesKitCollection: Коллекция продаж
        """
        endpoint = "/GetSales"
        request_id = await self._timestamp_provider.async_get_now()
        url = f"{self._base_url}{endpoint}"
        to_dt_api_format = ProjectTime.datetime_to_str_kit(to_date)
        from_dt_api_format = ProjectTime.datetime_to_str_kit(from_date)

        data = {
            "Auth": self._build_auth(request_id),
            "Filter": {
                "UpDate": from_dt_api_format,
                "ToDate": to_dt_api_format,
                "VendingMachineId": vending_machine_id,
            }
        }

        response = await self._async_send_post_request(url, data)
        sales_collection = SalesKitCollection.model_validate(response)

        return sales_collection

    async def get_products(self) -> ProductsKitCollection:
        """
        Получить список товаров
        
        Returns:
            ProductsKitCollection: Коллекция товаров
        """
        endpoint = "/GetGoods"
        request_id = await self._timestamp_provider.async_get_now()
        url = f"{self._base_url}{endpoint}"
        data = {
            "Auth": self._build_auth(request_id),
        }

        response = await self._async_send_post_request(url, data)
        products_collection = ProductsKitCollection.model_validate(response)

        return products_collection

    async def get_recipes(self) -> RecipesKitCollection:
        """Получить список рецептов напитков."""
        endpoint = "/GetFormulations"
        request_id = await self._timestamp_provider.async_get_now()
        url = f"{self._base_url}{endpoint}"
        data = {
            "Auth": self._build_auth(request_id),
        }

        response = await self._async_send_post_request(url, data)
        models = RecipesKitCollection.model_validate(response)

        return models

    async def get_product_matrices(self) -> MatricesKitCollection:
        """
        Получить матрицы товаров
        
        Returns:
            MatricesKitCollection: Коллекция матриц
        """
        endpoint = "/GetGoodsMatrices"
        request_id = await self._timestamp_provider.async_get_now()
        url = f"{self._base_url}{endpoint}"
        data = {
            "Auth": self._build_auth(request_id),
        }

        response = await self._async_send_post_request(url, data)
        matrix_collection = MatricesKitCollection.model_validate(response)

        return matrix_collection

    async def get_vending_machines(self) -> VendingMachinesCollection:
        """
        Получить список торговых автоматов
        
        Returns:
            VendingMachinesCollection: Коллекция торговых автоматов
        """
        endpoint = "/GetVendingMachines"
        request_id = await self._timestamp_provider.async_get_now()
        url = f"{self._base_url}{endpoint}"
        data = {
            "Auth": self._build_auth(request_id),
        }

        response = await self._async_send_post_request(url, data)
        collection = VendingMachinesCollection.model_validate(response)

        return collection

    def _build_auth(self, request_id: int) -> dict[str, Any]:
        """Построить объект авторизации"""
        sign = hashlib.md5(
            f"{self._company_id}{self._password}{request_id}".encode("utf-8")
        ).hexdigest()
        return {
            "CompanyId": self._company_id,
            "RequestId": request_id,
            "UserLogin": self._login,
            "Sign": sign,
        }

    async def _get_session(self) -> aiohttp.ClientSession:
        """Получить HTTP сессию, создав её при необходимости"""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
            self._own_session = True
        return self._session

    async def _async_send_post_request(self, url: str, data: Mapping) -> Mapping:
        """Отправить асинхронный POST запрос"""
        session = await self._get_session()

        try:
            async with session.post(url=url, data=json.dumps(data)) as response:
                response.raise_for_status()

                try:
                    response_data = await response.json()
                except (ContentTypeError, json.JSONDecodeError) as e:
                    raise KitAPIResponseError(
                        f"Не удалось разобрать JSON ответ от API: {e}",
                        result_code=-1
                    )

                try:
                    result_code = response_data['ResultCode']
                except KeyError:
                    raise KitAPIResponseError(
                        "Ответ API не содержит поле ResultCode",
                        result_code=-1
                    )

                if result_code == ResultCodes.TOO_MANY_REQUEST:
                    raise KitAPIResponseError(
                        f"Превышен лимит запросов к API. Код ответа: {result_code}",
                        result_code=result_code
                    )

                if result_code != ResultCodes.SUCCESS:
                    message = response_data.get("ErrorMessage", "Неизвестная ошибка")
                    raise KitAPIResponseError(
                        f'Не удалось получить данные от Kit API, код ответа - {result_code}, текст ошибки: {message}',
                        result_code=result_code
                    )

                return response_data

        except AioHTTPClientError as e:
            raise KitAPINetworkError(f"Ошибка сети: {e}") from e
        except KitAPIResponseError:
            raise
        except Exception as e:
            raise KitAPIError(f"Неожиданная ошибка при выполнении запроса: {e}") from e

    async def close(self):
        """Закрыть HTTP сессию, если она была создана клиентом"""
        if self._session and not self._session.closed and self._own_session:
            await self._session.close()
            self._session = None

    async def __aenter__(self):
        """Асинхронный контекстный менеджер: вход"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Асинхронный контекстный менеджер: выход (закрытие сессии)"""
        await self.close()
