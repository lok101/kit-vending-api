from typing import Annotated

from pydantic import BaseModel, Field


class VendingMachineModel(BaseModel):
    id: Annotated[int, Field(validation_alias="VendingMachineId")]
    name: Annotated[str, Field(validation_alias="VendingMachineName")]
    matrix_id: Annotated[int | None, Field(validation_alias="GoodsMatrix")]
    company_id: Annotated[int, Field(validation_alias="CompanyId")]
    terminal_number: Annotated[int | None, Field(validation_alias="ModemSerialNumber")]
