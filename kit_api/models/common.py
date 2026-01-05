"""
Общие модели для Kit API
"""

import logging
from pydantic import BaseModel


class ProductModel(BaseModel):
    """Модель товара"""
    name: str
    code: int | None

    @classmethod
    def create(cls, val: str):
        """
        Создать модель товара из строки формата "code|name" или просто "name"
        
        Args:
            val: Строка с информацией о товаре
            
        Returns:
            ProductModel: Экземпляр модели товара
        """
        splitter = "|"
        if splitter in val:
            try:
                code_str, name = val.split(splitter, 1)
                code_str = code_str.strip()
                name = name.strip()
                
                try:
                    code = int(code_str) if code_str else None
                except ValueError:
                    logging.warning(
                        f"Не удалось преобразовать код товара в число: '{code_str}'. "
                        f"Исходная строка: \"{val}\""
                    )
                    code = None
                
                return cls(name=name, code=code)
            except ValueError as e:
                logging.warning(
                    f"Ошибка при разборе строки товара: {e}. Исходная строка: \"{val}\""
                )
                return cls(name=val.strip(), code=None)

        logging.warning(
            f"В полученном имени товара не встречен разделитель: \"{val}\""
        )
        return cls(name=val.strip(), code=None)

