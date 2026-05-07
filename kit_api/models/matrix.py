from typing import Literal, Union, Annotated, cast
from pydantic import BaseModel, Field, Tag

from kit_api.models.matrix_cell import GoodsCell, BaseMatrixCell, RecipeCell, RecipeCodeCell


class MatrixModel(BaseModel):
    id: Annotated[int, Field(validation_alias="MatrixId")]
    name: Annotated[str, Field(validation_alias="MatrixName")]
    cells: Annotated[list[BaseMatrixCell], Field(validation_alias="Details")]


class GoodsMatrixModel(MatrixModel):
    type: Literal[1] = Field(validation_alias="MatrixType")
    cells: Annotated[list[GoodsCell], Field(validation_alias="Details")]  # type: ignore[assignment]


class RecipeMatrixModel(MatrixModel):
    type: Literal[2] = Field(validation_alias="MatrixType")
    cells: Annotated[list[RecipeCell], Field(validation_alias="Details")]  # type: ignore[assignment]


class RecipeCodeMatrixModel(BaseModel):
    id: int
    name: str
    type: Literal[2] = 2
    cells: list[RecipeCodeCell]


class ComboMatrixModel(MatrixModel):
    type: Literal[3] = Field(validation_alias="MatrixType")


MatrixType = Annotated[
    Union[
        Annotated[GoodsMatrixModel, Tag(1)],  # pyright: ignore[reportArgumentType]
        Annotated[RecipeMatrixModel, Tag(2)],  # pyright: ignore[reportArgumentType]
        Annotated[ComboMatrixModel, Tag(3)],  # pyright: ignore[reportArgumentType]
    ],
    Field(discriminator="type")
]


class MatricesKitCollection(BaseModel):
    items: Annotated[list[MatrixType], Field(validation_alias="GoodsMatrices")]

    def get_snack_matrices(self) -> list[GoodsMatrixModel]:
        return [item for item in self.items if isinstance(item, GoodsMatrixModel)]

    def get_recipes_matrices(self) -> list[RecipeMatrixModel]:
        return [item for item in self.items if isinstance(item, RecipeMatrixModel)]

    def get_all_matrices(self) -> list[MatrixModel]:
        return cast(list[MatrixModel], self.items.copy())


__all__ = [
    "ComboMatrixModel",
    "GoodsMatrixModel",
    "MatricesKitCollection",
    "MatrixModel",
    "MatrixType",
    "RecipeCodeMatrixModel",
    "RecipeMatrixModel",
    "GoodsCell",
    "RecipeCell",
    "RecipeCodeCell",
]
