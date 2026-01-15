#!/bin/bash

# Скрипт для импорта продуктов с сайта 4roads.su
# Использование:
#   ./import_products.sh              - обычный импорт
#   ./import_products.sh --refresh    - обновить изображения
#   ./import_products.sh --cleanup    - только очистка дублей
#   ./import_products.sh --dry-run    - тестовый запуск без сохранения

set -e  # Остановка при ошибке

# Цвета для вывода
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# URL коллекции по умолчанию
COLLECTION_URL="https://4roads.su/collection/vse-kollektsii"
MAX_PAGES=""
DELAY="0.5"
REFRESH_IMAGES=""
DRY_RUN=""
CLEANUP_ONLY=false

# Парсинг аргументов
while [[ $# -gt 0 ]]; do
    case $1 in
        --refresh)
            REFRESH_IMAGES="--refresh-images"
            shift
            ;;
        --dry-run)
            DRY_RUN="--dry-run"
            shift
            ;;
        --cleanup)
            CLEANUP_ONLY=true
            shift
            ;;
        --max-pages)
            MAX_PAGES="--max-pages $2"
            shift 2
            ;;
        --url)
            COLLECTION_URL="$2"
            shift 2
            ;;
        --help)
            echo "Использование: $0 [OPTIONS]"
            echo ""
            echo "Опции:"
            echo "  --refresh       Обновить изображения существующих продуктов"
            echo "  --dry-run       Тестовый запуск без сохранения в БД"
            echo "  --cleanup       Только очистка неиспользуемых изображений"
            echo "  --max-pages N   Ограничить количество страниц для парсинга"
            echo "  --url URL       URL коллекции (по умолчанию: vse-kollektsii)"
            echo "  --help          Показать эту справку"
            echo ""
            echo "Примеры:"
            echo "  $0                              # Обычный импорт"
            echo "  $0 --refresh                    # Обновить с заменой изображений"
            echo "  $0 --dry-run --max-pages 1      # Тест на 1 странице"
            echo "  $0 --cleanup                    # Только очистка дублей"
            exit 0
            ;;
        *)
            echo -e "${RED}Неизвестная опция: $1${NC}"
            echo "Используйте --help для справки"
            exit 1
            ;;
    esac
done

echo -e "${BLUE}═══════════════════════════════════════════════════${NC}"
echo -e "${BLUE}   4Roads Product Import Tool${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════${NC}"
echo ""

# Проверка наличия Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python3 не найден!${NC}"
    exit 1
fi

# Если только очистка
if [ "$CLEANUP_ONLY" = true ]; then
    echo -e "${YELLOW}🧹 Запуск очистки неиспользуемых изображений...${NC}"
    echo ""
    
    # Сначала показываем что будет удалено
    echo -e "${BLUE}Проверка наличия дублей:${NC}"
    python3 -m app.utils.cleanup_orphaned_images
    echo ""
    
    # Спрашиваем подтверждение
    read -p "Удалить найденные файлы? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${GREEN}Удаление файлов...${NC}"
        python3 -m app.utils.cleanup_orphaned_images --execute
        echo -e "${GREEN}✅ Очистка завершена!${NC}"
    else
        echo -e "${YELLOW}Операция отменена${NC}"
    fi
    exit 0
fi

# Показываем параметры импорта
echo -e "${BLUE}Параметры импорта:${NC}"
echo "  URL: $COLLECTION_URL"
echo "  Обновление изображений: ${REFRESH_IMAGES:-нет}"
echo "  Режим dry-run: ${DRY_RUN:-нет}"
echo "  Ограничение страниц: ${MAX_PAGES:-нет}"
echo ""

# Подсчет текущих файлов
if [ -d "static/images/products" ]; then
    FILES_BEFORE=$(find static/images/products -name "*.webp" 2>/dev/null | wc -l | tr -d ' ')
    echo -e "${BLUE}📊 Текущее количество файлов изображений: ${FILES_BEFORE}${NC}"
    echo ""
fi

# Запуск импорта
echo -e "${YELLOW}🚀 Запуск импорта продуктов...${NC}"
echo ""

python3 -m app.utils.import_4roads_full \
    --collection-url "$COLLECTION_URL" \
    --delay "$DELAY" \
    $MAX_PAGES \
    $REFRESH_IMAGES \
    $DRY_RUN

# Статистика после импорта
echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✅ Импорт завершен!${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════${NC}"
echo ""

# Подсчет файлов после
if [ -d "static/images/products" ]; then
    FILES_AFTER=$(find static/images/products -name "*.webp" 2>/dev/null | wc -l | tr -d ' ')
    FILES_DIFF=$((FILES_AFTER - FILES_BEFORE))
    
    echo -e "${BLUE}📊 Статистика:${NC}"
    echo "  Файлов было: $FILES_BEFORE"
    echo "  Файлов стало: $FILES_AFTER"
    
    if [ $FILES_DIFF -gt 0 ]; then
        echo -e "  Изменение: ${GREEN}+${FILES_DIFF}${NC}"
    elif [ $FILES_DIFF -lt 0 ]; then
        echo -e "  Изменение: ${RED}${FILES_DIFF}${NC}"
    else
        echo "  Изменение: 0"
    fi
    echo ""
fi

# Проверка на дубли
if [ -z "$DRY_RUN" ]; then
    echo -e "${BLUE}🔍 Проверка на неиспользуемые файлы:${NC}"
    python3 -m app.utils.cleanup_orphaned_images
    echo ""
fi

echo -e "${GREEN}Готово! 🎉${NC}"

