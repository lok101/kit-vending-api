from typing import Annotated
from pydantic import BaseModel, Field


class ProductModel(BaseModel):
    id: Annotated[int, Field(validation_alias="GoodsId")]
    name: Annotated[str, Field(validation_alias="GoodsName")]
