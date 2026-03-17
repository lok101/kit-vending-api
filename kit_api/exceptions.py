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
