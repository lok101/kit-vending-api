import re

from kit_api.enums import VendingMachineStatus


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


# def extract_vending_machine_id(vending_machine_name: str) -> int | None:
#     pattern = r'\[(\d+)\]'
#     match = re.search(pattern, vending_machine_name)
#     if match:
#         return int(match.group(1))
#     return None


def extract_product_id(product_name: str) -> int | None:
    pattern = r'(\d+) |]'
    match = re.search(pattern, product_name)
    if match:
        return int(match.group(1))
    return None


def extract_status(vending_machine_name: str) -> bool:
    if "тест" in vending_machine_name.lower():
        return False
    pattern = r'^\[ X \]'
    match = re.match(pattern, vending_machine_name, re.IGNORECASE)
    if match:
        return False
    return True
