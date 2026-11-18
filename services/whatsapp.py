import logging
from urllib.parse import urlparse

import httpx

from config import get_meta_key, get_url

logger = logging.getLogger(__name__)

url = get_url()
meta_key = get_meta_key()


def _validate_configuration(phone_number: str) -> dict | None:
    if not meta_key:
        return {"error": "META_KEY is not configured"}
    if not url:
        return {"error": "URL is not configured"}
    if not phone_number:
        return {"error": "PHONE_NUMBER_RECEIVER is not configured"}
    return None


def _headers() -> dict:
    return {
        "Authorization": f"Bearer {meta_key}",
        "Content-Type": "application/json",
    }


def _safe_api_host(api_url: str) -> str:
    try:
        return urlparse(api_url).netloc or "unknown"
    except ValueError:
        return "unknown"


def _exception_chain(exc: BaseException) -> list[str]:
    chain = []
    current: BaseException | None = exc
    seen: set[int] = set()
    while current is not None and id(current) not in seen:
        seen.add(id(current))
        chain.append(
            f"{type(current).__module__}.{type(current).__name__}: "
            f"{str(current) or '<no message>'}"
        )
        current = current.__cause__ or current.__context__
    return chain


async def send_message_template(phone_number: str, template_dict: dict):
    error = _validate_configuration(phone_number)
    if error:
        return error

    body = {
        "messaging_product": "whatsapp",
        "to": phone_number,
        "type": "template",
        "template": {
            "name": template_dict.get("name"),
            "language": {
                "code": template_dict.get("language")
            },
        },
    }
    return await send_post_request(url, _headers(), body)


async def send_message(phone_number: str, message: str):
    error = _validate_configuration(phone_number)
    if error:
        return error

    body = {
        "messaging_product": "whatsapp",
        "to": phone_number,
        "type": "text",
        "text": {
            "preview_url": False,
            "body": message,
        },
    }
    return await send_post_request(url, _headers(), body)


async def send_button_message(phone_number: str, message: str, buttons: list):
    error = _validate_configuration(phone_number)
    if error:
        return error

    body = {
        "messaging_product": "whatsapp",
        "to": phone_number,
        "type": "interactive",
        "interactive": {
            "type": "button",
            "body": {
                "text": message,
            },
            "action": {
                "buttons": buttons,
            },
        },
    }
    return await send_post_request(url, _headers(), body)


async def send_post_request(api_url: str, headers: dict, body: dict):
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(api_url, headers=headers, json=body)
            response.raise_for_status()
            result = response.json()
            logger.info(
                "WhatsApp message sent successfully",
                extra={"recipient": body.get("to"), "message_type": body.get("type")},
            )
            return result

    except httpx.HTTPStatusError as exc:
        try:
            details = exc.response.json()
        except ValueError:
            details = exc.response.text
        logger.error(
            "WhatsApp API rejected message",
            extra={
                "api_host": _safe_api_host(api_url),
                "status_code": exc.response.status_code,
                "exception_type": type(exc).__name__,
                "response": exc.response.text,
            },
        )
        return {
            "error": "Meta API returned an error",
            "status_code": exc.response.status_code,
            "details": details,
        }

    except httpx.RequestError as exc:
        logger.error(
            "Could not connect to WhatsApp API",
            extra={
                "api_host": _safe_api_host(api_url),
                "exception_type": type(exc).__name__,
                "timeout": isinstance(exc, httpx.TimeoutException),
                "exception_chain": " | ".join(_exception_chain(exc)),
            },
        )
        return {
            "error": "Could not connect to Meta API",
            "details": {
                "exception_type": type(exc).__name__,
                "message": str(exc),
                "exception_chain": _exception_chain(exc),
            },
        }
