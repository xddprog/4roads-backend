import argparse
import io
import re
import time
import uuid
from html.parser import HTMLParser
from pathlib import Path
from typing import Iterable
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen

from PIL import Image
from sqlalchemy import select

from app.infrastructure.config.config import APP_CONFIG
from app.infrastructure.database.adapters.sync_connection import sync_session_maker
from app.infrastructure.database.models.category import Category
from app.infrastructure.database.models.product import Product, ProductImage


PRODUCT_LINK_RE = re.compile(r'href=["\'](/product/[^"\'>?#]+)')
PAGE_RE = re.compile(r'page=(\d+)')
PRICE_RE = re.compile(r'(\d[\d\s\xa0]+)\s*руб', re.IGNORECASE)


class ProductPageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._index = 0
        self._in_h1 = False
        self._current_anchor_href = None
        self._current_anchor_text: list[str] = []

        self.h1_text: list[str] = []
        self.h1_index: int | None = None
        self.tokens: list[tuple[int, str]] = []
        self.anchors: list[tuple[int, str, str | None]] = []
        self.images: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self._index += 1
        attrs_dict = dict(attrs)

        if tag == "h1":
            self._in_h1 = True

        if tag == "a":
            self._current_anchor_href = attrs_dict.get("href")

        for key in ("src", "data-src", "href"):
            value = attrs_dict.get(key)
            if value and "static.insales-cdn.com" in value:
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

    def handle_data(self, data: str) -> None:
        text = data.strip()
        if not text:
            return
        self._index += 1
        if self._in_h1:
            self.h1_text.append(text)
        if self._current_anchor_href is not None:
            self._current_anchor_text.append(text)
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
    links = set()
    for match in PRODUCT_LINK_RE.findall(html):
        links.add(urljoin(base_url, match))
    return links


def extract_max_page(html: str) -> int:
    pages = [int(num) for num in PAGE_RE.findall(html)]
    return max(pages) if pages else 1


def normalize_whitespace(text: str) -> str:
    text = text.replace("\xa0", " ")
    text = re.sub(r"[ \t\r\f\v]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


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


def parse_product_page(html: str, url: str) -> dict:
    parser = ProductPageParser()
    parser.feed(html)

    name = " ".join(parser.h1_text).strip() or None
    h1_index = parser.h1_index
    price, old_price = extract_prices(parser.tokens, h1_index)

    text_after_h1 = "\n".join(
        text for idx, text in parser.tokens
        if h1_index is None or idx >= h1_index
    )
    description = extract_description(text_after_h1)

    category_name, category_slug = extract_category(parser.anchors, h1_index)

    images = []
    seen = set()
    for link in parser.images:
        if link not in seen:
            seen.add(link)
            images.append(link)

    slug = urlparse(url).path.rstrip("/").split("/")[-1]

    return {
        "slug": slug,
        "name": name,
        "description": description,
        "price": price,
        "old_price": old_price,
        "category_name": category_name,
        "category_slug": category_slug,
        "images": images,
    }


def compute_discount_percent(price: int | None, old_price: int | None) -> int | None:
    if not price or not old_price or old_price <= price:
        return None
    return int(round((1 - (price / old_price)) * 100))


def download_image(url: str, target_dir: Path) -> str:
    target_dir.mkdir(parents=True, exist_ok=True)
    request = Request(url, headers={"User-Agent": "Mozilla/5.0"})
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


def import_products(
    collection_url: str,
    max_pages: int | None,
    delay: float,
    update_existing: bool,
    dry_run: bool,
) -> None:
    base_url = "{0.scheme}://{0.netloc}".format(urlparse(collection_url))
    fallback_slug = parse_collection_slug(collection_url) or "vse-kollektsii"
    fallback_name = "Все товары" if fallback_slug == "vse-kollektsii" else None
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

    if not product_links:
        print("No products found.")
        return

    with sync_session_maker() as session:
        for index, product_url in enumerate(sorted(product_links), start=1):
            html = fetch_html(product_url)
            data = parse_product_page(html, product_url)
            if not data["name"] or not data["price"]:
                print(f"[{index}] skipped (missing name/price): {product_url}")
                time.sleep(delay)
                continue
            category = get_or_create_category(session, data["category_name"], data["category_slug"])
            if category is None:
                category = get_or_create_category(session, fallback_name, fallback_slug)

            product, status = create_or_update_product(
                session,
                data,
                category,
                update_existing,
            )

            if status == "created":
                images_dir = Path(APP_CONFIG.IMAGES_DIR) / "products"
                for order, image_url in enumerate(data["images"]):
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
                print(f"[{index}] dry-run: {product_url}")
            else:
                session.commit()
                print(f"[{index}] {status}: {product_url}")

            time.sleep(delay)


def main() -> None:
    parser = argparse.ArgumentParser(description="Import products from 4roads.su")
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
    args = parser.parse_args()

    import_products(
        collection_url=args.collection_url,
        max_pages=args.max_pages,
        delay=args.delay,
        update_existing=not args.skip_existing,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    main()
