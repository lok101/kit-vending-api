from enum import Enum, IntEnum


class ResultCode(IntEnum):
    SUCCESS = 0
    TOO_MANY_REQUEST = 27


class VendingMachineCommand(IntEnum):
    LOAD_MATRIX = 3
    APPLY_MATRIX = 4


class VendingMachineStatus(IntEnum):
    MATRIX_LOADED = 21
    NO_CONNECTION = 1


class VendingMachineActivityStatus(str, Enum):
    """Статус отображения ТА в списке: пометка «X» в названии — неактивен."""

    ACTIVE = "active"
    NOT_ACTIVE = "not_active"


class VendingMachineKind(str, Enum):
    """Тип линейки автомата по коду в названии ([5xx] — снековый)."""

    NOT_DEFINED = "not_defined"
    SNACK = "snack"
    COFFEE = "coffee"
