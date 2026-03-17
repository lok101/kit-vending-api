from datetime import datetime
from zoneinfo import ZoneInfo


class LibDateTime:
    _project_timezone: ZoneInfo = ZoneInfo('Asia/Yekaterinburg')

    _KIT_API_DATETIME_FORMAT = "%d.%m.%Y %H:%M:%S"

    @classmethod
    def set_timezone(cls, tz_name: str) -> None:
        cls._project_timezone = ZoneInfo(tz_name)

    @classmethod
    def datetime_to_str_kit(cls, dt: datetime) -> str:
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=cls._project_timezone)
        else:
            dt = dt.astimezone(cls._project_timezone)
        return dt.strftime(cls._KIT_API_DATETIME_FORMAT)

    @classmethod
    def datetime_from_str_kit(cls, val: str) -> datetime:
        dt = datetime.strptime(val, cls._KIT_API_DATETIME_FORMAT)
        return dt.replace(tzinfo=cls._project_timezone)
