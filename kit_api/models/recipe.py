from typing import Annotated

from pydantic import BaseModel, Field, BeforeValidator, computed_field

from kit_api.utils import extract_product_id


class RecipeModel(BaseModel):
    id: Annotated[int, Field(validation_alias="FormulationId")]
    number: Annotated[int | None, Field(validation_alias="FormulationName"), BeforeValidator(extract_product_id)]
    name: Annotated[str, Field(validation_alias="FormulationName")]

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


