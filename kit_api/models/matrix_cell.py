from typing import Annotated

from pydantic import BaseModel, Field, computed_field


class BaseMatrixCell(BaseModel):
    line_number: Annotated[int, Field(validation_alias="LineNumber")]
    price: Annotated[float | None, Field(validation_alias="Price2")]


class GoodsCell(BaseMatrixCell):
    product_name: Annotated[str, Field(validation_alias="GoodsName")]
    capacity: Annotated[int | None, Field(validation_alias="MaxCount")]

    @computed_field
    @property
    def product_code(self) -> str | None:
        if "|" not in self.product_name:
            return None
        left, _ = self.product_name.split("|", 1)
        left_stripped = left.strip()
        if left_stripped.isdigit():
            return left_stripped
        return None



class RecipeCell(BaseMatrixCell):
    recipe_id: Annotated[int, Field(validation_alias="FormulationId")]
