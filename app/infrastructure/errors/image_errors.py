from fastapi import HTTPException, status


class ImageError(HTTPException):
    """Базовая ошибка для работы с изображениями"""
    def __init__(self, detail: str):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


class InvalidImageType(ImageError):
    """Неверный тип файла"""
    def __init__(self):
        super().__init__(detail="Файл должен быть изображением")


class InvalidImageFormat(ImageError):
    """Неподдерживаемый формат изображения"""
    def __init__(self, allowed_formats: str):
        super().__init__(
            detail=f"Неподдерживаемый формат. Разрешены: {allowed_formats}"
        )


class ImageTooLarge(ImageError):
    """Файл слишком большой"""
    def __init__(self, max_size_mb: int):
        super().__init__(
            detail=f"Файл слишком большой. Максимальный размер: {max_size_mb}MB"
        )


class EmptyImageFile(ImageError):
    """Пустой файл"""
    def __init__(self):
        super().__init__(detail="Файл пустой")


class ImageProcessingError(ImageError):
    """Ошибка обработки изображения"""
    def __init__(self, error_message: str):
        super().__init__(detail=f"Не удалось обработать изображение: {error_message}")

