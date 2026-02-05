import hashlib
import json
import os
from dataclasses import dataclass
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


@dataclass(frozen=True, slots=True, kw_only=True)
class KitAPIAccount:
    login: str
    password: str
    company_id: int


@rate_limit(max_requests, time_window)
class KitVendingAPIClient:

    def __init__(
            self,
            login: str | None = None,
            password: str | None = None,
            company_id: int | None = None,
            timestamp_provider: TimestampAPI | None = None,
            session: aiohttp.ClientSession | None = None
    ):

        self._timestamp_provider = timestamp_provider or TimestampAPI()
        self._base_url = "https://api2.kit-invest.ru/APIService.svc"
        self._session = session
        self._own_session = session is None
        self._backoff = GlobalBackoff(timeout=backoff_timeout)

        self._login: str | None = login
        self._password: str | None = password
        self._company_id: int | None = company_id

    async def get_sales(
            self,
            from_date: datetime,
            to_date: datetime,
            vending_machine_id: int = None,
            account: KitAPIAccount | None = None,
    ) -> SalesCollection:
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
                filter_data["Filter"]["VendingMachineId"] = vending_machine_id

            return {
                "Auth": self._build_auth(request_id, account),
                **filter_data
            }

        response = await self._async_send_post_request(url, build_data)
        sales_collection = SalesCollection.model_validate(response)

        return sales_collection

    async def get_products(self, account: KitAPIAccount | None = None) -> ProductsKitCollection:
        url = f"{self._base_url}/GetGoods"

        async def build_data() -> dict[str, Any]:
            request_id = await self._timestamp_provider.async_get_now()
            return {"Auth": self._build_auth(request_id, account)}

        response = await self._async_send_post_request(url, build_data)
        products_collection = ProductsKitCollection.model_validate(response)

        return products_collection

    async def get_recipes(self, account: KitAPIAccount | None = None) -> RecipesKitCollection:
        url = f"{self._base_url}/GetFormulations"

        async def build_data() -> dict[str, Any]:
            request_id = await self._timestamp_provider.async_get_now()
            return {"Auth": self._build_auth(request_id, account)}

        response = await self._async_send_post_request(url, build_data)
        models = RecipesKitCollection.model_validate(response)

        return models

    async def get_product_matrices(self, account: KitAPIAccount | None = None) -> MatricesKitCollection:
        url = f"{self._base_url}/GetGoodsMatrices"

        async def build_data() -> dict[str, Any]:
            request_id = await self._timestamp_provider.async_get_now()
            return {"Auth": self._build_auth(request_id, account)}

        response = await self._async_send_post_request(url, build_data)
        matrix_collection = MatricesKitCollection.model_validate(response)

        return matrix_collection

    async def get_vending_machines(self, account: KitAPIAccount | None = None) -> VendingMachinesCollection:
        url = f"{self._base_url}/GetVendingMachines"

        async def build_data() -> dict[str, Any]:
            request_id = await self._timestamp_provider.async_get_now()
            return {"Auth": self._build_auth(request_id, account)}

        response = await self._async_send_post_request(url, build_data)
        collection = VendingMachinesCollection.model_validate(response)

        return collection

    async def create_matrix(
            self,
            positions: list[dict[str, Any]],
            matrix_name: str,
            account: KitAPIAccount | None = None
    ) -> int:
        url = f"{self._base_url}/CreatePiecesMatrix"

        async def build_data() -> dict[str, Any]:
            request_id = await self._timestamp_provider.async_get_now()

            return {
                "Auth": self._build_auth(request_id, account),
                "MatrixName": matrix_name,
                "Positions": [
                    {
                        'LineNumber': position['line_number'],
                        'ChoiceNumber': position['line_number'],
                        'GoodsName': position['product_name'],
                        'Price2': position['price'],
                        'Price': position['price'],
                    } for position in positions
                ]
            }

        response = await self._async_send_post_request(url, build_data)
        return int(response["Id"])

    def is_authenticated(self) -> bool:
        return self._login is not None and self._password is not None and self._company_id is not None

    def _build_auth(self, request_id: int, account: KitAPIAccount | None) -> dict[str, Any]:
        if not self.is_authenticated() and account is None:
            raise KitAPIAuthError(
                "Учётные данные не установлены. Передайте данные в констуктор клиента "
                "или в аргументах метода в виде аккаунта.")


        if account is not None:
            login = account.login
            password = account.password
            company_id = account.company_id

        else:
            login = self._login
            password = self._password
            company_id = self._company_id


        sign = hashlib.md5(
            f"{company_id}{password}{request_id}".encode("utf-8")
        ).hexdigest()
        return {
            "CompanyId": company_id,
            "RequestId": request_id,
            "UserLogin": login,
            "Sign": sign,
        }

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
            self._own_session = True
        return self._session

    async def _async_send_post_request(
            self,
            url: str,
            build_data: Callable[[], Awaitable[Mapping]]
    ) -> Mapping:

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

        raise KitAPIError("Неожиданное завершение цикла retry")

    async def close(self):
        if self._session and not self._session.closed and self._own_session:
            await self._session.close()
            self._session = None

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
