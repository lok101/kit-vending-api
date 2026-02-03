from typing import Annotated

from pydantic import BaseModel, Field, BeforeValidator

from kit_api.utils import extract_product_id


class RecipeKitModel(BaseModel):
    """Модель рецепта из Kit API"""
    id: Annotated[int, Field(validation_alias="FormulationId")]
    number: Annotated[int | None, Field(validation_alias="FormulationName"), BeforeValidator(extract_product_id)]
    name: Annotated[str, Field(validation_alias="FormulationName")]


class RecipesKitCollection(BaseModel):
    """Коллекция рецептов из Kit API"""
    items: Annotated[list[RecipeKitModel], Field(validation_alias="Formulations")]

    def get_all(self) -> list[RecipeKitModel]:
        return self.items.copy()
