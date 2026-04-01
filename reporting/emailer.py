"""Email delivery of execution reports."""

from __future__ import annotations

import smtplib
from email.message import EmailMessage
from pathlib import Path
from typing import Iterable

try:
    from loguru import logger  # type: ignore
except ImportError:  # pragma: no cover
    import logging

    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

from config.report_settings import load_report_settings


class ReportEmailer:
    """Simple SMTP client for distributing test reports."""

    def __init__(self) -> None:
        self.settings = load_report_settings()

    def send(self, subject: str, body: str, attachments: Iterable[Path] | None = None) -> None:
        if not self.settings.enable_email:
            logger.info("Email delivery disabled via configuration")
            return

        self.settings.validate()
        message = EmailMessage()
        message["Subject"] = subject
        message["From"] = self.settings.sender
        message["To"] = ", ".join(self.settings.recipients)
        message.set_content(body)

        for path in attachments or []:
            if not path.exists():
                logger.warning(f"Skipping attachment; file missing: {path}")
                continue
            with path.open("rb") as handle:
                message.add_attachment(
                    handle.read(),
                    maintype="application",
                    subtype="octet-stream",
                    filename=path.name,
                )

        logger.info(f"Sending execution report email to {self.settings.recipients}")
        with smtplib.SMTP(self.settings.smtp_host, self.settings.smtp_port, timeout=self.settings.smtp_timeout) as smtp:
            if self.settings.use_tls:
                smtp.starttls()
            if self.settings.smtp_username and self.settings.smtp_password:
                smtp.login(self.settings.smtp_username, self.settings.smtp_password)
            smtp.send_message(message)
