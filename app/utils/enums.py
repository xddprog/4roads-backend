from enum import Enum

class CharacteristicTypeEnum(str, Enum):
    SIZE = "Размер"
    MATERIAL = "Материал"
    WEIGHT = "Вес"
    VOLUME = "Объём"
    COLOR = "Цвет"
    BRAND = "Бренд"
