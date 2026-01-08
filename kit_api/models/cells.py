from typing import Annotated

from pydantic import BaseModel, Field


class BaseMatrixCell(BaseModel):
    line_number: Annotated[int, Field(validation_alias="LineNumber")]
    price: Annotated[float | None, Field(validation_alias="Price2")]


class GoodsCell(BaseMatrixCell):
    product_name: Annotated[str, Field(validation_alias="GoodsName")]
    capacity: Annotated[int | None, Field(validation_alias="MaxCount")]


class RecipeCell(BaseMatrixCell):
    recipe_id: Annotated[int, Field(validation_alias="FormulationId")]
