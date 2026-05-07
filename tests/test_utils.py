"""Тесты утилит kit_api.utils."""

from kit_api.utils import is_product_name_placeholder, is_product_zero_placeholder


class TestIsProductNamePlaceholder:
    def test_positive(self) -> None:
        assert is_product_name_placeholder("Товар 5") is True
        assert is_product_name_placeholder("  Товар 12  ") is True

    def test_negative(self) -> None:
        assert is_product_name_placeholder("товар 5") is False
        assert is_product_name_placeholder("Товар") is False
        assert is_product_name_placeholder("Товар x") is False
        assert is_product_name_placeholder("123|Name") is False
        assert is_product_name_placeholder("Товар 1 extra") is False


class TestIsProductZeroPlaceholder:
    def test_positive(self) -> None:
        assert is_product_zero_placeholder("Товар 0") is True
        assert is_product_zero_placeholder("  Товар 0  ") is True

    def test_negative(self) -> None:
        assert is_product_zero_placeholder("Товар 1") is False
        assert is_product_zero_placeholder("Товар 00") is False
        assert is_product_zero_placeholder("товар 0") is False
