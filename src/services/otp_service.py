# src/services/otp_service.py
"""
OTP delivery service with pluggable providers.

Providers are selected via the OTP_PROVIDER env var:
  - "console" (default): prints the OTP to the server log. Use in development.
  - "email": sends the OTP via SMTP. Requires SMTP_HOST / SMTP_PORT and
             (optionally) SMTP_USER / SMTP_PASSWORD / SMTP_USE_TLS plus
             OTP_EMAIL_FROM_ADDRESS / OTP_EMAIL_FROM_NAME. Uses stdlib
             `smtplib` (no extra package).
  - "twilio": sends the OTP via Twilio SMS. Requires TWILIO_ACCOUNT_SID,
             TWILIO_AUTH_TOKEN, TWILIO_FROM_NUMBER. `pip install twilio`.
             DORMANT — blocked on DLT/GSTIN; see re-enable note below.
  - "msg91": sends via MSG91 Flow API (India). Requires MSG91_AUTH_KEY and
             MSG91_TEMPLATE_ID (a DLT-approved template whose variable is
             named ##OTP## or `otp`). No extra package required — uses
             `requests` which is already a dependency.
             DORMANT — blocked on DLT/GSTIN; see re-enable note below.

# SMS RE-ENABLE (once DLT/GSTIN clears):
#   1. In e-commerce/.env set OTP_PROVIDER=msg91 (or twilio) with its vars.
#   2. In src/schemas/auth.py + auth_vendor.py, revert `email: EmailStr` back
#      to `phone_number: str` on SendOTPRequest/VerifyOTPRequest.
#   3. In both React apps, swap the router back to PhoneLogin.jsx and send
#      phone_number in authAPI.js. Redux slot `identifier` can stay as-is.

The service also generates cryptographically-secure 6-digit OTPs and exposes
rate-limit / max-attempt settings read from the environment.
"""
import logging
import os
import re
import secrets
import smtplib
from email.message import EmailMessage
from email.utils import formataddr
from typing import Optional

import requests
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

OTP_PROVIDER = os.getenv("OTP_PROVIDER", "console").lower()
OTP_EXPIRY_MINUTES = int(os.getenv("OTP_EXPIRY_MINUTES", "10"))
OTP_MAX_ATTEMPTS = int(os.getenv("OTP_MAX_ATTEMPTS", "5"))
OTP_RESEND_COOLDOWN_SECONDS = int(os.getenv("OTP_RESEND_COOLDOWN_SECONDS", "60"))

SMTP_HOST = os.getenv("SMTP_HOST", "localhost")
SMTP_PORT = int(os.getenv("SMTP_PORT", "1025"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_USE_TLS = os.getenv("SMTP_USE_TLS", "false").lower() == "true"
SMTP_TIMEOUT_SECONDS = int(os.getenv("SMTP_TIMEOUT_SECONDS", "10"))

OTP_EMAIL_FROM_ADDRESS = os.getenv("OTP_EMAIL_FROM_ADDRESS", "no-reply@elakkiyaboutique.local")
OTP_EMAIL_FROM_NAME = os.getenv("OTP_EMAIL_FROM_NAME", "Elakkiya Boutique")
OTP_EMAIL_SUBJECT = os.getenv("OTP_EMAIL_SUBJECT", "Your verification code")

# --- SMS DORMANT (DLT/GSTIN blocker) ----------------------------------------
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "")
TWILIO_FROM_NUMBER = os.getenv("TWILIO_FROM_NUMBER", "")

MSG91_AUTH_KEY = os.getenv("MSG91_AUTH_KEY", "")
MSG91_TEMPLATE_ID = os.getenv("MSG91_TEMPLATE_ID", "")
MSG91_SENDER_ID = os.getenv("MSG91_SENDER_ID", "")
MSG91_DEFAULT_COUNTRY_CODE = os.getenv("MSG91_DEFAULT_COUNTRY_CODE", "91")
MSG91_FLOW_URL = "https://control.msg91.com/api/v5/flow"
MSG91_TIMEOUT_SECONDS = int(os.getenv("MSG91_TIMEOUT_SECONDS", "10"))
# --- /SMS DORMANT -----------------------------------------------------------


class OTPDeliveryError(Exception):
    """Raised when an OTP cannot be delivered to the user."""


def generate_otp(length: int = 6) -> str:
    """Generate a cryptographically-secure numeric OTP of the given length."""
    upper = 10 ** length
    return str(secrets.randbelow(upper)).zfill(length)


def _format_phone_for_sms(phone_number: str) -> str:
    """Ensure the number starts with '+'. Assumes it already contains a country code."""
    phone_number = phone_number.strip()
    if not phone_number.startswith("+"):
        phone_number = "+" + phone_number.lstrip("0")
    return phone_number


def _send_via_console(recipient: str, otp_code: str, purpose: str) -> None:
    banner = "=" * 60
    logger.warning(
        "\n%s\n[OTP:%s] to=%s code=%s (expires in %d min)\n%s",
        banner, purpose, recipient, otp_code, OTP_EXPIRY_MINUTES, banner,
    )
    print(
        f"\n{banner}\n[OTP:{purpose}] to={recipient} code={otp_code} "
        f"(expires in {OTP_EXPIRY_MINUTES} min)\n{banner}",
        flush=True,
    )


def _send_via_email(recipient: str, otp_code: str, purpose: str) -> None:
    msg = EmailMessage()
    msg["Subject"] = OTP_EMAIL_SUBJECT
    msg["From"] = formataddr((OTP_EMAIL_FROM_NAME, OTP_EMAIL_FROM_ADDRESS))
    msg["To"] = recipient
    msg.set_content(
        f"Your Elakkiya Boutique {purpose} verification code is: {otp_code}\n\n"
        f"This code expires in {OTP_EXPIRY_MINUTES} minutes. "
        f"Do not share it with anyone.\n\n"
        f"If you did not request this code, you can safely ignore this email."
    )

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=SMTP_TIMEOUT_SECONDS) as client:
            client.ehlo()
            if SMTP_USE_TLS:
                client.starttls()
                client.ehlo()
            if SMTP_USER and SMTP_PASSWORD:
                client.login(SMTP_USER, SMTP_PASSWORD)
            client.send_message(msg)
    except (smtplib.SMTPException, OSError) as exc:
        logger.exception("SMTP send failed for %s", recipient)
        raise OTPDeliveryError(f"Failed to send OTP via email: {exc}") from exc


def _send_via_twilio(recipient: str, otp_code: str, purpose: str) -> None:
    if not (TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN and TWILIO_FROM_NUMBER):
        raise OTPDeliveryError(
            "Twilio provider selected but TWILIO_ACCOUNT_SID / TWILIO_AUTH_TOKEN / "
            "TWILIO_FROM_NUMBER are not configured."
        )
    try:
        from twilio.rest import Client  # type: ignore
    except ImportError as exc:
        raise OTPDeliveryError(
            "Twilio provider selected but the 'twilio' package is not installed. "
            "Run: pip install twilio"
        ) from exc

    client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    body = (
        f"Your Elakkiya Boutique {purpose} verification code is {otp_code}. "
        f"It expires in {OTP_EXPIRY_MINUTES} minutes. Do not share this code."
    )
    try:
        client.messages.create(
            body=body,
            from_=TWILIO_FROM_NUMBER,
            to=_format_phone_for_sms(recipient),
        )
    except Exception as exc:
        logger.exception("Twilio send failed for %s", recipient)
        raise OTPDeliveryError(f"Failed to send OTP via Twilio: {exc}") from exc


def _format_phone_for_msg91(phone_number: str) -> str:
    """MSG91 requires digits only, with country code, no '+'. E.g., 919876543210."""
    digits = re.sub(r"\D", "", phone_number)
    if not digits:
        raise OTPDeliveryError(f"Cannot parse phone number '{phone_number}' for MSG91")
    # If the caller sent only a 10-digit Indian mobile (no country code), prepend default.
    if len(digits) == 10:
        digits = MSG91_DEFAULT_COUNTRY_CODE + digits
    return digits


def _send_via_msg91(recipient: str, otp_code: str, purpose: str) -> None:
    if not (MSG91_AUTH_KEY and MSG91_TEMPLATE_ID):
        raise OTPDeliveryError(
            "MSG91 provider selected but MSG91_AUTH_KEY / MSG91_TEMPLATE_ID are not configured."
        )

    payload: dict = {
        "template_id": MSG91_TEMPLATE_ID,
        "short_url": "0",
        "recipients": [
            {
                "mobiles": _format_phone_for_msg91(recipient),
                "otp": otp_code,
                "OTP": otp_code,
            }
        ],
    }
    if MSG91_SENDER_ID:
        payload["sender"] = MSG91_SENDER_ID

    headers = {
        "authkey": MSG91_AUTH_KEY,
        "Content-Type": "application/json",
        "accept": "application/json",
    }

    try:
        response = requests.post(
            MSG91_FLOW_URL,
            json=payload,
            headers=headers,
            timeout=MSG91_TIMEOUT_SECONDS,
        )
    except requests.RequestException as exc:
        logger.exception("MSG91 network error for %s", recipient)
        raise OTPDeliveryError(f"MSG91 request failed: {exc}") from exc

    if response.status_code >= 400:
        logger.error(
            "MSG91 returned %s for %s: %s",
            response.status_code, recipient, response.text[:500],
        )
        raise OTPDeliveryError(
            f"MSG91 rejected the request (HTTP {response.status_code}): {response.text[:200]}"
        )

    try:
        body = response.json()
    except ValueError:
        body = {}
    # MSG91 returns {"type": "success", ...} on success; any other "type" is an error.
    if isinstance(body, dict) and body.get("type") and body["type"].lower() != "success":
        logger.error("MSG91 error body for %s: %s", recipient, body)
        raise OTPDeliveryError(
            f"MSG91 error: {body.get('message') or body}"
        )


def deliver_otp(recipient: str, otp_code: str, purpose: str = "login") -> str:
    """Dispatch the OTP through the configured provider. Returns the provider used.

    `recipient` is the channel-specific address — an email for OTP_PROVIDER=email
    and a phone number (with or without leading +) for sms providers.
    """
    provider = OTP_PROVIDER
    if provider == "email":
        _send_via_email(recipient, otp_code, purpose)
    elif provider == "twilio":
        _send_via_twilio(recipient, otp_code, purpose)
    elif provider == "msg91":
        _send_via_msg91(recipient, otp_code, purpose)
    elif provider == "console":
        _send_via_console(recipient, otp_code, purpose)
    else:
        logger.warning("Unknown OTP_PROVIDER '%s' — falling back to console", provider)
        _send_via_console(recipient, otp_code, purpose)
        provider = "console"
    return provider
