from typing import Literal, Union, Annotated
from pydantic import BaseModel, Field, Tag

from kit_api.models.matrix_cell import GoodsCell, BaseMatrixCell, RecipeCell, RecipeCodeCell


class MatrixModel(BaseModel):
    id: Annotated[int, Field(validation_alias="MatrixId")]
    name: Annotated[str, Field(validation_alias="MatrixName")]
    cells: Annotated[list[BaseMatrixCell], Field(validation_alias="Details")]


class GoodsMatrixModel(MatrixModel):
    type: Literal[1] = Field(validation_alias="MatrixType")
    cells: Annotated[list[GoodsCell], Field(validation_alias="Details")]


class RecipeMatrixModel(MatrixModel):
    type: Literal[2] = Field(validation_alias="MatrixType")
    cells: Annotated[list[RecipeCell], Field(validation_alias="Details")]


class RecipeCodeMatrixModel(BaseModel):
    id: int
    name: str
    type: Literal[2] = 2
    cells: list[RecipeCodeCell]


class ComboMatrixModel(MatrixModel):
    type: Literal[3] = Field(validation_alias="MatrixType")


MatrixType = Annotated[
    Union[
        Annotated[GoodsMatrixModel, Tag(1)],
        Annotated[RecipeMatrixModel, Tag(2)],
        Annotated[ComboMatrixModel, Tag(3)],
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
        return self.items.copy()
