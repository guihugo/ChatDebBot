from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from services.whatsapp import send_message, send_message_template
from routes.webhook import router

app = FastAPI()
app.include_router(router)

class Message(BaseModel):
    template_name: str
    template_language: str

@app.post("/test-message")
async def send_whatsapp_template_message(message: Message):
    """
    Tests the WhatsApp message sending functionality.
    """
    result = await send_message_template(template_name=message.template_name, message_language=message.template_language)

    return result

@app.post("/send-message")
async def send_whatsapp_message(phone_number: str, message: str):
    """
    Sends a WhatsApp message using the personalized message and language.
    """
    result = await send_message(phone_number=phone_number, message=message)

    if "error" in result:
        raise HTTPException(status_code=400, detail=result)

    return result