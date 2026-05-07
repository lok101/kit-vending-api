"""
Тесты для LibDateTime (проектный часовой пояс по умолчанию — Asia/Yekaterinburg).
"""

from datetime import datetime
from zoneinfo import ZoneInfo

from kit_api.project_time import LibDateTime

_TZ_EKB = ZoneInfo("Asia/Yekaterinburg")


class TestProjectTime:
    """Тесты LibDateTime"""

    def test_datetime_to_str_kit_with_timezone(self) -> None:
        """aware datetime приводится к проектному поясу перед форматированием."""
        dt = datetime(2024, 1, 15, 12, 30, 45, tzinfo=ZoneInfo("Europe/Moscow"))
        result = LibDateTime.datetime_to_str_kit(dt)
        assert result == "15.01.2024 14:30:45"

    def test_datetime_to_str_kit_without_timezone(self) -> None:
        """naive datetime считается временем в проектном поясе."""
        dt = datetime(2024, 1, 15, 12, 30, 45)
        result = LibDateTime.datetime_to_str_kit(dt)
        assert result == "15.01.2024 12:30:45"

    def test_datetime_to_str_kit_different_timezone(self) -> None:
        """Конвертация из UTC в проектный пояс."""
        dt = datetime(2024, 1, 15, 9, 30, 45, tzinfo=ZoneInfo("UTC"))
        result = LibDateTime.datetime_to_str_kit(dt)
        assert result == "15.01.2024 14:30:45"

    def test_datetime_from_str_kit(self) -> None:
        """Парсинг строки Kit API — tzinfo проекта."""
        date_str = "15.01.2024 12:30:45"
        result = LibDateTime.datetime_from_str_kit(date_str)

        assert isinstance(result, datetime)
        assert result.year == 2024
        assert result.month == 1
        assert result.day == 15
        assert result.hour == 12
        assert result.minute == 30
        assert result.second == 45
        assert result.tzinfo == _TZ_EKB

    def test_datetime_from_str_kit_roundtrip(self) -> None:
        """Туда-обратно для момента в проектном поясе."""
        original_dt = datetime(2024, 1, 15, 12, 30, 45, tzinfo=_TZ_EKB)
        str_repr = LibDateTime.datetime_to_str_kit(original_dt)
        parsed_dt = LibDateTime.datetime_from_str_kit(str_repr)

        assert parsed_dt == original_dt

    def test_set_timezone(self) -> None:
        """Смена проектного пояса через set_timezone."""
        original_tz = LibDateTime._project_timezone

        try:
            LibDateTime.set_timezone("UTC")
            assert LibDateTime._project_timezone == ZoneInfo("UTC")

            dt = datetime(2024, 1, 15, 12, 30, 45)
            result = LibDateTime.datetime_to_str_kit(dt)
            assert result == "15.01.2024 12:30:45"
        finally:
            LibDateTime._project_timezone = original_tz

    def test_datetime_to_str_kit_edge_cases(self) -> None:
        """Граничные значения в проектном поясе (naive = Екатеринбург)."""
        dt = datetime(2024, 1, 1, 0, 0, 0)
        result = LibDateTime.datetime_to_str_kit(dt)
        assert result == "01.01.2024 00:00:00"

        dt = datetime(2024, 12, 31, 23, 59, 59)
        result = LibDateTime.datetime_to_str_kit(dt)
        assert result == "31.12.2024 23:59:59"

    def test_datetime_from_str_kit_edge_cases(self) -> None:
        """Граничные значения при разборе строки."""
        date_str = "01.01.2024 00:00:00"
        result = LibDateTime.datetime_from_str_kit(date_str)
        assert result.hour == 0
        assert result.minute == 0
        assert result.second == 0

        date_str = "31.12.2024 23:59:59"
        result = LibDateTime.datetime_from_str_kit(date_str)
        assert result.hour == 23
        assert result.minute == 59
        assert result.second == 59
