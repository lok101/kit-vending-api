import asyncio
import inspect
import time
from collections import deque
from collections.abc import Awaitable, Callable
from typing import Any, Deque, TypeVar

_T = TypeVar("_T")


class GlobalBackoff:
    """
    Механизм глобальной блокировки при превышении лимита API (код TOO_MANY_REQUEST).
    Все запросы ждут, пока backoff активен.
    """

    def __init__(self, timeout: float = 60.0):
        self._timeout = timeout
        self._event: asyncio.Event | None = None
        self._lock: asyncio.Lock | None = None
        self._backoff_task: asyncio.Task[None] | None = None

    def _ensure_initialized(self) -> None:
        """Ленивая инициализация asyncio примитивов в текущем event loop."""
        if self._event is None:
            self._event = asyncio.Event()
            self._event.set()
        if self._lock is None:
            self._lock = asyncio.Lock()

    async def wait_if_blocked(self) -> None:
        """Ждать, если активен backoff."""
        self._ensure_initialized()
        assert self._event is not None
        await self._event.wait()

    async def trigger_backoff(self) -> None:
        """
        Активировать глобальный backoff.
        Все запросы будут ждать timeout секунд.
        Если backoff уже активен, просто ждём его завершения.
        """
        self._ensure_initialized()
        assert self._lock is not None
        assert self._event is not None

        async with self._lock:
            if not self._event.is_set():
                # Backoff уже активен, ждём его завершения
                pass
            else:
                # Активируем backoff
                self._event.clear()
                self._backoff_task = asyncio.create_task(self._backoff_timer())

        # Ждём завершения backoff вне lock
        await self._event.wait()

    async def _backoff_timer(self) -> None:
        """Таймер backoff, разблокирует после timeout."""
        try:
            await asyncio.sleep(self._timeout)
        finally:
            assert self._event is not None
            self._event.set()
            self._backoff_task = None

    def is_blocked(self) -> bool:
        if self._event is None:
            return False
        return not self._event.is_set()


class RateLimiter:
    """
    Упрощенный ограничитель запросов для одного API с одним набором лимитов.
    """

    def __init__(self, max_requests: int, time_window: float = 1.0):
        """
        Args:
            max_requests: Максимальное количество запросов в time_window секунд
            time_window: Временное окно в секундах
        """
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests: Deque[float] = deque()
        self._lock = asyncio.Lock()

    async def wait(self) -> None:
        """
        Асинхронно ожидает, когда можно будет выполнить следующий запрос.
        """
        async with self._lock:
            current_time = time.monotonic()

            # Удаляем старые запросы
            while self.requests and self.requests[0] <= current_time - self.time_window:
                self.requests.popleft()

            if len(self.requests) < self.max_requests:
                # Можно выполнить запрос сразу
                self.requests.append(current_time)
                return

            # Нужно подождать
            wait_until = self.requests[0] + self.time_window
            wait_time = max(0.0, wait_until - current_time)

            # Обновляем очередь
            self.requests.append(wait_until)
            self.requests.popleft()

            if wait_time > 0:
                await asyncio.sleep(wait_time)


def rate_limit(max_requests: int, time_window: float = 1.0) -> Callable[[type[_T]], type[_T]]:
    """
    Декоратор класса для автоматического ограничения запросов к API.

    Args:
        max_requests: Максимальное количество запросов в time_window секунд
        time_window: Временное окно в секундах
    """

    def decorator(cls: type[_T]) -> type[_T]:
        # Создаем экземпляр ограничителя для класса
        limiter = RateLimiter(max_requests, time_window)

        # Обходим все методы класса
        for attr_name in dir(cls):
            if attr_name.startswith('_'):
                continue

            attr = getattr(cls, attr_name)
            # Если это асинхронный метод, оборачиваем его
            if callable(attr) and inspect.iscoroutinefunction(attr):
                setattr(cls, attr_name, _wrap_method(attr, limiter))

        # Добавляем ограничитель как атрибут класса
        setattr(cls, "_limiter", limiter)
        return cls

    return decorator


def _wrap_method(
    method: Callable[..., Awaitable[Any]],
    limiter: RateLimiter,
) -> Callable[..., Awaitable[Any]]:
    """
    Обертка для асинхронного метода, добавляющая ожидание ограничителя.
    """

    async def wrapper(self: Any, *args: Any, **kwargs: Any) -> Any:
        await limiter.wait()
        return await method(self, *args, **kwargs)

    return wrapper


def api_method(
    max_requests: int | None = None,
    time_window: float = 1.0,
) -> Callable[[Callable[..., Awaitable[Any]]], Callable[..., Awaitable[Any]]]:
    """
    Декоратор для отдельных методов API.
    Если параметры не указаны, используются параметры из декоратора класса.
    """

    def decorator(func: Callable[..., Awaitable[Any]]) -> Callable[..., Awaitable[Any]]:
        async def wrapper(self: Any, *args: Any, **kwargs: Any) -> Any:
            limiter = getattr(self, '_limiter', None)
            if limiter is None:
                if max_requests is None:
                    raise ValueError(
                        "Для метода нужно указать max_requests или использовать "
                        "декоратор @rate_limit на классе"
                    )
                limiter = RateLimiter(max_requests, time_window)

            await limiter.wait()
            return await func(self, *args, **kwargs)

        return wrapper

    return decorator
