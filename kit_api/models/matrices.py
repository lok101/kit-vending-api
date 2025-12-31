"""
Модели матриц товаров Kit API
"""

from dataclasses import dataclass
from typing import Literal, Union, Annotated
from pydantic import BaseModel, Field, Tag, BeforeValidator


class ProductModel(BaseModel):
    """Модель товара в матрице"""
    name: str
    code: int | None

    @classmethod
    def create(cls, val: str):
        if "|" in val:
            code, name = val.split("|")
            return cls(
                name=name.strip(),
                code=int(code.strip())
            )

        return cls(
            name=val.strip(),
            code=None
        )


class GoodsMatrixCell(BaseModel):
    line_number: Annotated[int, Field(validation_alias="LineNumber")]
    product: Annotated[ProductModel, Field(validation_alias="GoodsName"), BeforeValidator(ProductModel.create)]
    price: Annotated[float, Field(validation_alias="Price2")]
    capacity: Annotated[int | None, Field(validation_alias="MaxCount")]

    def as_dict(self) -> dict[str, int | float | str]:
        return {
            "line_number": self.line_number,
            "price": self.price,
            "capacity": self.capacity,
            "product_code": self.product.code,
            "product_name": self.product.name,
        }


class RecipeMatrixCell(BaseModel):
    line_number: Annotated[int, Field(validation_alias="LineNumber")]
    recipe_id: Annotated[int, Field(validation_alias="FormulationId")]
    price: Annotated[float | None, Field(validation_alias="Price2")]


class MatrixKitModel(BaseModel):
    id: Annotated[int, Field(validation_alias="MatrixId")]
    name: Annotated[str, Field(validation_alias="MatrixName")]


class GoodsMatrixKitModel(MatrixKitModel):
    type: Literal[1] = Field(validation_alias="MatrixType")
    cells: Annotated[list[GoodsMatrixCell], Field(validation_alias="Details")]


class RecipeMatrixKitModel(MatrixKitModel):
    type: Literal[2] = Field(validation_alias="MatrixType")
    cells: Annotated[list[RecipeMatrixCell], Field(validation_alias="Details")]


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
        """Получить только матрицы товаров (тип 1)"""
        return [item for item in self.items if isinstance(item, GoodsMatrixKitModel)]

