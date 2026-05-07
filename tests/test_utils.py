"""Тесты утилит kit_api.utils."""

from kit_api.utils import (
    is_product_name_placeholder,
    is_product_zero_placeholder,
    try_product_code_from_placeholder_name,
)


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


class TestTryProductCodeFromPlaceholderName:
    def test_four_digit_two_prefix(self) -> None:
        assert try_product_code_from_placeholder_name("Товар 2311") == "2311"
        assert try_product_code_from_placeholder_name("  Товар 2101  ") == "2101"
        assert try_product_code_from_placeholder_name("Товар 2000") == "2000"

    def test_not_applicable(self) -> None:
        assert try_product_code_from_placeholder_name("Товар 5") is None
        assert try_product_code_from_placeholder_name("Товар 231") is None
        assert try_product_code_from_placeholder_name("Товар 23111") is None
        assert try_product_code_from_placeholder_name("Товар 3999") is None
        assert try_product_code_from_placeholder_name("123|X") is None
        assert try_product_code_from_placeholder_name("Товар 0") is None
