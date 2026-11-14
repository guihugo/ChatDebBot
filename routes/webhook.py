from fastapi import APIRouter, Query, HTTPException
from fastapi.responses import PlainTextResponse
from config import get_secret_webhook
from handlers.messages import message_received_handler, send_first_message

router = APIRouter()


@router.get("/webhook")
async def webhook_verify(
    mode: str = Query(alias="hub.mode"),
    token: str = Query(alias="hub.verify_token"),
    challenge: str = Query(alias="hub.challenge")
):
    secret_webhook = get_secret_webhook()

    if mode == "subscribe" and token == secret_webhook:
        return PlainTextResponse(challenge)

    raise HTTPException(status_code=403, detail="Verification failed")


@router.post("/webhook")
async def webhook_receive(payload: dict):
    """
    Receives incoming messages from the WhatsApp API.
    """
    
    value = payload["entry"][0]["changes"][0]["value"]
    if value.get('messages'):
        sender_id = value["metadata"]["phone_number_id"]
        contact = value["contacts"][0]
        name = contact["profile"]["name"]
        sender_phone_number = value["messages"][0].get("from", {})
        message_text = value["messages"][0].get("text", {}).get("body", "")
        message_id = value["messages"][0].get("id")
        print(f"Received message from: {name}, Sender ID: {sender_id}, Message: {message_text}, sender_phone_number: {sender_phone_number}, id: {message_id}")

        message = {
            "name": name,
            "sender_id": sender_id,
            "sender_phone_number": sender_phone_number,
            "message_id": message_id,
            "message_text": message_text
        }

        await message_received_handler(message)

    elif value.get('statuses'):
        status = value["statuses"][0]
        print(f"Received status update: {status}")

    else:
        print(f"Received unknown payload: {payload}")
    
    return {"status": "received", "payload": payload}