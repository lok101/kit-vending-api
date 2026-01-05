"""
API для получения текущего timestamp
"""

import json
import aiohttp
import requests
from aiohttp import ClientError as AioHTTPClientError, ContentTypeError

from kit_api.exceptions import KitAPINetworkError, KitAPIError


class TimestampAPI:
    """
    Класс для получения текущего timestamp с сервера
    """
    
    def __init__(self, base_url: str | None = None):
        """
        Args:
            base_url: URL для получения timestamp. 
                     По умолчанию используется сервис SberDevices
        """
        self._base_url = base_url or "https://smartapp-code.sberdevices.ru/tools/api/now?tz=Europe/Moscow&format=dd/MM/yyyy"

    async def async_get_now(self) -> int:
        """
        Асинхронно получить текущий timestamp
        
        Returns:
            int: Текущий timestamp в секундах
            
        Raises:
            KitAPINetworkError: Ошибка сети
            KitAPIError: Ошибка при получении timestamp
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url=self._base_url) as response:
                    response.raise_for_status()
                    try:
                        data = await response.json()
                    except (ContentTypeError, json.JSONDecodeError) as e:
                        raise KitAPIError(f"Не удалось разобрать JSON ответ от timestamp API: {e}") from e
                    
                    try:
                        return data['timestamp']
                    except KeyError:
                        raise KitAPIError(f"Ответ timestamp API не содержит поле 'timestamp'. Данные: {data}")
        except AioHTTPClientError as e:
            raise KitAPINetworkError(f"Ошибка сети при получении timestamp: {e}") from e

    def get_now(self) -> int:
        """
        Синхронно получить текущий timestamp
        
        Returns:
            int: Текущий timestamp в секундах
            
        Raises:
            KitAPINetworkError: Ошибка сети
            KitAPIError: Ошибка при получении timestamp
        """
        try:
            response = requests.get(url=self._base_url)
            response.raise_for_status()
            try:
                data = response.json()
            except json.JSONDecodeError as e:
                raise KitAPIError(f"Не удалось разобрать JSON ответ от timestamp API: {e}") from e
            
            try:
                return data['timestamp']
            except KeyError:
                raise KitAPIError(f"Ответ timestamp API не содержит поле 'timestamp'. Данные: {data}")
        except requests.RequestException as e:
            raise KitAPINetworkError(f"Ошибка сети при получении timestamp: {e}") from e

