from typing import Annotated

from pydantic import BaseModel, Field, BeforeValidator

from kit_api.utils import extract_product_id


class RecipeModel(BaseModel):
    id: Annotated[int, Field(validation_alias="FormulationId")]
    number: Annotated[int | None, Field(validation_alias="FormulationName"), BeforeValidator(extract_product_id)]
    name: Annotated[str, Field(validation_alias="FormulationName")]
