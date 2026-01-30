from email.message import EmailMessage
from pathlib import Path
import html

import aiosmtplib

from app.core.dto.contact_form import ContactFormModel
from app.core.dto.order import OrderModel
from app.core.dto.settings import SettingsModel
from app.infrastructure.config.config import APP_CONFIG
from app.infrastructure.logging import get_logger


logger = get_logger(__name__)

ORDER_TEMPLATE_PATH = Path(__file__).resolve().parent / "templates" / "order_notification.html"

def _smtp_configured(settings: SettingsModel) -> bool:
    return bool(
        APP_CONFIG.SMTP_HOST
        and APP_CONFIG.SMTP_PORT
        and APP_CONFIG.SMTP_USER
        and APP_CONFIG.SMTP_PASS
        and settings.email
    )


def _build_contact_message(settings: SettingsModel, contact: ContactFormModel) -> EmailMessage:
    message = EmailMessage()
    from_address = APP_CONFIG.SMTP_FROM or APP_CONFIG.SMTP_USER
    message["From"] = from_address
    message["To"] = settings.email
    message["Subject"] = "Новая заявка с сайта"
    message.set_content(
        "\n".join(
            [
                "Поступила новая заявка.",
                f"Имя: {contact.name}",
                f"Телефон: {contact.phone}",
                f"Сообщение: {contact.message}",
                f"Дата: {contact.created_at}",
            ]
        )
    )
    return message


def _format_money(amount: int) -> str:
    return f"{amount} ₽"


def _render_order_items_rows(order: OrderModel) -> str:
    rows = []
    for item in order.items:
        rows.append(
            "<tr>"
            f"<td>{html.escape(item.product_name)}</td>"
            f"<td align=\"center\">{item.quantity}</td>"
            f"<td align=\"right\">{_format_money(item.unit_price)}</td>"
            f"<td align=\"right\">{_format_money(item.total_price)}</td>"
            "</tr>"
        )
    return "\n".join(rows)


def _render_order_html(order: OrderModel) -> str:
    template = ORDER_TEMPLATE_PATH.read_text(encoding="utf-8")
    return template.format(
        order_id=order.id,
        created_at=order.created_at,
        name=html.escape(order.name),
        phone=html.escape(order.phone),
        email=html.escape(order.email or "—"),
        comment=html.escape(order.comment or "—"),
        total_amount=_format_money(order.total_amount),
        items_rows=_render_order_items_rows(order),
    )


def _build_order_message(settings: SettingsModel, order: OrderModel) -> EmailMessage:
    message = EmailMessage()
    from_address = APP_CONFIG.SMTP_FROM or APP_CONFIG.SMTP_USER
    message["From"] = from_address
    message["To"] = settings.email
    message["Subject"] = "Новый заказ с сайта"
    message.set_content(
        "\n".join(
            [
                "Поступил новый заказ.",
                f"Номер: {order.id}",
                f"Дата: {order.created_at}",
                f"Имя: {order.name}",
                f"Телефон: {order.phone}",
                f"Email: {order.email or '-'}",
                f"Комментарий: {order.comment or '-'}",
                "Товары:",
                *[
                    f"- {item.product_name} x{item.quantity} = {_format_money(item.total_price)}"
                    for item in order.items
                ],
                f"Итого: {_format_money(order.total_amount)}",
            ]
        )
    )
    message.add_alternative(_render_order_html(order), subtype="html")
    return message


async def send_contact_form_notification(
    settings: SettingsModel,
    contact: ContactFormModel,
) -> None:
    if not _smtp_configured(settings):
        logger.warning(
            "contact_form_email_skipped",
            reason="smtp_not_configured",
            has_recipient=bool(settings.email),
        )
        return

    try:
        message = _build_contact_message(settings, contact)

        use_tls_direct = bool(APP_CONFIG.SMTP_USE_TLS) and APP_CONFIG.SMTP_PORT == 465
        start_tls = bool(APP_CONFIG.SMTP_USE_TLS) and not use_tls_direct

        await aiosmtplib.send(
            message,
            hostname=APP_CONFIG.SMTP_HOST,
            port=APP_CONFIG.SMTP_PORT,
            username=APP_CONFIG.SMTP_USER,
            password=APP_CONFIG.SMTP_PASS,
            use_tls=use_tls_direct,
            start_tls=start_tls,
        )
        logger.info(
            "contact_form_email_sent",
            recipient=settings.email,
            contact_id=str(contact.id),
        )
    except Exception as exc:
        logger.error("contact_form_email_failed", error=str(exc))


async def send_order_notification(
    settings: SettingsModel,
    order: OrderModel,
) -> None:
    if not _smtp_configured(settings):
        logger.warning(
            "order_email_skipped",
            reason="smtp_not_configured",
            has_recipient=bool(settings.email),
        )
        return

    try:
        message = _build_order_message(settings, order)

        use_tls_direct = bool(APP_CONFIG.SMTP_USE_TLS) and APP_CONFIG.SMTP_PORT == 465
        start_tls = bool(APP_CONFIG.SMTP_USE_TLS) and not use_tls_direct

        await aiosmtplib.send(
            message,
            hostname=APP_CONFIG.SMTP_HOST,
            port=APP_CONFIG.SMTP_PORT,
            username=APP_CONFIG.SMTP_USER,
            password=APP_CONFIG.SMTP_PASS,
            use_tls=use_tls_direct,
            start_tls=start_tls,
        )
        logger.info(
            "order_email_sent",
            recipient=settings.email,
            order_id=str(order.id),
        )
    except Exception as exc:
        logger.error("order_email_failed", error=str(exc))
