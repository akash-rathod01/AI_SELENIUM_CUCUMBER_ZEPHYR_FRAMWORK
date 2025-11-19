"""Configuration loader for report distribution."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import List


@dataclass
class ReportSettings:
    smtp_host: str = os.getenv("REPORT_SMTP_HOST", "")
    smtp_port: int = int(os.getenv("REPORT_SMTP_PORT", "587"))
    smtp_username: str | None = os.getenv("REPORT_SMTP_USER")
    smtp_password: str | None = os.getenv("REPORT_SMTP_PASSWORD")
    use_tls: bool = os.getenv("REPORT_SMTP_USE_TLS", "true").lower() == "true"
    smtp_timeout: int = int(os.getenv("REPORT_SMTP_TIMEOUT", "30"))
    sender: str = os.getenv("REPORT_SENDER", "")
    recipients: List[str] = field(default_factory=lambda: [r.strip() for r in os.getenv("REPORT_RECIPIENTS", "").split(",") if r.strip()])
    enable_email: bool = os.getenv("REPORT_ENABLE_EMAIL", "false").lower() == "true"

    def validate(self) -> None:
        if not self.recipients:
            raise RuntimeError("REPORT_RECIPIENTS must be set when email delivery is enabled")
        if not self.sender:
            raise RuntimeError("REPORT_SENDER must be provided for email delivery")
        if not self.smtp_host:
            raise RuntimeError("REPORT_SMTP_HOST is required for email delivery")


def load_report_settings() -> ReportSettings:
    return ReportSettings()
