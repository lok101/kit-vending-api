"""Тесты разрешения кода товара из продажи."""

from __future__ import annotations

import pytest

from kit_api.exceptions import SaleProductCodeResolveCriticalError
from kit_api.models import SaleModel
from kit_api.sale_resolve import resolve_sale_product_code


def _sale(
        *,
        goods_name: str,
        matrix_id: int | None,
        line: int = 1,
) -> SaleModel:
    return SaleModel.model_validate(
        {
            "LineNumber": line,
            "Sum": 1.0,
            "DateTime": "01.05.2026 12:00:00",
            "GoodsName": goods_name,
            "VendingMachine": 1,
            "VendingMachineName": "Test [501]",
            "MatrixId": matrix_id,
        }
    )


class TestResolveSaleProductCodePlaceholderMatrixMissing:
    def test_matrix_id_none_four_digit_two(self) -> None:
        sale = _sale(goods_name="Товар 2311", matrix_id=None)
        assert resolve_sale_product_code(sale, {}, {}) == "2311"

    def test_matrix_id_none_no_fallback(self) -> None:
        sale = _sale(goods_name="Товар 12", matrix_id=None)
        with pytest.raises(SaleProductCodeResolveCriticalError):
            resolve_sale_product_code(sale, {}, {})

    def test_matrix_missing_in_catalog_four_digit_two(self) -> None:
        sale = _sale(goods_name="Товар 2101", matrix_id=999)
        assert resolve_sale_product_code(sale, {}, {}) == "2101"

    def test_matrix_missing_no_fallback_wrong_prefix(self) -> None:
        sale = _sale(goods_name="Товар 3999", matrix_id=None)
        with pytest.raises(SaleProductCodeResolveCriticalError):
            resolve_sale_product_code(sale, {}, {})
