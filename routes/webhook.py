from fastapi import APIRouter, Query, HTTPException
from fastapi.responses import PlainTextResponse
from config import get_secret_webhook

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
    # Process the incoming payload
    id = payload.get("entry")[0].get("id")
    value = payload["entry"][0]["changes"][0]["value"]
    if value.get('messages'):
        sender_id = value["metadata"]["phone_number_id"]
        contact = value["contacts"][0]
        name = contact["profile"]["name"]
        sender_phone_number = value["messages"][0].get("from", {})
        message = value["messages"][0].get("text", {}).get("body", "")
        print(f"Received message from: {name}, Sender ID: {sender_id}, Message: {message}, sender_phone_number: {sender_phone_number}, id: {id}")

    elif value.get('statuses'):
        status = value["statuses"][0]
        print(f"Received status update: {status}")

    else:
        print(f"Received unknown payload: {payload}")
    
    return {"status": "received", "payload": payload}