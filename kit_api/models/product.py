from typing import Annotated

from pydantic import BaseModel, Field, computed_field


class ProductModel(BaseModel):
    id: Annotated[int, Field(validation_alias="GoodsId")]
    name: Annotated[str, Field(validation_alias="GoodsName")]

    @computed_field
    @property
    def code(self) -> str | None:
        if "|" not in self.name:
            return None
        left, _ = self.name.split("|", 1)
        left_stripped = left.strip()
        if left_stripped.isdigit():
            return left_stripped
        return None
