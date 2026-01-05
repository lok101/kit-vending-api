"""
Kit Vending API Client Package

Пакет для работы с API Kit Vending (api2.kit-invest.ru)
"""

from kit_api.client import KitVendingAPIClient
from kit_api.exceptions import (
    KitAPIError,
    KitAPIAuthError,
    KitAPINetworkError,
    KitAPIResponseError,
    KitAPIValidationError,
)
from kit_api.models import (
    MatricesKitCollection,
    ProductsKitCollection,
    SalesKitCollection,
    VendingMachinesCollection,
    RecipesKitCollection,
    ProductKitModel,
    VendingMachineModel,
    SaleKitModel,
    GoodsMatrixKitModel,
    RecipeMatrixKitModel,
    ComboMatrixKitModel,
    RecipeKitModel
)

__version__ = "0.1.0"

__all__ = [
    # Client
    "KitVendingAPIClient",
    # Exceptions
    "KitAPIError",
    "KitAPIAuthError",
    "KitAPINetworkError",
    "KitAPIResponseError",
    "KitAPIValidationError",
    # Models
    "MatricesKitCollection",
    "ProductsKitCollection",
    "SalesKitCollection",
    "VendingMachinesCollection",
    "RecipesKitCollection",
    "ProductKitModel",
    "VendingMachineModel",
    "SaleKitModel",
    "GoodsMatrixKitModel",
    "RecipeMatrixKitModel",
    "ComboMatrixKitModel",
    "RecipeKitModel",
]

