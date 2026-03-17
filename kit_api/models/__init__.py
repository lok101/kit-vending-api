"""
Модели данных для Kit API
"""

from kit_api.models.common import ProductModel
from kit_api.models.matrices import (
    MatricesKitCollection,
    GoodsMatrixKitModel,
    RecipeMatrixKitModel,
    ComboMatrixKitModel,
    MatrixKitModel,
    GoodsCell,
    RecipeCell,
)
from kit_api.models.products import (
    ProductsKitCollection,
    ProductKitModel,
)
from kit_api.models.recipes import (
    RecipesKitCollection,
    RecipeKitModel,
)
from kit_api.models.sales import (
    SalesCollection,
    SaleModel
)
from kit_api.models.vending_machines import (
    VendingMachineModel,
)

__all__ = [
    # Common
    "ProductModel",
    # Matrices
    "MatricesKitCollection",
    "GoodsMatrixKitModel",
    "RecipeMatrixKitModel",
    "ComboMatrixKitModel",
    "MatrixKitModel",
    "GoodsCell",
    "RecipeCell",
    # Products
    "ProductsKitCollection",
    "ProductKitModel",
    # Recipes
    "RecipesKitCollection",
    "RecipeKitModel",
    # Sales
    "SalesCollection",
    "SaleModel",
    # Vending Machines
    "VendingMachineModel",
]
