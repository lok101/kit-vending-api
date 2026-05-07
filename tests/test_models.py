"""
Тесты для моделей данных
"""

from kit_api.models.product import ProductModel


def _goods(goods_id: int, goods_name: str) -> ProductModel:
    return ProductModel.model_validate({"GoodsId": goods_id, "GoodsName": goods_name})


class TestProductModel:
    """Тесты ProductModel (ответ GetGoods: GoodsId, GoodsName)."""

    def test_code_from_pipe_name(self) -> None:
        """Код из префикса «числа|» в GoodsName."""
        product = _goods(1, "123|Test Product")
        assert product.code == "123"
        assert product.name == "123|Test Product"

    def test_name_without_pipe_has_no_code(self) -> None:
        """Без «|» computed code — None."""
        product = _goods(2, "Test Product")
        assert product.code is None
        assert product.name == "Test Product"

    def test_empty_numeric_prefix_has_no_code(self) -> None:
        """Префикс «|» без цифр — код None."""
        product = _goods(3, "|Test Product")
        assert product.code is None
        assert product.name == "|Test Product"

    def test_non_numeric_prefix_has_no_code(self) -> None:
        """Нецифровой префикс до «|» — код None."""
        product = _goods(4, "abc|Test Product")
        assert product.code is None
        assert product.name == "abc|Test Product"

    def test_whitespace_stripped_for_code_extraction(self) -> None:
        """Пробелы вокруг числового префикса учитываются в extract_product_code."""
        product = _goods(5, "  123  |  Test Product  ")
        assert product.code == "123"
        assert product.name == "  123  |  Test Product  "

    def test_model_validate_minimal(self) -> None:
        """Прямая валидация из словаря API."""
        product = ProductModel.model_validate({"GoodsId": 10, "GoodsName": "99|X"})
        assert product.id == 10
        assert product.code == "99"
        assert product.name == "99|X"
