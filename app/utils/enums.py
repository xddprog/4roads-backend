from enum import Enum

class CharacteristicTypeEnum(str, Enum):
    SIZE = "Размер"
    WIDTH = "Ширина"
    HEIGHT = "Высота"
    DEPTH = "Глубина"
    WEIGHT = "Вес"
    DIAMETER = "Диаметр"
    LENGTH = "Длина"
    VOLUME = "Объём"
    MATERIAL = "Материал"
    COLOR = "Цвет"


class OrderStatusEnum(str, Enum):
    NEW = "Новая"
    IN_PROGRESS = "В работе"
    DONE = "Завершена"
    CANCELED = "Отменена"
