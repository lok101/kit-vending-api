import re


def extract_vending_machine_id(vending_machine_name: str) -> int | None:
    pattern = r'\[(\d+)\]'
    match = re.search(pattern, vending_machine_name)
    if match:
        return int(match.group(1))
    return None

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
