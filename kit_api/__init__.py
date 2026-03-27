from kit_api.client import KitVendingAPIClient
from kit_api.enums import ResultCode, VendingMachineCommand
from kit_api.exceptions import (
    KitAPIError,
    KitAPIAuthError,
    KitAPINetworkError,
    KitAPIResponseError,
    KitAPIValidationError,
)
from kit_api.models import (
    MatricesKitCollection,
    ProductModel,
    VendingMachineModel,
    GoodsMatrixModel,
    RecipeMatrixModel,
    ComboMatrixModel,
    RecipeModel, SaleModel
)

__version__ = "0.1.0"

__all__ = [
    # enums
    "ResultCode",
    "VendingMachineCommand",

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
    "ProductModel",
    "VendingMachineModel",
    "GoodsMatrixModel",
    "RecipeMatrixModel",
    "ComboMatrixModel",
    "RecipeModel",
    "SaleModel",
]
