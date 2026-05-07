import re

from kit_api.enums import VendingMachineStatus, VendingMachineKind

_PRODUCT_NAME_PLACEHOLDER = re.compile(r"Товар\s+\d+")
_PRODUCT_PLACEHOLDER_CAPTURE = re.compile(r"Товар\s+(\d+)")
_PRODUCT_ZERO_PLACEHOLDER = re.compile(r"Товар\s+0")
_VM_CODE_RE = re.compile(r"\[(\d{3})\]")


def is_product_name_placeholder(name: str) -> bool:
    """Имя вида «Товар <номер>», когда товар в продаже не удалось определить по названию."""
    return bool(_PRODUCT_NAME_PLACEHOLDER.fullmatch(name.strip()))


def is_product_zero_placeholder(name: str) -> bool:
    """Плейсхолдер «Товар 0» — недопустимая позиция, отдельно от остальных «Товар N»."""
    return bool(_PRODUCT_ZERO_PLACEHOLDER.fullmatch(name.strip()))


def try_product_code_from_placeholder_name(name: str) -> str | None:
    """Если имя — плейсхолдер «Товар N», а N — ровно 4 цифры и начинается с «2», вернуть N как код товара.

    Используется, когда MatrixId отсутствует или матрица не пришла в GetGoodsMatrices, но номер
    на самом деле совпадает с кодом товара в учётной системе (например 2311, 2101).
    """
    m = _PRODUCT_PLACEHOLDER_CAPTURE.fullmatch(name.strip())
    if not m:
        return None
    digits = m.group(1)
    if len(digits) == 4 and digits.startswith("2"):
        return digits
    return None


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


def extract_product_code(product_name: str) -> str | None:
    if "|" not in product_name:
        return None

    left, _ = product_name.split("|", 1)
    left_stripped = left.strip()

    if left_stripped.isdigit():
        return left_stripped

    return None


def extract_vending_machine_code(vending_machine_name: str) -> str | None:
    m = _VM_CODE_RE.search(vending_machine_name)
    return m.group(1) if m else None


def compute_vending_machine_type(vending_machine_code: str | None) -> VendingMachineKind:
    if vending_machine_code is None:
        return VendingMachineKind.NOT_DEFINED
    if vending_machine_code.startswith("5"):
        return VendingMachineKind.SNACK
    return VendingMachineKind.COFFEE
