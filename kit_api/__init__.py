"""
Kit Vending API Client Package

Пакет для работы с API Kit Vending (api2.kit-invest.ru)
"""

from kit_api.client import KitVendingAPIClient
from kit_api.models import (
    MatricesKitCollection,
    ProductsKitCollection,
    SalesKitCollection,
    VendingMachinesCollection,
    ProductKitModel,
    VendingMachineModel,
    SaleKitModel,
    GoodsMatrixKitModel,
    RecipeMatrixKitModel,
    ComboMatrixKitModel,
)

__version__ = "0.1.0"

__all__ = [
    "KitVendingAPIClient",
    "MatricesKitCollection",
    "ProductsKitCollection",
    "SalesKitCollection",
    "VendingMachinesCollection",
    "ProductKitModel",
    "VendingMachineModel",
    "SaleKitModel",
    "GoodsMatrixKitModel",
    "RecipeMatrixKitModel",
    "ComboMatrixKitModel",
]

