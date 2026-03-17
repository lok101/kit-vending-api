import asyncio
import json
from typing import Any

import aiohttp
from aiohttp import ClientError as AioHTTPClientError, ContentTypeError

from kit_api.exceptions import KitAPINetworkError, KitAPIError


class TimestampAPI:
    def __init__(self, base_url: str | None = None):
        self._base_url: str = base_url or "https://smartapp-code.sberdevices.ru/tools/api/now?tz=Europe/Moscow&format=dd/MM/yyyy"

    async def async_get_now(self) -> int:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url=self._base_url) as response:
                    response: aiohttp.ClientResponse
                    response.raise_for_status()
                    try:
                        data: dict[str, Any] = await response.json()
                    except (ContentTypeError, json.JSONDecodeError) as e:
                        raise KitAPIError(f"Не удалось разобрать JSON ответ от timestamp API: {e}") from e

                    try:
                        return data['timestamp']
                    except KeyError:
                        raise KitAPIError(f"Ответ timestamp API не содержит поле 'timestamp'. Данные: {data}")
        except AioHTTPClientError as e:
            raise KitAPINetworkError(f"Ошибка сети при получении timestamp: {e}") from e
