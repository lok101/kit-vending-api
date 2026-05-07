from typing import Annotated

from pydantic import BaseModel, Field, computed_field

from kit_api.utils import extract_product_code


class ProductModel(BaseModel):
    id: Annotated[int, Field(validation_alias="GoodsId")]
    name: Annotated[str, Field(validation_alias="GoodsName")]

    @computed_field
    @property
    def code(self) -> str | None:
        return extract_product_code(self.name)
