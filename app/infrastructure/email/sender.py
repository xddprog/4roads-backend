from email.message import EmailMessage

import aiosmtplib

from app.core.dto.contact_form import ContactFormModel
from app.core.dto.settings import SettingsModel
from app.infrastructure.config.config import APP_CONFIG
from app.infrastructure.logging import get_logger


logger = get_logger(__name__)


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
