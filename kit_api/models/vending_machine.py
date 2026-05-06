import re
from typing import Annotated

from pydantic import BaseModel, Field, computed_field

from kit_api.enums import VendingMachineActivityStatus, VendingMachineKind

_VM_CODE_RE = re.compile(r"\[(\d{3})\]")
_VM_INACTIVE_NAME_RE = re.compile(r"\[\s*[ХхXx]\s*\]")


class VendingMachineModel(BaseModel):
    id: Annotated[int, Field(validation_alias="VendingMachineId")]
    name: Annotated[str, Field(validation_alias="VendingMachineName")]
    matrix_id: Annotated[int | None, Field(validation_alias="GoodsMatrix")]
    company_id: Annotated[int, Field(validation_alias="CompanyId")]

    @computed_field
    @property
    def code(self) -> str | None:
        m = _VM_CODE_RE.search(self.name)
        return m.group(1) if m else None

    @computed_field
    @property
    def status(self) -> VendingMachineActivityStatus:
        if _VM_INACTIVE_NAME_RE.search(self.name):
            return VendingMachineActivityStatus.NOT_ACTIVE
        return VendingMachineActivityStatus.ACTIVE

    @computed_field
    @property
    def type(self) -> VendingMachineKind:
        c = self.code
        if c is None:
            return VendingMachineKind.NOT_DEFINED
        if f"{c:03d}".startswith("5"):
            return VendingMachineKind.SNACK
        return VendingMachineKind.COFFEE
