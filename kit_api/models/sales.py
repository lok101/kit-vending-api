"""
Модели продаж Kit API
"""

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
    """Коллекция продаж из Kit API"""
    items: Annotated[list[ProductSaleModel], Field(validation_alias="Sales")]
