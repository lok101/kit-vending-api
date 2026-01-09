from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, Field, BeforeValidator


class BaseSaleModel(BaseModel):
    line: Annotated[int, Field(validation_alias="LineNumber")]
    price: Annotated[float, Field(validation_alias="Sum")]
    timestamp: Annotated[
        datetime,
        Field(validation_alias="DateTime"),
        BeforeValidator(
            lambda val: datetime.strptime(val, "%d.%m.%Y %H:%M:%S")
        )
    ]

    vending_machine_id: Annotated[int, Field(validation_alias="VendingMachine")]
    vending_machine_name: Annotated[str, Field(validation_alias="VendingMachineName")]
    matrix_id: Annotated[int, Field(validation_alias="MatrixId")]


class RecipeDrinkSaleModel(BaseSaleModel):
    recipe_id: Annotated[int, Field(validation_alias="FormulationId")]


class ProductSaleModel(BaseSaleModel):
    product_name: Annotated[str, Field(validation_alias="GoodsName")]


class SalesCollection(BaseModel):
    items: Annotated[list[BaseSaleModel], Field(validation_alias="Sales")]

    def get_product_sales(self) -> list[ProductSaleModel]:
        return [sale for sale in self.items if isinstance(sale, ProductSaleModel)]

    def get_drink_sales(self) -> list[RecipeDrinkSaleModel]:
        return [sale for sale in self.items if isinstance(sale, RecipeDrinkSaleModel)]

    def get_all(self) -> list[BaseSaleModel]:
        return self.items.copy()
