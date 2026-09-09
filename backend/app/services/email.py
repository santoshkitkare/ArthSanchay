"""Password-reset email delivery (FR-AUTH-6).

Stubbed for this pass, per an explicit decision: instead of sending real email, the reset link is
logged server-side. Swapping in real SMTP later means implementing `send_reset_email` against
`config.Settings`'s SMTP_* fields (add them to `Settings` when that time comes) — no change to the
route, the token model, or anything that calls this function.
"""
import logging

logger = logging.getLogger("app.email")


def send_reset_email(to: str, reset_link: str) -> None:
    logger.info("PASSWORD RESET (stub — no email provider configured) for %s: %s", to, reset_link)
