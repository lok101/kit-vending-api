from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, Field, BeforeValidator, computed_field

from kit_api.project_time import LibDateTime
from kit_api.utils import extract_product_code


class SaleModel(BaseModel):
    line: Annotated[int, Field(validation_alias="LineNumber")]
    price: Annotated[float, Field(validation_alias="Sum")]
    timestamp: Annotated[
        datetime,
        Field(validation_alias="DateTime"),
        BeforeValidator(
            lambda val: LibDateTime.datetime_from_str_kit(val)
        )
    ]
    product_name: Annotated[str, Field(validation_alias="GoodsName")]

    vending_machine_id: Annotated[int, Field(validation_alias="VendingMachine")]
    vending_machine_name: Annotated[str, Field(validation_alias="VendingMachineName")]
    matrix_id: Annotated[
        int | None,
        Field(validation_alias="MatrixId"),
        BeforeValidator(lambda val: int(val) if val else None)
    ]

    @computed_field
    @property
    def product_code(self) -> str | None:
        return extract_product_code(self.product_name)


class SaleResolvedModel(BaseModel):
    """Продажа с разрешённым кодом товара (без полного набора полей SaleModel)."""

    price: float
    timestamp: datetime
    product_code: str
    vending_machine_code: str
