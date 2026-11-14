from fastapi import FastAPI
from pydantic import BaseModel
from services.whatsapp import send_message

app = FastAPI()

class Message(BaseModel):
    template_name: str
    template_language: str

@app.post("/test-message")
async def test_message(message: Message):
    """
    Tests the WhatsApp message sending functionality.
    """
    result = await send_message(template_name=message.template_name, message_language=message.template_language)

    return result
