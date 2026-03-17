from typing import Literal, Union, Annotated
from pydantic import BaseModel, Field, Tag

from kit_api.models.matrix_cell import GoodsCell, BaseMatrixCell, RecipeCell


class MatrixKitModel(BaseModel):
    id: Annotated[int, Field(validation_alias="MatrixId")]
    name: Annotated[str, Field(validation_alias="MatrixName")]
    cells: Annotated[list[BaseMatrixCell], Field(validation_alias="Details")]


class GoodsMatrixKitModel(MatrixKitModel):
    type: Literal[1] = Field(validation_alias="MatrixType")
    cells: Annotated[list[GoodsCell], Field(validation_alias="Details")]


class RecipeMatrixKitModel(MatrixKitModel):
    type: Literal[2] = Field(validation_alias="MatrixType")
    cells: Annotated[list[RecipeCell], Field(validation_alias="Details")]


class ComboMatrixKitModel(MatrixKitModel):
    type: Literal[3] = Field(validation_alias="MatrixType")


MatrixType = Annotated[
    Union[
        Annotated[GoodsMatrixKitModel, Tag(1)],
        Annotated[RecipeMatrixKitModel, Tag(2)],
        Annotated[ComboMatrixKitModel, Tag(3)],
    ],
    Field(discriminator="type")
]


class MatricesKitCollection(BaseModel):
    items: Annotated[list[MatrixType], Field(validation_alias="GoodsMatrices")]

    def get_snack_matrices(self) -> list[GoodsMatrixKitModel]:
        return [item for item in self.items if isinstance(item, GoodsMatrixKitModel)]

    def get_recipes_matrices(self) -> list[RecipeMatrixKitModel]:
        return [item for item in self.items if isinstance(item, RecipeMatrixKitModel)]

    def get_all_matrices(self) -> list[MatrixKitModel]:
        return self.items.copy()
