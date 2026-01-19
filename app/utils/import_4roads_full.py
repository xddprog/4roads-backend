import argparse
import io
import json
import re
import time
import uuid
from html.parser import HTMLParser
from pathlib import Path
from typing import Iterable
from urllib.parse import urljoin, urlparse, urlsplit, urlunsplit, quote
from urllib.request import Request, urlopen

from PIL import Image
from slugify import slugify
from sqlalchemy import select, delete

from app.infrastructure.config.config import APP_CONFIG
from app.infrastructure.database.adapters.sync_connection import sync_session_maker
from app.infrastructure.database.models.category import Category
from app.infrastructure.database.models.product import (
    Product,
    ProductImage,
    ProductCharacteristic,
    CharacteristicType,
)
from app.infrastructure.database.models.review import Review
from app.utils.enums import CharacteristicTypeEnum


PAGE_RE = re.compile(r'page=(\d+)')
PRICE_RE = re.compile(r'(\d[\d\s\xa0]+)\s*руб', re.IGNORECASE)
DIMENSION_RE = re.compile(
    r"(\d+(?:[.,]\d+)?)\s*см?\s*[xх×]\s*(\d+(?:[.,]\d+)?)\s*см?"
    r"(?:\s*[xх×]\s*(\d+(?:[.,]\d+)?)\s*см?)?",
    re.IGNORECASE,
)

COLOR_TOKENS = {
    "белый", "белый жемчужный", "бежевый", "бордовый", "васильковый",
    "вишневый", "вишня", "голубой", "желтый", "коричневый",
    "королевский синий", "красный", "оранж", "оранжевый", "петролеум",
    "пурпурный", "розовый", "салатовый", "светло-синий", "серо-голубой",
    "серо-оливковый", "серый", "синий", "темно-зеленый", "темно-пурпурный",
    "темно-серый", "темно-синий", "черный", "хаки", "зеленый",
}


class ProductLinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: set[str] = set()

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag != "a":
            return
        attrs_dict = dict(attrs)
        href = attrs_dict.get("href")
        class_attr = (attrs_dict.get("class") or "").lower()
        if href and href.startswith("/product/") and "inner" in class_attr:
            self.links.add(href)


class ProductPageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._index = 0
        self._depth = 0
        self._in_h1 = False
        self._current_anchor_href = None
        self._current_anchor_text: list[str] = []
        self._in_description = False
        self._desc_depth: int | None = None
        self._in_characteristics = False
        self._char_depth: int | None = None
        self._in_gallery = False
        self._gallery_depth: int | None = None
        self._in_introtext = False
        self._intro_depth: int | None = None
        self._current_option: str | None = None
        self._option_depth: int | None = None
        self._in_price = False
        self._price_depth: int | None = None
        self._in_old_price = False
        self._old_price_depth: int | None = None

        self.h1_text: list[str] = []
        self.h1_index: int | None = None
        self.tokens: list[tuple[int, str]] = []
        self.anchors: list[tuple[int, str, str | None]] = []
        self.images: list[str] = []
        self.description_parts: list[str] = []
        self.characteristics_parts: list[str] = []
        self.introtext_parts: list[str] = []
        self.price_text: str | None = None
        self.old_price_text: str | None = None
        self.size_value: str | None = None
        self.color_value: str | None = None
        self.sku: str | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self._index += 1
        self._depth += 1
        attrs_dict = dict(attrs)
        class_attr = (attrs_dict.get("class") or "").lower()

        if tag == "h1":
            self._in_h1 = True

        if attrs_dict.get("id") == "product-description":
            self._in_description = True
            self._desc_depth = self._depth

        if attrs_dict.get("id") == "product-characteristics":
            self._in_characteristics = True
            self._char_depth = self._depth

        if "product-gallery" in class_attr:
            self._in_gallery = True
            self._gallery_depth = self._depth

        if "product-introtext" in class_attr:
            self._in_introtext = True
            self._intro_depth = self._depth

        if "option-razmer" in class_attr:
            self._current_option = "size"
            self._option_depth = self._depth
        elif "option-cvet" in class_attr:
            self._current_option = "color"
            self._option_depth = self._depth

        if "js-product-price" in class_attr:
            self._in_price = True
            self._price_depth = self._depth

        if "js-product-old-price" in class_attr:
            self._in_old_price = True
            self._old_price_depth = self._depth

        if tag == "a":
            self._current_anchor_href = attrs_dict.get("href")

        if self._in_gallery:
            for key in ("src", "data-src", "href"):
                value = attrs_dict.get(key)
                if value and "static.insales-cdn.com/images/products" in value:
                    self.images.append(value)

    def handle_endtag(self, tag: str) -> None:
        self._index += 1
        if tag == "h1":
            self._in_h1 = False
            self.h1_index = self._index

        if tag == "a" and self._current_anchor_href is not None:
            text = "".join(self._current_anchor_text).strip()
            self.anchors.append((self._index, text, self._current_anchor_href))
            self._current_anchor_href = None
            self._current_anchor_text = []

        if self._desc_depth is not None and self._depth == self._desc_depth:
            self._in_description = False
            self._desc_depth = None

        if self._char_depth is not None and self._depth == self._char_depth:
            self._in_characteristics = False
            self._char_depth = None

        if self._gallery_depth is not None and self._depth == self._gallery_depth:
            self._in_gallery = False
            self._gallery_depth = None

        if self._intro_depth is not None and self._depth == self._intro_depth:
            self._in_introtext = False
            self._intro_depth = None

        if self._option_depth is not None and self._depth == self._option_depth:
            self._current_option = None
            self._option_depth = None

        if self._price_depth is not None and self._depth == self._price_depth:
            self._in_price = False
            self._price_depth = None

        if self._old_price_depth is not None and self._depth == self._old_price_depth:
            self._in_old_price = False
            self._old_price_depth = None

        self._depth -= 1

    def handle_data(self, data: str) -> None:
        text = data.strip()
        if not text:
            return
        self._index += 1
        if self._in_h1:
            self.h1_text.append(text)
        if self._current_anchor_href is not None:
            self._current_anchor_text.append(text)
        if self._in_description:
            self.description_parts.append(text)
        if self._in_characteristics:
            self.characteristics_parts.append(text)
        if self._in_introtext:
            self.introtext_parts.append(text)
        if self._in_price and self.price_text is None:
            match = PRICE_RE.search(text)
            if match:
                self.price_text = match.group(1)
        if self._in_old_price and self.old_price_text is None:
            match = PRICE_RE.search(text)
            if match:
                self.old_price_text = match.group(1)
        if self._current_option == "size" and self.size_value is None:
            if text.lower() != "размер":
                self.size_value = text
        if self._current_option == "color" and self.color_value is None:
            if text.lower() != "цвет":
                self.color_value = text
        if self.sku is None and "Артикул" in text:
            match = re.search(r"Артикул[:\s]*([A-Za-zА-Яа-я0-9-]+)", text)
            if match:
                self.sku = match.group(1)
        self.tokens.append((self._index, text))


def fetch_html(url: str, timeout: int = 30) -> str:
    request = Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (compatible; 4roads-scraper/1.0)",
            "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8",
        },
    )
    with urlopen(request, timeout=timeout) as response:
        charset = response.headers.get_content_charset() or "utf-8"
        return response.read().decode(charset, errors="replace")


def extract_product_links(html: str, base_url: str) -> set[str]:
    parser = ProductLinkParser()
    parser.feed(html)
    return {urljoin(base_url, href) for href in parser.links}


def extract_max_page(html: str) -> int:
    pages = [int(num) for num in PAGE_RE.findall(html)]
    return max(pages) if pages else 1


def normalize_whitespace(text: str) -> str:
    text = text.replace("\xa0", " ")
    text = re.sub(r"[ \t\r\f\v]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def normalize_color_token(token: str) -> str | None:
    cleaned = normalize_whitespace(token).strip(",;").lower()
    if not cleaned:
        return None
    if cleaned in {"в ассортименте", "ассорти", "ассортимент"}:
        return None
    if cleaned in COLOR_TOKENS:
        return cleaned.capitalize()
    return cleaned.capitalize()


def extract_color_from_text(text: str) -> str | None:
    match = re.search(
        r"(?:доступные\s+цвета|цвета|цвет)\s*[:\-]\s*([^.\n]+)",
        text,
        re.IGNORECASE,
    )
    if not match:
        return None
    raw = match.group(1)
    tokens = [t for t in re.split(r"[,/]", raw) if t.strip()]
    colors = []
    for token in tokens:
        normalized = normalize_color_token(token)
        if normalized:
            colors.append(normalized)
    if len(colors) == 1:
        return colors[0]
    return None


def extract_material_from_text(text: str) -> str | None:
    lowered = text.lower()
    key_pos = lowered.find("материал")
    if key_pos == -1:
        return None
    tail = text[key_pos + len("материал"):]
    tail = tail.lstrip(" :.-")
    if not tail:
        return None
    keywords = ["объём", "объем", "цвета", "цвет", "размеры", "размер", "доступные"]
    end_positions = []
    tail_lower = tail.lower()
    for keyword in keywords:
        pos = tail_lower.find(keyword)
        if pos != -1:
            end_positions.append(pos)
    for sep in [".", "\n"]:
        pos = tail.find(sep)
        if pos != -1:
            end_positions.append(pos)
    end = min(end_positions) if end_positions else len(tail)
    material = tail[:end].strip(" ,.-")
    return material or None


def extract_introtext_characteristics(text: str) -> dict[str, str]:
    if not text:
        return {}
    text_norm = normalize_whitespace(text)
    result: dict[str, str] = {}

    size_match = re.search(r"Размер[:\s]*([0-9]+)\s*\"", text_norm, re.IGNORECASE)
    if size_match:
        result["Размер"] = f"{size_match.group(1)}\""

    dim_match = DIMENSION_RE.search(text_norm)
    if dim_match:
        parts = [p for p in dim_match.groups() if p]
        if parts:
            size_value = "x".join(parts) + " см"
            result.setdefault("Размер", size_value)

    width = re.search(r"Ширина[:\s]*([0-9]+(?:[.,][0-9]+)?)\s*см", text_norm, re.IGNORECASE)
    height = re.search(r"Высота[:\s]*([0-9]+(?:[.,][0-9]+)?)\s*см", text_norm, re.IGNORECASE)
    depth = re.search(r"Глубина[:\s]*([0-9]+(?:[.,][0-9]+)?)\s*см", text_norm, re.IGNORECASE)
    if width:
        result["Ширина"] = f"{width.group(1)} см"
    if height:
        result["Высота"] = f"{height.group(1)} см"
    if depth:
        result["Глубина"] = f"{depth.group(1)} см"

    if "Размер" not in result and width and height and depth:
        result["Размер"] = f"{width.group(1)}x{height.group(1)}x{depth.group(1)} см"

    weight = re.search(r"Вес[:\s]*([0-9]+(?:[.,][0-9]+)?)\s*(кг|г)?", text_norm, re.IGNORECASE)
    if weight:
        unit = weight.group(2) or "г"
        result["Вес"] = f"{weight.group(1)} {unit}"

    volume = re.search(r"Объ[её]м[:\s]*([0-9]+(?:[.,][0-9]+)?)\s*(мл|л)?", text_norm, re.IGNORECASE)
    if volume:
        unit = volume.group(2) or "мл"
        result["Объём"] = f"{volume.group(1)} {unit}"

    diameter = re.search(r"диаметр[^0-9]*([0-9]+(?:[.,][0-9]+)?)\s*см", text_norm, re.IGNORECASE)
    if diameter:
        result["Диаметр"] = f"{diameter.group(1)} см"

    length = re.search(r"длина[:\s]*([0-9]+(?:[.,][0-9]+)?)\s*см", text_norm, re.IGNORECASE)
    if length:
        result["Длина"] = f"{length.group(1)} см"

    material = extract_material_from_text(text_norm)
    if material:
        result.setdefault("Материал", material)

    color = extract_color_from_text(text_norm)
    if color:
        result.setdefault("Цвет", color)

    return result


def extract_description(text: str) -> str | None:
    if not text:
        return None
    markers = ["· Артикул", "Артикул:", "Артикул"]
    start = -1
    for marker in markers:
        pos = text.find(marker)
        if pos != -1:
            start = pos
            break
    if start != -1:
        end_markers = ["Имя", "E-mail", "Оценка", "Отправить", "Отзывы"]
        end_positions = [text.find(m, start) for m in end_markers]
        end_positions = [pos for pos in end_positions if pos != -1]
        end = min(end_positions) if end_positions else len(text)
        return normalize_whitespace(text[start:end])

    desc_marker = "Описание"
    pos = text.find(desc_marker)
    if pos != -1:
        tail = text[pos + len(desc_marker):]
        end = tail.find("Отзывы")
        if end != -1:
            tail = tail[:end]
        return normalize_whitespace(tail)
    return None


def extract_prices(tokens: Iterable[tuple[int, str]], h1_index: int | None) -> tuple[int | None, int | None]:
    matches: list[int] = []
    for idx, text in tokens:
        if h1_index is not None and idx < h1_index:
            continue
        for match in PRICE_RE.findall(text):
            price = int(match.replace(" ", "").replace("\xa0", ""))
            matches.append(price)
    if not matches:
        return None, None
    if len(matches) == 1:
        return matches[0], None
    price = matches[0]
    old_price = None
    if matches[1] > price:
        old_price = matches[1]
    return price, old_price


def extract_category(anchors: list[tuple[int, str, str | None]], h1_index: int | None) -> tuple[str | None, str | None]:
    if h1_index is None:
        return None, None
    main_anchor_idx = None
    for idx, text, _href in anchors:
        if idx < h1_index and text.strip().lower() == "главная":
            if main_anchor_idx is None or idx > main_anchor_idx:
                main_anchor_idx = idx
    if main_anchor_idx is None:
        return None, None
    for idx, text, href in anchors:
        if idx > main_anchor_idx and idx < h1_index and href and "/collection/" in href:
            name = text.strip() or None
            slug = parse_collection_slug(href)
            return name, slug
    return None, None


def parse_collection_slug(href: str) -> str | None:
    path = urlparse(href).path
    if "/collection/" not in path:
        return None
    slug = path.split("/collection/")[-1].strip("/")
    return slug or None


def find_label_value(tokens: list[str], label: str) -> str | None:
    label_lower = label.lower()
    for idx, text in enumerate(tokens):
        if text.lower() == label_lower:
            for j in range(idx + 1, min(idx + 6, len(tokens))):
                candidate = tokens[j].strip()
                if not candidate:
                    continue
                if candidate.lower() in {"количество", "в наличии"}:
                    continue
                return candidate
    return None


def extract_size_from_name(name: str | None) -> str | None:
    if not name:
        return None
    match = re.search(r"\(([^)]+)\)", name)
    if match:
        raw = match.group(1).strip()
        if re.search(r"\d", raw) or re.fullmatch(r"[SML]", raw, re.IGNORECASE):
            return raw
        return None
    return None


def normalize_size(value: str | None) -> str | None:
    if not value:
        return None
    value = value.strip()
    if re.search(r"[xх×]|см|мм|\"", value, re.IGNORECASE):
        return normalize_whitespace(value)
    match = re.search(r"\b([SML])\b", value, re.IGNORECASE)
    if match:
        return match.group(1).upper()
    match = re.fullmatch(r"(\d{2})\s*\"?", value)
    if match:
        return match.group(1)
    return value


def normalize_material(value: str | None) -> str | None:
    if not value:
        return None
    lower = value.lower()
    if "поликарбонат" in lower:
        return "Поликарбонат"
    if "полипропилен" in lower:
        return "Полипропилен"
    if "abs" in lower:
        return "ABS-пластик"
    if "полиэстер" in lower:
        return "Полиэстер"
    if "нейлон" in lower:
        return "Нейлон"
    if "спандекс" in lower:
        return "Спандекс"
    if "кожзам" in lower:
        return "Кожзам"
    return value.strip()


def extract_color_from_name(name: str | None) -> str | None:
    if not name:
        return None
    lower = name.lower()
    for color in sorted(COLOR_TOKENS, key=len, reverse=True):
        if lower.endswith(color):
            return color.capitalize()
    return None


def extract_characteristics(
    tokens: list[str],
    text: str,
    name: str | None,
    introtext: str | None,
) -> dict[str, str]:
    text_norm = normalize_whitespace(text)
    intro_data = extract_introtext_characteristics(introtext or "")
    size = find_label_value(tokens, "Размер")
    color = find_label_value(tokens, "Цвет")
    material = None

    material_match = re.search(r"Материал[:\s]+([^\n]+)", text_norm, re.IGNORECASE)
    if material_match:
        material = material_match.group(1).strip()
    if not material:
        material = intro_data.get("Материал") or extract_material_from_text(text_norm)

    if not size:
        size = intro_data.get("Размер") or extract_size_from_name(name)
    size = normalize_size(size)

    if not color:
        color = intro_data.get("Цвет") or extract_color_from_name(name) or extract_color_from_text(text_norm)
    if color:
        color = color.strip().capitalize()

    material = normalize_material(material)

    result: dict[str, str] = {}
    for key, value in intro_data.items():
        if key in {"Размер", "Материал", "Цвет"}:
            continue
        result[key] = value
    if size:
        result["Размер"] = size
    if material:
        result["Материал"] = material
    if color:
        result["Цвет"] = color
    return result


def parse_product_page(html: str, url: str) -> dict:
    parser = ProductPageParser()
    parser.feed(html)

    name = " ".join(parser.h1_text).strip() or None
    h1_index = parser.h1_index
    price, old_price = extract_prices(parser.tokens, h1_index)
    if parser.price_text:
        price = int(parser.price_text.replace(" ", "").replace("\xa0", ""))
    if parser.old_price_text:
        old_price = int(parser.old_price_text.replace(" ", "").replace("\xa0", ""))

    text_after_h1 = "\n".join(
        text for idx, text in parser.tokens
        if h1_index is None or idx >= h1_index
    )
    description = None
    if parser.description_parts:
        description = normalize_whitespace(" ".join(parser.description_parts))
    if not description:
        description = extract_description(text_after_h1)

    category_name, category_slug = extract_category(parser.anchors, h1_index)

    introtext = None
    if parser.introtext_parts:
        introtext = normalize_whitespace(" ".join(parser.introtext_parts))

    images = []
    seen = set()
    large_links: list[str] = []
    fallback_links: list[str] = []
    for link in parser.images:
        path = urlparse(link).path
        filename = Path(path).name.lower()
        if filename.startswith("large_"):
            large_links.append(link)
        else:
            fallback_links.append(link)

    selected_links = large_links or fallback_links
    for link in selected_links:
        if link not in seen:
            seen.add(link)
            images.append(link)

    slug = urlparse(url).path.rstrip("/").split("/")[-1]
    tokens = [text for _idx, text in parser.tokens]
    characteristics = extract_characteristics(tokens, text_after_h1, name, introtext)
    if parser.size_value and "Размер" not in characteristics:
        characteristics["Размер"] = normalize_size(parser.size_value)
    if parser.color_value:
        characteristics["Цвет"] = parser.color_value.strip().capitalize()

    return {
        "slug": slug,
        "name": name,
        "description": description,
        "price": price,
        "old_price": old_price,
        "category_name": category_name,
        "category_slug": category_slug,
        "images": images,
        "characteristics": characteristics,
        "sku": parser.sku,
    }


def compute_discount_percent(price: int | None, old_price: int | None) -> int | None:
    if not price or not old_price or old_price <= price:
        return None
    return int(round((1 - (price / old_price)) * 100))


def download_image(url: str, target_dir: Path) -> str:
    target_dir.mkdir(parents=True, exist_ok=True)
    split = urlsplit(url)
    safe_path = quote(split.path)
    safe_url = urlunsplit((split.scheme, split.netloc, safe_path, split.query, split.fragment))
    request = Request(safe_url, headers={"User-Agent": "Mozilla/5.0"})
    with urlopen(request, timeout=30) as response:
        content = response.read()
    max_bytes = APP_CONFIG.MAX_IMAGE_SIZE_MB * 1024 * 1024
    if len(content) > max_bytes:
        raise ValueError(f"image too large: {len(content)} bytes")
    image = Image.open(io.BytesIO(content))
    if image.mode in ("RGBA", "LA", "P"):
        background = Image.new("RGB", image.size, (255, 255, 255))
        if image.mode == "P":
            image = image.convert("RGBA")
        if image.mode in ("RGBA", "LA"):
            background.paste(image, mask=image.split()[-1])
        else:
            background.paste(image)
        image = background
    elif image.mode != "RGB":
        image = image.convert("RGB")

    filename = f"{uuid.uuid4()}.webp"
    filepath = target_dir / filename
    image.save(
        filepath,
        "WEBP",
        quality=APP_CONFIG.WEBP_QUALITY,
        method=6,
        optimize=True,
    )
    return filename


def get_or_create_category(session, name: str | None, slug: str | None) -> Category | None:
    if not slug:
        return None
    category = session.scalars(select(Category).where(Category.slug == slug)).first()
    if category:
        if name and category.name != name:
            category.name = name
        return category
    if not name:
        name = slug.replace("-", " ").title()
    category = Category(name=name, slug=slug)
    session.add(category)
    session.flush()
    return category


def get_or_create_characteristic_type(session, enum_value: CharacteristicTypeEnum) -> CharacteristicType:
    characteristic = session.scalars(
        select(CharacteristicType).where(CharacteristicType.name == enum_value)
    ).first()
    if characteristic:
        return characteristic
    characteristic = CharacteristicType(
        name=enum_value,
        slug=slugify(enum_value.value),
    )
    session.add(characteristic)
    session.flush()
    return characteristic


def get_existing_product(session, slug: str) -> Product | None:
    return session.scalars(select(Product).where(Product.slug == slug)).first()


def create_or_update_product(
    session,
    data: dict,
    category: Category | None,
    update_existing: bool,
) -> tuple[Product, str]:
    existing = get_existing_product(session, data["slug"])
    if existing and not update_existing:
        return existing, "skipped"
    if existing:
        product = existing
    else:
        product = Product(
            slug=data["slug"],
            name=data["name"] or data["slug"],
            description=data["description"],
            price=data["price"] or 0,
            discount_percent=compute_discount_percent(data["price"], data["old_price"]),
            is_active=True,
            is_featured=False,
            category_id=category.id if category else None,
        )
        session.add(product)
        session.flush()
        return product, "created"

    product.name = data["name"] or product.name
    product.description = data["description"] or product.description
    if data["price"]:
        product.price = data["price"]
    product.discount_percent = compute_discount_percent(data["price"], data["old_price"])
    if category:
        product.category_id = category.id
    return product, "updated"


def upsert_characteristics(session, product: Product, characteristics: dict[str, str]) -> None:
    if not characteristics:
        return
    mapping = {
        "Размер": CharacteristicTypeEnum.SIZE,
        "Ширина": CharacteristicTypeEnum.WIDTH,
        "Высота": CharacteristicTypeEnum.HEIGHT,
        "Глубина": CharacteristicTypeEnum.DEPTH,
        "Вес": CharacteristicTypeEnum.WEIGHT,
        "Диаметр": CharacteristicTypeEnum.DIAMETER,
        "Длина": CharacteristicTypeEnum.LENGTH,
        "Объём": CharacteristicTypeEnum.VOLUME,
        "Материал": CharacteristicTypeEnum.MATERIAL,
        "Цвет": CharacteristicTypeEnum.COLOR,
    }
    for key, value in characteristics.items():
        enum_value = mapping.get(key)
        if not enum_value or not value:
            continue
        char_type = get_or_create_characteristic_type(session, enum_value)
        existing = session.scalars(
            select(ProductCharacteristic).where(
                ProductCharacteristic.product_id == product.id,
                ProductCharacteristic.characteristic_type_id == char_type.id,
            )
        ).first()
        if existing:
            existing.value = value
        else:
            session.add(
                ProductCharacteristic(
                    value=value,
                    product_id=product.id,
                    characteristic_type_id=char_type.id,
                )
            )


def scrape_products(
    collection_url: str,
    max_pages: int | None,
    delay: float,
) -> list[dict]:
    base_url = "{0.scheme}://{0.netloc}".format(urlparse(collection_url))
    first_html = fetch_html(collection_url)
    max_page = extract_max_page(first_html)
    if max_pages:
        max_page = min(max_page, max_pages)

    product_links = set()
    product_links.update(extract_product_links(first_html, base_url))
    for page in range(2, max_page + 1):
        page_url = f"{collection_url}?page={page}"
        html = fetch_html(page_url)
        product_links.update(extract_product_links(html, base_url))
        time.sleep(delay)

    products: list[dict] = []
    for index, product_url in enumerate(sorted(product_links), start=1):
        html = fetch_html(product_url)
        data = parse_product_page(html, product_url)
        data["source_url"] = product_url
        if not data["name"] or not data["price"]:
            print(f"[{index}] skipped (missing name/price): {product_url}")
            time.sleep(delay)
            continue
        products.append(data)
        time.sleep(delay)
    return products


def import_products(
    products: list[dict],
    collection_url: str,
    update_existing: bool,
    dry_run: bool,
    refresh_images: bool,
    reset_catalog: bool,
) -> None:
    fallback_slug = parse_collection_slug(collection_url) or "vse-kollektsii"
    fallback_name = "Все товары" if fallback_slug == "vse-kollektsii" else None

    with sync_session_maker() as session:
        if reset_catalog:
            if dry_run:
                print("[reset] dry-run: skip catalog reset")
            else:
                session.execute(delete(ProductImage))
                session.execute(delete(ProductCharacteristic))
                session.execute(delete(Review))
                session.execute(delete(Product))
                session.execute(delete(Category))
                session.execute(delete(CharacteristicType))
                session.commit()
                print("[reset] catalog cleared")

        for index, data in enumerate(products, start=1):
            category = get_or_create_category(session, data.get("category_name"), data.get("category_slug"))
            if category is None:
                category = get_or_create_category(session, fallback_name, fallback_slug)

            product, status = create_or_update_product(
                session,
                data,
                category,
                update_existing,
            )

            if status != "skipped":
                upsert_characteristics(session, product, data.get("characteristics", {}))

            # Удаляем старые изображения и файлы при обновлении с refresh_images
            if refresh_images and status != "skipped":
                # Получаем пути к файлам перед удалением записей из БД
                old_images = session.scalars(
                    select(ProductImage).where(ProductImage.product_id == product.id)
                ).all()
                images_dir = Path(APP_CONFIG.IMAGES_DIR)
                
                # Удаляем файлы с диска
                deleted_files = 0
                for old_img in old_images:
                    old_file_path = images_dir / old_img.image_path
                    if old_file_path.exists():
                        try:
                            old_file_path.unlink()
                            deleted_files += 1
                        except Exception as exc:
                            print(f"[{index}] failed to delete old image file {old_file_path}: {exc}")
                
                if deleted_files > 0:
                    print(f"[{index}] deleted {deleted_files} old image file(s)")
                
                # Удаляем записи из БД
                session.execute(delete(ProductImage).where(ProductImage.product_id == product.id))
                session.flush()

            # Добавляем изображения только для новых продуктов или при явном refresh_images
            if status == "created" or (refresh_images and status != "skipped"):
                images_dir = Path(APP_CONFIG.IMAGES_DIR) / "products"
                for order, image_url in enumerate(data.get("images", [])):
                    try:
                        filename = download_image(image_url, images_dir)
                    except Exception as exc:
                        print(f"[{index}] image download failed: {image_url} ({exc})")
                        continue
                    session.add(
                        ProductImage(
                            image_path=f"products/{filename}",
                            order=order,
                            product_id=product.id,
                        )
                    )

            if dry_run:
                session.rollback()
                print(f"[{index}] dry-run: {data.get('source_url')}")
            else:
                session.commit()
                print(f"[{index}] {status}: {data.get('source_url')}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Import products from 4roads.su with characteristics")
    parser.add_argument(
        "--collection-url",
        default="https://4roads.su/collection/vse-kollektsii",
        help="Collection URL to scrape",
    )
    parser.add_argument("--max-pages", type=int, default=None, help="Limit pages")
    parser.add_argument("--delay", type=float, default=0.5, help="Delay between requests")
    parser.add_argument(
        "--skip-existing",
        action="store_true",
        help="Skip existing products (default is upsert/update)",
    )
    parser.add_argument("--dry-run", action="store_true", help="Parse without DB writes")
    parser.add_argument("--refresh-images", action="store_true", help="Replace images on update")
    parser.add_argument(
        "--reset-catalog",
        action="store_true",
        help="Delete products and related data before import",
    )
    parser.add_argument("--json-path", default="data/4roads_products.json", help="Path for export/import JSON")
    parser.add_argument("--export-json", action="store_true", help="Export scraped data to JSON")
    parser.add_argument("--import-json", action="store_true", help="Import from JSON instead of scraping")
    args = parser.parse_args()

    json_path = Path(args.json_path)
    products: list[dict]

    if args.import_json and json_path.exists():
        products = json.loads(json_path.read_text(encoding="utf-8"))
    else:
        products = scrape_products(
            collection_url=args.collection_url,
            max_pages=args.max_pages,
            delay=args.delay,
        )
        if args.export_json:
            json_path.parent.mkdir(parents=True, exist_ok=True)
            json_path.write_text(json.dumps(products, ensure_ascii=False, indent=2), encoding="utf-8")

    if args.import_json or not args.export_json:
        import_products(
            products=products,
            collection_url=args.collection_url,
            update_existing=not args.skip_existing,
            dry_run=args.dry_run,
            refresh_images=args.refresh_images,
            reset_catalog=args.reset_catalog,
        )


if __name__ == "__main__":
    main()
