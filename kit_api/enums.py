from enum import IntEnum


class ResultCode(IntEnum):
    SUCCESS = 0
    TOO_MANY_REQUEST = 27


class VendingMachineCommand(IntEnum):
    LOAD_MATRIX = 3
    APPLY_MATRIX = 4
