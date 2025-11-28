import io
import uuid
from pathlib import Path
import asyncio

from PIL import Image
from fastapi import UploadFile

from app.infrastructure.config.config import APP_CONFIG
from app.infrastructure.errors.image_errors import (
    InvalidImageType,
    InvalidImageFormat,
    ImageTooLarge,
    EmptyImageFile,
    ImageProcessingError
)


class ImageService:
    """Асинхронный сервис для работы с изображениями"""
    
    def __init__(self):
        Path(APP_CONFIG.IMAGES_DIR).mkdir(parents=True, exist_ok=True)
    
    async def upload_and_convert(
        self, 
        file: UploadFile, 
        subfolder: str = "products"
    ) -> str:
        await self._validate_file(file)
        contents = await file.read()
        await file.seek(0)
        
        images_dir = Path(APP_CONFIG.IMAGES_DIR)
        target_dir = images_dir / subfolder
        target_dir.mkdir(parents=True, exist_ok=True)
        
        filename = f"{uuid.uuid4()}.webp"
        filepath = target_dir / filename
        
        await asyncio.to_thread(
            self._convert_and_save,
            contents,
            filepath
        )
        
        return f"{subfolder}/{filename}"
    
    def _convert_and_save(self, contents: bytes, filepath: Path) -> None:
        try:
            image = Image.open(io.BytesIO(contents))
            
            image = self._convert_to_rgb(image)
            
            image.save(
                filepath,
                "WEBP",
                quality=APP_CONFIG.WEBP_QUALITY,
                method=6,
                optimize=True
            )
            
        except Exception as e:
            raise ImageProcessingError(str(e))
    
    def _convert_to_rgb(self, image: Image.Image) -> Image.Image:
        if image.mode in ("RGBA", "LA", "P"):
            background = Image.new("RGB", image.size, (255, 255, 255))
            
            if image.mode == "P":
                image = image.convert("RGBA")
            
            if image.mode in ("RGBA", "LA"):
                background.paste(image, mask=image.split()[-1])
            else:
                background.paste(image)
            
            return background
        
        elif image.mode != "RGB":
            return image.convert("RGB")
        
        return image
    
    async def _validate_file(self, file: UploadFile) -> None:
        if not file.content_type or not file.content_type.startswith("image/"):
            raise InvalidImageType()
        
        if file.filename:
            allowed_extensions = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"}
            file_ext = Path(file.filename).suffix.lower()
            if file_ext not in allowed_extensions:
                raise InvalidImageFormat(', '.join(allowed_extensions))
        
        file.file.seek(0, 2)
        size = file.file.tell()
        file.file.seek(0)
        
        max_bytes = APP_CONFIG.MAX_IMAGE_SIZE_MB * 1024 * 1024
        if size > max_bytes:
            raise ImageTooLarge(APP_CONFIG.MAX_IMAGE_SIZE_MB)
        
        if size == 0:
            raise EmptyImageFile()
    
    async def delete_image(self, image_path: str) -> bool:
        try:
            images_dir = Path(APP_CONFIG.IMAGES_DIR)
            full_path = images_dir / image_path
            
            await asyncio.to_thread(self._delete_file, full_path)
            return True
            
        except Exception:
            return False
    
    @staticmethod
    def _delete_file(filepath: Path) -> None:
        if filepath.exists() and filepath.is_file():
            filepath.unlink()
    

    async def upload_multiple(
        self, 
        files: list[UploadFile], 
        subfolder: str
    ) -> list[str]:
        tasks = [
            self.upload_and_convert(file, subfolder)
            for file in files
        ]
        return await asyncio.gather(*tasks)
