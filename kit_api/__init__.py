from kit_api.client import KitAPIAccount, KitVendingAPIClient
from kit_api.enums import ResultCode, VendingMachineCommand
from kit_api.exceptions import (
    KitAPIError,
    KitAPIAuthError,
    KitAPINetworkError,
    KitAPIResponseError,
    KitAPIValidationError,
    SaleProductCodeResolveCriticalError,
    SaleProductCodeResolveError,
    SaleProductCodeResolveNonCriticalError,
)
from kit_api.models import (
    MatricesKitCollection,
    ProductModel,
    VendingMachineModel,
    GoodsMatrixModel,
    RecipeMatrixModel,
    RecipeCodeMatrixModel,
    ComboMatrixModel,
    RecipeCodeCell,
    RecipeModel,
    SaleModel,
    SaleResolvedModel,
    VendingMachineStateModel,
)
from kit_api.sale_resolve import (
    resolve_sale_product_code,
    resolve_sale_vending_machine_code,
    resolve_sales_with_catalog,
)

__version__ = "0.1.0"

__all__ = [
    # enums
    "ResultCode",
    "VendingMachineCommand",

    # Client
    "KitAPIAccount",
    "KitVendingAPIClient",
    # Exceptions
    "KitAPIError",
    "KitAPIAuthError",
    "KitAPINetworkError",
    "KitAPIResponseError",
    "KitAPIValidationError",
    "SaleProductCodeResolveCriticalError",
    "SaleProductCodeResolveError",
    "SaleProductCodeResolveNonCriticalError",
    # Sale resolution
    "resolve_sale_product_code",
    "resolve_sale_vending_machine_code",
    "resolve_sales_with_catalog",
    # Models
    "MatricesKitCollection",
    "ProductModel",
    "VendingMachineModel",
    "GoodsMatrixModel",
    "RecipeMatrixModel",
    "RecipeCodeMatrixModel",
    "ComboMatrixModel",
    "RecipeCodeCell",
    "RecipeModel",
    "SaleModel",
    "SaleResolvedModel",
    "VendingMachineStateModel",
]
