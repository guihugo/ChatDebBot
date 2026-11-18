import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from database.connection import initialize_database
from routes.webhook import router
from services.reminders import reminder_worker

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s - %(message)s",
)

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