"""
Тесты для исключений
"""

import pytest

from kit_api.exceptions import (
    KitAPIError,
    KitAPIAuthError,
    KitAPIRateLimitError,
    KitAPIResponseError,
    KitAPINetworkError,
    KitAPIValidationError,
)


class TestExceptions:
    """Тесты исключений"""

    def test_kit_api_error_is_base_exception(self):
        """Тест что KitAPIError является базовым исключением"""
        error = KitAPIError("Test error")
        assert isinstance(error, Exception)
        assert str(error) == "Test error"

    def test_kit_api_auth_error_inherits_from_kit_api_error(self):
        """Тест что KitAPIAuthError наследуется от KitAPIError"""
        error = KitAPIAuthError("Auth error")
        assert isinstance(error, KitAPIError)
        assert str(error) == "Auth error"

    def test_kit_api_rate_limit_error_inherits_from_kit_api_error(self):
        """Тест что KitAPIRateLimitError наследуется от KitAPIError"""
        error = KitAPIRateLimitError("Rate limit error")
        assert isinstance(error, KitAPIError)
        assert str(error) == "Rate limit error"

    def test_kit_api_response_error_inherits_from_kit_api_error(self):
        """Тест что KitAPIResponseError наследуется от KitAPIError"""
        error = KitAPIResponseError("Response error", result_code=1)
        assert isinstance(error, KitAPIError)
        assert str(error) == "Response error"
        assert error.result_code == 1

    def test_kit_api_network_error_inherits_from_kit_api_error(self):
        """Тест что KitAPINetworkError наследуется от KitAPIError"""
        error = KitAPINetworkError("Network error")
        assert isinstance(error, KitAPIError)
        assert str(error) == "Network error"

    def test_kit_api_validation_error_inherits_from_kit_api_error(self):
        """Тест что KitAPIValidationError наследуется от KitAPIError"""
        error = KitAPIValidationError("Validation error")
        assert isinstance(error, KitAPIError)
        assert str(error) == "Validation error"

    def test_kit_api_response_error_with_result_code(self):
        """Тест KitAPIResponseError с кодом результата"""
        error = KitAPIResponseError("Error message", result_code=27)
        assert error.result_code == 27
        assert str(error) == "Error message"

