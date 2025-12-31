"""
API для получения текущего timestamp
"""

import aiohttp
import requests


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
        """
        async with aiohttp.ClientSession() as session:
            async with session.get(url=self._base_url) as response:
                response.raise_for_status()
                data = await response.json()
                return data['timestamp']

    def get_now(self) -> int:
        """
        Синхронно получить текущий timestamp
        
        Returns:
            int: Текущий timestamp в секундах
        """
        response = requests.get(url=self._base_url)
        response.raise_for_status()
        data = response.json()
        return data['timestamp']

