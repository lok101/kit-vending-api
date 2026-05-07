import re
from typing import Annotated

from pydantic import BaseModel, Field, computed_field

from kit_api.enums import VendingMachineActivityStatus, VendingMachineKind
from kit_api.utils import extract_vending_machine_code, compute_vending_machine_type

_VM_INACTIVE_NAME_RE = re.compile(r"\[\s*[ХхXx]\s*\]")


class VendingMachineModel(BaseModel):
    id: Annotated[int, Field(validation_alias="VendingMachineId")]
    name: Annotated[str, Field(validation_alias="VendingMachineName")]
    matrix_id: Annotated[int | None, Field(validation_alias="GoodsMatrix")]
    company_id: Annotated[int, Field(validation_alias="CompanyId")]

    @computed_field
    @property
    def code(self) -> str | None:
        return extract_vending_machine_code(self.name)

    @computed_field
    @property
    def status(self) -> VendingMachineActivityStatus:
        if _VM_INACTIVE_NAME_RE.search(self.name):
            return VendingMachineActivityStatus.NOT_ACTIVE
        return VendingMachineActivityStatus.ACTIVE

    @computed_field
    @property
    def type(self) -> VendingMachineKind:
        return compute_vending_machine_type(self.code)
