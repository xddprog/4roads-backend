from fastapi import HTTPException, status


class InvalidImageType(HTTPException):
    status_code = status.HTTP_400_BAD_REQUEST
    detail = "Файл должен быть изображением"
    
    def __init__(self):
        super().__init__(
            status_code=self.status_code,
            detail=self.detail
        )


class InvalidImageFormat(HTTPException):
    status_code = status.HTTP_400_BAD_REQUEST
    detail = "Неподдерживаемый формат изображения"
    
    def __init__(self, allowed_formats: str):
        super().__init__(
            status_code=self.status_code,
            detail=f"Неподдерживаемый формат. Разрешены: {allowed_formats}"
        )


class ImageTooLarge(HTTPException):
    status_code = status.HTTP_400_BAD_REQUEST
    detail = "Файл слишком большой"
    
    def __init__(self, max_size_mb: int):
        super().__init__(
            status_code=self.status_code,
            detail=f"Файл слишком большой. Максимальный размер: {max_size_mb}MB"
        )


class EmptyImageFile(HTTPException):
    status_code = status.HTTP_400_BAD_REQUEST
    detail = "Файл пустой"
    
    def __init__(self):
        super().__init__(
            status_code=self.status_code,
            detail=self.detail
        )


class ImageProcessingError(HTTPException):
    status_code = status.HTTP_400_BAD_REQUEST
    detail = "Ошибка обработки изображения"
    
    def __init__(self, error_message: str):
        super().__init__(
            status_code=self.status_code,
            detail=f"Не удалось обработать изображение: {error_message}"
        )
