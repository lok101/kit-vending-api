"""
Кастомные исключения для Kit API
"""


class KitAPIError(Exception):
    """Базовое исключение для ошибок Kit API"""
    pass


class KitAPIAuthError(KitAPIError):
    """Ошибка аутентификации"""
    pass


class KitAPIRateLimitError(KitAPIError):
    """Ошибка превышения лимита запросов"""
    pass


class KitAPIResponseError(KitAPIError):
    """Ошибка ответа от API"""
    def __init__(self, message: str, result_code: int):
        self.result_code = result_code
        super().__init__(message)


class KitAPINetworkError(KitAPIError):
    """Ошибка сети"""
    pass


class KitAPIValidationError(KitAPIError):
    """Ошибка валидации данных"""
    pass

