import httpx
import logging

from config import get_meta_key, get_url

logger = logging.getLogger(__name__)

url = get_url()
meta_key = get_meta_key()

async def send_message_template(phone_number: str, template_dict: dict):
    """
    Sends a message to the WhatsApp API.

    Args:
        phone_number (str): The phone number to send the message to.
        template_dict (dict): A dictionary containing the template name and language.
    """

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
            "name": template_dict.get("name"),
            "language": {
                "code": template_dict.get("language")
            }
        }
    }   

    return await send_post_request(url, headers, body)


async def send_message(phone_number: str, message: str):
    """
    Sends a message to the WhatsApp API.

    Args:
        phone_number (str): The phone number to send the message to.
        message (str): The message to send.
    """

    if not meta_key or not phone_number:
            return {"error": "META_KEY or PHONE_NUMBER_RECEIVER is not set in the environment variables."}
    headers = {
        "Authorization": f"Bearer {meta_key}",
        "Content-Type": "application/json"
    }

    body = {
        "messaging_product": "whatsapp",
        "to": phone_number,
        "type": "text",
        "text": {
            "preview_url": False,
            "body": message
        }
    }   
    
    return await send_post_request(url, headers, body)

async def send_button_message(phone_number: str, message: str, buttons: list):
    """
    Sends a button message to the WhatsApp API.

    Args:
        phone_number (str): The phone number to send the message to.
        message (str): The message to send.
        buttons (list): A list of button dictionaries.
    """

    if not meta_key or not phone_number:
            return {"error": "META_KEY or PHONE_NUMBER_RECEIVER is not set in the environment variables."}
    headers = {
        "Authorization": f"Bearer {meta_key}",
        "Content-Type": "application/json"
    }

    body = {
        "messaging_product": "whatsapp",
        "to": phone_number,
        "type": "interactive",
        "interactive": {
            "type": "button",
            "body": {
                "text": message
            },
            "action": {
                "buttons": buttons
            }
        }
    }   
    
    return await send_post_request(url, headers, body)


async def send_post_request(url: str, headers: dict, body: dict):
    """
    Sends a POST request to the specified URL with the given headers and body.

    Args:
        url (str): The URL to send the request to.
        headers (dict): The headers to include in the request.
        body (dict): The body of the request.

    Returns:
        dict: The response from the server.
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=body)
            response.raise_for_status()
            result = response.json()
            logger.info(
                "WhatsApp message sent successfully",
                extra={"recipient": body.get("to"), "message_type": body.get("type")},
            )
            return result

    except httpx.HTTPStatusError as exc:
        logger.error(
            "WhatsApp API rejected message: status=%s response=%s",
            exc.response.status_code,
            exc.response.text,
        )
        return {
            "error": "Meta API returned an error",  
            "status_code": exc.response.status_code,
            "details": exc.response.json()
        }

    except httpx.RequestError as exc:
        logger.error("Could not connect to WhatsApp API: %s", exc)
        return {
            "error": "Could not connect to Meta API",
            "details": str(exc)
        }