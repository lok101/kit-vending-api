"""Разрешение продаж Kit в код товара и SaleResolvedModel."""

from __future__ import annotations

import logging
from typing import Final

from beartype import beartype

from kit_api.enums import VendingMachineKind
from kit_api.exceptions import (
    SaleProductCodeResolveCriticalError,
    SaleProductCodeResolveNonCriticalError,
)
from kit_api.models import (
    ComboMatrixModel,
    GoodsCell,
    GoodsMatrixModel,
    MatrixModel,
    RecipeCell,
    RecipeMatrixModel,
    RecipeModel,
    SaleModel,
    SaleResolvedModel,
)
from kit_api.utils import (
    compute_vending_machine_type,
    extract_vending_machine_code,
    is_product_name_placeholder,
    is_product_zero_placeholder,
    try_product_code_from_placeholder_name,
)

_LOGGER: Final = logging.getLogger(__name__)


@beartype
def resolve_sale_vending_machine_code(sale: SaleModel) -> str | None:
    vending_machine_code: str | None = extract_vending_machine_code(sale.vending_machine_name)
    if vending_machine_code is None:
        return None
    return vending_machine_code


@beartype
def resolve_sale_product_code(
        sale: SaleModel,
        matrices_by_id: dict[int, MatrixModel],
        recipes_by_id: dict[int, RecipeModel],
) -> str:
    """Возвращает код товара или бросает SaleProductCodeResolve*Error."""
    direct = sale.product_code
    if direct is not None:
        return direct

    if sale.line == -1:
        raise SaleProductCodeResolveNonCriticalError(
            "продажа помечена как «переплата» (LineNumber=-1)"
        )

    if is_product_zero_placeholder(sale.product_name):
        raise SaleProductCodeResolveNonCriticalError(
            "плейсхолдер «Товар 0» — недопустимая позиция"
        )

    if not is_product_name_placeholder(sale.product_name):
        raise SaleProductCodeResolveCriticalError(
            "в названии нет кода (не плейсхолдер «Товар <номер>»)"
        )

    if sale.matrix_id is None:
        fallback = try_product_code_from_placeholder_name(sale.product_name)
        if fallback is not None:
            return fallback
        raise SaleProductCodeResolveCriticalError(
            "плейсхолдер без MatrixId, восстановление по матрице невозможно"
        )

    matrix = matrices_by_id.get(sale.matrix_id)
    if matrix is None:
        fallback = try_product_code_from_placeholder_name(sale.product_name)
        if fallback is not None:
            return fallback
        raise SaleProductCodeResolveCriticalError(
            "матрица не найдена в ответе GetGoodsMatrices"
        )

    cell: GoodsCell | RecipeCell | None = None
    for c in matrix.cells:
        # ошибочная планограмма снеков TCN, двойная ячейка должна обозначаться нечётным числом, но она обозначена чётным.
        if c.line_number == sale.line or sale.line % 2 == 0 and sale.line - 1 == c.line_number:
            if isinstance(c, (GoodsCell, RecipeCell)):
                cell = c
            break

    if cell is None:
        raise SaleProductCodeResolveCriticalError(
            "ячейка с указанным LineNumber не найдена или тип ячейки не поддерживается"
        )

    if isinstance(matrix, GoodsMatrixModel):
        if isinstance(cell, GoodsCell):
            resolved = cell.product_code
            if resolved is None:
                raise SaleProductCodeResolveCriticalError(
                    "в ячейке матрицы товаров нет кода в GoodsName"
                )
            return resolved
        raise SaleProductCodeResolveCriticalError(
            "ожидалась ячейка товарной матрицы (GoodsCell)"
        )

    if isinstance(matrix, RecipeMatrixModel):
        if not isinstance(cell, RecipeCell):
            raise SaleProductCodeResolveCriticalError(
                "ожидалась ячейка рецептурной матрицы (RecipeCell)"
            )
        recipe = recipes_by_id.get(cell.recipe_id)
        if recipe is None:
            raise SaleProductCodeResolveCriticalError(
                f"рецепт FormulationId={cell.recipe_id} не найден в GetFormulations"
            )
        resolved = recipe.code
        if resolved is None:
            raise SaleProductCodeResolveCriticalError(
                "в названии рецепта нет кода (FormulationName)"
            )
        return resolved

    if isinstance(matrix, ComboMatrixModel):
        raise SaleProductCodeResolveCriticalError(
            "матрица типа Combo (MatrixType=3): восстановление кода не поддерживается"
        )

    raise SaleProductCodeResolveCriticalError("неизвестный тип матрицы")


@beartype
def resolve_sales_with_catalog(
        sales: list[SaleModel],
        matrices_by_id: dict[int, MatrixModel],
        recipes_by_id: dict[int, RecipeModel],
        *,
        logger: logging.Logger | None = None,
) -> list[SaleResolvedModel]:
    """Преобразует сырые продажи в разрешённые; при ошибках по строкам логирует и пропускает строку."""
    log = logger if logger is not None else _LOGGER
    result: list[SaleResolvedModel] = []
    for sale in sales:
        try:
            code = resolve_sale_product_code(sale, matrices_by_id, recipes_by_id)
        except SaleProductCodeResolveNonCriticalError as exc:
            log.debug(
                "Пропуск продажи без кода товара (%s): "
                "vending_machine_name=%s, line=%s, matrix_id=%s, product_name=%r",
                exc,
                sale.vending_machine_name,
                sale.line,
                sale.matrix_id,
                sale.product_name,
            )
            continue
        except SaleProductCodeResolveCriticalError as exc:
            log.warning(
                "Не удалось определить код товара для продажи (%s): "
                "vending_machine_name=%s, line=%s, matrix_id=%s, product_name=%r",
                exc,
                sale.vending_machine_name,
                sale.line,
                sale.matrix_id,
                sale.product_name,
                exc_info=True,
            )
            continue

        vending_machine_code = resolve_sale_vending_machine_code(sale)
        if vending_machine_code is None:
            log.warning(
                "Не удалось определить код аппарата для продажи."
                "vending_machine_name=%s, line=%s, matrix_id=%s, product_name=%r",
                sale.vending_machine_name,
                sale.line,
                sale.matrix_id,
                sale.product_name,
            )
            continue

        vending_machine_type: VendingMachineKind = compute_vending_machine_type(vending_machine_code)

        result.append(
            SaleResolvedModel(
                price=sale.price,
                timestamp=sale.timestamp,
                product_code=code,
                vending_machine_code=vending_machine_code,
                vending_machine_type=vending_machine_type,
            )
        )
    return result


__all__ = [
    "resolve_sale_product_code",
    "resolve_sale_vending_machine_code",
    "resolve_sales_with_catalog",
]
