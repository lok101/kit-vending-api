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

    def get_snack_machines(self) -> list[VendingMachineModel]:
        """Получить только снэк-автоматы (номера начинаются с 5)"""
        return [item for item in self.items if str(item.number).startswith("5")]


class VendingMachineStateModel(BaseModel):
    """Модель состояния торгового автомата"""
    id: Annotated[int, Field(validation_alias="VendingMachineId")]


class VendingMachineStatesCollection(BaseModel):
    """Коллекция состояний торговых автоматов"""
    items: Annotated[list[VendingMachineStateModel], Field(validation_alias="VendingMachines")]

