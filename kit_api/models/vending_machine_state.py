from typing import Annotated

from pydantic import BaseModel, Field, BeforeValidator

from kit_api.enums import VendingMachineStatus
from kit_api.utils import extract_statuses


class VendingMachineStateModel(BaseModel):
    id: Annotated[int, Field(validation_alias="VendingMachineId")]
    statuses: Annotated[
        list[VendingMachineStatus],
        Field(validation_alias="Statuses"),
        BeforeValidator(extract_statuses)
    ]


class VendingMachinesStatesCollection(BaseModel):
    items: Annotated[list[VendingMachineStateModel], Field(validation_alias="VendingMachines")]

    def get_all(self) -> list[VendingMachineStateModel]:
        return self.items.copy()

    def as_map(self) -> dict[int, VendingMachineStateModel]:
        return {item.id: item for item in self.items}
