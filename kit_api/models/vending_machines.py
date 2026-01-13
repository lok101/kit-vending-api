"""
Модели торговых автоматов Kit API
"""

from typing import Annotated, Any

from pydantic import BaseModel, Field, model_validator


class VendingMachineModel(BaseModel):
    """Модель торгового автомата из Kit API"""
    id: Annotated[int, Field(validation_alias="VendingMachineId")]
    name: Annotated[str, Field(validation_alias="VendingMachineName")]
    matrix_id: Annotated[int | None, Field(validation_alias="GoodsMatrix")]
    number: Annotated[int, Field(validation_alias="AutomatNumber")]
    company_id: Annotated[int, Field(validation_alias="CompanyId")]


class ActiveVendingMachineModel(VendingMachineModel):
    terminal_number: Annotated[int, Field(validation_alias="ModemSerialNumber")]


class NotActiveVendingMachineModel(VendingMachineModel):
    terminal_number: Annotated[None, Field(validation_alias="ModemSerialNumber")]


class VendingMachinesCollection(BaseModel):
    """Коллекция торговых автоматов из Kit API"""
    items: Annotated[
        list[ActiveVendingMachineModel | NotActiveVendingMachineModel],
        Field(validation_alias="VendingMachines")
    ]

    @model_validator(mode='before')
    @classmethod
    def _create_typed_models(cls, data: Any) -> Any:
        if isinstance(data, dict) and "VendingMachines" in data:
            machines = []
            for machine_data in data["VendingMachines"]:
                if isinstance(machine_data, dict):
                    modem_serial = machine_data.get("ModemSerialNumber")
                    if modem_serial is not None:
                        machines.append(ActiveVendingMachineModel.model_validate(machine_data))
                    else:
                        machines.append(NotActiveVendingMachineModel.model_validate(machine_data))
                else:
                    machines.append(machine_data)
            data["VendingMachines"] = machines
        return data

    def get_all(self) -> list[VendingMachineModel]:
        return self.items.copy()

    def get_active(self) -> list[ActiveVendingMachineModel]:
        return [item for item in self.items if isinstance(item, ActiveVendingMachineModel)]
