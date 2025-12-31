"""
Модели продаж Kit API
"""

import logging
from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, Field, BeforeValidator

from kit_api.project_time import ProjectTime


class ProductModel(BaseModel):
    """Модель товара в продаже"""
    name: str
    code: int | None

    @classmethod
    def create(cls, val: str):
        splitter = "|"
        if splitter in val:
            code, name = val.split(splitter)
            return cls(
                name=name.strip(),
                code=int(code.strip())
            )

        logging.warning(f"В полученном имени товара не встречен разделитель: \"{val}\"")
        return cls(
            code=None,
            name=val
        )


class SaleKitModel(BaseModel):
    """Модель продажи из Kit API"""
    line: Annotated[int, Field(validation_alias="LineNumber")]
    product: Annotated[ProductModel, Field(validation_alias="GoodsName"), BeforeValidator(ProductModel.create)]
    price: Annotated[float, Field(validation_alias="Sum")]
    timestamp: Annotated[datetime, Field(validation_alias="DateTime"), BeforeValidator(
        ProjectTime.datetime_from_str_kit
    )]
    vm_id: Annotated[int, Field(validation_alias="VendingMachine")]
    vm_name: Annotated[str, Field(validation_alias="VendingMachineName")]
    matrix_id: Annotated[int, Field(validation_alias="MatrixId")]

    def as_dict(self) -> dict:
        """Преобразовать в словарь"""
        return {
            "product_code": self.product.code,
            "product_name": self.product.name,
            "line_number": self.line,
            "matrix_id": self.matrix_id,
            "price": self.price,
            "timestamp": self.timestamp,
        }


class SalesKitCollection(BaseModel):
    """Коллекция продаж из Kit API"""
    items: Annotated[list[SaleKitModel], Field(validation_alias="Sales")]

