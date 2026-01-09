"""
Модели товаров Kit API
"""

from typing import Annotated
from pydantic import BaseModel, Field


class ProductKitModel(BaseModel):
    """Модель товара из Kit API"""
    id: Annotated[int, Field(validation_alias="GoodsId")]
    name: Annotated[str, Field(validation_alias="GoodsName")]


class ProductsKitCollection(BaseModel):
    """Коллекция товаров из Kit API"""
    items: Annotated[list[ProductKitModel], Field(validation_alias="Goods")]

    def get_all(self) -> list[ProductKitModel]:
        return self.items.copy()
