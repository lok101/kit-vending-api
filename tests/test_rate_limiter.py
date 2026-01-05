"""
Тесты для RateLimiter
"""

import pytest
import asyncio
import time
from kit_api.rate_limiter import RateLimiter, rate_limit


class TestRateLimiter:
    """Тесты RateLimiter"""

    @pytest.mark.asyncio
    async def test_rate_limiter_allows_requests_within_limit(self):
        """Тест что лимитер разрешает запросы в пределах лимита"""
        limiter = RateLimiter(max_requests=5, time_window=1.0)

        # Выполняем 5 запросов подряд
        start_time = time.monotonic()
        for _ in range(5):
            await limiter.wait()
        end_time = time.monotonic()

        # Все запросы должны пройти быстро (без ожидания)
        assert end_time - start_time < 0.1

    @pytest.mark.asyncio
    async def test_rate_limiter_blocks_exceeding_requests(self):
        """Тест что лимитер блокирует запросы превышающие лимит"""
        limiter = RateLimiter(max_requests=2, time_window=0.5)

        # Первые 2 запроса должны пройти быстро
        await limiter.wait()
        await limiter.wait()

        # Третий запрос должен ждать
        start_time = time.monotonic()
        await limiter.wait()
        end_time = time.monotonic()

        # Должно быть ожидание около 0.5 секунды
        assert end_time - start_time >= 0.4
        assert end_time - start_time < 0.7

    @pytest.mark.asyncio
    async def test_rate_limiter_resets_after_time_window(self):
        """Тест что лимитер сбрасывается после временного окна"""
        limiter = RateLimiter(max_requests=1, time_window=0.3)

        # Первый запрос проходит
        await limiter.wait()

        # Второй должен ждать
        await limiter.wait()

        # Ждем окончания временного окна
        await asyncio.sleep(0.35)

        # Следующий запрос должен пройти быстро
        start_time = time.monotonic()
        await limiter.wait()
        end_time = time.monotonic()

        assert end_time - start_time < 0.1

    @pytest.mark.asyncio
    async def test_rate_limiter_thread_safety(self):
        """Тест потокобезопасности лимитера"""
        limiter = RateLimiter(max_requests=10, time_window=1.0)

        # Выполняем много запросов параллельно
        tasks = [limiter.wait() for _ in range(20)]
        start_time = time.monotonic()
        await asyncio.gather(*tasks)
        end_time = time.monotonic()

        # Первые 10 должны пройти быстро, остальные должны ждать
        # Общее время должно быть около 1 секунды
        assert end_time - start_time >= 0.9
        assert end_time - start_time < 1.5


class TestRateLimitDecorator:
    """Тесты декоратора rate_limit"""

    @pytest.mark.asyncio
    async def test_rate_limit_decorator_applies_to_async_methods(self):
        """Тест что декоратор применяется к асинхронным методам"""

        @rate_limit(max_requests=2, time_window=0.5)
        class TestClass:
            async def async_method(self):
                return "result"

            def sync_method(self):
                return "result"

        instance = TestClass()

        # Асинхронный метод должен быть обернут
        assert hasattr(TestClass, '_limiter')
        assert asyncio.iscoroutinefunction(instance.async_method)

        # Синхронный метод не должен быть обернут
        assert not asyncio.iscoroutinefunction(instance.sync_method)

    @pytest.mark.asyncio
    async def test_rate_limit_decorator_limits_calls(self):
        """Тест что декоратор ограничивает вызовы методов"""

        @rate_limit(max_requests=2, time_window=0.5)
        class TestClass:
            async def test_method(self):
                return time.monotonic()

        instance = TestClass()

        # Первые два вызова должны пройти быстро
        start = time.monotonic()
        await instance.test_method()
        await instance.test_method()
        first_two = time.monotonic() - start

        # Третий вызов должен ждать
        start = time.monotonic()
        await instance.test_method()
        third = time.monotonic() - start

        assert first_two < 0.1
        assert third >= 0.4

    @pytest.mark.asyncio
    async def test_rate_limit_decorator_preserves_method_signature(self):
        """Тест что декоратор сохраняет сигнатуру метода"""

        @rate_limit(max_requests=1, time_window=1.0)
        class TestClass:
            async def test_method(self, arg1, arg2=None):
                return arg1, arg2

        instance = TestClass()
        result = await instance.test_method("test", arg2="value")

        assert result == ("test", "value")

    @pytest.mark.asyncio
    async def test_rate_limit_decorator_ignores_private_methods(self):
        """Тест что декоратор игнорирует приватные методы"""

        @rate_limit(max_requests=1, time_window=1.0)
        class TestClass:
            async def _private_method(self):
                return "private"

            async def public_method(self):
                return "public"

        instance = TestClass()

        # Приватный метод не должен быть обернут
        # Проверяем что он не использует лимитер
        start = time.monotonic()
        await instance._private_method()
        await instance._private_method()
        elapsed = time.monotonic() - start

        # Оба вызова должны пройти быстро (без ожидания)
        assert elapsed < 0.1


