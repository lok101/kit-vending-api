class KitAPIError(Exception):
    pass


class KitAPIAuthError(KitAPIError):
    pass


class KitAPIRateLimitError(KitAPIError):
    pass


class KitAPIResponseError(KitAPIError):
    def __init__(self, message: str, result_code: int):
        self.result_code = result_code
        super().__init__(message)


class KitAPINetworkError(KitAPIError):
    pass


class KitAPIValidationError(KitAPIError):
    pass


class SaleProductCodeResolveError(KitAPIError):
    """Не удалось определить код товара для разрешённой продажи (SaleResolvedModel)."""


class SaleProductCodeResolveCriticalError(SaleProductCodeResolveError):
    """Несогласованные или неполные данные каталога/матрицы — логируется как warning."""


class SaleProductCodeResolveNonCriticalError(SaleProductCodeResolveError):
    """Ожидаемый пропуск (переплата, «Товар 0», не плейсхолдер и т. п.) — логируется как debug."""
