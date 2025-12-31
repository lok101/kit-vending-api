import hashlib
import json
from datetime import datetime
from enum import IntEnum
from typing import Mapping, Any

import aiohttp
import requests

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


@rate_limit(1, 10)
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
        login: str, 
        password: str, 
        company_id: str, 
        timestamp_provider: TimestampAPI | None = None
    ):
        self._timestamp_provider = timestamp_provider or TimestampAPI()
        self._login = login
        self._password = password
        self._company_id = company_id
        self._base_url = "https://api2.kit-invest.ru/APIService.svc"

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

    @staticmethod
    async def _async_send_post_request(url: str, data: Mapping) -> Mapping:
        """Отправить асинхронный POST запрос"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url=url, data=json.dumps(data)) as response:
                    response.raise_for_status()
                    response_data = await response.json()
                    result_code = response_data['ResultCode']

                    if result_code != ResultCodes.SUCCESS:
                        message = response_data.get("ErrorMessage", "Неизвестная ошибка")
                        raise Exception(
                            f'Не удалось получить данные от Kit API, код ответа - {result_code}, текст ошибки: {message}'
                        )

                    return response_data

        except aiohttp.ClientError as e:
            raise Exception(f"Ошибка сети: {e}")

    @staticmethod
    def _send_post_request(url: str, data: Mapping) -> Mapping:
        """Отправить синхронный POST запрос"""
        response = requests.post(url, data=json.dumps(data))
        response.raise_for_status()
        response_data = response.json()
        result_code = response_data['ResultCode']

        if result_code != ResultCodes.SUCCESS:
            message = response_data.get("ErrorMessage", "Неизвестная ошибка")
            raise Exception(
                f'Не удалось получить данные от Kit API, код ответа - {result_code}, текст ошибки: {message}'
            )

        return response_data

