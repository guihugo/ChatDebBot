import httpx
from config import get_meta_key, get_phone_number, get_url

url = get_url()

async def send_message(template_name: str, message_language: str):
    """
    Sends a message to the WhatsApp API.
    
    Args:
        template_name (str): The type of the message (e.g., "text", "template").
        message_language (str): The language of the message.
    """

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
            "name": template_name,
            "language": {
                "code": message_language
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
