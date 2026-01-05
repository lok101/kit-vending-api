"""
Тесты для моделей данных
"""

import pytest
from kit_api.models.common import ProductModel


class TestProductModel:
    """Тесты ProductModel"""

    def test_product_model_create_with_code_and_name(self):
        """Тест создания модели товара с кодом и именем"""
        product = ProductModel.create("123|Test Product")
        assert product.code == 123
        assert product.name == "Test Product"

    def test_product_model_create_with_name_only(self):
        """Тест создания модели товара только с именем"""
        product = ProductModel.create("Test Product")
        assert product.code is None
        assert product.name == "Test Product"

    def test_product_model_create_with_empty_code(self):
        """Тест создания модели товара с пустым кодом"""
        product = ProductModel.create("|Test Product")
        assert product.code is None
        assert product.name == "Test Product"

    def test_product_model_create_with_invalid_code(self, caplog):
        """Тест создания модели товара с невалидным кодом"""
        product = ProductModel.create("abc|Test Product")
        assert product.code is None
        assert product.name == "Test Product"
        # Проверяем что было предупреждение
        assert "Не удалось преобразовать код товара" in caplog.text

    def test_product_model_create_with_whitespace(self):
        """Тест создания модели товара с пробелами"""
        product = ProductModel.create("  123  |  Test Product  ")
        assert product.code == 123
        assert product.name == "Test Product"

    def test_product_model_create_direct(self):
        """Тест прямого создания модели товара"""
        product = ProductModel(name="Test Product", code=123)
        assert product.code == 123
        assert product.name == "Test Product"

    def test_product_model_create_with_none_code(self):
        """Тест создания модели товара с None кодом"""
        product = ProductModel(name="Test Product", code=None)
        assert product.code is None
        assert product.name == "Test Product"

