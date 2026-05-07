from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, computed_field

from kit_api.utils import extract_product_code


class BaseMatrixCell(BaseModel):
    line_number: Annotated[int, Field(validation_alias="LineNumber")]
    price: Annotated[float | None, Field(validation_alias="Price2")]


class GoodsCell(BaseMatrixCell):
    product_name: Annotated[str, Field(validation_alias="GoodsName")]
    capacity: Annotated[int | None, Field(validation_alias="MaxCount")]

    @computed_field
    @property
    def product_code(self) -> str | None:
        return extract_product_code(self.product_name)


class RecipeCell(BaseMatrixCell):
    recipe_id: Annotated[int, Field(validation_alias="FormulationId")]


class RecipeCodeCell(BaseMatrixCell):
    model_config = ConfigDict(populate_by_name=True)

    recipe_id: int
    recipe_code: str | None
