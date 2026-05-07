import re

from kit_api.enums import VendingMachineStatus

_PRODUCT_NAME_PLACEHOLDER = re.compile(r"Товар\s+\d+")
_VM_CODE_RE = re.compile(r"\[(\d{3})\]")


def is_product_name_placeholder(name: str) -> bool:
    """Имя вида «Товар <номер>», когда товар в продаже не удалось определить по названию."""
    return bool(_PRODUCT_NAME_PLACEHOLDER.fullmatch(name.strip()))


def extract_statuses(statuses_str: str) -> list[VendingMachineStatus]:
    res: list[VendingMachineStatus] = []

    if statuses_str:
        statuses: list[str] = statuses_str.split(',')

        for status in statuses:

            try:
                int_status: int = int(status)
                enum_status: VendingMachineStatus = VendingMachineStatus(int_status)
                res.append(enum_status)

            except ValueError:
                continue

    return res


def extract_product_code(product_name: str):
    if "|" not in product_name:
        return None

    left, _ = product_name.split("|", 1)
    left_stripped = left.strip()

    if left_stripped.isdigit():
        return left_stripped

    return None


def extract_vending_machine_code(vending_machine_name: str):
    m = _VM_CODE_RE.search(vending_machine_name)
    return m.group(1) if m else None
