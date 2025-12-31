"""
Утилиты для работы с датой и временем в форматах Kit API
"""

from datetime import datetime
from zoneinfo import ZoneInfo


class ProjectTime:
    """
    Класс для работы с датами и временем в форматах Kit API
    """
    
    # Часовой пояс по умолчанию
    _project_timezone = ZoneInfo('Europe/Moscow')

    # Формат строки для Kit API
    _KIT_API_DATETIME_FORMAT = "%d.%m.%Y %H:%M:%S"

    @classmethod
    def set_timezone(cls, tz_name: str) -> None:
        """Установка часового пояса проекта"""
        cls._project_timezone = ZoneInfo(tz_name)

    @classmethod
    def datetime_to_str_kit(cls, dt: datetime) -> str:
        """
        Конвертация datetime в строку Kit API.
        Время форматируется в московском часовом поясе.
        
        Args:
            dt: datetime объект для конвертации
            
        Returns:
            str: Строка в формате Kit API (dd.mm.yyyy HH:MM:SS)
        """
        # Убеждаемся, что datetime в московском часовом поясе
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=cls._project_timezone)
        else:
            dt = dt.astimezone(cls._project_timezone)
        # Форматируем (Kit API ожидает московское время)
        return dt.strftime(cls._KIT_API_DATETIME_FORMAT)

    @classmethod
    def datetime_from_str_kit(cls, val: str) -> datetime:
        """
        Парсинг строки Kit API в datetime.
        Время интерпретируется как московское.
        
        Args:
            val: Строка в формате Kit API (dd.mm.yyyy HH:MM:SS)
            
        Returns:
            datetime: datetime объект с московским часовым поясом
        """
        dt = datetime.strptime(val, cls._KIT_API_DATETIME_FORMAT)
        return dt.replace(tzinfo=cls._project_timezone)

