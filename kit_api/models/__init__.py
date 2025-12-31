"""
Модели данных для Kit API
"""

from kit_api.models.matrices import (
    MatricesKitCollection,
    GoodsMatrixKitModel,
    RecipeMatrixKitModel,
    ComboMatrixKitModel,
    MatrixKitModel,
    GoodsMatrixCell,
    RecipeMatrixCell,
)
from kit_api.models.products import (
    ProductsKitCollection,
    ProductKitModel,
)
from kit_api.models.sales import (
    SalesKitCollection,
    SaleKitModel,
    ProductModel as SalesProductModel,
)
from kit_api.models.vending_machine import (
    VendingMachinesCollection,
    VendingMachineModel,
    VendingMachineStateModel,
    VendingMachineStatesCollection,
)

__all__ = [
    # Matrices
    "MatricesKitCollection",
    "GoodsMatrixKitModel",
    "RecipeMatrixKitModel",
    "ComboMatrixKitModel",
    "MatrixKitModel",
    "GoodsMatrixCell",
    "RecipeMatrixCell",
    # Products
    "ProductsKitCollection",
    "ProductKitModel",
    # Sales
    "SalesKitCollection",
    "SaleKitModel",
    "SalesProductModel",
    # Vending Machines
    "VendingMachinesCollection",
    "VendingMachineModel",
    "VendingMachineStateModel",
    "VendingMachineStatesCollection",
]

