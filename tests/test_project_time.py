"""
Тесты для ProjectTime
"""

import pytest
from datetime import datetime
from zoneinfo import ZoneInfo

from kit_api.project_time import ProjectTime


class TestProjectTime:
    """Тесты ProjectTime"""

    def test_datetime_to_str_kit_with_timezone(self):
        """Тест конвертации datetime с часовым поясом в строку Kit API"""
        dt = datetime(2024, 1, 15, 12, 30, 45, tzinfo=ZoneInfo('Europe/Moscow'))
        result = ProjectTime.datetime_to_str_kit(dt)
        assert result == "15.01.2024 12:30:45"

    def test_datetime_to_str_kit_without_timezone(self):
        """Тест конвертации datetime без часового пояса в строку Kit API"""
        dt = datetime(2024, 1, 15, 12, 30, 45)
        result = ProjectTime.datetime_to_str_kit(dt)
        # Должно быть преобразовано в московское время
        assert result == "15.01.2024 12:30:45"

    def test_datetime_to_str_kit_different_timezone(self):
        """Тест конвертации datetime из другого часового пояса"""
        dt = datetime(2024, 1, 15, 9, 30, 45, tzinfo=ZoneInfo('UTC'))
        result = ProjectTime.datetime_to_str_kit(dt)
        # UTC+3 (Москва) = 12:30:45
        assert result == "15.01.2024 12:30:45"

    def test_datetime_from_str_kit(self):
        """Тест парсинга строки Kit API в datetime"""
        date_str = "15.01.2024 12:30:45"
        result = ProjectTime.datetime_from_str_kit(date_str)

        assert isinstance(result, datetime)
        assert result.year == 2024
        assert result.month == 1
        assert result.day == 15
        assert result.hour == 12
        assert result.minute == 30
        assert result.second == 45
        assert result.tzinfo == ZoneInfo('Europe/Moscow')

    def test_datetime_from_str_kit_roundtrip(self):
        """Тест обратного преобразования (туда-обратно)"""
        original_dt = datetime(2024, 1, 15, 12, 30, 45, tzinfo=ZoneInfo('Europe/Moscow'))
        str_repr = ProjectTime.datetime_to_str_kit(original_dt)
        parsed_dt = ProjectTime.datetime_from_str_kit(str_repr)

        assert parsed_dt == original_dt

    def test_set_timezone(self):
        """Тест установки часового пояса"""
        original_tz = ProjectTime._project_timezone

        try:
            ProjectTime.set_timezone('UTC')
            assert ProjectTime._project_timezone == ZoneInfo('UTC')

            dt = datetime(2024, 1, 15, 12, 30, 45)
            result = ProjectTime.datetime_to_str_kit(dt)
            # Должно быть в UTC
            assert result == "15.01.2024 12:30:45"
        finally:
            # Восстанавливаем исходный часовой пояс
            ProjectTime._project_timezone = original_tz

    def test_datetime_to_str_kit_edge_cases(self):
        """Тест граничных случаев для конвертации"""
        # Начало дня
        dt = datetime(2024, 1, 1, 0, 0, 0, tzinfo=ZoneInfo('Europe/Moscow'))
        result = ProjectTime.datetime_to_str_kit(dt)
        assert result == "01.01.2024 00:00:00"

        # Конец дня
        dt = datetime(2024, 12, 31, 23, 59, 59, tzinfo=ZoneInfo('Europe/Moscow'))
        result = ProjectTime.datetime_to_str_kit(dt)
        assert result == "31.12.2024 23:59:59"

    def test_datetime_from_str_kit_edge_cases(self):
        """Тест граничных случаев для парсинга"""
        # Начало дня
        date_str = "01.01.2024 00:00:00"
        result = ProjectTime.datetime_from_str_kit(date_str)
        assert result.hour == 0
        assert result.minute == 0
        assert result.second == 0

        # Конец дня
        date_str = "31.12.2024 23:59:59"
        result = ProjectTime.datetime_from_str_kit(date_str)
        assert result.hour == 23
        assert result.minute == 59
        assert result.second == 59

