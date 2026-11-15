import hashlib
import hmac
import json
import logging
from typing import Any

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import PlainTextResponse

from config import get_meta_app_secret, get_secret_webhook
from handlers.messages import message_received_handler
from handlers.statuses import message_status_handler

router = APIRouter()
WEBHOOK_PATH = "/webhook"
logger = logging.getLogger(__name__)


@router.get(WEBHOOK_PATH)
async def webhook_verify(
    mode: str = Query(alias="hub.mode"),
    token: str = Query(alias="hub.verify_token"),
    challenge: str = Query(alias="hub.challenge"),
) -> PlainTextResponse:
    if mode == "subscribe" and token == get_secret_webhook():
        return PlainTextResponse(challenge)

    raise HTTPException(status_code=403, detail="Verification failed")


@router.post(WEBHOOK_PATH)
async def webhook_receive(request: Request) -> dict[str, Any]:
    """
    Receives incoming messages from the WhatsApp API.
    """

    try:
        body = await request.body()
        verify_webhook_signature(body, request.headers.get("X-Hub-Signature-256"))
        try:
            payload: dict[str, Any] = json.loads(body)
        except json.JSONDecodeError as exc:
            raise HTTPException(status_code=400, detail="Invalid JSON payload") from exc

        for entry in payload.get("entry", []):
            for change in entry.get("changes", []):
                value = change.get("value", {})
                if value.get("messages"):
                    await _handle_messages(value)
                elif value.get("statuses"):
                    for status in value["statuses"]:
                        message_status_handler(status)
                else:
                    logger.warning("Received webhook change with no messages or statuses")

        return {"status": "received", "payload": payload}
    except HTTPException:
        raise
    except Exception:
        logger.exception("Unexpected error while processing webhook request")
        raise


def verify_webhook_signature(body: bytes, signature: str | None) -> None:
    app_secret = get_meta_app_secret()
    if not app_secret:
        logger.error(
            "META_APP_SECRET is missing; configure it in .env before receiving webhooks"
        )
        raise HTTPException(
            status_code=500,
            detail="Webhook app secret is not configured",
        )
    if not signature or not signature.startswith("sha256="):
        raise HTTPException(status_code=401, detail="Invalid webhook signature")

    expected = "sha256=" + hmac.new(
        app_secret.encode(),
        body,
        hashlib.sha256,
    ).hexdigest()
    if not hmac.compare_digest(expected, signature):
        raise HTTPException(status_code=401, detail="Invalid webhook signature")


async def _handle_messages(value: dict[str, Any]) -> None:
    for message in value["messages"]:
        if message.get("type") == "text":
            await _handle_text_message(value, message)
        elif message.get("type") == "interactive":
            await _handle_interactive_message(value, message)


def _sender_context(value: dict[str, Any], message: dict[str, Any]) -> dict[str, Any]:
    contact = value["contacts"][0]
    return {
        "name": contact["profile"]["name"],
        "sender_id": value["metadata"]["phone_number_id"],
        "sender_phone_number": message.get("from", {}),
        "message_id": message.get("id"),
    }


async def _handle_text_message(
    value: dict[str, Any], message: dict[str, Any]
) -> None:
    context = _sender_context(value, message)
    message_text = message.get("text", {}).get("body", "")
    logger.info(
        "Received text message",
        extra={
            "sender_name": context["name"],
            "sender_phone_number": context["sender_phone_number"],
            "message_id": context["message_id"],
        },
    )

    await message_received_handler({**context, "message_text": message_text})


async def _handle_interactive_message(
    value: dict[str, Any], message: dict[str, Any]
) -> None:
    context = _sender_context(value, message)
    button_reply = message.get("interactive", {}).get("button_reply", {})
    button_payload = button_reply.get("id", "")
    logger.info(
        "Received interactive button",
        extra={
            "sender_name": context["name"],
            "sender_phone_number": context["sender_phone_number"],
            "button_payload": button_payload,
            "message_id": context["message_id"],
        },
    )
    await message_received_handler(
        {**context, "message_text": button_payload, "button_payload": button_payload}
    )
