"""
Модели торговых автоматов Kit API
"""

from typing import Annotated

from pydantic import BaseModel, Field


class VendingMachineModel(BaseModel):
    """Модель торгового автомата из Kit API"""
    id: Annotated[int, Field(validation_alias="VendingMachineId")]
    name: Annotated[str, Field(validation_alias="VendingMachineName")]
    matrix_id: Annotated[int | None, Field(validation_alias="GoodsMatrix")]
    number: Annotated[int, Field(validation_alias="AutomatNumber")]


class VendingMachinesCollection(BaseModel):
    """Коллекция торговых автоматов из Kit API"""
    items: Annotated[list[VendingMachineModel], Field(validation_alias="VendingMachines")]

    def get_all(self) -> list[VendingMachineModel]:
        return self.items.copy()
