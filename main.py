from fastapi import FastAPI
import httpx
from config import get_meta_key, get_phone_number

app = FastAPI()

url = "https://graph.facebook.com/v25.0/1418565291345962/messages"


@app.post("/test-message")
async def test_message():

    meta_key = get_meta_key()
    phone_number = get_phone_number()


    if not meta_key or not phone_number:
            return {"error": "META_KEY or PHONE_NUMBER_RECEIVER is not set in the environment variables."}
    headers = {
        "Authorization": f"Bearer {meta_key}",
        "Content-Type": "application/json"
    }

    body = {
        "messaging_product": "whatsapp",
        "to": phone_number,
        "type": "template",
        "template": {
            "name": "hello_world",
            "language": {
                "code": "en_US"
            }
        }
    }

    
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=body)
            response.raise_for_status()
            res = response.json()

    except httpx.HTTPStatusError as exc:
        return {
            "error": "Meta API returned an error",  
            "status_code": exc.response.status_code,
            "details": exc.response.json()
        }

    except httpx.RequestError as exc:
        return {
            "error": "Could not connect to Meta API",
            "details": str(exc)
        }

    return res
