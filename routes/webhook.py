from typing import Any

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import PlainTextResponse

from config import get_secret_webhook
from handlers.messages import message_received_handler
from handlers.statuses import message_status_handler

router = APIRouter()
WEBHOOK_PATH = "/webhook"


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
async def webhook_receive(payload: dict[str, Any]) -> dict[str, Any]:
    """
    Receives incoming messages from the WhatsApp API.
    """

    for entry in payload["entry"]:
        for change in entry["changes"]:
            value = change["value"]
            if value.get("messages"):
                await _handle_messages(value)
            elif value.get("statuses"):
                for status in value["statuses"]:
                    message_status_handler(status)
            else:
                print(f"Received unknown payload: {payload}")

    return {"status": "received", "payload": payload}


async def _handle_messages(value: dict[str, Any]) -> None:
    for message in value["messages"]:
        print(f"Received message: {message}")

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
    print(
        f"Received message from: {context['name']}, "
        f"Sender ID: {context['sender_id']}, Message: {message_text}, "
        f"sender_phone_number: {context['sender_phone_number']}, "
        f"id: {context['message_id']}"
    )

    await message_received_handler({**context, "message_text": message_text})


async def _handle_interactive_message(
    value: dict[str, Any], message: dict[str, Any]
) -> None:
    context = _sender_context(value, message)
    button_reply = message.get("interactive", {}).get("button_reply", {})
    button_payload = button_reply.get("id", "")
    print(
        f"Received button click from: {context['name']}, "
        f"Sender ID: {context['sender_id']}, Button Payload: {button_payload}, "
        f"sender_phone_number: {context['sender_phone_number']}, "
        f"id: {context['message_id']}"
    )
    await message_received_handler(
        {**context, "message_text": button_payload, "button_payload": button_payload}
    )
