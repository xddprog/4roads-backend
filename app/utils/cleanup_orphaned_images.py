"""
Утилита для очистки неиспользуемых файлов изображений.

Удаляет файлы изображений, которые есть на диске, но отсутствуют в базе данных.
Это может произойти после многократных запусков импорта с флагом --refresh-images.
"""
import argparse
from pathlib import Path

from sqlalchemy import select

from app.infrastructure.config.config import APP_CONFIG
from app.infrastructure.database.adapters.sync_connection import sync_session_maker
from app.infrastructure.database.models.product import ProductImage


def get_used_image_paths(session) -> set[str]:
    """Получить все пути к изображениям, используемым в БД."""
    images = session.scalars(select(ProductImage)).all()
    return {img.image_path for img in images}


def find_orphaned_images(images_dir: Path, used_paths: set[str]) -> list[Path]:
    """Найти файлы изображений, которых нет в БД."""
    orphaned = []
    products_dir = images_dir / "products"
    
    if not products_dir.exists():
        return orphaned
    
    for image_file in products_dir.glob("*.webp"):
        relative_path = f"products/{image_file.name}"
        if relative_path not in used_paths:
            orphaned.append(image_file)
    
    return orphaned


def cleanup_orphaned_images(dry_run: bool = True) -> None:
    """Удалить неиспользуемые файлы изображений."""
    images_dir = Path(APP_CONFIG.IMAGES_DIR)
    
    with sync_session_maker() as session:
        used_paths = get_used_image_paths(session)
    
    orphaned = find_orphaned_images(images_dir, used_paths)
    
    if not orphaned:
        print("✅ Неиспользуемых изображений не найдено")
        return
    
    total_size = sum(f.stat().st_size for f in orphaned)
    print(f"🗑️  Найдено {len(orphaned)} неиспользуемых файлов ({total_size / 1024 / 1024:.2f} MB)")
    
    if dry_run:
        print("\n🔍 Режим dry-run, файлы не будут удалены:")
        for idx, file_path in enumerate(orphaned[:10], 1):
            print(f"  [{idx}] {file_path.name} ({file_path.stat().st_size / 1024:.1f} KB)")
        if len(orphaned) > 10:
            print(f"  ... и ещё {len(orphaned) - 10} файлов")
        print("\n💡 Запустите с флагом --execute для удаления")
    else:
        deleted = 0
        errors = 0
        for file_path in orphaned:
            try:
                file_path.unlink()
                deleted += 1
            except Exception as exc:
                print(f"❌ Ошибка при удалении {file_path.name}: {exc}")
                errors += 1
        
        print(f"✅ Удалено: {deleted} файлов")
        if errors:
            print(f"❌ Ошибок: {errors}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Очистка неиспользуемых файлов изображений"
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Выполнить удаление (по умолчанию только показать список)",
    )
    args = parser.parse_args()
    
    cleanup_orphaned_images(dry_run=not args.execute)


if __name__ == "__main__":
    main()

