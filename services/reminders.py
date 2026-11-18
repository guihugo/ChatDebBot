import asyncio
import logging

from database.connection import get_debts_ready_for_reminder, mark_reminder_sent
from services.whatsapp import send_button_message

logger = logging.getLogger(__name__)

REMINDER_INTERVAL_SECONDS = 60


async def send_due_debt_reminders() -> None:
    for debt in get_debts_ready_for_reminder():
        try:
            description = (
                f" Descrição: {debt['description']}."
                if debt["description"]
                else ""
            )
            result = await send_button_message(
                phone_number=debt["owner_phone_number"],
                message=(
                    f"Olá! Lembrete: você tem uma cobrança de "
                    f"R${debt['amount']:.2f} para {debt['debtor_name']}."
                    f"{description} Essa cobrança já foi paga?"
                ),
                buttons=[
                    {
                        "type": "reply",
                        "reply": {
                            "id": f"mark_paid_{debt['id']}",
                            "title": "Já pagou",
                        },
                    },
                ],
            )
            if "error" not in result:
                mark_reminder_sent(debt["id"], debt["owner_phone_number"])
        except Exception:
            logger.exception(
                "Failed to send reminder",
                extra={
                    "debt_id": debt["id"],
                    "owner_phone_number": debt["owner_phone_number"],
                },
            )


async def reminder_worker() -> None:
    while True:
        try:
            await send_due_debt_reminders()
        except Exception:
            logger.exception("Reminder cycle failed; worker will continue")
        await asyncio.sleep(REMINDER_INTERVAL_SECONDS)
