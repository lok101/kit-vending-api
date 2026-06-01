"""
Тесты для TimestampAPI
"""

import time

import pytest

from kit_api.timestamp_api import TimestampAPI


class TestAsyncGetNow:
    """Тесты асинхронного метода async_get_now"""

    @pytest.mark.asyncio
    async def test_async_get_now_returns_current_unix_timestamp(self):
        """Тест получения локального unix timestamp"""
        api = TimestampAPI()
        before = int(time.time())
        result = await api.async_get_now()
        after = int(time.time())

        assert before <= result <= after
