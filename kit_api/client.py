import hashlib
import json
import os
from datetime import datetime
from enum import IntEnum
from typing import Mapping, Any, Callable, Awaitable

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
    SalesCollection,
    VendingMachinesCollection,
)
from kit_api.timestamp_api import TimestampAPI
from kit_api.project_time import LibDateTime
from kit_api.rate_limiter import rate_limit, GlobalBackoff


class ResultCodes(IntEnum):
    SUCCESS = 0
    TOO_MANY_REQUEST = 27


load_dotenv()

try:
    max_requests = int(os.getenv("KIT_API_REQUEST_PER_WINDOW", 1))
    time_window = int(os.getenv("KIT_API_WINDOW_SECONDS", 10))
    backoff_timeout = float(os.getenv("KIT_API_BACKOFF_SECONDS", 60.0))
except ValueError as e:
    raise KitAPIValidationError(
        "KIT_API_REQUEST_PER_WINDOW, KIT_API_WINDOW_SECONDS и KIT_API_BACKOFF_SECONDS (.env) должны быть числами."
    )


@rate_limit(max_requests, time_window)
class KitVendingAPIClient:
    """
    Клиент для работы с Kit Vending API (api2.kit-invest.ru)
    """

    def __init__(
            self,
            login: str | None = None,
            password: str | None = None,
            company_id: int | None = None,
            timestamp_provider: TimestampAPI | None = None,
            session: aiohttp.ClientSession | None = None
    ):
        """
        Args:
            login: Логин для авторизации (опционально, можно установить позже через login())
            password: Пароль для авторизации (опционально, можно установить позже через login())
            company_id: ID компании (опционально, можно установить позже через login())
            timestamp_provider: Провайдер для получения timestamp (по умолчанию TimestampAPI)
            session: HTTP сессия для переиспользования (опционально)
        """
        self._timestamp_provider = timestamp_provider or TimestampAPI()
        self._base_url = "https://api2.kit-invest.ru/APIService.svc"
        self._session = session
        self._own_session = session is None
        self._backoff = GlobalBackoff(timeout=backoff_timeout)

        # Учётные данные изначально не заданы
        self._login: str | None = None
        self._password: str | None = None
        self._company_id: int | None = None

        # Если учётные данные переданы при инициализации, устанавливаем их
        if login and password and company_id:
            self.login(login, password, company_id)

    async def get_sales(
            self,
            from_date: datetime,
            to_date: datetime,
            vending_machine_id: int = None,
    ) -> SalesCollection:
        """
        Получить продажи по торговому автомату за период
        
        Args:
            vending_machine_id: ID торгового автомата
            from_date: Начальная дата
            to_date: Конечная дата
            
        Returns:
            SalesCollection: Коллекция продаж
        """
        url = f"{self._base_url}/GetSales"
        to_dt_api_format = LibDateTime.datetime_to_str_kit(to_date)
        from_dt_api_format = LibDateTime.datetime_to_str_kit(from_date)

        async def build_data() -> dict[str, Any]:
            request_id = await self._timestamp_provider.async_get_now()
            filter_data: dict[str, Any] = {
                "Filter": {
                    "UpDate": from_dt_api_format,
                    "ToDate": to_dt_api_format,
                }
            }
            if vending_machine_id is not None:
                filter_data["VendingMachineId"] = vending_machine_id

            return {
                "Auth": self._build_auth(request_id),
                **filter_data
            }

        response = await self._async_send_post_request(url, build_data)
        sales_collection = SalesCollection.model_validate(response)

        return sales_collection

    async def get_products(self) -> ProductsKitCollection:
        """
        Получить список товаров
        
        Returns:
            ProductsKitCollection: Коллекция товаров
        """
        url = f"{self._base_url}/GetGoods"

        async def build_data() -> dict[str, Any]:
            request_id = await self._timestamp_provider.async_get_now()
            return {"Auth": self._build_auth(request_id)}

        response = await self._async_send_post_request(url, build_data)
        products_collection = ProductsKitCollection.model_validate(response)

        return products_collection

    async def get_recipes(self) -> RecipesKitCollection:
        """Получить список рецептов напитков."""
        url = f"{self._base_url}/GetFormulations"

        async def build_data() -> dict[str, Any]:
            request_id = await self._timestamp_provider.async_get_now()
            return {"Auth": self._build_auth(request_id)}

        response = await self._async_send_post_request(url, build_data)
        models = RecipesKitCollection.model_validate(response)

        return models

    async def get_product_matrices(self) -> MatricesKitCollection:
        """
        Получить матрицы товаров
        
        Returns:
            MatricesKitCollection: Коллекция матриц
        """
        url = f"{self._base_url}/GetGoodsMatrices"

        async def build_data() -> dict[str, Any]:
            request_id = await self._timestamp_provider.async_get_now()
            return {"Auth": self._build_auth(request_id)}

        response = await self._async_send_post_request(url, build_data)
        matrix_collection = MatricesKitCollection.model_validate(response)

        return matrix_collection

    async def get_vending_machines(self) -> VendingMachinesCollection:
        """
        Получить список торговых автоматов
        
        Returns:
            VendingMachinesCollection: Коллекция торговых автоматов
        """
        url = f"{self._base_url}/GetVendingMachines"

        async def build_data() -> dict[str, Any]:
            request_id = await self._timestamp_provider.async_get_now()
            return {"Auth": self._build_auth(request_id)}

        response = await self._async_send_post_request(url, build_data)
        collection = VendingMachinesCollection.model_validate(response)

        return collection

    def login(self, login: str, password: str, company_id: int) -> None:
        """Установить учётные данные для авторизации"""
        if not login:
            raise KitAPIValidationError("login не может быть пустым")
        if not password:
            raise KitAPIValidationError("password не может быть пустым")
        if not company_id:
            raise KitAPIValidationError("company_id не может быть пустым")

        self._login = login
        self._password = password
        self._company_id = company_id

    def logout(self) -> None:
        """Удалить учётные данные"""
        self._login = None
        self._password = None
        self._company_id = None

    def is_authenticated(self) -> bool:
        """Проверить, установлены ли учётные данные"""
        return self._login is not None and self._password is not None and self._company_id is not None

    def _build_auth(self, request_id: int) -> dict[str, Any]:
        """Построить объект авторизации"""
        if not self.is_authenticated():
            raise KitAPIAuthError(
                "Учётные данные не установлены. Используйте метод login() для установки учётных данных.")

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

    async def _async_send_post_request(
            self,
            url: str,
            build_data: Callable[[], Awaitable[Mapping]]
    ) -> Mapping:
        """
        Отправить асинхронный POST запрос с поддержкой retry при TOO_MANY_REQUEST.
        
        Args:
            url: URL для запроса
            build_data: Асинхронная функция для построения данных запроса.
                        Вызывается заново при каждой попытке для обновления request_id.
        """
        max_retries = 2

        for attempt in range(max_retries):
            await self._backoff.wait_if_blocked()

            data = await build_data()
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
                        if attempt < max_retries - 1:
                            await self._backoff.trigger_backoff()
                            continue
                        raise KitAPIResponseError(
                            f"Превышен лимит запросов к API после {max_retries} попыток",
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

        # Этот код не должен выполняться, но для полноты
        raise KitAPIError("Неожиданное завершение цикла retry")

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
