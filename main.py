import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from database.connection import initialize_database
from services.whatsapp import send_message, send_message_template
from routes.webhook import router
from services.reminders import reminder_worker

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s - %(message)s",
)

class Message(BaseModel):
    template_name: str
    template_language: str

@asynccontextmanager
async def lifespan(app: FastAPI):
    initialize_database()
    reminder_task = asyncio.create_task(reminder_worker())
    try:
        yield
    finally:
        reminder_task.cancel()
        await asyncio.gather(reminder_task, return_exceptions=True)

app = FastAPI(lifespan=lifespan)
app.include_router(router)

@app.post("/send-template")
async def send_whatsapp_template_message(phone_number: str, template_dict: dict):
    """
    Sends a WhatsApp template message to the specified phone number.
    """
    result = await send_message_template(phone_number=phone_number, template_dict=template_dict)

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